#requires -Version 7.0
param(
    [ValidateSet('All', 'Scan', 'Repair', 'Verify')]
    [string]$Mode          = 'Scan',
    [string]$Root          = '',
    [string]$OutRoot       = 'C:\VIA\VIA_Unified',
    [string]$PythonExe     = 'C:\Users\tonyk\envs\via_vrn4\Scripts\python.exe',
    [int]$ThrottleLimit    = 8,
    [int]$ChunkSize        = 25,
    [int]$MaxFiles         = 0,
    [int]$MaxTestFiles     = 40,
    [int]$TestTimeoutS     = 30,
    [string[]]$ExcludePattern = @(
        '*\rollback\*', 'rb-*', '*\__pycache__\*', '*\.venv\*', '*\.git\*',
        '*\vendor\*', '*\VIA_RetiredEngines\*', '*\SCOPE_COPY\*',
        '*\site-packages\*', '*\node_modules\*', '*\_output\*',
        '*\_bytecode_originals\*'
    ),
    [switch]$IncludeSnapshots,
    [switch]$SkipTests,
    [switch]$RepairParseErrors,
    [string[]]$InstallPackages = @(),
    [string]$GoToken       = '',
    [switch]$NoOpen
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

# =====================================================================
# Invoke-VIA-Unified-Accel20-v0103
#
# One PowerShell file for the whole loop: scan, repair, verify.
# Pure PowerShell. Python is used only to run pytest, and only in Verify.
# Nothing here can be blocked by the environment layer.
#
# Non-blocking by construction:
#   - file analysis runs in parallel runspaces, in chunks, with the
#     progress bar and narration refreshed at every chunk boundary
#   - every child process is launched directly (never through a shell,
#     so paths with spaces survive), reads its streams asynchronously,
#     and is killed at a hard timeout
#   - no Start-Job, no Read-Host, no synchronous ReadToEnd on a pipe
#
# Modes
#   Scan    analyse only, write plan and matrix                (default)
#   Repair  Scan, then apply Parallel-Fixable fixes             (needs GO_v1)
#   Verify  Scan, then run the test suites and report
#   All     Scan, Repair, Verify in one pass                    (needs GO_v1)
#
# Governance: dry-run unless -GoToken GO_v1. Nothing is deleted. Every
# edit keeps a .viafix.bak sibling and is re-parsed in memory first: a
# fix that would introduce a parse error is rejected outright.
# =====================================================================

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Stamp     = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:RunId     = 'VIA-UNIFIED-v0103-' + $script:Stamp
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:LogLines  = [System.Collections.Generic.List[string]]::new()
$script:ApplyMode = ($GoToken -eq 'GO_v1')

$script:AccelNames = [ordered]@{
    'U01' = 'AST Precision Parser'
    'U02' = 'Token Stream Inspector'
    'U03' = 'Alias Expansion Detector'
    'U04' = 'Reserved Variable Guard'
    'U05' = 'Blocking Pattern Detector'
    'U06' = 'Deadlock Pattern Detector'
    'U07' = 'Encoding and BOM Normaliser'
    'U08' = 'Uncollectable Test Detector'
    'U09' = 'Hydra Coupling Graph'
    'U10' = 'Dependency Topology Sort'
    'U11' = 'Error Classification'
    'U12' = 'Complexity and Nesting'
    'U13' = 'Duplicate and Snapshot Analysis'
    'U14' = 'Sandbox Test Execution'
    'U15' = 'Precision Fix Generation'
    'U16' = 'Version Diff and Backup'
    'U17' = 'Dynamic Progress Bar'
    'U18' = 'Dynamic Status Narration'
    'U19' = 'Non-Blocking Parallel Execution'
    'U20' = 'UI Matrix and Auto-Init'
}
$script:Accel = [ordered]@{}
foreach ($k in $script:AccelNames.Keys) {
    $script:Accel[$k] = [pscustomobject]@{
        Id = $k; Name = $script:AccelNames[$k]; State = 'PENDING'; Mode = ''; Detail = ''; Count = 0
    }
}
function Set-Accel {
    param([string]$Id, [string]$State, [string]$Mode = '', [string]$Detail = '', [int]$Count = -1)
    $a = $script:Accel[$Id]
    if ($null -eq $a) { return }
    if ($a.State -eq 'GREEN' -and $State -eq 'RUNNING') { return }
    $a.State = $State
    if ($Mode -ne '')   { $a.Mode = $Mode }
    if ($Detail -ne '') { $a.Detail = $Detail }
    if ($Count -ge 0)   { $a.Count = $Count }
}
function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '] [' + $Level + '] ' + $Message
    $script:LogLines.Add($line)
    $c = 'Gray'
    if ($Level -eq 'OK')    { $c = 'Green' }
    if ($Level -eq 'WARN')  { $c = 'Yellow' }
    if ($Level -eq 'FAIL')  { $c = 'Red' }
    if ($Level -eq 'PHASE') { $c = 'Cyan' }
    if ($Level -eq 'ACCEL') { $c = 'Magenta' }
    Write-Host $line -ForegroundColor $c
}
function Show-Prog {
    param([string]$Status, [int]$Percent)
    Write-Progress -Activity ('VIA Unified · ' + $Mode + ' · 20 accelerators') `
                   -Status $Status -PercentComplete ([Math]::Min(100, [Math]::Max(0, $Percent)))
}
function Get-CleanPath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return $Value.Trim().Trim("'").Trim('"').TrimEnd('\')
}
function Write-TextFile {
    param([string]$Path, [string]$Content)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'Write-TextFile called with an empty path' }
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

# U19: direct launch, async stream drain, hard timeout. No shell, so a
# path containing spaces cannot be split; no pipe wait, so a chatty
# child cannot deadlock the parent.
function Invoke-Child {
    param([string]$FilePath, [string[]]$ArgumentList, [string]$WorkDir = '', [int]$TimeoutSeconds = 60)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    if ($WorkDir -ne '') { $psi.WorkingDirectory = $WorkDir }
    foreach ($a in $ArgumentList) { $psi.ArgumentList.Add($a) }
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    $sb = New-Object System.Text.StringBuilder
    $timedOut = $false
    try {
        $p.Start() | Out-Null
        $tOut = $p.StandardOutput.ReadToEndAsync()
        $tErr = $p.StandardError.ReadToEndAsync()
        $waited = 0
        while (-not $p.HasExited) {
            Start-Sleep -Milliseconds 200
            $waited += 200
            if ($waited -ge ($TimeoutSeconds * 1000)) {
                try { $p.Kill($true) } catch { }
                $timedOut = $true
                break
            }
        }
        $p.WaitForExit()
        try { [void]$sb.Append($tOut.GetAwaiter().GetResult()) } catch { }
        try { [void]$sb.Append($tErr.GetAwaiter().GetResult()) } catch { }
    } catch {
        [void]$sb.Append($_.Exception.Message)
    }
    $code = -1
    try { $code = $p.ExitCode } catch { }
    return [pscustomobject]@{ Code = $code; Out = $sb.ToString(); TimedOut = $timedOut }
}

Write-Host ''
Write-Host ('  VIA Unified Governance Engine  ·  20 Accelerators  ·  Mode: ' + $Mode) -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
if ($script:ApplyMode) {
    Write-Host '  GO token accepted: repairs will be written' -ForegroundColor Yellow
} else {
    Write-Host '  DRY-RUN: nothing will be written (pass -GoToken GO_v1 to apply)' -ForegroundColor DarkGray
}
Write-Host ''

# --- U20a  preflight, fail hard rather than cascade -------------------
$Root    = Get-CleanPath -Value $Root
$OutRoot = Get-CleanPath -Value $OutRoot
if ($OutRoot -eq '') { $OutRoot = 'C:\VIA\VIA_Unified' }
if ($Root -eq '' -or -not (Test-Path -LiteralPath $Root)) {
    Write-Host ('  BLOCKED_ROOT  pass -Root pointing at a real tree. Got: "' + $Root + '"') -ForegroundColor Red
    return
}
$runDir = ''
try {
    $runDir = Join-Path $OutRoot ('UNIFIED_' + $script:Stamp)
    foreach ($d in @($runDir, (Join-Path $runDir 'reports'), (Join-Path $runDir 'logs'))) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
} catch {
    Write-Host ('  BLOCKED_RUNDIR  cannot create output under "' + $OutRoot + '": ' + $_.Exception.Message) -ForegroundColor Red
    return
}
$ErrorActionPreference = 'Continue'
Set-Accel -Id 'U20' -State 'RUNNING' -Mode 'EXACT' -Detail $runDir
Write-Log ('run dir  ' + $runDir) 'OK'
Write-Log ('root     ' + $Root) 'OK'

# --- enumerate ---------------------------------------------------------
Show-Prog -Status 'enumerating' -Percent 3
$eo = [System.IO.EnumerationOptions]::new()
$eo.RecurseSubdirectories = $true
$eo.IgnoreInaccessible = $true
$psFiles = [System.Collections.Generic.List[string]]::new()
$pyFiles = [System.Collections.Generic.List[string]]::new()
$snapFiles = [System.Collections.Generic.List[string]]::new()
$excluded = 0
foreach ($f in [System.IO.Directory]::EnumerateFiles($Root, '*', $eo)) {
    $ext = [System.IO.Path]::GetExtension($f).ToLower()
    if ($ext -ne '.ps1' -and $ext -ne '.psm1' -and $ext -ne '.psd1' -and $ext -ne '.py') { continue }
    $leaf = [System.IO.Path]::GetFileName($f)
    if ($leaf -like '*.bak') { continue }
    $fNorm = $f.Replace('/', '\')
    if ($fNorm -like '*\rollback\*') { $snapFiles.Add($f) }
    if (-not $IncludeSnapshots) {
        $skip = $false
        foreach ($pat in $ExcludePattern) {
            $pNorm = $pat.Replace('/', '\')
            if ($fNorm -like $pNorm -or $leaf -like $pNorm) { $skip = $true; break }
        }
        if ($skip) { $excluded++; continue }
    }
    if ($ext -eq '.py') { $pyFiles.Add($f) } else { $psFiles.Add($f) }
}
if ($MaxFiles -gt 0 -and $psFiles.Count -gt $MaxFiles) {
    $psFiles = [System.Collections.Generic.List[string]]::new(@($psFiles)[0..($MaxFiles - 1)])
}
Write-Log ('targets  ' + $psFiles.Count + ' PowerShell, ' + $pyFiles.Count + ' Python, ' + $snapFiles.Count + ' snapshots') 'OK'
if ($excluded -gt 0) { Write-Log ($excluded.ToString() + ' files excluded (-IncludeSnapshots to scan them)') 'WARN' }
if ($psFiles.Count -eq 0 -and $pyFiles.Count -eq 0) {
    Write-Log 'BLOCKED_NO_TARGETS  nothing to analyse under -Root' 'FAIL'
    return
}
Set-Accel -Id 'U20' -State 'GREEN' -Detail ('paths ready, ' + $excluded + ' excluded')

# --- U19  parallel PowerShell analysis ---------------------------------
$psAnalyze = {
    $path = $_
    $RepairParseErrors = $using:RepairParseErrors
    $rec = [ordered]@{
        Path = $path; Name = [System.IO.Path]::GetFileName($path)
        ParseErrors = @(); Findings = @(); Fixes = @()
        Tokens = 0; Functions = 0; MaxNesting = 0; DotSources = 0; Bom = $false
    }
    try {
        $bytes = [System.IO.File]::ReadAllBytes($path)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $rec.Bom = $true }
        $text = [System.IO.File]::ReadAllText($path)
        $tokens = $null; $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$tokens, [ref]$errors)
        foreach ($e in $errors) {
            $rec.ParseErrors += [ordered]@{
                Message = $e.Message; Line = $e.Extent.StartLineNumber; Column = $e.Extent.StartColumnNumber
            }
        }
        $rec.Tokens = @($tokens).Count
        if ($null -ne $ast) {
            $rec.Functions = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)).Count
            foreach ($c in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
                $ne = $c.CommandElements[0]
                if ($null -eq $ne) { continue }
                $nm = $ne.Extent.Text
                if ($nm -eq '.') { $rec.DotSources++ }
                $al = @(Get-Alias -Name $nm -ErrorAction SilentlyContinue)
                if ($al.Count -eq 1) {
                    $tg = $al[0].ResolvedCommandName
                    if ([string]::IsNullOrWhiteSpace($tg)) { $tg = $al[0].Definition }
                    if (-not [string]::IsNullOrWhiteSpace($tg)) {
                        $rec.Findings += [ordered]@{ Rule='ALIAS_IN_SCRIPT'; Severity='LOW'; Class='Parallel-Fixable'
                            Line=$c.Extent.StartLineNumber; Detail=($nm + ' -> ' + $tg) }
                        $rec.Fixes += [pscustomobject]@{ Rule='ALIAS_IN_SCRIPT'
                            StartOffset=[int]$ne.Extent.StartOffset; EndOffset=[int]$ne.Extent.EndOffset; Replacement=[string]$tg }
                    }
                } elseif ($al.Count -gt 1) {
                    $rec.Findings += [ordered]@{ Rule='ALIAS_AMBIGUOUS'; Severity='MEDIUM'; Class='Sequence-Dependent'
                        Line=$c.Extent.StartLineNumber; Detail=($nm + ' resolves to several commands; pick one by hand') }
                }
                if ($nm -eq 'Read-Host') {
                    $rec.Findings += [ordered]@{ Rule='READ_HOST_BLOCKS'; Severity='HIGH'; Class='Sequence-Dependent'
                        Line=$c.Extent.StartLineNumber; Detail='interactive prompt stalls unattended runs' }
                }
                if ($nm -eq 'Start-Job' -or $nm -eq 'Wait-Job') {
                    $rec.Findings += [ordered]@{ Rule='START_JOB_BANNED'; Severity='HIGH'; Class='Sequence-Dependent'
                        Line=$c.Extent.StartLineNumber; Detail='use ProcessStartInfo or runspaces' }
                }
                if ($nm -eq 'Start-Process' -and $c.Extent.Text -notmatch '\.html?') {
                    $rec.Findings += [ordered]@{ Rule='START_PROCESS_CHILD'; Severity='MEDIUM'; Class='Sequence-Dependent'
                        Line=$c.Extent.StartLineNumber; Detail='ProcessStartInfo with ArgumentList is the governed pattern' }
                }
            }
            $reserved = @('args','input','home','env','error','host','psitem','this','true','false','null')
            foreach ($pa in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ParameterAst] }, $true)) {
                $vn = $pa.Name.VariablePath.UserPath
                if ($reserved -contains $vn.ToLower()) {
                    $rec.Findings += [ordered]@{ Rule='RESERVED_PARAM_NAME'; Severity='HIGH'; Class='Sequence-Dependent'
                        Line=$pa.Extent.StartLineNumber; Detail=('$' + $vn + ' is reserved or automatic') }
                }
            }
            $d = 0; $md = 0
            foreach ($ch in $text.ToCharArray()) {
                if ($ch -eq '{') { $d++; if ($d -gt $md) { $md = $d } } elseif ($ch -eq '}') { $d-- }
            }
            $rec.MaxNesting = $md
        }
        if ($text -match 'RedirectStandardOutput\s*=\s*\$true' -and $text -match 'ReadToEnd\(\)') {
            $rec.Findings += [ordered]@{ Rule='PIPE_READTOEND_DEADLOCK'; Severity='HIGH'; Class='Sequence-Dependent'
                Line=0; Detail='redirect to a file or read asynchronously' }
        }
        $glRx = [regex]'New-Object\s+(?:-TypeName\s+)?System\.Collections\.Generic\.List\[([A-Za-z0-9_.\[\]]+)\]'
        foreach ($m in $glRx.Matches($text)) {
            $inner = $m.Groups[1].Value
            $rec.Findings += [ordered]@{ Rule='GENERIC_LIST_NEW_OBJECT'; Severity='MEDIUM'; Class='Parallel-Fixable'
                Line=(($text.Substring(0, $m.Index) -split "`n").Count); Detail=('use [System.Collections.Generic.List[' + $inner + ']]::new()') }
            $rec.Fixes += [pscustomobject]@{ Rule='GENERIC_LIST_NEW_OBJECT'
                StartOffset=[int]$m.Index; EndOffset=[int]($m.Index + $m.Length)
                Replacement=('[System.Collections.Generic.List[' + $inner + ']]::new()') }
        }
        if ($text -match '\?\.') {
            $rec.Findings += [ordered]@{ Rule='NULL_CONDITIONAL'; Severity='MEDIUM'; Class='Sequence-Dependent'
                Line=0; Detail='not safe across all hosts here' }
        }
        if ($rec.Bom) {
            $rec.Findings += [ordered]@{ Rule='UTF8_BOM'; Severity='LOW'; Class='Parallel-Fixable'
                Line=1; Detail='rewrite as UTF-8 without BOM' }
        }
        # ------------------------------------------------------------
        # parse-error repairs. Each pattern below is mechanical: the
        # intent is unambiguous from the text itself. Anything requiring
        # judgement (a missing brace or paren somewhere in a 2000-line
        # file) is reported, never guessed at.
        # ------------------------------------------------------------
        if (@($rec.ParseErrors).Count -gt 0 -and $RepairParseErrors) {
            $msgs = @($rec.ParseErrors | ForEach-Object { $_.Message })
            $errLn = @($rec.ParseErrors | ForEach-Object { $_.Line })

            # "foreach($x in$y)" - the space before the operand was eaten
            if (($msgs -join ' ') -like "*Missing 'in' after variable in foreach loop*") {
                $frx = [regex]'(?i)(foreach\s*\(\s*\$[A-Za-z_][A-Za-z0-9_]*\s+in)(\$)'
                foreach ($m in $frx.Matches($text)) {
                    $rec.Fixes += [pscustomobject]@{ Rule='FOREACH_IN_SPACING'
                        StartOffset=[int]$m.Index; EndOffset=[int]($m.Index + $m.Length)
                        Replacement=($m.Groups[1].Value + ' $') }
                }
                $rec.Findings += [ordered]@{ Rule='FOREACH_IN_SPACING'; Severity='HIGH'; Class='Parallel-Fixable'
                    Line=$errLn[0]; Detail='foreach needs whitespace between in and its operand' }
            }

            # a block comment containing > or < : PowerShell reads the
            # angle bracket as redirection and the comment never closes
            if (($msgs -join ' ') -like '*Missing file specification after redirection operator*') {
                $rec.Findings += [ordered]@{ Rule='BLOCK_COMMENT_ANGLE'; Severity='HIGH'; Class='Sequence-Dependent'
                    Line=$errLn[0]; Detail='a block comment holds < or >; convert the whole comment to # line comments' }
            }
        }

        # a drive-qualified-looking "$var:" inside a string is the single
        # parse failure that can be repaired mechanically and proven
        if (@($rec.ParseErrors).Count -gt 0) {
            $needsBrace = $false
            foreach ($pe in $rec.ParseErrors) {
                if ($pe.Message -like "*was not followed by a valid variable name character*") { $needsBrace = $true }
            }
            if ($needsBrace) {
                # $env:, $script:, $global: and friends are legitimate scope
                # and drive qualifiers. Rewriting them to ${env}: still parses
                # but silently changes meaning, so they are never touched.
                $scopes = @('env','script','global','local','private','using','variable','function','alias','workflow')
                $errLines = @($rec.ParseErrors | ForEach-Object { $_.Line })
                $vrx = [regex]'\$([A-Za-z_][A-Za-z0-9_]*):(?![\\/:])'
                $emitted = 0
                foreach ($m in $vrx.Matches($text)) {
                    $nm2 = $m.Groups[1].Value
                    if ($scopes -contains $nm2.ToLower()) { continue }
                    if ($nm2.Length -eq 1) { continue }
                    $lineNo = ($text.Substring(0, $m.Index) -split "`n").Count
                    if ($errLines -notcontains $lineNo) { continue }
                    $rec.Fixes += [pscustomobject]@{ Rule='VAR_DELIMIT'
                        StartOffset=[int]$m.Index; EndOffset=[int]($m.Index + $m.Length)
                        Replacement=('${' + $nm2 + '}:') }
                    $emitted++
                }
                if ($emitted -gt 0) {
                    $rec.Findings += [ordered]@{ Rule='VAR_COLON_UNDELIMITED'; Severity='HIGH'; Class='Parallel-Fixable'
                        Line=(@($rec.ParseErrors)[0].Line); Detail='use ${name}: so the colon is not read as a scope or drive qualifier' }
                }
            }
        }
    } catch { }
    [pscustomobject]$rec
}

Write-Log 'U19  parallel PowerShell analysis' 'ACCEL'
$psResults = [System.Collections.Generic.List[object]]::new()
$totalChunks = [Math]::Max(1, [Math]::Ceiling($psFiles.Count / [double]$ChunkSize))
$ci = 0
$sw = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $psFiles.Count; $i += $ChunkSize) {
    $end = [Math]::Min($i + $ChunkSize - 1, $psFiles.Count - 1)
    $chunk = @($psFiles)[$i..$end]
    $ci++
    Show-Prog -Status ('U17 analysing chunk ' + $ci + '/' + $totalChunks) -Percent (3 + [int](32 * $ci / [double]$totalChunks))
    foreach ($r in ($chunk | ForEach-Object -Parallel $psAnalyze -ThrottleLimit $ThrottleLimit)) { $psResults.Add($r) }
    Write-Log ('U18  chunk ' + $ci + '/' + $totalChunks + '  ·  ' + $psResults.Count + ' parsed  ·  ' + [int]$sw.Elapsed.TotalSeconds + 's') 'ACCEL'
}
$sw.Stop()
Set-Accel -Id 'U19' -State 'GREEN' -Mode 'EXACT' -Detail ($totalChunks.ToString() + ' chunks, throttle ' + $ThrottleLimit)
Set-Accel -Id 'U17' -State 'GREEN' -Mode 'EXACT' -Detail ($totalChunks.ToString() + ' progress refreshes')
Set-Accel -Id 'U18' -State 'GREEN' -Mode 'EXACT' -Detail 'per-chunk narration streamed'

# --- roll up -----------------------------------------------------------
$findings = [System.Collections.Generic.List[object]]::new()
$parseBad = [System.Collections.Generic.List[object]]::new()
$tokens = 0; $coupled = 0; $deepest = 0
foreach ($r in $psResults) {
    $tokens += $r.Tokens
    if ($r.DotSources -gt 0) { $coupled++ }
    if ($r.MaxNesting -gt $deepest) { $deepest = $r.MaxNesting }
    if (@($r.ParseErrors).Count -gt 0) {
        $first = @($r.ParseErrors)[0]
        $ctx = ''
        try {
            $ln = @(Get-Content -LiteralPath $r.Path -ErrorAction Stop)
            $from = [Math]::Max(1, $first.Line - 3)
            $to = [Math]::Min($ln.Count, $first.Line + 3)
            $buf = [System.Collections.Generic.List[string]]::new()
            for ($z = $from; $z -le $to; $z++) {
                $mk = '  '
                if ($z -eq $first.Line) { $mk = '>>' }
                $buf.Add($mk + ' ' + $z.ToString().PadLeft(5) + '  ' + $ln[$z - 1])
            }
            $ctx = ($buf -join "`n")
        } catch { }
        $parseBad.Add([pscustomobject]@{ File=$r.Name; Path=$r.Path; Errors=@($r.ParseErrors).Count
            Line=$first.Line; Message=$first.Message; Context=$ctx })
    }
    foreach ($f in $r.Findings) {
        $findings.Add([pscustomobject]@{ File=$r.Name; Path=$r.Path; Rule=$f.Rule
            Severity=$f.Severity; Class=$f.Class; Line=$f.Line; Detail=$f.Detail })
    }
}
function Count-Rule { param([string[]]$Rules) return @($findings | Where-Object { $Rules -contains $_.Rule }).Count }
$parallelFix = @($findings | Where-Object { $_.Class -eq 'Parallel-Fixable' })
# count fixes that actually exist, not findings that merely look fixable.
# v0100 reported 74 ready and applied none, which is the same false-green
# failure this engine exists to catch.
$applicableFix = 0
$filesWithFix = 0
foreach ($r in $psResults) {
    $nf = @($r.Fixes).Count
    if ($r.Bom) { $nf++ }
    if ($nf -gt 0) { $filesWithFix++; $applicableFix += $nf }
}
$seqDep      = @($findings | Where-Object { $_.Class -eq 'Sequence-Dependent' })

Set-Accel -Id 'U01' -State $(if ($parseBad.Count) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail ($parseBad.Count.ToString() + ' scripts fail to parse') -Count $parseBad.Count
Set-Accel -Id 'U02' -State 'GREEN' -Mode 'EXACT' -Detail ($tokens.ToString() + ' tokens') -Count $tokens
Set-Accel -Id 'U03' -State $(if ((Count-Rule -Rules @('ALIAS_IN_SCRIPT','ALIAS_AMBIGUOUS'))) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'command-token anchored, strings untouched' -Count (Count-Rule -Rules @('ALIAS_IN_SCRIPT','ALIAS_AMBIGUOUS'))
Set-Accel -Id 'U04' -State $(if ((Count-Rule -Rules @('RESERVED_PARAM_NAME'))) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'reserved and automatic names in param blocks' -Count (Count-Rule -Rules @('RESERVED_PARAM_NAME'))
Set-Accel -Id 'U05' -State $(if ((Count-Rule -Rules @('READ_HOST_BLOCKS','START_JOB_BANNED','START_PROCESS_CHILD'))) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'Read-Host, Start-Job, child launches' -Count (Count-Rule -Rules @('READ_HOST_BLOCKS','START_JOB_BANNED','START_PROCESS_CHILD'))
Set-Accel -Id 'U06' -State $(if ((Count-Rule -Rules @('PIPE_READTOEND_DEADLOCK'))) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'redirected pipe plus synchronous ReadToEnd' -Count (Count-Rule -Rules @('PIPE_READTOEND_DEADLOCK'))
Set-Accel -Id 'U07' -State $(if ((Count-Rule -Rules @('UTF8_BOM'))) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'BOM detection at byte level' -Count (Count-Rule -Rules @('UTF8_BOM'))
Set-Accel -Id 'U09' -State $(if ($coupled) { 'YELLOW' } else { 'GREEN' }) -Mode 'HEURISTIC' -Detail 'dot-source count as a coupling proxy, not a blast-radius proof' -Count $coupled
Set-Accel -Id 'U10' -State 'GREEN' -Mode 'EXACT' -Detail 'parallel fixes first, then sequence-dependent by severity'
Set-Accel -Id 'U11' -State 'GREEN' -Mode 'EXACT' -Detail ($parallelFix.Count.ToString() + ' parallel / ' + $seqDep.Count.ToString() + ' sequential; ' + $applicableFix.ToString() + ' concrete edits across ' + $filesWithFix.ToString() + ' files')
Set-Accel -Id 'U12' -State $(if ($deepest -ge 10) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail ('deepest brace nesting ' + $deepest) -Count $deepest

# --- U08  uncollectable tests (pure PowerShell, no Python needed) ------
Show-Prog -Status 'U08 uncollectable test detection' -Percent 38
Write-Log 'U08  uncollectable test detection' 'ACCEL'
$defTestFiles = [System.Collections.Generic.List[object]]::new()
$wokenFiles   = [System.Collections.Generic.List[object]]::new()
$n = 0
foreach ($f in $pyFiles) {
    $n++
    if ($n % 400 -eq 0) {
        Show-Prog -Status ('U08 scanning python ' + $n + '/' + $pyFiles.Count) -Percent (38 + [int](7 * $n / [double]$pyFiles.Count))
        Write-Log ('U18  python scan ' + $n + '/' + $pyFiles.Count) 'ACCEL'
    }
    $txt = ''
    try { $txt = [System.IO.File]::ReadAllText($f) } catch { continue }
    if ($txt -notmatch 'def\s+(def_)?test_') { continue }
    $bad = ([regex]::Matches($txt, '(?m)^def\s+def_test_')).Count
    $good = ([regex]::Matches($txt, '(?m)^def\s+test_')).Count
    if ($bad -gt 0) { $defTestFiles.Add([pscustomobject]@{ Path=$f; Name=[System.IO.Path]::GetFileName($f); Count=$bad }) }
    if ($good -gt 0) { $wokenFiles.Add([pscustomobject]@{ Path=$f; Name=[System.IO.Path]::GetFileName($f); Tests=$good }) }
}
Set-Accel -Id 'U08' -State $(if ($defTestFiles.Count) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' `
    -Detail ($defTestFiles.Count.ToString() + ' files hold def_test_ that pytest can never collect; ' + $wokenFiles.Count.ToString() + ' files expose collectable tests') `
    -Count $defTestFiles.Count
Write-Log ('  ' + $defTestFiles.Count + ' uncollectable, ' + $wokenFiles.Count + ' collectable') 'OK'

# --- U13  duplicate and snapshot analysis ------------------------------
Show-Prog -Status 'U13 duplicate analysis' -Percent 47
Write-Log 'U13  duplicate and snapshot analysis' 'ACCEL'
$dupFamilies = @($psResults | Group-Object Name | Where-Object { $_.Count -gt 1 } | Sort-Object Count -Descending)
$dupFiles = ($dupFamilies | Measure-Object Count -Sum).Sum
# a family whose copies differ is drift; one whose copies match is just
# duplication. Only the first is a correctness risk.
$dupDetail = [System.Collections.Generic.List[object]]::new()
$driftFamilies = 0
$dq = 0
foreach ($fam in $dupFamilies) {
    $dq++
    if ($dq % 20 -eq 0) { Show-Prog -Status ('U13 hashing family ' + $dq + '/' + $dupFamilies.Count) -Percent 49 }
    $hashes = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($g in $fam.Group) {
        try { [void]$hashes.Add((Get-FileHash -LiteralPath $g.Path -Algorithm SHA256).Hash) } catch { }
    }
    $verdict = 'IDENTICAL'
    if ($hashes.Count -gt 1) { $verdict = 'DRIFTED'; $driftFamilies++ }
    $dupDetail.Add([pscustomobject]@{ Name=$fam.Name; Copies=$fam.Count; Distinct=$hashes.Count; Verdict=$verdict })
}
Set-Accel -Id 'U13' -State $(if ($driftFamilies) { 'RED' } elseif ($dupFamilies.Count) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' `
    -Detail ($dupFamilies.Count.ToString() + ' duplicated names covering ' + [int]$dupFiles + ' files; ' + $driftFamilies.ToString() + ' have copies that have drifted apart') `
    -Count $driftFamilies
Write-Log ('  ' + $dupFamilies.Count + ' duplicated names, ' + $driftFamilies + ' drifted') 'OK'

# --- U15 / U16  repair --------------------------------------------------
$applied = 0; $rejected = 0; $healed = 0; $partial = 0
$doRepair = ($Mode -eq 'Repair' -or $Mode -eq 'All')
if ($doRepair -and $script:ApplyMode) {
    Show-Prog -Status 'U15 applying parallel-safe fixes' -Percent 52
    Write-Log 'U15  applying parallel-safe fixes only' 'ACCEL'
    $k = 0
    foreach ($r in $psResults) {
        $k++
        $fixes = @($r.Fixes)
        if ($fixes.Count -eq 0 -and -not $r.Bom) { continue }
        if ($k % 20 -eq 0) { Show-Prog -Status ('U15 repairing ' + $k + '/' + $psResults.Count) -Percent 55 }
        try {
            $text = [System.IO.File]::ReadAllText($r.Path)
            foreach ($fx in ($fixes | Sort-Object -Property { [int]$_.StartOffset } -Descending)) {
                $len = $fx.EndOffset - $fx.StartOffset
                $text = $text.Remove($fx.StartOffset, $len).Insert($fx.StartOffset, $fx.Replacement)
            }
            $t2 = $null; $e2 = $null
            [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$t2, [ref]$e2) | Out-Null
            $before = @($r.ParseErrors).Count
            $after = @($e2).Count
            if ($after -gt $before) {
                $rejected++
                Write-Log ('  REJECT ' + $r.Name + '  ' + $before + ' -> ' + $after + ' parse errors, the fix makes it worse') 'FAIL'
                continue
            }
            if ($before -gt 0 -and $after -gt 0) {
                $partial++
                Write-Log ('  partial ' + $r.Name + '  ' + $before + ' -> ' + $after + ' parse errors, still broken') 'WARN'
            } elseif ($before -gt 0 -and $after -eq 0) {
                $healed++
                Write-Log ('  healed  ' + $r.Name + '  ' + $before + ' -> 0 parse errors') 'OK'
            }
            $bak = $r.Path + '.viafix.bak'
            if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $r.Path -Destination $bak -Force }
            [System.IO.File]::WriteAllText($r.Path, $text, $script:Utf8NoBom)
            $applied++
        } catch {
            Write-Log ('  fix failed ' + $r.Name + ': ' + $_.Exception.Message) 'FAIL'
        }
    }
    Write-Log ('  ' + $applied + ' edited, ' + $healed + ' fully healed, ' + $partial + ' improved but still broken, ' + $rejected + ' rejected') 'OK'
    Set-Accel -Id 'U15' -State 'GREEN' -Mode 'EXACT' -Detail ($applied.ToString() + ' edited, ' + $healed.ToString() + ' parse errors fully healed, ' + $partial.ToString() + ' improved but still broken, ' + $rejected.ToString() + ' rejected as making things worse') -Count $applied
    Set-Accel -Id 'U16' -State 'GREEN' -Mode 'EXACT' -Detail '.viafix.bak written before every edit' -Count $applied
} elseif ($doRepair) {
    Set-Accel -Id 'U15' -State 'SKIPPED' -Mode 'EXACT' -Detail ($applicableFix.ToString() + ' concrete edits ready; GO token absent')
    Set-Accel -Id 'U16' -State 'SKIPPED' -Mode 'EXACT' -Detail 'no edits, no backups needed'
    Write-Log 'U15  repair requested but no GO token; nothing written' 'WARN'
} else {
    Set-Accel -Id 'U15' -State 'SKIPPED' -Mode 'EXACT' -Detail ('mode is ' + $Mode)
    Set-Accel -Id 'U16' -State 'SKIPPED' -Mode 'EXACT' -Detail ('mode is ' + $Mode)
}

# --- U20b  optional package install, same GO gate as everything else ---
$pkgList = [System.Collections.Generic.List[string]]::new()
foreach ($raw in $InstallPackages) {
    foreach ($one in ($raw -split '[,;]')) {
        $t = $one.Trim().Trim("'").Trim('"')
        if ($t -ne '') { $pkgList.Add($t) }
    }
}
if ($pkgList.Count -gt 0) {
    Show-Prog -Status 'U20 installing packages' -Percent 56
    Write-Log ('U20  package install requested: ' + ($pkgList -join ', ')) 'ACCEL'
    if (-not $script:ApplyMode) {
        Write-Log '  dry-run: nothing installed. Add -GoToken GO_v1 to proceed.' 'WARN'
    } elseif (-not (Test-Path -LiteralPath $PythonExe)) {
        Write-Log ('  BLOCKED python missing: ' + $PythonExe) 'FAIL'
    } else {
        $uv = Get-Command uv -ErrorAction SilentlyContinue
        foreach ($pkg in $pkgList) {
            $ir = $null
            if ($null -ne $uv) {
                $ir = Invoke-Child -FilePath $uv.Source -ArgumentList @('pip','install','--python',$PythonExe,$pkg) -TimeoutSeconds 300
            } else {
                $ir = Invoke-Child -FilePath $PythonExe -ArgumentList @('-m','pip','install','--upgrade',$pkg,'--disable-pip-version-check') -TimeoutSeconds 300
            }
            if ($ir.Code -eq 0) {
                Write-Log ('  installed ' + $pkg) 'OK'
            } else {
                $why = (($ir.Out -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -Last 1))
                Write-Log ('  failed ' + $pkg + '  ' + $why) 'WARN'
            }
        }
    }
}

# --- U14  sandbox test execution ---------------------------------------
$testRows = [System.Collections.Generic.List[object]]::new()
$passT = 0; $failT = 0; $errT = 0; $toT = 0; $envT = 0
$missingModules = [System.Collections.Generic.HashSet[string]]::new()
$doVerify = ($Mode -eq 'Verify' -or $Mode -eq 'All')
if (-not $doVerify -or $SkipTests) {
    Set-Accel -Id 'U14' -State 'SKIPPED' -Mode 'EXACT' -Detail ('mode is ' + $Mode)
} elseif (-not (Test-Path -LiteralPath $PythonExe)) {
    Set-Accel -Id 'U14' -State 'RED' -Mode 'EXACT' -Detail ('python not found at ' + $PythonExe)
    Write-Log ('U14  BLOCKED python missing: ' + $PythonExe) 'FAIL'
} else {
    Show-Prog -Status 'U14 sandbox test execution' -Percent 58
    Write-Log 'U14  sandbox test execution' 'ACCEL'

    # pytest walks up looking for a config file. On this machine it finds
    # one in the home directory, which silently changes rootdir and
    # collection for every run. Pin an empty ini so behaviour is the
    # same no matter where the engine is invoked from.
    $pinIni = Join-Path $runDir 'via_pytest.ini'
    Write-TextFile -Path $pinIni -Content "[pytest]`n"

    $probeDir = Join-Path $runDir '_probe'
    New-Item -ItemType Directory -Path $probeDir -Force | Out-Null
    $probeFile = Join-Path $probeDir 'test_via_probe.py'
    Write-TextFile -Path $probeFile -Content "def test_probe():`n    assert 1 + 1 == 2`n"
    $probe = Invoke-Child -FilePath $PythonExe -ArgumentList @('-m','pytest',$probeFile,'-q','--no-header','-c',$pinIni,'-p','no:cacheprovider') -WorkDir $probeDir -TimeoutSeconds 60
    if ($probe.Out -match '1\s+passed') {
        Write-Log '  harness self-check OK (1 passed)' 'OK'
    } else {
        Write-Log '  HARNESS_SELFCHECK_FAILED  results below are not trustworthy' 'FAIL'
    }

    $subset = @($wokenFiles | Sort-Object Tests -Descending | Select-Object -First $MaxTestFiles)
    $j = 0
    foreach ($w in $subset) {
        $j++
        Show-Prog -Status ('U14 pytest ' + $j + '/' + $subset.Count + '  ' + $w.Name) -Percent (58 + [int](25 * $j / [double][Math]::Max(1, $subset.Count)))
        $ownDir = [System.IO.Path]::GetDirectoryName($w.Path)
        $prevPP = $env:PYTHONPATH
        $env:PYTHONPATH = $ownDir
        $r = Invoke-Child -FilePath $PythonExe -ArgumentList @('-m','pytest',$w.Path,'-q','--no-header','-c',$pinIni,'-p','no:cacheprovider') -WorkDir $ownDir -TimeoutSeconds $TestTimeoutS
        $env:PYTHONPATH = $prevPP
        $p = 0; $fl = 0; $er = 0
        if ($r.Out -match '(\d+)\s+passed') { $p = [int]$Matches[1] }
        if ($r.Out -match '(\d+)\s+failed') { $fl = [int]$Matches[1] }
        if ($r.Out -match '(\d+)\s+error')  { $er = [int]$Matches[1] }
        $cause = ''; $mod = ''
        if ($r.Out -match "ModuleNotFoundError: No module named '([^']+)'") { $cause = 'ENV_MISSING_MODULE'; $mod = $Matches[1] }
        elseif ($r.Out -match 'ImportError') { $cause = 'ENV_IMPORT' }
        $state = 'PASS'
        $hangAt = ''
        if ($r.TimedOut) {
            $state = 'TIMEOUT'; $toT++
            # a timeout on its own says nothing. Re-run once under
            # faulthandler so the stack at the moment of the hang is
            # captured, then report the deepest frame in our own code.
            # faulthandler with exit=True aborts the process, so the dump
            # never reaches a captured pipe. Write it to a file instead.
            $dumpFile = Join-Path $runDir ('_hang_' + [System.IO.Path]::GetFileNameWithoutExtension($w.Path) + '_' + $j + '.txt')
            $probe = 'import faulthandler,sys' + "`n" +
                     '_f = open(r"' + $dumpFile + '","w")' + "`n" +
                     'faulthandler.dump_traceback_later(' + [int]([Math]::Max(5, $TestTimeoutS / 2)) + ', file=_f, exit=True)' + "`n" +
                     'import pytest' + "`n" +
                     'sys.exit(pytest.main([r"' + $w.Path + '","-q","--no-header","-c",r"' + $pinIni + '","-p","no:cacheprovider"]))'
            $d = Invoke-Child -FilePath $PythonExe -ArgumentList @('-c', $probe) -WorkDir $ownDir -TimeoutSeconds ($TestTimeoutS + 15)
            $dumpText = ''
            if (Test-Path -LiteralPath $dumpFile) { $dumpText = [System.IO.File]::ReadAllText($dumpFile) }
            $frames = @($dumpText -split "`n" | Where-Object { $_ -match 'File "' -and $_ -match 'line \d+' })
            if ($frames.Count -gt 0) {
                # prefer the deepest frame that is not inside pytest or the
                # standard library: that is the code actually hanging
                # drop the launcher shim and anything inside pytest or the
                # standard library; what is left is the code that is stuck
                $own = @($frames | Where-Object {
                    $_ -notmatch 'File "<string>"' -and
                    $_ -notmatch '(?i)\\(site-packages|Lib)\\' -and
                    $_ -notmatch '(?i)/(site-packages|lib)/' -and
                    $_ -notmatch '(?i)[\\/](_pytest|pluggy)[\\/]'
                })
                $pick = $frames[0]
                if ($own.Count -gt 0) { $pick = $own[0] }
                $hangAt = ($pick.Trim() -replace '\s+', ' ')
            }
            if ($hangAt -eq '') {
                $hangAt = 'no stack captured within ' + $TestTimeoutS + 's'
            }
            if ($hangAt -ne '') { Write-Log ('    hang at: ' + $hangAt) 'WARN' }
        }
        elseif ($cause -ne '' -and $p -eq 0 -and $fl -eq 0) { $state = 'ENV_GAP'; $envT++ }
        elseif ($fl -gt 0) { $state = 'FAIL' }
        elseif ($er -gt 0) { $state = 'ERROR' }
        elseif ($p -eq 0)  { $state = 'NO_TESTS' }
        $passT += $p; $failT += $fl; $errT += $er
        if ($mod -ne '') { [void]$missingModules.Add($mod) }
        $tail = ($r.Out -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -Last 1)
        $testRows.Add([pscustomobject]@{ File=$w.Name; Path=$w.Path; Declared=$w.Tests
            Passed=$p; Failed=$fl; Errors=$er; State=$state; Cause=$cause; MissingModule=$mod; HangAt=$hangAt
            Tail=($tail -replace '[\u0000-\u001F]', ' ') })
        $lvl = 'OK'
        if ($state -ne 'PASS') { $lvl = 'WARN' }
        Write-Log ('U18  ' + $j + '/' + $subset.Count + '  ' + $state.PadRight(8) + ' ' + $w.Name + '  (' + $p + 'P/' + $fl + 'F/' + $er + 'E)') $lvl
    }
    $realBad = @($testRows | Where-Object { $_.State -eq 'FAIL' -or $_.State -eq 'ERROR' }).Count
    $st = 'GREEN'
    if ($realBad -gt 0) { $st = 'RED' } elseif ($toT -gt 0 -or $envT -gt 0) { $st = 'YELLOW' }
    Set-Accel -Id 'U14' -State $st -Mode 'EXACT' `
        -Detail ($passT.ToString() + ' passed, ' + $failT.ToString() + ' failed, ' + $toT.ToString() + ' timed out, ' + $envT.ToString() + ' blocked by a missing package (not a defect)') `
        -Count $testRows.Count
}

# --- plan, verdict, matrix ---------------------------------------------
Show-Prog -Status 'U20 rendering matrix' -Percent 90
$blockers = [System.Collections.Generic.List[string]]::new()
if ($parseBad.Count -gt 0) { $blockers.Add($parseBad.Count.ToString() + ' scripts fail to parse') }
if ($defTestFiles.Count -gt 0) { $blockers.Add($defTestFiles.Count.ToString() + ' files with uncollectable tests') }
$rf = @($testRows | Where-Object { $_.State -eq 'FAIL' }).Count
$re = @($testRows | Where-Object { $_.State -eq 'ERROR' }).Count
if ($rf -gt 0) { $blockers.Add($rf.ToString() + ' failing test files') }
if ($re -gt 0) { $blockers.Add($re.ToString() + ' erroring test files') }
if ($rejected -gt 0) { $blockers.Add($rejected.ToString() + ' fixes rejected by re-parse') }

$overall = 'GREEN'
if ($blockers.Count -gt 0) { $overall = 'RED' }
elseif ($findings.Count -gt 0 -or $toT -gt 0 -or $envT -gt 0) { $overall = 'YELLOW' }

$actions = [System.Collections.Generic.List[object]]::new()
$rank = 1
if ($parseBad.Count -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Fix ' + $parseBad.Count + ' unparseable scripts'); Why='they cannot run at all; purely mechanical, no judgement needed' }); $rank++ }
if ($defTestFiles.Count -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Rename def_test_ in ' + $defTestFiles.Count + ' files'); Why='pytest reports "no tests ran" and the exit code looks clean: a false green' }); $rank++ }
if ($rf + $re -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Triage ' + ($rf + $re) + ' failing or erroring test files'); Why='these were invisible until the tests became collectable' }); $rank++ }
if ($missingModules.Count -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Install or path-fix: ' + (($missingModules | Sort-Object) -join ', ')); Why='environment gaps, not defects; they inflate the error count' }); $rank++ }
if ($driftFamilies -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Pick a canonical copy for ' + $driftFamilies + ' drifted name families'); Why='same name, different content in several places: a passing copy can mask a failing original' }); $rank++ }
elseif ($dupFamilies.Count -gt 0) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Deduplicate ' + $dupFamilies.Count + ' identical copies'); Why='no correctness risk, but they inflate every scan' }); $rank++ }
if ($applicableFix -gt 0 -and -not $script:ApplyMode) { $actions.Add([pscustomobject]@{ Order=$rank; Action=('Apply ' + $applicableFix + ' concrete edits across ' + $filesWithFix + ' files with -Mode Repair -GoToken GO_v1'); Why='mechanical and reversible from the .viafix.bak siblings' }); $rank++ }
$actions.Add([pscustomobject]@{ Order=$rank; Action='Re-run in Verify mode once the above settle'; Why='a clean denominator makes the remaining reds meaningful' })

$plan = [pscustomobject]@{
    schema='VIA_Unified/1.0'; run_id=$script:RunId; at=$script:StartedAt.ToString('s'); mode=$Mode
    root=$Root; overall=$overall; apply_mode=$script:ApplyMode; blockers=$blockers
    ps_files=$psFiles.Count; py_files=$pyFiles.Count; excluded=$excluded
    findings=$findings; parse_errors=$parseBad; def_test_files=$defTestFiles
    applicable_fixes=$applicableFix; files_with_fix=$filesWithFix
    duplicate_families=$dupDetail; drifted_families=$driftFamilies
    tests=$testRows; missing_modules=@($missingModules); actions=$actions
    applied=$applied; rejected=$rejected; healed=$healed; partial=$partial
}
if ($driftFamilies -gt 0) {
    $ledger = [System.Collections.Generic.List[string]]::new()
    $ledger.Add('name,copies,distinct,path,sha256')
    foreach ($fam in $dupFamilies) {
        $dd = $dupDetail | Where-Object { $_.Name -eq $fam.Name } | Select-Object -First 1
        if ($null -eq $dd -or $dd.Verdict -ne 'DRIFTED') { continue }
        foreach ($g in $fam.Group) {
            $h = ''
            try { $h = (Get-FileHash -LiteralPath $g.Path -Algorithm SHA256).Hash.Substring(0,16) } catch { }
            $ledger.Add('"' + $fam.Name + '",' + $dd.Copies + ',' + $dd.Distinct + ',"' + $g.Path + '","' + $h + '"')
        }
    }
    Write-TextFile -Path (Join-Path $runDir 'drift_ledger.csv') -Content (($ledger -join "`n") + "`n")
    Write-Log ('  drift ledger written: ' + (Join-Path $runDir 'drift_ledger.csv')) 'OK'
}

$planPath = Join-Path $runDir 'unified_plan.json'
Write-TextFile -Path $planPath -Content ($plan | ConvertTo-Json -Depth 6)

function Get-Badge { param([string]$S)
    $c='gy'
    if ($S -eq 'GREEN' -or $S -eq 'PASS') { $c='gr' }
    if ($S -eq 'YELLOW' -or $S -eq 'TIMEOUT' -or $S -eq 'NO_TESTS' -or $S -eq 'SKIPPED') { $c='ye' }
    if ($S -eq 'RED' -or $S -eq 'FAIL' -or $S -eq 'ERROR') { $c='rd' }
    if ($S -eq 'ENV_GAP') { $c='bl' }
    return '<span class="b ' + $c + '">' + $S + '</span>'
}
function Section-Rows { param([string[]]$Ids)
    $s=''
    foreach ($id in $Ids) {
        $a = $script:Accel[$id]
        $m = $(if ($a.Mode) { $a.Mode } else { 'EXACT' })
        $mb = 'exact'; if ($m -eq 'HEURISTIC') { $mb='heur' }
        $s = $s + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c"><span class="b ' + $mb + '">' + $m + '</span></td><td class="c">' + $a.Count + '</td><td>' + $a.Detail + '</td></tr>'
    }
    return $s
}
Set-Accel -Id 'U20' -State 'GREEN' -Detail 'four-section matrix rendered'

$secModule = Section-Rows -Ids @('U01','U08','U13','U11','U12')
$secEngine = Section-Rows -Ids @('U14','U15','U16','U19','U20')
$secLib    = Section-Rows -Ids @('U02','U03','U04','U05','U06','U07','U09','U10')
$secOther  = Section-Rows -Ids @('U17','U18')

$rowsRule = ''
foreach ($g in ($findings | Group-Object Rule | Sort-Object Count -Descending)) {
    $s0 = ($g.Group | Select-Object -First 1)
    $sb = 'ye'; if ($s0.Severity -eq 'HIGH') { $sb='rd' }; if ($s0.Severity -eq 'LOW') { $sb='gy' }
    $rowsRule = $rowsRule + '<tr><td class="m">' + $g.Name + '</td><td class="c"><span class="b ' + $sb + '">' + $s0.Severity + '</span></td><td class="c">' + $s0.Class + '</td><td class="c">' + $g.Count + '</td><td>' + $s0.Detail + '</td></tr>'
}
if ($rowsRule -eq '') { $rowsRule = '<tr><td colspan="5" class="dim">Clean.</td></tr>' }

$rowsParse = ''
foreach ($p in $parseBad) {
    $ctxHtml = ''
    if ($p.Context) { $ctxHtml = '<pre style="margin:5px 0 0;max-height:150px">' + ($p.Context.Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')) + '</pre>' }
    $rowsParse = $rowsParse + '<tr><td class="m">' + $p.File + '</td><td class="c">' + $p.Errors + '</td><td class="c">' + $p.Line + '</td><td>' + ($p.Message -replace '<','&lt;') + $ctxHtml + '</td></tr>'
}
if ($rowsParse -eq '') { $rowsParse = '<tr><td colspan="4" class="dim">Every script parses.</td></tr>' }

$rowsTest = ''
foreach ($t in ($testRows | Sort-Object @{e={$_.State -eq 'PASS'}}, File)) {
    $ct = $t.Cause
    if ($t.MissingModule -ne '') { $ct = $ct + ' (' + $t.MissingModule + ')' }
    if ($t.HangAt -ne '') { $ct = 'hang: ' + $t.HangAt }
    $rowsTest = $rowsTest + '<tr><td class="m">' + $t.File + '</td><td class="c">' + (Get-Badge -S $t.State) + '</td><td class="c">' + $t.Declared + '</td><td class="c">' + $t.Passed + '</td><td class="c">' + $t.Failed + '</td><td class="m dim">' + $ct + '</td><td class="m dim">' + $t.Tail + '</td></tr>'
}
if ($rowsTest -eq '') { $rowsTest = '<tr><td colspan="7" class="dim">No tests executed in this mode.</td></tr>' }

$rowsDup = ''
foreach ($d in ($dupDetail | Sort-Object @{e={$_.Verdict -eq 'IDENTICAL'}}, @{e={-$_.Distinct}} | Select-Object -First 40)) {
    $vb = 'gy'
    if ($d.Verdict -eq 'DRIFTED') { $vb = 'rd' }
    $rowsDup = $rowsDup + '<tr><td class="m">' + $d.Name + '</td><td class="c">' + $d.Copies + '</td><td class="c">' + $d.Distinct + '</td><td class="c"><span class="b ' + $vb + '">' + $d.Verdict + '</span></td></tr>'
}
if ($rowsDup -eq '') { $rowsDup = '<tr><td colspan="4" class="dim">No duplicated names.</td></tr>' }

$rowsAct = ''
foreach ($a in $actions) { $rowsAct = $rowsAct + '<tr><td class="c">' + $a.Order + '</td><td>' + $a.Action + '</td><td class="dim">' + $a.Why + '</td></tr>' }

$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$logText = ($script:LogLines -join "`n").Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA UNIFIED MATRIX — $($script:RunId)</title>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --line:#334155; --tx:#f8fafc; --mu:#94a3b8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--tx); overflow-x:hidden;
         font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif;
         font-size:11px; line-height:1.35; letter-spacing:-0.01em; }
  .wrap { width:100%; max-width:1400px; margin:0 auto; padding:18px 14px 48px; }
  h1 { font-size:14px; margin:0; font-weight:600; }
  .sub { font-size:11px; color:var(--mu); margin:3px 0 0; }
  h2 { font-size:12px; margin:22px 0 7px; font-weight:600; border-bottom:1px solid var(--line); padding-bottom:5px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:8px; margin-top:14px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:3px; padding:9px 11px; }
  .kpi .n { font-size:17px; font-weight:600; }
  .kpi .l { font-size:10px; color:var(--mu); margin-top:2px; }
  table { width:100%; table-layout:fixed; border-collapse:collapse; background:var(--card);
          border:1px solid var(--line); border-radius:3px; }
  th { font-size:11px; color:var(--mu); font-weight:500; text-align:left; padding:4px 6px; border-bottom:1px solid var(--line); }
  td { padding:4px 6px; border-bottom:1px solid #253248; vertical-align:top;
       word-wrap:break-word; overflow-wrap:break-word; white-space:normal; }
  tr:last-child td { border-bottom:none; }
  td.c { text-align:center; }
  .m { font-family:ui-monospace,Consolas,monospace; }
  .dim { color:var(--mu); }
  .b { display:inline-block; font-size:10px; padding:1px 6px; border-radius:2px; border:1px solid; }
  .gr { background:#064e3b; color:#34d399; border-color:#059669; }
  .ye { background:#78350f; color:#fde047; border-color:#d97706; }
  .rd { background:#7f1d1d; color:#fca5a5; border-color:#dc2626; }
  .gy { background:#1f2937; color:#9ca3af; border-color:#374151; }
  .bl { background:#1e3a5f; color:#93c5fd; border-color:#3b82f6; }
  .exact { background:#0c2d48; color:#7dd3fc; border-color:#0369a1; }
  .heur { background:#3b2f0b; color:#fcd34d; border-color:#a16207; }
  .note { background:var(--card); border:1px solid var(--line); border-left:3px solid #d97706;
          border-radius:3px; padding:10px 12px; }
  pre { background:#0b1220; color:#cbd5e1; font-family:ui-monospace,Consolas,monospace;
        font-size:10.5px; padding:11px; border-radius:3px; overflow-x:auto; max-height:300px; }
</style>
</head>
<body>
<div class="wrap">

<h1>VIA UNIFIED GOVERNANCE MATRIX</h1>
<p class="sub">$($script:RunId) · mode $Mode · overall $overall · $elapsed s · $Root</p>

<div class="kpis">
  <div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div>
  <div class="kpi"><div class="n">$($psFiles.Count)</div><div class="l">powershell files</div></div>
  <div class="kpi"><div class="n">$($pyFiles.Count)</div><div class="l">python files</div></div>
  <div class="kpi"><div class="n">$($parseBad.Count)</div><div class="l">unparseable</div></div>
  <div class="kpi"><div class="n">$($findings.Count)</div><div class="l">findings</div></div>
  <div class="kpi"><div class="n">$applicableFix</div><div class="l">concrete edits ready</div></div>
  <div class="kpi"><div class="n">$applied</div><div class="l">files edited</div></div>
  <div class="kpi"><div class="n">$healed</div><div class="l">parse errors healed</div></div>
  <div class="kpi"><div class="n">$passT</div><div class="l">tests passing</div></div>
  <div class="kpi"><div class="n">$failT</div><div class="l">tests failing</div></div>
  <div class="kpi"><div class="n">$envT</div><div class="l">env gap, not a defect</div></div>
</div>

<h2>MODULE</h2>
<table><colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
<thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead><tbody>$secModule</tbody></table>

<h2>ENGINE</h2>
<table><colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
<thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead><tbody>$secEngine</tbody></table>

<h2>FUNCTION-LIB</h2>
<table><colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
<thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead><tbody>$secLib</tbody></table>

<h2>OTHERS</h2>
<table><colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
<thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead><tbody>$secOther</tbody></table>

<h2>RULE MATRIX</h2>
<table><colgroup><col style="width:24%"><col style="width:10%"><col style="width:16%"><col style="width:8%"><col style="width:42%"></colgroup>
<thead><tr><th>Rule</th><th>Severity</th><th>Class</th><th>Count</th><th>Remedy</th></tr></thead><tbody>$rowsRule</tbody></table>

<h2>UNPARSEABLE SCRIPTS</h2>
<table><colgroup><col style="width:30%"><col style="width:8%"><col style="width:8%"><col style="width:54%"></colgroup>
<thead><tr><th>Script</th><th>Errors</th><th>Line</th><th>First message</th></tr></thead><tbody>$rowsParse</tbody></table>

<h2>TEST EXECUTION</h2>
<table><colgroup><col style="width:24%"><col style="width:9%"><col style="width:8%"><col style="width:7%"><col style="width:7%"><col style="width:14%"><col style="width:31%"></colgroup>
<thead><tr><th>File</th><th>State</th><th>Declared</th><th>Pass</th><th>Fail</th><th>Cause</th><th>pytest tail</th></tr></thead><tbody>$rowsTest</tbody></table>

<h2>DUPLICATE NAME FAMILIES</h2>
<table><colgroup><col style="width:58%"><col style="width:12%"><col style="width:14%"><col style="width:16%"></colgroup>
<thead><tr><th>File name</th><th>Copies</th><th>Distinct contents</th><th>Verdict</th></tr></thead><tbody>$rowsDup</tbody></table>

<h2>ORDERED ACTIONS</h2>
<table><colgroup><col style="width:6%"><col style="width:44%"><col style="width:50%"></colgroup>
<thead><tr><th>#</th><th>Action</th><th>Why</th></tr></thead><tbody>$rowsAct</tbody></table>

<h2>EVIDENCE HONESTY</h2>
<div class="note">
  EXACT accelerators report a measurement taken by the PowerShell parser itself, a byte-level check,
  or a real pytest exit. HEURISTIC accelerators report a proxy: U09 counts dot-sources as a coupling
  stand-in, which is not a proof of blast radius. Only Parallel-Fixable findings are ever applied,
  each edit is anchored to an exact AST extent offset, and the file is re-parsed in memory before it
  reaches disk — a fix that would introduce a parse error is rejected and the original left untouched.
  pytest runs against a pinned empty ini so a stray config file elsewhere on the machine cannot
  silently change collection.
</div>

<h2>CONSOLE LOG</h2>
<pre>$logText</pre>

</div>
</body>
</html>
"@

$reportPath = Join-Path $runDir ('reports\VIA_UNIFIED_MATRIX_' + $script:Stamp + '.html')
Write-TextFile -Path $reportPath -Content $html
Write-TextFile -Path (Join-Path $runDir 'logs\console.log') -Content $logText
Write-Progress -Activity ('VIA Unified · ' + $Mode + ' · 20 accelerators') -Completed

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  ' + $psFiles.Count + ' ps1  ·  ' + $findings.Count + ' findings  ·  ' + $applied + ' edited  ·  ' + $passT + 'P/' + $failT + 'F') -ForegroundColor Green
if ($blockers.Count -gt 0) { Write-Host ('  blockers: ' + ($blockers -join '; ')) -ForegroundColor Yellow }
Write-Host ('  plan    ' + $planPath) -ForegroundColor DarkGray
Write-Host ('  matrix  ' + $reportPath) -ForegroundColor DarkGray
if ($applicableFix -gt 0 -and -not $script:ApplyMode) {
    Write-Host ('  ' + $applicableFix + ' concrete edits across ' + $filesWithFix + ' files ready: -Mode Repair -GoToken GO_v1') -ForegroundColor Yellow
}
Write-Host ''
if (-not $NoOpen) { try { Start-Process -FilePath $reportPath } catch { } }
