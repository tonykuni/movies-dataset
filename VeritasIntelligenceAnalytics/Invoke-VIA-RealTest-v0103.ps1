# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RealTest-v0103.ps1 — 短指令 via-realtest(R45 · v0102 進化一版;via-realtest 自動取最新版號)
#   操作員(R45 2026-10-02):「確認加上加速模組及矩陣報告模組 透過vcgc vcgc-vdf vcgc-vrn三路線同步進行快速完成指令
#   vcgc碰到環境部分直接啟動完整安裝流程 強化上面指令進化一版」
#   本版在 v0102 上加三件(其餘一字照 v0102):
#   (A) 三路線同步:VCGC 本身那一路(VCGC 全功能串測 test --quick)和 v0101 的 VCGC→VDF ∥ VCGC→VRN 同時起跑(背景子行程,
#       log 在 VIA_Reports\realtest\VCGC_<時間>.log);v0101 跑完再等 VCGC 那一路收尾(有進度條 · 有看門狗)。
#   (B) 環境完整安裝流程:ENV MANAGER 總判不是 GREEN → 直接接既有兩支正主:
#       ① CGC_MDL135_EnvGovernance tools --apply --approve(= via-envtools -Apply -Approve:裝前 freeze 存證 · 順序安裝 · 中高風險同名獨立境)
#       ② CGC_MDL137_RunGate run --family vdf,vrn --approve-install(鏈上缺件裝進家族境,只增不減,base 不裝功能件)
#       ③ 再跑 ENV MANAGER check,前後總判都記進交接紀錄。
#       網路同意閘(L07/L08)**AI 不代設**:沒開時,在互動視窗問你一次「輸入 Y 開本次同意閘」;你答 Y 才在本行程開(跑完還原)。
#       你事先就同意:帶 -AutoInstall(= 你親手開閘)或自己設 $env:VIA_NET_CONSENT='YES'。不要裝:-NoInstall。
#   (D) 全景 AST 錨點定位(R45 第二令「加入全景分析功能 ast定位功能 錨點精準定位 全面 快 精準不遺漏 再生及一次 與panorama指令結合只增不減」):
#       和 VCGC 路線同時起兩條唯讀背景線(鎖冊 token 那一支 CGC_MDL158;只 ast.parse,不執行被讀的檔):
#       PAN-SCAN `scan --fast --json`(活樹全部,治理七類 ACCEL/NET/VERB/HARDIMP/PINVER/SYSEXE/TALIB,約 20 秒)·
#       PAN-READ `read <VDF> <VRN> <registry> --json`(通用 AST 類 SYNTAX/COMPILE/DUPDEF/TAILAPI/UNREACH/BAREEXC/SWALLOW/MUTDEF)。
#       每個問題落成一個錨點「檔:行 類 說明」,**一個不漏**寫進 VIA_Reports\realtest\AST_ANCHORS_<時間>.txt + _latest.txt(每輪再生);
#       SYNTAX / COMPILE / TALIB 有就記紅;其餘分類計數進交接紀錄與黃字。v0101 原有的 Panorama monitor 照跑(只增不減)。
#   (E) MasterControl 總控頁併入 VCGC 收尾(R45 第三令「master control main併入vcgc總控」):追蹤頁 ui_support\VIA_UI_MasterControl_v0100.html
#       由正主管理器(VIA_SYSTEM_MANAGER 尾版 _build_page)產生;新模組一進來頁就落後,CI test_11 會紅。收尾時用契約測試同一把尺比對,
#       落後才重產(LF · UTF-8)並跟交接紀錄一起提交;一樣就不動。
#   (C) 加速模組 · 矩陣報告確認列:PS 25 加速器(v0101 ①)· PY 加速器 / 網路工具載入(ENV MANAGER ②③)· 覆蓋矩陣頁 · 三合一頁,收尾一行交代。
# ---- 以下為 v0102 原說明 ----
# Invoke-VIA-RealTest-v0102.ps1 — 短指令 via-realtest(R44 · 一支 PS 全包:拉齊 → 實測 → 樣本驗證 → 交接紀錄 → 同步 GitHub)
#   操作員(R44 2026-10-02):「integrate into one ps code to handle all and log the handover report sync all to github」
#   工作站實錄:`git pull` 被兩種東西擋住 ——
#     (a) 本機帳本有只增寫的新列(VIA_Lessons_Ledger · VIA_ToolCoverage_Ledger)→「local changes would be overwritten」;
#     (b) 先前從分支單拉的檔(Invoke-VIA-RealTest-v0100 · Register-v0265 · 鏈跑器 v0105 / v0108)成了未追蹤檔,內容和遠端一樣
#         →「untracked working tree files would be overwritten」。
#   本版只加頭尾,實測本體照 v0101(呼叫它,不複製):
#   ① 拉齊(-NoSync 跳過):未完成合併先 abort;擋路的未追蹤檔**和遠端一模一樣**才搬到 %TEMP%\VIA_presync_<時間>(搬,不刪;
#      內容不同就不碰、列紅字);只增寫帳本(*_Ledger_v####.json/.jsonl)先在本機提交;已知的副作用檔
#      (VIA_Engine_Consolidation_Register:鏈跑會寫 candidates)還原;其餘本機改動**不碰**,照實列出;
#      然後交給既有拉齊醫生 CGC_MDL143_MergeMedic sync --apply(分叉 merge --no-ff · 帳本聯集 · 零 force / reset / 刪除)。
#   ② 實測:呼叫 Invoke-VIA-RealTest-v0101(25 加速器 · VDF ∥ VRN ∥ 覆蓋 ∥ 衝突 · ENV 等鏈跑完 · 全景 + 三合一 · 紅字 / 黃字)。
#   ③ 樣本驗證:VRN_ENG392_TextCompleteness run --dir <-Samples,預設 C:\測試樣本報告>(經 VCGC)。
#   ④ 交接:VCGC handoff check(只判,不寫 checkpoint;checkpoint 要綠才准,由 AI 端在 PR 上做)。
#   ⑤ 交接紀錄:docs\handoff\workstation\WS_HANDOVER_<時間>.md + WS_HANDOVER_latest.md(結果總表 · 紅字 · 黃字全文 · 樣本 · 交接 · 拉齊動作)。
#   ⑥ 同步 GitHub(-NoPush 跳過):只提交「只增寫帳本 + docs\handoff\」;VIA_Reports 永不提交(.gitignore 也擋);
#      push 被拒(遠端又動了)→ 再拉齊一次 → 再 push 一次;還不行就照實記紅,不 force。
#   不代開網路同意閘;不用 TA-Lib;不刪檔;不 force;不 reset --hard;不 stash drop。
# 用法:via-realtest [-AutoInstall | -NoInstall] [-NoSync] [-NoPush] [-Samples <夾>] [-Resume] [-NoOpen] [-StrictGate] [-StallSec 240] [-MaxMin 60]
# 結束碼:同 v0101(0 全綠 · 2 有發現 · 1 有紅 · 124 有一條超時);拉齊或推送失敗另算紅(1)。
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$AutoInstall,
    [switch]$NoInstall,
    [switch]$NoSync,
    [switch]$NoPush,
    [string]$Samples = "C:\測試樣本報告",
    [switch]$Resume,
    [switch]$FixEnv,
    [switch]$NoOpen,
    [switch]$StrictGate,
    [int]$StallSec = 240,
    [int]$MaxMin = 60
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
$Reg = Join-Path $VIA "supportive modules\registry"
$Rep = Join-Path $VIA "VIA_Reports"
$LogDir = Join-Path $Rep "realtest"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Red = New-Object System.Collections.Generic.List[string]
$Notes = New-Object System.Collections.Generic.List[string]
$SideEffect = @("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Engine_Consolidation_Register_v0100.json")
$LedgerRx = '_Ledger_v\d{3,4}\.jsonl?$'
$HandoffRx = '^VeritasIntelligenceAnalytics/docs/handoff/|^VeritasIntelligenceAnalytics/supportive modules/ui_support/VIA_UI_MasterControl_v0100\.html$'
$keepFromVcgc = $env:VIA_FROM_VCGC; $keepPush = $env:VIA_VCGC_PUSH; $keepConsent = $env:VIA_NET_CONSENT

function Get-Py {
    foreach ($c in @($env:VIA_PY, "python", "python3", "py")) {
        if (-not $c) { continue }
        $cmd = Get-Command $c -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }
    return $null
}
function Get-Newest([string]$Dir, [string]$Filter) {
    Get-ChildItem -LiteralPath $Dir -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
}
function G { & git -C $Repo @args 2>&1 | ForEach-Object { "" + $_ } }
function Unquote([string]$p) { $p = $p.Trim(); if ($p.StartsWith('"') -and $p.EndsWith('"')) { $p = $p.Substring(1, $p.Length - 2) -replace '\\"', '"' }; return $p }
function Get-Porcelain {
    # 回 @{ code; path }(-z 不好在 PS 拆;用 core.quotepath=false 讓中文路徑原樣)
    @(& git -C $Repo -c core.quotepath=false status --porcelain -uall 2>$null | ForEach-Object {
        $l = "" + $_
        if ($l.Length -ge 4) { [pscustomobject]@{ code = $l.Substring(0, 2); path = (Unquote ($l.Substring(3) -replace '^.* -> ', '')) } }
    })
}
function Invoke-MergeMedic([string]$py, [string]$V) {
    $out = @(& $py $V run --family core CGC_MDL143_MergeMedic sync --apply 2>&1 | ForEach-Object { "" + $_ })
    return @{ rc = $LASTEXITCODE; out = $out }
}

$py = Get-Py
$V = Get-Newest $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
if (-not $py -or -not $V) { Write-Host "  [via-realtest v0103] 找不到 python 或 VCGC 主控台尾版" -ForegroundColor Red; exit 1 }
$env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"
$headBefore = (G rev-parse --short HEAD | Select-Object -Last 1)
$branch = (G rev-parse --abbrev-ref HEAD | Select-Object -Last 1)

Write-Host ""
Write-Host "  ╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  via-realtest v0103 · 拉齊 → VCGC ∥ VDF ∥ VRN ∥ 全景AST → 環境安裝 → 樣本 → 交接 → GitHub" -ForegroundColor Cyan
Write-Host "  ╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ① 拉齊 ---------------------------------------------------------------------------------
$syncLine = "跳過(-NoSync)"
if (-not $NoSync) {
    Write-Progress -Id 0 -Activity "via-realtest v0103" -Status "① 拉齊 GitHub…" -PercentComplete 1
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) {
        $null = G merge --abort
        $Notes.Add("未完成的合併已 abort(合併前的本機狀態原樣回來)")
    }
    $null = G fetch -q origin $branch
    # 已知副作用檔還原(鏈跑會在冊上寫 candidates;不提交)
    foreach ($s in $SideEffect) {
        if (@(Get-Porcelain | Where-Object { $_.path -eq $s -and $_.code -match 'M' }).Count) { $null = G checkout -- $s; $Notes.Add("副作用檔還原:" + (Split-Path $s -Leaf)) }
    }
    # 擋路的未追蹤檔:遠端有同路徑 → 內容一樣才搬走(搬到 %TEMP%,不刪)
    $bk = Join-Path ([IO.Path]::GetTempPath()) ("VIA_presync_" + $stamp)
    foreach ($u in @(Get-Porcelain | Where-Object { $_.code -eq '??' })) {
        $rel = $u.path
        if ($rel.EndsWith("/")) { continue }
        $remoteBlob = (& git -C $Repo rev-parse --verify -q ("origin/" + $branch + ":" + $rel) 2>$null)
        if (-not $remoteBlob) { continue }
        $localBlob = (& git -C $Repo hash-object -- (Join-Path $Repo $rel) 2>$null)
        if ($localBlob -eq $remoteBlob) {
            $dest = Join-Path $bk $rel
            New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
            Move-Item -LiteralPath (Join-Path $Repo $rel) -Destination $dest -Force
            $Notes.Add("未追蹤檔與遠端一模一樣 → 搬到 " + $dest + "(拉下來的就是同一份)")
        } else {
            $Red.Add("拉齊:未追蹤檔 " + $rel + " 和遠端不同 → 不碰;請你決定留哪份(另存新版號或移開)後再跑")
        }
    }
    # 只增寫帳本先在本機提交(拉齊醫生合併時做聯集,不丟列)
    $led = @(Get-Porcelain | Where-Object { $_.code -match 'M' -and $_.path -match $LedgerRx } | ForEach-Object { $_.path })
    if ($led.Count) {
        $null = G add -- @led
        $null = G commit -q -m ("workstation: append-only ledgers before sync (" + $stamp + ")") -- @led
        $Notes.Add("只增寫帳本先在本機提交 " + $led.Count + " 支:" + (($led | ForEach-Object { Split-Path $_ -Leaf }) -join "、"))
    }
    $other = @(Get-Porcelain | Where-Object { $_.code -ne '??' })
    if ($other.Count) { $Notes.Add("其餘本機改動不碰(" + $other.Count + " 檔):" + (($other | Select-Object -First 8 | ForEach-Object { $_.path }) -join "、")) }
    $mm = Invoke-MergeMedic $py $V.FullName
    $mmLine = @($mm.out | Where-Object { $_ -match '拉齊|MergeMedic|ff|merge|分叉|DIVERGED|BEHIND|UP_TO_DATE|AHEAD|衝突|聯集' } | Select-Object -Last 3) -join " | "
    $headAfter = (G rev-parse --short HEAD | Select-Object -Last 1)
    $ab = (G rev-list --left-right --count ("origin/" + $branch + "...HEAD") | Select-Object -Last 1)
    $syncLine = "HEAD " + $headBefore + " → " + $headAfter + " · 落後/領先 " + ($ab -replace "\s+", "/") + " · MergeMedic rc " + $mm.rc + $(if ($mmLine) { " · " + $mmLine } else { "" })
    if ($mm.rc -notin 0, 2) { $Red.Add("拉齊:MergeMedic rc " + $mm.rc + " · " + (($mm.out | Select-Object -Last 4) -join " | ")) }
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) { $Red.Add("拉齊:合併有人工衝突沒解(git status 看 UU 檔);實測照跑,推送跳過") }
    Write-Host ("  ① 拉齊 · " + $syncLine) -ForegroundColor $(if ($Red.Count) { "Red" } else { "Green" })
    $Notes | ForEach-Object { Write-Host ("     · " + $_) -ForegroundColor DarkGray }
}

# ② 三路線:VCGC 本身(背景)∥ v0101 的 VCGC→VDF ∥ VCGC→VRN -------------------------------
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$vcgcLog = Join-Path $LogDir ("VCGC_" + $stamp + ".log"); $vcgcErr = Join-Path $LogDir ("VCGC_" + $stamp + ".err.log")
$vcgcProc = $null; $vcgcT0 = Get-Date
try {
    $vcgcProc = Start-Process -FilePath $py -ArgumentList ('"' + $V.FullName + '" test --quick') -WorkingDirectory $VIA -NoNewWindow -PassThru `
        -RedirectStandardOutput $vcgcLog -RedirectStandardError $vcgcErr
    Write-Host "  ② 啟動 VCGC 全功能串測(test --quick)· 與 VCGC→VDF ∥ VCGC→VRN 同步進行" -ForegroundColor DarkGray
} catch { $Red.Add("VCGC 路線起不來:" + $_.Exception.Message) }
# (D) 全景 AST 錨點:兩條唯讀背景線(鎖冊 token 那一支)
$tok = $null
try { $tok = Join-Path $Repo ((Get-Content -LiteralPath (Join-Path $Reg "VIA_ToolVersion_Lock_v0100.json") -Raw -Encoding UTF8 | ConvertFrom-Json).token.path) } catch { }
if (-not $tok -or -not (Test-Path -LiteralPath $tok)) { $tok = (Get-Newest $Reg "CGC_MDL158_VIAPanoramaAuditRepair_v*.py").FullName }
$panScan = Join-Path $LogDir ("PANSCAN_" + $stamp + ".json"); $panRead = Join-Path $LogDir ("PANREAD_" + $stamp + ".json")
$panProcs = @()
if ($tok) {
    try {
        $panProcs += Start-Process -FilePath $py -ArgumentList ('"' + $tok + '" scan --fast --json') -WorkingDirectory $VIA -NoNewWindow -PassThru `
            -RedirectStandardOutput $panScan -RedirectStandardError (Join-Path $LogDir ("PANSCAN_" + $stamp + ".err.log"))
        $panProcs += Start-Process -FilePath $py -ArgumentList ('"' + $tok + '" read "functional modules\VDF" "functional modules\VRN" "supportive modules\registry" --json') -WorkingDirectory $VIA -NoNewWindow -PassThru `
            -RedirectStandardOutput $panRead -RedirectStandardError (Join-Path $LogDir ("PANREAD_" + $stamp + ".err.log"))
        Write-Host "  ② 啟動 全景 AST 錨點定位(PAN-SCAN 治理七類 · PAN-READ 通用 AST 類)· 唯讀並行" -ForegroundColor DarkGray
    } catch { $Red.Add("全景 AST 線起不來:" + $_.Exception.Message) }
} else { $Red.Add("全景 AST:找不到鎖冊 token 工具(CGC_MDL158)") }
$rt = Join-Path $VIA "Invoke-VIA-RealTest-v0101.ps1"
$rtRc = -1
if (Test-Path -LiteralPath $rt) {
    $rtArgs = @{ StallSec = $StallSec; MaxMin = $MaxMin }
    if ($Resume) { $rtArgs.Resume = $true }; if ($FixEnv) { $rtArgs.FixEnv = $true }
    if ($NoOpen) { $rtArgs.NoOpen = $true }; if ($StrictGate) { $rtArgs.StrictGate = $true }
    & $rt @rtArgs
    $rtRc = $LASTEXITCODE
} else { $Red.Add("實測:找不到 Invoke-VIA-RealTest-v0101.ps1(拉齊沒成功?)") }
$env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"      # v0101 跑完會還原環境變數,這裡再設回來
$vcgcRc = -1; $vcgcLine = "(沒起跑)"
if ($vcgcProc) {
    while (-not $vcgcProc.HasExited) {
        $el = [int]((Get-Date) - $vcgcT0).TotalSeconds
        $last = @(Get-Content -LiteralPath $vcgcLog -Tail 1 -ErrorAction SilentlyContinue) -join ""
        Write-Progress -Id 9 -Activity "VCGC 全功能串測(test --quick)" -Status ("收尾中 · 已 " + $el + "s · " + $(if ($last.Length -gt 90) { $last.Substring(0, 90) } else { $last })) -PercentComplete ([Math]::Min(95, [int]($el / 3)))
        if ($el -ge $MaxMin * 60) { try { $vcgcProc.Kill($true) } catch { }; $Red.Add("VCGC 路線超過 " + $MaxMin + " 分鐘被看門狗停掉"); break }
        Start-Sleep -Milliseconds 800
    }
    Write-Progress -Id 9 -Activity "VCGC 全功能串測(test --quick)" -Completed
    $vcgcProc.WaitForExit(); $vcgcRc = $vcgcProc.ExitCode
    $vcgcLine = (@(Get-Content -LiteralPath $vcgcLog -ErrorAction SilentlyContinue | Where-Object { $_ -match 'VCGC 全功能串測' }) | Select-Object -Last 1)
    $vcgcBad = @(Get-Content -LiteralPath $vcgcLog -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*\[(RED|YELLOW)\]' } | Select-Object -First 8)
    Write-Host ("  ② VCGC 路線 · rc " + $vcgcRc + " · " + $vcgcLine) -ForegroundColor $(if ($vcgcRc -eq 0) { "Green" } elseif ($vcgcRc -eq 2) { "Yellow" } else { "Red" })
    $vcgcBad | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor $(if ($_ -match 'RED') { "Red" } else { "Yellow" }) }
    if ($vcgcRc -eq 1) { $Red.Add("VCGC 全功能串測 rc 1:" + $vcgcLine) }
}

# (D) 全景 AST 錨點收尾 ---------------------------------------------------------------------
foreach ($pp in $panProcs) { if ($pp -and -not $pp.HasExited) { if (-not $pp.WaitForExit(600000)) { try { $pp.Kill($true) } catch { }; $Red.Add("全景 AST 線超過 10 分鐘被停掉") } } }
function Read-JsonTail([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) { return $null }
    $t = Get-Content -LiteralPath $p -Raw -Encoding UTF8
    $i = $t.IndexOf("{"); if ($i -lt 0) { return $null }
    try { return ($t.Substring($i) | ConvertFrom-Json -Depth 64) } catch { return $null }
}
$anchors = New-Object System.Collections.Generic.List[string]
$astCount = [ordered]@{}
$severe = @("SYNTAX", "COMPILE", "TALIB")
$sj = Read-JsonTail $panScan
if ($sj) {
    foreach ($r in @($sj.rows | Where-Object { -not $_.exempt })) {
        $anchors.Add(("{0}:{1}  {2}  {3}" -f $r.file, $r.line, $r.cls, $r.detail))
        $astCount["治理:" + $r.cls] = 1 + [int]$astCount["治理:" + $r.cls]
    }
}
$rj = Read-JsonTail $panRead
if ($rj) {
    foreach ($c in @($rj.cards)) {
        $rel = ("" + $c.path); if ($rel.StartsWith($VIA)) { $rel = $rel.Substring($VIA.Length).TrimStart('\', '/') }
        foreach ($is in @($c.issues)) {
            if (-not $is) { continue }
            $anchors.Add(("{0}:{1}  {2}  {3}" -f $rel, $is.line, $is.cls, $is.detail))
            $astCount["AST:" + $is.cls] = 1 + [int]$astCount["AST:" + $is.cls]
        }
    }
}
$anchorFile = Join-Path $LogDir ("AST_ANCHORS_" + $stamp + ".txt")
$hdr = @("# 全景 AST 錨點 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · 共 " + $anchors.Count + " 個(檔:行 類 說明;一個不漏)",
         "# PAN-SCAN 活樹 " + $(if ($sj) { $sj.files_scanned } else { "?" }) + " 檔 · PAN-READ " + $(if ($rj) { $rj.files } else { "?" }) + " 檔 · 工具 " + (Split-Path $tok -Leaf))
($hdr + ($anchors | Sort-Object)) | Set-Content -LiteralPath $anchorFile -Encoding UTF8
Copy-Item -LiteralPath $anchorFile -Destination (Join-Path $LogDir "AST_ANCHORS_latest.txt") -Force
$astLine = "錨點 " + $anchors.Count + " · " + ((@($astCount.Keys) | ForEach-Object { $_ + " " + $astCount[$_] }) -join " · ") + " · 全文 " + $anchorFile
$sev = @($anchors | Where-Object { $a = $_; @($severe | Where-Object { $a -match ("  " + $_ + "  ") }).Count -gt 0 })
if (-not $sj -or -not $rj) { $Red.Add("全景 AST:" + $(if (-not $sj) { "PAN-SCAN " } else { "" }) + $(if (-not $rj) { "PAN-READ " } else { "" }) + "沒產出 JSON(看 VIA_Reports\realtest\PAN*.err.log)") }
foreach ($a in ($sev | Select-Object -First 20)) { $Red.Add("AST 錨點(必修):" + $a) }
Write-Host ("  ⓓ 全景 AST · " + $astLine) -ForegroundColor $(if ($sev.Count) { "Red" } elseif ($anchors.Count) { "Yellow" } else { "Green" })
$sev | Select-Object -First 10 | ForEach-Object { Write-Host ("     ✖ " + $_) -ForegroundColor Red }

# (B) 環境完整安裝流程 ----------------------------------------------------------------------
$envBefore = ""; $envAfter = ""; $installLine = "不需要(ENV GREEN)"
$envJson = Join-Path $Rep "env_manager\ENVMGR_latest.json"
try { $envBefore = (Get-Content -LiteralPath $envJson -Raw -Encoding UTF8 | ConvertFrom-Json).verdict } catch { $envBefore = "NODATA" }
if ($envBefore -ne "GREEN") {
    if ($NoInstall) { $installLine = "ENV " + $envBefore + " · -NoInstall:不裝" }
    else {
        if ($env:VIA_NET_CONSENT -ne "YES") {
            if ($AutoInstall) { $env:VIA_NET_CONSENT = "YES"; $Notes.Add("-AutoInstall:操作員事先同意,本行程開網路同意閘(跑完還原)") }
            elseif ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
                Write-Host ("  ⓔ ENV MANAGER 總判 " + $envBefore + " · 要現在跑完整安裝流程嗎?(會連網安裝;同意閘 AI 不代開)") -ForegroundColor Yellow
                $ans = Read-Host "    輸入 Y 開本次同意閘並安裝(其他鍵 = 不裝)"
                if ("" + $ans -match '^[Yy]') { $env:VIA_NET_CONSENT = "YES"; $Notes.Add("操作員在視窗答 Y:本行程開網路同意閘(跑完還原)") }
            }
        }
        if ($env:VIA_NET_CONSENT -eq "YES") {
            Write-Progress -Id 0 -Activity "via-realtest v0103" -Status "ⓔ 環境完整安裝流程…" -PercentComplete 90
            Write-Host "  ⓔ 環境完整安裝 ① 工具冊順序安裝(CGC_MDL135 tools --apply --approve)…" -ForegroundColor Cyan
            $i1 = @(& $py $V.FullName run --family core CGC_MDL135_EnvGovernance tools --apply --approve 2>&1 | ForEach-Object { "" + $_ }); $i1rc = $LASTEXITCODE
            Write-Host "  ⓔ 環境完整安裝 ② 鏈上缺件裝進家族境(CGC_MDL137 run --family vdf,vrn --approve-install)…" -ForegroundColor Cyan
            $i2 = @(& $py $V.FullName run --family core CGC_MDL137_RunGate run --family vdf,vrn --approve-install 2>&1 | ForEach-Object { "" + $_ }); $i2rc = $LASTEXITCODE
            Write-Host "  ⓔ 環境完整安裝 ③ 再驗(ENV MANAGER check)…" -ForegroundColor Cyan
            $null = & $py $V.FullName run --family core CGC_MDL240_EnvManager check 2>&1
            try { $envAfter = (Get-Content -LiteralPath $envJson -Raw -Encoding UTF8 | ConvertFrom-Json).verdict } catch { $envAfter = "NODATA" }
            $installLine = "ENV " + $envBefore + " → " + $envAfter + " · 工具冊 rc " + $i1rc + " · 家族境補庫 rc " + $i2rc
            foreach ($l in @(($i1 + $i2) | Where-Object { $_ -match 'FAIL|BLOCK|ERROR|錯|失敗' } | Select-Object -First 6)) { $Notes.Add("安裝:" + $l) }
            if ($i1rc -eq 1 -or $i2rc -eq 1) { $Red.Add("環境安裝有紅:" + $installLine) }
        } else { $installLine = "ENV " + $envBefore + " · 同意閘沒開:只列補法(下次帶 -AutoInstall 或答 Y)" }
    }
}
Write-Host ("  ⓔ 環境 · " + $installLine) -ForegroundColor $(if ($installLine -match 'GREEN\)$|→ GREEN') { "Green" } elseif ($installLine -match '紅') { "Red" } else { "Yellow" })

# (C) 加速模組 · 矩陣報告確認 ----------------------------------------------------------------
$pasteNow = Join-Path $LogDir "PASTE_TO_AI_latest.txt"
$pt = if (Test-Path -LiteralPath $pasteNow) { Get-Content -LiteralPath $pasteNow -Raw -Encoding UTF8 } else { "" }
$accPs = if ($pt -match 'PS 加速器 (\d+)/25') { $Matches[1] + "/25" } else { "?" }
$accPy = "?"; try { $ej = Get-Content -LiteralPath $envJson -Raw -Encoding UTF8 | ConvertFrom-Json; $accPy = (@($ej.rows | Where-Object { $_.item -match '^[②③]' } | ForEach-Object { $_.state }) -join "/") } catch { }
$covPage = Join-Path $Rep "toolprobe\COVERAGE_MATRIX_latest.html"
$triPage = Join-Path $Rep "template_adapter\synced\VIAHTMLUniversalUI_Standalone\VIA_UI_VIAHTMLUniversalUI_Standalone_latest.html"
$fresh = { param($p) (Test-Path -LiteralPath $p) -and (Get-Item -LiteralPath $p).LastWriteTime -ge $vcgcT0.AddSeconds(-5) }
$accLine = "PS 加速器 " + $accPs + " · PY 加速器 / 網路工具載入 " + $accPy + " · 覆蓋矩陣頁 " + $(if (& $fresh $covPage) { "本輪新" } else { "沒更新" }) + " · 三合一頁 " + $(if (& $fresh $triPage) { "本輪新" } else { "沒更新" })
Write-Host ("  ⓐ 加速模組 · 矩陣報告 · " + $accLine) -ForegroundColor $(if ($accPs -eq "25/25" -and (& $fresh $covPage)) { "Green" } else { "Yellow" })

# ③ 樣本驗證 -----------------------------------------------------------------------------
Write-Progress -Id 0 -Activity "via-realtest v0103" -Status "③ 樣本驗證 $Samples…" -PercentComplete 92
$smpLines = @(); $smpRc = -1
if (Test-Path -LiteralPath $Samples) {
    $nPdf = @(Get-ChildItem -LiteralPath $Samples -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in ".pdf", ".docx", ".txt" }).Count
    $smpLines = @(& $py $V.FullName run --family vrn VRN_ENG392_TextCompleteness run --dir $Samples 2>&1 | ForEach-Object { "" + $_ })
    $smpRc = $LASTEXITCODE
    $smpSum = @($smpLines | Where-Object { $_ -match '\[計\]|總判|verdict|完整度|COMPLETE|檔' } | Select-Object -Last 3)
    Write-Host ("  ③ 樣本驗證 · " + $Samples + " · 檔 " + $nPdf + " · rc " + $smpRc + " · " + ($smpSum -join " | ")) -ForegroundColor $(if ($smpRc -eq 0) { "Green" } elseif ($smpRc -in 2, 3, 4) { "Yellow" } else { "Red" })
    if ($smpRc -eq 1) { $Red.Add("樣本驗證 rc 1:" + ($smpSum -join " | ")) }
} else {
    $Notes.Add("樣本夾不在:" + $Samples + "(-Samples <夾> 指定)")
    Write-Host ("  ③ 樣本驗證 · 夾不在 " + $Samples) -ForegroundColor Yellow
}

# ④ 交接檢查 -----------------------------------------------------------------------------
Write-Progress -Id 0 -Activity "via-realtest v0103" -Status "④ 交接檢查…" -PercentComplete 95
$hc = @(& $py $V.FullName handoff check 2>&1 | ForEach-Object { "" + $_ })
$hcRc = $LASTEXITCODE
$hcLine = @($hc | Where-Object { $_ -match '交接防遺漏' } | Select-Object -Last 1)
$hcFind = @($hc | Where-Object { $_ -match '^\[(RED|YELLOW)\]' } | Select-Object -First 12)
Write-Host ("  ④ 交接 · rc " + $hcRc + " · " + ($hcLine -join "")) -ForegroundColor $(if ($hcRc -eq 0) { "Green" } elseif ($hcRc -eq 2) { "Yellow" } else { "Red" })

# ⑤ 交接紀錄 -----------------------------------------------------------------------------
$wsDir = Join-Path $VIA "docs\handoff\workstation"
New-Item -ItemType Directory -Force -Path $wsDir | Out-Null
$paste = Join-Path $LogDir "PASTE_TO_AI_latest.txt"
$pasteText = if ((Test-Path -LiteralPath $paste) -and (Get-Item -LiteralPath $paste).LastWriteTime -ge (Get-Date).AddHours(-3)) { Get-Content -LiteralPath $paste -Raw -Encoding UTF8 } else { "(本輪沒有 PASTE_TO_AI_latest.txt)" }
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# 工作站交接紀錄 · via-realtest v0103 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
$md.Add("")
$md.Add("- 分支 " + $branch + " · HEAD(開始)" + $headBefore + " · (拉齊後)" + (G rev-parse --short HEAD | Select-Object -Last 1))
$md.Add("- ① 拉齊:" + $syncLine)
foreach ($n in $Notes) { $md.Add("  - " + $n) }
$md.Add("- ② 三路線:VCGC 全功能串測 rc " + $vcgcRc + " · " + $vcgcLine + " · log " + $vcgcLog)
$md.Add("- ② VCGC→VDF ∥ VCGC→VRN(實測 v0101)結束碼:" + $rtRc + "(0 全綠 · 2 有發現 · 1 有紅 · 124 超時)")
$md.Add("- ⓔ 環境完整安裝:" + $installLine)
$md.Add("- ⓐ 加速模組 · 矩陣報告:" + $accLine)
$md.Add("- ⓓ 全景 AST 錨點:" + $astLine)
foreach ($a in ($sev | Select-Object -First 40)) { $md.Add("    ✖ " + $a) }
$md.Add("- ③ 樣本驗證 " + $Samples + ":rc " + $smpRc)
foreach ($l in @($smpLines | Select-Object -Last 12)) { $md.Add("    " + $l) }
$md.Add("- ④ 交接檢查:rc " + $hcRc + " · " + ($hcLine -join ""))
foreach ($l in $hcFind) { $md.Add("    " + $l) }
$md.Add("")
$md.Add("## 紅字(本支)")
if ($Red.Count) { foreach ($r in $Red) { $md.Add("- " + $r) } } else { $md.Add("- 無") }
$md.Add("")
$md.Add("## 實測全文(v0101 的「貼給 AI」整段)")
$md.Add("")
$md.Add('```')
$md.Add($pasteText.TrimEnd())
$md.Add('```')
$wsFile = Join-Path $wsDir ("WS_HANDOVER_" + $stamp + ".md")
$md -join "`n" | Set-Content -LiteralPath $wsFile -Encoding UTF8
Copy-Item -LiteralPath $wsFile -Destination (Join-Path $wsDir "WS_HANDOVER_latest.md") -Force
Write-Host ("  ⑤ 交接紀錄 · " + $wsFile) -ForegroundColor Cyan

# (E) MasterControl 總控頁同步(落後才重產;同契約測試那把尺) ----------------------------------
$mcLine = "沒跑"
$mcTest = Get-Newest (Join-Path $Reg "tests") "test_master_control_contract_v*.py"
if ($mcTest) {
    $mcPy = Join-Path ([IO.Path]::GetTempPath()) ("via_mc_sync_" + $stamp + ".py")
    @'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("mct_sync", sys.argv[1]); t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
mgr = t.load_module(t.MANAGER_PATH, "via_manager_sync"); deck = t.load_module(t.latest_deck_path(), "via_deck_sync")
page = mgr._build_page(mgr.do_list(do_print=False), deck.task_registry())
old = t.MASTER_HTML.read_text(encoding="utf-8") if t.MASTER_HTML.exists() else ""
if t.normalized_generated_page(old) == t.normalized_generated_page(page):
    print("[總控頁] SAME · 與正主一致,不動")
else:
    t.MASTER_HTML.write_text(page, encoding="utf-8", newline="\n")
    print("[總控頁] REGEN · 落後 → 已依正主重產 " + t.MASTER_HTML.name)
'@ | Set-Content -LiteralPath $mcPy -Encoding UTF8
    $mcOut = @(& $py $mcPy $mcTest.FullName 2>&1 | ForEach-Object { "" + $_ })
    $mcLine = (@($mcOut | Where-Object { $_ -match '\[總控頁\]' }) | Select-Object -Last 1)
    if (-not $mcLine) { $mcLine = "失敗:" + (($mcOut | Select-Object -Last 2) -join " | "); $Red.Add("MasterControl 總控頁同步 " + $mcLine) }
    Move-Item -LiteralPath $mcPy -Destination (Join-Path $LogDir ("via_mc_sync_" + $stamp + ".py")) -Force
}
Write-Host ("  ⓜ MasterControl 總控頁 · " + $mcLine) -ForegroundColor $(if ($mcLine -match 'SAME|REGEN') { "Green" } else { "Red" })
$md2 = Join-Path $wsDir "WS_HANDOVER_latest.md"
Add-Content -LiteralPath $wsFile -Value ("- ⓜ MasterControl 總控頁:" + $mcLine) -Encoding UTF8
Copy-Item -LiteralPath $wsFile -Destination $md2 -Force

# ⑥ 同步 GitHub ---------------------------------------------------------------------------
$pushLine = "跳過(-NoPush)"
if (-not $NoPush) {
    Write-Progress -Id 0 -Activity "via-realtest v0103" -Status "⑥ 同步 GitHub…" -PercentComplete 98
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) {
        $pushLine = "跳過:合併衝突沒解"
    } else {
        foreach ($s in $SideEffect) { if (@(Get-Porcelain | Where-Object { $_.path -eq $s -and $_.code -match 'M' }).Count) { $null = G checkout -- $s } }
        $take = @(Get-Porcelain | Where-Object { ($_.path -match $LedgerRx -or $_.path -match $HandoffRx) -and $_.path -notmatch '/VIA_Reports/' } | ForEach-Object { $_.path })
        if ($take.Count) {
            $null = G add -- @take
            $null = G commit -q -m ("workstation handover " + $stamp + ": vcgc rc " + $vcgcRc + " · realtest rc " + $rtRc + " · samples rc " + $smpRc + " · handoff rc " + $hcRc + " (ledgers append-only + docs/handoff)") -- @take
        }
        $p = @(G push origin ("HEAD:" + $branch))
        if ($LASTEXITCODE -ne 0) {
            $Notes.Add("push 被拒(遠端又動了)→ 再拉齊一次")
            $null = G fetch -q origin $branch
            $mm2 = Invoke-MergeMedic $py $V.FullName
            $p = @(G push origin ("HEAD:" + $branch))
        }
        if ($LASTEXITCODE -eq 0) { $pushLine = "已推 " + $branch + " · 提交 " + $take.Count + " 檔(帳本 + docs/handoff)· HEAD " + (G rev-parse --short HEAD | Select-Object -Last 1) }
        else { $pushLine = "推送失敗:" + (($p | Select-Object -Last 3) -join " | "); $Red.Add($pushLine) }
    }
    Write-Host ("  ⑥ 同步 GitHub · " + $pushLine) -ForegroundColor $(if ($pushLine -like "已推*") { "Green" } else { "Red" })
}
Write-Progress -Id 0 -Activity "via-realtest v0103" -Completed

# 收尾 ------------------------------------------------------------------------------------
Write-Host ""
if ($Red.Count) {
    Write-Host "  ═══════════ 紅字(拉齊 / 樣本 / 推送)═══════════" -ForegroundColor Red
    $Red | ForEach-Object { Write-Host ("  ✖ " + $_) -ForegroundColor Red }
}
$tail = @("", "[v0103] VCGC 路線:rc " + $vcgcRc + " · " + $vcgcLine, "[v0103] 全景 AST:" + $astLine, "[v0103] 環境安裝:" + $installLine, "[v0103] 加速 · 矩陣:" + $accLine, "[v0102] 拉齊:" + $syncLine, "[v0102] 樣本驗證 " + $Samples + ":rc " + $smpRc + " · " + (@($smpLines | Select-Object -Last 3) -join " | "),
          "[v0102] 交接:rc " + $hcRc + " · " + ($hcLine -join ""), "[v0102] 同步:" + $pushLine, "[v0102] 交接紀錄:" + $wsFile)
if (Test-Path -LiteralPath $paste) { Add-Content -LiteralPath $paste -Value $tail -Encoding UTF8 }
if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { try { ($pasteText.TrimEnd() + [Environment]::NewLine + ($tail -join [Environment]::NewLine)) | Set-Clipboard } catch { } }
Write-Host "  黃字整段 + v0102 四行已放進剪貼簿(Ctrl+V 貼給 AI)· 交接紀錄已寫進 docs\handoff\workstation 並同步 GitHub" -ForegroundColor Yellow
$env:VIA_FROM_VCGC = $keepFromVcgc; $env:VIA_VCGC_PUSH = $keepPush; $env:VIA_NET_CONSENT = $keepConsent
$final = if ($Red.Count -and $rtRc -ne 124) { 1 } else { $rtRc }
exit $final
