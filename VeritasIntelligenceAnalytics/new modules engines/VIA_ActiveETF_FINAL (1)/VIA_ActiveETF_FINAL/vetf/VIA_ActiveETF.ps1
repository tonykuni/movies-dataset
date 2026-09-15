#requires -Version 7.0
# ============================================================================
# VIA_ActiveETF.ps1  —  整合單一 PowerShell：SYNC（資料）→ ACTIVATE（HTML UI）
# 流程：Windows 對話框選 BASE/DICT → 呼叫 VIA_ActiveETF_System.py sync
#       （抓取→PARQUET 增量→匯出內嵌→注入建 HTML）→ Start-Process 跳出 Console
# LL：param 頂部 / 全名函式 / py 啟動器(LL#16) / Start-Process 開 HTML(LL#12) / append-only
# ============================================================================
param(
    [string]$Root = "",
    [string]$Base = "",
    [string]$Dict = "",
    [string]$AsOf = "",
    [switch]$NoPicker,
    [switch]$NoBrowser,
    [switch]$NoSync
)

$script:Console  = "VIA_ActiveETF_Console.html"
$script:PyModule = "VIA_ActiveETF_System.py"
$script:Template = "console_merged_template.html"

function Write-Status { param([string]$Level,[string]$Message)
    Write-Host ("[{0}][{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level.ToUpper(), $Message) }

function Resolve-Root { param([string]$Hint,[string]$Need)
    $cands = @($Hint,$PSScriptRoot,
        (Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\_hub"),
        (Get-Location).Path)
    foreach ($c in $cands) { if ($c -and (Test-Path (Join-Path $c $Need))) { return (Resolve-Path $c).Path } }
    return $null
}

function Find-Python {
    foreach ($v in @("3.12","3.11","3.13")) {
        try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("py","-$v") } } catch {}
    }
    try { & python -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("python") } } catch {}
    return $null
}

function Invoke-Proc {
    param([string]$Exe,[string[]]$ArgList,[int]$TimeoutSec=900,[string]$Activity="processing")
    $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $Exe
    foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::new(); $p.StartInfo = $psi
    [void]$p.Start()
    $to = $p.StandardOutput.ReadToEndAsync(); $te = $p.StandardError.ReadToEndAsync()
    $sw = [System.Diagnostics.Stopwatch]::StartNew(); $killed = $false
    while (-not $p.HasExited) {
        if ($sw.Elapsed.TotalSeconds -ge $TimeoutSec) { try { $p.Kill($true) } catch {}; $killed = $true; break }
        Write-Progress -Id 1 -Activity $Activity -Status ("{0:N0}s" -f $sw.Elapsed.TotalSeconds) -PercentComplete ([Math]::Min(99, $sw.Elapsed.TotalSeconds / $TimeoutSec * 100))
        Start-Sleep -Milliseconds 120
    }
    Write-Progress -Id 1 -Completed
    [void]$to.Wait(2000); [void]$te.Wait(2000)
    return [pscustomobject]@{ Exit = $(if ($killed) { -1 } else { $p.ExitCode }); Out = $to.Result; Err = $te.Result; Seconds = [Math]::Round($sw.Elapsed.TotalSeconds,2); Killed = $killed }
}

function Select-Folder { param([string]$Title,[string]$Start)
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
        $dlg.Description = $Title; $dlg.UseDescriptionForTitle = $true
        if ($Start -and (Test-Path $Start)) { $dlg.SelectedPath = $Start }
        if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dlg.SelectedPath }
    } catch { $m = Read-Host $Title; if ($m) { return $m } }
    return ""
}

# ---- locate ----
Write-Status INFO "VIA Active ETF — SYNC & ACTIVATE"
$root = Resolve-Root -Hint $Root -Need $script:PyModule
if (-not $root) { Write-Status FAIL "找不到 $script:PyModule。請與其放同資料夾或用 -Root 指定。"; exit 1 }
Write-Status OK "Root = $root"
if (-not (Test-Path (Join-Path $root $script:Template))) { Write-Status WARN "missing template: $script:Template（sync 將沿用現有 Console）" }

# ---- BASE / DICT（Windows I/O 搜尋確認）----
$defDict = Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\_dict\active_etf"
$defBase = Join-Path $defDict "_base"
if (-not $Dict -and -not $NoPicker) { $Dict = Select-Folder -Title "選擇 DICT（資料字典 / PARQUET 庫）" -Start $defDict }
if (-not $Base -and -not $NoPicker) { $Base = Select-Folder -Title "選擇 BASE（基準輸入路徑）" -Start $defBase }
if (-not $Dict) { $Dict = $defDict }; if (-not $Base) { $Base = $defBase }
Write-Status OK ("DICT = {0}" -f $Dict)
Write-Status OK ("BASE = {0}" -f $Base)

# ---- SYNC（呼叫 PY）----
if (-not $NoSync) {
    $py = Find-Python
    if (-not $py) { Write-Status FAIL "找不到 Python（py 啟動器 / python）。"; exit 1 }
    Write-Status INFO ("Python = {0}" -f ($py -join ' '))
    $logo = Join-Path $root "VIA_logo.png"
    $pyArgs = @((Join-Path $root $script:PyModule), "sync",
        "--dict", $Dict, "--base", $Base, "--templates", $root, "--out", $root)
    if (Test-Path $logo) { $pyArgs += @("--logo", $logo) }
    if ($AsOf) { $pyArgs += @("--as-of", $AsOf) }
    Write-Status INFO "Syncing data → PARQUET → building HTML UI...（非阻塞）"
    $r = Invoke-Proc -Exe $py[0] -ArgList ($py[1..($py.Count-1)] + $pyArgs) -TimeoutSec 900 -Activity "VIA sync"
    $code = $r.Exit
    if ($r.Killed) { Write-Status WARN "sync 逾時已結束；仍嘗試以現有 HTML 啟動。" }
    elseif ($code -eq 2) { Write-Status FAIL "eco 守門 BLOCK（套件/環境衝突）。已停止，未啟動 UI。"; exit 2 }
    elseif ($code -ne 0) { Write-Status WARN "sync 回傳非零（$code）；仍嘗試以現有 HTML 啟動。" }
    else { Write-Status OK ("SYNC 完成 {0}s（PARQUET 增量 + HTML UI 已建置）。" -f $r.Seconds) }
} else { Write-Status INFO "NoSync：略過資料同步，直接啟動現有 UI。" }

# ---- ACTIVATE（跳出 HTML UI）----
$consolePath = Join-Path $root $script:Console
if (-not (Test-Path $consolePath)) { Write-Status FAIL "找不到 $script:Console（請先成功 sync）。"; exit 1 }
if ($NoBrowser) { Write-Status OK "Done（NoBrowser）。開啟：$consolePath"; exit 0 }
Write-Status INFO "Activating Console UI..."
Start-Process $consolePath
Write-Status OK "VIA Active ETF 已同步並啟動。BASE/DICT 已注入並凍結。"
exit 0
