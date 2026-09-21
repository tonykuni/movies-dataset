<#
.SYNOPSIS
    VIA ALL-IN-ONE:同步 → 進環境 → 25 加速器 → 實測全系統 → 驗證產出(不卡斷)

.DESCRIPTION
    操作員令(批604):「all integrate into one ps code with 25 accelerators」。
    v0106 → v0107(批609 操作員令「SAVE ALL STATUS AND HANDOVER REPORT AUTOMATICALLY」):
    每一跑自動產 HANDOVER.md(判定/HEAD/同步/步驟表/紅的逐個點名+各自 log/產出驗證/上船清點/下一步)
    · 第 16 步上船清點(唯讀:母資料夾裡有什麼還沒進 git)。
    v0105 → v0106(批607 操作員令「優化指令省 TOKEN」):畫面濾鏡(log 永遠全、畫面才壓;
    紅字不受上限)· 全景稽核不吐 JSON(6 行摘要取代 101 列)· 全格逾時 3600→7200 且逾時要讀心跳
    講出跑到哪一站 · MDL135 的 `\e` 警告修掉(每一步都印一次的那個)。
    v0104 → v0105(批606):SYNC 段補**未追蹤件撞名清理**——工作站實錄證明
    追蹤檔清乾淨之後還是會被擋(PR #41 把 `_patches\` commit 進分支,本機同路徑是未追蹤的);
    只把撞到的那幾個移開保存到本跑存證夾,沒撞到的一根不碰。
    v0103 → v0104 加的是**第 0 段 SYNC**,因為實測三次證明真正卡住的不是引擎,是同步:

      工作站 git status -sb  →  [behind 3]
      工作樹有 41 個被改過的追蹤檔(再生的 U/I 頁與註冊表),
      其中幾支倉上這三批也動過 → git 為了不蓋掉你的修改,**拒絕合併**,
      於是 via-envgov 永遠挑到 v0108,新動詞一律掉進 print(__doc__)。

    SYNC 段的紅線(這一段會動到工作樹,所以規矩寫死在這裡):
      · 只 stash **追蹤檔**;`git stash` 不帶 -u → 你的 ?? 未追蹤件一根不碰
        (CGC_MDL148_EngineBus_v0128.py、_patches\、*.bak_b600_* 全部原地不動)
      · stash 之前先**整包複製一份**到本跑存證夾 —— 一份在 stash、一份是看得到的檔案
      · 只做 --ff-only;真的分岔就**誠實停**,不自動 merge、不 rebase、不 force
      · -NoSync 可整段跳過

.PARAMETER Families      家族清單(預設 vdf,vrn,vap)
.PARAMETER NoSync        跳過第 0 段同步
.PARAMETER SkipHeavy     跳過全格(10 步)
.PARAMETER Only          只跑步驟名含這些關鍵字的步(逗號分隔)
.PARAMETER ViaRoot       母資料夾;預設 = 本檔上一層
.PARAMETER StationTimeout 單步預設逾時秒數

.NOTES
    紅線:不代設 VIA_NET_CONSENT / 不代裝套件 / 不刪任何檔 / 不 force push。
    誠實 rc:0 綠 · 1 紅 · 2 黃(黃不是綠)。
#>
[CmdletBinding()]
param(
    [string]$Families = 'vdf,vrn,vap',
    [string]$ViaRoot,
    [string]$Only,
    [int]$StationTimeout = 900,
    [int]$GridTimeoutSec = 7200,
    [int]$MaxLines = 60,
    [switch]$NoSync,
    [switch]$SkipHeavy,
    [switch]$OpenPage,
    # 批616 操作員實錄「卡住」:13_SelftestGrid 跑了 4,394s 還沒完,而前面 12 步全綠——
    #   要看第 13 步的結果,卻得把前面 12 步再跑一次。**重跑已經綠的步驟不是測試,是罰站。**
    $From,            # 從這一步開始(名字前綴,例:-From 13)
    [switch]$Resume,  # 讀上一跑 run.json,GREEN 的略過;RED/NODATA/ABSENT 照跑
    [switch]$ProgressLines,   # 批618:強制「每 N 秒印一行」(要複製逐字稿時用;\r 重畫抓下來會有殘影)
    [int]$ProgressEverySec = 0  # 0=自動(TTY 1s / 非 TTY 30s)
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

# 不卡斷律:全域不用 Stop。單步的錯自己接,接完往下走。
$ErrorActionPreference = 'Continue'
# 批618 回歸修(我在 v0109 造的):操作員畫面上出現
#   `VIA ALL-IN-ONE v0109 [05_EnvTools 已跑 2s / 完成 4 步  ] VIA ALL-IN-ONE v0109 [已跑 3s…`
#   ——那是 **Write-Progress 的原生渲染**,每 100ms 一次;v0109 又加了我自己的進度行,
#   兩個疊在一起,在他的逐字稿裡糊成一片。**進度只能有一個出處。**
#   留我的那一條(它走 stdout,導向也看得見);原生那條關掉。
$ProgressPreference = 'SilentlyContinue'
$PSNativeCommandUseErrorActionPreference = $false
$RunStart = Get-Date
# 批616:版號從**檔名**解,不寫死。v0107→v0108 時抬頭還印 v0107,
#   操作員畫面上看到的版本與實際跑的不是同一個——跟「本視窗點的是舊冊」同族。
$SelfVer = '????'
if ([IO.Path]::GetFileNameWithoutExtension($PSCommandPath) -match 'v(\d{4})$') { $SelfVer = $Matches[1] }

function Write-Line([string]$Text, [string]$Colour = 'Gray') { Write-Host $Text -ForegroundColor $Colour }


# ── 畫面濾鏡(批607 省 TOKEN)──────────────────────────────────────────────
#   操作員令「優化指令省 TOKEN」。這一跑的證據:全景稽核 `scan --json` 吐了 101 列 JSON、
#   全格 250 站逐站刷屏、每一步開頭都印一次 SyntaxWarning ——**那些全都已經落 log 了**,
#   畫面再刷一次只是把 TOKEN 燒掉。
#   規矩:**log 永遠是全的**(一個字都不少);畫面才壓。而且壓的方式不准蓋掉紅燈——
#   純噪音直接丟,其餘照印到上限,**過了上限只留「說得出原因」的那幾行**。
$script:NoisePat = '^\s*(@@PROGRESS\||\[[█░]|[|/\-\\]\s+\[[█░])'
$script:LoudPat  = '(\[FAIL|\[錯|\[停\]|\[RED|\[TIMEOUT|Traceback|\[計\]|判定|裁決|逾時|存證)'

function Test-Noise([string]$Line, [ref]$SkipNext) {
    if ($SkipNext.Value) { $SkipNext.Value = $false; return $true }   # SyntaxWarning 的下一行是原始碼回音
    if ($Line -match 'SyntaxWarning: invalid escape sequence') { $SkipNext.Value = $true; return $true }
    if ($Line -match $script:NoisePat) { return $true }
    return $false
}

function _Unquote([string]$p) {
    $p = $p.Trim()
    if ($p.StartsWith('"') -and $p.EndsWith('"')) { $p = $p.Substring(1, $p.Length - 2) }
    $p
}

# ── 0 進母根 ───────────────────────────────────────────────────────────────
if (-not $ViaRoot) {
    $here = Split-Path -Parent $PSCommandPath
    $ViaRoot = Split-Path -Parent $here          # launchers\ 的上一層 = 母資料夾
}
if (-not (Test-Path -LiteralPath $ViaRoot -PathType Container)) {
    Write-Line "  [FAIL] 母資料夾不存在:$ViaRoot" 'Red'; exit 2
}
Set-Location -LiteralPath $ViaRoot
Write-Line "`n=== VIA ALL-IN-ONE v$SelfVer(同步 + 25 加速器 + 全系統實測)===" 'Cyan'
Write-Line "  母資料夾 : $ViaRoot"

# 本跑存證夾要先建好,SYNC 段的備份要落在裡面
$RunDir = Join-Path $ViaRoot ('VIA_Reports\accelerated_test\' + $RunStart.ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
Write-Line "  本跑存證 : $RunDir"

# ── 0.5 SYNC:把倉同步到最新(這一段是 v0104 的重點)──────────────────────
$Sync = [ordered]@{ state = 'SKIPPED'; behind = 0; ahead = 0; stashed = 0; collisions = 0; backup = ''; why = '' }
$RepoRoot = $null
if (-not $NoSync) {
    $RepoRoot = (& git -C $ViaRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $RepoRoot) {
        $Sync.state = 'ABSENT'; $Sync.why = '這裡不是 git 工作樹(或 git 不在 PATH)'
        Write-Line "  同步     : ABSENT($($Sync.why))" 'Yellow'
    } else {
        $RepoRoot = $RepoRoot.Trim()
        $Branch = (& git -C $RepoRoot rev-parse --abbrev-ref HEAD 2>$null)
        if ($Branch) { $Branch = $Branch.Trim() }
        Write-Line "`n=== 0 · 同步(分支 $Branch)===" 'Cyan'
        & git -C $RepoRoot fetch origin $Branch 2>&1 | ForEach-Object { Write-Line "    $_" 'DarkGray' }

        $counts = (& git -C $RepoRoot rev-list --left-right --count "HEAD...origin/$Branch" 2>$null)
        if ($counts) {
            $parts = @($counts -split '\s+' | Where-Object { $_ -ne '' })
            if ($parts.Count -ge 2) { $Sync.ahead = [int]$parts[0]; $Sync.behind = [int]$parts[1] }
        }
        Write-Line ("    本地領先 {0} · 落後 {1}" -f $Sync.ahead, $Sync.behind)

        if ($Sync.ahead -gt 0) {
            # 分岔 = 你這邊有我沒有的 commit。自動 merge/rebase 都可能改寫你的歷史 → 誠實停。
            $Sync.state = 'DIVERGED'
            $Sync.why = "本地領先 $($Sync.ahead) 個 commit;自動合併會動到你的歷史,這一步交給你決定"
            Write-Line "    [停] $($Sync.why)" 'Yellow'
            Write-Line "         看差異:git log --oneline origin/$Branch..HEAD" 'Yellow'
        } elseif ($Sync.behind -eq 0) {
            $Sync.state = 'UPTODATE'
            Write-Line '    已是最新,不需要動工作樹' 'Green'
        } else {
            # 落後且沒領先 → ff-only 一定能成。擋路的是工作樹裡被改過的追蹤檔。
            $dirty = @(& git -C $RepoRoot status --porcelain --untracked-files=no 2>$null |
                    Where-Object { $_ -and $_.Length -gt 3 })
            if ($dirty.Count -gt 0) {
                # 先整包複製一份看得見的備份(stash 之外的第二條退路)
                $bk = Join-Path $RunDir 'presync_backup'
                New-Item -ItemType Directory -Path $bk -Force | Out-Null
                foreach ($d in $dirty) {
                    $rel = $d.Substring(3).Trim('"')
                    if ($rel -match ' -> ') { $rel = ($rel -split ' -> ')[-1] }
                    $src = Join-Path $RepoRoot $rel
                    if (Test-Path -LiteralPath $src -PathType Leaf) {
                        $dst = Join-Path $bk $rel
                        New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
                        Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction SilentlyContinue
                    }
                }
                $Sync.backup = $bk
                $Sync.stashed = $dirty.Count
                Write-Line "    工作樹有 $($dirty.Count) 個被改過的追蹤檔(多半是再生的 U/I 頁與註冊表)" 'Yellow'
                Write-Line "    已整包備份 → $bk" 'Yellow'
                $stashName = 'VIA-AllInOne-presync-' + $RunStart.ToString('yyyyMMdd_HHmmss')
                # 不帶 -u:未追蹤件(你的 EngineBus v0128 / _patches\ / .bak_*)一根不碰
                & git -C $RepoRoot stash push -m $stashName 2>&1 | ForEach-Object { Write-Line "    $_" 'DarkGray' }
                if ($LASTEXITCODE -ne 0) {
                    $Sync.state = 'STASH_FAILED'; $Sync.why = 'git stash 失敗;工作樹沒動,同步略過'
                    Write-Line "    [停] $($Sync.why)" 'Red'
                }
                Write-Line "    要拿回來:git stash list  然後  git stash pop" 'DarkGray'
            }
            # 批606 工作站實錄:追蹤檔清乾淨之後**還是**擋住——
            #   「untracked working tree files would be overwritten by merge」。
            #   PR #41 把 `_patches\` 那幾個檔 commit 進分支了,而本機同路徑是**未追蹤**的。
            #   v0104 只處理追蹤檔、刻意不碰未追蹤件 → 方向對但**不完整**。
            #   正解:只把**撞到的那幾個**移開保存(不是刪、也不是整夾清掉),其餘一根不碰。
            $incoming = @(& git -C $RepoRoot diff --name-only --diff-filter=A HEAD "origin/$Branch" |
                    ForEach-Object { _Unquote $_ } | Where-Object { $_ })
            $untracked = @(& git -C $RepoRoot ls-files --others --exclude-standard |
                    ForEach-Object { _Unquote $_ } | Where-Object { $_ })
            $hit = @($untracked | Where-Object { $incoming -contains $_ })
            if ($hit.Count) {
                $bk2 = Join-Path $RunDir '_untracked_collisions'
                $same = 0
                foreach ($rel in $hit) {
                    $src = Join-Path $RepoRoot ($rel -replace '/', '\')
                    if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { continue }
                    $ls = (& git -C $RepoRoot hash-object -- "$rel" 2>$null)
                    $rs = (& git -C $RepoRoot rev-parse "origin/${Branch}:$rel" 2>$null)
                    if ($ls -and $rs -and $ls.Trim() -eq $rs.Trim()) { $same++ }
                    $dst = Join-Path $bk2 ($rel -replace '/', '\')
                    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
                    Move-Item -LiteralPath $src -Destination $dst -Force
                }
                $Sync.collisions = $hit.Count
                Write-Line ("    撞到 {0} 個未追蹤件(位元組相同 {1} · 不同 {2})→ 移開保存到 {3}" -f `
                        $hit.Count, $same, ($hit.Count - $same), $bk2) 'Yellow'
            }
            if ($Sync.state -ne 'STASH_FAILED') {
                & git -C $RepoRoot merge --ff-only "origin/$Branch" 2>&1 | ForEach-Object { Write-Line "    $_" 'DarkGray' }
                if ($LASTEXITCODE -eq 0) {
                    $Sync.state = 'FASTFORWARD'
                    Write-Line "    [OK] 已快轉到 origin/$Branch" 'Green'
                } else {
                    $Sync.state = 'FF_FAILED'; $Sync.why = 'ff-only 失敗(分支狀態與預期不符);不自動 merge'
                    Write-Line "    [停] $($Sync.why)" 'Red'
                }
            }
        }
        $head = (& git -C $RepoRoot log --oneline -1 2>$null)
        if ($head) { Write-Line "    HEAD     : $($head.Trim())" }
    }
}

# ── 1 指令冊(短令 + 中央 python 入口)─────────────────────────────────────
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $Register) { Write-Line '  [FAIL] 指令註冊冊缺(Register-VIA-Commands-v*.ps1)' 'Red'; exit 2 }
. $Register.FullName
Set-Location -LiteralPath $ViaRoot
Write-Line "`n  指令冊   : $($Register.Name)"

if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Line '  [FAIL] 中央 python 入口 Invoke-VIAPython 不在;禁止繞過 VIA 直呼 python(fail-closed)' 'Red'
    exit 2
}

# ── 2 加速器 25 名冊 ───────────────────────────────────────────────────────
$Roster25 = Join-Path $ViaRoot 'supportive modules\registry\VIA_PS_Accelerators_25_Roster_v0100.ps1'
$AccelCount = 0
if (Test-Path -LiteralPath $Roster25) {
    . $Roster25
    if (Get-Variable -Name VIA_PS_ACCELERATORS_25 -Scope Global -ErrorAction SilentlyContinue) {
        $global:VIA_ACCEL25 = $global:VIA_PS_ACCELERATORS_25
    } elseif (Test-Path variable:VIA_PS_ACCELERATORS_25) {
        $global:VIA_ACCEL25 = $VIA_PS_ACCELERATORS_25
    }
    if ($global:VIA_ACCEL25) { $AccelCount = @($global:VIA_ACCEL25.Keys).Count }
}
if ($AccelCount -eq 25) {
    Write-Line "  加速器   : 25/25 已點亮(名冊 VIA_PS_Accelerators_25_Roster_v0100.ps1)" 'Green'
} else {
    # 名冊不對是治理問題,不是「今天不准跑實測」的理由 → WARN 不 throw
    Write-Line "  加速器   : **$AccelCount/25**(名冊對不上;實測照跑,這一條另案處理)" 'Yellow'
}

# ── 3 進環境(每一家族先解析本位解譯器)─────────────────────────────────
$FamList = @($Families.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
$PyOf = @{}
$EnvFallback = @()
foreach ($f in (@('core') + $FamList | Select-Object -Unique)) {
    $p = Get-VIAEnvPython $f
    $PyOf[$f] = $p
    if ($p -eq 'python' -or -not (Test-Path -LiteralPath $p -PathType Leaf)) {
        $EnvFallback += $f
        Write-Line "  環境 $f   : **base 退路**(家族境未見;能跑 ≠ 在本位跑)" 'Yellow'
    } else {
        Write-Line "  環境 $f   : $p" 'Green'
    }
}
if ($EnvFallback.Count) {
    Write-Line "  [提醒] 這些家族沒有本位環境:$($EnvFallback -join ',') → 建境:via-envgov apply --approve" 'Yellow'
}

$Rows = [System.Collections.Generic.List[object]]::new()

function Get-Newest([string]$Folder, [string]$Pattern) {
    $d = Join-Path $ViaRoot $Folder
    if (-not (Test-Path -LiteralPath $d -PathType Container)) { return $null }
    $f = Get-ChildItem -LiteralPath $d -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($f) { return $f.FullName } else { return $null }
}

# ── 4 一步 = 一個子行程;逾時只殺自己生的那個;失敗照樣往下 ───────────────
# ── 批616:-Resume 讀上一跑 ──────────────────────────────────────────────────
#   上一跑的 run.json 在 VIA_Reports\accelerated_test\<ts>\run.json;取最新那一份。
#   **只沿用 GREEN**:RED / NODATA / ABSENT / 逾時 一律重跑——沿用紅燈等於把紅燈藏起來。
$PrevGreen = @{}
if ($Resume) {
    try {
        $acc = Join-Path $ViaRoot 'VIA_Reports\accelerated_test'
        # 自審(LL133 同族):本跑的存證夾**在這之前就建好了**,不排掉的話
        #   `Select-Object -Last 1` 會挑到自己那個空夾,然後回報「上一跑沒有 run.json」。
        #   工具讀自己的輸出當輸入,永遠是錯的。
        $selfDir = Split-Path $RunDir -Leaf
        $last = Get-ChildItem -LiteralPath $acc -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -ne $selfDir } |
                Sort-Object Name | Select-Object -Last 1
        if ($last) {
            $rj = Join-Path $last.FullName 'run.json'
            if (Test-Path -LiteralPath $rj) {
                $prevRun = Get-Content -LiteralPath $rj -Raw -Encoding UTF8 | ConvertFrom-Json
                # 自審:第一版寫 `$prevRun.rows`——那是我腦中的形狀,不是檔案的形狀。
                #   run.json 的鍵是 `steps`。**假設欄位名等於沒讀過那個檔。**
                foreach ($r in $prevRun.steps) {
                    if ($r.State -eq 'GREEN') { $PrevGreen[$r.Step] = $last.Name }
                }
                Write-Line "[Resume] 沿用上一跑 $($last.Name) 的 GREEN $($PrevGreen.Count) 步;其餘照跑" 'Green'
            } else { Write-Line "[Resume] 上一跑沒有 run.json → 全部照跑(誠實)" 'DarkYellow' }
        } else { Write-Line "[Resume] 找不到上一跑 → 全部照跑(誠實)" 'DarkYellow' }
    } catch {
        Write-Line "[Resume] 讀上一跑失敗:$($_.Exception.Message) → 全部照跑(誠實)" 'DarkYellow'
    }
}

# ── 批617:看得見的進度條(操作員第三次提同一件事)────────────────────────
#   他要「動態進度條 百分比」,我前兩次都回「已經有了」——**那是我沒看懂他在看什麼**。
#   v0108 用的是 `Write-Progress`,它寫到 host 的**進度 UI 通道**;
#   一旦輸出被導向/被複製成逐字稿(他每次貼回來的就是那個),那個通道**完全看不見**。
#   於是第 13 步沉默 4,394 秒,畫面上一個字都沒有——**那就是他說的「卡住」**。
#   格子明明每站都寫 SELFTEST_PROGRESS.json 心跳(批423),只是從來沒人去讀它。
$script:LastProg = [datetime]::MinValue
$script:LastProgLen = 0
$script:ProgTty = -not [Console]::IsOutputRedirected
$script:TotalSteps = 15

function Get-InnerHeartbeat {
    # 長步驟的內層進度:格子每站落一次心跳。讀不到就誠實說讀不到,不卡住。
    # 自審:第一版這裡寫成 Python 風的 """docstring""" ——在 PowerShell 裡那是
    #   **字串運算式**,會被當成函式輸出送進管線,回傳值就變成 [字串, 物件] 兩個東西。
    #   AST 檢查過得去,因為它語法上完全合法。註解才是註解。
    try {
        $hb = Join-Path $ViaRoot 'VIA_Reports\selftest_runs\SELFTEST_PROGRESS.json'
        if (-not (Test-Path -LiteralPath $hb)) { return $null }
        $j = Get-Content -LiteralPath $hb -Raw -Encoding UTF8 | ConvertFrom-Json
        $beat = [datetime]::Parse($j.heartbeat)
        $age = ((Get-Date) - $beat).TotalSeconds
        return [pscustomobject]@{ Done = [int]$j.done; Total = [int]$j.total; Eta = [int]$j.eta_s
                                  Ok = [int]$j.ok; Fail = [int]$j.fail; State = [string]$j.state
                                  Age = [int]$age; Cur = [string]$j.current; Beat = $beat }
    } catch { return $null }
}

function Write-ProgLine {
    param([string]$Name, [double]$Elapsed, [int]$Timeout, [datetime]$Since, [switch]$Force)
    # 節流:TTY 每 1s 重畫;非 TTY 每 30s 印一行(逐字稿要看得出還活著,又不能洗版)
    if ($ProgressLines) { $script:ProgTty = $false }        # 批618:強制行模式
    $gap = if ($ProgressEverySec -gt 0) { $ProgressEverySec } elseif ($script:ProgTty) { 1 } else { 30 }
    if (-not $Force -and ((Get-Date) - $script:LastProg).TotalSeconds -lt $gap) { return }
    $script:LastProg = Get-Date
    $stepNo = $Rows.Count + 1
    $pctStep = if ($Timeout -gt 0) { [math]::Min(100, [int](100.0 * $Elapsed / $Timeout)) } else { 0 }
    $hb = Get-InnerHeartbeat
    # 自審:第一版總進度只看「跑完幾步」,於是內層已經 57% 而總條還停在 0%——
    #   讀起來仍然像沒動,跟原本的問題一模一樣。本步跑到哪也是進度,要併進去。
    $frac = 0.0
    # 自審(LL179 第三次):心跳「很新」不等於「是本步寫的」。
    #   實測:上一跑剛結束的 252/252 心跳還只有幾秒大,於是本步一開跑就顯示 100%。
    #   判準改成**這一步開始之後才寫的**才算數——時間新不代表出處對。
    $hbMine = ($null -ne $hb -and $hb.Total -gt 0 -and $hb.Age -le 120 -and $hb.Beat -ge $Since)
    if ($hbMine) { $frac = [double]$hb.Done / $hb.Total }
    elseif ($Timeout -gt 0) { $frac = [math]::Min(0.9, $Elapsed / $Timeout) }   # 沒心跳就用時間當粗估,封頂 0.9 不假裝快做完
    $pctAll = [math]::Min(100, [int](100.0 * (($stepNo - 1) + $frac) / $script:TotalSteps))
    $bar = ('#' * [int]($pctAll / 5)).PadRight(20, '.')
    $txt = "[{0}] {1,3}%  步 {2}/{3} {4}  已跑 {5:N0}s/{6}s({7}%)" -f `
           $bar, $pctAll, $stepNo, $script:TotalSteps, $Name, $Elapsed, $Timeout, $pctStep
    if ($null -ne $hb -and $hb.Total -gt 0) {
        if ($hbMine) {
            $ip = [int](100.0 * $hb.Done / $hb.Total)
            $txt += "  ·  內層 {0}/{1}({2}%) OK {3} FAIL {4} ETA {5}s" -f `
                    $hb.Done, $hb.Total, $ip, $hb.Ok, $hb.Fail, $hb.Eta
        } elseif ($hb.Beat -lt $Since) {
            $txt += "  ·  內層心跳是本步**開始之前**寫的(上一跑留下的),不採用"
        } else {
            $txt += "  ·  內層心跳 {0}s 沒更新(可能不是本步在寫)" -f $hb.Age
        }
    }
    if ($script:ProgTty) {
        # 批618:只補到「比上一次長一點」就好,不再 PadRight 到整行寬——
        #   填滿整行是逐字稿裡那一長串空白與 `]` 殘影的來源。
        $w = 200; try { $w = [Console]::WindowWidth - 1 } catch { }
        if ($txt.Length -gt $w) { $txt = $txt.Substring(0, $w) }
        $pad = [math]::Max($txt.Length, $script:LastProgLen)
        [Console]::Write("`r" + $txt.PadRight($pad))
        $script:LastProgLen = $txt.Length
    } else {
        Write-Host "    $txt" -ForegroundColor DarkCyan
    }
}

function Complete-ProgLine {
    if ($script:ProgTty) { try { [Console]::Write("`r" + (' ' * ([Console]::WindowWidth - 1)) + "`r") } catch { } }
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$Family,
        [string]$Folder,
        [string]$Pattern,
        [string[]]$Arguments = @(),
        [int]$TimeoutSec = 0
    )
    if ($Only) {
        $keys = @($Only.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
        if (-not ($keys | Where-Object { $Name.ToLower().Contains($_) })) { return }
    }
    # 批616:略過的步驟**要留一列**,不是消失——表上少一行,看的人會以為它跑過了
    if ($From -and ([string]$Name) -lt ([string]$From)) {
        Write-Line "`n=== $Name / $Family === SKIPPED(-From $From)" 'DarkGray'
        $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = 'SKIPPED'; ExitCode = $null
                Seconds = 0; Why = "-From $From 之前,本跑沒跑=沒有結論"; Log = '' })
        return
    }
    if ($Resume -and $PrevGreen.ContainsKey($Name)) {
        Write-Line "`n=== $Name / $Family === SKIPPED(-Resume;上一跑 GREEN)" 'DarkGray'
        $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = 'SKIPPED'; ExitCode = $null
                Seconds = 0; Why = "上一跑 GREEN($($PrevGreen[$Name]))=沿用,未重跑"; Log = '' })
        return
    }
    $target = Get-Newest $Folder $Pattern
    if (-not $target) {
        Write-Line "`n=== $Name / $Family === ABSENT(找不到 $Pattern)" 'DarkYellow'
        $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = 'ABSENT'; ExitCode = $null
                Seconds = 0; Why = "引擎缺:$Pattern"; Log = '' })
        return
    }
    $timeout = if ($TimeoutSec -gt 0) { $TimeoutSec } else { $StationTimeout }
    $py = $PyOf[$Family]; if (-not $py) { $py = Get-VIAEnvPython $Family; $PyOf[$Family] = $py }
    $log = Join-Path $RunDir ($Name + '.log')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $stepStart = Get-Date          # 批617:心跳要比這個時間新才算是本步寫的
    Write-Line "`n=== $Name / $Family === (逾時 ${timeout}s)" 'Cyan'
    Write-Line "    引擎 $(Split-Path $target -Leaf) $($Arguments -join ' ')" 'DarkGray'

    $state = 'RED'; $code = $null; $why = ''
    $lines = [System.Collections.Generic.List[string]]::new()
    $shown = 0; $hidden = 0; $noise = 0; $loud = 0; $skipNext = $false
    try {
        $info = [System.Diagnostics.ProcessStartInfo]::new()
        $info.FileName = $py
        $info.WorkingDirectory = $ViaRoot
        $info.UseShellExecute = $false
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $info.Environment['PYTHONUTF8'] = '1'
        $info.Environment['PYTHONUNBUFFERED'] = '1'
        if (Test-Path -LiteralPath $py -PathType Leaf) {
            $info.Environment['PATH'] = (Split-Path $py -Parent) + ';' + $env:PATH
            $info.Environment['VIRTUAL_ENV'] = Split-Path (Split-Path $py -Parent) -Parent
        }
        foreach ($a in (@('-u', $target) + $Arguments)) { $info.ArgumentList.Add([string]$a) }
        $proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $info
        if (-not $proc.Start()) { throw '子行程啟動失敗' }
        $streams = @($proc.StandardOutput, $proc.StandardError)
        $tasks = @($streams[0].ReadLineAsync(), $streams[1].ReadLineAsync())
        $killed = $false
        while (-not $proc.HasExited -or $null -ne $tasks[0] -or $null -ne $tasks[1]) {
            for ($i = 0; $i -lt 2; $i++) {
                if ($null -ne $tasks[$i] -and $tasks[$i].IsCompleted) {
                    $line = $tasks[$i].GetAwaiter().GetResult()
                    if ($null -eq $line) { $tasks[$i] = $null }
                    else {
                        $lines.Add($line)
                        Add-Content -LiteralPath $log -Value $line -Encoding utf8   # log 永遠是全的
                        if (-not (Test-Noise $line ([ref]$skipNext))) {
                            if ($shown -lt $MaxLines) { Write-Host $line; $shown++ }
                            elseif ($line -match $script:LoudPat) { Write-Host $line; $loud++ }
                            else { $hidden++ }
                        } else { $noise++ }
                        $tasks[$i] = $streams[$i].ReadLineAsync()
                    }
                }
            }
            # 不卡斷:過了死線就只殺自己生的那個子行程,別的步驟照跑
            if (-not $killed -and $timer.Elapsed.TotalSeconds -gt $timeout) {
                $killed = $true
                try { $proc.Kill($true) } catch { }
                Write-Line "    [TIMEOUT] 超過 ${timeout}s,殺掉本步子行程,繼續下一步" 'Red'
            }
            Write-Progress -Activity "VIA ALL-IN-ONE v$SelfVer" `
                -Status ("$Name 已跑 {0:N0}s / 完成 {1} 步" -f $timer.Elapsed.TotalSeconds, $Rows.Count)
            # 批617:同一份資訊也走 **stdout**——Write-Progress 在導向時看不見
            Write-ProgLine -Name $Name -Elapsed $timer.Elapsed.TotalSeconds -Timeout $timeout -Since $stepStart
            Start-Sleep -Milliseconds 100
        }
        $code = $proc.ExitCode
        $proc.Dispose()
        Complete-ProgLine
        if ($killed) {
            $state = 'TIMEOUT'; $why = "逾時 ${timeout}s"
            # 批607:格子每站落一次心跳。逾時只說「逾時」等於把已經跑完的 N 站丟掉——
            #   讀 SELFTEST_PROGRESS.json 把「跑到哪一站、綠幾紅幾」講出來。
            $hb = Join-Path $ViaRoot 'VIA_Reports\selftest_runs\SELFTEST_PROGRESS.json'
            if (Test-Path -LiteralPath $hb -PathType Leaf) {
                try {
                    $j = Get-Content -LiteralPath $hb -Raw -Encoding utf8 | ConvertFrom-Json
                    $why += (" · 心跳:{0}/{1} 站 · OK {2} FAIL {3} · 最後 {4}" -f `
                            $j.done, $j.total, $j.ok, $j.fail, $j.current)
                } catch { }
            }
        }
        else {
            # 誠實多態:0 綠 · 2 缺料 · 3 缺件 · 4 閘未開 · 其餘紅
            switch ($code) {
                0 { $state = 'GREEN' }
                2 { $state = 'NODATA'; $why = '引擎自述缺料(不是壞掉)' }
                3 { $state = 'ABSENT'; $why = '引擎自述缺件' }
                4 { $state = 'GATED'; $why = '同意閘未開(要跑=你開閘)' }
                default { $state = 'RED'; $why = "rc=$code" }
            }
        }
    } catch {
        $state = 'RED'; $why = $_.Exception.Message
        Write-Line "    [EXC] $why" 'Red'
    }
    # 批603 L81/LL160 同律:紅的時候要指得出哪一檢紅,不能只給最後兩行
    if ($state -in @('RED', 'TIMEOUT')) {
        $bad = @($lines | Where-Object { $_.TrimStart().StartsWith('[FAIL') -or $_.TrimStart().StartsWith('[錯') })
        if ($bad.Count) { $why = ($why + ' · ' + (($bad | Select-Object -First 2) -join ' / ')).Trim(' ·') }
    }
    if ($EnvFallback -contains $Family) { $why = ($why + ' · ENV_FALLBACK(非本位環境)').Trim(' ·') }
    if ($hidden -or $noise) {
        Write-Line ("    …畫面壓了 {0} 行(另濾噪音 {1} 行;紅字 {2} 行照印)· 全文在 {3}" -f `
                $hidden, $noise, $loud, (Split-Path $log -Leaf)) 'DarkGray'
    }
    $colour = switch ($state) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'TIMEOUT' { 'Red' } default { 'Yellow' } }
    Write-Line ("    → {0}  {1:N1}s  {2}" -f $state, $timer.Elapsed.TotalSeconds, $why) $colour
    $Rows.Add([pscustomobject]@{ Step = $Name; Family = $Family; State = $state; ExitCode = $code
            Seconds = [math]::Round($timer.Elapsed.TotalSeconds, 1); Why = $why; Log = $log })
    $Rows | Export-Csv (Join-Path $RunDir 'summary.csv') -NoTypeInformation -Encoding utf8BOM
}

# ── 5 實測全部系統 ─────────────────────────────────────────────────────────
$REG = 'supportive modules\registry'
Invoke-Step '01_Accel_Core'    'core' 'supportive modules'        'SUP_MDL737_SuperAccelModule_v*.py'        @('--selftest') 300
Invoke-Step '02_Net_Canon'     'vdf'  'supportive modules\network' 'SUP_MDL740_NetUnified_v*.py'             @('--selftest') 300
Invoke-Step '03_AccelControl'  'core' $REG 'CGC_MDL156_VIAAcceleratorControl_v*.py'                          @('--selftest') 600
Invoke-Step '04_EnvRunGate'    'vrn'  $REG 'CGC_MDL137_RunGate_v*.py'                @('run', '--fast', '--family', $Families) 900
Invoke-Step '05_EnvTools'      'core' $REG 'CGC_MDL135_EnvGovernance_v*.py'          @('tools') 900
Invoke-Step '06_EnvPlan'       'core' $REG 'CGC_MDL135_EnvGovernance_v*.py'          @('plan', '--offline') 1200
Invoke-Step '07_EnvResume'     'core' $REG 'CGC_MDL135_EnvGovernance_v*.py'          @('resume') 300
Invoke-Step '08_RegistrySync'  'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('registry-sync', '--apply') 600
Invoke-Step '09_GovAudit'      'core' $REG 'CGC_MDL164_GovernanceCompletenessAudit_v*.py'                    @('--selftest') 900
Invoke-Step '10_UIUnifyGate'   'core' $REG 'CGC_MDL160_UIUnifyGate_v*.py'                                    @('--selftest') 900
# 批607:`--json` 會把 101 列問題全吐到畫面,而同一份 JSON 本來就落在 VIA_Reports\panorama_audit。
#   不帶 --json 是 6 行摘要 —— 一樣的資訊密度,少掉幾百行。
Invoke-Step '11_PanoramaScan'  'core' $REG 'CGC_MDL158_VIAPanoramaAuditRepair_v*.py'          @('scan') 900
Invoke-Step '12_MatrixConsole' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('matrix', '--family', $Families) 3600
if (-not $SkipHeavy) {
    # 批607 工作站實錄:全格在工作站跑 2314s(平行)+ 第二段序跑複判,**整段超過 3600s 被殺**,
    #   一整跑的結果跟著沒了。本容器 292s、工作站 2314s —— 差 8 倍,3600 是拿我的錶去量他的路。
    Invoke-Step '13_SelftestGrid' 'core' $REG 'CGC_MDL064_SelftestGrid_v*.py'                  @() $GridTimeoutSec
}
Invoke-Step '14_Handover'      'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('page') 600
Invoke-Step '15_ApprovalCheck' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('check') 600

# ── 16 上船清點(批609;唯讀)────────────────────────────────────────────────
#   操作員令 AUTO-CONSOLIDATE / AUTO SYNC。同步只做 pull 那一半;
#   另一半是「母資料夾裡有什麼還沒進 git」——每一跑都把它浮出來,
#   **但只清點不動**(要上船是 via-sync -Onboard -Commit,他的手)。
$Onb = [ordered]@{ state = 'SKIPPED'; take = 0; regen = 0; temp = 0; items = @() }
if (-not $NoSync -and $RepoRoot) {
    $RegenPat = '(^VeritasIntelligenceAnalytics/VIA_Reports/|/ui_support/VIA_UI_.*\.html$|/registry/VIA_(Engine_|Schema_|Unified_Register|IndustryUnifiedMap|SSOT_RegexDict|ProjectCompletion|ParallelLanes|VDFArchitecture))'
    $TempPat = '(\.bak_|\.tmp$|__pycache__|~$|/_patches/|\.orig$|\.rej$)'
    $all = @()
    foreach ($r in @(& git -C $RepoRoot ls-files --others --exclude-standard | ForEach-Object { _Unquote $_ } | Where-Object { $_ })) {
        $all += [pscustomobject]@{ st = '未追蹤'; rel = $r }
    }
    foreach ($d in @(& git -C $RepoRoot status --porcelain --untracked-files=no | Where-Object { $_ -and $_.Length -gt 3 })) {
        $r = _Unquote $d.Substring(3); if ($r -match ' -> ') { $r = ($r -split ' -> ')[-1] }
        $all += [pscustomobject]@{ st = '已改'; rel = $r }
    }
    foreach ($x in $all) {
        $cls = if ($x.rel -match $TempPat) { '暫存' } elseif ($x.rel -match $RegenPat) { '再生物' } else { '該上船' }
        $Onb.items += [pscustomobject]@{ 狀態 = $x.st; 類 = $cls; 路徑 = $x.rel }
    }
    $Onb.take = @($Onb.items | Where-Object { $_.類 -eq '該上船' }).Count
    $Onb.regen = @($Onb.items | Where-Object { $_.類 -eq '再生物' }).Count
    $Onb.temp = @($Onb.items | Where-Object { $_.類 -eq '暫存' }).Count
    $Onb.state = if ($Onb.take) { 'PENDING' } else { 'CLEAN' }
    Write-Line "`n=== 16_Onboard(唯讀)=== 該上船 $($Onb.take) · 再生物 $($Onb.regen) · 暫存 $($Onb.temp)" 'Cyan'
    foreach ($x in @($Onb.items | Where-Object { $_.類 -eq '該上船' } | Select-Object -First 20)) {
        Write-Line ("    {0}  {1}" -f $x.狀態, $x.路徑) 'Yellow'
    }
    if ($Onb.take -gt 20) { Write-Line "    …另 $($Onb.take - 20) 件(全表在 HANDOVER.md)" 'DarkGray' }
    if ($Onb.take) { Write-Line "    要上船(你的手):via-sync -Onboard -Commit [-Push]" 'DarkGray' }
}
Write-Progress -Activity "VIA ALL-IN-ONE v$SelfVer" -Completed

# ── 6 驗證:產出**存在**而且**是這一跑產的** ───────────────────────────────
# 舊檔還在不等於這一跑產出了東西——那是假綠最常見的入口。
$Expect = @(
    @{ Name = '矩陣控制台一頁'; Path = 'VIA_Reports\vcgc\VIA_UI_MatrixControl_v0100.html' },
    @{ Name = '一頁交接';       Path = 'VIA_Reports\vcgc\VIA_UI_CentralGovernanceConsole_v0100.html' },
    @{ Name = '加速器控制面';   Path = 'VIA_Reports\accelerator\VIA_ACCELERATOR_CONTROL_latest.json' },
    @{ Name = '工具導入計畫';   Path = 'VIA_Reports\env_governance\TOOLS_PLAN_latest.ps1' },
    @{ Name = '全景稽核存證';   Path = 'VIA_Reports\panorama_audit'; Glob = '*.json' },
    @{ Name = '自測格存證';     Path = 'VIA_Reports\selftest_runs'; Glob = 'GRID_*.json' },
    @{ Name = '能跑閘存證';     Path = 'VIA_Reports\rungate'; Glob = '*.json' }
)
$Verify = [System.Collections.Generic.List[object]]::new()
foreach ($e in $Expect) {
    $full = Join-Path $ViaRoot $e.Path
    $item = $null
    if ($e.ContainsKey('Glob')) {
        if (Test-Path -LiteralPath $full -PathType Container) {
            $item = Get-ChildItem -LiteralPath $full -Filter $e.Glob -File -Recurse -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime | Select-Object -Last 1
        }
    } elseif (Test-Path -LiteralPath $full -PathType Leaf) {
        $item = Get-Item -LiteralPath $full
    }
    if (-not $item) {
        $st = 'MISSING'; $when = ''
    } elseif ($item.LastWriteTime -ge $RunStart) {
        $st = 'FRESH'; $when = $item.LastWriteTime.ToString('HH:mm:ss')
    } else {
        $st = 'STALE'; $when = $item.LastWriteTime.ToString('yyyy-MM-dd HH:mm')
    }
    $Verify.Add([pscustomobject]@{ 產出 = $e.Name; 狀態 = $st; 時間 = $when
            路徑 = $(if ($item) { $item.FullName } else { $full }) })
}
$Verify | Export-Csv (Join-Path $RunDir 'verify.csv') -NoTypeInformation -Encoding utf8BOM

# ── 7 總表 ─────────────────────────────────────────────────────────────────
$tally = @{}
foreach ($r in $Rows) { $tally[$r.State] = 1 + [int]$tally[$r.State] }
$bad = @($Rows | Where-Object { $_.State -in @('RED', 'TIMEOUT') })
Write-Line "`n=== 實測總表 ===" 'Cyan'
$Rows | Format-Table Step, Family, State, ExitCode, Seconds, Why -AutoSize | Out-Host
Write-Line "=== 產出驗證(FRESH=這一跑產的 · STALE=舊檔還在但這跑沒產 · MISSING=根本沒有)===" 'Cyan'
$Verify | Format-Table 產出, 狀態, 時間 -AutoSize | Out-Host

# 同步沒成功 = 你跑的可能不是最新版 → 至少黃,不准綠
$syncBad = $Sync.state -in @('DIVERGED', 'STASH_FAILED', 'FF_FAILED')
$verdict = if ($bad.Count) { 'RED' }
elseif (@($Verify | Where-Object { $_.狀態 -ne 'FRESH' }).Count) { 'YELLOW' }
elseif ($syncBad -or $EnvFallback.Count -or $AccelCount -ne 25) { 'YELLOW' }
else { 'GREEN' }

[pscustomobject]@{
    verdict = $verdict; ts = $RunStart.ToString('s'); via_root = $ViaRoot
    accelerators = "$AccelCount/25"; env_fallback = $EnvFallback; sync = $Sync
    onboard = $Onb; tally = $tally; steps = $Rows; verify = $Verify
} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $RunDir 'run.json') -Encoding utf8

# ── 交接報告(批609;操作員令 SAVE ALL STATUS AND HANDOVER REPORT AUTOMATICALLY)──
#   一份讀得動的 Markdown,**每一跑自動產**,不必再把整個主控台貼回來。
#   規矩同 L86:紅的一定在裡面,而且每一條都指得到自己的 log。
$H = [System.Collections.Generic.List[string]]::new()
$H.Add("# VIA ALL-IN-ONE 交接報告 · $($RunStart.ToString('yyyy-MM-dd HH:mm:ss'))")
$H.Add("")
$H.Add("| | |")
$H.Add("|---|---|")
$H.Add("| 判定 | **$verdict** |")
$H.Add("| 母資料夾 | ``$ViaRoot`` |")
$H.Add("| 同步 | $($Sync.state) · 落後 $($Sync.behind) · 領先 $($Sync.ahead) · stash $($Sync.stashed) · 撞名 $($Sync.collisions) |")
$H.Add("| HEAD | $((& git -C $ViaRoot log --oneline -1 2>$null)) |")
$H.Add("| 加速器 | $AccelCount/25 |")
$H.Add("| 家族境退路 | $(if ($EnvFallback.Count) { $EnvFallback -join ',' } else { '無' }) |")
$H.Add("| 本跑存證 | ``$RunDir`` |")
$H.Add("")
$H.Add("## 步驟(" + (($tally.GetEnumerator() | ForEach-Object { "$($_.Key) $($_.Value)" }) -join ' · ') + ")")
$H.Add("")
$H.Add("| 步 | 家族 | 態 | rc | 秒 | 因由 |")
$H.Add("|---|---|---|---|---|---|")
foreach ($r in $Rows) {
    $w = ($r.Why -replace '\|', '\\|'); if ($w.Length -gt 160) { $w = $w.Substring(0, 160) + '…' }
    $H.Add("| $($r.Step) | $($r.Family) | **$($r.State)** | $($r.ExitCode) | $($r.Seconds) | $w |")
}
$H.Add("")
if ($bad.Count) {
    $H.Add("## 紅的逐個點名")
    $H.Add("")
    foreach ($b in $bad) {
        $H.Add("### $($b.Step) · $($b.State)")
        $H.Add("")
        $H.Add("``````")
        $H.Add(($b.Why -replace '`', "'"))
        $H.Add("``````")
        $H.Add("")
        $H.Add("紀錄:``$($b.Log)``")
        $H.Add("")
    }
} else {
    $H.Add("## 紅的逐個點名")
    $H.Add("")
    $H.Add("本跑無 RED / TIMEOUT。")
    $H.Add("")
}
$H.Add("## 產出驗證")
$H.Add("")
$H.Add("| 產出 | 狀態 | 時間 |")
$H.Add("|---|---|---|")
foreach ($v in $Verify) { $H.Add("| $($v.產出) | $($v.狀態) | $($v.時間) |") }
$H.Add("")
$H.Add("## 上船清點(母資料夾 vs git;唯讀)")
$H.Add("")
$H.Add("該上船 **$($Onb.take)** · 再生物 $($Onb.regen)(不上船)· 暫存 $($Onb.temp)(不上船)")
$H.Add("")
if ($Onb.take) {
    $H.Add("| 狀態 | 路徑 |")
    $H.Add("|---|---|")
    foreach ($x in @($Onb.items | Where-Object { $_.類 -eq '該上船' })) { $H.Add("| $($x.狀態) | ``$($x.路徑)`` |") }
    $H.Add("")
    $H.Add("上船(你的手):``via-sync -Onboard -Commit [-Push]``")
    $H.Add("")
}
$H.Add("## 下一步")
$H.Add("")
$H.Add("- 同步解卡:``via-sync``")
$H.Add("- 再跑一次:``via-allinone``(``-SkipHeavy`` 跳過全格 · ``-MaxLines 30`` 更省畫面)")
$H.Add("- 這份報告:``$(Join-Path $RunDir 'HANDOVER.md')``")
$HandoverPath = Join-Path $RunDir 'HANDOVER.md'
$H -join "`n" | Set-Content -LiteralPath $HandoverPath -Encoding utf8

$vc = switch ($verdict) { 'GREEN' { 'Green' } 'RED' { 'Red' } default { 'Yellow' } }
Write-Line ("[VIA ALL-IN-ONE v$SelfVer] {0} · 同步 {1}(落後 {2})· 步 {3} · {4} · 加速器 {5}/25 · 存證 {6}" -f `
        $verdict, $Sync.state, $Sync.behind, $Rows.Count,
    (($tally.GetEnumerator() | ForEach-Object { "$($_.Key) $($_.Value)" }) -join ' · '), $AccelCount, $RunDir) $vc
if ($bad.Count) {
    Write-Line '  紅的逐個點名(不卡斷=跑完才講,不是跑一半就停):' 'Red'
    foreach ($b in $bad) { Write-Line ("   · {0} / {1} · {2} · 紀錄 {3}" -f $b.Step, $b.State, $b.Why, $b.Log) 'Red' }
}
if ($syncBad) { Write-Line "  [黃] 同步 $($Sync.state):$($Sync.why)(跑的可能不是最新版)" 'Yellow' }
if ($Sync.stashed -gt 0) {
    Write-Line "  [提醒] 同步前 stash 了 $($Sync.stashed) 個追蹤檔;備份在 $($Sync.backup)" 'DarkGray'
    Write-Line "         那些多半是再生物,引擎再跑一次就會重生;真要拿回來:git stash pop" 'DarkGray'
}
if ($EnvFallback.Count) { Write-Line "  [黃] 家族境未見:$($EnvFallback -join ',')(能跑 ≠ 在本位跑)" 'Yellow' }
if ($Onb.take) { Write-Line "  [上船] 母資料夾有 $($Onb.take) 件還沒進 git → via-sync -Onboard -Commit" 'Yellow' }
Write-Line "  [交接] $HandoverPath   ← 貼這一份就夠,不必貼整個主控台" 'Cyan' 
if ($OpenPage -and (Get-Command via-open -ErrorAction SilentlyContinue)) {
    via-open (Join-Path $ViaRoot 'VIA_Reports\vcgc\VIA_UI_MatrixControl_v0100.html')
}
# 誠實三態 rc:0 綠 · 1 紅 · 2 黃(黃不是綠)
exit $(switch ($verdict) { 'GREEN' { 0 } 'RED' { 1 } default { 2 } })
