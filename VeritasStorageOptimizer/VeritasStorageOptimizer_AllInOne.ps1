param(
    [int]$Port = 8868,
    [double]$MaxMB = 200,
    [string]$Dir = '',
    [switch]$Execute,
    [switch]$NoBrowser,
    [switch]$SelfTest,
    [switch]$TestAll
)

# ============================================================================
#  Veritas Storage Optimizer  ALL-IN-ONE  (2026 Edition)
#  EMBEDDED single-file system: native PS cleaning engine + HttpListener
#  backend + animated HTML front-end. Consolidates the Python / Node.js
#  engines as optional sub-engines when their scripts sit next to this file.
#  Dry-Run by default. Root / home-ancestor / symlinked targets always refused.
#  Self-contained, append-only log, inline self-test (-SelfTest), full
#  project test chain (-TestAll). Windows PowerShell 5.x auto-relaunches
#  under pwsh 7+; busy ports probe upward; 127.0.0.1 ACL-denied hosts fall
#  back to localhost.
#  PS7 rules honored: param() top, no block comments, ProcessStartInfo
#  (no Start-Job / no -Args splat), single-quote here-string + .Replace(),
#  [IO.File]::WriteAllText, -f only inside parentheses.
# ============================================================================

$ErrorActionPreference = 'Continue'

# ---- PowerShell 5.x bootstrap: relaunch under pwsh 7+ ------------------------
# Everything below needs PS7 runtime APIs (ProcessStartInfo.ArgumentList,
# GetContextAsync); this gate is the only code Windows PowerShell executes.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $pwshCmd = Get-Command 'pwsh' -ErrorAction SilentlyContinue
    if ($pwshCmd) {
        Write-Host ('[Veritas] PowerShell ' + $PSVersionTable.PSVersion + ' detected - relaunching under pwsh 7+ ...')
        $fwd = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Port', [string]$Port, '-MaxMB', [string]$MaxMB)
        if ($Dir)       { $fwd += @('-Dir', $Dir) }
        if ($Execute)   { $fwd += '-Execute' }
        if ($NoBrowser) { $fwd += '-NoBrowser' }
        if ($SelfTest)  { $fwd += '-SelfTest' }
        if ($TestAll)   { $fwd += '-TestAll' }
        & $pwshCmd.Source @fwd
        exit $LASTEXITCODE
    }
    Write-Host '[Veritas] PowerShell 7+ (pwsh) is required but was not found on PATH.'
    Write-Host '[Veritas] Install: winget install Microsoft.PowerShell  (or https://aka.ms/powershell)'
    exit 9
}

# ---- Config / paths --------------------------------------------------------
$script:Base = $PSScriptRoot
if (-not $script:Base) { $script:Base = (Get-Location).Path }
$script:LogDir     = Join-Path $script:Base 'logs'
$script:LogFile    = Join-Path $script:LogDir 'ps_gui_activity.log'
$script:PyEngine   = Join-Path $script:Base 'engine/veritas_cleaner.py'
$script:JsEngine   = Join-Path $script:Base 'engine/veritas_cleaner.js'
$script:Stop       = $false

$script:TempExtensions = @('.tmp', '.log', '.cache', '.bak', '.old', '.temp', '.swp', '.dmp')
$script:ProtectedDirs  = @('.git', '.svn', '.venv', 'node_modules', 'site-packages', '$RECYCLE.BIN', 'System Volume Information')
# Coding byproducts: caches and compiled leftovers that build/test tooling
# regenerates on demand. Directories are matched per path component, so a
# junk dir anywhere under the target marks its whole subtree.
$script:CodingJunkDirs = @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.ipynb_checkpoints')
$script:CodingJunkExtensions = @('.pyc', '.pyo')
# Files below this size never enter duplicate detection: deleting them frees
# ~no space, yet near-empty twins are often structural (__init__.py, .gitkeep,
# 1-byte stdout stubs) and removing "duplicates" across projects breaks them.
$script:DupMinBytes    = 1024
# User-placed marker: any directory containing this file is off-limits to
# every strategy, letting users pin "do not touch" zones inside a scan.
$script:ProtectMarker  = '.veritas_protect'

if (-not (Test-Path -LiteralPath $script:LogDir)) { New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null }

# ---- Logging (append-only) -------------------------------------------------
function Write-Log {
    param([string]$Msg, [string]$Level = 'INFO')
    $line = ('{0} | {1,-5} | {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Msg)
    try { [System.IO.File]::AppendAllText($script:LogFile, $line + [Environment]::NewLine, [System.Text.Encoding]::UTF8) } catch {}
    Write-Host $line
}

# ---- System protection guard ------------------------------------------------
function Test-RefusedTarget {
    param([string]$Path)
    # Returns a refusal reason, or '' when the target is acceptable.
    if ([string]::IsNullOrWhiteSpace($Path)) { return '目標路徑為空' }
    try { $full = [System.IO.Path]::GetFullPath($Path) } catch { return '路徑無法解析' }
    if (-not (Test-Path -LiteralPath $full -PathType Container)) { return '目標資料夾不存在' }
    try {
        $attr = [System.IO.File]::GetAttributes($full)
        if (($attr -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return '拒絕:目標本身為符號連結 (Symlink/Junction)' }
    } catch { return '路徑屬性無法讀取' }
    if (Test-Path -LiteralPath (Join-Path $full $script:ProtectMarker) -PathType Leaf) { return ('拒絕:目標受 {0} 保護標記鎖定' -f $script:ProtectMarker) }
    $root = [System.IO.Path]::GetPathRoot($full)
    $norm = $full.TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    if ($norm -eq $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar)) { return '拒絕:不可對檔案系統根目錄執行' }
    $userHome = [System.IO.Path]::GetFullPath([Environment]::GetFolderPath('UserProfile')).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    if ($norm -eq $userHome) { return '拒絕:不可對使用者家目錄執行(請選擇子資料夾)' }
    if ($userHome.StartsWith($norm + [System.IO.Path]::DirectorySeparatorChar)) { return '拒絕:不可對家目錄上層執行' }
    return ''
}

# ---- Helpers -----------------------------------------------------------------
function Format-Size {
    param([double]$Bytes)
    $units = @('B', 'KB', 'MB', 'GB', 'TB')
    $i = 0
    while ($Bytes -ge 1024 -and $i -lt ($units.Count - 1)) { $Bytes = $Bytes / 1024; $i++ }
    return ('{0:N2} {1}' -f $Bytes, $units[$i])
}

function Get-StreamHash {
    # Streaming MD5 fingerprint - constant memory even on multi-GB files.
    param([string]$Path)
    $md5 = $null; $fs = $null
    try {
        $md5 = [System.Security.Cryptography.MD5]::Create()
        $fs = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read, 65536)
        $bytes = $md5.ComputeHash($fs)
        return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    } catch { return '' }
    finally {
        if ($fs) { $fs.Dispose() }
        if ($md5) { $md5.Dispose() }
    }
}

# ---- Native PS cleaning engine ------------------------------------------------
function Test-ReparsePoint {
    # Symlinks / junctions are never traversed: following them can loop
    # forever or escape the target directory and delete outside files.
    param([string]$Path)
    try {
        $attr = [System.IO.File]::GetAttributes($Path)
        return (($attr -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
    } catch { return $true }
}

function Test-SkippedDir {
    # Protected names, reparse points, Python virtual environments (marked
    # by pyvenv.cfg - venvs share thousands of identical package files, so
    # cross-venv dedup would gut every env after the first), and user
    # protect-marker zones (.veritas_protect).
    param([string]$Path)
    if ($script:ProtectedDirs -contains [System.IO.Path]::GetFileName($Path)) { return $true }
    if (Test-ReparsePoint -Path $Path) { return $true }
    if (Test-Path -LiteralPath (Join-Path $Path 'pyvenv.cfg') -PathType Leaf) { return $true }
    if (Test-Path -LiteralPath (Join-Path $Path $script:ProtectMarker) -PathType Leaf) { return $true }
    return $false
}

function Get-EmptyDirectories {
    # Lightweight directory-only walk (no file stat, no hashing).
    # Returns currently-empty directories, deepest paths first.
    param([string]$Root)
    $dirs = [System.Collections.Generic.List[string]]::new()
    $stack = [System.Collections.Generic.Stack[string]]::new()
    $stack.Push($Root)
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        try {
            foreach ($s in [System.IO.Directory]::EnumerateDirectories($d)) {
                if (Test-SkippedDir -Path $s) { continue }
                $stack.Push($s)
                $dirs.Add($s)
            }
        } catch {}
    }
    $empty = [System.Collections.Generic.List[string]]::new()
    foreach ($d in ($dirs | Sort-Object -Property Length -Descending)) {
        try {
            $hasAny = $false
            foreach ($x in [System.IO.Directory]::EnumerateFileSystemEntries($d)) { $hasAny = $true; break }
            if (-not $hasAny) { $empty.Add($d) }
        } catch {}
    }
    return $empty
}

function Test-JunkDir {
    # True when any path component is a coding-junk directory name.
    param([string]$Path)
    foreach ($part in $Path.Split([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)) {
        if ($script:CodingJunkDirs -contains $part) { return $true }
    }
    return $false
}

function Invoke-VeritasScan {
    # Pass 1: fault-tolerant walk classifying coding-junk / temp / oversize
    # files and collecting (extension, size) candidate groups. Pass 2:
    # streaming-hash only those groups. Keying candidates by extension AND
    # size (not size alone) keeps groups small, so far fewer files are ever
    # hashed - lower memory and I/O on large trees.
    param([string]$Root, [long]$LimitBytes)
    $items = [System.Collections.Generic.List[object]]::new()
    $groups = @{}
    $groupSize = @{}
    $freed = [long]0

    $stack = [System.Collections.Generic.Stack[string]]::new()
    $stack.Push($Root)
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        try {
            foreach ($s in [System.IO.Directory]::EnumerateDirectories($d)) {
                if (Test-SkippedDir -Path $s) { continue }
                $stack.Push($s)
            }
        } catch {}
        $dirIsJunk = Test-JunkDir -Path $d
        try {
            foreach ($f in [System.IO.Directory]::EnumerateFiles($d)) {
                $fi = $null
                try { $fi = [System.IO.FileInfo]::new($f) } catch { continue }
                $ext = $fi.Extension.ToLowerInvariant()
                if ($dirIsJunk -or $script:CodingJunkExtensions -contains $ext) {
                    $items.Add([pscustomobject]@{ path = $f; size = (Format-Size $fi.Length); reason = 'Coding Junk' })
                    $freed += $fi.Length
                    continue
                }
                if ($script:TempExtensions -contains $ext) {
                    $items.Add([pscustomobject]@{ path = $f; size = (Format-Size $fi.Length); reason = 'Temp File' })
                    $freed += $fi.Length
                    continue
                }
                if ($fi.Length -gt $LimitBytes) {
                    $items.Add([pscustomobject]@{ path = $f; size = (Format-Size $fi.Length); reason = ('Over Limit (>{0}MB)' -f ($LimitBytes / 1MB)) })
                    $freed += $fi.Length
                    continue
                }
                if ($fi.Length -ge $script:DupMinBytes) {
                    $key = ($ext + '|' + [string]$fi.Length)
                    if (-not $groups.Contains($key)) { $groups[$key] = [System.Collections.Generic.List[string]]::new(); $groupSize[$key] = $fi.Length }
                    $groups[$key].Add($f)
                }
            }
        } catch {}
    }

    foreach ($key in @($groups.Keys)) {
        $paths = $groups[$key]
        if ($paths.Count -lt 2) { continue }
        $size = [long]$groupSize[$key]
        $seen = @{}
        foreach ($p in $paths) {
            $h = Get-StreamHash -Path $p
            if (-not $h) { continue }
            if ($seen.Contains($h)) {
                $keeper = [System.IO.Path]::GetFileName($seen[$h])
                $items.Add([pscustomobject]@{ path = $p; size = (Format-Size $size); reason = ('Duplicate of {0}' -f $keeper) })
                $freed += $size
            } else {
                $seen[$h] = $p
            }
        }
    }

    return [pscustomobject]@{ Items = $items; EmptyDirs = (Get-EmptyDirectories -Root $Root); FreedBytes = $freed }
}

# ---- Sub-engine invocation (Python / Node via ProcessStartInfo) ----------------
function Invoke-SubProc {
    param([string]$Exe, [string[]]$ArgsList, [int]$TimeoutSec = 3600)
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
        if (-not $p.WaitForExit($TimeoutSec * 1000)) { try { $p.Kill() } catch {}; return [pscustomobject]@{ Ok = $false; Out = $out; Err = 'timeout'; Code = -1 } }
        return [pscustomobject]@{ Ok = ($p.ExitCode -eq 0); Out = $out; Err = $err; Code = $p.ExitCode }
    } catch { return [pscustomobject]@{ Ok = $false; Out = ''; Err = $_.Exception.Message; Code = -1 } }
}

function ConvertFrom-EngineOutput {
    # Parses the stdout contract shared by veritas_cleaner.py / .js
    param([string]$Text)
    $items = [System.Collections.Generic.List[object]]::new()
    $empty = [System.Collections.Generic.List[string]]::new()
    $freedHuman = ''
    foreach ($line in ($Text -split "`n")) {
        $t = $line.Trim()
        $m = [regex]::Match($t, '^\[Empty Directory\] -> (?<path>.+)$')
        if ($m.Success) { $empty.Add($m.Groups['path'].Value); continue }
        $m = [regex]::Match($t, '^\[(?<reason>.+?)\] (?<size>[\d.,]+ [KMGTP]?B) -> (?<path>.+)$')
        if ($m.Success) {
            $items.Add([pscustomobject]@{ path = $m.Groups['path'].Value; size = $m.Groups['size'].Value; reason = $m.Groups['reason'].Value })
            continue
        }
        $m = [regex]::Match($t, '^(?:Total Space to Free|Potential Space Released): (?<size>.+)$')
        if ($m.Success) { $freedHuman = $m.Groups['size'].Value }
    }
    return [pscustomobject]@{ Items = $items; EmptyDirs = $empty; FreedHuman = $freedHuman }
}

# ---- Environment detection ------------------------------------------------------
function Find-Interpreter {
    param([string[]]$Names)
    foreach ($n in $Names) {
        $cmd = Get-Command $n -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return ''
}

function Get-EnvSnapshot {
    $py = Find-Interpreter -Names @('python3', 'python', 'py')
    $node = Find-Interpreter -Names @('node')
    $pyVer = ''; $nodeVer = ''
    if ($py) { $r = Invoke-SubProc -Exe $py -ArgsList @('--version') -TimeoutSec 15; $pyVer = (($r.Out + $r.Err).Trim() -split "`n")[0] }
    if ($node) { $r = Invoke-SubProc -Exe $node -ArgsList @('--version') -TimeoutSec 15; $nodeVer = ($r.Out.Trim() -split "`n")[0] }
    return [pscustomobject]@{
        PSVer = $PSVersionTable.PSVersion.ToString()
        Python = $py; PythonVer = $pyVer
        Node = $node; NodeVer = $nodeVer
        PyEngine = (Test-Path -LiteralPath $script:PyEngine)
        JsEngine = (Test-Path -LiteralPath $script:JsEngine)
        GenTime = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }
}

# ---- Unified run (engine dispatch + audit log) -----------------------------------
function Invoke-VeritasRun {
    param([string]$Engine, [string]$Target, [double]$MaxMBIn, [bool]$Live)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if ($MaxMBIn -le 0 -or [double]::IsNaN($MaxMBIn)) {
        return [pscustomobject]@{ ok = $false; error = '大檔閾值必須為正數 (MB)' }
    }
    $reason = Test-RefusedTarget -Path $Target
    if ($reason) {
        Write-Log ('REFUSED target=' + $Target + ' reason=' + $reason) 'WARN'
        return [pscustomobject]@{ ok = $false; error = $reason }
    }
    $full = [System.IO.Path]::GetFullPath($Target)
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    $audit = Join-Path $script:LogDir ('veritas_audit_{0}_{1}.log' -f $Engine, $stamp)
    Write-Log ('RUN engine={0} execute={1} maxMB={2} target={3}' -f $Engine, $Live, $MaxMBIn, $full)

    $items = $null; $emptyDirs = $null; $freedHuman = ''; $rawOut = ''

    if ($Engine -eq 'python' -or $Engine -eq 'node') {
        $env0 = Get-EnvSnapshot
        $exe = ''; $scriptPath = ''
        if ($Engine -eq 'python') { $exe = $env0.Python; $scriptPath = $script:PyEngine }
        else { $exe = $env0.Node; $scriptPath = $script:JsEngine }
        if (-not $exe) { return [pscustomobject]@{ ok = $false; error = ('未偵測到 {0} 直譯器' -f $Engine) } }
        if (-not (Test-Path -LiteralPath $scriptPath)) { return [pscustomobject]@{ ok = $false; error = ('引擎腳本缺失: {0}' -f $scriptPath) } }
        $argsList = @($scriptPath, '--dir', $full, '--max-mb', [string]$MaxMBIn, '--log', $audit)
        if ($Live) { $argsList += '--execute' }
        $r = Invoke-SubProc -Exe $exe -ArgsList $argsList
        if (-not $r.Ok) { return [pscustomobject]@{ ok = $false; error = ('引擎結束代碼 {0}: {1}' -f $r.Code, $r.Err) } }
        $parsed = ConvertFrom-EngineOutput -Text $r.Out
        $items = $parsed.Items; $emptyDirs = $parsed.EmptyDirs; $freedHuman = $parsed.FreedHuman
        $rawOut = $r.Out
    } else {
        $scan = Invoke-VeritasScan -Root $full -LimitBytes ([long]($MaxMBIn * 1MB))
        $items = $scan.Items; $emptyDirs = $scan.EmptyDirs
        $freedHuman = Format-Size $scan.FreedBytes

        $auditLines = [System.Collections.Generic.List[string]]::new()
        $auditLines.Add('=== VERITAS PS ALL-IN-ONE AUDIT LOG ===')
        $auditLines.Add('Timestamp: ' + (Get-Date -Format 'o'))
        $auditLines.Add('Target Directory: ' + $full)
        $auditLines.Add('Execution Mode: ' + $(if ($Live) { 'LIVE_DELETE' } else { 'DRY-RUN' }))
        $auditLines.Add('--- Target File Items ---')
        foreach ($it in $items) {
            $auditLines.Add(('[{0}] {1} -> {2}' -f $it.reason, $it.size, $it.path))
            if ($Live) {
                try { [System.IO.File]::Delete($it.path) } catch { $auditLines.Add('  Failed to remove: ' + $_.Exception.Message) }
            }
        }
        if ($Live) {
            # Re-sweep until stable: deleting files may empty a directory,
            # whose removal may in turn empty its parent. Lightweight
            # directory-only walk each round - no re-hashing of the tree.
            $removedDirs = [System.Collections.Generic.List[string]]::new()
            for ($round = 0; $round -lt 32; $round++) {
                $sweep = Get-EmptyDirectories -Root $full
                if ($sweep.Count -eq 0) { break }
                foreach ($d in $sweep) {
                    try { [System.IO.Directory]::Delete($d, $false); $removedDirs.Add($d) } catch {}
                }
            }
            $emptyDirs = $removedDirs
        }
        $auditLines.Add('--- Removed Empty Directories ---')
        foreach ($d in $emptyDirs) { $auditLines.Add('[Empty Directory] -> ' + $d) }
        $auditLines.Add('Summary:')
        $auditLines.Add('Total Files Marked: ' + $items.Count)
        $auditLines.Add('Estimated Space Freed: ' + $freedHuman)
        [System.IO.File]::WriteAllText($audit, ($auditLines -join [Environment]::NewLine), [System.Text.Encoding]::UTF8)
        $rawOut = ($auditLines -join "`n")
    }

    $sw.Stop()
    $result = [pscustomobject]@{
        ok = $true
        execute = $Live
        engine = $Engine
        target = $full
        items = @($items)
        emptyDirs = @($emptyDirs)
        totalFiles = $items.Count
        freedHuman = $freedHuman
        logPath = $audit
        elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        output = $(if ($rawOut.Length -gt 8000) { $rawOut.Substring($rawOut.Length - 8000) } else { $rawOut })
        genTime = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }
    $verb = if ($Live) { 'CLEAN' } else { 'SCAN ' }
    Write-Log ('{0} engine={1} files={2} freed={3} elapsed={4}s' -f $verb, $Engine, $result.totalFiles, $freedHuman, $result.elapsedSec)
    return $result
}

# ============================================================================
#  FRONTEND  (VIA house style; single-quote here-string + .Replace)
# ============================================================================
$htmlTpl = @'
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Veritas Storage Optimizer AIO</title>
<style>
:root{--fg:#0f172a;--muted:#64748b;--line:#e6e8ee;--card:rgba(255,255,255,.78);--shadow:0 10px 30px rgba(15,23,42,.10);
--blue:#4C72B0;--green:#55A868;--red:#C44E52;--purple:#8172B2;--yellow:#CCB974;--cyan:#64B5CD;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",Arial,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace;}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{font-family:var(--sans);color:var(--fg);position:relative;overflow-x:hidden;background:#f6f8fc;}
body::before{content:"";position:fixed;inset:-20%;z-index:-1;background:
radial-gradient(40% 40% at 15% 20%,rgba(76,114,176,.20),transparent 60%),
radial-gradient(40% 40% at 85% 15%,rgba(100,181,205,.18),transparent 60%),
radial-gradient(45% 45% at 75% 85%,rgba(129,114,178,.16),transparent 60%),
radial-gradient(40% 40% at 20% 90%,rgba(85,168,104,.15),transparent 60%);
filter:blur(10px);animation:drift 22s ease-in-out infinite alternate;}
@keyframes drift{0%{transform:translate3d(0,0,0) scale(1)}100%{transform:translate3d(0,-3%,0) scale(1.06)}}
.wrap{max-width:1020px;margin:0 auto;padding:24px}
.hdr{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.live{width:12px;height:12px;border-radius:999px;background:var(--green);box-shadow:0 0 0 0 rgba(85,168,104,.6);animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(85,168,104,.55)}70%{box-shadow:0 0 0 12px rgba(85,168,104,0)}100%{box-shadow:0 0 0 0 rgba(85,168,104,0)}}
h1{font-size:19px;margin:0;letter-spacing:.2px}.meta{font-size:12px;color:var(--muted)}
.card{border:1px solid var(--line);border-radius:18px;background:var(--card);backdrop-filter:blur(14px);box-shadow:var(--shadow);
padding:18px;margin-bottom:16px;opacity:0;transform:translateY(10px);animation:rise .55s cubic-bezier(.2,.7,.2,1) forwards}
.card:nth-child(2){animation-delay:.05s}.card:nth-child(3){animation-delay:.10s}.card:nth-child(4){animation-delay:.15s}
@keyframes rise{to{opacity:1;transform:none}}
.card h2{margin:0 0 12px;font-size:15px}
.field{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.field label{font-size:13px;font-weight:600;min-width:110px}
input[type=text],input[type=number]{flex:1;min-width:220px;border:1px solid var(--line);border-radius:12px;padding:10px 13px;font-size:13px;font-family:var(--mono);background:#fff}
input[type=number]{flex:0 1 140px;min-width:110px}
input:focus{outline:2px solid rgba(76,114,176,.35);border-color:var(--blue)}
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid var(--line);font-size:11px}
.badge.ok{border-color:rgba(85,168,104,.45);background:rgba(85,168,104,.10);color:#2f6e44}
.badge.warn{border-color:rgba(204,185,116,.55);background:rgba(204,185,116,.14);color:#7a6a2a}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px}
button{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:13px;padding:11px 17px;font-size:14px;font-weight:700;position:relative;overflow:hidden;transition:transform .12s,border-color .2s,box-shadow .2s}
button:hover{border-color:var(--blue);box-shadow:0 4px 14px rgba(76,114,176,.18)}button:active{transform:scale(.97)}
button.primary{background:linear-gradient(135deg,#4C72B0,#5b86c9);color:#fff;border:none}
button:disabled{opacity:.5;cursor:not-allowed}
.rp{position:absolute;border-radius:50%;transform:scale(0);background:rgba(255,255,255,.5);animation:rp .6s ease-out}
@keyframes rp{to{transform:scale(3.5);opacity:0}}
.switch{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:#fff}
.switch button{border:none;border-radius:0;padding:9px 15px;font-size:13px}.switch button.act{background:var(--blue);color:#fff}
.switch button.actred{background:var(--red);color:#fff}
.prog{height:10px;border-radius:999px;background:rgba(15,23,42,.07);overflow:hidden;margin:10px 0 6px;display:none}
.prog>i{display:block;height:100%;width:0;background:linear-gradient(90deg,#4C72B0,#64B5CD);transition:width .4s ease}
.phase{font-size:12px;color:var(--muted);min-height:16px}
.result{font-family:var(--mono);font-size:12px;background:#0b1220;color:#e5e7eb;padding:14px;border-radius:13px;white-space:pre-wrap;max-height:380px;overflow:auto}
.muted{color:var(--muted);font-size:12px}
.stat{display:inline-block;margin-right:18px}.stat b{font-size:19px;color:var(--blue)}
.toast{position:fixed;right:22px;bottom:22px;background:#0b1220;color:#fff;padding:13px 17px;border-radius:13px;box-shadow:0 12px 30px rgba(0,0,0,.3);
font-size:13px;opacity:0;transform:translateY(16px);transition:.35s;z-index:9}.toast.show{opacity:1;transform:none}
.toast.ok{border-left:4px solid var(--green)}.toast.err{border-left:4px solid var(--red)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}body::before{animation:none}}
</style></head><body><div class="wrap">

<div class="hdr"><div class="live"></div><div><h1>Veritas Storage Optimizer <span style="color:var(--purple)">AIO</span></h1>
<div class="meta">單檔整併版 · 原生 PS 引擎 + Python / Node.js 子引擎 · 2-Pass Hash · 127.0.0.1:__PORT__</div></div></div>

<div class="card"><h2>引擎環境 (Engine Environment)</h2>
  <div id="env" class="muted">偵測中...</div>
</div>

<div class="card"><h2>掃描設定 (Scan Configuration)</h2>
  <div class="field"><label>目標資料夾</label><input type="text" id="dir" placeholder="/path/to/clean 或 C:\path\to\clean"></div>
  <div class="field"><label>大檔閾值 (MB)</label><input type="number" id="maxmb" value="__MAXMB__" min="1" step="50">
    <span class="muted">超過此容量的檔案將被標記刪除</span></div>
  <div class="field"><label>清理引擎</label>
    <div class="switch">
      <button id="engPs" class="act" onclick="setEngine('ps')">PowerShell (內建)</button>
      <button id="engPy" onclick="setEngine('python')">Python</button>
      <button id="engJs" onclick="setEngine('node')">Node.js</button>
    </div>
  </div>
  <div class="muted">保護名單:.git / .svn / .venv / node_modules / site-packages / $RECYCLE.BIN / System Volume Information 與所有 Python 虛擬環境(偵測 pyvenv.cfg)一律跳過;在資料夾內放置空檔案 <b>.veritas_protect</b> 可將該區整個鎖定不掃不刪;根目錄與家目錄上層一律拒絕;小於 1 KB 的檔案不列入重複比對(保護 __init__.py / .gitkeep 等結構檔)。</div>
</div>

<div class="card"><h2>執行</h2>
  <div class="bar">
    <span class="muted">模式:</span>
    <div class="switch"><button id="mScan" class="act" onclick="setExec(false)">僅掃描 Dry-Run (安全)</button><button id="mExec" onclick="setExec(true)">實體刪除</button></div>
    <button class="primary" id="btnRun" onclick="runClean()">▶ 開始掃描 (Dry-Run)</button>
  </div>
  <div class="prog" id="prog"><i id="progBar"></i></div>
  <div class="phase" id="phase"></div>
  <div style="margin:10px 0 8px">
    <span class="stat"><b id="stFiles">0</b> 標記檔案</span>
    <span class="stat"><b id="stDirs">0</b> 空資料夾</span>
    <span class="stat"><b id="stFreed">0 B</b> 可釋放容量</span>
  </div>
  <div class="result" id="out">就緒。先以 Dry-Run 檢視預計刪除清單,確認後再切換「實體刪除」。</div>
  <div class="muted" style="margin-top:8px">Log (append-only):__LOGPATH__</div>
</div>

</div>
<div class="toast" id="toast"></div>
<script>
"use strict";
var EXEC=false, ENGINE="ps", ENV=null;
function $(s){return document.querySelector(s);}
function toast(msg,type){var t=$("#toast");t.textContent=msg;t.className="toast show "+(type||"ok");
  setTimeout(function(){t.className="toast "+(type||"ok");},2600);}
function phase(txt,pct){$("#phase").textContent=txt;$("#progBar").style.width=pct+"%";}
function setEngine(e){
  if(e==="python"&&ENV&&(!ENV.Python||!ENV.PyEngine)){toast("Python 引擎未就緒","err");return;}
  if(e==="node"&&ENV&&(!ENV.Node||!ENV.JsEngine)){toast("Node.js 引擎未就緒","err");return;}
  ENGINE=e;
  $("#engPs").classList.toggle("act",e==="ps");
  $("#engPy").classList.toggle("act",e==="python");
  $("#engJs").classList.toggle("act",e==="node");}
function setExec(v){EXEC=v;
  $("#mScan").classList.toggle("act",!v);
  $("#mExec").classList.toggle("actred",v);
  $("#btnRun").textContent=v?"▶ 開始清理 (實體刪除)":"▶ 開始掃描 (Dry-Run)";}
async function loadEnv(){
  try{var r=await fetch("/api/env");ENV=await r.json();
    $("#env").innerHTML=
     '<span class="badge ok">PowerShell: '+ENV.PSVer+'</span> '+
     '<span class="badge '+(ENV.Python?"ok":"warn")+'">Python: '+(ENV.Python?ENV.PythonVer:"未偵測")+'</span> '+
     '<span class="badge '+(ENV.Node?"ok":"warn")+'">Node.js: '+(ENV.Node?ENV.NodeVer:"未偵測")+'</span> '+
     '<span class="badge '+(ENV.PyEngine?"ok":"warn")+'">Py Engine: '+(ENV.PyEngine?"就緒":"缺失")+'</span> '+
     '<span class="badge '+(ENV.JsEngine?"ok":"warn")+'">JS Engine: '+(ENV.JsEngine?"就緒":"缺失")+'</span>';
    if(!ENV.Python||!ENV.PyEngine){$("#engPy").disabled=true;}
    if(!ENV.Node||!ENV.JsEngine){$("#engJs").disabled=true;}
  }catch(e){$("#env").textContent="環境偵測失敗: "+e;}
}
async function runClean(){
  var dir=$("#dir").value.trim(), maxmb=parseFloat($("#maxmb").value);
  if(!dir){toast("請先輸入目標資料夾","err");return;}
  if(!(maxmb>0)){toast("大檔閾值必須為正數","err");return;}
  if(EXEC && !confirm("⚠ 實體刪除模式\n\n目標: "+dir+"\n將永久刪除暫存檔、超過 "+maxmb+" MB 的大檔與重複檔案。\n此動作無法復原。確定要繼續嗎?")) return;
  $("#btnRun").disabled=true;$("#prog").style.display="block";
  phase("階段 1/3 · 遍歷檔案樹 (2-Pass 候選收集)...",25);
  try{
    var r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({dir:dir,maxMB:maxmb,engine:ENGINE,execute:EXEC})});
    phase("階段 2/3 · 串流 Hash 重複比對...",65);
    var d=await r.json();
    if(!d.ok){throw new Error(d.error||"engine failed");}
    $("#stFiles").textContent=d.totalFiles;
    $("#stDirs").textContent=d.emptyDirs.length;
    $("#stFreed").textContent=d.freedHuman||"0 B";
    var s="["+(d.execute?"EXECUTE":"DRY-RUN")+"] engine="+d.engine+"  "+d.genTime+"  ("+d.elapsedSec+"s)\n";
    s+="Target: "+d.target+"\n可釋放容量: "+(d.freedHuman||"0 B")+"\n\n[標記清單]\n";
    var max=Math.min(d.items.length,500);
    for(var i=0;i<max;i++){var it=d.items[i];s+="  ["+it.reason+"] "+it.size+"  "+it.path+"\n";}
    if(d.items.length>max){s+="  ... 其餘 "+(d.items.length-max)+" 筆詳見稽核日誌\n";}
    s+="\n[空資料夾] "+d.emptyDirs.length+" 個\n";
    s+="\n稽核日誌: "+d.logPath+"\n";
    $("#out").textContent=s;
    phase("階段 3/3 · 完成 ✓",100);
    toast((d.execute?"清理完成":"掃描完成")+" · "+d.totalFiles+" 檔案 · "+(d.freedHuman||"0 B"),"ok");
  }catch(e){$("#out").textContent="執行失敗: "+e.message;phase("失敗",0);toast("執行失敗","err");}
  setTimeout(function(){$("#prog").style.display="none";phase("",0);},1200);
  $("#btnRun").disabled=false;
}
document.addEventListener("click",function(ev){var b=ev.target.closest("button");if(!b)return;
  var c=document.createElement("span");c.className="rp";var z=Math.max(b.clientWidth,b.clientHeight);
  c.style.width=c.style.height=z+"px";c.style.left=(ev.offsetX-z/2)+"px";c.style.top=(ev.offsetY-z/2)+"px";
  b.appendChild(c);setTimeout(function(){c.remove();},600);});
loadEnv();
</script></body></html>
'@

$script:HtmlBody = $htmlTpl.Replace('__PORT__', [string]$Port).Replace('__MAXMB__', [string]$MaxMB).Replace('__LOGPATH__', $script:LogFile)

# ============================================================================
#  EMBEDDED SELF-TEST  (-SelfTest)
# ============================================================================
function Invoke-SelfTest {
    Write-Host ''
    Write-Host '== Veritas AIO  Self-Test ==' -ForegroundColor Cyan
    $tests = [System.Collections.Generic.List[object]]::new()
    function Add-Test { param([string]$Name, [bool]$Ok) $tests.Add([pscustomobject]@{ Name = $Name; Ok = $Ok }) }

    Add-Test 'HTML tokens substituted' ((-not $script:HtmlBody.Contains('__PORT__')) -and $script:HtmlBody.Contains([string]$Port))
    Add-Test 'HTML structurally balanced' ($script:HtmlBody.Contains('<html') -and $script:HtmlBody.Contains('</html>') -and $script:HtmlBody.Length -gt 2000)

    $rootPath = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath('.'))
    Add-Test 'Guard rejects filesystem root'  ((Test-RefusedTarget -Path $rootPath) -ne '')
    $homeDir = [Environment]::GetFolderPath('UserProfile')
    Add-Test 'Guard rejects home directory'   ((Test-RefusedTarget -Path $homeDir) -ne '')
    Add-Test 'Guard rejects home ancestor'    ((Test-RefusedTarget -Path (Split-Path -Parent $homeDir)) -ne '')
    Add-Test 'Guard rejects empty'            ((Test-RefusedTarget -Path '') -ne '')

    Add-Test 'Format-Size 1536 -> 1.50 KB'    ((Format-Size 1536) -eq '1.50 KB')

    $sample = "[Temp File] 10.00 B -> /x/a.tmp`n[Duplicate of a.dat] 50.00 KB -> /x/b.dat`n[Empty Directory] -> /x/empty`nTotal Space to Free: 3.05 MB"
    $parsed = ConvertFrom-EngineOutput -Text $sample
    Add-Test 'Parser extracts item rows'      ($parsed.Items.Count -eq 2 -and $parsed.Items[0].reason -eq 'Temp File')
    Add-Test 'Parser extracts empty dirs'     ($parsed.EmptyDirs.Count -eq 1)
    Add-Test 'Parser extracts freed size'     ($parsed.FreedHuman -eq '3.05 MB')

    $envSnap = Get-EnvSnapshot
    Add-Test 'Env detects PowerShell version' ([bool]$envSnap.PSVer)

    $sand = Join-Path ([System.IO.Path]::GetTempPath()) ('veritas_aio_selftest_' + $PID)
    if (Test-Path -LiteralPath $sand) { Remove-Item -LiteralPath $sand -Recurse -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType Directory -Path (Join-Path $sand 'sub/empty_dir') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $sand '.git') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sand 'junk.tmp') -Value 'temp data'
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'bigfile.bin'), [byte[]]::new(3MB))
    $dupBytes = [byte[]]::new(51200); for ($i = 0; $i -lt 51200; $i++) { $dupBytes[$i] = 65 }
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'orig.dat'), $dupBytes)
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'sub/copy.dat'), $dupBytes)
    Set-Content -LiteralPath (Join-Path $sand 'keep.txt') -Value 'keep me'
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'stub_a.txt'), [byte[]]@(10))
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'stub_b.txt'), [byte[]]@(10))
    Set-Content -LiteralPath (Join-Path $sand '.git/protected.tmp') -Value 'protected'
    New-Item -ItemType Directory -Path (Join-Path $sand 'fake_env') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sand 'fake_env/pyvenv.cfg') -Value 'home = /usr'
    Set-Content -LiteralPath (Join-Path $sand 'fake_env/venvjunk.tmp') -Value 'venv temp'
    New-Item -ItemType Directory -Path (Join-Path $sand 'keepzone') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sand 'keepzone/.veritas_protect') -Value ''
    Set-Content -LiteralPath (Join-Path $sand 'keepzone/zonejunk.tmp') -Value 'zone temp'
    New-Item -ItemType Directory -Path (Join-Path $sand '__pycache__') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sand '__pycache__/mod.cpython-311.pyc') -Value 'bytecode'
    Set-Content -LiteralPath (Join-Path $sand 'legacy.pyc') -Value 'old bytecode'
    $pairBytes = [byte[]]::new(2048)
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'pair_a.dat'), $pairBytes)
    [System.IO.File]::WriteAllBytes((Join-Path $sand 'pair_b.txt'), $pairBytes)
    New-Item -ItemType Directory -Path (Join-Path $sand 'nest/inner') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sand 'nest/inner/only.tmp') -Value 'cascade me'

    Add-Test 'Guard accepts sandbox subdir'   ((Test-RefusedTarget -Path $sand) -eq '')

    $linkProbe = Join-Path $sand 'link_probe'
    $symPriv = $true
    try { New-Item -ItemType SymbolicLink -Path $linkProbe -Target (Join-Path $sand 'sub') -ErrorAction Stop | Out-Null } catch { $symPriv = $false }
    if ($symPriv) { Add-Test 'Guard rejects symlinked target' ((Test-RefusedTarget -Path $linkProbe) -ne '') }
    else          { Write-Host '  [SKIP] Guard rejects symlinked target (no symlink privilege)' -ForegroundColor Yellow }

    $dry = Invoke-VeritasRun -Engine 'ps' -Target $sand -MaxMBIn 2 -Live $false
    Add-Test 'Dry-run engine ok'              ([bool]$dry.ok)
    $reasons = @($dry.items | ForEach-Object { $_.reason }) -join '|'
    Add-Test 'Dry-run marks temp file'        ($reasons.Contains('Temp File'))
    Add-Test 'Dry-run marks oversize file'    ($reasons.Contains('Over Limit'))
    Add-Test 'Dry-run marks duplicate'        ($reasons.Contains('Duplicate of'))
    Add-Test 'Dry-run ignores tiny duplicates' (@($dry.items | Where-Object { $_.path.Contains('stub_') }).Count -eq 0)
    Add-Test 'Dry-run marks coding junk dir'  (@($dry.items | Where-Object { $_.reason -eq 'Coding Junk' -and $_.path.Contains('__pycache__') }).Count -eq 1)
    Add-Test 'Dry-run marks compiled leftover' (@($dry.items | Where-Object { $_.reason -eq 'Coding Junk' -and $_.path.Contains('legacy.pyc') }).Count -eq 1)
    Add-Test 'Dry-run keeps cross-ext twins'  (@($dry.items | Where-Object { $_.path.Contains('pair_') }).Count -eq 0)
    Add-Test 'Dry-run skips protected .git'   (-not (@($dry.items | Where-Object { $_.path.Contains('.git') }).Count -gt 0))
    Add-Test 'Dry-run skips python venv'      (@($dry.items | Where-Object { $_.path.Contains('fake_env') }).Count -eq 0)
    Add-Test 'Dry-run skips protect-marker zone' (@($dry.items | Where-Object { $_.path.Contains('keepzone') }).Count -eq 0)
    Add-Test 'Guard rejects protect-marked target' ((Test-RefusedTarget -Path (Join-Path $sand 'keepzone')) -ne '')
    Add-Test 'Dry-run counts empty dir'       ($dry.emptyDirs.Count -ge 1)
    Add-Test 'Dry-run deletes nothing'        ((Test-Path -LiteralPath (Join-Path $sand 'junk.tmp')) -and (Test-Path -LiteralPath (Join-Path $sand 'bigfile.bin')))
    Add-Test 'Dry-run audit log written'      (Test-Path -LiteralPath $dry.logPath)

    $live = Invoke-VeritasRun -Engine 'ps' -Target $sand -MaxMBIn 2 -Live $true
    Add-Test 'Execute engine ok'              ([bool]$live.ok)
    Add-Test 'Execute removes temp file'      (-not (Test-Path -LiteralPath (Join-Path $sand 'junk.tmp')))
    Add-Test 'Execute removes oversize file'  (-not (Test-Path -LiteralPath (Join-Path $sand 'bigfile.bin')))
    $survivors = @('orig.dat', 'sub/copy.dat') | Where-Object { Test-Path -LiteralPath (Join-Path $sand $_) }
    Add-Test 'Execute keeps one duplicate'    (@($survivors).Count -eq 1)
    Add-Test 'Execute keeps normal file'      (Test-Path -LiteralPath (Join-Path $sand 'keep.txt'))
    Add-Test 'Execute keeps protected .git'   (Test-Path -LiteralPath (Join-Path $sand '.git/protected.tmp'))
    Add-Test 'Execute keeps venv content'     (Test-Path -LiteralPath (Join-Path $sand 'fake_env/venvjunk.tmp'))
    Add-Test 'Execute keeps protect-marker zone' (Test-Path -LiteralPath (Join-Path $sand 'keepzone/zonejunk.tmp'))
    Add-Test 'Execute removes coding junk'    ((-not (Test-Path -LiteralPath (Join-Path $sand '__pycache__'))) -and (-not (Test-Path -LiteralPath (Join-Path $sand 'legacy.pyc'))))
    Add-Test 'Execute keeps cross-ext twins'  ((Test-Path -LiteralPath (Join-Path $sand 'pair_a.dat')) -and (Test-Path -LiteralPath (Join-Path $sand 'pair_b.txt')))
    Add-Test 'Execute removes empty dir'      (-not (Test-Path -LiteralPath (Join-Path $sand 'sub/empty_dir')))
    Add-Test 'Execute cascades nested empties' (-not (Test-Path -LiteralPath (Join-Path $sand 'nest')))

    Remove-Item -LiteralPath $sand -Recurse -Force -ErrorAction SilentlyContinue

    $pass = @($tests | Where-Object { $_.Ok }).Count
    $failN = @($tests | Where-Object { -not $_.Ok }).Count
    foreach ($t in $tests) {
        if ($t.Ok) { Write-Host ('  [PASS] ' + $t.Name) -ForegroundColor Green }
        else       { Write-Host ('  [FAIL] ' + $t.Name) -ForegroundColor Red }
    }
    $sumColor = if ($failN -eq 0) { 'Green' } else { 'Red' }
    Write-Host ('-- {0}/{1} PASS --' -f $pass, $tests.Count) -ForegroundColor $sumColor
    Write-Log ('SELFTEST {0}/{1} PASS' -f $pass, $tests.Count)
    return ($failN -eq 0)
}

if ($SelfTest) { $ok = Invoke-SelfTest; if ($ok) { exit 0 } else { exit 1 } }

# ============================================================================
#  FULL TEST CHAIN  (-TestAll): every suite in the project with one command.
#  Suites whose interpreter is missing are SKIPped, never silently dropped.
# ============================================================================
function Invoke-TestChain {
    Write-Host ''
    Write-Host '== Veritas AIO  Full Test Chain ==' -ForegroundColor Cyan
    $envSnap = Get-EnvSnapshot
    $suites = [System.Collections.Generic.List[object]]::new()
    function Add-Suite { param([string]$Name, [string]$State, [string]$Detail = '') $suites.Add([pscustomobject]@{ Name = $Name; State = $State; Detail = $Detail }) }
    function Invoke-Suite {
        param([string]$Name, [string]$Exe, [string[]]$ArgsList, [int]$TimeoutSec)
        Write-Host ''
        Write-Host ('-- ' + $Name + ' --') -ForegroundColor Cyan
        $r = Invoke-SubProc -Exe $Exe -ArgsList $ArgsList -TimeoutSec $TimeoutSec
        if ($r.Out) { Write-Host $r.Out.TrimEnd() }
        if ($r.Err) { Write-Host $r.Err.TrimEnd() -ForegroundColor Yellow }
        $state = 'FAIL'
        if ($r.Ok) { $state = 'PASS' }
        Add-Suite $Name $state ('exit ' + $r.Code)
    }

    $lintPath   = Join-Path $script:Base 'tests/ps_lint.py'
    $guiPath    = Join-Path $script:Base 'veritas_gui.py'
    $apiTest    = Join-Path $script:Base 'tests/e2e_apitest.js'
    $psTest     = Join-Path $script:Base 'tests/e2e_ps_usertest.js'

    if ($envSnap.Python -and (Test-Path -LiteralPath $lintPath)) {
        Invoke-Suite 'PS static lint (tests/ps_lint.py)' $envSnap.Python @($lintPath, $PSCommandPath) 120
    } else { Add-Suite 'PS static lint (tests/ps_lint.py)' 'SKIP' 'python or lint script missing' }

    Write-Host ''
    Write-Host '-- PS embedded self-test (-SelfTest) --' -ForegroundColor Cyan
    $selfState = 'FAIL'
    if (Invoke-SelfTest) { $selfState = 'PASS' }
    Add-Suite 'PS embedded self-test (-SelfTest)' $selfState

    if ($envSnap.Python -and (Test-Path -LiteralPath $guiPath)) {
        Invoke-Suite 'Python GUI self-test (veritas_gui.py --self-test)' $envSnap.Python @($guiPath, '--self-test') 300
    } else { Add-Suite 'Python GUI self-test' 'SKIP' 'python or veritas_gui.py missing' }

    if ($envSnap.Node -and $envSnap.Python -and (Test-Path -LiteralPath $apiTest)) {
        Invoke-Suite 'Python GUI e2e (tests/e2e_apitest.js)' $envSnap.Node @($apiTest) 900
    } else { Add-Suite 'Python GUI e2e (tests/e2e_apitest.js)' 'SKIP' 'node / python / test script missing' }

    if ($envSnap.Node -and (Test-Path -LiteralPath $psTest)) {
        Invoke-Suite 'PS AIO server e2e (tests/e2e_ps_usertest.js)' $envSnap.Node @($psTest) 900
    } else { Add-Suite 'PS AIO server e2e (tests/e2e_ps_usertest.js)' 'SKIP' 'node or test script missing' }

    Write-Host ''
    Write-Host '== Test Chain Summary ==' -ForegroundColor Cyan
    foreach ($s in $suites) {
        $color = 'Yellow'
        if ($s.State -eq 'PASS') { $color = 'Green' }
        if ($s.State -eq 'FAIL') { $color = 'Red' }
        $line = ('  [{0}] {1}' -f $s.State, $s.Name)
        if ($s.Detail) { $line = ($line + '  (' + $s.Detail + ')') }
        Write-Host $line -ForegroundColor $color
    }
    $failed = @($suites | Where-Object { $_.State -eq 'FAIL' }).Count
    $ranOk  = @($suites | Where-Object { $_.State -eq 'PASS' }).Count
    Write-Log ('TESTCHAIN pass={0} fail={1} skip={2}' -f $ranOk, $failed, (@($suites | Where-Object { $_.State -eq 'SKIP' }).Count))
    return ($failed -eq 0)
}

if ($TestAll) { $ok = Invoke-TestChain; if ($ok) { exit 0 } else { exit 1 } }

# ---- Headless CLI mode (-Dir) ------------------------------------------------
if ($Dir) {
    $res = Invoke-VeritasRun -Engine 'ps' -Target $Dir -MaxMBIn $MaxMB -Live $Execute.IsPresent
    if (-not $res.ok) { Write-Host ('[Error] ' + $res.error) -ForegroundColor Red; exit 1 }
    foreach ($it in $res.items) { Write-Host ('[{0}] {1} -> {2}' -f $it.reason, $it.size, $it.path) }
    Write-Host ('Items to purge: {0} files, {1} empty folders.' -f $res.totalFiles, $res.emptyDirs.Count)
    Write-Host ('Total Space to Free: ' + $res.freedHuman)
    Write-Host ('Audit log saved to: ' + $res.logPath)
    exit 0
}

# ---- Pre-flight gate ---------------------------------------------------------
$preflight = $true
try {
    $rootProbe = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath('.'))
    $preflight = ((Test-RefusedTarget -Path $rootProbe) -ne '') -and ((Format-Size 1024) -eq '1.00 KB') -and (-not $script:HtmlBody.Contains('__PORT__'))
} catch { $preflight = $false }
$pf = if ($preflight) { 'PASS' } else { 'WARN' }
Write-Log ('PRE-FLIGHT ' + $pf + ' (guard, format, html tokens)')

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

# Port busy -> probe the next 20 ports. Some Windows setups ACL-deny the
# 127.0.0.1 prefix for non-admin users while exempting localhost, so each
# port tries 127.0.0.1 first and falls back to localhost.
$listener = $null; $prefix = ''; $boundPort = $Port; $lastBindErr = ''
foreach ($cand in ($Port..($Port + 20))) {
    foreach ($bindHost in @('127.0.0.1', 'localhost')) {
        $probe = [System.Net.HttpListener]::new()
        $probe.Prefixes.Add(('http://{0}:{1}/' -f $bindHost, $cand))
        try {
            $probe.Start()
            $listener = $probe; $boundPort = $cand
            $prefix = ('http://{0}:{1}/' -f $bindHost, $cand)
            break
        } catch { $lastBindErr = $_.Exception.Message; try { $probe.Close() } catch {} }
    }
    if ($listener) { break }
}
if (-not $listener) {
    Write-Log (('HttpListener start failed on ports {0}-{1}: {2}' -f $Port, ($Port + 20), $lastBindErr)) 'ERROR'
    throw ('無法啟動後端(埠 {0}-{1} 皆不可用):{2}' -f $Port, ($Port + 20), $lastBindErr)
}
if ($boundPort -ne $Port) {
    Write-Log (('Port {0} busy - fell back to {1}' -f $Port, $boundPort)) 'WARN'
    $script:HtmlBody = $htmlTpl.Replace('__PORT__', [string]$boundPort).Replace('__MAXMB__', [string]$MaxMB).Replace('__LOGPATH__', $script:LogFile)
}
Write-Log ('Backend listening: ' + $prefix)
if (-not $NoBrowser) { try { Start-Process $prefix } catch {} }

Write-Host ''
Write-Host ('==> Veritas Storage Optimizer AIO is live at ' + $prefix) -ForegroundColor Green
Write-Host '==> Ctrl+C in this window to stop the server.' -ForegroundColor Yellow
Write-Host ''

try {
    # Async accept with short waits keeps Ctrl+C responsive and lets
    # /api/shutdown exit the loop promptly instead of blocking in GetContext.
    $pendingCtx = $null
    while ($listener.IsListening -and -not $script:Stop) {
        $ctx = $null
        try {
            if (-not $pendingCtx) { $pendingCtx = $listener.GetContextAsync() }
            if (-not $pendingCtx.Wait(250)) { continue }
            $ctx = $pendingCtx.Result
            $pendingCtx = $null
        } catch { break }
        if (-not $ctx) { continue }
        $path = $ctx.Request.Url.AbsolutePath
        try {
            switch -Regex ($path) {
                '^/$'          { Send-Response -Ctx $ctx -Body $script:HtmlBody -Type 'text/html; charset=utf-8'; break }
                '^/api/env$'   { Send-Response -Ctx $ctx -Body ((Get-EnvSnapshot) | ConvertTo-Json -Depth 5 -Compress); break }
                '^/api/run$' {
                    $enc = $ctx.Request.ContentEncoding; if (-not $enc) { $enc = [System.Text.Encoding]::UTF8 }
                    $reader = [System.IO.StreamReader]::new($ctx.Request.InputStream, $enc)
                    $bodyTxt = $reader.ReadToEnd(); $reader.Close()
                    if ([string]::IsNullOrWhiteSpace($bodyTxt)) { $bodyTxt = '{}' }
                    $req = $bodyTxt | ConvertFrom-Json
                    $engineName = if ($req.engine) { [string]$req.engine } else { 'ps' }
                    $maxIn = $MaxMB
                    if ($null -ne $req.PSObject.Properties['maxMB']) { $maxIn = [double]$req.maxMB }
                    $out = Invoke-VeritasRun -Engine $engineName -Target ([string]$req.dir) -MaxMBIn $maxIn -Live ([bool]$req.execute)
                    Send-Response -Ctx $ctx -Body ($out | ConvertTo-Json -Depth 6 -Compress)
                    break
                }
                '^/api/shutdown$' { Send-Response -Ctx $ctx -Body '{"ok":true}'; $script:Stop = $true; break }
                default        { Send-Response -Ctx $ctx -Body '{"error":"not found"}' -Code 404; break }
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
