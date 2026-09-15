#requires -Version 7.0
# ============================================================================
# VIA_DeployAll.ps1  —  ONE PowerShell handle-all（原子化貼上安全 / 不關閉視窗 / 自動補裝）
#   用法（在你開著的 PS7 直接跑，視窗不會關）：
#       & "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf\VIA_DeployAll.ps1"
#   或整段貼進 PS7（整塊 & { } 一次解析，不會有 elseif 逐行錯誤）。
#   全程非阻塞、逾時不卡死；缺 pyarrow/pandas/yfinance 會自動補裝後重探。
# ============================================================================
& {
    # ---- 可改參數（保持預設即可）----
    $Root       = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf"
    $ModulesDir = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\supportive modules"
    $DictRoot   = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\_dict\active_etf"
    $UpdateTime = "08:00"
    $DoInstall  = $true
    $DoAddPath  = $true
    $DoSchedule = $true
    $ProbeTimeoutSec = 60
    $InstallTimeoutSec = 1200
    $TaskName = "VIA_ActiveETF_DailyUpdate"

    $Core = @("VIA_ActiveETF_System.py","console_merged_template.html","VIA_ActiveETF.ps1","VIA_ActiveETF_Console.html")
    $Used = @("VeritasAegisNexus.py","VeritasCeleritas.py","VIA_EnvManager.py","VIA_SSOT_Unified.py")
    $Report = [ordered]@{}
    $swAll = [System.Diagnostics.Stopwatch]::StartNew()

    function Write-Status { param([string]$Level,[string]$Message)
        $col = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Gray"} }
        Write-Host ("[{0}][{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level.ToUpper(), $Message) -ForegroundColor $col }

    function Invoke-Proc {
        param([string]$Exe,[string[]]$ArgList,[int]$TimeoutSec=60,[string]$Activity="processing")
        $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $Exe
        foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
        $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::new(); $proc.StartInfo = $psi
        [void]$proc.Start()
        $to = $proc.StandardOutput.ReadToEndAsync(); $te = $proc.StandardError.ReadToEndAsync()
        $sw = [System.Diagnostics.Stopwatch]::StartNew(); $killed = $false
        while (-not $proc.HasExited) {
            if ($sw.Elapsed.TotalSeconds -ge $TimeoutSec) { try { $proc.Kill($true) } catch {}; $killed = $true; break }
            Write-Progress -Id 1 -Activity $Activity -Status ("{0:N0}s / {1}s" -f $sw.Elapsed.TotalSeconds,$TimeoutSec) -PercentComplete ([Math]::Min(99,$sw.Elapsed.TotalSeconds/$TimeoutSec*100))
            Start-Sleep -Milliseconds 100
        }
        Write-Progress -Id 1 -Completed
        [void]$to.Wait(2000); [void]$te.Wait(2000)
        return [pscustomobject]@{ Exit = $(if ($killed) { -1 } else { $proc.ExitCode }); Out = $to.Result; Err = $te.Result; Seconds = [Math]::Round($sw.Elapsed.TotalSeconds,2); Killed = $killed }
    }

    Write-Status INFO "VIA Active ETF - DeployAll (atomic / non-blocking / keep-open)"
    if (-not (Test-Path $Root)) { Write-Status FAIL "vetf not found: $Root"; return }

    # 探測 probe（一次取回 python/套件/eco）
    $probe = @'
import json,sys
root = sys.argv[1] if len(sys.argv)>1 else "."
r = {"python":{"version":".".join(map(str,sys.version_info[:3])),"exe":sys.executable}}
pk = {}
for p in ["pyarrow","pandas","numpy","yfinance"]:
    try: pk[p] = getattr(__import__(p),"__version__","?")
    except Exception: pk[p] = None
r["packages"] = pk
try: r["numpy_ok"] = (pk["numpy"] is None) or (int((pk["numpy"] or "1").split(".")[0]) < 2)
except Exception: r["numpy_ok"] = True
eco = None
try:
    sys.path.insert(0, root); import VIA_ActiveETF_System as S
    eco = S.check_eco(["pyarrow","pandas","yfinance"], r["python"]["version"], "windows")["decision"]
except Exception: eco = None
r["eco"] = eco
sys.stdout.write(json.dumps(r))
'@
    $probePath = Join-Path $env:TEMP "via_probe.py"
    [IO.File]::WriteAllText($probePath, $probe, [System.Text.UTF8Encoding]::new($false))

    function Get-Probe { param([string[]]$Launcher)
        $a = @($Launcher[1..($Launcher.Count-1)] + @($probePath,$Root))
        $r = Invoke-Proc -Exe $Launcher[0] -ArgList $a -TimeoutSec $ProbeTimeoutSec -Activity ("probe ({0})" -f ($Launcher -join ' '))
        if ($r.Exit -eq 0 -and $r.Out.Trim().StartsWith("{")) { try { return ($r.Out | ConvertFrom-Json) } catch { return $null } }
        return $null
    }

    $cands = @(@("py","-3.12"),@("py","-3.11"),@("py","-3.13"),@("python"))
    $info = $null; $pyL = $null
    foreach ($c in $cands) { $i = Get-Probe -Launcher $c; if ($i) { $info = $i; $pyL = $c; break } }
    if (-not $info) { Write-Status FAIL "no usable Python."; return }
    $pyVer = $info.python.version; $pyReal = $info.python.exe
    Write-Status OK ("Python = {0} ({1})" -f $pyVer,$pyReal)
    $pkg = $info.packages

    # ---- AUTO-INSTALL 缺的（pyarrow/pandas 必需、yfinance 選用；numpy 鎖 <2.0）----
    if ($DoInstall) {
        $need = [System.Collections.Generic.List[string]]::new()
        foreach ($p in @("pyarrow","pandas")) { if (-not $pkg.$p) { $need.Add($p) } }
        if (-not $pkg.yfinance) { $need.Add("yfinance") }
        if (-not $pkg.numpy) { $need.Add("numpy>=1.24,<2.0") }
        if ($need.Count) {
            Write-Status INFO ("INSTALL (non-blocking): {0}" -f ($need -join ' '))
            $pa = @($pyL[1..($pyL.Count-1)] + @("-m","pip","install","--upgrade") + $need)
            $r = Invoke-Proc -Exe $pyL[0] -ArgList $pa -TimeoutSec $InstallTimeoutSec -Activity "pip install"
            if ($r.Killed) { Write-Status WARN ("pip timeout {0}s" -f $InstallTimeoutSec) }
            elseif ($r.Exit -eq 0) { Write-Status OK ("installed {0}s; re-probing..." -f $r.Seconds); $i2 = Get-Probe -Launcher $pyL; if ($i2) { $info = $i2; $pkg = $info.packages } }
            else { Write-Status WARN ("pip exit {0}: {1}" -f $r.Exit, ($r.Err.Trim() -split "`n" | Select-Object -Last 1)) }
        } else { Write-Status OK "packages already complete." }
    }

    # ---- AUDIT 套件/eco ----
    $conflicts = [System.Collections.Generic.List[string]]::new()
    $warnings  = [System.Collections.Generic.List[string]]::new()
    foreach ($p in @("pyarrow","pandas","numpy","yfinance")) {
        $v = $pkg.$p
        if ($v) { Write-Status OK ("pkg {0} = {1}" -f $p,$v) }
        elseif ($p -eq "yfinance") { Write-Status WARN "yfinance still missing (real prices only)"; $warnings.Add("opt_missing:yfinance") }
        elseif ($p -eq "numpy") { Write-Status INFO "numpy not detected" }
        else { Write-Status WARN ("required still missing: {0} (daily sync needs it)" -f $p); $warnings.Add("req_missing:$p") }
    }
    if (-not $info.numpy_ok) { Write-Status FAIL ("numpy {0} violates <2.0" -f $pkg.numpy); $conflicts.Add("numpy>=2.0") }
    if ($info.eco -eq "BLOCK") { Write-Status FAIL "eco-check BLOCK"; $conflicts.Add("eco_block") }
    elseif ($info.eco -eq "PASS") { Write-Status OK "eco-check PASS" }
    else { Write-Status WARN "eco-check N/A (System.py import failed - pyarrow/pandas?)" }

    $missCore = @($Core | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
    foreach ($m in $missCore) { Write-Status FAIL ("missing core: {0}" -f $m); $conflicts.Add("missing_core:$m") }
    $haveUsed = @($Used | Where-Object { (Test-Path (Join-Path $ModulesDir $_)) -or (Test-Path (Join-Path $Root $_)) })
    Write-Status OK ("supportive ready {0}/4" -f $haveUsed.Count)
    $edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe","$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1

    # ---- GATE（硬衝突才停；不關閉視窗，用 return）----
    if ($conflicts.Count -gt 0) {
        Write-Status FAIL ("conflicts: {0}" -f ($conflicts -join '; '))
        Write-Status FAIL "stop (no schedule). fix then re-run."
        return
    }
    Write-Status OK "audit PASS - baseline locked."

    # ---- PATH ----
    if ($DoAddPath) {
        $cur = [Environment]::GetEnvironmentVariable("Path","User"); if (-not $cur) { $cur = "" }
        if ($cur -notlike "*$Root*") { [Environment]::SetEnvironmentVariable("Path",($cur.TrimEnd(';')+";"+$Root),"User"); Write-Status OK "vetf added to user PATH." }
        else { Write-Status OK "PATH already has vetf." }
    }

    # ---- DAILY SCHEDULE ----
    $sys = Join-Path $Root "VIA_ActiveETF_System.py"
    $dailyArgs = @($sys,"sync","--dict",$DictRoot,"--templates",$Root,"--out",$Root)
    $logo = Join-Path $Root "VIA_logo.png"; if (Test-Path $logo) { $dailyArgs += @("--logo",$logo) }
    if ($DoSchedule) {
        try {
            $action  = New-ScheduledTaskAction -Execute $pyReal -Argument ($dailyArgs -join ' ') -WorkingDirectory $Root
            $trigger = New-ScheduledTaskTrigger -Daily -At $UpdateTime
            $set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
            Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $set -Description "VIA Active ETF daily sync + console rebuild" -Force | Out-Null
            Write-Status OK ("daily update scheduled: {0} @ {1}" -f $TaskName,$UpdateTime)
        } catch { Write-Status WARN ("schedule failed (admin?): {0}" -f $_.Exception.Message) }
    }

    # ---- 首次 sync（把資料建起來，讓 Console 有真內容）----
    Write-Status INFO "initial sync (non-blocking)..."
    $rs = Invoke-Proc -Exe $pyL[0] -ArgList @($pyL[1..($pyL.Count-1)] + $dailyArgs) -TimeoutSec $InstallTimeoutSec -Activity "VIA sync"
    if ($rs.Killed) { Write-Status WARN "sync timeout." }
    elseif ($rs.Exit -eq 0) { Write-Status OK ("sync done {0}s." -f $rs.Seconds) }
    else { Write-Status WARN ("sync exit {0}: {1}" -f $rs.Exit, (($rs.Err.Trim() -split "`n" | Select-Object -Last 1))) }

    # ---- SNAPSHOT / CLOSEOUT ----
    $swAll.Stop()
    $Report.python = @{ version=$pyVer; exe=$pyReal; launcher=($pyL -join ' ') }
    $Report.packages = $pkg; $Report.eco = $info.eco
    $Report.autodeploy = @{ root=$Root; modules_dir=$ModulesDir; dict_root=$DictRoot; task=$TaskName; time=$UpdateTime; exec=$pyReal; edge=$edge
        reinstall_cmd=("{0} -m pip install --upgrade pyarrow pandas ""numpy>=1.24,<2.0"" yfinance" -f $pyReal) }
    $Report.warnings = @($warnings); $Report.result = "DEPLOYED"; $Report.elapsed_sec = [Math]::Round($swAll.Elapsed.TotalSeconds,2)
    [IO.File]::WriteAllText((Join-Path $Root "VIA_ActiveETF_DeployConfig.json"), ($Report | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))

    Write-Host ""
    Write-Status OK "============ CLOSEOUT ============"
    Write-Status OK ("env: Python {0} . numpy<2.0 . eco {1}" -f $pyVer, $info.eco)
    Write-Status OK ("daily update: {0} @ {1}" -f $TaskName, $UpdateTime)
    Write-Status OK ("elapsed: {0}s (non-blocking / single-probe / auto-install)" -f $Report.elapsed_sec)
    if ($warnings.Count) { Write-Status WARN ("notes: {0}" -f ($warnings -join '; ')) }
    Write-Status OK "open UI: double-click VIA_ActiveETF_Console.html (or run VIA_ActiveETF.ps1)"
    Write-Status OK "done. (PowerShell stays open)"
}
