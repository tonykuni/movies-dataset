param(
    [switch]$NoBrowser,
    [switch]$Stop,
    [switch]$Governance,
    [string]$PromptSource = "",
    [string]$PromptFile = "",
    [switch]$OpenReport
)

#requires -Version 7.0
$ErrorActionPreference = "Stop"

# ==============================================================================
# VIA Forge Launcher  (Orchestrator / Bootstrapper)
# ------------------------------------------------------------------------------
# Role split (locked):
#   PowerShell = detect Python / build venv / install deps / make paths /
#                self-test / launch backend / open UI / health check / stop
#   Python     = via_forge.py (engine) + via_server.py (thin backend)
#   HTML       = ui/index.html, talks to loopback JSON API
#
# LL conventions: param() first; no aliases; no Read-Host; no exit;
#                 ProcessStartInfo for subprocess; UTF8 no-BOM; append-only.
# ==============================================================================

$script:Root       = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:ConfigPath = Join-Path $script:Root "via_forge_config.json"
$script:PidFile    = Join-Path $script:Root "runtime\server.pid"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) { "OK"{"Green"} "WARN"{"Yellow"} "ERR"{"Red"} "STEP"{"Cyan"} default{"Gray"} }
    Write-Host ("[{0}] {1}" -f $ts, $Message) -ForegroundColor $color
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Get-Config {
    if (-not (Test-Path $script:ConfigPath)) { throw "Config not found: $script:ConfigPath" }
    return Get-Content $script:ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Invoke-Proc {
    param([string]$File, [string]$Arguments, [string]$WorkDir = $script:Root, [switch]$Quiet)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $File; $psi.Arguments = $Arguments; $psi.WorkingDirectory = $WorkDir
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEnd(); $err = $p.StandardError.ReadToEnd(); $p.WaitForExit()
    if (-not $Quiet -and $err) {
        foreach ($line in ($err -split "`n")) {
            if ($line -match '@@PROGRESS\|(\d+)\|(.+)') { Write-Log ("  {0,3}%  {1}" -f $Matches[1], $Matches[2].Trim()) "STEP" }
        }
    }
    return @{ ExitCode = $p.ExitCode; Out = $out; Err = $err }
}

function Resolve-Python {
    param($Config)
    $cands = @()
    foreach ($v in $Config.environment.python_fallbacks) { $cands += "py -$v" }
    $cands += "python"
    foreach ($c in $cands) {
        $parts = $c -split '\s+', 2; $exe = $parts[0]; $a = if ($parts.Count -gt 1) { $parts[1] } else { "" }
        try {
            $r = Invoke-Proc -File $exe -Arguments ("{0} --version" -f $a).Trim() -Quiet
            if ($r.ExitCode -eq 0 -and ($r.Out + $r.Err) -match "Python 3") {
                Write-Log ("Found Python: {0}" -f $c) "OK"; return @{ Cmd = $exe; Args = $a }
            }
        } catch { }
    }
    throw "No suitable Python 3 found. Install Python 3.11/3.12."
}

function Initialize-Paths {
    param($Config)
    Write-Log "Building directory tree..." "STEP"
    foreach ($k in @("root","inbox","runtime","ledger","cache","output","reports","exports","logs","quarantine")) {
        $p = $Config.paths.$k
        if ($p -and -not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null; Write-Log ("  + {0}" -f $p) }
    }
    Write-Log "Paths ready." "OK"
}

function Initialize-Venv {
    param($Config, $Python)
    $venv = $Config.paths.venv; $venvPy = Join-Path $venv "Scripts\python.exe"
    if (-not (Test-Path $venvPy)) {
        Write-Log ("Creating venv: {0}" -f $venv) "STEP"
        $r = Invoke-Proc -File $Python.Cmd -Arguments ("{0} -m venv `"{1}`"" -f $Python.Args, $venv).Trim() -Quiet
        if ($r.ExitCode -ne 0) { throw "venv creation failed: $($r.Err)" }
        Write-Log "venv created." "OK"
    } else { Write-Log "venv exists; reusing." "OK" }

    if ($Config.environment.auto_install_deps) {
        Write-Log "Upgrading pip..." "STEP"
        Invoke-Proc -File $venvPy -Arguments "-m pip install --upgrade pip --quiet" -Quiet | Out-Null
        $pkgs = @(); $pkgs += $Config.environment.packages_required; $pkgs += $Config.environment.packages_optional
        $pkgs = $pkgs | Where-Object { $_ -and ($_ -notin $Config.environment.packages_banned) }
        Write-Log ("Installing {0} packages (optional -> graceful degrade if any fail)..." -f $pkgs.Count) "STEP"
        foreach ($pkg in $pkgs) {
            $r = Invoke-Proc -File $venvPy -Arguments ("-m pip install `"{0}`" --quiet" -f $pkg) -Quiet
            if ($r.ExitCode -eq 0) { Write-Log ("  ok  {0}" -f $pkg) "OK" }
            else { Write-Log ("  skip {0} (optional)" -f $pkg) "WARN" }
        }
        if ($Config.environment.numpy_pin) {
            Invoke-Proc -File $venvPy -Arguments ("-m pip install `"numpy{0}`" --quiet" -f $Config.environment.numpy_pin) -Quiet | Out-Null
        }
    }
    return $venvPy
}

function Test-Engines {
    param($VenvPy)
    Write-Log "Running engine self-tests..." "STEP"
    $all = $true
    foreach ($e in @("via_forge.py --selftest", "via_server.py --selftest", "via_connect.py --selftest", "via_pmine.py --selftest", "via_sink.py --selftest", "via_panorama.py --selftest")) {
        $r = Invoke-Proc -File $VenvPy -Arguments $e -Quiet
        $c = $r.Out + $r.Err
        if ($c -match "(\d+) PASS / (\d+) FAIL") {
            $pass = [int]$Matches[1]; $fail = [int]$Matches[2]
            if ($fail -eq 0) { Write-Log ("  {0,-26} {1} PASS" -f $e, $pass) "OK" }
            else { Write-Log ("  {0,-26} {1} PASS / {2} FAIL" -f $e, $pass, $fail) "ERR"; $all = $false }
        } else { Write-Log ("  {0,-26} no result" -f $e) "WARN" }
    }
    return $all
}

function Start-Backend {
    param($VenvPy)
    Write-Log "Launching backend..." "STEP"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $VenvPy
    $b = if ($NoBrowser) { "--no-browser" } else { "" }
    $psi.Arguments = ("via_server.py {0}" -f $b).Trim()
    $psi.WorkingDirectory = $script:Root; $psi.UseShellExecute = $false
    $proc = [System.Diagnostics.Process]::Start($psi)
    if (-not (Test-Path (Split-Path $script:PidFile))) { New-Item -ItemType Directory -Path (Split-Path $script:PidFile) -Force | Out-Null }
    Write-Utf8NoBom -Path $script:PidFile -Content ([string]$proc.Id)
    Write-Log ("Backend PID {0}" -f $proc.Id) "OK"; Start-Sleep -Seconds 2
    return $proc
}

function Test-Health {
    param($Config)
    for ($i = 0; $i -lt 10; $i++) {
        try {
            $r = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/api/health" -f $Config.server.port) -TimeoutSec 3
            if ($r.status -eq "ok") { Write-Log ("Health OK  ·  {0} formats supported" -f $r.supported.Count) "OK"; return $true }
        } catch { Start-Sleep -Milliseconds 600 }
    }
    Write-Log "Health check timed out." "WARN"; return $false
}

function Stop-Backend {
    if (Test-Path $script:PidFile) {
        try {
            $cfg = Get-Config
            Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/api/shutdown" -f $cfg.server.port) -Method Post -TimeoutSec 3 | Out-Null
            Write-Log "Sent graceful shutdown." "OK"
        } catch { Write-Log "Shutdown endpoint unreachable; process may have exited." "WARN" }
    } else { Write-Log "No PID file; nothing to stop." "WARN" }
}

# ==================================================================== main flow
Write-Host ""
Write-Host "  VIA Forge · Consolidated Stack" -ForegroundColor Cyan
Write-Host "  1 strong engine + thin backend + HTML front-end" -ForegroundColor DarkGray
Write-Host ("  " + ("=" * 52)) -ForegroundColor DarkGray
Write-Host ""

if ($Stop) { Stop-Backend; return }

# Governance dispatch: run the static-only prompt-injection orchestrator instead
# of launching the stack. Operates on the canonical VIA supportive tree.
if ($Governance) {
    $govScript = Join-Path $PSScriptRoot "Invoke-VIA-SupportiveCore-PromptInjection.ps1"
    if (-not (Test-Path -LiteralPath $govScript)) {
        Write-Log "Governance script not found next to launcher." "ERR"; return
    }
    Write-Log "Dispatching to governed prompt-injection (static-only)..." "INFO"
    $govArgs = @{}
    if ($PromptSource) { $govArgs["PromptSource"] = $PromptSource }
    if ($PromptFile)   { $govArgs["PromptFile"] = $PromptFile }
    if ($OpenReport)   { $govArgs["OpenReport"] = $true }
    & $govScript @govArgs
    return
}

$config = Get-Config
$python = Resolve-Python -Config $config
Initialize-Paths -Config $config
$venvPy = Initialize-Venv -Config $config -Python $python
if (-not (Test-Engines -VenvPy $venvPy)) { Write-Log "Engine self-tests failed. Fix before serving." "ERR"; return }
Start-Backend -VenvPy $venvPy | Out-Null
Test-Health -Config $config | Out-Null

Write-Host ""
Write-Log ("UI ready: http://127.0.0.1:{0}/" -f $config.server.port) "OK"
Write-Log "Stop with:  .\VIA_Forge_Launcher.ps1 -Stop" "INFO"
Write-Host ""

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
