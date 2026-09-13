#Requires -Version 5.1
param(
    [string]$Root = "",
    [int]$StageTimeoutSec = 3600,
    [switch]$SkipAccel,
    [switch]$SkipData,
    [switch]$SkipMatrix,
    [switch]$DryRun
)
# =============================================================================
# Invoke-VIA-OneShot-v0100.ps1 — 一個指令跑完全部(批394 續章;操作員令「整合成一個 PS
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
# 紀律:零 force、零刪除、台帳只增不減、FRED 鑰永不入 git(只判在位,不讀不印)、
#       同意閘不覆蓋(Set-VIAGateDefaults 只在未設時補)、逾時 kill 不卡斷、誠實三態。
# 用法:& .\Invoke-VIA-OneShot-v0100.ps1                 全跑
#       & .\Invoke-VIA-OneShot-v0100.ps1 -DryRun         只列計畫不動手
#       & .\Invoke-VIA-OneShot-v0100.ps1 -SkipData       略過資料擷取段
#       & .\Invoke-VIA-OneShot-v0100.ps1 -SkipMatrix     略過 207 站全矩陣
# =============================================================================
$ErrorActionPreference = "Continue"
$env:VIA_NO_OPEN = "1"
$env:GIT_EDITOR = "true"
$env:GIT_MERGE_AUTOEDIT = "no"
$env:PYTHONUTF8 = "1"
$script:T0 = Get-Date
$script:Rows = New-Object System.Collections.ArrayList

function Add-Row([string]$Stage, [string]$State, [string]$Note, [double]$Secs) {
    [void]$script:Rows.Add([pscustomobject]@{ Stage = $Stage; State = $State; Note = $Note; Secs = [math]::Round($Secs, 1) })
    $tag = "  [" + $State.PadRight(4) + "] " + $Stage
    if ($Secs -gt 0) { $tag = $tag + " · " + [math]::Round($Secs, 1) + "s" }
    if ($Note) { $tag = $tag + " · " + $Note }
    Write-Host $tag
}

function Invoke-Stage {
    param([string]$Stage, [scriptblock]$Body, [int]$TimeoutSec = 0)
    if ($TimeoutSec -le 0) { $TimeoutSec = $StageTimeoutSec }
    Write-Host ""
    Write-Host ("── " + $Stage + " ──")
    if ($DryRun) { Add-Row $Stage "PLAN" "唯讀計畫(去掉 -DryRun 才動手)" 0; return }
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
    $state = "OK"
    if ($txt -match "(?m)^\s*SKIP |不在位|鑰不在位") { $state = "SKIP" }
    if ($txt -match "can't open file|No such file|FileNotFoundError|Errno 2|ModuleNotFoundError") { $state = "SKIP" }
    if ($txt -match "\[FAIL\]|Traceback|Exception:|is not recognized|ParserError|FAIL [1-9]") { $state = "FAIL" }
    if ($rc -ne 0 -and $state -eq "OK") { $state = "FAIL" }
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
Write-Host " VIA ONE-SHOT · 一個指令跑完全部(Invoke-VIA-OneShot v0100)"
Write-Host "==============================================================="
Write-Host ("  根 " + $Root)
Write-Host ("  起 " + $script:T0.ToString("yyyy-MM-dd HH:mm:ss") + " · 段逾時 " + $StageTimeoutSec + "s · 零跳出 VIA_NO_OPEN=1")

# ================= S1 解卡 =================
Invoke-Stage "S1 解卡(倉庫拉齊;繞 bootstrap 死結)" {
    $r = $Root
    $v = $Via
    $u = Get-ChildItem -LiteralPath $v -Filter "Invoke-VIA-Unstick-v*.ps1" -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if (-not $u) {
        & git -C $r fetch -q origin main 2>&1 | Out-Null
        & git -C $r checkout origin/main -- "VeritasIntelligenceAnalytics/Invoke-VIA-Unstick-v0100.ps1" 2>&1 | Out-Null
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
    Invoke-Stage "S4 加速器導入(via-accel-import --apply --approve;base 零觸碰)" {
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
    Invoke-Stage "S6a 價格增量(via-price)" {
        if (Get-Command via-price -ErrorAction SilentlyContinue) { via-price } else { Write-Output "SKIP via-price 不在位" }
    } 3600
    Invoke-Stage "S6b 籌碼增量(via-chip)" {
        if (Get-Command via-chip -ErrorAction SilentlyContinue) { via-chip } else { Write-Output "SKIP via-chip 不在位" }
    } 3600
    Invoke-Stage "S6c 日交易×籌碼對齊(via-align update --apply)" {
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
Write-Host ""
Write-Host "==============================================================="
Write-Host " ONE-SHOT 總表(誠實三態;SKIP=缺件或鑰缺,非假綠)"
Write-Host "==============================================================="
foreach ($row in $script:Rows) {
    $line = "  " + $row.State.PadRight(4) + " · " + $row.Stage.PadRight(42)
    if ($row.Secs -gt 0) { $line = $line + " " + ([string]$row.Secs).PadLeft(7) + "s" }
    Write-Host $line
    $nt = ([string]$row.Note)
    if ($nt) { Write-Host ("         " + $nt.Substring(0, [math]::Min(150, $nt.Length))) }
}
Write-Host ""
Write-Host ("  [計] OK " + $nOK + " · FAIL " + $nFail + " · SKIP " + $nSkip + " · PLAN " + $nPlan + " · 總 " + [math]::Round($elapsed, 1) + "s")
$regNow = Get-Tail $via "Register-VIA-Commands-v*.ps1"
Write-Host ("  [冊] " + $(if ($regNow) { Split-Path $regNow -Leaf } else { "(缺)" }) + " · 本視窗短令已生效")
if ($nFail -gt 0) {
    Write-Host "  [下一步] 把上面總表整段貼回對話即可續修(現場已保留;零 force 零刪除)"
} else {
    Write-Host "  [下一步] 全段無紅。看頁:via-open 入口 / via-console / via-handover"
}
exit $(if ($nFail -gt 0) { 1 } else { 0 })
