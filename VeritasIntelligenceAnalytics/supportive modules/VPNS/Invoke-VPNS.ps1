#requires -Version 5.1

# =============================================================================
# def PARAMETERS · BASE PATH 推導所有路徑 (INPUT / TEMP / OUTPUT / ...)
# =============================================================================
param(
    [string]$BasePath = "$PSScriptRoot",
    [switch]$AuditOnly,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

# BASE PATH → 子路徑(與 engine.py 的 config.json paths 對齊)
$def_BASE    = $BasePath
$def_INPUT   = Join-Path $def_BASE "input"
$def_MM      = Join-Path $def_BASE "input\mm"
$def_CONTROL = Join-Path $def_BASE "input\control"
$def_TEMP    = Join-Path $def_BASE "temp"
$def_LAKE    = Join-Path $def_BASE "lake"
$def_OUTPUT  = Join-Path $def_BASE "output"
$def_ARCHIVE = Join-Path $def_BASE "archive"

$def_ENGINE  = Join-Path $def_BASE "engine.py"
$def_CONFIG  = Join-Path $def_BASE "config.json"
$def_UI      = Join-Path $def_BASE "VPNS_UI.html"
$def_REPORT  = Join-Path $def_OUTPUT "report.html"
$def_PANORAMA= Join-Path $def_OUTPUT "panorama_report.html"

# 凍結治理(對齊 NexusCore 規範):不刪檔、不停程序、不裝網路套件、視窗不關
$def_KEEP_OPEN = $true
$def_FORBIDDEN = @("Remove-Item","Stop-Process","Restart-Computer","pip install","npm install","git clone")

# =============================================================================
# def UTILITIES
# =============================================================================
function def_Log {
    param([string]$Level, [string]$Msg)
    $c = switch ($Level) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} "RUN"{"Cyan"} default{"Gray"} }
    Write-Host ("[{0}] [{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level, $Msg) -ForegroundColor $c
}

function def_EnsureDir { param([string]$P)
    if (-not (Test-Path -LiteralPath $P)) { New-Item -ItemType Directory -Path $P -Force | Out-Null; def_Log "OK" "建立: $P" }
}

function def_FindPython {
    foreach ($c in @("python","py","python3")) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function def_Sha256 { param([string]$P)
    if (Test-Path -LiteralPath $P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
    return $null
}

# 不卡斷動態進度條:python 步驟丟到背景 Job,主執行緒邊等邊推進度(加速器手感)
function def_RunWithProgress {
    param([string]$Activity, [string]$Python, [string[]]$PyArgs)
    $job = Start-Job -ScriptBlock { param($py,$a) & $py @a 2>&1 } -ArgumentList $Python, $PyArgs
    $p = 5
    while ($job.State -eq "Running") {
        # 加速器:接近 90% 前快速推進,之後放慢,永不卡在同一格
        if ($p -lt 90) { $p += [Math]::Max(1, [int]((92 - $p) / 6)) } else { $p = 90 }
        Write-Progress -Activity $Activity -Status "$p% · 執行中…" -PercentComplete $p
        Start-Sleep -Milliseconds 120
    }
    $out = Receive-Job $job
    Remove-Job $job -Force
    Write-Progress -Activity $Activity -Status "100% · 完成" -PercentComplete 100
    Start-Sleep -Milliseconds 150
    Write-Progress -Activity $Activity -Completed
    return ($out | Out-String)
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " def VPNS · Veritas Process Nexus · BASE-PATH LAUNCHER (非侵入式智慧疊加層)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    def_Log "RUN" "BASE PATH : $def_BASE"

    # Phase 1 — BASE PATH 自動生成資料夾骨架
    Write-Progress -Activity "VPNS 啟動" -Status "建立路徑骨架" -PercentComplete 8
    foreach ($d in @($def_BASE,$def_INPUT,$def_MM,$def_CONTROL,$def_TEMP,$def_LAKE,$def_OUTPUT,$def_ARCHIVE)) { def_EnsureDir $d }

    # 凍結治理:engine.py 只讀不改,先記 SHA256
    if (Test-Path -LiteralPath $def_ENGINE) {
        def_Log "OK" ("engine.py SHA256 = " + (def_Sha256 $def_ENGINE).Substring(0,16) + "… (copy-only, 不修改)")
    } else {
        def_Log "FAIL" "找不到 engine.py(請與 config.json / VAP_System.html 放在 BASE PATH)"; return
    }

    $python = def_FindPython
    if (-not $python) { def_Log "FAIL" "找不到 Python(請確認 PATH 有 python 或 py)"; return }
    def_Log "OK" "Python: $python"

    Push-Location $def_BASE
    try {
        if (-not $AuditOnly) {
            # Phase 2 — 跑引擎(產出寫入 output/)
            def_Log "RUN" "流程探勘中(台達電電子零組件示範或你的 input/ 資料)…"
            $o1 = def_RunWithProgress -Activity "流程探勘 · auto_run" -Python $python -PyArgs @($def_ENGINE, $def_BASE)
            ($o1 -split "`n" | Select-Object -First 4) | ForEach-Object { if ($_.Trim()) { def_Log "OK" $_.Trim() } }
        }

        # Phase 3 — 三輪全景自審(全面性→順序性→收尾性,≤3 輪提早收尾)
        def_Log "RUN" "三輪全景式分析中(平行可修 / 順序須修,避免九頭龍)…"
        $o2 = def_RunWithProgress -Activity "三輪全景自審 · panorama" -Python $python -PyArgs @($def_ENGINE, $def_BASE, "--audit")
        ($o2 -split "`n") | ForEach-Object { if ($_.Trim()) { def_Log "OK" $_.Trim() } }
    }
    finally { Pop-Location }

    # Phase 4 — 自動跳出 HTML 矩陣報告 + UI
    if (-not $NoOpen) {
        if (Test-Path -LiteralPath $def_PANORAMA) { def_Log "OK" "開啟全景矩陣報告"; Start-Process $def_PANORAMA }
        if (Test-Path -LiteralPath $def_REPORT)   { def_Log "OK" "開啟流程探勘報告"; Start-Process $def_REPORT }
        if (Test-Path -LiteralPath $def_UI)       { def_Log "OK" "開啟系統 UI";       Start-Process $def_UI }
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host " def VPNS 啟動完成" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host (" INPUT   : {0}" -f $def_INPUT)
    Write-Host (" TEMP    : {0}" -f $def_TEMP)
    Write-Host (" OUTPUT  : {0}" -f $def_OUTPUT)
    Write-Host (" REPORT  : {0}" -f $def_REPORT)
    Write-Host (" PANORAMA: {0}" -f $def_PANORAMA)
    Write-Host (" UI      : {0}" -f $def_UI)
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host ("[FATAL] " + $_.Exception.Message) -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    if ($def_KEEP_OPEN) {
        Write-Host ""
        Write-Host "PowerShell 保持開啟,不自動關閉。" -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
