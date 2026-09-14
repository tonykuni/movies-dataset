# =====================================================================================
# VIA_PS_PyProgress_Module.ps1 — 所有 py 指令的統一啟動包裝(批486)
# 操作員令:「ps 檔案要加 20 個加速器動態進度條;所有 py 指令都要加速加速器」
# -------------------------------------------------------------------------------------
# 先查再造:PS 側 20 加速器實體模組早在 supportive modules\VIA_PS_Accel_Module.ps1(TOOL-101,批102):
#   $VIA_ACCEL20 冊(20 條)+ Write-VIAProgress(16 動態進度條)+ Invoke-VIAGuarded(18 看門狗)。
#   本模組**不重造**那 20 條,只把它們接到「每一次 python 啟動」上:
#     ① 每個 PowerShell 視窗第一次跑 python:SUP_MDL737 --activate 真點亮(Celeritas 冊;缺席誠實說缺,不點假燈),
#        同時用 $VIA_ACCEL20 走一條 20 格的點亮進度條;之後同視窗不重點(快取 $env:VIA_ACCEL_LIT)。
#     ② 每一次 python 子行程:邊跑邊轉播(stdout 走 pipeline=上游 `| Out-String` 照樣抓得到;stderr 灰字),
#        Write-VIAProgress 動態條(跑了幾秒 · 引擎最後一行),逾時 Kill 整樹=不卡斷,$LASTEXITCODE 照真回。
#     ③ 加速器本體(批476 啟動層 sitecustomize)由 PYTHONPATH 帶進子行程——這裡只負責「看得見」。
#   短令冊 v0189 起,三種 python 呼叫形狀一律改走 Invoke-VIAPython;啟動器逐個接。
# =====================================================================================

if (-not (Get-Variable -Name VIA_ACCEL20 -Scope Script -ErrorAction SilentlyContinue)) {
    $accelMod = Join-Path $PSScriptRoot "VIA_PS_Accel_Module.ps1"
    if (Test-Path -LiteralPath $accelMod) { . $accelMod }
}

function Get-VIAPyProgRoot {
    # 本檔在 <VIA>\supportive modules\ → 上一層
    return (Split-Path -Parent $PSScriptRoot)
}

function Show-VIAAccel20 {
    # 20 加速器點亮(一視窗一次;-Force 重點)。真點=SUP_MDL737 --activate;條=$VIA_ACCEL20 二十格。
    param([switch]$Force)
    if ($env:VIA_ACCEL_LIT -and -not $Force) { return }
    $root = Get-VIAPyProgRoot
    $m = Get-ChildItem -LiteralPath (Join-Path $root "supportive modules") -Filter "SUP_MDL737_SuperAccelModule_v*.py" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    $summary = ""
    if ($m) {
        try {
            $py = if (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { Get-VIAEnvPython "core" } else { "python" }
            $o = & $py $m.FullName --activate 2>&1 | Out-String
            $summary = (($o -split "`r?`n") | Where-Object { $_ -match "lib 冊|Celeritas" } | Select-Object -First 1)
            if (-not $summary) { $summary = (($o -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -First 1) }
        } catch { $summary = "點名例外:" + $_.Exception.Message }
    } else { $summary = "SUP_MDL737 缺檔(誠實;不影響跑,只是沒加速)" }
    $names = if (Get-Variable -Name VIA_ACCEL20 -Scope Script -ErrorAction SilentlyContinue) { $script:VIA_ACCEL20 } else { $null }
    if ($names) {
        $i = 0
        foreach ($k in $names.Keys) {
            $i++
            Write-Progress -Id 12 -Activity "VIA 20 加速器點亮" -Status ("{0}/20 {1}" -f $k, $names[$k]) -PercentComplete ([int](100 * $i / 20))
            Start-Sleep -Milliseconds 25
        }
        Write-Progress -Id 12 -Activity "VIA 20 加速器點亮" -Completed
    }
    $env:VIA_ACCEL_LIT = "1"
    Write-Host ("  [加速器] 20 格點亮 · " + ("" + $summary).Trim()) -ForegroundColor DarkCyan
}

function Invoke-VIAPython {
    # 所有 py 指令的統一啟動:Invoke-VIAPython [-Family vdf|vrn|vap|core] [-Python <exe>] [-TimeoutSec N] <script或-c> [args...]
    [CmdletBinding(PositionalBinding = $false)]
    param(
        [string]$Family = "",
        [string]$Python = "",
        [int]$TimeoutSec = 0,
        [Parameter(ValueFromRemainingArguments = $true)][object[]]$Rest
    )
    $argv = @()
    foreach ($r in $Rest) { if ($null -eq $r) { continue }; if ($r -is [System.Array]) { foreach ($x in $r) { if ($null -ne $x -and "$x" -ne "") { $argv += "$x" } } } elseif ("$r" -ne "") { $argv += "$r" } }
    if ($argv.Count -eq 0) { Write-Host "  [Invoke-VIAPython] 沒有給要跑的 python 檔" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $exe = if ($Python) { $Python } elseif (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { Get-VIAEnvPython $Family } else { "python" }
    $isAccelSelf = ($argv[0] -match "SUP_MDL737_SuperAccelModule")
    if (-not $isAccelSelf) { Show-VIAAccel20 }
    if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
    if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }
    $tmp = [IO.Path]::GetTempPath(); $tag = "via_py_" + $PID + "_" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $outF = Join-Path $tmp ($tag + ".out"); $errF = Join-Path $tmp ($tag + ".err")
    $quoted = ($argv | ForEach-Object { $a = "$_" -replace '"', '\"'; if ($a -match '\s|^$') { '"' + $a + '"' } else { $a } }) -join ' '
    $name = [IO.Path]::GetFileName($argv[0]); if ($name -eq "-c") { $name = "python -c" }
    $t0 = Get-Date
    try {
        $p = Start-Process -FilePath $exe -ArgumentList $quoted -NoNewWindow -PassThru -RedirectStandardOutput $outF -RedirectStandardError $errF
    } catch {
        Write-Host ("  [Invoke-VIAPython] 起不來:" + $_.Exception.Message) -ForegroundColor Red; $global:LASTEXITCODE = 1; return
    }
    $posO = 0L; $posE = 0L; $timedOut = $false
    # 排水:位置走 [ref]、行走 pipeline(第一版把行和位置一起回傳,行全被 $posO 吞掉=捕捉 0 行);
    # 用位元組找最後一個 \n 定位,不用重算文字長度(Windows 的 \r\n 會讓文字長度漂移)。
    $drain = {
        param($Path, [ref]$Pos, $IsErr, $Final)
        if (-not (Test-Path -LiteralPath $Path)) { return }
        try {
            $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            try {
                $len = $fs.Length; if ($len -le $Pos.Value) { return }
                [void]$fs.Seek($Pos.Value, [IO.SeekOrigin]::Begin)
                $buf = New-Object byte[] ($len - $Pos.Value); $n = $fs.Read($buf, 0, $buf.Length)
                $cut = [Array]::LastIndexOf($buf, [byte]10, $n - 1)
                if ($cut -lt 0) { if (-not $Final) { return }; $cut = $n - 1 }
                $text = [Text.Encoding]::UTF8.GetString($buf, 0, $cut + 1)
                $Pos.Value = $Pos.Value + $cut + 1
                foreach ($ln in ($text -split "`n")) {
                    $ln = $ln.TrimEnd("`r"); if ($ln -eq "") { continue }
                    $script:__viaLast = $ln
                    if ($IsErr) { Write-Host ("  " + $ln) -ForegroundColor DarkGray } else { Write-Output $ln }
                }
            } finally { $fs.Close() }
        } catch { }
    }
    $script:__viaLast = ""
    while (-not $p.HasExited) {
        & $drain $outF ([ref]$posO) $false $false
        & $drain $errF ([ref]$posE) $true $false
        $el = [int]((Get-Date) - $t0).TotalSeconds
        if ($TimeoutSec -gt 0 -and $el -ge $TimeoutSec) { try { $p.Kill($true) } catch {}; $timedOut = $true; break }
        $pct = [int](($el % 30) * 100 / 30)   # 動態條:不知道總長就用 30 秒一輪的脈動
        $st = if ($script:__viaLast) { ("{0}s · {1}" -f $el, $script:__viaLast.Substring(0, [Math]::Min(90, $script:__viaLast.Length))) } else { "{0}s · 起跑中" -f $el }
        if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) { Write-VIAProgress -Activity ("VIA · " + $name + " · 加速器 20/20") -Status $st -Percent $pct -Id 13 }
        else { Write-Progress -Id 13 -Activity ("VIA · " + $name) -Status $st -PercentComplete $pct }
        Start-Sleep -Milliseconds 250
    }
    try { $p.WaitForExit() } catch {}
    & $drain $outF ([ref]$posO) $false $true
    & $drain $errF ([ref]$posE) $true $true
    Write-Progress -Id 13 -Activity ("VIA · " + $name) -Completed
    $rc = if ($timedOut) { 124 } else { try { $p.WaitForExit(); $p.ExitCode } catch { 1 } }
    Remove-Item -LiteralPath $outF, $errF -Force -ErrorAction SilentlyContinue
    if ($timedOut) { Write-Host ("  [Invoke-VIAPython] 逾 {0}s 已停(不卡斷;只殺自己生的樹)" -f $TimeoutSec) -ForegroundColor Yellow }
    $global:LASTEXITCODE = $rc
}
