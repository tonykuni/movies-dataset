# =====================================================================
# Invoke-VIA-VdfFetch-v0103.ps1 — 單一 PowerShell 啟動 VDF 擷取(含進入環境+倉庫自癒)
# 批383 操作員令「用一個 powershell 啟動 vdf 包含進入環境」
# =====================================================================
# 一貼即用(新視窗、任何目錄皆可;不需先載短令冊):
#   powershell -NoProfile -ExecutionPolicy Bypass -File "<本檔完整路徑>" -Year 2023
#   在本窗進環境並跑(之後 via-* 短令續可用):. "<本檔完整路徑>" -Year 2023
#   先小量實測:… -Year 2023 -Limit 100     只看計畫不抓:… -Dry
#
# 本腳本做七件事(全部誠實印出;零跳出;不卡斷):
#   ① 找 VIA 根(本檔所在→真 Documents(OneDrive 重導向亦認)→%USERPROFILE%\movies-dataset→Github 副本;找不到=列出試過的路徑誠實停)
#      批383 工作站實錄:庫實住 C:\Users\tonyk\OneDrive\Documents\movies-dataset\…,舊候選清單無此路→-File 報「路徑不存在」
#   ①b 倉庫自癒(批388;預設開,-NoHeal 關;批389 雲端 pwsh 真測:分叉 1/1 → merge --no-ff 成功、零衝突、兩邊提交皆在):卡未合併→merge --abort;髒樹→stash -u;落後→ff;分叉→merge --no-ff;
#      衝突→MDL143 拉齊醫生按律解(台帳聯集/同名雙物讓位遠端/再生物取遠端);零 force 零 reset --hard 零刪除
#      實錄:工作站副本曾卡未合併→merge --abort 後分叉→ff-only 永遠失敗→新短令與本腳本皆拉不到(.cmd not recognized)
#   ② 進環境=點源 Register-VIA-Commands 尾版(via-* 短令於本進程生效;批378 全域 VIA_NO_OPEN=1)
#   ③ 同意閘不覆蓋律(批408):Set-VIAGateDefaults 在位即用;缺席則「僅在未設時」補預設,操作員既設值一律尊重
#   ④ 家族環境 python(批384):Get-VIAEnvPython vdf → via_vdf_312/via_vdf…;缺=base python(誠實印)
#   ⑤ 年份旗標:VIA_HIST_SINCE=<年>-01-01 / VIA_REV_SINCE=<年>-01(MDL125 尾版步冊 hist_2023/revenue_backfill 直讀)
#   ⑥ 20 加速器點亮 → Hydra 哨兵 H1–H6(MDL134 plan;H3 進程雙頭/H5 尾版律 FAIL=誠實停不跑)
#   ⑦ 十一步資料鏈十道並行(同庫序跑=單寫者律;逾時 kill;每步終態即落 PROGRESS.json)→ lanes digest + projects digest
# 律:零 force、零刪除、引擎/冊皆 glob 尾版動態解析(永不寫死版號)、失敗誠實回非零 rc。
# =====================================================================
param(
    [string]$Year = "2023",
    [int]$Limit = 0,
    [switch]$Dry,
    [switch]$NoEnter,
    [switch]$NoHeal,
    [string]$Root = ""
)

$ErrorActionPreference = "Continue"
# 點源道安全退出:. 本檔 時 exit 會關掉操作員視窗→改 return(僅結束本腳本);-File 道維持 exit <rc>
$script:Dotted = ($MyInvocation.InvocationName -eq ".")


function Write-Step([string]$Text) { Write-Host ("--- " + $Text) -ForegroundColor Cyan }

function Resolve-VIARoot([string]$Hint) {
    $cands = @()
    if ($Hint) { $cands += $Hint }
    if ($PSScriptRoot) { $cands += $PSScriptRoot }
    # 批383:真 Documents(OneDrive 重導向=C:\Users\<你>\OneDrive\Documents)優先於猜測路徑
    # 批389 雲端 pwsh 真測實錯兩枚(真因非我首猜之 null):
    #   ① USERPROFILE 空 → 基底含空值(已改逐項非空判)
    #   ② 硬寫 "C:\Users\tonyk" 在非 Windows 上 → Join-Path 噴「Cannot find drive. A drive with the name 'C' does not exist.」
    #      → Windows 專屬基底只在 Windows 加入;兩個 Join-Path 亦包 try/catch(路徑組不出來≠腳本該噴錯)
    $bases = @()
    try { $md = [Environment]::GetFolderPath("MyDocuments"); if ($md) { $bases += $md } } catch { }
    foreach ($od in @($env:OneDrive, $env:OneDriveCommercial, $env:OneDriveConsumer)) {
        if ($od) { $bases += (Join-Path $od "Documents"); $bases += $od }
    }
    if ($env:USERPROFILE) { $bases += @($env:USERPROFILE, (Join-Path $env:USERPROFILE "Documents"), (Join-Path $env:USERPROFILE "Github")) }
    if ($env:HOME) { $bases += @($env:HOME, (Join-Path $env:HOME "Documents")) }
    if ($IsWindows -or ($env:OS -match "Windows")) { $bases += @("C:\Users\tonyk") }   # 批389:Windows 專屬基底
    foreach ($b in $bases) {
        if ($b) {
            try {
                $cands += (Join-Path $b "movies-dataset\VeritasIntelligenceAnalytics")
                $cands += (Join-Path $b "Github\movies-dataset\VeritasIntelligenceAnalytics")
            } catch { }   # 批389:跨平台路徑組不出來=略過該基底(不噴錯)
        }
    }
    $tried = @()
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            $reg = Get-ChildItem -LiteralPath $c -Filter "Register-VIA-Commands-v*.ps1" -ErrorAction SilentlyContinue
            if ($reg) { return (Get-Item -LiteralPath $c).FullName }
        }
        if ($c) { $tried += $c }
    }
    $script:TriedRoots = $tried
    return ""
}

function Get-Tail([string]$Dir, [string]$Pat) {
    $h = Get-ChildItem -LiteralPath $Dir -Filter $Pat -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($h) { return $h.FullName }
    return ""
}

# ---------------------------------------------------------------- ① VIA 根
$VIA = Resolve-VIARoot $Root
if (-not $VIA) {
    Write-Host "  [FAIL] 找不到 VIA 根(需含 Register-VIA-Commands-v*.ps1)。請加 -Root <VeritasIntelligenceAnalytics 完整路徑>" -ForegroundColor Red
    if ($script:TriedRoots) { Write-Host ("  [誠實] 已試過 " + $script:TriedRoots.Count + " 路:`n    " + ($script:TriedRoots -join "`n    ")) -ForegroundColor DarkYellow }
    if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 }
}
Write-Host ("=== [via-vdffetch] 單一 PowerShell 啟動 VDF · 根 " + $VIA + " ===") -ForegroundColor Cyan
$PYHEAL = "python"   # 自癒只用 stdlib+git,base python 足夠(家族境在 ④ 才解析)

# ---------------------------------------------------------------- ①b 倉庫自癒(批388)
if (-not $NoHeal) {
    $repo = Split-Path $VIA -Parent
    if (Test-Path -LiteralPath (Join-Path $repo ".git")) {
        $br = (git -C $repo rev-parse --abbrev-ref HEAD 2>$null); if (-not $br -or $br -eq "HEAD") { $br = "main" }
        $tgt = "origin/" + $br
        $stuck = @(git -C $repo status --porcelain 2>$null | Where-Object { $_ -match "^(UU|AA|DU|UD|AU|UA|DD) " })
        if ($stuck.Count -gt 0) {
            Write-Step ("①b 自癒:卡未合併 " + $stuck.Count + " 件 → merge --abort(回乾淨態;零刪除)")
            git -C $repo merge --abort 2>$null
            if ($LASTEXITCODE -ne 0) { git -C $repo reset --merge 2>$null }
        }
        git -C $repo fetch -q origin $br 2>$null
        $stashed = $false
        if (@(git -C $repo status --porcelain 2>$null).Count -gt 0) {
            git -C $repo stash push --include-untracked -q -m ("vdffetch-selfheal " + (Get-Date -Format "yyyyMMdd_HHmmss")) 2>$null
            if ($LASTEXITCODE -eq 0) { $stashed = $true; Write-Step "①b 自癒:工作樹有變更 → 已 stash(含未追蹤;拉齊後自動還原)" }
        }
        $cnt = (git -C $repo rev-list --left-right --count ("HEAD..." + $tgt) 2>$null)
        $ah = 0; $bh = 0
        if ($cnt -match "^\s*(\d+)\s+(\d+)") { $ah = [int]$Matches[1]; $bh = [int]$Matches[2] }
        Write-Step ("①b 自癒:分支 " + $br + " · 本地獨有 " + $ah + " · 遠端獨有 " + $bh)
        if ($bh -gt 0) {
            if ($ah -eq 0) {
                git -C $repo merge --ff-only $tgt 2>&1 | Out-Null
                Write-Step ("①b 自癒:ff 快轉 → " + (git -C $repo rev-parse --short HEAD))
            } else {
                git -C $repo -c user.name="tonykuni" -c user.email="tonyhuang0122@gmail.com" merge --no-ff --no-edit $tgt 2>&1 | Out-Null
                $cf = @(git -C $repo status --porcelain 2>$null | Where-Object { $_ -match "^(UU|AA|DU|UD|AU|UA|DD) " })
                if ($cf.Count -gt 0) {
                    $medic = (Get-ChildItem -LiteralPath (Join-Path $VIA "supportive modules\registry") -Filter "CGC_MDL143_MergeMedic_v*.py" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1)
                    if ($medic) {
                        Write-Step ("①b 自癒:分叉合併起衝突 " + $cf.Count + " 件 → 拉齊醫生按律解(台帳聯集/同名雙物讓位遠端/再生物取遠端)")
                        & $PYHEAL $medic.FullName sync --apply --branch $br --root $repo
                    } else {
                        Write-Host ("  [WARN] 衝突 " + $cf.Count + " 件且拉齊醫生缺 → 保留現場;可在該倉執行 git merge --abort(倉:" + $repo + ")") -ForegroundColor Yellow
                    }
                } else {
                    Write-Step ("①b 自癒:分叉已合併 → " + (git -C $repo rev-parse --short HEAD))
                }
            }
        }
        if ($stashed) {
            git -C $repo stash pop 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) { Write-Step "①b 自癒:stash 已原樣還原" }
            else { Write-Host "  [WARN] stash 還原衝突(誠實;stash 留存,手動 git stash pop)" -ForegroundColor Yellow }
        }
    } else {
        Write-Step "①b 自癒:非 git 工作樹=略(純解壓副本)"
    }
}

# ---------------------------------------------------------------- ② 進環境(點源短令冊尾版)
if ($env:VIA_OPEN_PAGES -ne "1") { $env:VIA_NO_OPEN = "1" }   # 批378 零跳出律(.html 預設程式=VS Code)
$env:VIA_FRED_PROMPT = "0"                                     # 並行道不問 TTY(鑰缺=SKIP 印指令)
$env:PYTHONUTF8 = "1"
$env:GIT_EDITOR = "true"
if (-not $NoEnter) {
    $reg = Get-Tail $VIA "Register-VIA-Commands-v*.ps1"
    if ($reg) {
        . $reg
        Write-Step ("② 進環境:已點源 " + (Split-Path $reg -Leaf) + "(via-* 短令於本進程生效)")
    } else {
        Write-Host "  [WARN] 短令冊缺=只跑引擎(不影響本次擷取)" -ForegroundColor Yellow
    }
}

# ---------------------------------------------------------------- ③ 同意閘不覆蓋律(批408)
if (Get-Command Set-VIAGateDefaults -ErrorAction SilentlyContinue) {
    Set-VIAGateDefaults
} else {
    if (-not $env:VIA_NET_CONSENT) { $env:VIA_NET_CONSENT = "YES" }
    if (-not $env:VIA_SCRAPE_CONSENT) { $env:VIA_SCRAPE_CONSENT = "YES" }
}
Write-Step ("③ 同意閘:NET=" + $env:VIA_NET_CONSENT + " SCRAPE=" + $env:VIA_SCRAPE_CONSENT + "(既設值一律尊重;不覆蓋)")

# ---------------------------------------------------------------- ④ 家族環境 python(批384)
$PY = "python"
if (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { $PY = Get-VIAEnvPython "vdf" }
if ($PY -eq "python") {
    Write-Step "④ python:vdf 家族境未找到=用 base python(誠實;缺套件時請 via-envgov 檢視)"
} else {
    Write-Step ("④ python:vdf 家族境 " + $PY)
}

# ---------------------------------------------------------------- ⑤ 年份旗標
if (-not ($Year -match "^\d{4}$")) { Write-Host ("  [FAIL] -Year 需四位數年份,收到:" + $Year) -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
$env:VIA_HIST_SINCE = $Year + "-01-01"
$env:VIA_REV_SINCE = $Year + "-01"
if ($Limit -gt 0) { $env:VIA_HIST_LIMIT = "" + $Limit } else { $env:VIA_HIST_LIMIT = "" }
$limTxt = if ($Limit -gt 0) { "探測上限 " + $Limit + " 檔" } else { "全市場無上限" }
Write-Step ("⑤ 年份旗標:價格史深 " + $env:VIA_HIST_SINCE + " → 今 · 月營收 " + $env:VIA_REV_SINCE + " → 今 · " + $limTxt)

# ---------------------------------------------------------------- ⑥ 加速器 + Hydra 哨兵
Write-Step "⑥ 20 加速器點亮"
$accel = Get-Tail (Join-Path $VIA "supportive modules") "SUP_MDL737_SuperAccelModule_v*.py"
if ($accel) { & $PY $accel --activate } else { Write-Host "  [加速器] 模組缺=略(graceful)" -ForegroundColor Yellow }

$lanes = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL134_ParallelLanes_v*.py"
if (-not $lanes) { Write-Host "  [FAIL] 十道並行編排引擎缺(CGC_MDL134_ParallelLanes_v*.py)" -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
Write-Step "⑥ 九頭龍哨兵 H1-H6(唯讀;H3 進程雙頭/H5 尾版律 FAIL=誠實停)"
$plan = (& $PY $lanes plan 2>&1 | Out-String)
Write-Host $plan
if ($plan -match "H3 FAIL|H5 FAIL") {
    Write-Host "=== [via-vdffetch] 九頭龍風險(見上 H3/H5)=誠實停;關閉另一條在跑的鏈或修尾版後重試 ===" -ForegroundColor Red
    if ($script:Dotted) { $global:LASTEXITCODE = 3; return } else { exit 3 }
}

# ---------------------------------------------------------------- ⑦ 十一步資料鏈十道並行
$steps = "datahome,hist_2023,global,fred,revenue_backfill,etf_universe,etf_fetch,etf_history,consensus,revenue_consensus,etf_revenue"
$argv = @($lanes, "run", "--only", $steps)
if ($Dry) { $argv += "--dry" }
Write-Step ("⑦ 資料鏈十道並行" + $(if ($Dry) { "(DRY 只印不抓)" } else { "" }) + ":hist_" + $Year + " / global / fred / 月營收 / 主動 ETF 三步 / 共識二步 / 合流")
& $PY @argv
$rc = $LASTEXITCODE

Write-Step "存證"
& $PY $lanes digest
$proj = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL131_ProjectCompletion_v*.py"
if ($proj) { & $PY $proj digest }

Write-Host ("=== [via-vdffetch] 畢 rc=" + $rc + ";看頁:via-open 架構 / via-open 竣工(零跳出律:頁只落檔)===") -ForegroundColor Cyan
if ($script:Dotted) { $global:LASTEXITCODE = $rc } else { exit $rc }
