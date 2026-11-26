#Requires -Version 5.1
<#
Start-VIA-VDF-v0100.ps1 — VDF 一鍵啟動(PS 只做:找倉 → 開跑前檢查 → 叫 Python 啟動器 → 畫面)

操作員 2026-11-26:「接入排程優化加速器 · 不傷電腦不傷系統 · 現代化一點的 powershell U/I 動畫 · 主要功能還是寫在 py 上 · ps 啟動」。
主要功能全在 Python:VDF_MDL022_SafeParallelLaunch 尾版(VDF 自己的排程啟動器)
  ⓪ 暫存庫只補缺併進資料家(VDF_MDL023_StageMerge)· 擷取家 = 資料家(VDF_MDL012 / MDL008 v0113)
  ① 降壓:本行程與子行程 BELOW_NORMAL + IO LOW · 數學庫執行緒與 DuckDB 記憶體按道數分 · 暫存走 TEMP
  ② 3 道並行 + 監工:過熱減道、暫停最新子行程,冷卻再恢復 · DRAM 不足先等
  ③ 橋閘(加速器 + 網路工具 100%)→ 增量擷取(庫裡有的不重抓)→ parquet 只寫新鍵 → Rich 分類矩陣
本檔不設同意閘:要出網,請先在自己的視窗開兩道(VIA_NET_CONSENT · VIA_SCRAPE_CONSENT),本檔只檢查、只提醒。
用法:pwsh -NoProfile -File Start-VIA-VDF-v0100.ps1 [-Start 2018-01-01] [-DataHome <資料家>] [-Dry] [-NoMerge] [-Check] [-Plain]
  -Check  只做開跑前檢查(不叫主流程)   -Plain  不用動畫與 24 位元色(舊主控台)
#>
param(
    [string]$Start = '2018-01-01',
    [string]$DataHome = '',
    [switch]$Dry,
    [switch]$NoMerge,
    [switch]$Check,
    [switch]$Plain
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { Write-Verbose 'console encoding unchanged' }
$env:PYTHONUTF8 = '1'
$E = [char]27
$VT = (-not $Plain) -and $Host.UI.SupportsVirtualTerminal

function Paint([string]$Text, [int[]]$Rgb) {
    if ($VT) { return "$E[38;2;$($Rgb[0]);$($Rgb[1]);$($Rgb[2])m$Text$E[0m" }
    return $Text
}

function Show-Gradient([string]$Text, [int[]]$From, [int[]]$To) {
    if (-not $VT) { Write-Host $Text -ForegroundColor Cyan; return }
    $n = [Math]::Max(1, $Text.Length - 1)
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $Text.Length; $i++) {
        $r = [int]($From[0] + ($To[0] - $From[0]) * $i / $n)
        $g = [int]($From[1] + ($To[1] - $From[1]) * $i / $n)
        $b = [int]($From[2] + ($To[2] - $From[2]) * $i / $n)
        [void]$sb.Append("$E[38;2;$r;$g;${b}m$($Text[$i])")
    }
    Write-Host ($sb.ToString() + "$E[0m")
}

function Show-Box([string]$Title, [string[]]$Lines, [int[]]$Rgb) {
    $w = 64
    Write-Host (Paint ('╭─ ' + $Title + ' ' + ('─' * [Math]::Max(0, $w - $Title.Length - 4)) + '╮') $Rgb)
    foreach ($l in $Lines) { Write-Host ((Paint '│ ' $Rgb) + $l) }
    Write-Host (Paint ('╰' + ('─' * ($w - 1)) + '╯') $Rgb)
}

$Frames = @('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')
function Invoke-Step([string]$Label, [scriptblock]$Probe) {
    if ($VT) {
        Write-Host -NoNewline "$E[?25l"
        for ($k = 0; $k -lt 8; $k++) {
            Write-Host -NoNewline ("`r  " + (Paint $Frames[$k % $Frames.Count] @(120, 170, 255)) + " $Label")
            Start-Sleep -Milliseconds 45
        }
    }
    $res = & $Probe
    $ok = [bool]$res.Ok
    $mark = if ($ok) { Paint '✔' @(80, 220, 140) } elseif ($res.Warn) { Paint '!' @(255, 200, 60) } else { Paint '✖' @(255, 90, 90) }
    $line = "  $mark $Label" + $(if ($res.Note) { (Paint ('  ' + $res.Note) @(150, 150, 165)) } else { '' })
    if ($VT) { Write-Host ("`r$E[2K" + $line) } else { Write-Host $line }
    return $res
}

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$rc = 1
try {
    Write-Host ''
    Show-Gradient '  ▌ VIA · VDF  資料擷取啟動器  ·  排程加速 · 降壓保護 · 增量不重抓' @(90, 160, 255) @(170, 110, 255)
    Write-Host (Paint '  PS 只負責啟動;排程、降壓、擷取、併庫全在 Python(VDF_MDL022 尾版)' @(150, 150, 165))
    Write-Host ''

    $Via = $PSScriptRoot
    $r1 = Invoke-Step '找倉(VIA 根)' { [pscustomobject]@{ Ok = (Test-Path (Join-Path $Via 'functional modules\VDF')); Note = $Via } }
    if (-not $r1.Ok) { throw "這支 .ps1 要放在 VeritasIntelligenceAnalytics 根目錄(找不到 functional modules\VDF)" }

    $null = Invoke-Step '倉狀態(分支)' {
        $br = (& git -C $Via rev-parse --abbrev-ref HEAD 2>$null)
        $det = ($br -eq 'HEAD')
        [pscustomobject]@{ Ok = ($br -and -not $det); Warn = $true
            Note = $(if (-not $br) { '不是 git 倉(照跑)' } elseif ($det) { '沒在分支上(detached;上次中斷留下的)→ 先 git switch main 再 git pull' } else { "分支 $br" }) }
    }

    $py = $null
    $r2 = Invoke-Step 'Python' {
        $cand = @(@('py', '-3'), @('python'))
        foreach ($c in $cand) {
            if (Get-Command $c[0] -ErrorAction SilentlyContinue) { $script:py = $c; break }
        }
        [pscustomobject]@{ Ok = [bool]$script:py; Note = $(if ($script:py) { $script:py -join ' ' } else { '找不到 py / python' }) }
    }
    if (-not $r2.Ok) { throw 'Python 不在 PATH' }

    $tail = $null
    $r3 = Invoke-Step 'VDF 排程啟動器(MDL022 尾版)' {
        $script:tail = Get-ChildItem (Join-Path $Via 'functional modules\VDF') -Filter 'VDF_MDL022_SafeParallelLaunch_v*.py' |
            Sort-Object Name | Select-Object -Last 1
        [pscustomobject]@{ Ok = [bool]$script:tail; Note = $(if ($script:tail) { $script:tail.Name } else { '不在;請先 git pull' }) }
    }
    if (-not $r3.Ok) { throw 'VDF_MDL022_SafeParallelLaunch 不在這棵樹' }

    $null = Invoke-Step '加速器模組' {
        $acc = Test-Path (Join-Path $Via 'supportive modules\VIA_SuperAccel_Module.py')
        [pscustomobject]@{ Ok = $acc; Warn = (-not $acc); Note = $(if ($acc) { 'VIA_SuperAccel_Module(啟動器的橋閘會再驗一次真的載得到)' } else { '不在 → 啟動器會照實亮黃' }) }
    }
    $gates = @('VIA_NET_CONSENT', 'VIA_SCRAPE_CONSENT') | Where-Object { [Environment]::GetEnvironmentVariable($_) -ne 'YES' }
    $null = Invoke-Step '同意閘(只檢查,不代設)' {
        [pscustomobject]@{ Ok = ($gates.Count -eq 0); Warn = ($gates.Count -gt 0)
            Note = $(if ($gates.Count -eq 0) { '兩道都已由你開啟' } else { '沒開:' + ($gates -join ' · ') + ' → 只用庫內現有資料,不出網' }) }
    }

    $argsList = @('-X', 'utf8', $tail.FullName, 'run', '--start', $Start)
    if ($DataHome) { $argsList += @('--data-home', $DataHome) }
    if ($Dry) { $argsList += '--dry' }
    if ($NoMerge) { $argsList += '--no-merge' }
    Write-Host ''
    Show-Box '開跑' @(
        "起日 $Start → 最新 · 資料家 $(if ($DataHome) { $DataHome } else { '資料家冊(自動)' })",
        "⓪ 暫存併入 $(if ($NoMerge) { '跳過' } elseif ($Dry) { '只列計畫' } else { '只補缺' }) · ① 降壓 BELOW_NORMAL + IO LOW · ② 3 道 + 監工",
        "指令:$($py -join ' ') $($argsList -join ' ')") @(120, 170, 255)
    if ($Check) {
        Write-Host (Paint '  -Check:只做開跑前檢查,沒有叫主流程' @(255, 200, 60))
        $rc = 0
    }
    else {
        Write-Host ''
        $exe = $py[0]
        $pre = @($py | Select-Object -Skip 1)
        & $exe @pre @argsList
        $rc = $LASTEXITCODE
    }
}
catch {
    Write-Host (Paint ("  ✖ " + $_.Exception.Message) @(255, 90, 90))
    $rc = 1
}
finally {
    if ($VT) { Write-Host -NoNewline "$E[?25h" }
    $sw.Stop()
    $lamp = switch ($rc) { 0 { 'GREEN' } 2 { 'YELLOW' } default { 'RED' } }
    $rgb = switch ($lamp) { 'GREEN' { @(80, 220, 140) } 'YELLOW' { @(255, 200, 60) } default { @(255, 90, 90) } }
    Write-Host ''
    Show-Box "結果 $lamp" @(
        "rc $rc · 耗時 $([Math]::Round($sw.Elapsed.TotalMinutes, 1)) 分",
        '收據:VIA_Reports\vdf\stage_merge · VIA_Reports\vdf\datamatrix · VIA_Reports\vdf_lake',
        '這是桌機實跑結果;收尾成功仍要輸出驗證 + 你用滑鼠走完 U/I') $rgb
}
exit $rc
