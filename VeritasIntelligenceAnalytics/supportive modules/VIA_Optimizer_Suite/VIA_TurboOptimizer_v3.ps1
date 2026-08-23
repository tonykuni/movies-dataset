#requires -Version 7.0
param(
    [int]$Port = 8870,
    [int]$AgeDays = 3,
    [switch]$NoBrowser,
    [switch]$SelfTest
)

# ============================================================================
#  VIA Turbo Optimizer  v2  (VeritasIntelligenceAnalytics)
#  EMBEDDED single-file system: backend HttpListener + animated HTML front-end.
#  Safe disk cleanup + CPU/DRAM/Memory acceleration. Never auto-kills processes.
#  Self-contained, append-only log, inline self-test (-SelfTest).
#  PS7 rules honored: param() top, no <# #>, ${var}:, -f not on Write-Host,
#  ProcessStartInfo (no Start-Job / no -Args splat), single-quote here-string
#  + .Replace(), [IO.File]::WriteAllText, ordered .Contains().
# ============================================================================

$ErrorActionPreference = 'Continue'

# ---- Config / paths --------------------------------------------------------
$script:Base      = Join-Path $env:LOCALAPPDATA 'OptimizeTool'
$script:LogDir    = Join-Path $script:Base 'logs'
$script:LogFile   = Join-Path $script:LogDir 'OptimizeLog.txt'
$script:WebDir    = Join-Path $script:Base 'web'
$script:FrontFile = Join-Path $script:WebDir 'VIA_Optimizer_UI.html'
$script:Stop      = $false
$script:HighPerfGuid = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
$script:BalancedGuid = '381b4222-f694-41f0-9685-ff5bb260df2e'
$script:EnvMgrCanonical = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py'

foreach ($d in @($script:Base, $script:LogDir, $script:WebDir)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# ---- Logging (append-only) -------------------------------------------------
function Write-Log {
    param([string]$Msg, [string]$Level = 'INFO')
    $line = ('{0} | {1,-5} | {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Msg)
    try { [System.IO.File]::AppendAllText($script:LogFile, $line + [Environment]::NewLine, [System.Text.Encoding]::UTF8) } catch {}
    Write-Host $line
}

# ---- Admin / safety --------------------------------------------------------
$script:IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$script:SafeRoots = @(
    (Join-Path $env:LOCALAPPDATA 'Temp'),
    $env:TEMP,
    'C:\Windows\Temp',
    'C:\ProgramData\Microsoft\Windows\WER',
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Explorer'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\INetCache'),
    (Join-Path $env:LOCALAPPDATA 'CrashDumps'),
    'C:\Windows\SoftwareDistribution\Download'
) | ForEach-Object { $_.TrimEnd('\').ToLowerInvariant() } | Select-Object -Unique

function Test-SafePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    # Normalize (resolve .. and .) WITHOUT requiring the path to exist, so a
    # crafted traversal cannot escape the whitelist. GetFullPath is self-contained.
    try { $full = [System.IO.Path]::GetFullPath($Path) } catch { return $false }
    $p = $full.TrimEnd('\').ToLowerInvariant()
    foreach ($root in $script:SafeRoots) {
        if ($p -eq $root -or $p.StartsWith($root + '\')) { return $true }
    }
    return $false
}

# ---- Working-set trim (safe, reversible; NOT a process kill) ---------------
$script:CsLoaded = $false
$csTrim = @'
using System;
using System.Runtime.InteropServices;
public static class VIAMem {
    [DllImport("kernel32.dll")]
    static extern bool SetProcessWorkingSetSize(IntPtr proc, IntPtr min, IntPtr max);
    public static bool Trim(int pid){
        try {
            var p = System.Diagnostics.Process.GetProcessById(pid);
            return SetProcessWorkingSetSize(p.Handle, (IntPtr)(-1), (IntPtr)(-1));
        } catch { return false; }
    }
}
'@
try { Add-Type -TypeDefinition $csTrim -ErrorAction Stop; $script:CsLoaded = $true } catch { Write-Log ('Add-Type VIAMem failed: ' + $_.Exception.Message) 'WARN' }

# ---- Subprocess helper (ProcessStartInfo only) -----------------------------
function Invoke-PyProc {
    param([string]$Exe, [string[]]$ArgsList, [int]$TimeoutSec = 30)
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $Exe
        foreach ($a in $ArgsList) { $psi.ArgumentList.Add($a) }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow  = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $out = $p.StandardOutput.ReadToEnd()
        $err = $p.StandardError.ReadToEnd()
        if (-not $p.WaitForExit($TimeoutSec * 1000)) { try { $p.Kill() } catch {}; return [pscustomobject]@{ Ok = $false; Out = $out; Err = 'timeout' } }
        return [pscustomobject]@{ Ok = ($p.ExitCode -eq 0); Out = $out.Trim(); Err = $err.Trim(); Code = $p.ExitCode }
    } catch { return [pscustomobject]@{ Ok = $false; Out = ''; Err = $_.Exception.Message } }
}

# ---- Metrics ---------------------------------------------------------------
function Get-MemSnapshot {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeGB  = [math]::Round($os.FreePhysicalMemory   / 1MB, 2)
    $usedGB  = [math]::Round($totalGB - $freeGB, 2)
    $pct     = if ($totalGB -gt 0) { [math]::Round(($usedGB / $totalGB) * 100, 2) } else { 0 }
    return [pscustomobject]@{ TotalGB = $totalGB; UsedGB = $usedGB; FreeGB = $freeGB; UsedPct = $pct }
}
function Get-CpuLoad {
    try { return [int]((Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average) } catch { return 0 }
}
function Get-DriveSnapshot {
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
        [pscustomobject]@{ Name = $_.DeviceID.TrimEnd(':'); Root = $_.DeviceID + '\'
            UsedGB = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2); FreeGB = [math]::Round($_.FreeSpace / 1GB, 2) }
    }
}
function Get-TopProc {
    param([int]$Top = 10)
    $mem = Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First $Top |
        ForEach-Object { [pscustomobject]@{ Id = $_.Id; Name = $_.ProcessName; WorkingSetMB = [math]::Round($_.WorkingSet64 / 1MB, 2); Responding = $_.Responding } }
    return [pscustomobject]@{ Mem = $mem }
}

# ---- Fast fault-tolerant walk ----------------------------------------------
function Get-DirStat {
    param([string]$Root)
    $items = [System.Collections.Generic.List[object]]::new()
    $total = [int64]0
    if (-not (Test-Path -LiteralPath $Root)) { return [pscustomobject]@{ Items = $items; TotalMB = 0 } }
    $stack = [System.Collections.Generic.Stack[string]]::new(); $stack.Push($Root)
    while ($stack.Count -gt 0) {
        $dir = $stack.Pop()
        try { foreach ($s in [System.IO.Directory]::EnumerateDirectories($dir)) { $stack.Push($s) } } catch {}
        try {
            foreach ($f in [System.IO.Directory]::EnumerateFiles($dir)) {
                try { $fi = [System.IO.FileInfo]::new($f); $items.Add([pscustomobject]@{ Path = $f; Len = $fi.Length; LWT = $fi.LastWriteTime }); $total += $fi.Length } catch {}
            }
        } catch {}
    }
    return [pscustomobject]@{ Items = $items; TotalMB = [math]::Round($total / 1MB, 2) }
}

# ---- Target catalog --------------------------------------------------------
function Get-TargetCatalog {
    @(
        [pscustomobject]@{ Key = 'UserTemp';   Desc = '使用者 TEMP';             Path = $env:TEMP;                                                  Admin = $false }
        [pscustomobject]@{ Key = 'LocalTemp';  Desc = 'LOCALAPPDATA Temp';       Path = (Join-Path $env:LOCALAPPDATA 'Temp');                       Admin = $false }
        [pscustomobject]@{ Key = 'INetCache';  Desc = 'INetCache 網頁快取';      Path = (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\INetCache'); Admin = $false }
        [pscustomobject]@{ Key = 'CrashDumps'; Desc = 'CrashDumps 當機傾印';     Path = (Join-Path $env:LOCALAPPDATA 'CrashDumps');                 Admin = $false }
        [pscustomobject]@{ Key = 'ThumbCache'; Desc = '縮圖快取 (Explorer)';     Path = (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Explorer'); Admin = $false }
        [pscustomobject]@{ Key = 'WinTemp';    Desc = 'Windows Temp (系統)';     Path = 'C:\Windows\Temp';                                          Admin = $true  }
        [pscustomobject]@{ Key = 'WER';        Desc = 'Windows 錯誤回報 WER';    Path = 'C:\ProgramData\Microsoft\Windows\WER';                     Admin = $true  }
        [pscustomobject]@{ Key = 'WUCache';    Desc = 'Windows Update 下載快取'; Path = 'C:\Windows\SoftwareDistribution\Download';                 Admin = $true  }
    )
}

# ---- Safe cleanup ----------------------------------------------------------
function Invoke-CleanTarget {
    param([pscustomobject]$Target, [int]$Days, [switch]$Execute)
    $res = [ordered]@{ Key = $Target.Key; Path = $Target.Path; DeletedFiles = 0; DeletedDirs = 0; Skipped = 0; Errors = 0; FreedMB = 0.0; Notes = '' }
    if ($Target.Admin -and -not $script:IsAdmin) { $res.Notes = '需系統管理員 (Skipped)'; return [pscustomobject]$res }
    if (-not (Test-Path -LiteralPath $Target.Path)) { $res.Notes = '路徑不存在'; return [pscustomobject]$res }
    if (-not (Test-SafePath $Target.Path)) { $res.Errors = 1; $res.Notes = '安全白名單拒絕'; Write-Log ('REFUSED unsafe path: ' + $Target.Path) 'WARN'; return [pscustomobject]$res }

    $cutoff = (Get-Date).AddDays(-$Days)
    $stat = Get-DirStat -Root $Target.Path
    $freed = [int64]0
    foreach ($it in $stat.Items) {
        if ($it.LWT -ge $cutoff) { $res.Skipped++; continue }
        if (-not $Execute) { $res.DeletedFiles++; $freed += $it.Len; continue }
        try { [System.IO.File]::Delete($it.Path); $res.DeletedFiles++; $freed += $it.Len } catch { $res.Errors++ }
    }
    $res.FreedMB = [math]::Round($freed / 1MB, 2)

    if ($Execute) {
        $dirs = [System.Collections.Generic.List[string]]::new()
        $stk = [System.Collections.Generic.Stack[string]]::new(); $stk.Push($Target.Path)
        while ($stk.Count -gt 0) { $d = $stk.Pop(); try { foreach ($s in [System.IO.Directory]::EnumerateDirectories($d)) { $stk.Push($s); $dirs.Add($s) } } catch {} }
        foreach ($d in ($dirs | Sort-Object -Property Length -Descending)) {
            try {
                $hasAny = $false
                foreach ($x in [System.IO.Directory]::EnumerateFileSystemEntries($d)) { $hasAny = $true; break }
                if (-not $hasAny) { [System.IO.Directory]::Delete($d, $false); $res.DeletedDirs++ }
            } catch {}
        }
    }
    $verb = if ($Execute) { 'CLEAN' } else { 'SCAN ' }
    Write-Log ('{0} {1} files={2} dirs={3} freedMB={4} skip={5} err={6}' -f $verb, $Target.Key, $res.DeletedFiles, $res.DeletedDirs, $res.FreedMB, $res.Skipped, $res.Errors)
    return [pscustomobject]$res
}

# ---- Acceleration (CPU / DRAM / Memory) ------------------------------------
function Invoke-Optimize {
    param([string]$Opt)
    $r = [ordered]@{ Opt = $Opt; Ok = $false; Detail = '' }
    switch ($Opt) {
        'gc'        { [System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers(); [System.GC]::Collect(); $r.Ok = $true; $r.Detail = '.NET GC collected' }
        'trimall'   {
            if (-not $script:CsLoaded) { $r.Detail = 'WorkingSet API unavailable'; break }
            $n = 0; foreach ($p in (Get-Process)) { try { if ([VIAMem]::Trim($p.Id)) { $n++ } } catch {} }
            $r.Ok = $true; $r.Detail = ('Trimmed working set of {0} process(es)' -f $n)
        }
        'flushdns'  { try { Clear-DnsClientCache; $r.Ok = $true; $r.Detail = 'DNS cache flushed' } catch { $r.Detail = $_.Exception.Message } }
        'highperf'  { $out = & powercfg /setactive $script:HighPerfGuid 2>&1; $r.Ok = ($LASTEXITCODE -eq 0); $r.Detail = if ($r.Ok) { 'Power plan -> High Performance' } else { ('powercfg: ' + ($out -join ' ')) } }
        'balanced'  { $out = & powercfg /setactive $script:BalancedGuid 2>&1; $r.Ok = ($LASTEXITCODE -eq 0); $r.Detail = if ($r.Ok) { 'Power plan -> Balanced (restored)' } else { ('powercfg: ' + ($out -join ' ')) } }
        'recyclebin'{ try { Clear-RecycleBin -Force -ErrorAction Stop; $r.Ok = $true; $r.Detail = 'Recycle Bin emptied' } catch { $r.Ok = $true; $r.Detail = 'Recycle Bin already empty / skipped' } }
        default     { $r.Detail = 'unknown option' }
    }
    Write-Log ('OPTIMIZE {0} ok={1} {2}' -f $Opt, $r.Ok, $r.Detail)
    return [pscustomobject]$r
}

# ---- VIA_EnvManager integration --------------------------------------------
function Resolve-VIAEnv {
    $mgr = $null
    if (Test-Path -LiteralPath $script:EnvMgrCanonical) { $mgr = $script:EnvMgrCanonical }
    else {
        $cur = $PSScriptRoot; if (-not $cur) { $cur = (Get-Location).Path }
        for ($i = 0; $i -lt 4 -and $cur; $i++) {
            $probe = Join-Path $cur 'module\supportive_module\VIA_EnvManager.py'
            if (Test-Path -LiteralPath $probe) { $mgr = $probe; break }
            $parent = Split-Path -Parent $cur; if ($parent -eq $cur) { break }; $cur = $parent
        }
    }
    $py = $null
    foreach ($c in @('python', 'py')) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { $v = Invoke-PyProc -Exe $cmd.Source -ArgsList @('--version'); if ($v.Ok -or $v.Out -or $v.Err) { $py = $cmd.Source; break } }
    }
    if (-not $py) {
        $venvPy = Get-ChildItem -Path 'C:\Users\tonyk\envs' -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($venvPy) { $py = $venvPy.FullName }
    }
    $pyVer = ''; $psutil = ''
    if ($py) {
        $vr = Invoke-PyProc -Exe $py -ArgsList @('-c', 'import sys;print(sys.version.split()[0])'); if ($vr.Ok) { $pyVer = $vr.Out }
        $pr = Invoke-PyProc -Exe $py -ArgsList @('-c', 'import psutil;print(psutil.__version__)'); if ($pr.Ok) { $psutil = $pr.Out }
    }
    return [pscustomobject]@{ EnvMgr = $mgr; EnvMgrOk = [bool]$mgr; Python = $py; PythonVer = $pyVer; PsutilVer = $psutil; PsutilOk = [bool]$psutil }
}
function Install-Psutil {
    $env = Resolve-VIAEnv
    if (-not $env.Python) { return [pscustomobject]@{ Ok = $false; Detail = '找不到 python 直譯器' } }
    Write-Log ('pip install psutil -> ' + $env.Python)
    $r = Invoke-PyProc -Exe $env.Python -ArgsList @('-m', 'pip', 'install', '--upgrade', 'psutil') -TimeoutSec 180
    return [pscustomobject]@{ Ok = $r.Ok; Detail = (($r.Out + ' ' + $r.Err).Trim()) }
}

# ---- Turbo run -------------------------------------------------------------
function Invoke-TurboRun {
    param([bool]$Execute, [string[]]$Targets, [string[]]$Opts)
    $before = Get-MemSnapshot
    $cat = Get-TargetCatalog
    $cleaned = @()
    foreach ($key in @($Targets)) { $t = $cat | Where-Object { $_.Key -eq $key } | Select-Object -First 1; if ($t) { $cleaned += (Invoke-CleanTarget -Target $t -Days $AgeDays -Execute:$Execute) } }
    $optimized = @()
    foreach ($o in @($Opts)) { $optimized += (Invoke-Optimize -Opt $o) }
    Start-Sleep -Milliseconds 400
    $after = Get-MemSnapshot
    $sum = ($cleaned | Measure-Object -Property FreedMB -Sum).Sum; if (-not $sum) { $sum = 0 }
    return [pscustomobject]@{
        Execute = $Execute; Cleaned = @($cleaned); Optimized = @($optimized)
        TotalFreedMB = [math]::Round([double]$sum, 2)
        MemBefore = $before; MemAfter = $after
        MemReclaimedGB = [math]::Round($before.UsedGB - $after.UsedGB, 2)
        GenTime = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }
}

function Get-ScanResult {
    $cat = Get-TargetCatalog
    $targets = foreach ($t in $cat) {
        $exists = Test-Path -LiteralPath $t.Path
        $sizeMB = 0; if ($exists) { $sizeMB = (Get-DirStat -Root $t.Path).TotalMB }
        [pscustomobject]@{ Key = $t.Key; Desc = $t.Desc; Path = $t.Path; Admin = $t.Admin; Exists = $exists; SizeMB = $sizeMB; Blocked = ($t.Admin -and -not $script:IsAdmin) }
    }
    return [pscustomobject]@{
        GenTime = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); IsAdmin = $script:IsAdmin; AgeDays = $AgeDays
        Mem = (Get-MemSnapshot); Cpu = (Get-CpuLoad); Drives = @(Get-DriveSnapshot)
        Targets = @($targets); Proc = (Get-TopProc -Top 10); Env = (Resolve-VIAEnv)
    }
}

# ============================================================================
#  EMBEDDED SELF-TEST  (-SelfTest)
# ============================================================================
function Invoke-SelfTest {
    Write-Host ''
    Write-Host '== VIA Turbo Optimizer  Self-Test ==' -ForegroundColor Cyan
    $tests = [System.Collections.Generic.List[object]]::new()
    function Add-Test { param([string]$Name, [bool]$Ok) $tests.Add([pscustomobject]@{ Name = $Name; Ok = $Ok }) }

    Add-Test 'SafePath accepts user TEMP'        (Test-SafePath $env:TEMP)
    Add-Test 'SafePath rejects System32'         (-not (Test-SafePath 'C:\Windows\System32'))
    Add-Test 'SafePath rejects user Documents'   (-not (Test-SafePath (Join-Path $env:USERPROFILE 'Documents')))
    Add-Test 'SafePath rejects empty'            (-not (Test-SafePath ''))

    $cat = Get-TargetCatalog
    Add-Test 'Catalog has 8 targets'             ($cat.Count -eq 8)
    Add-Test 'Catalog keys are unique'           (($cat.Key | Select-Object -Unique).Count -eq $cat.Count)
    Add-Test 'WorkingSet trim type loaded'       ($script:CsLoaded)
    Add-Test 'Mem snapshot total > 0'            ((Get-MemSnapshot).TotalGB -gt 0)

    # Age-rule sandbox: old file counted, new file skipped (scan-only, no delete)
    $ageOk = $false
    try {
        $sand = Join-Path $env:TEMP 'VIA_SelfTest_Sandbox'
        if (Test-Path -LiteralPath $sand) { Remove-Item -LiteralPath $sand -Recurse -Force -ErrorAction SilentlyContinue }
        New-Item -ItemType Directory -Path $sand -Force | Out-Null
        $old = Join-Path $sand 'old.tmp'; Set-Content -LiteralPath $old -Value 'x'; (Get-Item $old).LastWriteTime = (Get-Date).AddDays(-10)
        $new = Join-Path $sand 'new.tmp'; Set-Content -LiteralPath $new -Value 'x'
        $tt = [pscustomobject]@{ Key = 'SelfTest'; Path = $sand; Admin = $false }
        $r = Invoke-CleanTarget -Target $tt -Days 3 -Execute:$false
        $ageOk = ($r.DeletedFiles -ge 1 -and $r.Skipped -ge 1)
        Remove-Item -LiteralPath $sand -Recurse -Force -ErrorAction SilentlyContinue
    } catch {}
    Add-Test 'Age rule: old counted, new skipped' $ageOk

    # Frontend HTML well-formed (basic structural balance)
    $htmlOk = $false
    try { $htmlOk = ($script:HtmlBody -match '<html' -and $script:HtmlBody -match '</html>' -and $script:HtmlBody.Length -gt 2000) } catch {}
    Add-Test 'Frontend HTML rendered + balanced' $htmlOk

    $pass = ($tests | Where-Object { $_.Ok }).Count
    $fail = ($tests | Where-Object { -not $_.Ok }).Count
    foreach ($t in $tests) {
        if ($t.Ok) { Write-Host ('  [PASS] ' + $t.Name) -ForegroundColor Green }
        else       { Write-Host ('  [FAIL] ' + $t.Name) -ForegroundColor Red }
    }
    $sumColor = if ($fail -eq 0) { 'Green' } else { 'Red' }
    Write-Host ('-- {0}/{1} PASS --' -f $pass, $tests.Count) -ForegroundColor $sumColor
    Write-Log ('SELFTEST {0}/{1} PASS' -f $pass, $tests.Count)
    return ($fail -eq 0)
}

# ============================================================================
#  FRONTEND  (modern animated HMI; single-quote here-string + .Replace)
# ============================================================================
$htmlTpl = @'
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>VIA Turbo Optimizer</title>
<style>
:root{--fg:#0f172a;--muted:#64748b;--line:#e6e8ee;--card:rgba(255,255,255,.78);--shadow:0 10px 30px rgba(15,23,42,.10);
--blue:#4C72B0;--green:#55A868;--red:#C44E52;--purple:#8172B2;--yellow:#CCB974;--cyan:#64B5CD;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",Arial,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace;}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{font-family:var(--sans);color:var(--fg);position:relative;overflow-x:hidden;
background:#f6f8fc;}
body::before{content:"";position:fixed;inset:-20%;z-index:-1;background:
radial-gradient(40% 40% at 15% 20%,rgba(76,114,176,.20),transparent 60%),
radial-gradient(40% 40% at 85% 15%,rgba(100,181,205,.18),transparent 60%),
radial-gradient(45% 45% at 75% 85%,rgba(129,114,178,.16),transparent 60%),
radial-gradient(40% 40% at 20% 90%,rgba(85,168,104,.15),transparent 60%);
filter:blur(10px);animation:drift 22s ease-in-out infinite alternate;}
@keyframes drift{0%{transform:translate3d(0,0,0) scale(1)}100%{transform:translate3d(0,-3%,0) scale(1.06)}}
.wrap{max-width:1120px;margin:0 auto;padding:24px}
.hdr{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.live{width:12px;height:12px;border-radius:999px;background:var(--green);box-shadow:0 0 0 0 rgba(85,168,104,.6);animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(85,168,104,.55)}70%{box-shadow:0 0 0 12px rgba(85,168,104,0)}100%{box-shadow:0 0 0 0 rgba(85,168,104,0)}}
h1{font-size:19px;margin:0;letter-spacing:.2px}.meta{font-size:12px;color:var(--muted)}
.card{border:1px solid var(--line);border-radius:18px;background:var(--card);backdrop-filter:blur(14px);box-shadow:var(--shadow);
padding:18px;margin-bottom:16px;opacity:0;transform:translateY(10px);animation:rise .55s cubic-bezier(.2,.7,.2,1) forwards}
.card:nth-child(2){animation-delay:.05s}.card:nth-child(3){animation-delay:.10s}.card:nth-child(4){animation-delay:.15s}
.card:nth-child(5){animation-delay:.20s}.card:nth-child(6){animation-delay:.25s}
@keyframes rise{to{opacity:1;transform:none}}
.card h2{margin:0 0 12px;font-size:15px}
.gauges{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.gauge{display:flex;flex-direction:column;align-items:center;border:1px solid var(--line);border-radius:14px;padding:12px;background:rgba(255,255,255,.6)}
.gauge .lab{font-size:12px;color:var(--muted);margin-top:6px}
.ring{transform:rotate(-90deg)}
.ring .bg{fill:none;stroke:rgba(15,23,42,.07);stroke-width:9}
.ring .fg{fill:none;stroke-width:9;stroke-linecap:round;stroke-dasharray:251;stroke-dashoffset:251;transition:stroke-dashoffset 1s cubic-bezier(.2,.7,.2,1),stroke .6s}
.gv{font-size:20px;font-weight:800}
.row{display:flex;align-items:center;gap:12px;padding:11px 12px;border:1px solid var(--line);border-radius:13px;margin-bottom:9px;background:rgba(255,255,255,.55);
opacity:0;transform:translateY(8px);animation:rise .4s ease forwards}
.row .grow{flex:1}.row .name{font-weight:600;font-size:13px}.row .sub{font-size:11px;color:var(--muted);word-break:break-all}
.size{font-family:var(--mono);font-size:13px;color:var(--blue);font-weight:800;min-width:78px;text-align:right}
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid var(--line);font-size:11px}
.badge.ok{border-color:rgba(85,168,104,.45);background:rgba(85,168,104,.10);color:#2f6e44}
.badge.warn{border-color:rgba(204,185,116,.55);background:rgba(204,185,116,.14);color:#7a6a2a}
.badge.danger{border-color:rgba(196,78,82,.45);background:rgba(196,78,82,.10);color:#9b3438}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px}
button{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:13px;padding:11px 17px;font-size:14px;font-weight:700;position:relative;overflow:hidden;transition:transform .12s,border-color .2s,box-shadow .2s}
button:hover{border-color:var(--blue);box-shadow:0 4px 14px rgba(76,114,176,.18)}button:active{transform:scale(.97)}
button.primary{background:linear-gradient(135deg,#4C72B0,#5b86c9);color:#fff;border:none}
button:disabled{opacity:.5;cursor:not-allowed}
.rp{position:absolute;border-radius:50%;transform:scale(0);background:rgba(255,255,255,.5);animation:rp .6s ease-out}
@keyframes rp{to{transform:scale(3.5);opacity:0}}
.switch{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:#fff}
.switch button{border:none;border-radius:0;padding:9px 15px;font-size:13px}.switch button.act{background:var(--blue);color:#fff}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--blue)}
.prog{height:10px;border-radius:999px;background:rgba(15,23,42,.07);overflow:hidden;margin:10px 0 6px;display:none}
.prog>i{display:block;height:100%;width:0;background:linear-gradient(90deg,#4C72B0,#64B5CD);transition:width .4s ease}
.phase{font-size:12px;color:var(--muted);min-height:16px}
.result{font-family:var(--mono);font-size:12px;background:#0b1220;color:#e5e7eb;padding:14px;border-radius:13px;white-space:pre-wrap;max-height:340px;overflow:auto}
.muted{color:var(--muted);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:12px}td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
.toast{position:fixed;right:22px;bottom:22px;background:#0b1220;color:#fff;padding:13px 17px;border-radius:13px;box-shadow:0 12px 30px rgba(0,0,0,.3);
font-size:13px;opacity:0;transform:translateY(16px);transition:.35s;z-index:9}.toast.show{opacity:1;transform:none}
.toast.ok{border-left:4px solid var(--green)}.toast.err{border-left:4px solid var(--red)}
@media(max-width:780px){.gauges{grid-template-columns:repeat(2,1fr)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}body::before{animation:none}}
</style></head><body><div class="wrap">

<div class="hdr"><div class="live"></div><div><h1>VIA Turbo Optimizer</h1>
<div class="meta">VeritasIntelligenceAnalytics &middot; 安全清理 + CPU/DRAM/記憶體加速 &middot; 127.0.0.1:__PORT__</div></div></div>

<div class="card"><h2>即時儀表</h2>
  <div class="gauges">
    <div class="gauge">
      <svg class="ring" width="92" height="92" viewBox="0 0 92 92"><circle class="bg" cx="46" cy="46" r="40"></circle><circle id="gCpu" class="fg" cx="46" cy="46" r="40" stroke="#4C72B0"></circle></svg>
      <div class="gv" id="vCpu">0%</div><div class="lab">CPU 負載</div></div>
    <div class="gauge">
      <svg class="ring" width="92" height="92" viewBox="0 0 92 92"><circle class="bg" cx="46" cy="46" r="40"></circle><circle id="gMem" class="fg" cx="46" cy="46" r="40" stroke="#8172B2"></circle></svg>
      <div class="gv" id="vMem">0%</div><div class="lab">記憶體使用</div></div>
    <div class="gauge"><div class="gv" id="vFree" style="margin-top:24px">0</div><div class="lab">可用記憶體 GB</div></div>
    <div class="gauge"><div class="gv" id="vTotal" style="margin-top:24px">0</div><div class="lab">總記憶體 GB</div></div>
  </div>
</div>

<div class="card"><h2>環境部署 (VIA_EnvManager)</h2>
  <div id="env" class="muted">偵測中...</div>
  <div class="bar"><button id="btnPsutil" onclick="installPsutil()">安裝 / 更新 psutil</button>
  <span class="muted">需按鈕觸發，寫入偵測到的直譯器。</span></div>
</div>

<div class="card"><h2>磁碟清理目標 (勾選)</h2>
  <div id="targets"><span class="muted">掃描中...</span></div>
  <div class="muted" style="margin-top:6px">規則：只刪 __AGE__ 天前檔案；只刪空資料夾；白名單外路徑一律拒絕；占用中檔案自動跳過。</div>
</div>

<div class="card"><h2>加速選項 (CPU / DRAM / 記憶體)</h2>
  <label class="row"><input type="checkbox" class="opt" value="gc" checked><span class="grow"><div class="name">.NET GC 回收</div><div class="sub">釋放受控記憶體，安全</div></span></label>
  <label class="row"><input type="checkbox" class="opt" value="trimall" checked><span class="grow"><div class="name">Working Set Trim (全進程)</div><div class="sub">壓縮工作集，可還原；不終止任何進程</div></span></label>
  <label class="row"><input type="checkbox" class="opt" value="flushdns" checked><span class="grow"><div class="name">清除 DNS 快取</div><div class="sub">Clear-DnsClientCache，安全</div></span></label>
  <label class="row"><input type="checkbox" class="opt" value="highperf"><span class="grow"><div class="name">電源計劃 → 高效能</div><div class="sub">可隨時還原平衡模式</div></span></label>
  <label class="row"><input type="checkbox" class="opt" value="recyclebin"><span class="grow"><div class="name">清空資源回收筒</div><div class="sub">不可還原，預設不勾</div></span></label>
</div>

<div class="card"><h2>執行</h2>
  <div class="bar">
    <span class="muted">模式：</span>
    <div class="switch"><button id="mScan" class="act" onclick="setExec(false)">僅掃描 (安全)</button><button id="mExec" onclick="setExec(true)">實際刪除</button></div>
    <button class="primary" id="btnRun" onclick="turbo()">⚡ 一鍵 Turbo 完成 (掃描)</button>
    <button onclick="loadScan()">重新掃描</button>
    <button onclick="restoreBalanced()">還原平衡電源</button>
  </div>
  <div class="prog" id="prog"><i id="progBar"></i></div>
  <div class="phase" id="phase"></div>
  <div class="result" id="out">就緒。先「僅掃描」確認大小，再切「實際刪除」。</div>
</div>

<div class="card"><h2>高占用進程 (僅供參考，不自動處理)</h2>
  <table id="proc"><thead><tr><th>Name</th><th>PID</th><th>WorkingSet MB</th></tr></thead><tbody></tbody></table>
</div>

<div class="muted">Log (append-only)：__LOGPATH__</div>
</div>
<div class="toast" id="toast"></div>
<script>
"use strict";
var EXEC=false, SCAN=null, CIRC=2*Math.PI*40;
function $(s){return document.querySelector(s);}
function raf(cb){return (typeof requestAnimationFrame!=="undefined")?requestAnimationFrame(cb):setTimeout(function(){cb(Date.now());},16);}
function fmt(n){return (n==null?0:n).toLocaleString();}
function setGauge(id,pct,color){var el=$("#"+id);if(!el)return;var off=CIRC*(1-Math.max(0,Math.min(100,pct))/100);
  el.style.strokeDasharray=CIRC;el.style.strokeDashoffset=off;
  if(color)el.setAttribute("stroke",color);else el.setAttribute("stroke",pct>85?"#C44E52":pct>65?"#CCB974":"#4C72B0");}
function animNum(id,to,suffix){var el=$("#"+id);if(!el)return;var from=parseFloat((el.textContent+"").replace(/[^\d.\-]/g,""))||0;var t0=null,dur=700;
  function step(ts){if(!t0)t0=ts;var k=Math.min(1,(ts-t0)/dur);var v=from+(to-from)*(1-Math.pow(1-k,3));
    el.textContent=(Math.round(v*100)/100)+(suffix||"");if(k<1)raf(step);} raf(step);}
function applyMetrics(m,cpu){
  setGauge("gCpu",cpu,"#4C72B0");animNum("vCpu",cpu,"%");
  setGauge("gMem",m.UsedPct,null);animNum("vMem",m.UsedPct,"%");
  animNum("vFree",m.FreeGB);animNum("vTotal",m.TotalGB);}
function toast(msg,type){var t=$("#toast");t.textContent=msg;t.className="toast show "+(type||"ok");
  setTimeout(function(){t.className="toast "+(type||"ok");},2600);}
async function loadScan(){
  try{var r=await fetch("/api/scan");SCAN=await r.json();render(SCAN);}
  catch(e){$("#out").textContent="掃描失敗: "+e;}
}
async function pollMetrics(){
  try{var r=await fetch("/api/metrics");var d=await r.json();applyMetrics(d.Mem,d.Cpu);}catch(e){}
}
function render(d){
  applyMetrics(d.Mem,d.Cpu);
  var e=d.Env;
  $("#env").innerHTML=
   '<span class="badge '+(e.EnvMgrOk?"ok":"warn")+'">EnvManager: '+(e.EnvMgrOk?"找到":"未找到")+'</span> '+
   '<span class="badge '+(e.Python?"ok":"warn")+'">Python: '+(e.Python?(e.PythonVer||"ok"):"未偵測")+'</span> '+
   '<span class="badge '+(e.PsutilOk?"ok":"warn")+'">psutil: '+(e.PsutilOk?e.PsutilVer:"未安裝")+'</span> '+
   '<span class="badge '+(d.IsAdmin?"ok":"danger")+'">Admin: '+d.IsAdmin+'</span>'+
   '<div class="muted" style="margin-top:6px">'+(e.EnvMgr||"(EnvManager 路徑未命中，已優雅降級)")+'</div>';
  var h="",i=0;
  for(var x=0;x<d.Targets.length;x++){var t=d.Targets[x];i++;
    var dis=t.Blocked?"disabled":"";
    var sub=t.Blocked?"需管理員，已停用":(t.Exists?t.Path:"路徑不存在");
    var chk=(!t.Blocked&&t.SizeMB>0)?"checked":"";
    h+='<label class="row" style="animation-delay:'+(i*0.04)+'s"><input type="checkbox" class="tgt" value="'+t.Key+'" '+chk+' '+dis+'>'+
       '<span class="grow"><div class="name">'+t.Desc+' '+(t.Admin?'<span class="badge warn">admin</span>':'')+'</div>'+
       '<div class="sub">'+sub+'</div></span><span class="size">'+fmt(t.SizeMB)+' MB</span></label>';
  }
  $("#targets").innerHTML=h;
  var tb=$("#proc tbody");tb.innerHTML="";
  for(var p=0;p<d.Proc.Mem.length;p++){var pr=d.Proc.Mem[p];
    tb.insertAdjacentHTML("beforeend","<tr><td>"+pr.Name+"</td><td>"+pr.Id+"</td><td>"+pr.WorkingSetMB+"</td></tr>");}
}
function picked(cls){var a=[].slice.call(document.querySelectorAll(cls));return a.filter(function(x){return x.checked&&!x.disabled;}).map(function(x){return x.value;});}
function setExec(v){EXEC=v;$("#mScan").classList.toggle("act",!v);$("#mExec").classList.toggle("act",v);
  $("#btnRun").textContent=v?"⚡ 一鍵 Turbo 刪除+加速":"⚡ 一鍵 Turbo 完成 (掃描)";}
function phase(txt,pct){$("#phase").textContent=txt;$("#progBar").style.width=pct+"%";}
async function turbo(){
  var tgts=picked(".tgt"), opts=picked(".opt");
  if(EXEC && !confirm("將實際刪除選定目標中 __AGE__ 天前的檔案，確定？")) return;
  $("#btnRun").disabled=true;$("#prog").style.display="block";
  phase("階段 1/4 · 準備中...",8);
  await new Promise(function(r){setTimeout(r,180);});
  phase(EXEC?"階段 2/4 · 安全刪除中...":"階段 2/4 · 掃描估算中...",38);
  try{
    var r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({execute:EXEC,targets:tgts,opts:opts})});
    phase("階段 3/4 · 加速 CPU/DRAM/記憶體...",72);
    var d=await r.json();
    var s="["+(d.Execute?"EXECUTE":"SCAN")+"] "+d.GenTime+"\n";
    s+="記憶體: 之前 "+d.MemBefore.UsedGB+"GB -> 之後 "+d.MemAfter.UsedGB+"GB  (回收 "+d.MemReclaimedGB+"GB)\n";
    s+="預估/實際釋放磁碟: "+d.TotalFreedMB+" MB\n\n[清理]\n";
    for(var c=0;c<d.Cleaned.length;c++){var cc=d.Cleaned[c];
      s+="  "+cc.Key+": files="+cc.DeletedFiles+" dirs="+cc.DeletedDirs+" freed="+cc.FreedMB+"MB skip="+cc.Skipped+" err="+cc.Errors+" "+cc.Notes+"\n";}
    s+="\n[加速]\n";
    for(var o=0;o<d.Optimized.length;o++){var oo=d.Optimized[o];s+="  "+oo.Opt+": "+(oo.Ok?"OK":"--")+" "+oo.Detail+"\n";}
    $("#out").textContent=s;
    phase("階段 4/4 · 完成 ✓",100);
    applyMetrics(d.MemAfter,SCAN?SCAN.Cpu:0);
    toast((d.Execute?"清理+加速完成":"掃描完成")+" · 釋放 "+d.TotalFreedMB+"MB","ok");
    await loadScan();
  }catch(e){$("#out").textContent="執行失敗: "+e;phase("失敗",0);toast("執行失敗","err");}
  setTimeout(function(){$("#prog").style.display="none";phase("",0);},1200);
  $("#btnRun").disabled=false;
}
async function installPsutil(){
  $("#out").textContent="安裝 psutil 中...";
  try{var r=await fetch("/api/psutil",{method:"POST"});var d=await r.json();
    $("#out").textContent=(d.Ok?"psutil OK\n":"psutil 失敗\n")+d.Detail;toast(d.Ok?"psutil 完成":"psutil 失敗",d.Ok?"ok":"err");await loadScan();}
  catch(e){$("#out").textContent="安裝失敗: "+e;}
}
async function restoreBalanced(){
  var r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({execute:false,targets:[],opts:["balanced"]})});
  var d=await r.json();$("#out").textContent=d.Optimized.map(function(o){return o.Opt+": "+o.Detail;}).join("\n");toast("電源已還原平衡","ok");
}
document.addEventListener("click",function(ev){var b=ev.target.closest("button");if(!b)return;
  var c=document.createElement("span");c.className="rp";var z=Math.max(b.clientWidth,b.clientHeight);
  c.style.width=c.style.height=z+"px";c.style.left=(ev.offsetX-z/2)+"px";c.style.top=(ev.offsetY-z/2)+"px";
  b.appendChild(c);setTimeout(function(){c.remove();},600);});
loadScan();
if(typeof setInterval!=="undefined"){setInterval(pollMetrics,2500);}
</script></body></html>
'@

$script:HtmlBody = $htmlTpl.Replace('__PORT__', [string]$Port).Replace('__AGE__', [string]$AgeDays).Replace('__LOGPATH__', $script:LogFile)
[System.IO.File]::WriteAllText($script:FrontFile, $script:HtmlBody, [System.Text.Encoding]::UTF8)
Write-Log ('Frontend written: ' + $script:FrontFile)

# ---- Self-test branch (no server) -----------------------------------------
if ($SelfTest) { $ok = Invoke-SelfTest; if ($ok) { exit 0 } else { exit 1 } }

# ---- Pre-flight gate at activation (fast, embedded, non-blocking) ----------
$preflight = $true
try {
    $preflight = (Test-SafePath $env:TEMP) -and (-not (Test-SafePath 'C:\Windows\System32')) -and ((Get-TargetCatalog).Count -eq 8) -and $script:CsLoaded
} catch { $preflight = $false }
$pf = if ($preflight) { 'PASS' } else { 'WARN' }
Write-Log ('PRE-FLIGHT ' + $pf + ' (safe-path guard, catalog, trim API)')

# ============================================================================
#  BACKEND  (HttpListener, loopback)
# ============================================================================
function Send-Response {
    param($Ctx, [string]$Body, [string]$Type = 'application/json; charset=utf-8', [int]$Code = 200)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $Ctx.Response.StatusCode = $Code
    $Ctx.Response.ContentType = $Type
    $Ctx.Response.Headers['Cache-Control'] = 'no-store'
    $Ctx.Response.ContentLength64 = $bytes.Length
    $Ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Ctx.Response.OutputStream.Close()
}

$listener = [System.Net.HttpListener]::new()
$prefix = ('http://127.0.0.1:{0}/' -f $Port)
$listener.Prefixes.Add($prefix)
try { $listener.Start() } catch { Write-Log ('HttpListener start failed (port busy?): ' + $_.Exception.Message) 'ERROR'; throw }
Write-Log ('Backend listening: ' + $prefix)
if (-not $NoBrowser) { try { Start-Process $prefix } catch {} }

Write-Host ''
Write-Host ('==> VIA Turbo Optimizer is live at ' + $prefix) -ForegroundColor Green
Write-Host '==> Ctrl+C in this window to stop the server.' -ForegroundColor Yellow
Write-Host ''

try {
    while ($listener.IsListening -and -not $script:Stop) {
        $ctx = $null
        try { $ctx = $listener.GetContext() } catch { break }
        if (-not $ctx) { continue }
        $path = $ctx.Request.Url.AbsolutePath
        try {
            switch -Regex ($path) {
                '^/$'            { Send-Response -Ctx $ctx -Body $script:HtmlBody -Type 'text/html; charset=utf-8'; break }
                '^/api/scan$'    { Send-Response -Ctx $ctx -Body ((Get-ScanResult) | ConvertTo-Json -Depth 8 -Compress); break }
                '^/api/metrics$' { Send-Response -Ctx $ctx -Body (([pscustomobject]@{ Mem = (Get-MemSnapshot); Cpu = (Get-CpuLoad) }) | ConvertTo-Json -Depth 5 -Compress); break }
                '^/api/run$' {
                    $enc = $ctx.Request.ContentEncoding; if (-not $enc) { $enc = [System.Text.Encoding]::UTF8 }
                    $reader = [System.IO.StreamReader]::new($ctx.Request.InputStream, $enc)
                    $bodyTxt = $reader.ReadToEnd(); $reader.Close()
                    if ([string]::IsNullOrWhiteSpace($bodyTxt)) { $bodyTxt = '{"execute":false,"targets":[],"opts":[]}' }
                    $req = $bodyTxt | ConvertFrom-Json
                    $out = Invoke-TurboRun -Execute ([bool]$req.execute) -Targets (@($req.targets)) -Opts (@($req.opts))
                    Send-Response -Ctx $ctx -Body ($out | ConvertTo-Json -Depth 8 -Compress)
                    break
                }
                '^/api/psutil$'  { Send-Response -Ctx $ctx -Body ((Install-Psutil) | ConvertTo-Json -Depth 5 -Compress); break }
                '^/api/shutdown$' { Send-Response -Ctx $ctx -Body '{"ok":true}'; $script:Stop = $true; break }
                default          { Send-Response -Ctx $ctx -Body '{"error":"not found"}' -Code 404; break }
            }
        } catch {
            Write-Log ('Request error ' + $path + ': ' + $_.Exception.Message) 'ERROR'
            try { Send-Response -Ctx $ctx -Body ('{"error":"' + ($_.Exception.Message -replace '"', "'") + '"}') -Code 500 } catch {}
        }
    }
} finally {
    try { $listener.Stop(); $listener.Close() } catch {}
    Write-Log 'Backend stopped.'
    Write-Host '==> Stopped.' -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
