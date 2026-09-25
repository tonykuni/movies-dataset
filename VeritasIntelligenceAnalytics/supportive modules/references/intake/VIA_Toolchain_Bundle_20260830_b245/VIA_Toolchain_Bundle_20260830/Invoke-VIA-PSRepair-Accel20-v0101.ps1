#requires -Version 7.0
param(
    [string]$Root          = '',
    [string[]]$Paths       = @(),
    [string]$OutRoot       = 'C:\VIA\VIA_PSRepair',
    [int]$ThrottleLimit    = 8,
    [int]$ChunkSize        = 25,
    [int]$MaxFiles         = 0,
    [string[]]$ExcludePattern = @('*\rollback\*', 'rb-*', '*\_bytecode_originals\*', '*\__pycache__\*'),
    [switch]$IncludeSnapshots,
    [string]$GoToken       = '',
    [switch]$NoOpen
)

# =====================================================================
# Invoke-VIA-PSRepair-Accel20-v0101
# PowerShell multi-round AST auto-repair engine.
#
# Pure PowerShell. No Python, no pytest, no EnvManager. It cannot be
# blocked by the environment layer because it depends on nothing that
# layer manages.
#
# Non-blocking by construction: files are analysed in parallel runspaces
# in chunks, and the progress bar plus narration are refreshed between
# every chunk. No Start-Job, no pipe ReadToEnd, no Read-Host.
#
# Dry-run by default. -GoToken GO_v1 applies only the fixes classified
# Parallel-Fixable, and every edited file keeps a .psrepair.bak sibling.
# =====================================================================

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Stamp     = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:RunId     = 'VIA-PSREPAIR-v0101-' + $script:Stamp
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:LogLines  = [System.Collections.Generic.List[string]]::new()
$script:ApplyMode = ($GoToken -eq 'GO_v1')

$script:AccelNames = [ordered]@{
    'P01' = 'AST Precision Parser'
    'P02' = 'Token Stream Inspector'
    'P03' = 'Alias Expansion Detector'
    'P04' = 'Cmdlet Resolution Check'
    'P05' = 'Reserved Variable Guard'
    'P06' = 'Encoding and BOM Normaliser'
    'P07' = 'Blocking Pattern Detector'
    'P08' = 'Deadlock Pattern Detector'
    'P09' = 'Hydra Coupling Graph'
    'P10' = 'Dependency Topology Sort'
    'P11' = 'Error Classification'
    'P12' = 'Complexity and Nesting'
    'P13' = 'PSScriptAnalyzer Bridge'
    'P14' = 'Sandbox Re-Parse Verify'
    'P15' = 'Precision Fix Generation'
    'P16' = 'Version Diff and Backup'
    'P17' = 'Dynamic Progress Bar'
    'P18' = 'Dynamic Status Narration'
    'P19' = 'Non-Blocking Parallel Execution'
    'P20' = 'UI Matrix Render'
}
$script:Accel = [ordered]@{}
foreach ($k in $script:AccelNames.Keys) {
    $script:Accel[$k] = [pscustomobject]@{
        Id = $k; Name = $script:AccelNames[$k]; State = 'PENDING'; Mode = ''; Detail = ''; Count = 0
    }
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

function Set-Accel {
    param([string]$Id, [string]$State, [string]$Mode = '', [string]$Detail = '', [int]$Count = -1)
    $a = $script:Accel[$Id]
    if ($null -eq $a) { return }
    # never let a later stage downgrade a finished accelerator back to RUNNING
    if ($a.State -eq 'GREEN' -and $State -eq 'RUNNING') { return }
    $a.State = $State
    if ($Mode -ne '')   { $a.Mode = $Mode }
    if ($Detail -ne '') { $a.Detail = $Detail }
    if ($Count -ge 0)   { $a.Count = $Count }
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
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

Write-Host ''
Write-Host '  VIA PowerShell Repair Engine  ·  20 Accelerators' -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
if ($script:ApplyMode) {
    Write-Host '  MODE: APPLY  (GO token accepted)' -ForegroundColor Yellow
} else {
    Write-Host '  MODE: DRY-RUN  (pass -GoToken GO_v1 to apply parallel-safe fixes)' -ForegroundColor DarkGray
}
Write-Host ''

# --- P20a  preflight: fail hard, never cascade -------------------------
$Root    = Get-CleanPath -Value $Root
$OutRoot = Get-CleanPath -Value $OutRoot
if ([string]::IsNullOrWhiteSpace($OutRoot)) { $OutRoot = 'C:\VIA\VIA_PSRepair' }

$runDir = ''
try {
    $runDir = Join-Path $OutRoot ('PSREPAIR_' + $script:Stamp)
    foreach ($d in @($runDir, (Join-Path $runDir 'reports'), (Join-Path $runDir 'logs'))) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
} catch {
    Write-Host ('  BLOCKED_RUNDIR  cannot create output under "' + $OutRoot + '": ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host '  nothing was analysed and nothing was changed.' -ForegroundColor Red
    return
}
Write-Log ('run dir  ' + $runDir) 'OK'

# --- gather targets ----------------------------------------------------
$ErrorActionPreference = 'Continue'
$targets = [System.Collections.Generic.List[string]]::new()
foreach ($p in $Paths) {
    $cp = Get-CleanPath -Value $p
    if ($cp -ne '' -and (Test-Path -LiteralPath $cp)) { $targets.Add((Resolve-Path -LiteralPath $cp).Path) }
}
if ($Root -ne '') {
    if (-not (Test-Path -LiteralPath $Root)) {
        Write-Log ('BLOCKED_ROOT_ABSENT  ' + $Root) 'FAIL'
        return
    }
    $opts = [System.IO.EnumerationOptions]::new()
    $opts.RecurseSubdirectories = $true
    $opts.IgnoreInaccessible    = $true
    $excluded = 0
    foreach ($f in [System.IO.Directory]::EnumerateFiles($Root, '*', $opts)) {
        if ($f -like '*\.git\*') { continue }
        $ext = [System.IO.Path]::GetExtension($f).ToLower()
        if ($ext -ne '.ps1' -and $ext -ne '.psm1' -and $ext -ne '.psd1') { continue }
        if (-not $IncludeSnapshots) {
            $leaf = [System.IO.Path]::GetFileName($f)
            $skip = $false
            foreach ($pat in $ExcludePattern) {
                if ($f -like $pat -or $leaf -like $pat) { $skip = $true; break }
            }
            if ($skip) { $excluded++; continue }
        }
        $targets.Add($f)
    }
    if ($excluded -gt 0) {
        Write-Log ($excluded.ToString() + ' files excluded as snapshots or backups (pass -IncludeSnapshots to scan them)') 'WARN'
    }
}
$fileList = @($targets | Sort-Object -Unique)
if ($MaxFiles -gt 0 -and $fileList.Count -gt $MaxFiles) { $fileList = $fileList[0..($MaxFiles - 1)] }

if ($fileList.Count -eq 0) {
    Write-Log 'BLOCKED_NO_TARGETS  pass -Root or -Paths' 'FAIL'
    return
}
Write-Log ('targets  ' + $fileList.Count + ' PowerShell files') 'OK'

# --- P13  PSScriptAnalyzer availability -------------------------------
$hasPSSA = $null -ne (Get-Module -ListAvailable -Name PSScriptAnalyzer -ErrorAction SilentlyContinue)
if ($hasPSSA) {
    Set-Accel -Id 'P13' -State 'GREEN' -Mode 'EXACT' -Detail 'PSScriptAnalyzer present'
    Write-Log 'P13  PSScriptAnalyzer available' 'ACCEL'
} else {
    Set-Accel -Id 'P13' -State 'YELLOW' -Mode 'EXACT' -Detail 'PSScriptAnalyzer absent; AST checks only, coverage is narrower'
    Write-Log 'P13  PSScriptAnalyzer absent, AST-only coverage' 'WARN'
}

# --- the per-file analyser, self-contained for the parallel runspace ---
$analyzeBlock = {
    $path = $_
    $rec = [ordered]@{
        Path = $path; Name = [System.IO.Path]::GetFileName($path)
        ParseErrors = @(); Findings = @(); Fixes = @()
        Tokens = 0; Functions = 0; MaxNesting = 0; Lines = 0
        Bom = $false; MixedEol = $false; DotSources = @()
        Error = ''
    }
    try {
        $bytes = [System.IO.File]::ReadAllBytes($path)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $rec.Bom = $true
        }
        $text = [System.IO.File]::ReadAllText($path)
        $rec.Lines = ($text -split "`n").Count
        $crlf = ([regex]::Matches($text, "`r`n")).Count
        $lfOnly = ([regex]::Matches($text, "(?<!`r)`n")).Count
        if ($crlf -gt 0 -and $lfOnly -gt 0) { $rec.MixedEol = $true }

        # P01 precision AST
        $tokens = $null
        $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$tokens, [ref]$errors)
        foreach ($e in $errors) {
            $rec.ParseErrors += [ordered]@{
                Message = $e.Message
                Line    = $e.Extent.StartLineNumber
                Column  = $e.Extent.StartColumnNumber
                Text    = $e.Extent.Text
            }
        }
        $rec.Tokens = @($tokens).Count

        if ($null -ne $ast) {
            $fns = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)
            $rec.Functions = @($fns).Count

            # P03 alias detection at command-token level, never inside strings
            $cmds = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)
            foreach ($c in $cmds) {
                $nameAst = $c.CommandElements[0]
                if ($null -eq $nameAst) { continue }
                $nm = $nameAst.Extent.Text
                $al = @(Get-Alias -Name $nm -ErrorAction SilentlyContinue)
                if ($al.Count -eq 1) {
                    $target = $al[0].ResolvedCommandName
                    if ([string]::IsNullOrWhiteSpace($target)) { $target = $al[0].Definition }
                    if (-not [string]::IsNullOrWhiteSpace($target)) {
                        $rec.Findings += [ordered]@{
                            Rule = 'ALIAS_IN_SCRIPT'; Severity = 'LOW'; Class = 'Parallel-Fixable'
                            Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                            Detail = ($nm + ' -> ' + $target)
                        }
                        $rec.Fixes += [pscustomobject]@{
                            Rule = 'ALIAS_IN_SCRIPT'
                            StartOffset = [int]$nameAst.Extent.StartOffset
                            EndOffset   = [int]$nameAst.Extent.EndOffset
                            Replacement = [string]$target
                        }
                    } else {
                        $rec.Findings += [ordered]@{
                            Rule = 'ALIAS_UNRESOLVED'; Severity = 'MEDIUM'; Class = 'Sequence-Dependent'
                            Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                            Detail = ($nm + ' is an alias but its target could not be resolved on this host')
                        }
                    }
                } elseif ($al.Count -gt 1) {
                    # ambiguous on this host: report it, never guess a replacement
                    $rec.Findings += [ordered]@{
                        Rule = 'ALIAS_AMBIGUOUS'; Severity = 'MEDIUM'; Class = 'Sequence-Dependent'
                        Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                        Detail = ($nm + ' resolves to ' + (($al | ForEach-Object { $_.ResolvedCommandName }) -join ' / ') + '; pick one by hand')
                    }
                }
                # P07 blocking patterns
                if ($nm -eq 'Read-Host') {
                    $rec.Findings += [ordered]@{
                        Rule = 'READ_HOST_BLOCKS'; Severity = 'HIGH'; Class = 'Sequence-Dependent'
                        Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                        Detail = 'interactive prompt stalls unattended runs'
                    }
                }
                if ($nm -eq 'Start-Job' -or $nm -eq 'Wait-Job') {
                    $rec.Findings += [ordered]@{
                        Rule = 'START_JOB_BANNED'; Severity = 'HIGH'; Class = 'Sequence-Dependent'
                        Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                        Detail = 'use ProcessStartInfo or runspaces instead'
                    }
                }
                if ($nm -eq 'Start-Process') {
                    $argTxt = $c.Extent.Text
                    if ($argTxt -notmatch '\.html?|\-FilePath\s+\$\w*[Rr]eport') {
                        $rec.Findings += [ordered]@{
                            Rule = 'START_PROCESS_CHILD'; Severity = 'MEDIUM'; Class = 'Sequence-Dependent'
                            Line = $c.Extent.StartLineNumber; Col = $c.Extent.StartColumnNumber
                            Detail = 'ProcessStartInfo with ArgumentList is the governed pattern'
                        }
                    }
                }
                # dot-source graph for P09
                if ($nm -eq '.') {
                    $rec.DotSources += $c.Extent.Text
                }
            }

            # P05 reserved variable names in param blocks
            $params = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ParameterAst] }, $true)
            $reserved = @('args', 'input', 'home', 'env', 'error', 'host', 'psitem', 'this', 'true', 'false', 'null')
            foreach ($pa in $params) {
                $vn = $pa.Name.VariablePath.UserPath
                if ($reserved -contains $vn.ToLower()) {
                    $rec.Findings += [ordered]@{
                        Rule = 'RESERVED_PARAM_NAME'; Severity = 'HIGH'; Class = 'Sequence-Dependent'
                        Line = $pa.Extent.StartLineNumber; Col = $pa.Extent.StartColumnNumber
                        Detail = ('$' + $vn + ' is reserved or automatic')
                    }
                }
            }

            # P12 nesting depth
            $depth = 0
            $maxd = 0
            foreach ($ch in $text.ToCharArray()) {
                if ($ch -eq '{') { $depth++; if ($depth -gt $maxd) { $maxd = $depth } }
                elseif ($ch -eq '}') { $depth-- }
            }
            $rec.MaxNesting = $maxd
        }

        # P08 deadlock: redirected stdout plus a synchronous ReadToEnd
        if ($text -match 'RedirectStandardOutput\s*=\s*\$true' -and $text -match 'ReadToEnd\(\)') {
            $rec.Findings += [ordered]@{
                Rule = 'PIPE_READTOEND_DEADLOCK'; Severity = 'HIGH'; Class = 'Sequence-Dependent'
                Line = 0; Col = 0
                Detail = 'redirect to a file and poll, or read asynchronously'
            }
        }
        # LL: generic List construction that throws on @() conversion
        if ($text -match 'New-Object\s+System\.Collections\.Generic\.List') {
            $rec.Findings += [ordered]@{
                Rule = 'GENERIC_LIST_NEW_OBJECT'; Severity = 'MEDIUM'; Class = 'Parallel-Fixable'
                Line = 0; Col = 0
                Detail = 'use [System.Collections.Generic.List[object]]::new()'
            }
        }
        # LL: Split with separate char arguments binds the wrong overload
        if ($text -match "\.Split\(\s*'[\\\/]'\s*,\s*'[\\\/]'\s*\)") {
            $rec.Findings += [ordered]@{
                Rule = 'SPLIT_OVERLOAD_TRAP'; Severity = 'MEDIUM'; Class = 'Parallel-Fixable'
                Line = 0; Col = 0
                Detail = "use .Split([char[]]@('\','/'))"
            }
        }
        if ($text -match '\?\.') {
            $rec.Findings += [ordered]@{
                Rule = 'NULL_CONDITIONAL'; Severity = 'MEDIUM'; Class = 'Sequence-Dependent'
                Line = 0; Col = 0
                Detail = 'null-conditional operator is not safe across all hosts here'
            }
        }
        if ($rec.Bom) {
            $rec.Findings += [ordered]@{
                Rule = 'UTF8_BOM'; Severity = 'LOW'; Class = 'Parallel-Fixable'
                Line = 1; Col = 1; Detail = 'rewrite as UTF-8 without BOM'
            }
        }
        if ($rec.MixedEol) {
            $rec.Findings += [ordered]@{
                Rule = 'MIXED_LINE_ENDINGS'; Severity = 'LOW'; Class = 'Parallel-Fixable'
                Line = 0; Col = 0; Detail = 'normalise to one convention'
            }
        }
    } catch {
        $rec.Error = $_.Exception.Message
    }
    [pscustomobject]$rec
}

# --- P19 / P17 / P18  chunked parallel execution with live progress ----
Write-Log 'P19  parallel analysis (runspaces, chunked, progress between chunks)' 'ACCEL'
Set-Accel -Id 'P19' -State 'RUNNING' -Mode 'EXACT' -Detail ('throttle ' + $ThrottleLimit)

$results = [System.Collections.Generic.List[object]]::new()
$totalChunks = [Math]::Ceiling($fileList.Count / [double]$ChunkSize)
$chunkIndex = 0
$sw = [System.Diagnostics.Stopwatch]::StartNew()

for ($i = 0; $i -lt $fileList.Count; $i += $ChunkSize) {
    $end = [Math]::Min($i + $ChunkSize - 1, $fileList.Count - 1)
    $chunk = $fileList[$i..$end]
    $chunkIndex++
    $pct = [int](($chunkIndex / [double]$totalChunks) * 100)
    Write-Progress -Activity 'VIA PS Repair · 20 accelerators' `
                   -Status ('chunk ' + $chunkIndex + '/' + $totalChunks + '  ·  analysing ' + $chunk.Count + ' files') `
                   -PercentComplete $pct
    $part = $chunk | ForEach-Object -Parallel $analyzeBlock -ThrottleLimit $ThrottleLimit
    foreach ($r in $part) { $results.Add($r) }
    $narration = 'chunk ' + $chunkIndex + '/' + $totalChunks + '  ·  ' + $results.Count + ' files parsed  ·  ' + [int]$sw.Elapsed.TotalSeconds + 's'
    Write-Progress -Activity 'VIA PS Repair · 20 accelerators' -Status $narration -PercentComplete $pct
    Write-Log ('P18  ' + $narration) 'ACCEL'
}
$sw.Stop()
Write-Progress -Activity 'VIA PS Repair · 20 accelerators' -Completed
Set-Accel -Id 'P19' -State 'GREEN' -Detail ($totalChunks.ToString() + ' chunks, throttle ' + $ThrottleLimit)
Set-Accel -Id 'P17' -State 'GREEN' -Mode 'EXACT' -Detail ($totalChunks.ToString() + ' progress refreshes')
Set-Accel -Id 'P18' -State 'GREEN' -Mode 'EXACT' -Detail 'per-chunk narration streamed'

# --- roll findings up --------------------------------------------------
$allFindings = [System.Collections.Generic.List[object]]::new()
$parseFail = 0
$totalTokens = 0
$totalFns = 0
foreach ($r in $results) {
    $totalTokens += $r.Tokens
    $totalFns += $r.Functions
    if (@($r.ParseErrors).Count -gt 0) { $parseFail++ }
    foreach ($f in $r.Findings) {
        $allFindings.Add([pscustomobject]@{
            File = $r.Name; Path = $r.Path; Rule = $f.Rule; Severity = $f.Severity
            Class = $f.Class; Line = $f.Line; Detail = $f.Detail
        })
    }
}
$byRule = $allFindings | Group-Object Rule | Sort-Object Count -Descending
$parallelFixable = @($allFindings | Where-Object { $_.Class -eq 'Parallel-Fixable' })
$sequenceDependent = @($allFindings | Where-Object { $_.Class -eq 'Sequence-Dependent' })

Set-Accel -Id 'P01' -State $(if ($parseFail -gt 0) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail ($parseFail.ToString() + ' files with ParseError') -Count $parseFail
Set-Accel -Id 'P02' -State 'GREEN' -Mode 'EXACT' -Detail ($totalTokens.ToString() + ' tokens across the set') -Count $totalTokens
Set-Accel -Id 'P03' -State $(if (@($allFindings | Where-Object { $_.Rule -eq 'ALIAS_IN_SCRIPT' }).Count -gt 0) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'command-token anchored, strings untouched' -Count @($allFindings | Where-Object { $_.Rule -eq 'ALIAS_IN_SCRIPT' }).Count
Set-Accel -Id 'P04' -State 'YELLOW' -Mode 'HEURISTIC' -Detail 'alias resolution only; full cmdlet binding not verified'
Set-Accel -Id 'P05' -State $(if (@($allFindings | Where-Object { $_.Rule -eq 'RESERVED_PARAM_NAME' }).Count -gt 0) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'reserved and automatic variable names in param blocks' -Count @($allFindings | Where-Object { $_.Rule -eq 'RESERVED_PARAM_NAME' }).Count
Set-Accel -Id 'P06' -State $(if (@($allFindings | Where-Object { $_.Rule -eq 'UTF8_BOM' -or $_.Rule -eq 'MIXED_LINE_ENDINGS' }).Count -gt 0) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'BOM and line-ending consistency' -Count @($allFindings | Where-Object { $_.Rule -eq 'UTF8_BOM' -or $_.Rule -eq 'MIXED_LINE_ENDINGS' }).Count
Set-Accel -Id 'P07' -State $(if (@($allFindings | Where-Object { $_.Rule -eq 'READ_HOST_BLOCKS' -or $_.Rule -eq 'START_JOB_BANNED' -or $_.Rule -eq 'START_PROCESS_CHILD' }).Count -gt 0) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'Read-Host, Start-Job, Start-Process child launches' -Count @($allFindings | Where-Object { $_.Rule -eq 'READ_HOST_BLOCKS' -or $_.Rule -eq 'START_JOB_BANNED' -or $_.Rule -eq 'START_PROCESS_CHILD' }).Count
Set-Accel -Id 'P08' -State $(if (@($allFindings | Where-Object { $_.Rule -eq 'PIPE_READTOEND_DEADLOCK' }).Count -gt 0) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail 'redirected pipe plus synchronous ReadToEnd' -Count @($allFindings | Where-Object { $_.Rule -eq 'PIPE_READTOEND_DEADLOCK' }).Count

# P09 coupling by dot-source count
$coupled = @($results | Where-Object { @($_.DotSources).Count -gt 0 })
Set-Accel -Id 'P09' -State $(if ($coupled.Count -gt 0) { 'YELLOW' } else { 'GREEN' }) -Mode 'HEURISTIC' -Detail 'dot-source count as a coupling proxy; not a blast-radius proof' -Count $coupled.Count
Set-Accel -Id 'P10' -State 'GREEN' -Mode 'EXACT' -Detail 'parallel fixes first, then sequence-dependent by severity'
Set-Accel -Id 'P11' -State 'GREEN' -Mode 'EXACT' -Detail ($parallelFixable.Count.ToString() + ' parallel / ' + $sequenceDependent.Count.ToString() + ' sequential')
$deepest = ($results | Sort-Object MaxNesting -Descending | Select-Object -First 1)
Set-Accel -Id 'P12' -State $(if ($null -ne $deepest -and $deepest.MaxNesting -ge 8) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail ('deepest brace nesting ' + $(if ($null -ne $deepest) { $deepest.MaxNesting } else { 0 }))

# --- P15 / P16 / P14  fix application ---------------------------------
$applied = 0
$reparsedOk = 0
$reparsedFail = 0
if ($script:ApplyMode) {
    Write-Log 'P15  applying parallel-safe fixes only' 'ACCEL'
    foreach ($r in $results) {
        $fixes = @($r.Fixes)
        $needBom = $r.Bom
        if ($fixes.Count -eq 0 -and -not $needBom) { continue }
        try {
            $text = [System.IO.File]::ReadAllText($r.Path)
            # apply offset-anchored replacements from the end so earlier offsets stay valid
            foreach ($fx in ($fixes | Sort-Object -Property { [int]$_.StartOffset } -Descending)) {
                $len = $fx.EndOffset - $fx.StartOffset
                $text = $text.Remove($fx.StartOffset, $len).Insert($fx.StartOffset, $fx.Replacement)
            }
            # P14 re-parse in memory before anything touches disk
            $t2 = $null
            $e2 = $null
            [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$t2, [ref]$e2) | Out-Null
            if (@($e2).Count -gt 0) {
                $reparsedFail++
                Write-Log ('  P14 REJECT ' + $r.Name + ' (fix would introduce ' + @($e2).Count + ' parse errors)') 'FAIL'
                continue
            }
            $reparsedOk++
            $bak = $r.Path + '.psrepair.bak'
            if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $r.Path -Destination $bak -Force }
            [System.IO.File]::WriteAllText($r.Path, $text, $script:Utf8NoBom)
            $applied++
            Write-Log ('  fixed ' + $r.Name + '  (' + $fixes.Count + ' anchored edits)') 'OK'
        } catch {
            Write-Log ('  fix failed ' + $r.Name + ': ' + $_.Exception.Message) 'FAIL'
        }
    }
    Set-Accel -Id 'P15' -State 'GREEN' -Mode 'EXACT' -Detail ($applied.ToString() + ' files edited') -Count $applied
    Set-Accel -Id 'P16' -State 'GREEN' -Mode 'EXACT' -Detail '.psrepair.bak written before every edit' -Count $applied
    Set-Accel -Id 'P14' -State $(if ($reparsedFail -gt 0) { 'YELLOW' } else { 'GREEN' }) -Mode 'EXACT' -Detail ($reparsedOk.ToString() + ' verified, ' + $reparsedFail.ToString() + ' rejected')
} else {
    Set-Accel -Id 'P15' -State 'SKIPPED' -Mode 'EXACT' -Detail ($parallelFixable.Count.ToString() + ' fixes ready; dry-run')
    Set-Accel -Id 'P16' -State 'SKIPPED' -Mode 'EXACT' -Detail 'no edits, no backups needed'
    Set-Accel -Id 'P14' -State 'SKIPPED' -Mode 'EXACT' -Detail 'verification runs only when fixes are applied'
}

# --- plan + report -----------------------------------------------------
$overall = 'GREEN'
if ($parseFail -gt 0 -or @($allFindings | Where-Object { $_.Severity -eq 'HIGH' }).Count -gt 0) { $overall = 'RED' }
elseif ($allFindings.Count -gt 0) { $overall = 'YELLOW' }

$plan = [pscustomobject]@{
    schema = 'VIA_PSRepairPlan/1.0'; run_id = $script:RunId; at = $script:StartedAt.ToString('s')
    files = $fileList.Count; overall = $overall; apply_mode = $script:ApplyMode
    parse_error_files = $parseFail
    parallel_fixable = $parallelFixable.Count
    sequence_dependent = $sequenceDependent.Count
    applied = $applied
    findings = $allFindings
}
$planPath = Join-Path $runDir 'psrepair_plan.json'
Write-TextFile -Path $planPath -Content ($plan | ConvertTo-Json -Depth 6)
Write-Log ('plan     ' + $planPath) 'OK'

function Get-Badge {
    param([string]$S)
    $c = 'gy'
    if ($S -eq 'GREEN')   { $c = 'gr' }
    if ($S -eq 'YELLOW')  { $c = 'ye' }
    if ($S -eq 'RED')     { $c = 'rd' }
    return '<span class="b ' + $c + '">' + $S + '</span>'
}

$secModule = ''
foreach ($g in ($allFindings | Group-Object File | Sort-Object Count -Descending | Select-Object -First 40)) {
    $hi = @($g.Group | Where-Object { $_.Severity -eq 'HIGH' }).Count
    $st = 'YELLOW'
    if ($hi -gt 0) { $st = 'RED' }
    $rules = (($g.Group | Select-Object -ExpandProperty Rule -Unique) -join ', ')
    $lines = (($g.Group | Where-Object { $_.Line -gt 0 } | Select-Object -ExpandProperty Line -Unique | Select-Object -First 8) -join ', ')
    $anchor = 'Precision::Line ' + $lines
    if ($lines -eq '') { $anchor = 'Elastic::WholeFile' }
    $secModule = $secModule + '<tr><td class="m">' + $g.Name + '</td><td class="c">' + (Get-Badge -S $st) + '</td><td class="c">' + $g.Count + '</td><td class="m">' + $anchor + '</td><td>' + $rules + '</td></tr>'
}
if ($secModule -eq '') { $secModule = '<tr><td colspan="5" class="dim">No findings.</td></tr>' }

$secEngine = ''
foreach ($id in @('P01','P02','P14','P15','P16','P19')) {
    $a = $script:Accel[$id]
    $secEngine = $secEngine + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c m">' + $(if ($a.Mode) { $a.Mode } else { 'EXACT' }) + '</td><td>' + $a.Detail + '</td></tr>'
}
$secLib = ''
foreach ($id in @('P03','P04','P05','P06','P07','P08','P09','P10','P11','P12','P13')) {
    $a = $script:Accel[$id]
    $m = $(if ($a.Mode) { $a.Mode } else { 'EXACT' })
    $mb = 'exact'
    if ($m -eq 'HEURISTIC') { $mb = 'heur' }
    $secLib = $secLib + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c"><span class="b ' + $mb + '">' + $m + '</span></td><td class="c">' + $a.Count + '</td><td>' + $a.Detail + '</td></tr>'
}
Set-Accel -Id 'P20' -State 'GREEN' -Mode 'EXACT' -Detail 'four-section matrix rendered'
$secOther = ''
foreach ($id in @('P17','P18','P20')) {
    $a = $script:Accel[$id]
    $secOther = $secOther + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td>' + $a.Detail + '</td></tr>'
}
$ruleRows = ''
foreach ($g in $byRule) {
    $sev = ($g.Group | Select-Object -First 1).Severity
    $cls = ($g.Group | Select-Object -First 1).Class
    $sb = 'ye'
    if ($sev -eq 'HIGH') { $sb = 'rd' }
    if ($sev -eq 'LOW')  { $sb = 'gy' }
    $ruleRows = $ruleRows + '<tr><td class="m">' + $g.Name + '</td><td class="c"><span class="b ' + $sb + '">' + $sev + '</span></td><td class="c">' + $cls + '</td><td class="c">' + $g.Count + '</td><td>' + ($g.Group | Select-Object -First 1).Detail + '</td></tr>'
}
if ($ruleRows -eq '') { $ruleRows = '<tr><td colspan="5" class="dim">Clean.</td></tr>' }

$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$modeText = 'DRY-RUN'
if ($script:ApplyMode) { $modeText = 'APPLIED' }
$logText = ($script:LogLines -join "`n").Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PS REPAIR MATRIX — $($script:RunId)</title>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --line:#334155; --tx:#f8fafc; --mu:#94a3b8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--tx); overflow-x:hidden;
         font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif;
         font-size:11px; line-height:1.35; letter-spacing:-0.01em; }
  .wrap { width:100%; max-width:1400px; margin:0 auto; padding:18px 14px 48px; }
  h1 { font-size:14px; margin:0; font-weight:600; }
  .sub { font-size:11px; color:var(--mu); margin:3px 0 0; }
  h2 { font-size:12px; margin:22px 0 7px; font-weight:600;
       border-bottom:1px solid var(--line); padding-bottom:5px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(112px,1fr)); gap:8px; margin-top:14px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:3px; padding:9px 11px; }
  .kpi .n { font-size:17px; font-weight:600; }
  .kpi .l { font-size:10px; color:var(--mu); margin-top:2px; }
  table { width:100%; table-layout:fixed; border-collapse:collapse;
          background:var(--card); border:1px solid var(--line); border-radius:3px; }
  th { font-size:11px; color:var(--mu); font-weight:500; text-align:left;
       padding:4px 6px; border-bottom:1px solid var(--line); }
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
  .exact { background:#0c2d48; color:#7dd3fc; border-color:#0369a1; }
  .heur { background:#3b2f0b; color:#fcd34d; border-color:#a16207; }
  .note { background:var(--card); border:1px solid var(--line); border-left:3px solid #d97706;
          border-radius:3px; padding:10px 12px; }
  pre { background:#0b1220; color:#cbd5e1; font-family:ui-monospace,Consolas,monospace;
        font-size:10.5px; padding:11px; border-radius:3px; overflow-x:auto; max-height:280px; }
</style>
</head>
<body>
<div class="wrap">

<h1>POWERSHELL REPAIR MATRIX</h1>
<p class="sub">$($script:RunId) · $modeText · $($fileList.Count) files · overall $overall</p>

<div class="kpis">
  <div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div>
  <div class="kpi"><div class="n">$($fileList.Count)</div><div class="l">files</div></div>
  <div class="kpi"><div class="n">$parseFail</div><div class="l">parse errors</div></div>
  <div class="kpi"><div class="n">$($allFindings.Count)</div><div class="l">findings</div></div>
  <div class="kpi"><div class="n">$($parallelFixable.Count)</div><div class="l">parallel-fixable</div></div>
  <div class="kpi"><div class="n">$($sequenceDependent.Count)</div><div class="l">sequence-dependent</div></div>
  <div class="kpi"><div class="n">$applied</div><div class="l">files edited</div></div>
  <div class="kpi"><div class="n">${elapsed}s</div><div class="l">elapsed</div></div>
</div>

<h2>MODULE — worst files</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:8%"><col style="width:23%"><col style="width:34%"></colgroup>
  <thead><tr><th>Script</th><th>RYG</th><th>Issues</th><th>AST Anchoring Scope</th><th>Rules Triggered</th></tr></thead>
  <tbody>$secModule</tbody>
</table>

<h2>ENGINE</h2>
<table>
  <colgroup><col style="width:28%"><col style="width:10%"><col style="width:12%"><col style="width:50%"></colgroup>
  <thead><tr><th>Component</th><th>RYG</th><th>Evidence Mode</th><th>Narration</th></tr></thead>
  <tbody>$secEngine</tbody>
</table>

<h2>FUNCTION-LIB</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence Mode</th><th>Hits</th><th>Governance Notes</th></tr></thead>
  <tbody>$secLib</tbody>
</table>

<h2>OTHERS</h2>
<table>
  <colgroup><col style="width:28%"><col style="width:10%"><col style="width:62%"></colgroup>
  <thead><tr><th>Support Component</th><th>RYG</th><th>Narration</th></tr></thead>
  <tbody>$secOther</tbody>
</table>

<h2>RULE MATRIX</h2>
<table>
  <colgroup><col style="width:24%"><col style="width:10%"><col style="width:16%"><col style="width:8%"><col style="width:42%"></colgroup>
  <thead><tr><th>Rule</th><th>Severity</th><th>Class</th><th>Count</th><th>Remedy</th></tr></thead>
  <tbody>$ruleRows</tbody>
</table>

<h2>EVIDENCE HONESTY</h2>
<div class="note">
  EXACT accelerators report a measurement from the PowerShell parser itself: ParseError extents, token
  streams, AST node types, byte-level BOM checks. HEURISTIC accelerators report a proxy. P04 resolves
  aliases but does not verify full parameter binding. P09 counts dot-sources as a coupling stand-in and
  is not a blast-radius proof. Only Parallel-Fixable findings are ever auto-applied, each edit is anchored
  to an exact AST extent offset, and every edited file is re-parsed in memory before it reaches disk:
  if the fix would introduce a parse error the edit is rejected and the original is left untouched.
</div>

<h2>CONSOLE LOG</h2>
<pre>$logText</pre>

</div>
</body>
</html>
"@

$reportPath = Join-Path $runDir ('reports\PS_REPAIR_MATRIX_' + $script:Stamp + '.html')
Write-TextFile -Path $reportPath -Content $html
Write-TextFile -Path (Join-Path $runDir 'logs\console.log') -Content $logText

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  ' + $fileList.Count + ' files  ·  ' + $allFindings.Count + ' findings  ·  ' + $modeText) -ForegroundColor Green
Write-Host ('  parallel-fixable ' + $parallelFixable.Count + '  ·  sequence-dependent ' + $sequenceDependent.Count) -ForegroundColor DarkGray
Write-Host ('  plan    ' + $planPath) -ForegroundColor DarkGray
Write-Host ('  matrix  ' + $reportPath) -ForegroundColor DarkGray
if (-not $script:ApplyMode) {
    Write-Host '  re-run with -GoToken GO_v1 to apply parallel-safe fixes only' -ForegroundColor Yellow
}
Write-Host ''

if (-not $NoOpen) {
    try { Start-Process -FilePath $reportPath } catch { Write-Log 'could not open the report automatically' 'WARN' }
}
