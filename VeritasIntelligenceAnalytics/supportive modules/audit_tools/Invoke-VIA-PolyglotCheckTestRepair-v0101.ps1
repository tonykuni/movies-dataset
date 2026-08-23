#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-VIA-PolyglotCheckTestRepair-v0101 {
    param(
        [string]$ProjectRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
        [string[]]$ExtraRoots = @(),
        [switch]$OpenHtmlReport = $true,
        [bool]$InstallTools = $true,
        [bool]$RunTests = $true,
        [switch]$ApplyRepairs,
        [string]$ApprovalToken = "",
        [switch]$IncludeNode,
        [switch]$IncludeDotnet
    )

    $script:OK = 0
    $script:WARN = 0
    $script:FAIL = 0
    $script:PhaseTotal = 12
    $script:PhaseNow = 0
    $RepairToken = "APPROVE_VIA_POLYGLOT_REPAIR"

    # ----------------------------- helpers -----------------------------
    function def_Stamp { Get-Date -Format "yyyyMMdd_HHmmss" }
    function def_Iso { (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffK") }
    function def_Mkdir([string]$Path) { [System.IO.Directory]::CreateDirectory($Path) | Out-Null }
    function def_Html([AllowNull()][string]$Text) { if ($null -eq $Text) { return "" } return [System.Net.WebUtility]::HtmlEncode($Text) }
    function def_WriteText { param([string]$Path,[string]$Text) [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false)) }
    function def_WriteJson { param([string]$Path,[object]$Obj) def_WriteText -Path $Path -Text ($Obj | ConvertTo-Json -Depth 100) }
    function def_Csv([object]$Value) {
        $s = if ($null -eq $Value) { "" } else { [string]$Value }
        if ($s -match '[",\r\n]') { '"' + $s.Replace('"','""') + '"' } else { $s }
    }
    function def_Hash([string]$Path) {
        try { if (-not [System.IO.File]::Exists($Path)) { return "" } return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash } catch { return "HASH_ERROR" }
    }
    function def_Phase {
        param([string]$Name)
        $script:PhaseNow++
        $pct = [int](($script:PhaseNow / $script:PhaseTotal) * 100)
        if ($pct -gt 100) { $pct = 100 }
        Write-Progress -Id 1 -Activity "VIA Polyglot Check-Test-Repair v01.1" -Status "[$($script:PhaseNow)/$($script:PhaseTotal)] $Name" -PercentComplete $pct
        $bar = ('#' * [int]($pct / 5)).PadRight(20,'.')
        Write-Host "  [$pct%] [$bar] $Name" -ForegroundColor DarkCyan
    }
    function def_AddRow {
        param(
            [System.Collections.Generic.List[object]]$Rows,
            [string]$Round,[string]$Lang,[string]$Module,[string]$Stage,[string]$Name,
            [string]$Status,[string]$Risk,[string]$FixClass,[string]$Mode,
            [string]$Metric,[string]$Value,[string]$Message,[string]$Path
        )
        if ($Status -match '^(OK|PASS|READY|CLEAN)') { $script:OK++ }
        elseif ($Status -match 'FAIL|FATAL|BLOCK|ERROR') { $script:FAIL++ }
        else { $script:WARN++ }
        $Rows.Add([pscustomobject]@{
            Round=$Round; Lang=$Lang; Module=$Module; Stage=$Stage; Name=$Name
            Status=$Status; Risk=$Risk; FixClass=$FixClass; Mode=$Mode
            Metric=$Metric; Value=$Value; Message=$Message; Path=$Path
        }) | Out-Null
    }
    function def_Proc {
        param([string]$FilePath,[string[]]$Arguments=@(),[int]$TimeoutSec=600,[string]$WorkDir="")
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $FilePath
        foreach ($a in $Arguments) { [void]$psi.ArgumentList.Add($a) }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        if (-not [string]::IsNullOrWhiteSpace($WorkDir)) { $psi.WorkingDirectory = $WorkDir }
        $proc = [System.Diagnostics.Process]::new()
        $proc.StartInfo = $psi
        try { [void]$proc.Start() } catch { return [pscustomobject]@{ ExitCode=-2; TimedOut=$false; StdOut=""; StdErr=$_.Exception.Message } }
        $outTask = $proc.StandardOutput.ReadToEndAsync()
        $errTask = $proc.StandardError.ReadToEndAsync()
        $exited = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $exited) {
            try { $proc.Kill($true) } catch {}
            return [pscustomobject]@{ ExitCode=-1; TimedOut=$true; StdOut=$outTask.GetAwaiter().GetResult(); StdErr="TIMEOUT after $TimeoutSec sec" }
        }
        return [pscustomobject]@{ ExitCode=$proc.ExitCode; TimedOut=$false; StdOut=$outTask.GetAwaiter().GetResult(); StdErr=$errTask.GetAwaiter().GetResult() }
    }
    function def_Grade {
        param([int]$Ok,[int]$Warn,[int]$Fail)
        $total = $Ok + $Warn + $Fail
        if ($total -le 0) { return "N/A" }
        $failR = $Fail / $total
        $warnR = $Warn / $total
        if ($Fail -eq 0 -and $warnR -lt 0.10) { return "A" }
        elseif ($Fail -eq 0 -and $warnR -lt 0.25) { return "B" }
        elseif ($failR -lt 0.05) { return "C" }
        elseif ($failR -lt 0.15) { return "D" }
        elseif ($failR -lt 0.30) { return "E" }
        else { return "F" }
    }

    if (-not [System.IO.Directory]::Exists($ProjectRoot)) { throw "ProjectRoot not found: $ProjectRoot" }

    # ----------------------------- system root (append-only) -----------------------------
    $Stamp = def_Stamp
    $SysRoot = Join-Path $ProjectRoot "tools\VIA_PolyglotCTR"
    $ConfigDir = Join-Path $SysRoot "config"
    $RegistryDir = Join-Path $SysRoot "registry"
    $RunsDir = Join-Path $SysRoot "runs"
    $RunRoot = Join-Path $RunsDir "RUN_$Stamp"
    $ReportDir = Join-Path $RunRoot "report"
    $RunRegDir = Join-Path $RunRoot "registry"
    $RuntimeDir = Join-Path $RunRoot "runtime"
    $BackupDir = Join-Path $RunRoot "backup"
    $InstallDir = Join-Path $RunRoot "install"
    foreach ($d in @($SysRoot,$ConfigDir,$RegistryDir,$RunsDir,$RunRoot,$ReportDir,$RunRegDir,$RuntimeDir,$BackupDir,$InstallDir)) { def_Mkdir $d }

    $Rows = [System.Collections.Generic.List[object]]::new()
    $LangSummary = [System.Collections.Generic.List[object]]::new()
    $Transcript = Join-Path $RuntimeDir "VIA_PolyglotCTR_v0101_Transcript_$Stamp.txt"

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA POLYGLOT CHECK-TEST-REPAIR SYSTEM v01.1" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "PS / Python / JS-TS / C# . check -> test -> repair(dry-run default) . 3-round . animated HTML"
    Write-Host ""
    try { Start-Transcript -LiteralPath $Transcript -Force | Out-Null } catch {}

    # ==========================================================================
    # Round 0 . M01 bootstrap / config SSOT (append-only)
    # ==========================================================================
    def_Phase "Round0 . M01 bootstrap + config SSOT"
    $ConfigFile = Join-Path $ConfigDir "VIA_PolyglotCTR_Config.json"
    if (-not [System.IO.File]::Exists($ConfigFile)) {
        def_WriteJson -Path $ConfigFile -Obj ([pscustomobject]@{
            created_at = def_Iso
            schema = "VIA_PolyglotCTR_Config_v1"
            policy = [pscustomobject]@{ db_write=$false; canonical_merge=$false; destructive_delete=$false; stop_process=$false; repair_requires_token=$true; repair_token=$RepairToken }
            exclude_segments = @("\node_modules\","\.git\","\.venv\","\_active\","\_backup\","\bin\","\obj\","\dist\","\.vs\")
            languages = @("PS","PY","JS","CS")
            timeouts_sec = [pscustomobject]@{ check=300; test=600; repair=600 }
        })
        def_AddRow $Rows "Round0" "VIA" "M01_CORE" "CONFIG" "Config SSOT" "OK_CREATED" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "config" "created" "System config created (append-only)." $ConfigFile
    } else {
        def_AddRow $Rows "Round0" "VIA" "M01_CORE" "CONFIG" "Config SSOT" "OK_PRESENT" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "config" "kept" "Existing config kept (append-only; not overwritten)." $ConfigFile
    }
    def_AddRow $Rows "Round0" "VIA" "M01_CORE" "POLICY" "Repair Gate" "OK_POLICY_LOCKED" "LOW" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "apply_repairs" "$([bool]$ApplyRepairs)" "Repairs are dry-run unless -ApplyRepairs and approval token match." $BackupDir

    $exclSeg = @("\node_modules\","\.git\","\.venv\","\_active\","\_backup\","\bin\","\obj\","\dist\","\.vs\")
    function def_Excluded([string]$p) { $l = $p.ToLowerInvariant(); foreach ($s in $exclSeg) { if ($l.Contains($s)) { return $true } } return $false }

    # ==========================================================================
    # Round 0 . M02 capability detection
    # ==========================================================================
    def_Phase "Round0 . M02 capability detection"
    function def_Tool([string]$n) { $c = Get-Command $n -ErrorAction SilentlyContinue; if ($null -ne $c) { return $c.Source } else { return "" } }
    $Caps = [ordered]@{
        pwsh   = def_Tool "pwsh"
        python = def_Tool "python"
        py     = def_Tool "py"
        node   = def_Tool "node"
        npm    = def_Tool "npm"
        dotnet = def_Tool "dotnet"
        git    = def_Tool "git"
        ruff   = def_Tool "ruff"
    }
    $HasPSSA = [bool](Get-Module -ListAvailable -Name PSScriptAnalyzer -ErrorAction SilentlyContinue)
    $HasPester = [bool](Get-Module -ListAvailable -Name Pester -ErrorAction SilentlyContinue)
    $ViaCorePy = Join-Path $ProjectRoot ".venv\via_core\Scripts\python.exe"
    $VdfCorePy = Join-Path $ProjectRoot ".venv\vdf_core\Scripts\python.exe"
    $PyExe = if ([System.IO.File]::Exists($ViaCorePy)) { $ViaCorePy } elseif ([System.IO.File]::Exists($VdfCorePy)) { $VdfCorePy } elseif (-not [string]::IsNullOrWhiteSpace($Caps.python)) { $Caps.python } else { "" }

    $CapCsv = Join-Path $RunRegDir "VIA_PolyglotCTR_Capability_$Stamp.csv"
    $capRows = foreach ($k in $Caps.Keys) { [pscustomobject]@{ tool=$k; found=[bool](-not [string]::IsNullOrWhiteSpace($Caps[$k])); path=$Caps[$k] } }
    $capRows = @($capRows) + @(
        [pscustomobject]@{ tool="PSScriptAnalyzer"; found=$HasPSSA; path="(module)" }
        [pscustomobject]@{ tool="Pester"; found=$HasPester; path="(module)" }
        [pscustomobject]@{ tool="python(effective)"; found=[bool](-not [string]::IsNullOrWhiteSpace($PyExe)); path=$PyExe }
    )
    $capRows | Export-Csv -LiteralPath $CapCsv -NoTypeInformation -Encoding UTF8BOM
    def_AddRow $Rows "Round0" "VIA" "M02_DETECT" "CAPABILITY" "Tool Capability Matrix" "OK_CREATED" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "tools" "$(@($capRows).Count)" "Capability matrix created." $CapCsv

    # ==========================================================================
    # Round 0 . M03 one-click toolchain install (additive / idempotent / no hang)
    # ==========================================================================
    def_Phase "Round0 . M03 one-click checker install"
    $InstallCsv = Join-Path $InstallDir "VIA_PolyglotCTR_Install_$Stamp.csv"
    $InstallRows = [System.Collections.Generic.List[object]]::new()
    foreach ($m in @("PSScriptAnalyzer","Pester","PSWriteHTML")) {
        $have = Get-Module -ListAvailable -Name $m -ErrorAction SilentlyContinue
        if ($have) {
            $InstallRows.Add([pscustomobject]@{ kind="ps_module"; target=$m; status="OK_PRESENT" }) | Out-Null
            def_AddRow $Rows "Round0" "PS" "M03_INSTALL" "PS_MODULE" "PS Module: $m" "OK_PRESENT" "LOW" "PARALLEL_SAFE" "ONECLICK_ADDITIVE" "module" $m "Already installed." $SysRoot
        } elseif ($InstallTools) {
            try {
                Install-Module -Name $m -Scope CurrentUser -Force -AllowClobber -SkipPublisherCheck -ErrorAction Stop
                $InstallRows.Add([pscustomobject]@{ kind="ps_module"; target=$m; status="OK_INSTALLED" }) | Out-Null
                def_AddRow $Rows "Round0" "PS" "M03_INSTALL" "PS_MODULE" "PS Module: $m" "OK_INSTALLED" "LOW" "PARALLEL_SAFE" "ONECLICK_ADDITIVE" "module" $m "Installed (CurrentUser)." $SysRoot
            } catch {
                $InstallRows.Add([pscustomobject]@{ kind="ps_module"; target=$m; status="WARN_INSTALL_FAILED" }) | Out-Null
                def_AddRow $Rows "Round0" "PS" "M03_INSTALL" "PS_MODULE" "PS Module: $m" "WARN_INSTALL_FAILED" "MEDIUM" "PARALLEL_SAFE" "ONECLICK_ADDITIVE" "module" $m "Install failed; not a hard block." $SysRoot
            }
        } else {
            def_AddRow $Rows "Round0" "PS" "M03_INSTALL" "PS_MODULE" "PS Module: $m" "WARN_PLAN_ONLY" "MEDIUM" "PARALLEL_SAFE" "PLAN_ONLY" "module" $m "Plan only (InstallTools disabled)." $SysRoot
        }
    }
    # refresh PS capability flags after install
    $HasPSSA = [bool](Get-Module -ListAvailable -Name PSScriptAnalyzer -ErrorAction SilentlyContinue)
    $HasPester = [bool](Get-Module -ListAvailable -Name Pester -ErrorAction SilentlyContinue)
    if ($HasPSSA) { try { Import-Module PSScriptAnalyzer -ErrorAction Stop } catch {} }

    # Python checker venv (ruff + pytest) into via_core
    if ($InstallTools -and -not [string]::IsNullOrWhiteSpace($Caps.py)) {
        $venvPath = Join-Path $ProjectRoot ".venv\via_core"
        $venvPy = Join-Path $venvPath "Scripts\python.exe"
        if (-not [System.IO.File]::Exists($venvPy)) {
            $r = def_Proc -FilePath $Caps.py -Arguments @("-3.11","-m","venv",$venvPath) -TimeoutSec 300
            $st = if ($r.ExitCode -eq 0 -and [System.IO.File]::Exists($venvPy)) { "OK_INSTALLED" } else { "WARN_INSTALL_FAILED" }
            def_AddRow $Rows "Round0" "PY" "M03_INSTALL" "VENV" "Venv via_core" $st "LOW" "SEQUENTIAL_GATED" "ONECLICK_ADDITIVE" "venv" "via_core" "py -3.11 -m venv." $venvPath
        }
        if ([System.IO.File]::Exists($venvPy)) {
            [void](def_Proc -FilePath $venvPy -Arguments @("-m","pip","install","--upgrade","pip","--disable-pip-version-check") -TimeoutSec 300)
            $ri = def_Proc -FilePath $venvPy -Arguments @("-m","pip","install","--disable-pip-version-check","ruff","pytest","pytest-xdist","rich") -TimeoutSec 600
            $st = if ($ri.TimedOut) { "WARN_INSTALL_FAILED" } elseif ($ri.ExitCode -eq 0) { "OK_INSTALLED" } else { "WARN_INSTALL_FAILED" }
            def_AddRow $Rows "Round0" "PY" "M03_INSTALL" "PIP" "ruff + pytest" $st "LOW" "SEQUENTIAL_GATED" "ONECLICK_ADDITIVE" "venv" "via_core" "Python checker/test libs." $venvPath
            $PyExe = $venvPy
            if ([string]::IsNullOrWhiteSpace($Caps.ruff)) { $Caps.ruff = Join-Path $venvPath "Scripts\ruff.exe" }
        }
    } elseif (-not $InstallTools) {
        def_AddRow $Rows "Round0" "PY" "M03_INSTALL" "VENV" "Python checker venv" "WARN_PLAN_ONLY" "MEDIUM" "SEQUENTIAL_GATED" "PLAN_ONLY" "venv" "via_core" "Plan only (InstallTools disabled)." $ProjectRoot
    }
    $InstallRows | Export-Csv -LiteralPath $InstallCsv -NoTypeInformation -Encoding UTF8BOM

    # ==========================================================================
    # Round 0 . accelerated source inventory (single pass, excludes deps/artifacts)
    # ==========================================================================
    def_Phase "Round0 . accelerated source inventory"
    $enumOpts = [System.IO.EnumerationOptions]::new()
    $enumOpts.RecurseSubdirectories = $true
    $enumOpts.IgnoreInaccessible = $true
    $enumOpts.ReturnSpecialDirectories = $false
    $enumOpts.AttributesToSkip = [System.IO.FileAttributes]::ReparsePoint

    $Roots = @($ProjectRoot) + @($ExtraRoots | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and [System.IO.Directory]::Exists($_) })
    $psPaths = [System.Collections.Generic.List[string]]::new()
    $pyPaths = [System.Collections.Generic.List[string]]::new()
    $jsPaths = [System.Collections.Generic.List[string]]::new()
    $csPaths = [System.Collections.Generic.List[string]]::new()
    $psTestPaths = [System.Collections.Generic.List[string]]::new()
    $pyTestPaths = [System.Collections.Generic.List[string]]::new()
    $csprojPaths = [System.Collections.Generic.List[string]]::new()
    $hasPackageJson = $false
    $hasTsconfig = $false
    $fileCount = 0

    foreach ($root in $Roots) {
        foreach ($p in [System.IO.Directory]::EnumerateFiles($root, "*", $enumOpts)) {
            try {
                $fileCount++
                if (def_Excluded $p) { continue }
                $name = [System.IO.Path]::GetFileName($p)
                $ext = [System.IO.Path]::GetExtension($p).ToLowerInvariant()
                switch ($ext) {
                    ".ps1"  { if ($name -match '\.Tests\.ps1$') { $psTestPaths.Add($p) } else { $psPaths.Add($p) } }
                    ".psm1" { $psPaths.Add($p) }
                    ".py"   { if ($name -match '^test_.*\.py$' -or $name -match '_test\.py$' -or $name -eq 'conftest.py') { $pyTestPaths.Add($p) } else { $pyPaths.Add($p) } }
                    ".js"   { $jsPaths.Add($p) }
                    ".mjs"  { $jsPaths.Add($p) }
                    ".cjs"  { $jsPaths.Add($p) }
                    ".cs"   { $csPaths.Add($p) }
                    ".csproj" { $csprojPaths.Add($p) }
                    default {
                        if ($name -eq "package.json") { $hasPackageJson = $true }
                        elseif ($name -eq "tsconfig.json") { $hasTsconfig = $true }
                    }
                }
                if (($fileCount % 2000) -eq 0) { Write-Progress -Id 2 -ParentId 1 -Activity "Source inventory" -Status "$fileCount files" }
            } catch { continue }
        }
    }
    Write-Progress -Id 2 -Completed
    def_AddRow $Rows "Round0" "VIA" "M02_DETECT" "INVENTORY" "Source Inventory" "OK_CREATED" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" "$fileCount" "PS=$(@($psPaths).Count) PY=$(@($pyPaths).Count) JS=$(@($jsPaths).Count) CS=$(@($csPaths).Count)" $ProjectRoot

    # ==========================================================================
    # Round 1 . M04 CHECK (parallel-safe, read-only) per language
    # ==========================================================================
    # ---- PowerShell check: parallel AST + PSScriptAnalyzer ----
    def_Phase "Round1 . M04 PowerShell check"
    $allPs = @($psPaths) + @($psTestPaths)
    $psOk=0; $psWarn=0; $psFail=0; $psFixable=0
    if (@($allPs).Count -gt 0) {
        $throttle = [Math]::Max(2,[Environment]::ProcessorCount)
        $psParse = $allPs | ForEach-Object -ThrottleLimit $throttle -Parallel {
            $path=$_; $tokens=$null; $errors=$null
            try {
                [void][System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
                $c = if ($null -eq $errors) { 0 } else { @($errors).Count }
                [pscustomobject]@{ path=$path; errs=$c }
            } catch { [pscustomobject]@{ path=$path; errs=999 } }
        }
        $psParse = @($psParse)
        $psParseFail = @($psParse | Where-Object { [int]$_.errs -gt 0 })
        if (@($psParseFail).Count -eq 0) {
            def_AddRow $Rows "Round1" "PS" "M04_CHECK" "AST" "PowerShell AST Parse" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "parse_fail" "0" "All PS files parse." $ProjectRoot
        } else {
            $psFail += @($psParseFail).Count
            def_AddRow $Rows "Round1" "PS" "M04_CHECK" "AST" "PowerShell AST Parse" "FAIL_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "ANALYZE_ONLY" "parse_fail" "$(@($psParseFail).Count)" "Files with parse errors." $ProjectRoot
        }
        if ($HasPSSA) {
            $diagErr=0; $diagWarn=0; $diagFix=0
            foreach ($f in $allPs) {
                try {
                    $d = Invoke-ScriptAnalyzer -Path $f -Severity Error,Warning -ErrorAction SilentlyContinue
                    foreach ($x in @($d)) {
                        if ($null -eq $x) { continue }
                        if ($x.Severity -eq 'Error') { $diagErr++ } else { $diagWarn++ }
                        if ($null -ne $x.SuggestedCorrections) { $diagFix++ }
                    }
                } catch {}
            }
            $psWarn += $diagWarn; $psFail += $diagErr; $psFixable = $diagFix
            $st = if ($diagErr -gt 0) { "FAIL_ANALYZER" } elseif ($diagWarn -gt 0) { "WARN_ANALYZER" } else { "OK_CLEAN" }
            def_AddRow $Rows "Round1" "PS" "M04_CHECK" "PSSA" "PSScriptAnalyzer" $st "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "err/warn/fixable" "$diagErr/$diagWarn/$diagFix" "Static analysis findings." $ProjectRoot
        } else {
            def_AddRow $Rows "Round1" "PS" "M04_CHECK" "PSSA" "PSScriptAnalyzer" "WARN_TOOL_MISSING" "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "module" "absent" "PSScriptAnalyzer not available; AST-only check." $ProjectRoot
        }
        $psOk = [Math]::Max(0, @($allPs).Count - $psFail)
    } else {
        def_AddRow $Rows "Round1" "PS" "M04_CHECK" "AST" "PowerShell" "WARN_NO_FILES" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" "0" "No PowerShell source files found." $ProjectRoot
    }

    # ---- Python check: compileall + ruff ----
    def_Phase "Round1 . M04 Python check"
    $pyParseFail=0; $pyLint=0; $pyFixable=0
    $allPy = @($pyPaths) + @($pyTestPaths)
    if (@($allPy).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($PyExe)) {
        $pyDirs = @($allPy | ForEach-Object { [System.IO.Path]::GetDirectoryName($_) } | Sort-Object -Unique)
        $cc = def_Proc -FilePath $PyExe -Arguments (@("-m","compileall","-q","-l") + @($pyDirs)) -TimeoutSec 300
        if ($cc.ExitCode -eq 0) {
            def_AddRow $Rows "Round1" "PY" "M04_CHECK" "COMPILE" "py_compile (compileall)" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "syntax" "clean" "All Python compiles." $ProjectRoot
        } else {
            $pyParseFail = 1
            $combined = ($cc.StdOut + " " + $cc.StdErr).Trim()
            $tail = if ($combined.Length -gt 300) { $combined.Substring($combined.Length-300) } else { $combined }
            def_AddRow $Rows "Round1" "PY" "M04_CHECK" "COMPILE" "py_compile (compileall)" "FAIL_SYNTAX" "HIGH" "SEQUENTIAL_REQUIRED" "ANALYZE_ONLY" "exit" "$($cc.ExitCode)" "Syntax errors: $tail" $ProjectRoot
        }
        $ruffExe = if (-not [string]::IsNullOrWhiteSpace($Caps.ruff) -and [System.IO.File]::Exists($Caps.ruff)) { $Caps.ruff } elseif (-not [string]::IsNullOrWhiteSpace($Caps.ruff)) { $Caps.ruff } else { "" }
        if (-not [string]::IsNullOrWhiteSpace($ruffExe)) {
            $rr = def_Proc -FilePath $ruffExe -Arguments (@("check","--output-format","json") + @($Roots)) -TimeoutSec 300
            $cnt=0; $fix=0
            try { $j = @($rr.StdOut | ConvertFrom-Json); $cnt = @($j).Count; $fix = @($j | Where-Object { $null -ne $_.fix }).Count } catch { $cnt=-1 }
            $pyLint = [Math]::Max(0,$cnt); $pyFixable = $fix
            $st = if ($cnt -gt 0) { "WARN_LINT" } elseif ($cnt -eq 0) { "OK_CLEAN" } else { "WARN_TOOL" }
            def_AddRow $Rows "Round1" "PY" "M04_CHECK" "RUFF" "ruff check" $st "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "findings/fixable" "$pyLint/$pyFixable" "Lint findings." $ProjectRoot
        } else {
            def_AddRow $Rows "Round1" "PY" "M04_CHECK" "RUFF" "ruff check" "WARN_TOOL_MISSING" "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "ruff" "absent" "ruff not available; compile-only check." $ProjectRoot
        }
    } elseif (@($allPy).Count -gt 0) {
        def_AddRow $Rows "Round1" "PY" "M04_CHECK" "COMPILE" "Python" "WARN_NO_PYTHON" "MEDIUM" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "python" "absent" "Python interpreter not found." $ProjectRoot
    } else {
        def_AddRow $Rows "Round1" "PY" "M04_CHECK" "COMPILE" "Python" "WARN_NO_FILES" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" "0" "No Python source files found." $ProjectRoot
    }

    # ---- JavaScript/TS check: node --check (bounded) ----
    def_Phase "Round1 . M04 JavaScript/TS check"
    $jsFail=0
    $jsCheckable = @($jsPaths | Where-Object { $_ -match '\.(js|mjs|cjs)$' })
    if (@($jsPaths).Count -eq 0 -and -not $hasPackageJson) {
        def_AddRow $Rows "Round1" "JS" "M04_CHECK" "NODE" "JavaScript/TS" "WARN_NO_FILES" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" "0" "No JS/TS sources found." $ProjectRoot
    } elseif ([string]::IsNullOrWhiteSpace($Caps.node)) {
        def_AddRow $Rows "Round1" "JS" "M04_CHECK" "NODE" "node --check" "WARN_NO_NODE" "MEDIUM" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "node" "absent" "Node.js not found; JS/TS check skipped." $ProjectRoot
    } elseif (@($jsCheckable).Count -gt 400) {
        def_AddRow $Rows "Round1" "JS" "M04_CHECK" "NODE" "node --check" "WARN_TOO_MANY" "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "js_files" "$(@($jsCheckable).Count)" "Over 400 JS files; bulk check skipped to avoid lag." $ProjectRoot
    } else {
        foreach ($jf in $jsCheckable) {
            $cr = def_Proc -FilePath $Caps.node -Arguments @("--check",$jf) -TimeoutSec 30
            if ($cr.ExitCode -ne 0) { $jsFail++ }
        }
        $st = if ($jsFail -gt 0) { "FAIL_SYNTAX" } else { "OK_ALL_PARSE" }
        $jsRisk = if ($jsFail -gt 0) { "HIGH" } else { "LOW" }
        def_AddRow $Rows "Round1" "JS" "M04_CHECK" "NODE" "node --check" $st $jsRisk "PARALLEL_SAFE" "ANALYZE_ONLY" "syntax_fail" "$jsFail" "Per-file syntax check." $ProjectRoot
        if ($hasTsconfig) { def_AddRow $Rows "Round1" "JS" "M04_CHECK" "TSC" "tsconfig present" "WARN_TS_TYPECHECK" "MEDIUM" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "tsconfig" "found" "Type-check needs local tsc (run via -IncludeNode workspace gate)." $ProjectRoot }
    }

    # ---- C# check: detect + optional dotnet format verify ----
    def_Phase "Round1 . M04 C#/.NET check"
    if (@($csPaths).Count -eq 0) {
        def_AddRow $Rows "Round1" "CS" "M04_CHECK" "DOTNET" "C#/.NET" "WARN_NO_FILES" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" "0" "No C# sources found." $ProjectRoot
    } elseif ([string]::IsNullOrWhiteSpace($Caps.dotnet)) {
        def_AddRow $Rows "Round1" "CS" "M04_CHECK" "DOTNET" "dotnet SDK" "WARN_NO_DOTNET" "MEDIUM" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "dotnet" "absent" "dotnet SDK not found." $ProjectRoot
    } elseif (-not $IncludeDotnet) {
        def_AddRow $Rows "Round1" "CS" "M04_CHECK" "DOTNET" "dotnet format" "WARN_DOTNET_GATED" "MEDIUM" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "include_dotnet" "false" "Pass -IncludeDotnet to run dotnet format/build (heavy)." $ProjectRoot
    } else {
        foreach ($proj in $csprojPaths) {
            $fr = def_Proc -FilePath $Caps.dotnet -Arguments @("format",$proj,"--verify-no-changes") -TimeoutSec 600
            $st = if ($fr.TimedOut) { "WARN_TIMEOUT" } elseif ($fr.ExitCode -eq 0) { "OK_CLEAN" } else { "WARN_FORMAT_DRIFT" }
            def_AddRow $Rows "Round1" "CS" "M04_CHECK" "DOTNET" "dotnet format verify" $st "MEDIUM" "SEQUENTIAL_REQUIRED" "ANALYZE_ONLY" "project" ([System.IO.Path]::GetFileName($proj)) "Format verification." $proj
        }
    }

    # ==========================================================================
    # Round 2 . M05 TEST (sequential, time-boxed) + M06 REPAIR (guarded)
    # ==========================================================================
    def_Phase "Round2 . M05 tests (PS/PY, sequential)"
    # PS tests via child pwsh + Pester (timeout-controlled)
    if (@($psTestPaths).Count -gt 0 -and $HasPester -and $RunTests -and -not [string]::IsNullOrWhiteSpace($Caps.pwsh)) {
        $pesterRunner = Join-Path $RuntimeDir "run_pester.ps1"
        $pesterOut = Join-Path $RuntimeDir "pester_result.json"
        $prLines = @(
            '#requires -Version 7.0',
            'param([string]$TestPath,[string]$OutJson)',
            '$ErrorActionPreference = "Continue"',
            'try {',
            '    Import-Module Pester -ErrorAction Stop',
            '    $r = Invoke-Pester -Path $TestPath -PassThru -Output None',
            '    [pscustomobject]@{ passed=$r.PassedCount; failed=$r.FailedCount; total=$r.TotalCount; ok=$true } | ConvertTo-Json | Set-Content -LiteralPath $OutJson -Encoding UTF8',
            '} catch {',
            '    [pscustomobject]@{ passed=0; failed=0; total=0; ok=$false; error=$_.Exception.Message } | ConvertTo-Json | Set-Content -LiteralPath $OutJson -Encoding UTF8',
            '}'
        )
        def_WriteText -Path $pesterRunner -Text ($prLines -join "`r`n")
        $tr = def_Proc -FilePath $Caps.pwsh -Arguments @("-NoProfile","-NonInteractive","-File",$pesterRunner,"-TestPath",$ProjectRoot,"-OutJson",$pesterOut) -TimeoutSec 600
        if ($tr.TimedOut) {
            def_AddRow $Rows "Round2" "PS" "M05_TEST" "PESTER" "Pester" "WARN_TIMEOUT" "MEDIUM" "SEQUENTIAL_REQUIRED" "TEST" "timeout" "600s" "Pester run timed out." $ProjectRoot
        } else {
            try {
                $pj = Get-Content -LiteralPath $pesterOut -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($pj.ok) {
                    $st = if ([int]$pj.failed -gt 0) { "FAIL_TESTS" } else { "PASS_TESTS" }
                    $psTestRisk = if ([int]$pj.failed -gt 0) { "HIGH" } else { "LOW" }
                    def_AddRow $Rows "Round2" "PS" "M05_TEST" "PESTER" "Pester" $st $psTestRisk "SEQUENTIAL_REQUIRED" "TEST" "pass/fail/total" "$($pj.passed)/$($pj.failed)/$($pj.total)" "Pester results." $ProjectRoot
                } else {
                    def_AddRow $Rows "Round2" "PS" "M05_TEST" "PESTER" "Pester" "WARN_TEST_ERROR" "MEDIUM" "SEQUENTIAL_REQUIRED" "TEST" "error" "see runtime" "Pester errored: $($pj.error)" $ProjectRoot
                }
            } catch { def_AddRow $Rows "Round2" "PS" "M05_TEST" "PESTER" "Pester" "WARN_TEST_NORESULT" "MEDIUM" "SEQUENTIAL_REQUIRED" "TEST" "result" "missing" "No Pester result JSON." $ProjectRoot }
        }
    } else {
        def_AddRow $Rows "Round2" "PS" "M05_TEST" "PESTER" "Pester" "WARN_SKIPPED" "LOW" "SEQUENTIAL_GATED" "TEST" "skipped" "no-tests-or-tool" "No *.Tests.ps1, Pester missing, or RunTests off." $ProjectRoot
    }

    # PY tests via pytest (timeout)
    if (@($pyTestPaths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($PyExe) -and $RunTests) {
        $pt = def_Proc -FilePath $PyExe -Arguments @("-m","pytest","-q","--no-header",$ProjectRoot) -TimeoutSec 600
        if ($pt.TimedOut) {
            def_AddRow $Rows "Round2" "PY" "M05_TEST" "PYTEST" "pytest" "WARN_TIMEOUT" "MEDIUM" "SEQUENTIAL_REQUIRED" "TEST" "timeout" "600s" "pytest timed out." $ProjectRoot
        } else {
            $st = switch ($pt.ExitCode) { 0 { "PASS_TESTS" } 5 { "WARN_NO_TESTS_COLLECTED" } default { "FAIL_TESTS" } }
            $risk = if ($pt.ExitCode -eq 0 -or $pt.ExitCode -eq 5) { "LOW" } else { "HIGH" }
            $tail = if ($pt.StdOut.Length -gt 200) { $pt.StdOut.Substring($pt.StdOut.Length-200) } else { $pt.StdOut }
            def_AddRow $Rows "Round2" "PY" "M05_TEST" "PYTEST" "pytest" $st $risk "SEQUENTIAL_REQUIRED" "TEST" "exit" "$($pt.ExitCode)" "pytest: $tail" $ProjectRoot
        }
    } else {
        def_AddRow $Rows "Round2" "PY" "M05_TEST" "PYTEST" "pytest" "WARN_SKIPPED" "LOW" "SEQUENTIAL_GATED" "TEST" "skipped" "no-tests-or-tool" "No python tests, no interpreter, or RunTests off." $ProjectRoot
    }

    if ($IncludeNode) { def_AddRow $Rows "Round2" "JS" "M05_TEST" "NPM" "npm test" "WARN_NODE_GATED" "MEDIUM" "SEQUENTIAL_GATED" "TEST" "node" "deferred" "Node tests deferred to dedicated workspace gate." $ProjectRoot }
    if ($IncludeDotnet) { def_AddRow $Rows "Round2" "CS" "M05_TEST" "DOTNET" "dotnet test" "WARN_DOTNET_HEAVY" "MEDIUM" "SEQUENTIAL_GATED" "TEST" "dotnet" "deferred" "dotnet test deferred (heavy; run explicitly)." $ProjectRoot }

    # ---- M06 REPAIR (guarded: dry-run unless ApplyRepairs + token) ----
    def_Phase "Round2 . M06 repair (guarded)"
    $repairApproved = ($ApplyRepairs -and ($ApprovalToken -eq $RepairToken))
    if ($ApplyRepairs -and -not $repairApproved) {
        def_AddRow $Rows "Round2" "VIA" "M06_REPAIR" "GATE" "Repair Approval" "WARN_TOKEN_MISMATCH" "MEDIUM" "SEQUENTIAL_GATED" "REPAIR" "approved" "false" "ApplyRepairs requested but token mismatch; staying dry-run." $BackupDir
    }
    $repairMode = if ($repairApproved) { "APPLY" } else { "DRY_RUN" }

    # PS repair
    if ($HasPSSA -and @($allPs).Count -gt 0) {
        if ($repairApproved) {
            $fixed=0
            foreach ($f in $allPs) {
                try {
                    $d = Invoke-ScriptAnalyzer -Path $f -Severity Error,Warning -ErrorAction SilentlyContinue
                    if (@($d | Where-Object { $null -ne $_.SuggestedCorrections }).Count -gt 0) {
                        Copy-Item -LiteralPath $f -Destination (Join-Path $BackupDir ("PS_" + [System.IO.Path]::GetFileName($f) + ".bak")) -Force
                        Invoke-ScriptAnalyzer -Path $f -Fix -ErrorAction SilentlyContinue | Out-Null
                        $fixed++
                    }
                } catch {}
            }
            def_AddRow $Rows "Round2" "PS" "M06_REPAIR" "PSSA_FIX" "PSScriptAnalyzer -Fix" "OK_REPAIRED" "MEDIUM" "SEQUENTIAL_REQUIRED" "REPAIR_APPLY" "files_fixed" "$fixed" "Auto-fixes applied with per-file backup." $BackupDir
        } else {
            def_AddRow $Rows "Round2" "PS" "M06_REPAIR" "PSSA_FIX" "PSScriptAnalyzer -Fix" "WARN_DRY_RUN" "LOW" "SEQUENTIAL_GATED" "REPAIR_DRYRUN" "fixable" "$psFixable" "Dry-run: fixable rule hits (no write)." $ProjectRoot
        }
    }
    # PY repair
    if (-not [string]::IsNullOrWhiteSpace($Caps.ruff) -and @($allPy).Count -gt 0) {
        if ($repairApproved) {
            foreach ($f in $allPy) { try { Copy-Item -LiteralPath $f -Destination (Join-Path $BackupDir ("PY_" + [System.IO.Path]::GetFileName($f) + ".bak")) -Force } catch {} }
            $rf = def_Proc -FilePath $Caps.ruff -Arguments (@("check","--fix") + @($Roots)) -TimeoutSec 600
            [void](def_Proc -FilePath $Caps.ruff -Arguments (@("format") + @($Roots)) -TimeoutSec 600)
            $st = if ($rf.ExitCode -le 1) { "OK_REPAIRED" } else { "WARN_REPAIR_PARTIAL" }
            def_AddRow $Rows "Round2" "PY" "M06_REPAIR" "RUFF_FIX" "ruff --fix + format" $st "MEDIUM" "SEQUENTIAL_REQUIRED" "REPAIR_APPLY" "exit" "$($rf.ExitCode)" "Ruff auto-fix + format with backup." $BackupDir
        } else {
            def_AddRow $Rows "Round2" "PY" "M06_REPAIR" "RUFF_FIX" "ruff --fix + format" "WARN_DRY_RUN" "LOW" "SEQUENTIAL_GATED" "REPAIR_DRYRUN" "fixable" "$pyFixable" "Dry-run: ruff-fixable findings (no write)." $ProjectRoot
        }
    }
    def_AddRow $Rows "Round2" "VIA" "M06_REPAIR" "SUMMARY" "Repair Mode" "OK_POLICY" "LOW" "SEQUENTIAL_GATED" "REPAIR" "mode" $repairMode "Repair executed in $repairMode mode." $BackupDir

    # ==========================================================================
    # Round 3 . M07 consolidate: per-language grades, registry, report, next-gate
    # ==========================================================================
    def_Phase "Round3 . M07 grades + registry"
    foreach ($lang in @("PS","PY","JS","CS")) {
        $lr = @($Rows | Where-Object { $_.Lang -eq $lang })
        $lo = @($lr | Where-Object { $_.Status -match '^(OK|PASS|READY|CLEAN)' }).Count
        $lw = @($lr | Where-Object { $_.Status -match '^(WARN)' }).Count
        $lf = @($lr | Where-Object { $_.Status -match 'FAIL|FATAL|BLOCK|ERROR' }).Count
        $grade = def_Grade $lo $lw $lf
        $files = switch ($lang) { "PS" { @($allPs).Count } "PY" { @($allPy).Count } "JS" { @($jsPaths).Count } "CS" { @($csPaths).Count } }
        $LangSummary.Add([pscustomobject]@{ lang=$lang; files=$files; ok=$lo; warn=$lw; fail=$lf; grade=$grade }) | Out-Null
    }

    # append-only module registry
    $RegistryFile = Join-Path $RegistryDir "VIA_PolyglotCTR_Registry.json"
    $catalog = @(
        [pscustomobject]@{ id="VPCTR-M01-CORE-000001"; module="M01_CORE"; role="bootstrap/config SSOT" }
        [pscustomobject]@{ id="VPCTR-M02-DETECT-000001"; module="M02_DETECT"; role="capability + source inventory" }
        [pscustomobject]@{ id="VPCTR-M03-INSTALL-000001"; module="M03_INSTALL"; role="one-click checker install" }
        [pscustomobject]@{ id="VPCTR-M04-CHECK-PS-000001"; module="M04_CHECK"; role="PowerShell AST + PSScriptAnalyzer" }
        [pscustomobject]@{ id="VPCTR-M04-CHECK-PY-000001"; module="M04_CHECK"; role="Python compileall + ruff" }
        [pscustomobject]@{ id="VPCTR-M04-CHECK-JS-000001"; module="M04_CHECK"; role="JS/TS node --check" }
        [pscustomobject]@{ id="VPCTR-M04-CHECK-CS-000001"; module="M04_CHECK"; role="C# dotnet format" }
        [pscustomobject]@{ id="VPCTR-M05-TEST-PS-000001"; module="M05_TEST"; role="Pester" }
        [pscustomobject]@{ id="VPCTR-M05-TEST-PY-000001"; module="M05_TEST"; role="pytest" }
        [pscustomobject]@{ id="VPCTR-M06-REPAIR-PS-000001"; module="M06_REPAIR"; role="PSScriptAnalyzer -Fix (guarded)" }
        [pscustomobject]@{ id="VPCTR-M06-REPAIR-PY-000001"; module="M06_REPAIR"; role="ruff --fix + format (guarded)" }
        [pscustomobject]@{ id="VPCTR-M07-REPORT-000001"; module="M07_REPORT"; role="grade + animated HTML + next-gate" }
    )
    $existingReg = @()
    if ([System.IO.File]::Exists($RegistryFile)) { try { $existingReg = @(Get-Content -LiteralPath $RegistryFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { $existingReg = @() } }
    $regIds = @($existingReg | Where-Object { $null -ne $_ -and ($_.PSObject.Properties.Name -contains 'id') } | ForEach-Object { $_.id })
    foreach ($m in $catalog) { if ($regIds -notcontains $m.id) { $existingReg += $m } }
    def_WriteJson -Path $RegistryFile -Obj @($existingReg)
    def_AddRow $Rows "Round3" "VIA" "M07_REPORT" "REGISTRY" "Module Registry" "OK_UPDATED" "LOW" "PARALLEL_SAFE" "PLAN_ONLY" "modules" "$(@($existingReg).Count)" "Append-only M-C-F registry updated." $RegistryFile

    # Top10 local-free libs by function/language (kept)
    $Top10Csv = Join-Path $RunRegDir "VIA_Top10_LocalFreeLibs_$Stamp.csv"
    $Top10 = @(
        [pscustomobject]@{FunctionArea="Check/Lint"; Language="PowerShell"; Libs="PSScriptAnalyzer; AST Parser; PSReadLine; Pester(assert); PlatyPS; PSPesterTest; InjectionHunter; ScriptBlockLogging; PSUseCompatibleSyntax; PSUseCompatibleCmdlets"}
        [pscustomobject]@{FunctionArea="Test"; Language="PowerShell"; Libs="Pester; PSPesterTest; Assert; Selenium-PS; PSKoans; PesterMatchHashtable; PSScriptAnalyzer; Format-Pester; PSGherkin; ThreadJob"}
        [pscustomobject]@{FunctionArea="Check/Lint"; Language="Python"; Libs="ruff; flake8; pylint; mypy; pyflakes; bandit; pycodestyle; pydocstyle; vulture; py_compile"}
        [pscustomobject]@{FunctionArea="Test"; Language="Python"; Libs="pytest; unittest; hypothesis; pytest-xdist; pytest-cov; pytest-mock; tox; nox; coverage; pytest-randomly"}
        [pscustomobject]@{FunctionArea="Check/Lint"; Language="JavaScript/TS"; Libs="eslint; typescript(tsc); biome; oxlint; prettier; jshint; standard; ts-prune; depcheck; madge"}
        [pscustomobject]@{FunctionArea="Test"; Language="JavaScript/TS"; Libs="vitest; jest; mocha; node:test; playwright; cypress; testing-library; c8; nyc; supertest"}
        [pscustomobject]@{FunctionArea="Check/Format"; Language="C#/.NET"; Libs="dotnet format; Roslynator; StyleCop.Analyzers; SonarAnalyzer; Microsoft.CodeAnalysis.NetAnalyzers; ErrorProne.NET; Meziantou.Analyzer; xunit.analyzers; dotnet build -warnAsError; editorconfig"}
        [pscustomobject]@{FunctionArea="Test"; Language="C#/.NET"; Libs="xUnit; NUnit; MSTest; FluentAssertions; Moq; NSubstitute; coverlet; BenchmarkDotNet; bUnit; Verify"}
        [pscustomobject]@{FunctionArea="Repair/Autofix"; Language="Mixed"; Libs="PSScriptAnalyzer -Fix; ruff --fix/format; eslint --fix; prettier -w; dotnet format; black; isort; autopep8; clang-format; editorconfig-checker"}
        [pscustomobject]@{FunctionArea="Report/UI"; Language="JavaScript/HTML"; Libs="Tabulator; DataTables; ECharts; Chart.js; D3.js; Mermaid; Bootstrap; AG Grid Community; DOMPurify; PSWriteHTML"}
    )
    $Top10 | Export-Csv -LiteralPath $Top10Csv -NoTypeInformation -Encoding UTF8BOM
    def_AddRow $Rows "Round3" "VIA" "M07_REPORT" "TOP10" "Top10 Local Free Libs" "OK_CREATED" "LOW" "PARALLEL_SAFE" "PLAN_ONLY" "rows" "$(@($Top10).Count)" "Check/test/repair libs by function/language." $Top10Csv

    $OverallGrade = def_Grade $script:OK $script:WARN $script:FAIL
    $Status = if ($script:FAIL -eq 0) { "VIA_POLYGLOT_CTR_HEALTHY" } else { "VIA_POLYGLOT_CTR_FINDINGS" }
    $NextStep = if ($script:FAIL -eq 0) { "no red findings; optionally run with -ApplyRepairs + token to apply safe autofixes" } else { "address red findings (parse/lint errors, failing tests); rerun; then -ApplyRepairs to autofix" }

    def_Phase "Round3 . M07 matrix + animated HTML"
    $CsvMatrix = Join-Path $RunRegDir "VIA_PolyglotCTR_Matrix_$Stamp.csv"
    $JsonMatrix = Join-Path $RunRegDir "VIA_PolyglotCTR_Matrix_$Stamp.json"
    $RuntimeResultJson = Join-Path $RuntimeDir "via_polyglot_ctr_result_$Stamp.json"
    $HtmlReport = Join-Path $ReportDir "VIA_PolyglotCTR_Report_$Stamp.html"
    $Rows | Export-Csv -LiteralPath $CsvMatrix -NoTypeInformation -Encoding UTF8BOM
    def_WriteJson -Path $JsonMatrix -Obj @($Rows)
    def_WriteJson -Path $RuntimeResultJson -Obj ([pscustomobject]@{
        generated_at=def_Iso; status=$Status; overall_grade=$OverallGrade
        ok=$script:OK; warn=$script:WARN; fail=$script:FAIL
        files_scanned=$fileCount; languages=@($LangSummary)
        repair_mode=$repairMode; run_tests=$RunTests
        db_write=$false; canonical_merge=$false; destructive_delete=$false
        system_root=$SysRoot; registry=$RegistryFile; next_step=$NextStep
    })

    $Total = [Math]::Max(1, ($script:OK + $script:WARN + $script:FAIL))
    $OkPct = [Math]::Round((($script:OK / $Total) * 100), 1)
    $WarnPct = [Math]::Round((($script:WARN / $Total) * 100), 1)
    $FailPct = [Math]::Round((($script:FAIL / $Total) * 100), 1)

    $cards = foreach ($s in $LangSummary) {
        $gc = switch ($s.grade) { "A" { "#2f9e6f" } "B" { "#4c78a8" } "C" { "#caa14a" } "D" { "#cf8a3b" } "E" { "#b4564f" } "F" { "#9b3a34" } default { "#9c9890" } }
        "<div class='card'><div class='cl'>$(def_Html $s.lang)</div><div class='cg' style='color:$gc'>$(def_Html $s.grade)</div><div class='cm'>files $($s.files) . ok $($s.ok) . warn $($s.warn) . fail $($s.fail)</div></div>"
    }
    $trs = foreach ($r in $Rows) {
        $cls = if ($r.Status -match 'FAIL|FATAL|BLOCK|ERROR') { "bad" } elseif ($r.Status -match '^(OK|PASS|READY|CLEAN)') { "ok" } else { "warn" }
        "<tr class='$cls'><td>$(def_Html $r.Round)</td><td>$(def_Html $r.Lang)</td><td>$(def_Html $r.Module)</td><td>$(def_Html $r.Stage)</td><td>$(def_Html $r.Name)</td><td>$(def_Html $r.Status)</td><td>$(def_Html $r.Risk)</td><td>$(def_Html $r.FixClass)</td><td>$(def_Html $r.Mode)</td><td>$(def_Html $r.Metric)</td><td>$(def_Html $r.Value)</td><td>$(def_Html $r.Message)</td></tr>"
    }

    $Html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Polyglot Check-Test-Repair v01.1</title>
<style>
body{margin:0;background:#f7f4ed;color:#25312f;font-family:Arial,"Microsoft JhengHei",sans-serif}
.wrap{max-width:1640px;margin:0 auto;padding:28px}
.hero{border:1px solid #d8d0c3;border-radius:24px;background:#fffdf8;padding:26px;box-shadow:0 18px 50px rgba(30,40,36,.08)}
h1{margin:0;font-size:25px}h2{margin-top:28px;font-size:20px}.sub{color:#6e7b78;margin-top:8px;line-height:1.7}
.badge{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid #d8d0c3;background:#fff;margin-right:8px;margin-top:8px}
.prog{margin-top:20px}.plabel{font-size:13px;color:#6e7b78;margin-bottom:6px}
.pbar{height:16px;border-radius:999px;background:#e8e1d6;overflow:hidden}
.pfill{height:100%;width:0%;border-radius:999px;background:linear-gradient(90deg,#439a9a,#4c78a8);background-size:200% 100%;transition:width 1.4s cubic-bezier(.2,.8,.2,1);animation:sh 2.4s linear infinite}
@keyframes sh{0%{background-position:200% 0}100%{background-position:-200% 0}}
.stack{display:flex;height:16px;border-radius:999px;overflow:hidden;margin-top:10px;border:1px solid #d8d0c3}
.s-ok{background:#439a9a;transition:width 1.4s ease}.s-warn{background:#caa14a;transition:width 1.4s ease}.s-bad{background:#b4564f;transition:width 1.4s ease}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:18px}
.card{border:1px solid #d8d0c3;border-radius:18px;background:#fff;padding:16px;text-align:center}
.cl{font-size:13px;color:#6e7b78}.cg{font-size:40px;font-weight:700;line-height:1}.cm{font-size:11px;color:#6e7b78;margin-top:8px}
.ok td{background:#f3fbf5}.warn td{background:#fff8e9}.bad td{background:#fff1f1}
.mw{overflow:auto;border:1px solid #d8d0c3;border-radius:18px;background:#fff;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:12px}
th{position:sticky;top:0;background:#e8eee9;color:#20332f;z-index:1}
th,td{border-bottom:1px solid #e8e1d6;padding:9px 10px;text-align:left;vertical-align:top;white-space:nowrap}
td:nth-child(12){white-space:normal;min-width:340px}
pre{white-space:pre-wrap;background:#17211f;color:#e9fff8;padding:16px;border-radius:16px;overflow:auto}
@media(max-width:900px){.cards{grid-template-columns:1fr 1fr}.wrap{padding:14px}}
</style>
</head>
<body>
<div class="wrap">
<div class="hero">
<h1>VIA Polyglot Check-Test-Repair System v01.1</h1>
<div class="sub">PS / Python / JS-TS / C# . one-click checker install . 3-round (check -> test -> repair) . repair guarded (dry-run default) . no DB write . append-only</div>
<p><span class="badge">Overall grade: $OverallGrade</span><span class="badge">Status: $(def_Html $Status)</span><span class="badge">Repair mode: $repairMode</span></p>
<div class="prog">
<div class="plabel">Pipeline completion</div>
<div class="pbar"><div class="pfill" id="pfill"></div></div>
<div class="stack" title="OK / WARN / FAIL">
<div class="s-ok" id="sok" style="width:0%"></div>
<div class="s-warn" id="swarn" style="width:0%"></div>
<div class="s-bad" id="sbad" style="width:0%"></div>
</div>
</div>
<div class="cards">$($cards -join "")</div>
</div>

<h2>def Matrix</h2>
<div class="mw">
<table>
<thead><tr><th>Round</th><th>Lang</th><th>Module</th><th>Stage</th><th>Name</th><th>Status</th><th>Risk</th><th>FixClass</th><th>Mode</th><th>Metric</th><th>Value</th><th>Message</th></tr></thead>
<tbody>$($trs -join "`n")</tbody>
</table>
</div>

<h2>def System + Next</h2>
<pre>
System Root   : $SysRoot
Config SSOT   : $ConfigFile
Registry      : $RegistryFile
Run Root      : $RunRoot
HTML          : $HtmlReport
Matrix CSV    : $CsvMatrix
Result JSON   : $RuntimeResultJson
Capability    : $CapCsv
Top10 Libs    : $Top10Csv

Overall grade : $OverallGrade   OK=$script:OK WARN=$script:WARN FAIL=$script:FAIL
Repair mode   : $repairMode   (apply needs -ApplyRepairs -ApprovalToken "$RepairToken")
Next step     : $NextStep

Policy: DB write=false . canonical merge=false . destructive delete=false . stop-process=false . append-only
</pre>
</div>
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    document.getElementById('pfill').style.width='100%';
    document.getElementById('sok').style.width='$OkPct%';
    document.getElementById('swarn').style.width='$WarnPct%';
    document.getElementById('sbad').style.width='$FailPct%';
  },180);
});
</script>
</body>
</html>
"@
    def_WriteText -Path $HtmlReport -Text $Html

    Write-Progress -Id 1 -Completed
    if ($OpenHtmlReport -and (Test-Path -LiteralPath $HtmlReport)) { Start-Process -FilePath $HtmlReport | Out-Null }
    try { Stop-Transcript | Out-Null } catch {}

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA POLYGLOT CHECK-TEST-REPAIR v01.1 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "System Root     : $SysRoot"
    Write-Host "HTML            : $HtmlReport"
    Write-Host "Registry        : $RegistryFile"
    Write-Host "Overall Grade   : $OverallGrade"
    foreach ($s in $LangSummary) { Write-Host ("  {0,-3} grade {1}  files {2}  ok {3}  warn {4}  fail {5}" -f $s.lang,$s.grade,$s.files,$s.ok,$s.warn,$s.fail) }
    Write-Host "OK / WARN / FAIL: $script:OK / $script:WARN / $script:FAIL"
    Write-Host "Repair Mode     : $repairMode"
    Write-Host "Next Step       : $NextStep"
    Write-Host ""
    Write-Host "PowerShell remains open. No exit. No Stop-Process. No destructive delete." -ForegroundColor Green
}

try {
    Invoke-VIA-PolyglotCheckTestRepair-v0101
}
catch {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "def VIA POLYGLOT CTR v01.1 FATAL BUT POWERSHELL STAYS OPEN" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
