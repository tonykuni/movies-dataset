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
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",

    [Parameter(Mandatory = $false)]
    [string]$Engine = (Join-Path $PSScriptRoot "VIA_CentralGovernment_AdaptiveDownstream_v0100.py"),

    [Parameter(Mandatory = $false)]
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA "VIA\CentralGovernanceRuns"),

    [Parameter(Mandatory = $false)]
    [ValidateSet("AUDIT", "STAGE")]
    [string]$Mode = "STAGE",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 64)]
    [int]$MaxWorkers = 12,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 64)]
    [int]$MaxDepth = 24,

    [Parameter(Mandatory = $false)]
    [switch]$NoIncremental,

    [Parameter(Mandatory = $false)]
    [switch]$SkipSelfTest,

    [Parameter(Mandatory = $false)]
    [switch]$DoNotOpenHtml
)

# =============================================================================
# def PARAMETERS / GOVERNANCE CONSTANTS
# =============================================================================
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$def_PARAM_TITLE = "VIA Central Government · Adaptive Downstream Governance v0100"
$def_PARAM_MUTEX_NAME = "Local\VIA_CG_ADAPTIVE_DOWNSTREAM_V0100"
$def_PARAM_ROUNDS = 3
$def_PARAM_POLICY = "read-only canonical / append-only run-local / no network / no install / no activation / no target import"
$def_PARAM_PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
    "C:\VeritasIntelligenceAnalytics\Environments\via_core\Scripts\python.exe"
)

# =============================================================================
# def CONSOLE HELPERS
# =============================================================================
function def_WriteBanner {
    param([Parameter(Mandatory = $true)][string]$Title)
    Write-Host ""
    Write-Host ("=" * 104) -ForegroundColor DarkCyan
    Write-Host ("def " + $Title) -ForegroundColor Cyan
    Write-Host ("=" * 104) -ForegroundColor DarkCyan
}

function def_WriteStep {
    param(
        [Parameter(Mandatory = $true)][ValidateRange(0, 100)][int]$Percent,
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $false)][ValidateSet("INFO", "PASS", "WARN", "FAIL")][string]$Status = "INFO"
    )
    $def_Width = 24
    $def_Filled = [Math]::Floor(($Percent / 100.0) * $def_Width)
    $def_Empty = $def_Width - $def_Filled
    $def_Bar = ("█" * $def_Filled) + ("░" * $def_Empty)
    $def_Color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        default { "Cyan" }
    }
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $Percent, $def_Bar, $Status, $Message) -ForegroundColor $def_Color
}

function def_WriteKeyValue {
    param(
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $false)][AllowNull()][object]$Value,
        [Parameter(Mandatory = $false)][ConsoleColor]$Color = [ConsoleColor]::White
    )
    Write-Host ("def {0,-22}: {1}" -f $Key, [string]$Value) -ForegroundColor $Color
}

# =============================================================================
# def NATIVE POWERSHELL AST SELF-CHECK
# =============================================================================
function def_ValidatePowerShellAst {
    param([Parameter(Mandatory = $true)][string]$ScriptPath)
    $def_Tokens = $null
    $def_Errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $ScriptPath,
        [ref]$def_Tokens,
        [ref]$def_Errors
    ) | Out-Null
    if ($null -ne $def_Errors -and $def_Errors.Count -gt 0) {
        $def_Messages = ($def_Errors | ForEach-Object { $_.Message }) -join " | "
        throw "PowerShell AST validation failed: $def_Messages"
    }
    return [pscustomobject]@{ TokenCount = @($def_Tokens).Count; ErrorCount = 0 }
}

# =============================================================================
# def PATH / ENVIRONMENT RESOLUTION
# =============================================================================
function def_ResolvePython {
    foreach ($def_Candidate in $def_PARAM_PYTHON_CANDIDATES) {
        if (Test-Path -LiteralPath $def_Candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $def_Candidate).Path
        }
    }

    foreach ($def_Name in @("python", "py")) {
        $def_Command = Get-Command $def_Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $def_Command) {
            return $def_Command.Source
        }
    }

    throw "Governed Python was not found. Checked via_core_312, via_core, python and py."
}

function def_AssertSafePaths {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$EnginePath,
        [Parameter(Mandatory = $true)][string]$RunOutputRoot
    )

    if (-not (Test-Path -LiteralPath $RootPath -PathType Container)) {
        throw "Mother Root not found: $RootPath"
    }
    if ($RootPath -match "(?i)OneDrive") {
        throw "Mother Root cannot be OneDrive under VIA governance policy: $RootPath"
    }
    if (-not (Test-Path -LiteralPath $EnginePath -PathType Leaf)) {
        throw "Adaptive engine not found: $EnginePath"
    }

    $def_ResolvedRoot = (Resolve-Path -LiteralPath $RootPath).Path
    $def_ResolvedEngine = (Resolve-Path -LiteralPath $EnginePath).Path
    $def_OutputPath = [System.IO.Path]::GetFullPath($RunOutputRoot)

    if ($def_OutputPath.StartsWith($def_ResolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Host "def NOTE: OutputRoot is below Mother Root; engine will exclude its own run directories." -ForegroundColor Yellow
    }

    [System.IO.Directory]::CreateDirectory($def_OutputPath) | Out-Null
    return [pscustomobject]@{
        Root = $def_ResolvedRoot
        Engine = $def_ResolvedEngine
        OutputRoot = $def_OutputPath
    }
}

# =============================================================================
# def PROCESS EXECUTION — NO SHELL STRING / NO TARGET IMPORT
# =============================================================================
function def_InvokePythonProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $def_StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $def_StartInfo.FileName = $Python
    $def_StartInfo.UseShellExecute = $false
    $def_StartInfo.RedirectStandardOutput = $true
    $def_StartInfo.RedirectStandardError = $true
    $def_StartInfo.CreateNoWindow = $true
    $def_StartInfo.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $def_StartInfo.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)

    foreach ($def_Argument in $Arguments) {
        $def_StartInfo.ArgumentList.Add([string]$def_Argument)
    }

    $def_Process = [System.Diagnostics.Process]::new()
    $def_Process.StartInfo = $def_StartInfo
    if (-not $def_Process.Start()) {
        throw "Unable to start governed Python process."
    }

    $def_StdOutTask = $def_Process.StandardOutput.ReadToEndAsync()
    $def_StdErrTask = $def_Process.StandardError.ReadToEndAsync()
    $def_Process.WaitForExit()
    $def_StdOut = $def_StdOutTask.GetAwaiter().GetResult()
    $def_StdErr = $def_StdErrTask.GetAwaiter().GetResult()

    return [pscustomobject]@{
        ExitCode = $def_Process.ExitCode
        StdOut = $def_StdOut
        StdErr = $def_StdErr
    }
}

function def_ParseJsonOutput {
    param([Parameter(Mandatory = $true)][string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) {
        throw "Python returned no JSON output."
    }
    try {
        return ($Text | ConvertFrom-Json -Depth 100)
    }
    catch {
        throw "Python output is not valid JSON: $($_.Exception.Message)`n$Text"
    }
}

# =============================================================================
# def SELF TEST / GOVERNANCE RUN
# =============================================================================
function def_RunSelfTest {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string]$EnginePath
    )
    $def_Result = def_InvokePythonProcess -Python $Python -Arguments @($EnginePath, "selftest")
    $def_Payload = def_ParseJsonOutput -Text $def_Result.StdOut
    if ($def_Result.ExitCode -ne 0 -or -not [bool]$def_Payload.ok) {
        throw "Engine self-test failed. ExitCode=$($def_Result.ExitCode)`n$($def_Result.StdErr)`n$($def_Result.StdOut)"
    }
    return $def_Payload
}

function def_RunGovernance {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string]$EnginePath,
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$RunOutputRoot,
        [Parameter(Mandatory = $true)][string]$RunMode,
        [Parameter(Mandatory = $true)][int]$Workers,
        [Parameter(Mandatory = $true)][int]$Depth,
        [Parameter(Mandatory = $true)][bool]$Incremental
    )

    $def_Arguments = @(
        $EnginePath,
        "run",
        "--root", $RootPath,
        "--output-root", $RunOutputRoot,
        "--mode", $RunMode,
        "--rounds", [string]$def_PARAM_ROUNDS,
        "--max-workers", [string]$Workers,
        "--max-depth", [string]$Depth
    )
    if (-not $Incremental) {
        $def_Arguments += "--no-incremental"
    }

    $def_Result = def_InvokePythonProcess -Python $Python -Arguments $def_Arguments
    $def_Payload = def_ParseJsonOutput -Text $def_Result.StdOut
    if ($def_Result.ExitCode -notin @(0)) {
        throw "Governance engine returned ExitCode=$($def_Result.ExitCode)`n$($def_Result.StdErr)`n$($def_Result.StdOut)"
    }
    return $def_Payload
}

function def_OpenFinalHtml {
    param([Parameter(Mandatory = $true)][object]$Summary)
    if ($DoNotOpenHtml) {
        return
    }
    $def_Html = [string]$Summary.final_html
    if (-not [string]::IsNullOrWhiteSpace($def_Html) -and (Test-Path -LiteralPath $def_Html -PathType Leaf)) {
        Start-Process -FilePath $def_Html | Out-Null
    }
}

# =============================================================================
# def MAIN — HASH-SAFE / SINGLE INSTANCE / POWER SHELL REMAINS OPEN
# =============================================================================
function def_Main {
    def_WriteBanner -Title $def_PARAM_TITLE
    def_WriteStep -Percent 3 -Message "Acquire single-instance governance mutex" -Status "INFO"

    $def_CreatedNew = $false
    $def_Mutex = [System.Threading.Mutex]::new($false, $def_PARAM_MUTEX_NAME, [ref]$def_CreatedNew)
    $def_LockAcquired = $false
    try {
        try {
            $def_LockAcquired = $def_Mutex.WaitOne(0)
        }
        catch [System.Threading.AbandonedMutexException] {
            $def_LockAcquired = $true
        }
        if (-not $def_LockAcquired) {
            def_WriteStep -Percent 100 -Message "Another VIA Central Government run is already active; duplicate execution skipped." -Status "WARN"
            return [pscustomobject]@{ Gate = "DUPLICATE_EXECUTION_SKIPPED"; ExitCode = 0 }
        }

        def_WriteStep -Percent 8 -Message "Validate launcher AST, Mother Root, engine and run-local output path" -Status "INFO"
        if (-not [string]::IsNullOrWhiteSpace($PSCommandPath) -and (Test-Path -LiteralPath $PSCommandPath -PathType Leaf)) {
            $def_Ast = def_ValidatePowerShellAst -ScriptPath $PSCommandPath
            def_WriteKeyValue -Key "PowerShell AST" -Value ("PASS · tokens=" + $def_Ast.TokenCount) -Color Green
        }
        $def_Paths = def_AssertSafePaths -RootPath $Root -EnginePath $Engine -RunOutputRoot $OutputRoot
        $def_Python = def_ResolvePython
        $def_EngineHash = (Get-FileHash -LiteralPath $def_Paths.Engine -Algorithm SHA256).Hash.ToLowerInvariant()

        def_WriteKeyValue -Key "Policy" -Value $def_PARAM_POLICY -Color Yellow
        def_WriteKeyValue -Key "Mother Root" -Value $def_Paths.Root
        def_WriteKeyValue -Key "Python" -Value $def_Python
        def_WriteKeyValue -Key "Engine" -Value $def_Paths.Engine
        def_WriteKeyValue -Key "Engine SHA256" -Value $def_EngineHash
        def_WriteKeyValue -Key "Output Root" -Value $def_Paths.OutputRoot
        def_WriteKeyValue -Key "Mode" -Value $Mode

        if (-not $SkipSelfTest) {
            def_WriteStep -Percent 15 -Message "Run engine self-test before project scan" -Status "INFO"
            $def_SelfTest = def_RunSelfTest -Python $def_Python -EnginePath $def_Paths.Engine
            def_WriteStep -Percent 23 -Message ("Self-test PASS {0}/{1}" -f $def_SelfTest.passed.Count, $def_SelfTest.total) -Status "PASS"
        }
        else {
            def_WriteStep -Percent 23 -Message "Self-test skipped by operator switch" -Status "WARN"
        }

        def_WriteStep -Percent 31 -Message "Round 1 · full discovery, AST, contract, Hydra and parallel-safe overlay" -Status "INFO"
        def_WriteStep -Percent 52 -Message "Round 2 · dependency-ordered sidecars and interface governance" -Status "INFO"
        def_WriteStep -Percent 72 -Message "Round 3 · re-analysis, verification and stability hardening" -Status "INFO"

        $def_Summary = def_RunGovernance `
            -Python $def_Python `
            -EnginePath $def_Paths.Engine `
            -RootPath $def_Paths.Root `
            -RunOutputRoot $def_Paths.OutputRoot `
            -RunMode $Mode `
            -Workers $MaxWorkers `
            -Depth $MaxDepth `
            -Incremental (-not $NoIncremental)

        $def_Status = if ([string]$def_Summary.gate -eq "READY_FOR_MANUAL_USER_TEST_REVIEW") { "PASS" } else { "WARN" }
        def_WriteStep -Percent 92 -Message ("Governance gate: {0}" -f $def_Summary.gate) -Status $def_Status
        def_WriteKeyValue -Key "Assets" -Value $def_Summary.assets
        def_WriteKeyValue -Key "Open Issues" -Value $def_Summary.issues_open
        def_WriteKeyValue -Key "Overlay Resolved" -Value $def_Summary.issues_resolved_in_overlay
        def_WriteKeyValue -Key "Unresolved High" -Value $def_Summary.unresolved_high
        def_WriteKeyValue -Key "Patches" -Value $def_Summary.patches
        def_WriteKeyValue -Key "Activation" -Value $def_Summary.activation -Color Yellow
        def_WriteKeyValue -Key "Canonical Mutation" -Value $def_Summary.canonical_mutation -Color Green
        def_WriteKeyValue -Key "Final HTML" -Value $def_Summary.final_html
        def_WriteKeyValue -Key "Run Dir" -Value $def_Summary.run_dir

        def_OpenFinalHtml -Summary $def_Summary
        def_WriteStep -Percent 100 -Message "Three-round governance cycle completed; PowerShell remains open." -Status $def_Status
        return $def_Summary
    }
    finally {
        if ($def_LockAcquired) {
            try { $def_Mutex.ReleaseMutex() } catch { }
        }
        if ($null -ne $def_Mutex) {
            $def_Mutex.Dispose()
        }
    }
}

$global:VIA_CG_LastExitCode = 0
$global:VIA_CG_LastResult = $null
try {
    $global:VIA_CG_LastResult = def_Main
}
catch {
    $global:VIA_CG_LastExitCode = 1
    Write-Host ""
    Write-Host ("def FATAL: " + $_.Exception.Message) -ForegroundColor Red
    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    }
    Write-Host "def PowerShell remains open. No canonical mutation, install, activation, target import or network action was executed." -ForegroundColor Yellow
}
