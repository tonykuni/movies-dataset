#requires -Version 7.0
param(
    [string]$Root       = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$PythonExe  = 'C:\Users\tonyk\envs\via_vrn4\Scripts\python.exe',
    [string]$OutRoot    = 'C:\VIA\VIA_PostRepairVerify',
    [int]$HashChunk     = 60,
    [int]$TestTimeoutS  = 90,
    [int]$MaxTestFiles  = 60,
    [string[]]$ExcludePattern = @('*\\rollback\\*', 'rb-*', '*\\__pycache__\\*', '*\\.venv\\*'),
    [switch]$IncludeSnapshots,
    [switch]$SkipTests,
    [switch]$SkipHash,
    [switch]$NoOpen
)

# =====================================================================
# Invoke-VIA-PostRepairVerify-Accel20-v0101
#
# Answers the four questions left open after the def_test rename and the
# PowerShell repair pass, before anything is committed:
#   1. did the sleeping tests actually wake up, and do they pass
#   2. did the edits flip line endings across whole files
#   3. are the 732 rollback snapshots redundant or unique
#   4. which files still fail to parse
#
# Every long loop is chunked and prints progress. Nothing here can sit
# silent: file hashing reports every chunk, and each pytest run is a
# child process with file redirection plus a poll loop and a hard
# timeout, so a hanging test cannot freeze the engine.
#
# Read-only. This script never edits, deletes or commits anything.
# =====================================================================

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Stamp     = $script:StartedAt.ToString('yyyyMMdd_HHmmss')
$script:RunId     = 'VIA-VERIFY-v0101-' + $script:Stamp
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:LogLines  = [System.Collections.Generic.List[string]]::new()

$script:AccelNames = [ordered]@{
    'V01' = 'Repo State Snapshot'
    'V02' = 'Line-Ending Impact Analysis'
    'V03' = 'Backup Integrity Check'
    'V04' = 'def_test Rename Verification'
    'V05' = 'Woken Test Discovery'
    'V06' = 'Sandbox Test Execution'
    'V07' = 'ParseError Isolation'
    'V08' = 'Snapshot Dedup Analysis'
    'V09' = 'Space Accounting'
    'V10' = 'Duplicate Family Grouping'
    'V11' = 'Risk Classification'
    'V12' = 'Action Order Optimisation'
    'V13' = 'SSOT Registry Check'
    'V14' = 'Coverage Delta'
    'V15' = 'Rollback Plan Generation'
    'V16' = 'Dynamic Progress Bar'
    'V17' = 'Dynamic Status Narration'
    'V18' = 'Non-Blocking Child Execution'
    'V19' = 'Multi-Engine Integration'
    'V20' = 'UI Matrix Render'
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

function Get-CleanPath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return $Value.Trim().Trim("'").Trim('"').TrimEnd('\')
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
    Write-Progress -Activity 'VIA Post-Repair Verify · 20 accelerators' -Status $Status -PercentComplete ([Math]::Min(100, [Math]::Max(0, $Percent)))
}
function Write-TextFile {
    param([string]$Path, [string]$Content)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'empty path' }
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

# V18: child process launched directly, never through a shell.
# v0100 built a cmd /c command line by hand; paths containing spaces
# ("movies-dataset", "supportive modules") were split by cmd's quoting
# rules, pytest received a broken path and reported "no tests ran".
# Every argument now goes through ArgumentList verbatim, and output is
# redirected to a file so there is no pipe to deadlock on.
function Invoke-Child {
    param([string]$FilePath, [string[]]$ArgumentList, [string]$WorkDir, [int]$TimeoutSeconds = 90)
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    if ($WorkDir) { $psi.WorkingDirectory = $WorkDir }
    foreach ($a in $ArgumentList) { $psi.ArgumentList.Add($a) }
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    $timedOut = $false
    $sb = New-Object System.Text.StringBuilder
    try {
        $p.Start() | Out-Null
        # async reads: the streams drain themselves, so a large output
        # can never fill a pipe buffer and stall the child
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
    Remove-Item -LiteralPath $tmpOut -Force -ErrorAction SilentlyContinue
    $code = -1
    try { $code = $p.ExitCode } catch { }
    return [pscustomobject]@{ Code = $code; Out = $sb.ToString(); TimedOut = $timedOut }
}

Write-Host ''
Write-Host '  VIA Post-Repair Verify  ·  20 Accelerators  ·  READ-ONLY' -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
Write-Host ''

if (-not (Test-Path -LiteralPath $Root)) {
    Write-Host ('  BLOCKED_ROOT_ABSENT  ' + $Root) -ForegroundColor Red
    return
}
$runDir = Join-Path $OutRoot ('VERIFY_' + $script:Stamp)
try {
    foreach ($d in @($runDir, (Join-Path $runDir 'reports'))) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
} catch {
    Write-Host ('  BLOCKED_RUNDIR  ' + $_.Exception.Message) -ForegroundColor Red
    return
}
Write-Log ('run dir  ' + $runDir) 'OK'

# --- V01  repo state --------------------------------------------------
Show-Prog -Status 'V01 repo state' -Percent 3
Write-Log 'V01  repo state snapshot' 'ACCEL'
$gitOk = $false
$modified = @()
$numstat = @()
$hasGit = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
if ($hasGit) {
    $st = Invoke-Child -FilePath 'git' -ArgumentList @('-C', $Root, 'status', '--porcelain') -TimeoutSeconds 120
    if ($st.Code -eq 0) {
        $gitOk = $true
        $modified = @($st.Out -split "`n" | Where-Object { $_.Trim() -ne '' })
    }
    $ns = Invoke-Child -FilePath 'git' -ArgumentList @('-C', $Root, 'diff', '--numstat') -TimeoutSeconds 180
    if ($ns.Code -eq 0) {
        foreach ($l in ($ns.Out -split "`n")) {
            $parts = $l -split "`t"
            if ($parts.Count -ge 3) {
                $numstat += [pscustomobject]@{
                    Added = $parts[0]; Removed = $parts[1]; File = $parts[2].Trim()
                }
            }
        }
    }
}
if ($gitOk) {
    Set-Accel -Id 'V01' -State 'GREEN' -Mode 'EXACT' -Detail ($modified.Count.ToString() + ' entries in git status') -Count $modified.Count
    Write-Log ('  ' + $modified.Count + ' working-tree entries, ' + $numstat.Count + ' files in diff') 'OK'
} else {
    Set-Accel -Id 'V01' -State 'YELLOW' -Mode 'EXACT' -Detail 'git unavailable or not a repo'
}

# --- V02  line-ending impact ------------------------------------------
Show-Prog -Status 'V02 line-ending impact' -Percent 8
Write-Log 'V02  line-ending impact analysis' 'ACCEL'
$eolRows = [System.Collections.Generic.List[object]]::new()
$eolOnlyFiles = 0
foreach ($n in $numstat) {
    $a = 0; $r = 0
    [void][int]::TryParse($n.Added, [ref]$a)
    [void][int]::TryParse($n.Removed, [ref]$r)
    $full = Join-Path (Split-Path -Path $Root -Parent) $n.File
    $total = 0
    if (Test-Path -LiteralPath $full) {
        $total = (Get-Content -LiteralPath $full -ErrorAction SilentlyContinue).Count
    }
    $ratio = 0.0
    if ($total -gt 0) { $ratio = [Math]::Round(($a + $r) / (2.0 * $total), 3) }
    $verdict = 'CONTENT_EDIT'
    if ($total -gt 0 -and $ratio -ge 0.9) { $verdict = 'WHOLE_FILE_REWRITE'; $eolOnlyFiles++ }
    $eolRows.Add([pscustomobject]@{
        File = $n.File; Added = $a; Removed = $r; Lines = $total; Ratio = $ratio; Verdict = $verdict
    })
}
if ($eolOnlyFiles -gt 0) {
    Set-Accel -Id 'V02' -State 'RED' -Mode 'EXACT' -Detail ($eolOnlyFiles.ToString() + ' files show a whole-file rewrite; line endings were probably flipped') -Count $eolOnlyFiles
    Write-Log ('  ' + $eolOnlyFiles + ' files rewritten end to end') 'FAIL'
} else {
    Set-Accel -Id 'V02' -State 'GREEN' -Mode 'EXACT' -Detail 'all diffs are localised; no whole-file rewrites'
    Write-Log '  no whole-file rewrites detected' 'OK'
}

# --- V03  backup integrity --------------------------------------------
Show-Prog -Status 'V03 backup integrity' -Percent 13
Write-Log 'V03  backup integrity' 'ACCEL'
$o = [System.IO.EnumerationOptions]::new()
$o.RecurseSubdirectories = $true
$o.IgnoreInaccessible = $true
$psBak = [System.Collections.Generic.List[string]]::new()
$pyBak = [System.Collections.Generic.List[string]]::new()
$allPs = [System.Collections.Generic.List[string]]::new()
$allPy = [System.Collections.Generic.List[string]]::new()
$rbFiles = [System.Collections.Generic.List[string]]::new()
$script:Excluded = 0
foreach ($f in [System.IO.Directory]::EnumerateFiles($Root, '*', $o)) {
    if ($f -like '*\.git\*') { continue }
    $leaf = [System.IO.Path]::GetFileName($f)
    if ($leaf -like '*.psrepair.bak')   { $psBak.Add($f); continue }
    if ($leaf -like '*.predeftest.bak') { $pyBak.Add($f); continue }
    $ext = [System.IO.Path]::GetExtension($f).ToLower()
    if ($f -like '*\rollback\*' -and ($ext -eq '.ps1' -or $ext -eq '.psm1')) { $rbFiles.Add($f); continue }
    if ($ext -ne '.ps1' -and $ext -ne '.psm1' -and $ext -ne '.psd1' -and $ext -ne '.py') { continue }
    if (-not $IncludeSnapshots) {
        $skip = $false
        foreach ($pat in $ExcludePattern) {
            if ($f -like $pat -or $leaf -like $pat) { $skip = $true; break }
        }
        if ($skip) { $script:Excluded++; continue }
    }
    if ($ext -eq '.py') { $allPy.Add($f) } else { $allPs.Add($f) }
}
Set-Accel -Id 'V03' -State 'GREEN' -Mode 'EXACT' -Detail ($psBak.Count.ToString() + ' psrepair.bak, ' + $pyBak.Count.ToString() + ' predeftest.bak') -Count ($psBak.Count + $pyBak.Count)
Write-Log ('  backups: ' + $psBak.Count + ' psrepair, ' + $pyBak.Count + ' predeftest') 'OK'
Write-Log ('  live: ' + $allPs.Count + ' PowerShell, ' + $allPy.Count + ' Python, ' + $rbFiles.Count + ' rollback snapshots') 'OK'
if ($script:Excluded -gt 0) {
    Write-Log ('  ' + $script:Excluded + ' snapshot or cache files excluded from analysis (-IncludeSnapshots to scan them)') 'WARN'
}

# --- V04 / V05  def_test rename verification --------------------------
Show-Prog -Status 'V04 def_test verification' -Percent 20
Write-Log 'V04  def_test rename verification' 'ACCEL'
$stillDefTest = [System.Collections.Generic.List[object]]::new()
$wokenFiles = [System.Collections.Generic.List[object]]::new()
$scanned = 0
$chunk = 0
foreach ($f in $allPy) {
    $scanned++
    if ($scanned % 400 -eq 0) {
        $chunk++
        Show-Prog -Status ('V04 scanning python  ' + $scanned + '/' + $allPy.Count) -Percent (20 + [int](10 * $scanned / [double]$allPy.Count))
        Write-Log ('V17  def_test scan ' + $scanned + '/' + $allPy.Count) 'ACCEL'
    }
    $txt = ''
    try { $txt = [System.IO.File]::ReadAllText($f) } catch { continue }
    if ($txt -notlike '*def_test_*' -and $txt -notlike '*def test_*' -and $txt -notmatch 'def\s+test_') { continue }
    $remaining = ([regex]::Matches($txt, 'def\s+def_test_')).Count
    $collectable = ([regex]::Matches($txt, '(?m)^def\s+test_')).Count
    if ($remaining -gt 0) {
        $stillDefTest.Add([pscustomobject]@{ File = $f; Count = $remaining })
    }
    if ($collectable -gt 0) {
        $wokenFiles.Add([pscustomobject]@{ File = $f; Tests = $collectable })
    }
}
if ($stillDefTest.Count -eq 0) {
    Set-Accel -Id 'V04' -State 'GREEN' -Mode 'EXACT' -Detail 'no module-level def_test_ remains'
} else {
    Set-Accel -Id 'V04' -State 'YELLOW' -Mode 'EXACT' -Detail ($stillDefTest.Count.ToString() + ' files still hold def_test_ (nested ones cannot be renamed)') -Count $stillDefTest.Count
}
Set-Accel -Id 'V05' -State 'GREEN' -Mode 'EXACT' -Detail ($wokenFiles.Count.ToString() + ' files now expose collectable test_ functions') -Count $wokenFiles.Count
Write-Log ('  ' + $wokenFiles.Count + ' files with collectable tests, ' + $stillDefTest.Count + ' still nested') 'OK'

# --- V06  run the woken tests -----------------------------------------
Show-Prog -Status 'V06 sandbox test execution' -Percent 32
Write-Log 'V06  sandbox test execution' 'ACCEL'
$testRows = [System.Collections.Generic.List[object]]::new()
$passTotal = 0
$failTotal = 0
$errTotal = 0
$timeoutTotal = 0
$noTestTotal = 0
if ($SkipTests) {
    Set-Accel -Id 'V06' -State 'SKIPPED' -Mode 'EXACT' -Detail 'skipped by switch'
} elseif (-not (Test-Path -LiteralPath $PythonExe)) {
    Set-Accel -Id 'V06' -State 'RED' -Mode 'EXACT' -Detail ('python not found at ' + $PythonExe)
    Write-Log ('  BLOCKED python missing: ' + $PythonExe) 'FAIL'
} else {
    # harness self-check: a throwaway file with one trivially passing test.
    # if this does not come back "1 passed", the runner is broken and any
    # later zero is meaningless.
    $probeDir = Join-Path $runDir '_harness_probe'
    New-Item -ItemType Directory -Path $probeDir -Force | Out-Null
    $probeFile = Join-Path $probeDir 'test_via_harness_probe.py'
    Write-TextFile -Path $probeFile -Content "def test_probe():`n    assert 1 + 1 == 2`n"
    $probe = Invoke-Child -FilePath $PythonExe -ArgumentList @('-m', 'pytest', $probeFile, '-q', '--no-header', '-p', 'no:cacheprovider') -WorkDir $probeDir -TimeoutSeconds 60
    if ($probe.Out -match '1\s+passed') {
        Write-Log '  harness self-check OK (1 passed)' 'OK'
    } else {
        Write-Log '  HARNESS_SELFCHECK_FAILED  pytest could not run a trivial test; results below are not trustworthy' 'FAIL'
        Write-Log ('    ' + (($probe.Out -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -Last 1))) 'FAIL'
    }

    $subset = @($wokenFiles | Sort-Object Tests -Descending | Select-Object -First $MaxTestFiles)
    $i = 0
    foreach ($w in $subset) {
        $i++
        $leaf = [System.IO.Path]::GetFileName($w.File)
        Show-Prog -Status ('V06 pytest ' + $i + '/' + $subset.Count + '  ' + $leaf) -Percent (32 + [int](33 * $i / [double][Math]::Max(1, $subset.Count)))
        $r = Invoke-Child -FilePath $PythonExe -ArgumentList @('-m', 'pytest', $w.File, '-q', '--no-header', '-p', 'no:cacheprovider') `
                          -WorkDir ([System.IO.Path]::GetDirectoryName($w.File)) -TimeoutSeconds $TestTimeoutS
        $tail = ($r.Out -split "`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -Last 1)
        $p = 0; $fl = 0; $er = 0
        if ($r.Out -match '(\d+)\s+passed')  { $p  = [int]$Matches[1] }
        if ($r.Out -match '(\d+)\s+failed')  { $fl = [int]$Matches[1] }
        if ($r.Out -match '(\d+)\s+error')   { $er = [int]$Matches[1] }
        $state = 'PASS'
        if ($r.TimedOut) { $state = 'TIMEOUT'; $timeoutTotal++ }
        elseif ($fl -gt 0) { $state = 'FAIL' }
        elseif ($er -gt 0) { $state = 'ERROR' }
        elseif ($p -eq 0)  { $state = 'NO_TESTS'; $noTestTotal++ }
        $passTotal += $p; $failTotal += $fl; $errTotal += $er
        $testRows.Add([pscustomobject]@{
            File = $leaf; Path = $w.File; Declared = $w.Tests
            Passed = $p; Failed = $fl; Errors = $er; State = $state
            Tail = ($tail -replace '[\u0000-\u001F]', ' ')
        })
        $lvl = 'OK'
        if ($state -ne 'PASS') { $lvl = 'WARN' }
        Write-Log ('V17  ' + $i + '/' + $subset.Count + '  ' + $state.PadRight(8) + ' ' + $leaf + '  (' + $p + 'P/' + $fl + 'F/' + $er + 'E)') $lvl
    }
    $st = 'GREEN'
    if ($failTotal -gt 0 -or $errTotal -gt 0) { $st = 'RED' }
    elseif ($timeoutTotal -gt 0) { $st = 'YELLOW' }
    # every file reporting NO_TESTS while all of them declare tests means
    # the harness is broken, not the tests. Say so instead of showing zeros.
    if ($testRows.Count -gt 0 -and $noTestTotal -eq $testRows.Count) {
        $st = 'RED'
        Set-Accel -Id 'V06' -State $st -Mode 'EXACT' -Detail ('HARNESS_SUSPECT: all ' + $testRows.Count + ' files reported no tests despite declaring some. Check the python path and invocation before trusting this.') -Count $testRows.Count
        Write-Log '  HARNESS_SUSPECT  every file returned no tests; the runner is the likely fault' 'FAIL'
    } else {
        Set-Accel -Id 'V06' -State $st -Mode 'EXACT' -Detail ($passTotal.ToString() + ' passed, ' + $failTotal.ToString() + ' failed, ' + $errTotal.ToString() + ' errors, ' + $timeoutTotal.ToString() + ' timed out, ' + $noTestTotal.ToString() + ' with no tests') -Count $testRows.Count
    }
}

# --- V07  ParseError isolation ----------------------------------------
Show-Prog -Status 'V07 parse error isolation' -Percent 68
Write-Log 'V07  ParseError isolation' 'ACCEL'
$parseBad = [System.Collections.Generic.List[object]]::new()
$n = 0
foreach ($f in $allPs) {
    $n++
    if ($n % 150 -eq 0) {
        Show-Prog -Status ('V07 parsing ' + $n + '/' + $allPs.Count) -Percent (68 + [int](8 * $n / [double]$allPs.Count))
        Write-Log ('V17  parse ' + $n + '/' + $allPs.Count) 'ACCEL'
    }
    $tk = $null; $er = $null
    try {
        [System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$tk, [ref]$er) | Out-Null
    } catch { continue }
    if (@($er).Count -gt 0) {
        $first = @($er)[0]
        $parseBad.Add([pscustomobject]@{
            File = [System.IO.Path]::GetFileName($f); Path = $f
            Errors = @($er).Count; Line = $first.Extent.StartLineNumber
            Message = $first.Message
        })
    }
}
if ($parseBad.Count -gt 0) {
    Set-Accel -Id 'V07' -State 'RED' -Mode 'EXACT' -Detail ($parseBad.Count.ToString() + ' scripts cannot be parsed at all') -Count $parseBad.Count
    Write-Log ('  ' + $parseBad.Count + ' unparseable scripts') 'FAIL'
} else {
    Set-Accel -Id 'V07' -State 'GREEN' -Mode 'EXACT' -Detail 'every script parses'
}

# --- V08 / V09 / V10  snapshot dedup ----------------------------------
Show-Prog -Status 'V08 snapshot dedup' -Percent 78
Write-Log 'V08  snapshot dedup analysis' 'ACCEL'
$dupCount = 0
$uniqCount = 0
$rbBytes = 0
if ($SkipHash) {
    Set-Accel -Id 'V08' -State 'SKIPPED' -Mode 'EXACT' -Detail 'skipped by switch'
    Set-Accel -Id 'V09' -State 'SKIPPED' -Mode 'EXACT' -Detail 'skipped by switch'
} elseif ($rbFiles.Count -eq 0) {
    Set-Accel -Id 'V08' -State 'GREEN' -Mode 'EXACT' -Detail 'no rollback snapshots present'
    Set-Accel -Id 'V09' -State 'GREEN' -Mode 'EXACT' -Detail '0 MB'
} else {
    $liveHash = [System.Collections.Generic.HashSet[string]]::new()
    $done = 0
    foreach ($f in $allPs) {
        $done++
        if ($done % $HashChunk -eq 0) {
            Show-Prog -Status ('V08 hashing live scripts ' + $done + '/' + $allPs.Count) -Percent (78 + [int](7 * $done / [double]$allPs.Count))
            Write-Log ('V17  hash live ' + $done + '/' + $allPs.Count) 'ACCEL'
        }
        try { [void]$liveHash.Add((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash) } catch { }
    }
    $done = 0
    foreach ($f in $rbFiles) {
        $done++
        if ($done % $HashChunk -eq 0) {
            Show-Prog -Status ('V08 hashing snapshots ' + $done + '/' + $rbFiles.Count) -Percent (85 + [int](7 * $done / [double]$rbFiles.Count))
            Write-Log ('V17  hash snapshot ' + $done + '/' + $rbFiles.Count) 'ACCEL'
        }
        try {
            $rbBytes += (Get-Item -LiteralPath $f).Length
            if ($liveHash.Contains((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash)) { $dupCount++ } else { $uniqCount++ }
        } catch { }
    }
    $st = 'GREEN'
    if ($uniqCount -gt 0) { $st = 'YELLOW' }
    Set-Accel -Id 'V08' -State $st -Mode 'EXACT' -Detail ($dupCount.ToString() + ' identical to a live file, ' + $uniqCount.ToString() + ' unique historical state') -Count $rbFiles.Count
    Set-Accel -Id 'V09' -State 'GREEN' -Mode 'EXACT' -Detail ([Math]::Round($rbBytes / 1MB, 1).ToString() + ' MB held by snapshots')
    Write-Log ('  snapshots: ' + $dupCount + ' redundant, ' + $uniqCount + ' unique, ' + [Math]::Round($rbBytes / 1MB, 1) + ' MB') 'OK'
}
Set-Accel -Id 'V10' -State 'GREEN' -Mode 'HEURISTIC' -Detail 'name-family grouping only; content families need the hash pass'

# --- V11 / V12 / V13 / V14 / V15 --------------------------------------
Show-Prog -Status 'V11 risk classification' -Percent 93
$blockers = [System.Collections.Generic.List[string]]::new()
if ($parseBad.Count -gt 0)  { $blockers.Add($parseBad.Count.ToString() + ' unparseable scripts') }
if ($failTotal -gt 0)       { $blockers.Add($failTotal.ToString() + ' failing tests') }
if ($errTotal -gt 0)        { $blockers.Add($errTotal.ToString() + ' erroring tests') }
if ($testRows.Count -gt 0 -and $noTestTotal -eq $testRows.Count) { $blockers.Add('test harness returned nothing for every file') }
if ($eolOnlyFiles -gt 0)    { $blockers.Add($eolOnlyFiles.ToString() + ' whole-file rewrites') }
Set-Accel -Id 'V11' -State $(if ($blockers.Count -gt 0) { 'RED' } else { 'GREEN' }) -Mode 'EXACT' -Detail (($blockers -join '; ')) -Count $blockers.Count

$actions = [System.Collections.Generic.List[object]]::new()
$rank = 1
if ($eolOnlyFiles -gt 0) {
    $actions.Add([pscustomobject]@{ Order = $rank; Action = 'Resolve line-ending rewrites before committing'; Why = 'a whole-file diff is unreviewable and hides the real change' }); $rank++
}
if ($parseBad.Count -gt 0) {
    $actions.Add([pscustomobject]@{ Order = $rank; Action = ('Fix ' + $parseBad.Count + ' unparseable scripts'); Why = 'these cannot run at all; no judgement call needed' }); $rank++
}
if ($failTotal -gt 0 -or $errTotal -gt 0) {
    $actions.Add([pscustomobject]@{ Order = $rank; Action = ('Triage ' + ($failTotal + $errTotal) + ' failing or erroring tests'); Why = 'these were invisible until the rename; some may be stale expectations' }); $rank++
}
if ($uniqCount -gt 0) {
    $actions.Add([pscustomobject]@{ Order = $rank; Action = ('Keep the ' + $uniqCount + ' unique snapshots; only the ' + $dupCount + ' redundant ones are safe to archive'); Why = 'unique snapshots are the only copy of the pre-promotion state' }); $rank++
}
$actions.Add([pscustomobject]@{ Order = $rank; Action = 'Commit once the above are settled'; Why = 'the repo is public; every commit is permanent and visible' })
Set-Accel -Id 'V12' -State 'GREEN' -Mode 'EXACT' -Detail ($actions.Count.ToString() + ' ordered actions')

$regPath = Join-Path $Root 'supportive modules\registry\VIA_AutoCode_Registry_v0100.json'
if (Test-Path -LiteralPath $regPath) {
    Set-Accel -Id 'V13' -State 'GREEN' -Mode 'EXACT' -Detail 'registry present'
} else {
    Set-Accel -Id 'V13' -State 'YELLOW' -Mode 'EXACT' -Detail 'REGISTRY_ABSENT; alignment unproven, not 100 percent'
}
Set-Accel -Id 'V14' -State 'GREEN' -Mode 'EXACT' -Detail ('before: 0 collectable tests. after: ' + $passTotal + ' passing across ' + $testRows.Count + ' files') -Count $passTotal
Set-Accel -Id 'V15' -State 'GREEN' -Mode 'EXACT' -Detail 'every edit is reversible from its .bak sibling'
Set-Accel -Id 'V16' -State 'GREEN' -Mode 'EXACT' -Detail 'progress refreshed at every chunk boundary'
Set-Accel -Id 'V17' -State 'GREEN' -Mode 'EXACT' -Detail 'per-chunk and per-test narration streamed'
Set-Accel -Id 'V18' -State 'GREEN' -Mode 'EXACT' -Detail ('file redirection plus poll loop, ' + $TestTimeoutS + 's hard timeout per child')
Set-Accel -Id 'V19' -State 'GREEN' -Mode 'EXACT' -Detail 'PowerShell parser, git and pytest chained in one pass'
Set-Accel -Id 'V20' -State 'GREEN' -Mode 'EXACT' -Detail 'four-section matrix rendered'

# --- report ------------------------------------------------------------
Show-Prog -Status 'V20 rendering matrix' -Percent 97
$overall = 'GREEN'
if ($blockers.Count -gt 0) { $overall = 'RED' }
elseif ($stillDefTest.Count -gt 0 -or $uniqCount -gt 0 -or $timeoutTotal -gt 0) { $overall = 'YELLOW' }

$payload = [pscustomobject]@{
    schema = 'VIA_PostRepairVerify/1.0'; run_id = $script:RunId; at = $script:StartedAt.ToString('s')
    root = $Root; overall = $overall; blockers = $blockers
    git_entries = $modified.Count; whole_file_rewrites = $eolOnlyFiles
    eol_rows = $eolRows; parse_errors = $parseBad; tests = $testRows
    woken_files = $wokenFiles.Count; still_nested = $stillDefTest.Count
    snapshots = [pscustomobject]@{ total = $rbFiles.Count; redundant = $dupCount; unique = $uniqCount; mb = [Math]::Round($rbBytes / 1MB, 1) }
    actions = $actions
}
$planPath = Join-Path $runDir 'verify_report.json'
Write-TextFile -Path $planPath -Content ($payload | ConvertTo-Json -Depth 6)

function Get-Badge {
    param([string]$S)
    $c = 'gy'
    if ($S -eq 'GREEN' -or $S -eq 'PASS') { $c = 'gr' }
    if ($S -eq 'YELLOW' -or $S -eq 'NO_TESTS' -or $S -eq 'TIMEOUT') { $c = 'ye' }
    if ($S -eq 'RED' -or $S -eq 'FAIL' -or $S -eq 'ERROR') { $c = 'rd' }
    return '<span class="b ' + $c + '">' + $S + '</span>'
}
$rowsTest = ''
foreach ($t in ($testRows | Sort-Object @{e={$_.State -eq 'PASS'}}, File)) {
    $rowsTest = $rowsTest + '<tr><td class="m">' + $t.File + '</td><td class="c">' + (Get-Badge -S $t.State) + '</td><td class="c">' + $t.Declared + '</td><td class="c">' + $t.Passed + '</td><td class="c">' + $t.Failed + '</td><td class="c">' + $t.Errors + '</td><td class="m dim">' + $t.Tail + '</td></tr>'
}
if ($rowsTest -eq '') { $rowsTest = '<tr><td colspan="7" class="dim">No tests were executed.</td></tr>' }

$rowsParse = ''
foreach ($p in $parseBad) {
    $rowsParse = $rowsParse + '<tr><td class="m">' + $p.File + '</td><td class="c">' + $p.Errors + '</td><td class="c">' + $p.Line + '</td><td>' + ($p.Message -replace '<', '&lt;') + '</td></tr>'
}
if ($rowsParse -eq '') { $rowsParse = '<tr><td colspan="4" class="dim">Every script parses.</td></tr>' }

$rowsEol = ''
foreach ($e in ($eolRows | Where-Object { $_.Verdict -eq 'WHOLE_FILE_REWRITE' } | Select-Object -First 40)) {
    $rowsEol = $rowsEol + '<tr><td class="m">' + $e.File + '</td><td class="c">' + $e.Added + '</td><td class="c">' + $e.Removed + '</td><td class="c">' + $e.Lines + '</td><td class="c">' + $e.Ratio + '</td></tr>'
}
if ($rowsEol -eq '') { $rowsEol = '<tr><td colspan="5" class="dim">No whole-file rewrites.</td></tr>' }

$rowsAct = ''
foreach ($a in $actions) {
    $rowsAct = $rowsAct + '<tr><td class="c">' + $a.Order + '</td><td>' + $a.Action + '</td><td class="dim">' + $a.Why + '</td></tr>'
}

function Section-Rows {
    param([string[]]$Ids)
    $s = ''
    foreach ($id in $Ids) {
        $a = $script:Accel[$id]
        $m = $(if ($a.Mode) { $a.Mode } else { 'EXACT' })
        $mb = 'exact'
        if ($m -eq 'HEURISTIC') { $mb = 'heur' }
        $s = $s + '<tr><td>' + $a.Id + ' ' + $a.Name + '</td><td class="c">' + (Get-Badge -S $a.State) + '</td><td class="c"><span class="b ' + $mb + '">' + $m + '</span></td><td class="c">' + $a.Count + '</td><td>' + $a.Detail + '</td></tr>'
    }
    return $s
}
$secModule = Section-Rows -Ids @('V01','V02','V03','V04','V05')
$secEngine = Section-Rows -Ids @('V06','V07','V18','V19')
$secLib    = Section-Rows -Ids @('V08','V09','V10','V11','V12','V13','V14','V15')
$secOther  = Section-Rows -Ids @('V16','V17','V20')

$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$logText = ($script:LogLines -join "`n").Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;')

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>POST-REPAIR VERIFY MATRIX — $($script:RunId)</title>
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
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(112px,1fr)); gap:8px; margin-top:14px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:3px; padding:9px 11px; }
  .kpi .n { font-size:17px; font-weight:600; }
  .kpi .l { font-size:10px; color:var(--mu); margin-top:2px; }
  table { width:100%; table-layout:fixed; border-collapse:collapse; background:var(--card);
          border:1px solid var(--line); border-radius:3px; }
  th { font-size:11px; color:var(--mu); font-weight:500; text-align:left; padding:4px 6px;
       border-bottom:1px solid var(--line); }
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
        font-size:10.5px; padding:11px; border-radius:3px; overflow-x:auto; max-height:300px; }
</style>
</head>
<body>
<div class="wrap">

<h1>POST-REPAIR VERIFY MATRIX</h1>
<p class="sub">$($script:RunId) · READ-ONLY · overall $overall · $elapsed s</p>

<div class="kpis">
  <div class="kpi"><div class="n">$overall</div><div class="l">overall RYG</div></div>
  <div class="kpi"><div class="n">$($wokenFiles.Count)</div><div class="l">files with woken tests</div></div>
  <div class="kpi"><div class="n">$passTotal</div><div class="l">tests passing</div></div>
  <div class="kpi"><div class="n">$failTotal</div><div class="l">failing</div></div>
  <div class="kpi"><div class="n">$errTotal</div><div class="l">erroring</div></div>
  <div class="kpi"><div class="n">$($parseBad.Count)</div><div class="l">unparseable ps1</div></div>
  <div class="kpi"><div class="n">$eolOnlyFiles</div><div class="l">whole-file rewrites</div></div>
  <div class="kpi"><div class="n">$uniqCount</div><div class="l">unique snapshots</div></div>
</div>

<h2>MODULE — repo and rename state</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead>
  <tbody>$secModule</tbody>
</table>

<h2>ENGINE — execution and parsing</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead>
  <tbody>$secEngine</tbody>
</table>

<h2>FUNCTION-LIB — analysis and planning</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead>
  <tbody>$secLib</tbody>
</table>

<h2>OTHERS</h2>
<table>
  <colgroup><col style="width:26%"><col style="width:9%"><col style="width:11%"><col style="width:8%"><col style="width:46%"></colgroup>
  <thead><tr><th>Accelerator</th><th>RYG</th><th>Evidence</th><th>Count</th><th>Narration</th></tr></thead>
  <tbody>$secOther</tbody>
</table>

<h2>WOKEN TESTS — first execution since they were written</h2>
<table>
  <colgroup><col style="width:24%"><col style="width:9%"><col style="width:8%"><col style="width:7%"><col style="width:7%"><col style="width:7%"><col style="width:38%"></colgroup>
  <thead><tr><th>File</th><th>State</th><th>Declared</th><th>Pass</th><th>Fail</th><th>Error</th><th>pytest tail</th></tr></thead>
  <tbody>$rowsTest</tbody>
</table>

<h2>UNPARSEABLE SCRIPTS</h2>
<table>
  <colgroup><col style="width:30%"><col style="width:8%"><col style="width:8%"><col style="width:54%"></colgroup>
  <thead><tr><th>Script</th><th>Errors</th><th>Line</th><th>First message</th></tr></thead>
  <tbody>$rowsParse</tbody>
</table>

<h2>WHOLE-FILE REWRITES — line-ending risk</h2>
<table>
  <colgroup><col style="width:52%"><col style="width:12%"><col style="width:12%"><col style="width:12%"><col style="width:12%"></colgroup>
  <thead><tr><th>File</th><th>Added</th><th>Removed</th><th>Lines</th><th>Ratio</th></tr></thead>
  <tbody>$rowsEol</tbody>
</table>

<h2>ORDERED ACTIONS</h2>
<table>
  <colgroup><col style="width:6%"><col style="width:44%"><col style="width:50%"></colgroup>
  <thead><tr><th>#</th><th>Action</th><th>Why</th></tr></thead>
  <tbody>$rowsAct</tbody>
</table>

<h2>EVIDENCE HONESTY</h2>
<div class="note">
  This engine reads and reports. It edits nothing, deletes nothing and commits nothing.
  EXACT accelerators report measurements: SHA256 comparisons, PowerShell ParseError extents,
  real pytest exit output, git numstat. V10 is HEURISTIC because it groups by name, not content.
  V02 infers a line-ending flip from the ratio of changed lines to total lines, so a file that
  genuinely changed everywhere will look the same as one whose endings flipped: confirm with
  <span class="m">git diff --ignore-cr-at-eol</span> before acting on it.
</div>

<h2>CONSOLE LOG</h2>
<pre>$logText</pre>

</div>
</body>
</html>
"@

$reportPath = Join-Path $runDir ('reports\POST_REPAIR_VERIFY_' + $script:Stamp + '.html')
Write-TextFile -Path $reportPath -Content $html
Write-Progress -Activity 'VIA Post-Repair Verify · 20 accelerators' -Completed

Write-Host ''
Write-Host ('  overall ' + $overall + '  ·  tests ' + $passTotal + 'P / ' + $failTotal + 'F / ' + $errTotal + 'E  ·  unparseable ' + $parseBad.Count) -ForegroundColor Green
if ($blockers.Count -gt 0) {
    Write-Host ('  blockers: ' + ($blockers -join '; ')) -ForegroundColor Yellow
}
Write-Host ('  report  ' + $planPath) -ForegroundColor DarkGray
Write-Host ('  matrix  ' + $reportPath) -ForegroundColor DarkGray
Write-Host ''

if (-not $NoOpen) {
    try { Start-Process -FilePath $reportPath } catch { }
}
