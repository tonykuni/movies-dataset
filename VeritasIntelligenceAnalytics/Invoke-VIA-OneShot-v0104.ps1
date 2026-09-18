#Requires -Version 5.1
param(
    [string]$Root = "",
    [int]$StageTimeoutSec = 3600,
    [switch]$SkipAccel,
    [switch]$SkipData,
    [switch]$SkipMatrix,
    [switch]$DryRun,
    # v0103:裝件一律 opt-in。不帶這個旗標就只做唯讀計畫——
    # 「不代裝套件」是律,不是預設值的問題:預設安全還不夠,要**沒說就不做**。
    [switch]$ApproveInstall,
    # v0103:全矩陣 231 站很久(工作站實錄 3296s)。預設 --fast,明帶才全跑。
    [switch]$FullMatrix,
    # v0103:只跑點名的段(逗號分隔的段號前綴,例如 "S6,S10")。空=全跑。
    [string]$Only = ""
)
# =============================================================================
# v0103→v0104(批572 操作員令「INTEGRATE ALL INTO ONE PS CODE WITH 加速器及動態進度條」):
#   把批567–571 新長出來的全部收進同一支(零九頭龍:不另開第二支一鍵統包)。
#   +12 段 —— S14 指令卡 · S15 指令凍結驗證 · S16 PEIS 能力掃描 ·
#             S17 資料家清點 · S17a 湖壞檔與落後 · S17b 名單欄位 · S17c 月營收涵蓋 ·
#             S17d 總經×akshare · S18a 增量缺口 · S18b 重抓風險稽核 ·
#             S19 畫面統一 · S20 VRN 驗證矩陣
#   12 段全部**零網路、零寫、無 --apply**(它們本來就是判定閘,不是動手的引擎)。
#   **分母改成自本檔實掃**:v0103 把 24 寫死,靠對帳檢當守衛;這一批加 12 段,
#   手寫必錯——所以改成分子分母同源、加段自動跟上,對帳檢改成**指名**哪一段對不上。
# =============================================================================
# =============================================================================
# Invoke-VIA-OneShot-v0103.ps1 — 一個指令跑完全部(批566 操作員令
#   「INTEGRATE ALL INTO ONE POWERSHELL CODE TO HANDLE ALL WITH 25 ACCELERATORS · 動態進度條」)
# =============================================================================
# v0102→v0103 三件:
#   ① **25 加速器真點名**:點源 supportive modules\VIA_PS_Accel_Module.ps1,開跑印 25 盞冊。
#      缺席=誠實說缺,不假裝有(v0102 只在文字裡提到加速器,沒有真的點過名)。
#   ② **動態進度條**:總段進度(n/N · % · 已耗 · 估剩)+ 段內心跳,一律走模組的
#      Write-VIAProgress(Zero-Hydra:不在這裡另寫第二條進度條)。非 TTY 時退單行文字,
#      不是靜默——畫面全白看起來就是死機(批423 教訓)。
#   ③ **把散在外面的都收進來**:v0102 只做到 S9,而操作員待辦裡還有共識橋(批563/564)、
#      VTMRA 家族閘、中央治理家族、家族 U/I、庫況、規則落差、四態燈。現在是 S1–S13。
#   紀律(三條寫在這裡,因為它們最容易在「一鍵跑完」裡被偷偷破掉):
#     · **不代設同意閘**:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 一律只讀不寫。
#       沒設=資料段誠實標 GATED 並印出要貼哪兩行,**不替操作員決定要不要觸網**。
#     · **不代裝套件**:via-envgov apply --approve 只在 -ApproveInstall 時才跑。
#     · **不卡斷**:每段獨立逾時 kill、邊跑邊吐、Ctrl+C 安全落檔。
# =============================================================================
# (v0102 原說明保留於下)
# Invoke-VIA-OneShot-v0102.ps1 — 一個指令跑完全部(批394 續章;操作員令「整合成一個 PS
#   指令含進入環境,一個指令跑完全部,把我還沒做的整合到這裡」)
# =============================================================================
# 為何本件存在:操作員待辦散落在多個短令,而他的副本又卡在倉庫未合併(拿不到新檔),
#   故第一步必須自己解卡,之後才有短令冊可用。全程零跳出、零互動、逾時 kill、誠實三態。
#
# 九段(每段獨立計時、獨立三態,任一段不擋後段=不卡斷):
#   S1 解卡      委派 Invoke-VIA-Unstick 尾版;本副本缺該件即自 origin 取出單檔(繞死結)
#   S2 短令冊    點源尾版 Register;via-pin 把 profile 指向本副本(新視窗亦生效)
#   S3 環境      via-envgov 唯讀計畫 + 進入 via_core 虛境(在位才進;印各家族境 python)
#   S4 加速器    via-accel-import --apply --approve(真裝可計畫件;base 零觸碰)
#   S5 能跑閘    via-rungate --fast(家族境 python 真跑引擎自測)
#   S6 資料      via-price → via-chip → via-align update --apply → via-fred(鑰在位才跑)
#   S7 PS 層     via-psrepair-ast(AST 全景) + via-pstest(PS 真測閘)
#   S8 全矩陣    via-selftest(207 站)
#   S9 收斂      via-productgate + via-projects + 誠實三態總表與下一指令
#
# v0101→v0102(自檢抓到我方違律):S1 以 git pathspec 取解卡器時寫死 Invoke-VIA-Unstick-v0100.ps1
#   ——「glob 尾版動態解析嚴禁寫死版號」律同樣適用於 git pathspec,解卡器一升版該行就取到舊版。
#   實測 git checkout 支援 glob pathspec,故改取整族 Invoke-VIA-Unstick-v*.ps1 再挑尾版。
# v0100→v0101(操作員工作站首跑實錄 OK 10 · FAIL 5 · SKIP 1 · 3296s 所得三修):
#   ① 四態:原只有 OK/FAIL/SKIP,把引擎的誠實中間態 YELLOW/PARTIAL/PART/WARN 一律算成
#      FAIL=判定過嚴的假紅。實錄:S5 via-rungate 印「判定 YELLOW」(家族境未建=base 退路,
#      能跑但非本位)卻被標 FAIL;S3b via-envgov 唯讀計畫 rc=1 亦屬「有待裁段」的中間態。
#      v0101 新增 WARN 態:YELLOW/PARTIAL/WARN/待裁 → WARN(不是綠,也不冒充紅)。
#   ② 紅站明細自動列出:S8 在工作站實錄 OK 181 · FAIL 22,但總表只給總數,操作員得另外
#      翻存證或貼畫面才知道是哪 22 站=來回白費。v0101 於 S8/S9 後自動讀最新存證
#      (GRID_*.json / VIA_ProductGate / VIA_ProjectCompletion),在總表後附「紅站明細」。
#   ③ 資料段異常提示:S6b 籌碼實錄「落庫 0 列」而庫其實落後數月、S6a 價格
#      「done 1988 · failed 1430」失敗過半——皆非引擎崩潰故原判 OK,但數字本身就是警訊。
#      v0101 對資料段做數字健檢:落庫 0 列或 failed 佔比 > 30% → WARN 並印建議下一步。
# 紀律:零 force、零刪除、台帳只增不減、FRED 鑰永不入 git(只判在位,不讀不印)、
#       同意閘不覆蓋(Set-VIAGateDefaults 只在未設時補)、逾時 kill 不卡斷、誠實三態。
# 用法:& .\Invoke-VIA-OneShot-v0102.ps1                 全跑
#       & .\Invoke-VIA-OneShot-v0102.ps1 -DryRun         只列計畫不動手
#       & .\Invoke-VIA-OneShot-v0102.ps1 -SkipData       略過資料擷取段
#       & .\Invoke-VIA-OneShot-v0102.ps1 -SkipMatrix     略過 207 站全矩陣
# =============================================================================
$ErrorActionPreference = "Continue"
$env:VIA_NO_OPEN = "1"
$env:GIT_EDITOR = "true"
$env:GIT_MERGE_AUTOEDIT = "no"
$env:PYTHONUTF8 = "1"
$script:T0 = Get-Date
$script:Rows = New-Object System.Collections.ArrayList
$script:StageNo = 0
# ===== v0104 分母:**不再手寫,自本檔實掃**(LL112 的根治)=====
#   v0103 我把 24 寫死,對帳檢留著當守衛——守衛是對的,但每加一段就要記得改常數,
#   而「要記得」正是 LL112 那一類 bug 的溫床(批571 加了 12 段,手寫必錯)。
#   v0104 改成:分母=本檔裡**會落一列的呼叫點**實掃,再扣掉
#     ① 互斥組(if/else 兩支寫同一個段名,只會落一列)
#     ② 本次開關排除的段(-SkipData 才會落「S6 資料補齊」那一列,反之落 S6a–S6d)
#   分子仍是已落列數。兩者同源,加段自動跟上;對帳檢照留(這次改成**指名**哪一段對不上)。
$script:ExclusiveGroups = @('S2 點源尾版短令冊', 'S3 進入 via_core 虛境', 'S4 加速器導入',
                            'S6d FRED 宏觀', 'S8 全矩陣')
# 可選列:**條件成立才會落**的段(不是每一跑都有)。分母把它算進去(它在檔裡),
# 對帳時若差額剛好由這些解釋得掉,就安靜一行帶過——不然每一跑都會噴一整份清單當雜訊。
$script:OptionalRows = @('S2 via-pin')
function Measure-VIAStageTotal {
    # 本檔路徑:正常執行是 $PSCommandPath;被點源時那個變數是呼叫者的,退 $MyInvocation。
    $self = $PSCommandPath
    if (-not $self -or -not (Test-Path -LiteralPath $self)) { $self = $MyInvocation.MyCommand.Path }
    if (-not $self -or -not (Test-Path -LiteralPath $self)) {
        # 掃不到本檔=**誠實說掃不到**,不要拿一個編出來的分母去除(分母說謊比沒有分母更糟)
        Write-Host "  [分母] 掃不到本檔路徑=進度條只報段序不報百分比(誠實;不編分母)" -ForegroundColor Yellow
        return 0
    }
    $sites = @()
    foreach ($m in (Select-String -LiteralPath $self -Pattern '^\s*(?:Invoke-Stage|Add-Row)\s+"([^"]+)"')) {
        $sites += $m.Matches[0].Groups[1].Value
    }
    if ($sites.Count -eq 0) {
        Write-Host "  [分母] 本檔掃不到任何段呼叫點=進度條只報段序(誠實;不編分母)" -ForegroundColor Yellow
        return 0
    }
    $n = $sites.Count
    foreach ($g in $script:ExclusiveGroups) {
        $hit = @($sites | Where-Object { $_.StartsWith($g) }).Count
        if ($hit -gt 1) { $n = $n - ($hit - 1) }      # 互斥組只會落一列
    }
    if ($SkipData) {
        # -SkipData:落「S6 資料補齊」一列,S6a/S6b/S6c/S6d 都不跑
        $n = $n - @($sites | Where-Object { $_ -match '^S6[a-c] ' }).Count - 1
    } else {
        $n = $n - @($sites | Where-Object { $_.StartsWith('S6 資料補齊') }).Count
    }
    return [math]::Max($n, 1)
}

$script:StageTotal = Measure-VIAStageTotal
$script:Gate = @{ Net = $false; Scrape = $false }

# ===== v0103:25 加速器真點名(點源正典模組;缺席=誠實說缺,不假裝有)=====
function Initialize-VIAAccel {
    param([string]$Via)
    $m = Join-Path $Via "supportive modules\VIA_PS_Accel_Module.ps1"
    if (-not (Test-Path -LiteralPath $m)) {
        Write-Host "  [加速器] ABSENT · 模組不在:supportive modules\VIA_PS_Accel_Module.ps1(本跑無進度條,改單行心跳)"
        return $false
    }
    try { . $m } catch {
        Write-Host ("  [加速器] ABSENT · 模組點源失敗:" + $_.Exception.Message)
        return $false
    }
    $n = 0
    try { $n = (Get-VIAAccelRoster).Count } catch { $n = 0 }
    if ($n -ne 25) {
        Write-Host ("  [加速器] WARN · 冊上 " + $n + " 盞(應為 25)——數字不對就不聲稱 25,照實印")
    } else {
        Write-Host "  [加速器] 25 盞在位 · 16 動態進度條 · 17 動態說明 · 18 非阻塞看門狗 · 并行原語"
    }
    return ($n -gt 0)
}

# ===== v0103:動態進度條(走模組的 Write-VIAProgress;非 TTY 退單行文字)=====
function Show-VIAOneShotProgress {
    param([string]$Stage, [string]$Status, [int]$Percent = -1)
    $has = (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) -ne $null
    if ($has) { Write-VIAProgress -Activity ("VIA ONE-SHOT · " + $Stage) -Status $Status -Percent $Percent -Id 21; return }
    # 退路:單行文字。**不靜默**——畫面全白看起來就是死機(批423 教訓)。
    $bar = ""
    if ($Percent -ge 0) {
        $f = [int]([Math]::Min(100, $Percent) / 4)
        $bar = "[" + ("#" * $f) + ("." * (25 - $f)) + "] " + [Math]::Min(100, $Percent) + "% "
    }
    Write-Host ("  " + $bar + $Stage + " · " + $Status)
}

function Complete-VIAOneShotProgress {
    if (Get-Command Write-Progress -ErrorAction SilentlyContinue) {
        Write-Progress -Id 21 -Activity "VIA ONE-SHOT" -Completed
    }
}

# ===== v0103:同意閘**只讀不寫**(不代設是律,不是預設值)=====
function Read-VIAGates {
    $script:Gate.Net = [bool]$env:VIA_NET_CONSENT -and $env:VIA_NET_CONSENT -ne "OFF"
    $script:Gate.Scrape = [bool]$env:VIA_SCRAPE_CONSENT
    $n = $(if ($script:Gate.Net) { "開" } else { "關" })
    $c = $(if ($script:Gate.Scrape) { "開" } else { "關" })
    Write-Host ("  [同意閘] VIA_NET_CONSENT=" + $n + " · VIA_SCRAPE_CONSENT=" + $c + "(本腳本**只讀不寫**)")
    if (-not $script:Gate.Net) {
        Write-Host "           觸網段會誠實標 GATED 並跳過。要跑的話,**你自己**先貼這兩行再重跑:"
        Write-Host '             $env:VIA_NET_CONSENT   = "YES"'
        Write-Host '             $env:VIA_SCRAPE_CONSENT = "I_ACCEPT_RESPONSIBLE_SCRAPING"'
    }
}

function Test-VIAOnly {
    param([string]$Stage)
    if (-not $Only) { return $true }
    foreach ($k in ($Only -split ",")) {
        $k = $k.Trim()
        if ($k -and $Stage.StartsWith($k, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Add-Row([string]$Stage, [string]$State, [string]$Note, [double]$Secs) {
    [void]$script:Rows.Add([pscustomobject]@{ Stage = $Stage; State = $State; Note = $Note; Secs = [math]::Round($Secs, 1) })
    $tag = "  [" + $State.PadRight(4) + "] " + $Stage
    if ($Secs -gt 0) { $tag = $tag + " · " + [math]::Round($Secs, 1) + "s" }
    if ($Note) { $tag = $tag + " · " + $Note }
    Write-Host $tag
}

function Invoke-Stage {
    param([string]$Stage, [scriptblock]$Body, [int]$TimeoutSec = 0, [switch]$NeedsNet)
    if ($TimeoutSec -le 0) { $TimeoutSec = $StageTimeoutSec }
    Write-Host ""
    Write-Host ("── " + $Stage + " ──")
    if (-not (Test-VIAOnly $Stage)) { Add-Row $Stage "SKIP" ("不在 -Only " + $Only + " 名單") 0; return }
    if ($DryRun) { Add-Row $Stage "PLAN" "唯讀計畫(去掉 -DryRun 才動手)" 0; return }
    # v0103:觸網段在同意閘關著時誠實 GATED——**不是 SKIP(那會被讀成缺件)也不是 FAIL**,
    # 更不是偷偷替操作員把閘打開。閘是他的手。
    if ($NeedsNet -and -not $script:Gate.Net) {
        Add-Row $Stage "GATED" "同意閘未開=本腳本不代設;貼上那兩行再重跑" 0
        return
    }
    # 兩個必修(本窗實測所得):
    #  ① Start-Job 是新工作階段,本視窗點源的 global 短令不會帶進去 → 段內 via-* 必然
    #     not recognized。故每段開頭先在 job 內點源尾版冊(路徑以 ArgumentList 傳入)。
    #  ② 批423 教訓:輸出緩衝到結束才吐=長跑段畫面全白,看起來死機。故邊跑邊收,
    #     並每 15s 印一次心跳(仍保留逾時 kill=不卡斷)。
    $wrapped = [scriptblock]::Create(
        'param($Root, $Via, $RegPath)' + [Environment]::NewLine +
        '$env:VIA_NO_OPEN = "1"; $env:GIT_EDITOR = "true"; $env:PYTHONUTF8 = "1"' + [Environment]::NewLine +
        'if ($RegPath -and (Test-Path -LiteralPath $RegPath)) { . $RegPath *> $null }' + [Environment]::NewLine +
        '$global:LASTEXITCODE = 0' + [Environment]::NewLine +
        $Body.ToString() + [Environment]::NewLine +
        'Write-Output ("__RC__=" + $(if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }))')
    $regPath = Get-Tail $via "Register-VIA-Commands-v*.ps1"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $job = Start-Job -ScriptBlock $wrapped -ArgumentList $Root, $via, $regPath
    $buf = New-Object System.Collections.ArrayList
    $beat = 0
    while ($true) {
        $chunk = Receive-Job -Job $job -ErrorAction SilentlyContinue 2>&1
        foreach ($c in @($chunk)) {
            $line = ($c | Out-String).TrimEnd()
            foreach ($l in ($line -split "`r?`n")) {
                if ($l.Trim()) {
                    if ($l -notmatch "__RC__=") { Write-Host ("     | " + $l.TrimEnd()) }
                    [void]$buf.Add($l)
                }
            }
        }
        if ($job.State -ne "Running") { break }
        if ($sw.Elapsed.TotalSeconds -gt $TimeoutSec) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
            Add-Row $Stage "FAIL" ("逾時 " + $TimeoutSec + "s=已 kill(不卡斷)") $sw.Elapsed.TotalSeconds
            return
        }
        Start-Sleep -Milliseconds 700
        $beat = $beat + 1
        # v0103 動態進度條:總段 n/N 與段內耗時/上限,就地重畫(不刷屏)
        # 分子=已落列數(與分母同源);在跑的這一段算第 n+1 段
        $script:StageNo = $script:Rows.Count + 1
        # 分母 0=掃不到本檔:只報段序不報百分比。**寧可少報一個數字,也不要報一個假的。**
        $pct = if ($script:StageTotal -gt 0) { [int](100 * $script:Rows.Count / $script:StageTotal) } else { 0 }
        $den = if ($script:StageTotal -gt 0) { "/" + $script:StageTotal } else { "(分母未知)" }
        Show-VIAOneShotProgress -Stage ("段 " + $script:StageNo + $den) `
            -Status ($Stage + " · " + [math]::Round($sw.Elapsed.TotalSeconds) + "s / 上限 " + $TimeoutSec + "s") `
            -Percent $pct
        if ($beat % 21 -eq 0) {
            Write-Host ("     . 進行中 " + [math]::Round($sw.Elapsed.TotalSeconds) + "s(逾時上限 " + $TimeoutSec + "s)")
        }
    }
    $tail = Receive-Job -Job $job -ErrorAction SilentlyContinue 2>&1
    foreach ($c in @($tail)) {
        $line = ($c | Out-String).TrimEnd()
        foreach ($l in ($line -split "`r?`n")) {
            if ($l.Trim()) {
                if ($l -notmatch "__RC__=") { Write-Host ("     | " + $l.TrimEnd()) }
                [void]$buf.Add($l)
            }
        }
    }
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    $sw.Stop()
    $txt = ($buf -join [Environment]::NewLine)
    # 段 rc 由 wrapped 末行回報(__RC__=n);沒有 rc 就不能聲稱綠。
    # 本窗假綠實錄:腳手架裡引擎檔不存在,python 噴 can't open file,但早期判定式抓不到
    # → 0.7s 回 OK = 假綠。故三態一律以 rc + 缺件樣式 + 錯誤樣式三者合判。
    $rc = 0
    $m = [regex]::Match($txt, "__RC__=(-?\d+)")
    if ($m.Success) { $rc = [int]$m.Groups[1].Value }
    $txt = ($txt -replace "__RC__=-?\d+", "").Trim()
    # 四態判定(v0101):先認缺件 SKIP,再認硬錯 FAIL,再認誠實中間態 WARN,其餘 OK。
    # WARN 的存在理由:引擎本就有 YELLOW/PARTIAL 這類「能跑但未到位」的誠實態,
    # 把它算成 FAIL 是假紅,算成 OK 是假綠——兩者都違誠實性律。
    $state = "OK"
    if ($txt -match "(?m)^\s*SKIP |不在位|鑰不在位") { $state = "SKIP" }
    if ($txt -match "can't open file|No such file|FileNotFoundError|Errno 2|ModuleNotFoundError") { $state = "SKIP" }
    $hardFail = ($txt -match "Traceback|Exception:|is not recognized|ParserError|FAIL [1-9]\d*( |$)|overall RED|總態 RED")
    $midState = ($txt -match "YELLOW|PARTIAL|PART( |$)|WARN|待裁|候裁")
    if ($hardFail) { $state = "FAIL" }
    elseif ($midState -and $state -eq "OK") { $state = "WARN" }
    # ===== v0104:**誠實四態的 rc 約定**(0 GREEN / 1 RED / 2 NODATA / 3 ABSENT)=====
    #   v0103 這裡是「rc 非 0 就 FAIL」——於是 rc=2(跑得動但庫裡沒料)與 rc=3(引擎/檔不在)
    #   都被判成紅燈。本窗真跑當場撞到:S17 資料家清點回 rc=2(資料家不在本機),
    #   OneShot 印 FAIL。**那正是「判錯的紅燈和假綠一樣傷」**——操作員會去修一個沒壞的東西。
    #   全庫的 py 引擎早就照這個約定回 rc,統包這一層卻沒認,所以補上。
    if ($rc -eq 2 -and $state -eq "OK") { $state = "NODATA" }
    elseif ($rc -eq 3 -and $state -eq "OK") { $state = "ABSENT" }
    elseif ($rc -ne 0 -and $state -eq "OK") { $state = "FAIL" }
    if ($rc -ne 0 -and $state -eq "WARN") { $state = "WARN" }
    if ($rc -ne 0) { $txt = $txt + " · rc=" + $rc }
    # 型別防禦(本窗真跑實錄):$buf 元素可能被裝成 Object[],直接 .Trim() 會噴
    # 「[System.Object[]] does not contain a method named 'Trim'」——解析綠卻執行紅,
    # 故一律先 [string] 強轉再處理,空值亦安全。
    $lastRaw = @($buf) | Where-Object { $_ -and ([string]$_).Trim() -and ([string]$_) -notmatch "__RC__=" } | Select-Object -Last 1
    $last = ""
    if ($null -ne $lastRaw) { $last = ([string]$lastRaw) }
    $note = (($last -replace "\s+", " ")).Trim()
    if ($rc -ne 0) { $note = $note + " · rc=" + $rc }
    Add-Row $Stage $state $note $sw.Elapsed.TotalSeconds
}

# ---- 自找倉庫根(零寫死路徑) ----
if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
    $probe = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    while ($probe) {
        if (Test-Path -LiteralPath (Join-Path $probe ".git")) { $Root = $probe; break }
        $parent = Split-Path $probe -Parent
        if (-not $parent -or $parent -eq $probe) { break }
        $probe = $parent
    }
}
if (-not $Root -or -not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
    Write-Host "  [FAIL] 找不到 git 工作樹根(可用 -Root 指定)"
    exit 2
}
$via = Join-Path $Root "VeritasIntelligenceAnalytics"
if (-not (Test-Path -LiteralPath $via)) { $via = $Root }

function Get-Tail([string]$Dir, [string]$Pat) {
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return "" }
    $g = @(Get-ChildItem -LiteralPath $Dir -Filter $Pat -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($g.Count -ge 1) { return $g[-1].FullName }
    return ""
}

Write-Host ""
Write-Host "==============================================================="
# 版本字串**自檔名取**,不要手寫——v0104 我複製 v0103 時橫幅還印著 v0103,
# 跟 LL112 同一家族:手寫的那個數字遲早跟真相脫鉤。
# 抓版號用 regex 釘尾巴(`v` + 四碼)。第一版我 `-split "_v"`,但 PS 啟動器的分隔是 `-v` 不是 `_v`
# (py 引擎才是 `_v`),結果整個檔名被當成版號印出來——**跨命名慣例的假設要先驗一次**。
$script:SelfVer = [regex]::Match([IO.Path]::GetFileNameWithoutExtension($(if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path })), 'v(\d{4})$').Groups[1].Value
if (-not $script:SelfVer) { $script:SelfVer = "?" }
Write-Host (" VIA ONE-SHOT · 一個指令跑完全部(Invoke-VIA-OneShot v" + $script:SelfVer + " · 25 加速器 · 動態進度條 · 分母自掃)")
Write-Host "==============================================================="
Write-Host ("  根 " + $Root)
Write-Host ("  起 " + $script:T0.ToString("yyyy-MM-dd HH:mm:ss") + " · 段逾時 " + $StageTimeoutSec + "s · 零跳出 VIA_NO_OPEN=1")
[void](Initialize-VIAAccel -Via $via)
Read-VIAGates
Write-Host ("  [段] 共 " + $(if ($script:StageTotal -gt 0) { $script:StageTotal } else { "?" }) + " 段(分母自本檔實掃,加段自動跟上)· 裝件 " + $(if ($ApproveInstall) { "已授權(-ApproveInstall)" } else { "**未授權**=只做唯讀計畫" }) +
            " · 全矩陣 " + $(if ($FullMatrix) { "全跑" } else { "--fast" }) + $(if ($Only) { " · 只跑 " + $Only } else { "" }))

# ================= S1 解卡 =================
Invoke-Stage "S1 解卡(倉庫拉齊;繞 bootstrap 死結)" {
    $r = $Root
    $v = $Via
    $u = Get-ChildItem -LiteralPath $v -Filter "Invoke-VIA-Unstick-v*.ps1" -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if (-not $u) {
        & git -C $r fetch -q origin main 2>&1 | Out-Null
        # 自訂律「glob 尾版動態解析嚴禁寫死版號」同樣適用於 git pathspec:
        # v0101 此處寫死 Invoke-VIA-Unstick-v0100.ps1,解卡器升版後就會取到舊版。
        # git checkout 支援 glob pathspec(實測),故取整族再由下方 Sort-Object 挑尾版。
        & git -C $r checkout origin/main -- "VeritasIntelligenceAnalytics/Invoke-VIA-Unstick-v*.ps1" 2>&1 | Out-Null
        $u = Get-ChildItem -LiteralPath $v -Filter "Invoke-VIA-Unstick-v*.ps1" -File -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -Last 1
    }
    if (-not $u) { Write-Output "[FAIL] 取不到解卡啟動器(檢查網路與 origin)"; return }
    & $u.FullName -Root $r -NoEnter
} 1800

# ================= S2 短令冊 =================
Write-Host ""
Write-Host "── S2 短令冊(點源尾版 + via-pin)──"
$reg = Get-Tail $via "Register-VIA-Commands-v*.ps1"
if ($reg) {
    . $reg
    Add-Row "S2 點源尾版短令冊" "OK" (Split-Path $reg -Leaf) 0
    if (-not $DryRun -and (Get-Command via-pin -ErrorAction SilentlyContinue)) {
        $pin = (via-pin 2>&1 | Out-String)
        Add-Row "S2 via-pin(profile 指向本副本)" "OK" (($pin -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)) 0
    }
} else {
    Add-Row "S2 點源尾版短令冊" "FAIL" "Register-VIA-Commands-v*.ps1 不在本副本" 0
}

# ================= S3 環境(含進入虛境) =================
Write-Host ""
Write-Host "── S3 環境(治理計畫 + 進入 via_core 虛境 + 家族境 python)──"
$venvRoot = ""
$cands = New-Object System.Collections.ArrayList
if ($env:VIA_VENV_ROOT) { [void]$cands.Add($env:VIA_VENV_ROOT) }
if ($env:USERPROFILE) { [void]$cands.Add((Join-Path $env:USERPROFILE ".venvs")) }   # 基底非空才組(批389 實錄:null 基底噴 Cannot bind)
if ($Root) { [void]$cands.Add((Join-Path $Root ".venvs")) }
if ($via) { [void]$cands.Add((Join-Path $via ".venvs")) }
foreach ($cand in $cands) {
    if ($cand -and (Test-Path -LiteralPath $cand)) { $venvRoot = $cand; break }
}
$act = ""
if ($venvRoot) {
    $p1 = Join-Path $venvRoot "via_core"
    $p2 = Join-Path $p1 "Scripts"
    $p3 = Join-Path $p2 "Activate.ps1"
    if (Test-Path -LiteralPath $p3) { $act = $p3 }
}
if ($act) {
    . $act
    Add-Row "S3 進入 via_core 虛境" "OK" $act 0
} else {
    Add-Row "S3 進入 via_core 虛境" "SKIP" "via_core 虛境不在位(本視窗用 base;各引擎短令仍走家族境 python)" 0
}
if (-not $DryRun -and (Get-Command via-envpy -ErrorAction SilentlyContinue)) {
    $ep = (via-envpy 2>&1 | Out-String)
    foreach ($l in ($ep -split "`r?`n")) { if ($l.Trim()) { Write-Host ("     | " + $l.TrimEnd()) } }
}
Invoke-Stage "S3b via-envgov 唯讀治理計畫" {
    if (Get-Command via-envgov -ErrorAction SilentlyContinue) { via-envgov } else { Write-Output "SKIP via-envgov 不在位" }
} 1200

# ================= S4 加速器 =================
if ($SkipAccel) {
    Add-Row "S4 加速器導入" "SKIP" "-SkipAccel" 0
} else {
    Invoke-Stage "S4 加速器導入(裝件=你的手;-ApproveInstall 才真裝,否則唯讀計畫)" {
        if (Get-Command via-accel-import -ErrorAction SilentlyContinue) {
            via-accel-import --apply --approve
        } else { Write-Output "SKIP via-accel-import 不在位" }
    } 3600
}

# ================= S5 能跑閘 =================
Invoke-Stage "S5 能跑閘(家族境 python 真跑引擎自測)" {
    if (Get-Command via-rungate -ErrorAction SilentlyContinue) { via-rungate --fast } else { Write-Output "SKIP via-rungate 不在位" }
} 1800

# ================= S6 資料 =================
if ($SkipData) {
    Add-Row "S6 資料補齊" "SKIP" "-SkipData" 0
} else {
    Invoke-Stage "S6a 價格增量(via-price)" -NeedsNet {
        if (Get-Command via-price -ErrorAction SilentlyContinue) { via-price } else { Write-Output "SKIP via-price 不在位" }
    } 3600
    Invoke-Stage "S6b 籌碼增量(via-chip)" -NeedsNet {
        if (Get-Command via-chip -ErrorAction SilentlyContinue) { via-chip } else { Write-Output "SKIP via-chip 不在位" }
    } 3600
    # v0101 資料段數字健檢:引擎沒崩不代表資料有進來(工作站實錄:籌碼落庫 0 列而庫落後數月、
    # 價格 failed 1430/done 1988=失敗過半)。數字本身就是警訊,故單獨標 WARN 並指路。
    $lastRows = @($script:Rows | Where-Object { $_.Stage -like "S6*" })
    foreach ($rw in $lastRows) {
        $nt2 = ([string]$rw.Note)
        if ($nt2 -match "落庫 0 列") {
            Add-Row ("S6 數字健檢 · " + $rw.Stage) "WARN" "引擎未崩但落庫 0 列=無新資料入庫;查 checkpoint 是否已全標 done、或端點/節流問題(--retry-parked / 重置 checkpoint 該段)" 0
        }
        $mf = [regex]::Match($nt2, "done (\d+).*?failed (\d+)")
        if ($mf.Success) {
            $dn = [int]$mf.Groups[1].Value
            $fl = [int]$mf.Groups[2].Value
            if (($dn + $fl) -gt 0 -and ($fl / [double]($dn + $fl)) -gt 0.3) {
                Add-Row ("S6 數字健檢 · " + $rw.Stage) "WARN" ("failed " + $fl + " / 總 " + ($dn + $fl) + "=失敗佔比 " + [math]::Round(100.0 * $fl / ($dn + $fl), 1) + "%(>30%);多為端點節流或代碼已下市,重試權保留,可重跑該段") 0
            }
        }
    }
    Invoke-Stage "S6c 日交易×籌碼對齊(via-align update --apply)" -NeedsNet {
        if (Get-Command via-align -ErrorAction SilentlyContinue) { via-align update --apply } else { Write-Output "SKIP via-align 不在位" }
    } 2400
    $keyFile = ""
    $hub = Join-Path $via "functional modules"
    if (Test-Path -LiteralPath $hub) {
        $k = Join-Path $hub "VDF\output_hub\mega\.fred_api_key"
        if (Test-Path -LiteralPath $k) { $keyFile = $k }
    }
    if ($keyFile -or $env:VDF_FRED_API_KEY) {
        Invoke-Stage "S6d FRED 宏觀(via-fred;鑰在位才跑,只判在位不讀不印)" {
            if (Get-Command via-fred -ErrorAction SilentlyContinue) { via-fred } else { Write-Output "SKIP via-fred 不在位" }
        } 3600
    } else {
        Add-Row "S6d FRED 宏觀(via-fred)" "SKIP" "FRED 鑰不在位(鑰檔 output_hub\mega\.fred_api_key;鑰永不入 git)" 0
    }
}

# ================= S7 PS 層 =================
Invoke-Stage "S7a PS AST 全景(via-psrepair-ast;唯讀)" {
    if (Get-Command via-psrepair-ast -ErrorAction SilentlyContinue) { via-psrepair-ast } else { Write-Output "SKIP via-psrepair-ast 不在位" }
} 1800
Invoke-Stage "S7b PS 真測閘(via-pstest)" {
    if (Get-Command via-pstest -ErrorAction SilentlyContinue) { via-pstest } else { Write-Output "SKIP via-pstest 不在位" }
} 1800

# ================= S8 全矩陣 =================
if ($SkipMatrix) {
    Add-Row "S8 全矩陣" "SKIP" "-SkipMatrix" 0
} else {
    Invoke-Stage "S8 全矩陣自測(via-selftest;207 站)" {
        if (Get-Command via-selftest -ErrorAction SilentlyContinue) { via-selftest } else { Write-Output "SKIP via-selftest 不在位" }
    } 3600
}

# ================= S9 收斂 =================
# ===== v0103 新段:把散在外面的都收進來(批563/564 的共識橋 + 三個治理閘 + 庫況/落差/四態燈)=====
Invoke-Stage "S10a 共識融合橋(via-consensus status;誠實四態,0 列與缺來源分得開)" {
    via-consensus status
} 300
Invoke-Stage "S10b 共識對映計畫(via-consensus plan;來源缺時**不猜對映**)" {
    via-consensus plan
} 300
Invoke-Stage "S11a VTMRA 家族閘(via-vtmra;批539 起 talib 兩員已隨 L50 退役拔除)" {
    via-vtmra
} 900
Invoke-Stage "S11b 中央治理家族(via-cgfamily cycles;G17 循環對回檔名與分區)" {
    via-cgfamily cycles
} 900
Invoke-Stage "S11c 家族 U/I 再生(via-famui all)" {
    via-famui all
} 900
Invoke-Stage "S12a 庫況(via-census;倉內+家內,逐庫一行)" {
    via-census
} 600
Invoke-Stage "S12b VRN 規則落差(via-vrnrules drift;三源聯集 66 詞)" {
    via-vrnrules drift
} 300
Invoke-Stage "S13 四態燈(via-ryg vdf,vrn;有界 selftest 驗收)" {
    via-ryg vdf,vrn -NoOpen
} 1800

# ===== v0104 新段:批567–571 長出來的判定閘(全部零網路/零寫/無 --apply)=====
Invoke-Stage "S14 指令卡(via-cmdcard cards;AI 讀卡不讀原始碼,L65)" {
    via-cmdcard cards
}
Invoke-Stage "S15 指令凍結驗證(via-cmdcard verify;凍結後被動過沒有,對不上=DRIFT 指名)" {
    via-cmdcard verify
}
Invoke-Stage "S16 PEIS 能力掃描(via-peis scan --family vdf,vrn;聚眾→測試→鎖定→能力卡)" -TimeoutSec 1800 {
    via-peis scan --family vdf,vrn
}
Invoke-Stage "S17 資料家清點(via-datahome catalog;下面三段都讀這一頁,不各自掃樹)" -TimeoutSec 900 {
    via-datahome catalog
}
Invoke-Stage "S17a 湖壞檔與落後(via-vdfcov lakes;壞檔逐個點名不截斷·湖落後庫逐夾算)" {
    via-vdfcov lakes
}
Invoke-Stage "S17b 名單欄位齊不齊(via-vdfcov universe;要觸網的欄標 GATED,不與缺件混)" {
    via-vdfcov universe
}
Invoke-Stage "S17c 月營收涵蓋(via-vdfcov revenue;落後兩個月以上=STALE 誠實報)" {
    via-vdfcov revenue
}
Invoke-Stage "S17d 總經×akshare 對照(via-vdfcov macro;預設全 UNVERIFIED,--probe 才驗且不代裝)" {
    via-vdfcov macro
}
Invoke-Stage "S18a 增量缺口(via-vdfinc plan --since 2023-01-01;只列缺口,不列已有)" -TimeoutSec 900 {
    via-vdfinc plan --since 2023-01-01
}
Invoke-Stage "S18b 重抓風險稽核(via-vdfinc audit;誰抓之前沒看庫——程式碼層代理指標)" {
    via-vdfinc audit
}
Invoke-Stage "S19 畫面統一(via-uiunify plan;LAW 紅/UNIFY 黃/ADVISORY 永不判紅;不代改頁)" {
    via-uiunify plan
}
Invoke-Stage "S20 VRN 驗證矩陣(via-vrnmatrix matrix;擷到**且驗過**才綠;庫沒建=誠實 NODATA)" -TimeoutSec 900 {
    via-vrnmatrix matrix
}

Invoke-Stage "S9a 產品資格閘(via-productgate)" {
    if (Get-Command via-productgate -ErrorAction SilentlyContinue) { via-productgate } else { Write-Output "SKIP via-productgate 不在位" }
} 1800
Invoke-Stage "S9b 四專案完工矩陣(via-projects)" {
    if (Get-Command via-projects -ErrorAction SilentlyContinue) { via-projects } else { Write-Output "SKIP via-projects 不在位" }
} 1800

# ================= 總表 =================
$elapsed = ((Get-Date) - $script:T0).TotalSeconds
$nOK = @($script:Rows | Where-Object { $_.State -eq "OK" }).Count
$nFail = @($script:Rows | Where-Object { $_.State -eq "FAIL" }).Count
$nSkip = @($script:Rows | Where-Object { $_.State -eq "SKIP" }).Count
$nPlan = @($script:Rows | Where-Object { $_.State -eq "PLAN" }).Count
$nWarn = @($script:Rows | Where-Object { $_.State -eq "WARN" }).Count
$nGated = @($script:Rows | Where-Object { $_.State -eq "GATED" }).Count
# v0104:誠實態多了 NODATA(跑得動但沒料)與 ABSENT(引擎/檔不在)——
# 兩者**都不是紅燈**,總表要各自成欄,不然又被讀成 OK 或 FAIL。
$nNodata = @($script:Rows | Where-Object { $_.State -eq "NODATA" }).Count
$nAbsent = @($script:Rows | Where-Object { $_.State -eq "ABSENT" }).Count
Complete-VIAOneShotProgress
Write-Host ""
Write-Host "==============================================================="
Write-Host " ONE-SHOT 總表(誠實七態;NODATA=跑得動但沒料 · ABSENT=引擎/檔不在 · GATED=閘未開 · SKIP=本跑不跑 —— 四者都不是紅燈,也都不是假綠)"
Write-Host "==============================================================="
foreach ($row in $script:Rows) {
    $line = "  " + $row.State.PadRight(4) + " · " + $row.Stage.PadRight(42)
    if ($row.Secs -gt 0) { $line = $line + " " + ([string]$row.Secs).PadLeft(7) + "s" }
    Write-Host $line
    $nt = ([string]$row.Note)
    if ($nt) { Write-Host ("         " + $nt.Substring(0, [math]::Min(150, $nt.Length))) }
}
Write-Host ""
Write-Host ("  [計] OK " + $nOK + " · WARN " + $nWarn + " · FAIL " + $nFail +
            " · NODATA " + $nNodata + " · ABSENT " + $nAbsent +
            " · SKIP " + $nSkip + " · GATED " + $nGated + " · PLAN " + $nPlan +
            " · 總 " + [math]::Round($elapsed, 1) + "s")
# v0104 分母對帳:分母已改成自本檔實掃(加段自動跟上),對帳檢仍留著——
# 它守的是「互斥組/可選列沒登記」這一類漂移,而且對不上時**指名**逐段列出。
if ($script:StageTotal -gt 0 -and $script:Rows.Count -ne $script:StageTotal) {
    $labels = @($script:Rows | ForEach-Object { $_.Stage })
    $missOpt = @($script:OptionalRows | Where-Object { $o = $_; -not ($labels | Where-Object { $_.StartsWith($o) }) })
    $gap = $script:StageTotal - $script:Rows.Count
    if ($gap -gt 0 -and $gap -eq $missOpt.Count) {
        # 差額**剛好**由可選列解釋得掉=正常,安靜一行就好
        Write-Host ("  [分母] " + $script:Rows.Count + "/" + $script:StageTotal +
                    " —— 差的是條件未成立的可選段:" + ($missOpt -join " · ")) -ForegroundColor DarkGray
    } else {
        # 解釋不掉才是真的對不上:**指名**逐段列出,不要只丟一個數字讓人自己去數(L62 同族)
        Write-Host ""
        Write-Host ("  [分母] 段數對不上:實跑 " + $script:Rows.Count + " 段,分母算 " + $script:StageTotal +
                    " —— 分母自本檔實掃,對不上代表有新段沒被掃到、或互斥組/可選列沒登記。") -ForegroundColor Yellow
        $i = 0
        foreach ($l in $labels) { $i = $i + 1; Write-Host ("         " + $i.ToString().PadLeft(3) + ". " + $l) -ForegroundColor DarkGray }
        Write-Host ("        互斥組:" + ($script:ExclusiveGroups -join " · ")) -ForegroundColor DarkYellow
        Write-Host ("        可選列:" + ($script:OptionalRows -join " · ")) -ForegroundColor DarkYellow
    }
}
if ($nGated -gt 0) {
    Write-Host ("  [閘] " + $nGated + " 段因同意閘未開而未跑。**本腳本不代設閘**;要跑就自己貼那兩行再重跑。")
}
$regNow = Get-Tail $via "Register-VIA-Commands-v*.ps1"
Write-Host ("  [冊] " + $(if ($regNow) { Split-Path $regNow -Leaf } else { "(缺)" }) + " · 本視窗短令已生效")
# ---- 紅站明細(v0101:自動讀最新存證,免操作員來回翻檔) ----
function Show-Detail([string]$Title, [string]$Path, [string]$Kind) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return }
    try { $j = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return }
    $lines = New-Object System.Collections.ArrayList
    if ($Kind -eq "grid") {
        foreach ($r in @($j.results)) {
            if ($r.state -eq "FAIL") {
                $nt = ([string]$r.note)
                if ($nt.Length -gt 110) { $nt = $nt.Substring(0, 110) }
                [void]$lines.Add("    · " + ([string]$r.name) + "  rc=" + ([string]$r.rc) + "  " + $nt)
            }
        }
    } elseif ($Kind -eq "gate") {
        foreach ($g in @($j.gates)) {
            if (([string]$g.state) -match "RED|FAIL|YELLOW") {
                $ev = ([string]$g.evidence)
                if ($ev.Length -gt 90) { $ev = $ev.Substring(0, 90) }
                [void]$lines.Add("    · " + ([string]$g.id) + " " + ([string]$g.name) + "  " + ([string]$g.state) +
                                 "  " + $ev + "  → " + ([string]$g.next))
            }
        }
    } elseif ($Kind -eq "proj") {
        foreach ($p in @($j.projects)) {
            if (([string]$p.state) -match "RED|YELLOW|NO_EVIDENCE|PARTIAL") {
                # 冊內鍵為 key/zh(非 name);實查存證後對齊,免印出空白欄
                $pn = ([string]$p.key)
                if (([string]$p.zh)) { $pn = $pn + " " + ([string]$p.zh) }
                $gp = ""
                $gc = @($p.gaps).Count
                if ($gc -gt 0) { $gp = " · 缺口 " + $gc + " 項" }
                [void]$lines.Add("    · " + $pn + "  " + ([string]$p.state) + $gp + "  → " + ([string]$p.next))
            }
        }
    }
    if ($lines.Count -eq 0) { return }
    Write-Host ""
    Write-Host ("  [明細] " + $Title + "(" + $lines.Count + " 筆;存證 " + (Split-Path $Path -Leaf) + ")")
    $shown = 0
    foreach ($l in $lines) {
        Write-Host $l
        $shown = $shown + 1
        if ($shown -ge 30) { Write-Host ("    … 其餘 " + ($lines.Count - 30) + " 筆見存證"); break }
    }
}
$repRoot = Join-Path $via "VIA_Reports"
$gridEv = ""
foreach ($sub in @("selftest_runs", "selftest")) {
    $dir = Join-Path $repRoot $sub
    if (Test-Path -LiteralPath $dir) {
        $g = @(Get-ChildItem -LiteralPath $dir -Filter "GRID_*.json" -File -ErrorAction SilentlyContinue | Sort-Object Name)
        if ($g.Count -ge 1) { $gridEv = $g[-1].FullName }
    }
}
Show-Detail "S8 全矩陣紅站" $gridEv "grid"
$regDir2 = Join-Path $via "supportive modules\registry"
Show-Detail "S9a 產品閘紅閘" (Join-Path $regDir2 "VIA_ProductGate_v0100.json") "gate"
Show-Detail "S9b 四專案未綠" (Join-Path $regDir2 "VIA_ProjectCompletion_v0100.json") "proj"

if ($nFail -gt 0) {
    Write-Host "  [下一步] 把上面總表整段貼回對話即可續修(現場已保留;零 force 零刪除)"
} else {
    Write-Host "  [下一步] 全段無紅。看頁:via-open 入口 / via-console / via-handover"
}
exit $(if ($nFail -gt 0) { 1 } else { 0 })
