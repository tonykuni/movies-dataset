<#
.SYNOPSIS
    VIA ALL-IN-ONE:同步 → 進環境 → 25 加速器 → 實測全系統 → 驗證產出(不卡斷)

.DESCRIPTION
    操作員令(批604):「all integrate into one ps code with 25 accelerators」。
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
    [switch]$NoSync,
    [switch]$SkipHeavy,
    [switch]$OpenPage
)

# 不卡斷律:全域不用 Stop。單步的錯自己接,接完往下走。
$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false
$RunStart = Get-Date

function Write-Line([string]$Text, [string]$Colour = 'Gray') { Write-Host $Text -ForegroundColor $Colour }

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
Write-Line "`n=== VIA ALL-IN-ONE v0105(同步 + 25 加速器 + 全系統實測)===" 'Cyan'
Write-Line "  母資料夾 : $ViaRoot"

# 本跑存證夾要先建好,SYNC 段的備份要落在裡面
$RunDir = Join-Path $ViaRoot ('VIA_Reports\accelerated_test\' + $RunStart.ToString('yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
Write-Line "  本跑存證 : $RunDir"

# ── 0.5 SYNC:把倉同步到最新(這一段是 v0104 的重點)──────────────────────
$Sync = [ordered]@{ state = 'SKIPPED'; behind = 0; ahead = 0; stashed = 0; collisions = 0; backup = ''; why = '' }
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
    Write-Line "`n=== $Name / $Family === (逾時 ${timeout}s)" 'Cyan'
    Write-Line "    引擎 $(Split-Path $target -Leaf) $($Arguments -join ' ')" 'DarkGray'

    $state = 'RED'; $code = $null; $why = ''
    $lines = [System.Collections.Generic.List[string]]::new()
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
                        Write-Host $line
                        $lines.Add($line)
                        Add-Content -LiteralPath $log -Value $line -Encoding utf8
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
            Write-Progress -Activity 'VIA ALL-IN-ONE v0105' `
                -Status ("$Name 已跑 {0:N0}s / 完成 {1} 步" -f $timer.Elapsed.TotalSeconds, $Rows.Count)
            Start-Sleep -Milliseconds 100
        }
        $code = $proc.ExitCode
        $proc.Dispose()
        if ($killed) { $state = 'TIMEOUT'; $why = "逾時 ${timeout}s" }
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
Invoke-Step '11_PanoramaScan'  'core' $REG 'CGC_MDL158_VIAPanoramaAuditRepair_v*.py'          @('scan', '--json') 900
Invoke-Step '12_MatrixConsole' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('matrix', '--family', $Families) 3600
if (-not $SkipHeavy) {
    Invoke-Step '13_SelftestGrid' 'core' $REG 'CGC_MDL064_SelftestGrid_v*.py'                  @() 3600
}
Invoke-Step '14_Handover'      'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('page') 600
Invoke-Step '15_ApprovalCheck' 'core' $REG 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' @('check') 600
Write-Progress -Activity 'VIA ALL-IN-ONE v0105' -Completed

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
    tally = $tally; steps = $Rows; verify = $Verify
} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $RunDir 'run.json') -Encoding utf8

$vc = switch ($verdict) { 'GREEN' { 'Green' } 'RED' { 'Red' } default { 'Yellow' } }
Write-Line ("[VIA ALL-IN-ONE v0105] {0} · 同步 {1}(落後 {2})· 步 {3} · {4} · 加速器 {5}/25 · 存證 {6}" -f `
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
if ($OpenPage -and (Get-Command via-open -ErrorAction SilentlyContinue)) {
    via-open (Join-Path $ViaRoot 'VIA_Reports\vcgc\VIA_UI_MatrixControl_v0100.html')
}
# 誠實三態 rc:0 綠 · 1 紅 · 2 黃(黃不是綠)
exit $(switch ($verdict) { 'GREEN' { 0 } 'RED' { 1 } default { 2 } })
