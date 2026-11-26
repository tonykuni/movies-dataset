#Requires -Version 5.1
<#
Start-VIA-VDF-v0101.ps1 — VDF 一鍵啟動(PS 只做:找到 Python 啟動器 · 偵測畫面工具 · 叫起來 · 畫進度條)

操作員 2026-11-26:「功能寫在 PY 裡 · PRINT DETAILED SUMMARY MATRIX BY RICH · PS 僅啟動加上檢測 PS 上有無
方案一 PwshSpectreConsole(高質感渲染)· 若無則方案二 零依賴原生 ANSI 平滑進度條」。
流程(判斷全在 Python:VDF_MDL022_SafeParallelLaunch 尾版):
  1. launch --check:開跑前檢查(倉 · 分支 · 加速器真的載到 · 網路工具 · 同意閘);紅就停。
  2. launch --skip-preflight 在背景跑(輸出寫日誌);PS 只讀 Python 寫的進度檔 LAUNCH_PROGRESS.json 畫進度條
     (百分比 · 完成數 · 已耗 · 預估剩餘都由 Python 算好):有 PwshSpectreConsole 且 PowerShell ≥ 7.2 → Spectre 進度條;
     沒有 → 原生 ANSI 八階平滑進度條(不自動安裝模組:安裝只走 VCGC 安裝閘)。
  3. summary:Python 用 Rich 印詳細摘要矩陣(流程 × 燈 × rc × 秒 + 紅黃的原因 → 下一步)。
Ctrl+C:收掉背景 Python 整棵行程樹再離開。本檔不設同意閘。
用法:pwsh -NoProfile -File Start-VIA-VDF-v0101.ps1 [--start 2018-01-01] [--data-home <資料家>] [--dry] [--no-merge] [--check] [--plain]
  --check / --plain / 非互動主控台 → 不畫進度條,直接在前景跑(輸出照常顯示)。
作廢:Start-VIA-VDF-v0100.ps1(仍可用,但沒有進度條與摘要矩陣)。
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { Write-Verbose 'console encoding unchanged' }
$E = [char]27
$tail = Get-ChildItem (Join-Path $PSScriptRoot 'functional modules\VDF') -Filter 'VDF_MDL022_SafeParallelLaunch_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $tail) { Write-Host '[RED] 找不到 VDF_MDL022_SafeParallelLaunch(請先 git pull)' -ForegroundColor Red; exit 1 }
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
$pyArgs = @($py | Select-Object -Skip 1) + @('-X', 'utf8', $tail.FullName)
if (-not $Rest) { $Rest = @() }

if (($Rest -contains '--check') -or ($Rest -contains '--plain') -or -not $Host.UI.SupportsVirtualTerminal) {
    & $py[0] @pyArgs launch @Rest
    exit $LASTEXITCODE
}

# 1. 開跑前檢查(前景)
& $py[0] @pyArgs launch --check @Rest
if ($LASTEXITCODE -eq 1) { exit 1 }

# 2. 背景跑 + 進度條
$prog = Join-Path $PSScriptRoot 'VIA_Reports\vdf\launch\LAUNCH_PROGRESS.json'
Remove-Item $prog -ErrorAction SilentlyContinue
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = Join-Path ([System.IO.Path]::GetTempPath()) "VIA_VDF_launch_$stamp.log"
$quoted = @($pyArgs + @('launch', '--skip-preflight') + $Rest | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
$p = Start-Process -FilePath $py[0] -ArgumentList $quoted -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"
Write-Host "  背景執行中 · 完整輸出 → $log"
function Read-Progress { try { Get-Content $prog -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $null } }
$useSpectre = ($PSVersionTable.PSVersion -ge [version]'7.2') -and [bool](Get-Module -ListAvailable -Name PwshSpectreConsole)
try {
    if ($useSpectre) {
        Import-Module PwshSpectreConsole
        Invoke-SpectreCommandWithProgress -ScriptBlock {
            param($Context)
            $task = $Context.AddTask('VDF 啟動', $true, 100)
            while (-not $p.HasExited) {
                $j = Read-Progress
                if ($j) { $task.Value = [double]$j.pct; $task.Description = "VDF $($j.done)/$($j.total) · $($j.current)" }
                Start-Sleep -Milliseconds 250
            }
            $task.Value = 100
            $task.StopTask()
        }
    }
    else {
        $blocks = @(' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'); $spin = @('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'); $w = 30; $f = 0
        [Console]::CursorVisible = $false
        while (-not $p.HasExited) {
            $j = Read-Progress
            $pct = if ($j) { [double]$j.pct / 100 } else { 0 }
            $x = $pct * $w; $full = [math]::Floor($x); $sub = [math]::Min(7, [int][math]::Floor(($x - $full) * 8))
            $bar = ('█' * $full) + $(if ($full -lt $w) { $blocks[$sub] + (' ' * ($w - $full - 1)) } else { '' })
            $eta = if ($j -and $null -ne $j.eta_s) { [TimeSpan]::FromSeconds([double]$j.eta_s).ToString('mm\:ss') } else { '--:--' }
            $el = if ($j) { [TimeSpan]::FromSeconds([double]$j.elapsed_s).ToString('mm\:ss') } else { '00:00' }
            $cnt = if ($j) { "$($j.done)/$($j.total)" } else { '…' }
            $cur = if ($j) { [string]$j.current } else { '開始' }
            [Console]::Write("`r$E[36m$($spin[$f % 10])$E[0m [$E[38;5;73m$bar$E[0m] $E[1m{0,5:N1}%$E[0m ($cnt) | $el / ETA $eta | $cur$E[K" -f ($pct * 100))
            $f++; Start-Sleep -Milliseconds 120
        }
        [Console]::Write("`r$E[32m✔$E[0m [$E[38;5;73m$('█' * $w)$E[0m] $E[1m100.0%$E[0m$E[K`n")
    }
}
finally {
    [Console]::CursorVisible = $true
    if (-not $p.HasExited) {
        Write-Host '  中斷:收掉背景 Python 行程樹'
        if ($IsWindows -or $env:OS -eq 'Windows_NT') { & taskkill /PID $p.Id /T /F | Out-Null } else { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    }
}
$p.WaitForExit()
$rc = $p.ExitCode

# 3. Rich 詳細摘要矩陣
& $py[0] @pyArgs summary
Write-Host "  完整輸出 → $log"
exit $rc
