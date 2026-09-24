# CELERITAS-TEMPLATE-JOIN v1(啟動器接法:不包裹;正主 supportive modules\ps7\VeritasCeleritas.PS7.ps1 關在動態模組裡,見下方 [VIA:CELERITAS-PS7] 與掉球 Z136)
#Requires -Version 7.0
# =====================================================================
# Invoke-VIA-VdfFetch-v0106.ps1 — 單一 PowerShell 啟動 VDF 擷取(含進入環境+倉庫自癒)
# v0105→v0106(側線 2026-09-23;工作站第一次實跑 Open-VIA-VDF,操作員「實測自測自修自完成」;v0105 留作版史 L04):
#   只換模板章的載法,其餘一字不動。v0105 的載法在工作站首載即炸(掉球 Z137 實證):正主 StrictMode 下讀還沒設的
#   $script:CeleritasPS7 → New-Module 失敗、紅字噴在視窗,「第一個錯」還印成最後一個。新載法見下方 [VIA:CELERITAS-PS7:v0101]。
#   還原本版:刪掉本檔,短令冊 newest glob 自動退回 v0105。
# v0104→v0105(側線 2026-09-23;主線批號由併線的手指定 L25;操作員「更新 VDF」):工作站 09-21 實錄——
#   先打 `via-vdffetch 2023 --limit 100`,再打 `via-vdffetch 2023` 想抓全市場,第二跑 hist_2023 仍 43 秒、庫只多幾百列:**還是 100 檔**。
#   根因:⑤ 把 $env:VIA_HIST_LIMIT 寫進本進程(視窗)後沒有還原;短令冊 via-vdffetch 沒打 --limit 時又會讀回它 → 探測上限黏在視窗裡。
#   修法只在本檔:起跑先記下 VIA_HIST_SINCE / VIA_REV_SINCE / VIA_HIST_LIMIT 三個的原值,每一個出口都還原(Restore-VIAFetchEnv);
#   你自己事先設的值照樣尊重(還原成你設的那個)。視窗原本就帶著 VIA_HIST_LIMIT 時 ⑤ 印黃字講明它從哪來、怎麼清。其餘一字不動(v0104 留作版史 L04)。
#   同版補模板章(L102,批715 令「AI 若生成 PS 檔都要加入其功能模板」;操作員 2026-09-23「許可出 v0105 依你建議執行」= L70 許可):
#   正主的 xps_join 會把整支包進 scriptblock —— param() 不再是腳本參數(-Year/-Limit 綁不上)、點源進環境的函式被關在裡面(Z136)。
#   所以改用「不包裹」接法:#Requires -Version 7.0 · 正主 VeritasCeleritas.PS7.ps1 載進動態模組(它檔頭的 Set-StrictMode 與 param 變數
#   不外洩到本檔、也不外洩到點源本檔的操作員視窗)· 每一個出口呼叫正主 Restore-CeleritasPS7(跑完即還原,不等視窗關)。
#   正主載入時自己套本行程減壓(優先權 AboveNormal · 親和性 · GC · 執行緒池 · 本執行緒文化 Invariant · 主控台 UTF-8),只動 $PID。
#   缺檔或載入失敗=略過並印一行(graceful,同加速器橋),擷取照跑。
#   還原本版:刪掉本檔,短令冊 newest glob 自動退回 v0104。
# 批383 操作員令「用一個 powershell 啟動 vdf 包含進入環境」
# =====================================================================
# 一貼即用(新視窗、任何目錄皆可;不需先載短令冊):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File "<本檔完整路徑>" -Year 2023   (v0105 起 #Requires 7:用 pwsh,不用 Windows PowerShell 5.1)
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

$ErrorActionPreference = "Continue"
# 點源道安全退出:. 本檔 時 exit 會關掉操作員視窗→改 return(僅結束本腳本);-File 道維持 exit <rc>
$script:Dotted = ($MyInvocation.InvocationName -eq ".")
# v0105:本跑前的視窗環境——跑完逐一還原(不讓 --limit / 年份旗標黏在操作員的視窗裡)
$script:VIAFetchEnvBefore = [ordered]@{}
foreach ($k in @("VIA_HIST_SINCE", "VIA_REV_SINCE", "VIA_HIST_LIMIT")) {
    $script:VIAFetchEnvBefore[$k] = [Environment]::GetEnvironmentVariable($k, "Process")
}
function Restore-VIAFetchEnv {
    foreach ($k in @($script:VIAFetchEnvBefore.Keys)) {
        [Environment]::SetEnvironmentVariable($k, $script:VIAFetchEnvBefore[$k], "Process")
    }
    # 模板章(v0105 起):正主減壓跑完即還原(正主 Restore-CeleritasPS7 依快照還原,重複呼叫無害)
    if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
}
# ===== [VIA:CELERITAS-PS7:v0101] 模板章(L102;接法:不包裹,正主關在動態模組裡)=====
# v0101 載法(工作站 2026-09-23 第一次實跑,掉球 Z137 實證):正主第 18 行開 StrictMode,第 24 行就讀還沒設的 $script:CeleritasPS7,
#   快照還讀 $OFS(預設不存在)與 $PSNativeCommandArgumentPassing(7.3 起才有)→ 首載即炸,New-Module 整個失敗、紅字噴在視窗。
#   正主是 Celeritas 線的檔(批715),側線不改它;這裡先在模組 scope 把三個變數設好,正主自己的「$null 就初始化」才走得到。
#   -RestoreOnly 只載函式、不自動起跑;先試拍快照(拍不到就不起跑),起跑另外呼叫,驗「已套且有快照」,
#   沒套上就依快照還原(失敗也拿得到模組)。
#   錯誤只記進 $Error、不噴紅字,印一行「第一個錯」。正主修好之後這幾行是無害的重複。
$script:VIACel = $null
$script:VIACelNote = "正主缺(supportive modules\ps7\VeritasCeleritas.PS7.ps1),略過"
try {
    $celFile = $null
    $celProbe = $PSScriptRoot
    while ($celProbe -and (Split-Path $celProbe -Parent)) {
        $celTry = Join-Path $celProbe "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $celTry) { $celFile = $celTry; break }
        $celProbe = Split-Path $celProbe -Parent
    }
    if ($celFile) {
        $celErr0 = $Error.Count
        $script:VIACel = New-Module -Name "VIACeleritasPS7" -ArgumentList $celFile -ErrorAction SilentlyContinue -ScriptBlock {
            param($CelFile)
            $script:CeleritasPS7 = $null
            $OFS = " "
            if (-not (Get-Variable -Name PSNativeCommandArgumentPassing -ErrorAction SilentlyContinue)) { $PSNativeCommandArgumentPassing = $null }
            $null = . $CelFile -RestoreOnly 2>$null
            Export-ModuleMember -Function Restore-CeleritasPS7
        }
        $celOn = $false
        $celSnap = $null   # 先試拍快照(唯讀、零副作用):拍不到就不起跑——正主拍快照失敗仍會照套設定,那樣就再也還原不回來
        if ($script:VIACel) { try { $celSnap = & $script:VIACel { Get-CeleritasSnapshot } 2>$null } catch { $celSnap = $null } }
        if ($script:VIACel -and ($null -ne $celSnap)) {
            try { $null = & $script:VIACel { Start-CeleritasPS7 } 2>$null } catch { }
            try { $celOn = [bool](& $script:VIACel { $script:CeleritasPS7.Applied -and ($null -ne $script:CeleritasPS7.Snapshot) } 2>$null) } catch { $celOn = $false }
            if (-not $celOn) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
        }
        $script:VIACelNote = $(if ($celOn) { "本行程減壓已套(只動本行程;跑完還原)" } else { "正主在但沒套上,略過(擷取照跑)" })
        $celNew = [Math]::Min($Error.Count - $celErr0, $Error.Count)
        if ((-not $celOn) -and ($celNew -gt 0)) { $script:VIACelNote += ";正主第一個錯:" + ("" + $Error[$celNew - 1]) }
    }
} catch {
    $script:VIACel = $null
    $script:VIACelNote = "正主載入失敗,略過(擷取照跑):" + $_.Exception.Message
}
Write-Host ("  [Celeritas] " + $script:VIACelNote) -ForegroundColor DarkGray
# ===== [VIA:CELERITAS-PS7:END] =====


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
# 批486:所有 py 指令統一走 Invoke-VIAPython(20 加速器點亮一次 + 動態進度條 + 邊跑邊轉播 + 逾時不卡斷)。
# 模組缺=誠實退回直呼(本檔照舊能跑,只是沒進度條)。
$viaPyProg = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
if (Test-Path -LiteralPath $viaPyProg) { . $viaPyProg }
else { function Invoke-VIAPython { param([string]$Family="",[string]$Python="",[int]$TimeoutSec=0,[Parameter(ValueFromRemainingArguments=$true)][object[]]$Rest) $exe = if ($Python) { $Python } else { "python" }; & $exe @Rest } }
if (-not $VIA) {
    Write-Host "  [FAIL] 找不到 VIA 根(需含 Register-VIA-Commands-v*.ps1)。請加 -Root <VeritasIntelligenceAnalytics 完整路徑>" -ForegroundColor Red
    if ($script:TriedRoots) { Write-Host ("  [誠實] 已試過 " + $script:TriedRoots.Count + " 路:`n    " + ($script:TriedRoots -join "`n    ")) -ForegroundColor DarkYellow }
    Restore-VIAFetchEnv
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
if (-not ($Year -match "^\d{4}$")) { Restore-VIAFetchEnv; Write-Host ("  [FAIL] -Year 需四位數年份,收到:" + $Year) -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
$limWas = "" + $script:VIAFetchEnvBefore["VIA_HIST_LIMIT"]
if ($limWas -match "^\d+$") {
    Write-Host ("  [注意] 本視窗原本就帶著 VIA_HIST_LIMIT=" + $limWas + "(上一次 --limit 留下的,或你自己設的);短令冊沒打 --limit 時會沿用它。要全市場:`$env:VIA_HIST_LIMIT='' 後再跑") -ForegroundColor Yellow
}
$env:VIA_HIST_SINCE = $Year + "-01-01"
$env:VIA_REV_SINCE = $Year + "-01"
if ($Limit -gt 0) { $env:VIA_HIST_LIMIT = "" + $Limit } else { $env:VIA_HIST_LIMIT = "" }
$limTxt = if ($Limit -gt 0) { "探測上限 " + $Limit + " 檔" } else { "全市場無上限" }
Write-Step ("⑤ 年份旗標:價格史深 " + $env:VIA_HIST_SINCE + " → 今 · 月營收 " + $env:VIA_REV_SINCE + " → 今 · " + $limTxt)

# ---------------------------------------------------------------- ⑥ 加速器 + Hydra 哨兵
Write-Step "⑥ 20 加速器點亮"
$accel = Get-Tail (Join-Path $VIA "supportive modules") "SUP_MDL737_SuperAccelModule_v*.py"
if ($accel) { Invoke-VIAPython -Python $PY $accel --activate } else { Write-Host "  [加速器] 模組缺=略(graceful)" -ForegroundColor Yellow }

$lanes = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL134_ParallelLanes_v*.py"
if (-not $lanes) { Restore-VIAFetchEnv; Write-Host "  [FAIL] 十道並行編排引擎缺(CGC_MDL134_ParallelLanes_v*.py)" -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
Write-Step "⑥ 九頭龍哨兵 H1-H6(唯讀;H3 進程雙頭/H5 尾版律 FAIL=誠實停)"
$plan = (Invoke-VIAPython -Python $PY $lanes plan 2>&1 | Out-String)
Write-Host $plan
if ($plan -match "H3 FAIL|H5 FAIL") {
    Restore-VIAFetchEnv
    Write-Host "=== [via-vdffetch] 九頭龍風險(見上 H3/H5)=誠實停;關閉另一條在跑的鏈或修尾版後重試 ===" -ForegroundColor Red
    if ($script:Dotted) { $global:LASTEXITCODE = 3; return } else { exit 3 }
}

# ---------------------------------------------------------------- ⑦ 十一步資料鏈十道並行
$steps = "datahome,hist_2023,global,fred,revenue_backfill,etf_universe,etf_fetch,etf_history,consensus,revenue_consensus,etf_revenue"
$argv = @($lanes, "run", "--only", $steps)
if ($Dry) { $argv += "--dry" }
Write-Step ("⑦ 資料鏈十道並行" + $(if ($Dry) { "(DRY 只印不抓)" } else { "" }) + ":hist_" + $Year + " / global / fred / 月營收 / 主動 ETF 三步 / 共識二步 / 合流")
Invoke-VIAPython -Python $PY @argv
$rc = $LASTEXITCODE

Write-Step "存證"
Invoke-VIAPython -Python $PY $lanes digest
$proj = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL131_ProjectCompletion_v*.py"
if ($proj) { Invoke-VIAPython -Python $PY $proj digest }

Restore-VIAFetchEnv
Write-Host ("=== [via-vdffetch] 畢 rc=" + $rc + " · " + $limTxt + "(視窗的 VIA_HIST_SINCE/VIA_REV_SINCE/VIA_HIST_LIMIT 已還原成本跑前的值);看頁:via-open 架構 / via-open 竣工(零跳出律:頁只落檔)===") -ForegroundColor Cyan
if ($script:Dotted) { $global:LASTEXITCODE = $rc } else { exit $rc }
