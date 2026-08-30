#requires -Version 7.0
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
<#
.SYNOPSIS
    Invoke-VIA-RedFinding-Triage v01 - turn a parse-error wall into a deduplicated fix plan.
.DESCRIPTION
    Companion to the NexusToolBridge / PolyglotCTR engines. It does the bottleneck work a
    human would otherwise do by hand:

      1) Re-scans PowerShell files for AST parse errors (child-process fallback, so a file that
         crashes the parser cannot crash this tool), OR loads an existing VIA_PS_ParseErrors.csv.
      2) For each error, AUTO-EXTRACTS the offending source lines (a context window with the
         failing line marked and a caret at the column) so you never open the file by hand.
      3) CLUSTERS errors by signature (ErrorId + normalized message) to reveal fix-one-fix-all
         root causes - e.g. four gateway copies all failing at 5:33 with the same message become
         ONE P0 cluster: fix the representative, apply to the rest, never four at once (anti-Hydra).
      4) DETECTS backup / timestamped files (e.g. *.before_v...ps1) and OneDrive mirror duplicates
         (same filename under multiple roots) and recommends excluding them from the parse gate,
         instead of treating them as real findings.
      5) Emits a prioritized repair plan + Visual-Lock HTML / CSV / JSON, and optionally writes a
         suggested exclude-regex file the gate engine can consume.

    Read-only and append-only: it never modifies your source, only reads + reports.
    LL-compliant: param first, [IO.File]::WriteAllText, ProcessStartInfo (no Start-Job /
    no Start-Process for subprocess), cuddled else/catch, no exit in main, Write-Progress -Id 1,
    [System.Net.WebUtility]::HtmlEncode, Start-Process only to open the report.
#>

param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$ParseCsv = "",
    [string]$OutputDir = "",
    [int]$ContextLines = 4,
    [switch]$WriteExcludeListSwitch,
    [switch]$NoOpenReportSwitch
)

# =============================================================================
# def STATE
# =============================================================================
$script:def_RunId     = "RUN_{0}_VIA_REDFINDING_TRIAGE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$script:def_Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$script:def_Utf8Bom   = [System.Text.UTF8Encoding]::new($true)

$script:def_OutRoot = if ([string]::IsNullOrWhiteSpace($OutputDir)) { Join-Path $Root ("tools\VIA_RedFindingTriage\runs\" + $script:def_RunId) } else { Join-Path $OutputDir $script:def_RunId }
$script:def_RuntimeDir  = Join-Path $script:def_OutRoot "runtime"
$script:def_RegistryDir = Join-Path $script:def_OutRoot "registry"
$script:def_ReportDir   = Join-Path $script:def_OutRoot "report"
$script:def_ReportHtml  = Join-Path $script:def_ReportDir "VIA_RedFinding_Triage_Report.html"
$script:def_PlanCsv     = Join-Path $script:def_RegistryDir "VIA_RedFinding_RepairPlan.csv"
$script:def_PlanJson    = Join-Path $script:def_RegistryDir "VIA_RedFinding_RepairPlan.json"
$script:def_ExcludeFile = Join-Path $script:def_RegistryDir "VIA_Suggested_ExcludeRegex.txt"

$script:def_LineCache = @{}

# Visual Lock (VPN v3.5)
$script:def_ColBlue = '#4c78a8'
$script:def_ColGrey = '#9c9890'
$script:def_ColTeal = '#439a9a'
$script:def_ColUp   = '#c96b5a'   # RED   = real error to fix
$script:def_ColDown = '#5a9e6f'   # GREEN = resolved / safe

$script:def_PsExt = @(".ps1", ".psm1", ".psd1")
$script:def_ExcludeDirs = @(".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", ".next", "dist", "build", ".venv", "venv", "_envs", "env", "site-packages")
$script:def_ExcludePathRegex = @("\\tools\\VIA_RedFindingTriage\\runs\\", "\\tools\\VIA_PolyglotCTR\\runs\\", "\\tools\\VIA_NexusToolBridge\\runs\\", "\\_vdf_system\\")

# Backup / timestamped-snapshot filename signatures (these should not gate real source).
$script:def_BackupNameRegex = '(?i)(\.before[_\.]|\.bak$|\.backup$|\.orig$|~$|_v\d+_\d{8}_\d{6}|\.\d{8}_\d{6}\.ps1$|[_\.]backup[_\.]|[_\.]copy[_\.]|\bcopy of\b)'

# =============================================================================
# def HELPERS
# =============================================================================
function def_EnsureDir {
    param([string]$Path)
    if (-not [string]::IsNullOrWhiteSpace($Path) -and -not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_SaveText {
    param([string]$Path, [string]$Text, [switch]$BomSwitch)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    $enc = $script:def_Utf8NoBom
    if ($BomSwitch) { $enc = $script:def_Utf8Bom }
    $body = $Text
    if ($null -eq $body) { $body = "" }
    [IO.File]::WriteAllText($Path, $body, $enc)
}

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_CsvField {
    param([object]$Value)
    $s = [string]$Value
    if ($null -eq $s) { $s = "" }
    $s = $s.Replace('"', '""')
    return ('"' + $s + '"')
}

function def_SaveCsv {
    param([string]$Path, [object[]]$Rows)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    $rowsArr = @($Rows)
    if ($rowsArr.Count -eq 0) {
        def_SaveText -Path $Path -Text "" -BomSwitch
        return
    }
    $cols = @($rowsArr[0].PSObject.Properties.Name)
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine(($cols | ForEach-Object { def_CsvField $_ }) -join ",")
    foreach ($r in $rowsArr) {
        $line = foreach ($c in $cols) { def_CsvField ($r.$c) }
        [void]$sb.AppendLine(($line -join ","))
    }
    def_SaveText -Path $Path -Text $sb.ToString() -BomSwitch
}

function def_WriteLog {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("HH:mm:ss")
    $color = switch ($Level) {
        'OK'   { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
        'RUN'  { 'Cyan' }
        default { 'Gray' }
    }
    Write-Host ("[{0}] [{1}] {2}" -f $ts, $Level, $Message) -ForegroundColor $color
}

$script:def_NextTick = [DateTime]::MinValue
function def_ShowProgress {
    param([int]$Step, [int]$Total, [string]$Status)
    $now = Get-Date
    if ($now -lt $script:def_NextTick -and $Step -lt $Total) { return }
    $script:def_NextTick = $now.AddMilliseconds(150)
    $pct = 0
    if ($Total -gt 0) { $pct = [Math]::Min(100, [int](($Step / $Total) * 100)) }
    Write-Progress -Id 1 -Activity "VIA Red-Finding Triage v01" -Status $Status -PercentComplete $pct
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    if ($InputObject -is [array]) { return $InputObject.Count }
    return 1
}

function def_IsBackupFile {
    param([string]$Name)
    return ($Name -match $script:def_BackupNameRegex)
}

function def_IsExcludedPath {
    param([string]$Path)
    foreach ($name in $script:def_ExcludeDirs) {
        if ($Path -match ("\\{0}(\z|\\)" -f [regex]::Escape($name))) { return $true }
    }
    foreach ($rx in $script:def_ExcludePathRegex) {
        if ($Path -match $rx) { return $true }
    }
    return $false
}

function def_GetSourceFiles {
    $all = Get-ChildItem -LiteralPath $Root -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $ext = $_.Extension.ToLowerInvariant()
            ($script:def_PsExt -contains $ext) -and (-not (def_IsExcludedPath -Path $_.FullName))
        }
    return @($all)
}

function def_GetPwsh {
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd2 = Get-Command powershell -ErrorAction SilentlyContinue
    if ($cmd2) { return $cmd2.Source }
    return $null
}

function def_GetFileLines {
    param([string]$Path)
    if ($script:def_LineCache.ContainsKey($Path)) { return $script:def_LineCache[$Path] }
    $lines = @()
    try {
        $lines = [IO.File]::ReadAllLines($Path)
    } catch {
        try { $lines = @(Get-Content -LiteralPath $Path -ErrorAction Stop) } catch { $lines = @() }
    }
    $script:def_LineCache[$Path] = $lines
    return $lines
}

# =============================================================================
# def CHILD-PROCESS AST PARSER (crash-isolated)
# =============================================================================
function def_GetChildParserScript {
    $childPath = Join-Path $script:def_RuntimeDir "VIA_PS_ChildParser.ps1"
    if (Test-Path -LiteralPath $childPath) { return $childPath }
    $child = @'
param([Parameter(Mandatory)][string]$LiteralPath)
$ErrorActionPreference = "Stop"
try {
    [System.Management.Automation.Language.Token[]]$tokens = $null
    [System.Management.Automation.Language.ParseError[]]$errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile([string]$LiteralPath, [ref]$tokens, [ref]$errors) | Out-Null
    $rows = @()
    foreach ($e in @($errors)) {
        $rows += [pscustomobject]@{
            Line = [int]$e.Extent.StartLineNumber
            Column = [int]$e.Extent.StartColumnNumber
            ErrorId = [string]$e.ErrorId
            Message = [string]$e.Message
        }
    }
    @($rows) | ConvertTo-Json -Depth 6 -Compress
    exit 0
}
catch {
    @([pscustomobject]@{ Line = 0; Column = 0; ErrorId = "ChildParserException"; Message = [string]$_.Exception.Message }) | ConvertTo-Json -Depth 6 -Compress
    exit 9
}
'@
    def_SaveText -Path $childPath -Text $child
    return $childPath
}

function def_InvokeChildParser {
    param([string]$FilePath)
    $pwsh = def_GetPwsh
    if ($null -eq $pwsh) { return @() }
    $childParser = def_GetChildParserScript
    $safe = ($FilePath -replace '[:\\/\*\?"<>\|\s]+', '_')
    if ($safe.Length -gt 90) { $safe = $safe.Substring($safe.Length - 90) }
    def_EnsureDir -Path $script:def_RuntimeDir
    $stdout = Join-Path $script:def_RuntimeDir ("child_{0}.out.txt" -f $safe)

    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $pwsh
        foreach ($a in @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $childParser, $FilePath)) { [void]$psi.ArgumentList.Add($a) }
        $psi.WorkingDirectory = $Root
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::new()
        $p.StartInfo = $psi
        [void]$p.Start()
        $outTask = $p.StandardOutput.ReadToEndAsync()
        $errTask = $p.StandardError.ReadToEndAsync()
        $finished = $p.WaitForExit(120 * 1000)
        if (-not $finished) {
            try { $p.Kill($true) } catch { }
            return @()
        }
        $jsonText = $outTask.Result
        if ([string]::IsNullOrWhiteSpace($jsonText)) { return @() }
        return @($jsonText | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        return @()
    }
}

function def_ParsePSFileSafe {
    param([System.IO.FileInfo]$File)
    $rows = [System.Collections.Generic.List[object]]::new()
    try {
        [System.Management.Automation.Language.Token[]]$tokens = $null
        [System.Management.Automation.Language.ParseError[]]$errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile([string]$File.FullName, [ref]$tokens, [ref]$errors) | Out-Null
        foreach ($e in @($errors)) {
            $rows.Add([pscustomobject]@{
                Path = $File.FullName; File = $File.Name
                Line = [int]$e.Extent.StartLineNumber; Column = [int]$e.Extent.StartColumnNumber
                ErrorId = [string]$e.ErrorId; Message = [string]$e.Message
            }) | Out-Null
        }
        return @($rows)
    } catch {
        foreach ($r in @(def_InvokeChildParser -FilePath $File.FullName)) {
            $rows.Add([pscustomobject]@{
                Path = $File.FullName; File = $File.Name
                Line = [int]$r.Line; Column = [int]$r.Column
                ErrorId = [string]$r.ErrorId; Message = [string]$r.Message
            }) | Out-Null
        }
        return @($rows)
    }
}

# =============================================================================
# def COLLECT ERRORS (fresh scan, or load existing parse CSV)
# =============================================================================
function def_CollectErrors {
    $rows = [System.Collections.Generic.List[object]]::new()

    if (-not [string]::IsNullOrWhiteSpace($ParseCsv) -and (Test-Path -LiteralPath $ParseCsv -PathType Leaf)) {
        def_WriteLog "RUN" ("Loading existing parse CSV: {0}" -f $ParseCsv)
        try {
            $csv = @(Import-Csv -LiteralPath $ParseCsv)
            foreach ($c in $csv) {
                $rows.Add([pscustomobject]@{
                    Path = [string]$c.Path
                    File = [string]$c.File
                    Line = [int]([string]$c.Line)
                    Column = [int]([string]$c.Column)
                    ErrorId = [string]$c.ErrorId
                    Message = [string]$c.Message
                }) | Out-Null
            }
            return @($rows)
        } catch {
            def_WriteLog "WARN" ("CSV load failed ({0}); falling back to fresh scan." -f $_.Exception.Message)
        }
    }

    def_WriteLog "RUN" "Fresh AST scan (child-process fallback)."
    $files = @(def_GetSourceFiles)
    $i = 0
    $total = [Math]::Max(1, (def_CountSafe $files))
    foreach ($f in $files) {
        $i++
        def_ShowProgress -Step $i -Total $total -Status ("AST scan {0}/{1}" -f $i, $total)
        foreach ($r in @(def_ParsePSFileSafe -File $f)) {
            if (($null -ne $r.ErrorId) -and ($r.ErrorId -ne "") -and (($r.Line -ne 0) -or ($r.Message -ne ""))) {
                $rows.Add($r) | Out-Null
            }
        }
    }
    Write-Progress -Id 1 -Activity "VIA Red-Finding Triage v01" -Completed
    return @($rows)
}

# =============================================================================
# def CONTEXT EXTRACTION - pull the actual offending lines
# =============================================================================
function def_ExtractContext {
    param([string]$Path, [int]$Line, [int]$Column)
    $lines = def_GetFileLines -Path $Path
    $n = def_CountSafe $lines
    $out = [System.Collections.Generic.List[object]]::new()
    if ($n -eq 0 -or $Line -lt 1) {
        return @($out)
    }
    $start = [Math]::Max(1, $Line - $ContextLines)
    $end = [Math]::Min($n, $Line + $ContextLines)
    for ($k = $start; $k -le $end; $k++) {
        $text = ""
        if ($k -le $n) { $text = [string]$lines[$k - 1] }
        $out.Add([pscustomobject]@{
            Num = $k
            Text = $text
            IsErr = ($k -eq $Line)
        }) | Out-Null
    }
    return @($out)
}

function def_GetOffendingLineText {
    param([string]$Path, [int]$Line)
    $lines = def_GetFileLines -Path $Path
    $n = def_CountSafe $lines
    if ($Line -ge 1 -and $Line -le $n) { return [string]$lines[$Line - 1] }
    return ""
}

# =============================================================================
# def CLUSTERING - group by root-cause signature (fix-one-fix-all)
# =============================================================================
function def_NormalizeMsg {
    param([string]$Message)
    $m = [string]$Message
    $m = $m -replace '\s+', ' '
    return $m.Trim()
}

function def_BuildClusters {
    param([object[]]$Errors)
    $map = [ordered]@{}
    foreach ($e in $Errors) {
        $norm = def_NormalizeMsg -Message $e.Message
        $sig = ("{0} || {1}" -f $e.ErrorId, $norm)
        if (-not $map.Contains($sig)) {
            $map[$sig] = [pscustomobject]@{
                Signature = $sig
                ErrorId = $e.ErrorId
                Message = $norm
                Items = [System.Collections.Generic.List[object]]::new()
                Files = [System.Collections.Generic.List[string]]::new()
            }
        }
        $map[$sig].Items.Add($e) | Out-Null
        if (-not $map[$sig].Files.Contains($e.Path)) { $map[$sig].Files.Add($e.Path) | Out-Null }
    }

    $clusters = [System.Collections.Generic.List[object]]::new()
    foreach ($k in $map.Keys) {
        $c = $map[$k]
        $fileCount = def_CountSafe $c.Files
        $priority = "P1"
        $kind = "SINGLETON"
        if ($fileCount -ge 2) {
            $priority = "P0"
            $kind = "SHARED_ROOT_CAUSE"
        }
        # representative = first item; pull its offending line + a column pointer
        $rep = $c.Items[0]
        $repLineText = def_GetOffendingLineText -Path $rep.Path -Line $rep.Line
        $clusters.Add([pscustomobject]@{
            Priority = $priority
            Kind = $kind
            ErrorId = $c.ErrorId
            Message = $c.Message
            FileCount = $fileCount
            ErrorCount = (def_CountSafe $c.Items)
            Files = @($c.Files)
            RepPath = $rep.Path
            RepFile = $rep.File
            RepLine = $rep.Line
            RepColumn = $rep.Column
            RepLineText = $repLineText
            Items = @($c.Items)
        }) | Out-Null
    }
    # P0 (shared root cause) first, then by file count desc
    return @($clusters | Sort-Object -Property @{ e = 'Priority'; desc = $false }, @{ e = 'FileCount'; desc = $true })
}

# =============================================================================
# def DUPLICATE / BACKUP DETECTION
# =============================================================================
function def_AnalyzeFileHygiene {
    param([object[]]$Errors)
    $paths = @($Errors | Select-Object -ExpandProperty Path -Unique)

    $backups = [System.Collections.Generic.List[object]]::new()
    $realPaths = [System.Collections.Generic.List[string]]::new()
    foreach ($p in $paths) {
        $name = Split-Path $p -Leaf
        if (def_IsBackupFile -Name $name) {
            $backups.Add([pscustomobject]@{ Path = $p; File = $name; Reason = "timestamped/backup snapshot" }) | Out-Null
        } else {
            $realPaths.Add($p) | Out-Null
        }
    }

    # mirror duplicates: same filename under 2+ distinct directories
    $byName = @{}
    foreach ($p in $realPaths) {
        $name = Split-Path $p -Leaf
        if (-not $byName.ContainsKey($name)) { $byName[$name] = [System.Collections.Generic.List[string]]::new() }
        $byName[$name].Add($p) | Out-Null
    }
    $dupSets = [System.Collections.Generic.List[object]]::new()
    foreach ($name in $byName.Keys) {
        $plist = @($byName[$name])
        if ($plist.Count -ge 2) {
            # canonical = prefer the one NOT under OneDrive, else the shortest path
            $canonical = @($plist | Where-Object { $_ -notmatch '(?i)OneDrive' } | Select-Object -First 1)
            if (-not $canonical) { $canonical = @($plist | Sort-Object -Property Length | Select-Object -First 1) }
            $dupSets.Add([pscustomobject]@{
                File = $name
                Count = $plist.Count
                Canonical = ([string]$canonical)
                Mirrors = @($plist | Where-Object { $_ -ne ([string]$canonical) })
                All = $plist
            }) | Out-Null
        }
    }

    return [pscustomobject]@{
        Backups = @($backups)
        DupSets = @($dupSets)
        RealPaths = @($realPaths)
    }
}

function def_BuildExcludeRegex {
    param([object]$Hygiene)
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("# Suggested exclude regexes for the parse gate (add to `$script:def_ExcludePathRegex).") | Out-Null
    $lines.Add("# 1) Backup / timestamped snapshots (filename pattern):") | Out-Null
    $lines.Add('(?i)(\.before[_\.]|\.bak$|\.backup$|\.orig$|_v\d+_\d{8}_\d{6}\.ps1$)') | Out-Null
    if ((def_CountSafe $Hygiene.DupSets) -gt 0) {
        $lines.Add("# 2) Mirror duplicates - keep canonical, exclude the mirror roots below:") | Out-Null
        $mirrorRoots = [System.Collections.Generic.List[string]]::new()
        foreach ($d in $Hygiene.DupSets) {
            foreach ($m in $d.Mirrors) {
                $dir = Split-Path $m -Parent
                if (-not $mirrorRoots.Contains($dir)) { $mirrorRoots.Add($dir) | Out-Null }
            }
        }
        foreach ($r in $mirrorRoots) {
            $esc = [regex]::Escape($r)
            $lines.Add($esc) | Out-Null
        }
    }
    return ($lines -join "`r`n")
}

# =============================================================================
# def REPAIR PLAN
# =============================================================================
function def_BuildRepairPlan {
    param([object[]]$Clusters, [object]$Hygiene)
    $plan = [System.Collections.Generic.List[object]]::new()
    $rank = 0
    foreach ($c in $Clusters) {
        $rank++
        $action = "Fix the representative, then apply the identical fix to the other copies; do NOT edit all at once."
        if ($c.Kind -eq "SINGLETON") { $action = "Fix this single file at the marked line:column." }
        $plan.Add([pscustomobject]@{
            Rank = $rank
            Priority = $c.Priority
            Kind = $c.Kind
            ErrorId = $c.ErrorId
            Files = $c.FileCount
            Errors = $c.ErrorCount
            RepFile = $c.RepFile
            RepLineCol = ("{0}:{1}" -f $c.RepLine, $c.RepColumn)
            Message = $c.Message
            Action = $action
            RepPath = $c.RepPath
        }) | Out-Null
    }
    foreach ($b in $Hygiene.Backups) {
        $rank++
        $plan.Add([pscustomobject]@{
            Rank = $rank
            Priority = "P2"
            Kind = "EXCLUDE_BACKUP"
            ErrorId = ""
            Files = 1
            Errors = 0
            RepFile = $b.File
            RepLineCol = ""
            Message = ("Backup/timestamped snapshot ({0}) - should not gate real source." -f $b.Reason)
            Action = "Add to the gate exclude list; do not fix."
            RepPath = $b.Path
        }) | Out-Null
    }
    return @($plan)
}

# =============================================================================
# def HTML REPORT (Visual Lock)
# =============================================================================
function def_BuildContextHtml {
    param([string]$Path, [int]$Line, [int]$Column)
    $ctx = @(def_ExtractContext -Path $Path -Line $Line -Column $Column)
    if ((def_CountSafe $ctx) -eq 0) { return "<div class='small'>(source not readable)</div>" }
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("<pre class='code'>")
    foreach ($row in $ctx) {
        $num = ("{0,5}" -f $row.Num)
        $txt = def_HtmlEncode $row.Text
        if ($row.IsErr) {
            [void]$sb.AppendLine(("<span class='err'>{0} | {1}</span>" -f $num, $txt))
            $caretPad = ""
            $padCount = 8 + [Math]::Max(0, $Column - 1)
            if ($padCount -gt 0) { $caretPad = (" " * $padCount) }
            [void]$sb.AppendLine(("<span class='caret'>{0}^ col {1}</span>" -f $caretPad, $Column))
        } else {
            [void]$sb.AppendLine(("{0} | {1}" -f $num, $txt))
        }
    }
    [void]$sb.AppendLine("</pre>")
    return $sb.ToString()
}

function def_BuildClusterCards {
    param([object[]]$Clusters)
    $sb = [System.Text.StringBuilder]::new()
    foreach ($c in $Clusters) {
        $pcolor = $script:def_ColGrey
        if ($c.Priority -eq "P0") {
            $pcolor = $script:def_ColUp
        } elseif ($c.Priority -eq "P1") {
            $pcolor = $script:def_ColBlue
        }
        [void]$sb.AppendLine("<div class='cluster'>")
        [void]$sb.AppendLine(("<div class='chead'><span class='pill' style='background:{0}'>{1} {2}</span> <b>{3}</b> <span class='small'>&middot; {4} file(s) &middot; {5} error(s) &middot; ErrorId {6}</span></div>" -f $pcolor, (def_HtmlEncode $c.Priority), (def_HtmlEncode $c.Kind), (def_HtmlEncode $c.Message), $c.FileCount, $c.ErrorCount, (def_HtmlEncode $c.ErrorId)))
        $fileList = [System.Collections.Generic.List[string]]::new()
        foreach ($f in $c.Files) { $fileList.Add(("<code>{0}</code>" -f (def_HtmlEncode (Split-Path $f -Leaf)))) | Out-Null }
        [void]$sb.AppendLine(("<div class='small files'>affected: {0}</div>" -f ($fileList -join " ")))
        [void]$sb.AppendLine(("<div class='small'>representative: <code>{0}</code> @ {1}:{2}</div>" -f (def_HtmlEncode $c.RepFile), $c.RepLine, $c.RepColumn))
        [void]$sb.AppendLine((def_BuildContextHtml -Path $c.RepPath -Line $c.RepLine -Column $c.RepColumn))
        [void]$sb.AppendLine("</div>")
    }
    return $sb.ToString()
}

function def_BuildHygieneRows {
    param([object]$Hygiene)
    $sb = [System.Text.StringBuilder]::new()
    foreach ($b in $Hygiene.Backups) {
        [void]$sb.AppendLine("<tr>")
        [void]$sb.AppendLine(("<td class='mono'>backup</td><td>{0}</td><td class='small'>{1}</td><td class='mono small'>{2}</td>" -f (def_HtmlEncode $b.File), (def_HtmlEncode $b.Reason), (def_HtmlEncode $b.Path)))
        [void]$sb.AppendLine("</tr>")
    }
    foreach ($d in $Hygiene.DupSets) {
        $mirrors = (@($d.Mirrors) | ForEach-Object { def_HtmlEncode $_ }) -join "<br>"
        [void]$sb.AppendLine("<tr>")
        [void]$sb.AppendLine(("<td class='mono'>mirror x{0}</td><td>{1}</td><td class='small'>canonical: <code>{2}</code></td><td class='mono small'>{3}</td>" -f $d.Count, (def_HtmlEncode $d.File), (def_HtmlEncode $d.Canonical), $mirrors))
        [void]$sb.AppendLine("</tr>")
    }
    return $sb.ToString()
}

function def_WriteReport {
    param([object[]]$Clusters, [object]$Hygiene, [int]$TotalErrors)
    $p0 = def_CountSafe ($Clusters | Where-Object { $_.Priority -eq "P0" })
    $clusterCount = def_CountSafe $Clusters
    $realFiles = def_CountSafe $Hygiene.RealPaths
    $backupCount = def_CountSafe $Hygiene.Backups
    $dupCount = def_CountSafe $Hygiene.DupSets
    $excludeText = def_BuildExcludeRegex -Hygiene $Hygiene

    $tpl = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Red-Finding Triage</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;700;800&display=swap');
:root{ --blue:@@BLUE@@; --grey:@@GREY@@; --teal:@@TEAL@@; --up:@@UP@@; --down:@@DOWN@@; }
*{ box-sizing:border-box; }
body{ margin:0; padding:34px 40px; background:#13161a; color:#e7e9ec; font-family:'DM Sans',sans-serif; }
h1{ font-family:'Syne',sans-serif; font-weight:800; font-size:24px; margin:0 0 4px; color:#fff; }
.sub{ color:var(--grey); font-size:13px; margin-bottom:18px; }
.grid{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:18px 0 24px; }
.card{ background:#1b1f24; border:1px solid #2a2f36; border-radius:14px; padding:14px 16px; }
.k{ font-size:12px; color:var(--grey); } .v{ font-size:23px; font-weight:700; margin-top:4px; font-family:'DM Mono',monospace; color:var(--teal); }
h2{ font-family:'Syne',sans-serif; font-weight:700; font-size:16px; color:var(--blue); border-bottom:1px solid #2a2f36; padding-bottom:8px; margin:28px 0 14px; }
.cluster{ background:#171b20; border:1px solid #2a2f36; border-radius:12px; padding:14px 16px; margin-bottom:14px; }
.chead{ margin-bottom:8px; } .chead b{ color:#fff; }
.files{ margin:4px 0 6px; }
.pill{ display:inline-block; padding:2px 9px; border-radius:11px; color:#13161a; font-weight:700; font-size:10.5px; font-family:'DM Mono',monospace; }
pre.code{ background:#0f1216; border:1px solid #23282e; border-radius:8px; padding:10px 12px; overflow-x:auto; font-family:'DM Mono',monospace; font-size:12px; line-height:1.5; color:#c9d1d9; margin:8px 0 0; white-space:pre; }
pre.code .err{ display:block; background:rgba(201,107,90,.16); color:#f0b8ad; }
pre.code .caret{ display:block; color:var(--up); }
table{ border-collapse:collapse; width:100%; background:#171b20; border:1px solid #2a2f36; border-radius:10px; overflow:hidden; font-size:12px; }
th{ background:#1d2228; color:var(--teal); text-align:left; padding:9px 10px; font-family:'DM Mono',monospace; font-size:11px; }
td{ padding:8px 10px; border-bottom:1px solid #23282e; vertical-align:top; }
.mono{ font-family:'DM Mono',monospace; } .small{ font-size:11px; color:#aab0b6; }
code{ background:#23282e; padding:1px 5px; border-radius:4px; font-family:'DM Mono',monospace; color:#e7e9ec; font-size:11px; }
pre.excl{ background:#0f1216; border:1px solid #23282e; border-radius:8px; padding:12px; font-family:'DM Mono',monospace; font-size:11.5px; color:#c9d1d9; white-space:pre-wrap; }
.foot{ color:var(--grey); font-size:11px; margin-top:22px; line-height:1.6; }
</style>
</head>
<body>
<h1>理 &middot; VIA Red-Finding Triage</h1>
<div class="sub">auto-extract offending lines &middot; cluster shared root causes &middot; 判天地之美，析萬物之理 &middot; @@RUNID@@</div>
<div class="grid">
  <div class="card"><div class="k">Total errors</div><div class="v">@@TOTAL@@</div></div>
  <div class="card"><div class="k">Real files</div><div class="v">@@REALFILES@@</div></div>
  <div class="card"><div class="k">Clusters</div><div class="v">@@CLUSTERS@@</div></div>
  <div class="card"><div class="k">P0 fix-one-fix-all</div><div class="v">@@P0@@</div></div>
  <div class="card"><div class="k">Backups / mirrors</div><div class="v">@@BACKUPS@@ / @@DUPS@@</div></div>
</div>

<h2>Root-cause clusters (fix-one-fix-all first)</h2>
@@CLUSTERCARDS@@

<h2>File hygiene - exclude these from the gate (do not fix)</h2>
<table>
<thead><tr><th>kind</th><th>file</th><th>why</th><th>path(s)</th></tr></thead>
<tbody>@@HYGIENEROWS@@</tbody>
</table>

<h2>Suggested exclude regex (for the gate engine)</h2>
<pre class="excl">@@EXCLUDE@@</pre>

<div class="foot">
Read-only triage: nothing in your source was modified. P0 clusters share one root cause across copies -
fix the representative, then apply the identical change to the rest (never all at once = anti-Hydra).
After parse clusters clear, the lint-level findings (PSSA-fixable / ruff-fixable) become the safe parallel batch.
Generated @@GENERATED@@.
</div>
</body>
</html>
'@
    $html = $tpl
    $html = $html.Replace('@@BLUE@@', $script:def_ColBlue)
    $html = $html.Replace('@@GREY@@', $script:def_ColGrey)
    $html = $html.Replace('@@TEAL@@', $script:def_ColTeal)
    $html = $html.Replace('@@UP@@', $script:def_ColUp)
    $html = $html.Replace('@@DOWN@@', $script:def_ColDown)
    $html = $html.Replace('@@RUNID@@', (def_HtmlEncode $script:def_RunId))
    $html = $html.Replace('@@TOTAL@@', [string]$TotalErrors)
    $html = $html.Replace('@@REALFILES@@', [string]$realFiles)
    $html = $html.Replace('@@CLUSTERS@@', [string]$clusterCount)
    $html = $html.Replace('@@P0@@', [string]$p0)
    $html = $html.Replace('@@BACKUPS@@', [string]$backupCount)
    $html = $html.Replace('@@DUPS@@', [string]$dupCount)
    $html = $html.Replace('@@CLUSTERCARDS@@', (def_BuildClusterCards -Clusters $Clusters))
    $html = $html.Replace('@@HYGIENEROWS@@', (def_BuildHygieneRows -Hygiene $Hygiene))
    $html = $html.Replace('@@EXCLUDE@@', (def_HtmlEncode $excludeText))
    $html = $html.Replace('@@GENERATED@@', (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
    def_SaveText -Path $script:def_ReportHtml -Text $html
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " VIA Red-Finding Triage v01  (auto-extract + root-cause clustering)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Root   : {0}" -f $Root)
    Write-Host ("Run ID : {0}" -f $script:def_RunId)
    Write-Host ""

    foreach ($d in @($script:def_OutRoot, $script:def_RuntimeDir, $script:def_RegistryDir, $script:def_ReportDir)) {
        def_EnsureDir -Path $d
    }

    $errors = @(def_CollectErrors)
    $totalErrors = def_CountSafe $errors
    def_WriteLog "RUN" ("Collected {0} parse error(s)." -f $totalErrors)

    if ($totalErrors -eq 0) {
        def_WriteLog "OK" "No parse errors - gate is clean. Nothing to triage."
    }

    $hygiene = def_AnalyzeFileHygiene -Errors $errors
    # exclude backups from the real clustering (they should not gate source)
    $realErrors = @($errors | Where-Object { -not (def_IsBackupFile -Name $_.File) })
    $clusters = @(def_BuildClusters -Errors $realErrors)
    $plan = @(def_BuildRepairPlan -Clusters $clusters -Hygiene $hygiene)

    def_SaveCsv -Path $script:def_PlanCsv -Rows $plan
    $planJson = $plan | ConvertTo-Json -Depth 8
    def_SaveText -Path $script:def_PlanJson -Text $planJson

    if ($WriteExcludeListSwitch) {
        $excludeText = def_BuildExcludeRegex -Hygiene $hygiene
        def_SaveText -Path $script:def_ExcludeFile -Text $excludeText
        def_WriteLog "OK" ("Exclude regex written: {0}" -f $script:def_ExcludeFile)
    }

    def_WriteReport -Clusters $clusters -Hygiene $hygiene -TotalErrors $totalErrors

    $p0 = def_CountSafe ($clusters | Where-Object { $_.Priority -eq "P0" })
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " TRIAGE COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Errors        : {0}" -f $totalErrors)
    Write-Host ("Clusters      : {0}  (P0 fix-one-fix-all: {1})" -f (def_CountSafe $clusters), $p0)
    Write-Host ("Backups       : {0}   Mirror dup sets: {1}" -f (def_CountSafe $hygiene.Backups), (def_CountSafe $hygiene.DupSets))
    Write-Host ("Plan CSV      : {0}" -f $script:def_PlanCsv)
    Write-Host ("HTML          : {0}" -f $script:def_ReportHtml)
    Write-Host ""

    if (-not $NoOpenReportSwitch -and (Test-Path -LiteralPath $script:def_ReportHtml)) {
        try { Start-Process $script:def_ReportHtml | Out-Null } catch { }
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host ("[FATAL] {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
