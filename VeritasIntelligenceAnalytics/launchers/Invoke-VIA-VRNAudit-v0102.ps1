#!/usr/bin/env pwsh
<#
    VIA VRN AUDIT:25 加速器 → VRN 實測鏈 → 驗證矩陣 → 誠實裁決(不卡斷)

    操作員令(批625):「整合入一個 PS 指令,加入 25 個加速器,動態進度條,
    加入並更新前一個指令,測試修正 VRN 直到成功,測試樣本如先前」。

    「直到成功」怎麼做才不是假的
    ────────────────────────────
    把同一句指令跑三次**不叫修正**,那只是把同一個結果印三遍(批624 LL205:
    修法句指回剛剛那一句 = 把人送回原地繞圈)。所以本件的輪迴律是:
      **下一輪一定要跟這一輪不一樣;找不到可調整的差異就誠實停。**
    目前只認一種可調整的差異(量出來的,不是想像的):
      鏈跑完了、但矩陣說庫不在 → 去找 ENG073 **實際寫到哪一個 .duckdb**,
      下一輪拿那個庫再讀一次矩陣。找不到就停,並把該看的東西指出來。
    引擎自己壞掉(rc≠0)一律不重試——重跑一個會爆的東西只會再爆一次。

    零卡斷:每一步都是自己生的子行程,逾時只殺自己那一個。
    零代設:VIA_NET_CONSENT 之類的閘一個都不碰。
    零捏造:任何一輪都不會把「沒產出」說成「成功」。
#>
[CmdletBinding()]
param(
    [string]$In = 'C:\測試樣本報告',
    # 批625 實跑抓到:`-Db` 撞 CmdletBinding 內建 `-Debug` 的別名 `db`,
    #   啟動當場 MetadataError。AST 一路綠燈——**只有真的跑一次才看得見**(LL182)。
    [string]$DbPath = '',
    [int]$MaxRounds = 3,
    [int]$StepTimeoutSec = 3600,
    [switch]$ProgressLines,
    [int]$ProgressEverySec = 0,
    [string]$ViaRoot = ''
)

# 不卡斷律:全域不用 Stop;單步的錯自己接,接完往下走。
$ErrorActionPreference = 'Continue'
# 批618:原生 Write-Progress 每 100ms 噴一次,逐字稿裡糊成一片。進度只走 stdout。
$ProgressPreference = 'SilentlyContinue'

$SelfVer = '0100'
if ([IO.Path]::GetFileNameWithoutExtension($PSCommandPath) -match 'v(\d{4})$') { $SelfVer = $Matches[1] }

function Write-Line([string]$Text, [string]$Color = 'Gray') {
    try { Write-Host $Text -ForegroundColor $Color } catch { Write-Host $Text }
}

# ── 0 母資料夾 ────────────────────────────────────────────────────
if (-not $ViaRoot) {
    $here = Split-Path -Parent $PSCommandPath
    $ViaRoot = Split-Path -Parent $here          # launchers\ 的上一層 = 母資料夾
}
if (-not (Test-Path -LiteralPath $ViaRoot -PathType Container)) {
    Write-Line "  [FAIL] 母資料夾不存在:$ViaRoot" 'Red'; exit 2
}
Set-Location -LiteralPath $ViaRoot

$Ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$RunDir = Join-Path $ViaRoot "VIA_Reports\vrn_audit\$Ts"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

Write-Line "`n=== VIA VRN AUDIT v$SelfVer(25 加速器 + 實測鏈 + 驗證矩陣)===" 'Cyan'
Write-Line "  母資料夾 : $ViaRoot"
Write-Line "  測試樣本 : $In"
Write-Line "  存證     : $RunDir"

# ── 1 指令冊(家族境解析要靠它)────────────────────────────────────
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $Register) { Write-Line '  [FAIL] 指令註冊冊缺(Register-VIA-Commands-v*.ps1)' 'Red'; exit 2 }
. $Register.FullName | Out-Null
Write-Line "  指令冊   : $($Register.Name)"

# ── 2 加速器 25 名冊(正典原文點源,不自己抄一份)────────────────────
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

# ── 3 VRN 本位解譯器 ───────────────────────────────────────────────
$PyVrn = 'python'
try { $PyVrn = Get-VIAEnvPython 'vrn' } catch { $PyVrn = 'python' }
if ($PyVrn -eq 'python' -or -not (Test-Path -LiteralPath $PyVrn -PathType Leaf)) {
    Write-Line "  環境 vrn : **base 退路**(家族境未見;能跑 ≠ 在本位跑)" 'Yellow'
} else {
    Write-Line "  環境 vrn : $PyVrn" 'Green'
}

function Get-Newest([string]$Folder, [string]$Pattern) {
    $d = Join-Path $ViaRoot $Folder
    if (-not (Test-Path -LiteralPath $d -PathType Container)) { return $null }
    $f = Get-ChildItem -LiteralPath $d -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($f) { return $f.FullName } else { return $null }
}

$Eng83 = Get-Newest 'functional modules\VRN' 'VRN_ENG083_VerifiedMatrix_v*.py'
$Eng73 = Get-Newest 'functional modules\VRN' 'VRN_ENG073_ReportStructuredDB_v*.py'
if (-not $Eng83) { Write-Line '  [FAIL] 找不到 VRN_ENG083_VerifiedMatrix_v*.py' 'Red'; exit 2 }
Write-Line "  矩陣引擎 : $(Split-Path $Eng83 -Leaf)"

# ── 4 進度條:@@PROGRESS 是**第二個內層來源**(批619)──────────────
$script:InnerProg = $null
$script:LastProg = [datetime]::MinValue
$script:LastProgLen = 0
$script:ProgTty = -not [Console]::IsOutputRedirected
$script:NoisePat = '^\s*(@@PROGRESS\||\[[█░])'

function Write-ProgLine([string]$Name, [double]$Elapsed, [int]$Timeout, [datetime]$Since, [switch]$Force) {
    if ($ProgressLines) { $script:ProgTty = $false }
    $gap = if ($ProgressEverySec -gt 0) { $ProgressEverySec } elseif ($script:ProgTty) { 1 } else { 20 }
    if (-not $Force -and ((Get-Date) - $script:LastProg).TotalSeconds -lt $gap) { return }
    $script:LastProg = Get-Date
    $ip = $script:InnerProg
    $ipMine = ($null -ne $ip -and $ip.At -ge $Since)
    $frac = if ($ipMine) { [math]::Min(1.0, $ip.Pct / 100.0) }
            elseif ($Timeout -gt 0) { [math]::Min(0.9, $Elapsed / $Timeout) } else { 0.0 }
    $pct = [int](100.0 * $frac)
    $bar = ('#' * [int]($pct / 5)).PadRight(20, '.')
    $txt = "[{0}] {1,3}%  {2}  已跑 {3:N0}s/{4}s" -f $bar, $pct, $Name, $Elapsed, $Timeout
    if ($ipMine) {
        $m = $ip.Msg; if ($m.Length -gt 46) { $m = $m.Substring(0, 46) }
        $txt += "  ·  內層 {0:N0}% {1}" -f $ip.Pct, $m
    } else {
        $txt += "  ·  (時間粗估;本步沒有內層進度來源)"
    }
    if ($script:ProgTty) {
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

# 一步 = 一個子行程。逾時只殺自己生的那一個,別的照跑(不卡斷律)。
function Invoke-Py([string]$Name, [string]$Script, [string[]]$Arguments, [int]$TimeoutSec) {
    $script:InnerProg = $null
    $since = Get-Date
    $log = Join-Path $RunDir ("{0}.log" -f ($Name -replace '[^\w\-]', '_'))
    Write-Line "`n  ── $Name ──" 'Cyan'
    Write-Line "     $(Split-Path $Script -Leaf) $($Arguments -join ' ')" 'DarkGray'
    $lines = [System.Collections.Generic.List[string]]::new()
    $rc = -1
    try {
        $info = [System.Diagnostics.ProcessStartInfo]::new()
        $info.FileName = $PyVrn
        $info.WorkingDirectory = $ViaRoot
        $info.UseShellExecute = $false
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $info.Environment['PYTHONUTF8'] = '1'
        $info.Environment['PYTHONUNBUFFERED'] = '1'
        foreach ($a in (@('-u', $Script) + $Arguments)) { $info.ArgumentList.Add([string]$a) }
        $proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $info
        if (-not $proc.Start()) { throw '子行程啟動失敗' }
        $streams = @($proc.StandardOutput, $proc.StandardError)
        $tasks = @($streams[0].ReadLineAsync(), $streams[1].ReadLineAsync())
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        $killed = $false
        while (-not $proc.HasExited -or $null -ne $tasks[0] -or $null -ne $tasks[1]) {
            for ($i = 0; $i -lt 2; $i++) {
                if ($null -ne $tasks[$i] -and $tasks[$i].IsCompleted) {
                    $line = $tasks[$i].GetAwaiter().GetResult()
                    if ($null -eq $line) { $tasks[$i] = $null }
                    else {
                        $lines.Add($line)
                        Add-Content -LiteralPath $log -Value $line -Encoding utf8
                        if ($line -match '^\s*@@PROGRESS\|([0-9.]+)\|(.*)$') {
                            $script:InnerProg = [pscustomobject]@{
                                Pct = [double]$Matches[1]; Msg = ([string]$Matches[2]).Trim(); At = (Get-Date) }
                        } elseif ($line -notmatch $script:NoisePat) {
                            Write-Host $line
                        }
                        $tasks[$i] = $streams[$i].ReadLineAsync()
                    }
                }
            }
            if (-not $killed -and $timer.Elapsed.TotalSeconds -gt $TimeoutSec) {
                $killed = $true
                try { $proc.Kill($true) } catch { }
                Write-Line "     [TIMEOUT] 超過 ${TimeoutSec}s,殺掉本步子行程" 'Red'
            }
            Write-ProgLine $Name $timer.Elapsed.TotalSeconds $TimeoutSec $since
            Start-Sleep -Milliseconds 120
        }
        $proc.WaitForExit()
        $rc = if ($killed) { 124 } else { $proc.ExitCode }
        Complete-ProgLine
    } catch {
        Complete-ProgLine
        Write-Line "     [FAIL] $($_.Exception.Message)" 'Red'
        $rc = 1
    }
    return [pscustomobject]@{ Name = $Name; Rc = $rc; Lines = $lines; Log = $log }
}

# ── 5 輪迴:每一輪一定要跟上一輪不一樣,否則誠實停 ────────────────
$DbNow = $DbPath
$Rounds = [System.Collections.Generic.List[object]]::new()
$Verdict = 'RED'
$Why = ''

for ($r = 1; $r -le $MaxRounds; $r++) {
    Write-Line "`n=== 第 $r 輪 / 上限 $MaxRounds ===" 'Magenta'

    if ($r -eq 1) {
        $a = @('run', '--in', $In)
        if ($DbNow) { $a += @('--db', $DbNow) }
        $runRes = Invoke-Py "R$r-鏈實跑" $Eng83 $a $StepTimeoutSec
        # 自審(第一次實跑就照出來):rc=3 是**誠實四態的 ABSENT**(料不在),
        #   我第一版把它跟「引擎壞了」寫成同一句,當場對著「樣本夾不在」說引擎壞了。
        #   0=GREEN 1=RED 2=NODATA 3=ABSENT 4=GATED——**rc 是有意義的,不是只有零和非零**。
        if ($runRes.Rc -eq 3) {
            $Verdict = 'ABSENT'
            $Why = ("樣本夾不在:$In。**這不是引擎壞了,是料不在**——" +
                    "把 -In 改成你機器上的實際位置再跑一次(這一次值得重跑,因為輸入會不一樣)。")
            $Rounds.Add($runRes) | Out-Null
            break
        }
        if ($runRes.Rc -notin @(0, 2)) {
            $Verdict = 'RED'
            $Why = "鏈實跑 rc=$($runRes.Rc)。**引擎自己壞了,重跑不會變好**——看 $($runRes.Log)"
            $Rounds.Add($runRes) | Out-Null
            break
        }
        # 批627 工作站實錄:R1 鏈實跑回 NODATA(ENG073 說「無分區 sidecar」=我沒有料),
        #   v0101 照樣往下跑矩陣,矩陣當然空,於是進診斷迴圈**換了兩個庫、跑滿三輪**,
        #   每一輪拿到同一句 NODATA。錯在我把「鏈說它沒有料」當成「可以往下走」。
        #   鏈沒有料,庫就不會被寫出來——**換一個庫去讀不會變出資料,那不是一個真差異**
        #   (批625 輪迴律:下一輪一定要跟這一輪不一樣,找不到差異就誠實停)。
        if ($runRes.Rc -eq 2) {
            $Verdict = 'NODATA'
            $chainWhy = ($runRes.Lines | Where-Object { $_ -match 'rc=\d' } | Select-Object -Last 3) -join ' / '
            $Why = ("鏈實跑 rc=2(NODATA)——**鏈上有站說它沒有料**,不是庫放錯地方。" +
                    "庫沒被寫出來是因為根本沒有東西可寫,所以這裡停,不換庫、不重跑。" +
                    "鏈說的是:$chainWhy")
            $Rounds.Add($runRes) | Out-Null
            break
        }
        $Rounds.Add($runRes) | Out-Null
    }

    $am = @('matrix')
    if ($DbNow) { $am += @('--db', $DbNow) }
    $mxRes = Invoke-Py "R$r-驗證矩陣" $Eng83 $am 600
    $Rounds.Add($mxRes) | Out-Null

    # 批626 實測抓到(我自己在 v0100 造的):判準寫成「rc=0 **而且**輸出裡不含 ABSENT」。
    #   但矩陣成功時本來就會印四態統計 `GREEN x · YELLOW y · NODATA z · ABSENT w`
    #   ——**ABSENT 是人家的欄位名,不是失敗訊號**。於是 `matrix · OK · 73 份報告 × 7 欄`
    #   被我自己判成失敗,整條掉進診斷迴圈。
    #   批625 才剛把 ENG083 的誠實四態接上 rc(_RC_OF),結果我在下游又回去比字串。
    #   **有 rc 就別比字串**:字串會撞到統計欄位、會撞到別人的說明文字。
    if ($mxRes.Rc -eq 0) {
        $Verdict = 'GREEN'
        $Why = "矩陣產出成功(第 $r 輪)· $(($mxRes.Lines | Where-Object { $_ -match 'matrix ·' } | Select-Object -Last 1))"
        break
    }

    # 失敗了。找**這一輪跟下一輪的差異**;找不到就停,不重跑同一句。
    Write-Line "`n  [診斷] 矩陣沒出來,找 ENG073 到底把庫寫去哪了" 'Yellow'
    $cands = @()
    foreach ($d in @('functional modules\VRN\output', 'functional modules\VDF\output_hub\mega')) {
        $p = Join-Path $ViaRoot $d
        if (Test-Path -LiteralPath $p -PathType Container) {
            $cands += @(Get-ChildItem -LiteralPath $p -Filter '*.duckdb' -File -ErrorAction SilentlyContinue |
                        Sort-Object LastWriteTime -Descending | Select-Object -First 3)
        }
    }
    $cands = @($cands | Where-Object { $_.FullName -ne $DbNow } | Sort-Object LastWriteTime -Descending)
    if ($cands.Count -eq 0) {
        $Verdict = 'NODATA'
        $Why = ("鏈跑完了,但兩個候選夾裡**一個 .duckdb 都沒有**。" +
                "下一輪跟這一輪不會有任何差異,所以停在這裡——" +
                "再跑一次只會得到同一個結果(批624 LL205)。" +
                "該看的是 ENG073 的落檔:「$(Split-Path $Eng73 -Leaf) status」")
        break
    }
    $pick = $cands[0].FullName
    Write-Line "     [換庫] 下一輪改讀 $pick  ·  最近寫入 $($cands[0].LastWriteTime)" 'Yellow'
    $DbNow = $pick
    if ($r -eq $MaxRounds) {
        $Verdict = 'NODATA'
        $Why = "試到第 $MaxRounds 輪仍沒有可讀的矩陣;最後一次換到 $pick 還是不行。"
    }
}

# ── 6 誠實裁決 ────────────────────────────────────────────────────
$summary = [ordered]@{
    schema = 'VIA.VRNAudit.v1'; ts = $Ts; via_root = $ViaRoot; sample = $In
    accelerators = "$AccelCount/25"; engine = (Split-Path $Eng83 -Leaf)
    py_vrn = $PyVrn; db = $DbNow; verdict = $Verdict; why = $Why
    rounds = @($Rounds | ForEach-Object { @{ name = $_.Name; rc = $_.Rc; log = $_.Log } })
}
$jsonPath = Join-Path $RunDir 'vrn_audit.json'
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$col = @{ GREEN = 'Green'; NODATA = 'Yellow'; ABSENT = 'DarkYellow'; RED = 'Red' }[$Verdict]
Write-Line "`n=== VRN AUDIT 裁決 · $Verdict ===" $col
Write-Line "  $Why"
Write-Line "  輪次 $($Rounds.Count) 步 · 加速器 $AccelCount/25 · 樣本 $In"
Write-Line "  存證 $jsonPath"
if ($Verdict -eq 'ABSENT') {
    Write-Line "  次步:把樣本路徑換成實際位置,例如" 'Yellow'
    Write-Line "    via-vrnaudit -In `"D:\你的報告夾`""
    Write-Line "    (本件不會替你猜路徑;猜對了也是猜的)"
} elseif ($Verdict -ne 'GREEN') {
    Write-Line "  次步(**不是叫你把同一句再打一次**):" 'Yellow'
    Write-Line "    1) 看 ENG073 落檔:$(Split-Path $Eng73 -Leaf) status"
    Write-Line "    2) 指定庫再讀矩陣:via-vrnaudit -In `"$In`" -DbPath `"<那個 .duckdb>`""
    Write-Line "    3) 逐步原文在 $RunDir"
}
# 誠實四態照原樣往外送:0=GREEN 1=RED 2=NODATA 3=ABSENT
exit $(switch ($Verdict) { 'GREEN' { 0 } 'NODATA' { 2 } 'ABSENT' { 3 } default { 1 } })
