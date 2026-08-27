#requires -Version 7.0
<#
.SYNOPSIS
    Invoke-VIA-NexusToolBridge-Unified v0.2 - one paste-and-run PS7 tool-bridge engine.
.DESCRIPTION
    Integrates the strengths of four prior scripts and engineers out their weaknesses:

      from RedFindingStabilizer v0122 : ProcessStartInfo invoke (async + kill-on-timeout),
                                        child-process AST parse fallback, Hydra parse-gate,
                                        approval-token-gated repairs, dry analyzers.
      from ToolBridge AIO v0.1        : 10-accelerator matrix, reusable .psm1 + .json bridge
                                        generation, module cache-first install/import.
      from Panorama 3-Round Gate      : Nexus bridge manifest (sha256 inventory of supportive +
                                        functional items), supportive-module activation
                                        (Read_Me parse + NexusCore + Polyglot via child process).

    Removed weaknesses (all four had some of these):
      * Start-Process for subprocesses -> replaced everywhere by ProcessStartInfo
        (Start-Process is used ONLY to open the final HTML report).
      * inline $(if(){}else{}) sub-expressions -> precomputed values / helper.
      * Set-Content -> [IO.File]::WriteAllText (HTML/JSON/PSM1 UTF-8 no-BOM; CSV UTF-8 BOM for Excel).
      * uncuddled else/elseif -> cuddled / switch.
      * light-theme HTML -> Visual Lock (DM Mono/DM Sans/Syne, blue/grey/teal, UP=red/DOWN=green).

    Methodology: 3-round panoramic (Round0 inventory -> Round1 import -> Round2 analyze/gate ->
    Round3 bridge/classify -> finalize). Default is analyze + import modules + invoke supportive
    (child-isolated) + generate bridge. Repairs are NEVER applied unless -ApplyRepairsSwitch AND
    -ApprovalToken match AND no parse blocker remains. Append-only: every run is an isolated folder.

    LL-compliant: param first, [IO.File]::WriteAllText, no aliases, cuddled else/catch,
    ProcessStartInfo (no Start-Job / no Start-Process for subprocess), no exit in main,
    Write-Progress -Id 1, [System.Net.WebUtility]::HtmlEncode, Start-Process only for the report.
#>

param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$ToolRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_NexusToolBridge",
    [switch]$NoNetworkInstallSwitch,
    [switch]$NoInvokeSupportiveSwitch,
    [switch]$ApplyRepairsSwitch,
    [string]$ApprovalToken = "",
    [switch]$NoOpenReportSwitch,
    [int]$TimeoutSec = 300
)

# =============================================================================
# def POLICY / STATE
# =============================================================================
$script:def_RunId       = "RUN_{0}_VIA_NEXUS_TOOLBRIDGE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$script:def_StartTime   = Get-Date
$script:def_DoInstall   = -not [bool]$NoNetworkInstallSwitch
$script:def_DoInvoke    = -not [bool]$NoInvokeSupportiveSwitch
$script:def_ApprovalRequired = "APPROVE_VIA_NEXUS_TOOLBRIDGE_REPAIR"
$script:def_Utf8NoBom   = [System.Text.UTF8Encoding]::new($false)
$script:def_Utf8Bom     = [System.Text.UTF8Encoding]::new($true)

$script:def_RunRoot   = Join-Path $ToolRoot ("runs\" + $script:def_RunId)
$script:def_RegistryDir = Join-Path $script:def_RunRoot "registry"
$script:def_LogDir    = Join-Path $script:def_RunRoot "logs"
$script:def_ReportDir = Join-Path $script:def_RunRoot "report"
$script:def_RuntimeDir = Join-Path $script:def_RunRoot "runtime"
$script:def_BridgeDir = Join-Path $ToolRoot "bridge"

$script:def_MatrixCsv  = Join-Path $script:def_RegistryDir "VIA_NexusToolBridge_Matrix.csv"
$script:def_MatrixJson = Join-Path $script:def_RegistryDir "VIA_NexusToolBridge_Matrix.json"
$script:def_ReportHtml = Join-Path $script:def_ReportDir "VIA_NexusToolBridge_Report.html"
$script:def_BridgePsm1 = Join-Path $script:def_BridgeDir "VIA_NexusToolBridge.psm1"
$script:def_BridgeJson = Join-Path $script:def_BridgeDir "VIA_NexusToolBridge.json"

$script:def_Rows = [System.Collections.Generic.List[object]]::new()

# Visual Lock (VPN v3.5)
$script:def_ColBlue = '#4c78a8'
$script:def_ColGrey = '#9c9890'
$script:def_ColTeal = '#439a9a'
$script:def_ColUp   = '#c96b5a'   # RED   = fail / high risk
$script:def_ColDown = '#5a9e6f'   # GREEN = ok / applied

$script:def_Policy = [ordered]@{
    db_write           = $false
    canonical_merge    = $false
    destructive_delete = $false
    stop_process       = $false
    append_only        = $true
    repair_mode        = "DRY_RUN"
    network_install    = $script:def_DoInstall
    invoke_supportive  = $script:def_DoInvoke
}

# Three supportive modules that MUST be imported (Tony's explicit requirement)
$script:def_SupportiveFiles = @(
    [pscustomobject]@{ Name = "Read_Me_VeritasNexusCore.md"; Kind = "doc"; Invoke = $false }
    [pscustomobject]@{ Name = "Invoke-VeritasNexusCore.ps1"; Kind = "ps"; Invoke = $true }
    [pscustomobject]@{ Name = "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"; Kind = "ps"; Invoke = $true }
)

# Network/local PS modules to install (cache-first) and import
$script:def_PsModules = @(
    [pscustomobject]@{ Name = "PSScriptAnalyzer"; Required = $true;  Purpose = "PowerShell static analysis / safe -Fix" }
    [pscustomobject]@{ Name = "Pester";           Required = $true;  Purpose = "test runner" }
    [pscustomobject]@{ Name = "PSWriteHTML";      Required = $false; Purpose = "optional HTML helpers" }
    [pscustomobject]@{ Name = "ImportExcel";      Required = $false; Purpose = "CSV/XLSX review" }
    [pscustomobject]@{ Name = "PSFramework";      Required = $false; Purpose = "structured logging" }
)

$script:def_NativeTools = @("pwsh", "python", "py", "pip", "git", "winget", "ruff")

# 10 accelerators (carried from ToolBridge AIO, each realized in this engine)
$script:def_Accelerators = @(
    [pscustomobject]@{ ID = "A01"; Name = "Run Isolation";      Detail = "Each run writes into an isolated append-only run folder." }
    [pscustomobject]@{ ID = "A02"; Name = "Timeout Guard";      Detail = "Child processes run via ProcessStartInfo with timeout + kill; parent never hangs." }
    [pscustomobject]@{ ID = "A03"; Name = "AST Before Invoke";  Detail = "PS files are parse-checked (child-process fallback) before being trusted." }
    [pscustomobject]@{ ID = "A04"; Name = "Module Cache First"; Detail = "Installed modules detected before any network install." }
    [pscustomobject]@{ ID = "A05"; Name = "Network Retry Lite"; Detail = "Install failure becomes WARN, not fatal; engine continues." }
    [pscustomobject]@{ ID = "A06"; Name = "Hash Inventory";     Detail = "SHA256 records guard against uncontrolled overwrite." }
    [pscustomobject]@{ ID = "A07"; Name = "Bridge Wrapper";     Detail = "Other scripts import one stable .psm1 instead of raw tool paths." }
    [pscustomobject]@{ ID = "A08"; Name = "Low-Memory Scan";    Detail = "Streaming file inventory avoids loading the whole tree." }
    [pscustomobject]@{ ID = "A09"; Name = "Hydra Gate";         Detail = "Parse errors block broad autofix; parallel-safe split from sequential." }
    [pscustomobject]@{ ID = "A10"; Name = "HTML Matrix";        Detail = "Every phase emits CSV/JSON/HTML for review and later integration." }
)

$script:def_PsExt = @(".ps1", ".psm1", ".psd1")
$script:def_ExcludeDirs = @(".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", ".next", "dist", "build", ".venv", "venv", "_envs", "env", "site-packages")
$script:def_ExcludePathRegex = @("\\tools\\VIA_NexusToolBridge\\runs\\", "\\tools\\VIA_PolyglotCTR\\runs\\", "\\_vdf_system\\")

# =============================================================================
# def CORE HELPERS
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

function def_WriteLog {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("HH:mm:ss.fff")
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
    Write-Progress -Id 1 -Activity "VIA Nexus ToolBridge Unified v0.2" -Status $Status -PercentComplete $pct
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    if ($InputObject -is [array]) { return $InputObject.Count }
    return 1
}

function def_AsArraySafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return @() }
    return @($InputObject)
}

function def_GetSha256 {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
        return ""
    } catch {
        return ""
    }
}

function def_AddRow {
    param(
        [string]$Round, [string]$Layer, [string]$Name, [string]$Status,
        [string]$Risk, [string]$Class, [string]$Priority, [string]$Metric,
        [object]$Value, [string]$Message, [string]$Path = ""
    )
    $row = [pscustomobject]@{
        Time     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Round    = $Round
        Layer    = $Layer
        Name     = $Name
        Status   = $Status
        Risk     = $Risk
        Class    = $Class
        Priority = $Priority
        Metric   = $Metric
        Value    = [string]$Value
        Message  = $Message
        Path     = $Path
    }
    $script:def_Rows.Add($row) | Out-Null
}

# LL-compliant subprocess invocation: ProcessStartInfo + async read + kill-on-timeout.
function def_InvokeProcess {
    param(
        [string]$Name, [string]$FilePath, [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = "", [int]$TimeoutSeconds = 300
    )
    def_EnsureDir -Path $script:def_LogDir
    $safe = ($Name -replace '[^\w\.\-]+', '_')
    $stdoutPath = Join-Path $script:def_LogDir ("{0}.stdout.txt" -f $safe)
    $stderrPath = Join-Path $script:def_LogDir ("{0}.stderr.txt" -f $safe)
    if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) { $WorkingDirectory = $Root }

    if (-not (Test-Path -LiteralPath $FilePath) -and -not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ Name = $Name; ExitCode = -999; TimedOut = $false; Stdout = $stdoutPath; Stderr = $stderrPath; Message = "Executable not found." }
    }

    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $FilePath
        foreach ($a in $ArgumentList) { [void]$psi.ArgumentList.Add($a) }
        $psi.WorkingDirectory = $WorkingDirectory
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        $p = [System.Diagnostics.Process]::new()
        $p.StartInfo = $psi
        [void]$p.Start()
        $outTask = $p.StandardOutput.ReadToEndAsync()
        $errTask = $p.StandardError.ReadToEndAsync()
        $finished = $p.WaitForExit($TimeoutSeconds * 1000)
        if (-not $finished) {
            try { $p.Kill($true) } catch { }
            def_SaveText -Path $stdoutPath -Text $outTask.Result
            def_SaveText -Path $stderrPath -Text (($errTask.Result) + "`nTIMEOUT after $TimeoutSeconds sec (child killed).")
            return [pscustomobject]@{ Name = $Name; ExitCode = 124; TimedOut = $true; Stdout = $stdoutPath; Stderr = $stderrPath; Message = "Timeout; child killed." }
        }
        def_SaveText -Path $stdoutPath -Text $outTask.Result
        def_SaveText -Path $stderrPath -Text $errTask.Result
        return [pscustomobject]@{ Name = $Name; ExitCode = $p.ExitCode; TimedOut = $false; Stdout = $stdoutPath; Stderr = $stderrPath; Message = "Completed." }
    } catch {
        return [pscustomobject]@{ Name = $Name; ExitCode = -998; TimedOut = $false; Stdout = $stdoutPath; Stderr = $stderrPath; Message = $_.Exception.Message }
    }
}

function def_GetPwsh {
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd2 = Get-Command powershell -ErrorAction SilentlyContinue
    if ($cmd2) { return $cmd2.Source }
    return $null
}

function def_GetPython {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd2 = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd2) { return $cmd2.Source }
    return $null
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
    param([string[]]$Extensions)
    $all = Get-ChildItem -LiteralPath $Root -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $ext = $_.Extension.ToLowerInvariant()
            ($Extensions -contains $ext) -and (-not (def_IsExcludedPath -Path $_.FullName))
        }
    return @($all)
}

# =============================================================================
# def AST PARSE (child-process fallback, carried from RedFindingStabilizer v0122)
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

function def_ToSafeLogName {
    param([string]$Text)
    $safe = $Text -replace '[:\\/\*\?"<>\|\s]+', '_'
    if ($safe.Length -gt 90) { $safe = $safe.Substring($safe.Length - 90) }
    return $safe
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
        # parent parser itself failed: fall back to an isolated child process
        $parentError = $_.Exception.Message
        $pwsh = def_GetPwsh
        if ($null -eq $pwsh) {
            return @([pscustomobject]@{ Path = $File.FullName; File = $File.Name; Line = 0; Column = 0; ErrorId = "NoPwsh"; Message = $parentError })
        }
        $childParser = def_GetChildParserScript
        $safe = def_ToSafeLogName -Text $File.FullName
        $res = def_InvokeProcess -Name ("ps_ast_child_{0}" -f $safe) -FilePath $pwsh -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $childParser, $File.FullName) -WorkingDirectory $Root -TimeoutSeconds 120
        $jsonText = ""
        if (Test-Path -LiteralPath $res.Stdout) { $jsonText = Get-Content -LiteralPath $res.Stdout -Raw -ErrorAction SilentlyContinue }
        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            return @([pscustomobject]@{ Path = $File.FullName; File = $File.Name; Line = 0; Column = 0; ErrorId = "ChildParserNoOutput"; Message = ("parent={0}; child exit={1}" -f $parentError, $res.ExitCode) })
        }
        try {
            $childRows = @($jsonText | ConvertFrom-Json -ErrorAction Stop)
            $out = [System.Collections.Generic.List[object]]::new()
            foreach ($r in $childRows) {
                $out.Add([pscustomobject]@{
                    Path = $File.FullName; File = $File.Name
                    Line = [int]$r.Line; Column = [int]$r.Column
                    ErrorId = [string]$r.ErrorId; Message = [string]$r.Message
                }) | Out-Null
            }
            return @($out)
        } catch {
            return @([pscustomobject]@{ Path = $File.FullName; File = $File.Name; Line = 0; Column = 0; ErrorId = "ChildJsonParseFail"; Message = $_.Exception.Message })
        }
    }
}

# =============================================================================
# def ROUND0 - inventory + policy + accelerators + native tools
# =============================================================================
function def_Round0_Initialize {
    def_ShowProgress -Step 1 -Total 12 -Status "Round0 initialize"
    foreach ($d in @($ToolRoot, $script:def_RunRoot, $script:def_RegistryDir, $script:def_LogDir, $script:def_ReportDir, $script:def_RuntimeDir, $script:def_BridgeDir)) {
        def_EnsureDir -Path $d
    }
    def_AddRow "Round0" "POLICY" "Safety Policy" "OK_LOCKED" "LOW" "SEQUENTIAL_GATED" "P0" "policy" "append-only" "No DB write / no canonical merge / no destructive delete / no stop-process." $ToolRoot
    foreach ($a in $script:def_Accelerators) {
        def_AddRow "Round0" "ACCELERATOR" $a.Name "OK_ENABLED" "LOW" "PARALLEL_SAFE" "P1" $a.ID "enabled" $a.Detail ""
    }
    if (Test-Path -LiteralPath $Root -PathType Container) {
        def_AddRow "Round0" "ROOT" "VIA Root" "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "exists" $true "Root folder available." $Root
    } else {
        def_AddRow "Round0" "ROOT" "VIA Root" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Root folder missing." $Root
    }
}

function def_Round0_CheckSupportiveAndTools {
    def_ShowProgress -Step 2 -Total 12 -Status "Round0 supportive files + native tools"
    foreach ($s in $script:def_SupportiveFiles) {
        $p = Join-Path $SupportiveDir $s.Name
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            $hash = def_GetSha256 -Path $p
            def_AddRow "Round0" "SUPPORTIVE" $s.Name "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "sha256" $hash ("Required supportive {0} found." -f $s.Kind) $p
        } else {
            def_AddRow "Round0" "SUPPORTIVE" $s.Name "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Required supportive module missing." $p
        }
    }
    foreach ($tool in $script:def_NativeTools) {
        $cmd = Get-Command $tool -ErrorAction SilentlyContinue
        if ($cmd) {
            def_AddRow "Round0" "NATIVE_TOOL" $tool "OK_FOUND" "LOW" "PARALLEL_SAFE" "P1" "path" $cmd.Source "Native tool available." $cmd.Source
        } else {
            def_AddRow "Round0" "NATIVE_TOOL" $tool "WARN_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "path" "" "Native tool not found; not fatal." ""
        }
    }
}

# =============================================================================
# def ROUND1 - install/import PS modules (cache-first), import supportive modules
# =============================================================================
function def_Round1_InstallImportModules {
    def_ShowProgress -Step 3 -Total 12 -Status "Round1 PS modules"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
    } catch {
        try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
    }
    foreach ($m in $script:def_PsModules) {
        $existing = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($existing) {
            def_AddRow "Round1" "PS_MODULE" $m.Name "OK_PRESENT" "LOW" "PARALLEL_SAFE" "P1" "version" $existing.Version ("Cache-first hit. Purpose: {0}" -f $m.Purpose) $existing.Path
        } elseif ($script:def_DoInstall) {
            try {
                Install-Module -Name $m.Name -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
                $installed = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($installed) {
                    def_AddRow "Round1" "PS_MODULE" $m.Name "OK_INSTALLED" "LOW" "PARALLEL_SAFE" "P1" "version" $installed.Version ("Installed. Purpose: {0}" -f $m.Purpose) $installed.Path
                } else {
                    def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_UNCONFIRMED" "MEDIUM" "PARALLEL_SAFE" "P2" "installed" "unknown" "Install completed but module not discovered." ""
                }
            } catch {
                $risk = "LOW"
                if ($m.Required) { $risk = "MEDIUM" }
                def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_FAILED" $risk "PARALLEL_SAFE" "P2" "error" $_.Exception.Message "Install failed; continuing (Network Retry Lite)." ""
            }
        } else {
            $risk = "LOW"
            if ($m.Required) { $risk = "MEDIUM" }
            def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_NOT_INSTALLED_BY_POLICY" $risk "PARALLEL_SAFE" "P2" "network" $false "Network install disabled by -NoNetworkInstallSwitch." ""
        }
        try {
            Import-Module -Name $m.Name -ErrorAction Stop
            def_AddRow "Round1" "PS_MODULE_IMPORT" $m.Name "OK_IMPORTED" "LOW" "PARALLEL_SAFE" "P1" "import" $true "Imported into session." ""
        } catch {
            def_AddRow "Round1" "PS_MODULE_IMPORT" $m.Name "WARN_IMPORT_FAILED" "LOW" "PARALLEL_SAFE" "P3" "error" $_.Exception.Message "Import failed; bridge can still call tools directly." ""
        }
    }
}

function def_Round1_ImportSupportiveModules {
    def_ShowProgress -Step 4 -Total 12 -Status "Round1 import supportive modules"
    $pwsh = def_GetPwsh
    foreach ($s in $script:def_SupportiveFiles) {
        $p = Join-Path $SupportiveDir $s.Name
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
            def_AddRow "Round1" "SUPPORTIVE_IMPORT" $s.Name "WARN_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "exists" $false "Supportive module not found; skipped." $p
            continue
        }

        if ($s.Kind -eq "doc") {
            # Read_Me: actually parse it (headings + key cues), not just note existence.
            try {
                $raw = Get-Content -LiteralPath $p -Raw -ErrorAction Stop
                $headings = @([regex]::Matches($raw, '(?m)^\#{1,6}\s+(.+)$') | ForEach-Object { $_.Groups[1].Value.Trim() })
                $cues = [System.Collections.Generic.List[string]]::new()
                if ($raw -match 'dry[\s\-]?run|DRY_RUN|append[\s\-]?only') { $cues.Add("policy-language") | Out-Null }
                if ($raw -match 'HTML|Matrix|Report|CSV|JSON') { $cues.Add("report-output") | Out-Null }
                if ($raw -match 'pwsh|python|Start-Process|WaitForExit|ProcessStartInfo') { $cues.Add("tool-bridge") | Out-Null }
                $val = ("{0} headings; cues: {1}" -f (def_CountSafe $headings), ($cues -join ','))
                def_AddRow "Round1" "SUPPORTIVE_DOC" $s.Name "OK_PARSED" "LOW" "PARALLEL_SAFE" "P1" "headings/cues" $val ("First heading: {0}" -f (@($headings)[0])) $p
            } catch {
                def_AddRow "Round1" "SUPPORTIVE_DOC" $s.Name "WARN_PARSE_FAILED" "LOW" "PARALLEL_SAFE" "P3" "error" $_.Exception.Message "Read_Me parse failed." $p
            }
            continue
        }

        # ps kind: A03 AST-before-invoke. Parse-check first; only invoke if clean.
        $fi = Get-Item -LiteralPath $p
        $parse = @(def_ParsePSFileSafe -File $fi)
        $errCount = def_CountSafe $parse
        if ($errCount -gt 0) {
            $first = $parse[0]
            def_AddRow "Round1" "SUPPORTIVE_AST" $s.Name "FAIL_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "line:col" ("{0}:{1}" -f $first.Line, $first.Column) ("Parse error - NOT invoked: {0}" -f $first.Message) $p
            continue
        }
        def_AddRow "Round1" "SUPPORTIVE_AST" $s.Name "OK_PARSE_CLEAN" "LOW" "PARALLEL_SAFE" "P1" "parse" "clean" "Parse-clean; safe to invoke." $p

        if (-not $s.Invoke) { continue }
        if (-not $script:def_DoInvoke) {
            def_AddRow "Round1" "SUPPORTIVE_INVOKE" $s.Name "WARN_SKIPPED" "LOW" "PARALLEL_SAFE" "P3" "invoke" $false "Invocation disabled by -NoInvokeSupportiveSwitch." $p
            continue
        }
        if ($null -eq $pwsh) {
            def_AddRow "Round1" "SUPPORTIVE_INVOKE" $s.Name "FAIL_NO_PWSH" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "pwsh" "missing" "pwsh not found; cannot invoke." $p
            continue
        }
        $res = def_InvokeProcess -Name ("invoke_{0}" -f (def_ToSafeLogName -Text $s.Name)) -FilePath $pwsh -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $p) -WorkingDirectory $SupportiveDir -TimeoutSeconds $TimeoutSec
        $st = "OK_EXIT_0"
        $risk = "LOW"
        if ($res.TimedOut) {
            $st = "WARN_TIMEOUT"; $risk = "MEDIUM"
        } elseif ($res.ExitCode -ne 0) {
            $st = ("WARN_EXIT_{0}" -f $res.ExitCode); $risk = "MEDIUM"
        }
        def_AddRow "Round1" "SUPPORTIVE_INVOKE" $s.Name $st $risk "PARALLEL_SAFE" "P2" "exit" $res.ExitCode "Invoked via child process (isolated, timeout-guarded)." $p
    }
}

# =============================================================================
# def ROUND2 - AST parse scan + Hydra gate + dry analyzers + inventory + plan
# =============================================================================
function def_Round2_ParseScan {
    def_ShowProgress -Step 5 -Total 12 -Status "Round2 PS AST parse scan"
    $psFiles = @(def_GetSourceFiles -Extensions $script:def_PsExt)
    $parseRows = [System.Collections.Generic.List[object]]::new()
    $i = 0
    $total = [Math]::Max(1, (def_CountSafe $psFiles))
    foreach ($f in $psFiles) {
        $i++
        def_ShowProgress -Step 5 -Total 12 -Status ("Round2 AST {0}/{1}" -f $i, $total)
        foreach ($r in @(def_ParsePSFileSafe -File $f)) {
            if (($null -ne $r.ErrorId) -and ($r.ErrorId -ne "") -and (($r.Line -ne 0) -or ($r.Message -ne ""))) {
                $parseRows.Add($r) | Out-Null
            }
        }
    }
    $parseCsv = Join-Path $script:def_RegistryDir "VIA_PS_ParseErrors.csv"
    def_SaveCsv -Path $parseCsv -Rows @($parseRows)

    $filesWithErrors = @($parseRows | Select-Object -ExpandProperty Path -Unique)
    $blockCount = def_CountSafe $filesWithErrors
    if ($blockCount -gt 0) {
        def_AddRow "Round2" "AST" "PowerShell AST Parse" "FAIL_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "files/errors" ("{0}/{1}" -f $blockCount, (def_CountSafe $parseRows)) "Parse errors present; broad autofix is Hydra-gated." $parseCsv
        foreach ($pf in $filesWithErrors) {
            $one = @($parseRows | Where-Object { $_.Path -eq $pf })[0]
            def_AddRow "Round2" "AST_DETAIL" $one.File "FAIL_PARSE_DETAIL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "line:col" ("{0}:{1}" -f $one.Line, $one.Column) $one.Message $pf
        }
    } else {
        def_AddRow "Round2" "AST" "PowerShell AST Parse" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "P1" "files/errors" "0/0" "All PowerShell files parse clean." $parseCsv
    }
    return ($blockCount -gt 0)
}

function def_Round2_DryAnalyzers {
    param([bool]$ParseBlock)
    def_ShowProgress -Step 6 -Total 12 -Status "Round2 dry analyzers"
    $pssa = Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue
    if ($pssa) {
        $pssaCsv = Join-Path $script:def_RegistryDir "VIA_PSScriptAnalyzer_Findings.csv"
        try {
            $findings = @(Invoke-ScriptAnalyzer -Path $Root -Recurse -Severity Error, Warning -ErrorAction Continue)
            def_SaveCsv -Path $pssaCsv -Rows $findings
            $errCount = @($findings | Where-Object { $_.Severity -eq "Error" }).Count
            $warnCount = @($findings | Where-Object { $_.Severity -eq "Warning" }).Count
            $st = "OK_CLEAN"
            $risk = "LOW"
            if ($errCount -gt 0 -or $warnCount -gt 0) { $st = "WARN_ANALYZER" }
            if ($errCount -gt 0) { $risk = "MEDIUM" }
            def_AddRow "Round2" "PSSA" "PSScriptAnalyzer" $st $risk "PARALLEL_SAFE" "P2" "error/warn" ("{0}/{1}" -f $errCount, $warnCount) "PSSA report generated; -Fix stays gated." $pssaCsv
        } catch {
            def_AddRow "Round2" "PSSA" "PSScriptAnalyzer" "WARN_ANALYZER_FAILED" "MEDIUM" "PARALLEL_SAFE" "P2" "error" "exception" $_.Exception.Message $Root
        }
    } else {
        def_AddRow "Round2" "PSSA" "PSScriptAnalyzer" "WARN_TOOL_MISSING" "LOW" "PARALLEL_SAFE" "P2" "tool" "missing" "PSScriptAnalyzer not available." ""
    }

    $python = def_GetPython
    if ($python) {
        $ruff = def_InvokeProcess -Name "ruff_check_dry" -FilePath $python -ArgumentList @("-m", "ruff", "check", $Root, "--exit-zero", "--output-format", "json") -WorkingDirectory $Root -TimeoutSeconds 1200
        $ruffJson = Join-Path $script:def_RegistryDir "VIA_Ruff_Findings.json"
        if (Test-Path -LiteralPath $ruff.Stdout) { Copy-Item -LiteralPath $ruff.Stdout -Destination $ruffJson -Force }
        $st = "WARN_EXIT"
        if ($ruff.ExitCode -eq 0) { $st = "OK_EXIT_0" }
        def_AddRow "Round2" "RUFF" "ruff check (dry)" $st "LOW" "PARALLEL_SAFE" "P2" "exit" $ruff.ExitCode "ruff dry report (if ruff installed)." $ruffJson
    } else {
        def_AddRow "Round2" "RUFF" "ruff check (dry)" "WARN_PYTHON_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "python" "missing" "Python not resolved." ""
    }
}

function def_Round2_Inventory {
    def_ShowProgress -Step 7 -Total 12 -Status "Round2 source inventory (low-memory)"
    $counts = [ordered]@{ ps = 0; py = 0; js = 0; cs = 0 }
    try {
        Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            if (def_IsExcludedPath -Path $_.FullName) { return }
            switch -Regex ($_.Extension.ToLowerInvariant()) {
                '^\.ps1$|^\.psm1$|^\.psd1$' { $counts.ps++; break }
                '^\.py$' { $counts.py++; break }
                '^\.js$|^\.ts$|^\.mjs$|^\.cjs$|^\.jsx$|^\.tsx$' { $counts.js++; break }
                '^\.cs$' { $counts.cs++; break }
            }
        }
        def_AddRow "Round2" "INVENTORY" "Source Inventory" "OK_SCANNED" "LOW" "PARALLEL_SAFE" "P2" "ps/py/js/cs" ("{0}/{1}/{2}/{3}" -f $counts.ps, $counts.py, $counts.js, $counts.cs) "Low-memory streaming inventory." $Root
    } catch {
        def_AddRow "Round2" "INVENTORY" "Source Inventory" "WARN_SCAN_FAILED" "MEDIUM" "PARALLEL_SAFE" "P2" "error" "exception" $_.Exception.Message $Root
    }
}

function def_Round2_RepairPlanAndApply {
    param([bool]$ParseBlock)
    def_ShowProgress -Step 8 -Total 12 -Status "Round2 repair plan + gated apply"

    if ($ParseBlock) {
        def_AddRow "Round2" "REPAIR" "Hydra Risk Gate" "FAIL_REPAIR_BLOCKED" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "gate" "blocked" "Broad PSSA/ruff autofix blocked until parse errors clear." ""
    } else {
        def_AddRow "Round2" "REPAIR" "Hydra Risk Gate" "OK_REPAIR_ALLOWED" "LOW" "SEQUENTIAL_GATED" "P1" "gate" "open" "No parse blocker; guarded fixes may be considered." ""
    }

    $approved = $ApplyRepairsSwitch -and ($ApprovalToken -eq $script:def_ApprovalRequired)
    if (-not $approved) {
        def_AddRow "Round2" "REPAIR" "Repair Mode" "OK_DRY_RUN" "LOW" "SEQUENTIAL_GATED" "P1" "apply" $false ("Dry-run. To apply: -ApplyRepairsSwitch -ApprovalToken {0} (only after parse-clean)." -f $script:def_ApprovalRequired) ""
        return
    }
    if ($ParseBlock) {
        def_AddRow "Round2" "REPAIR" "Repair Mode" "FAIL_BLOCKED_BY_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "apply" $false "Approval received but parse errors remain; no write performed." ""
        return
    }

    def_WriteLog "RUN" "Applying guarded repairs (approved + parse-clean)."
    $pssa = Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue
    if ($pssa) {
        try {
            Invoke-ScriptAnalyzer -Path $Root -Recurse -Fix -ErrorAction Continue | Out-Null
            def_AddRow "Round2" "REPAIR" "PSScriptAnalyzer -Fix" "OK_REPAIR_APPLIED" "LOW" "SEQUENTIAL_GATED" "P1" "fix" "done" "PSSA -Fix applied after gate clear." $Root
        } catch {
            def_AddRow "Round2" "REPAIR" "PSScriptAnalyzer -Fix" "WARN_REPAIR_FAILED" "MEDIUM" "SEQUENTIAL_GATED" "P1" "error" "exception" $_.Exception.Message $Root
        }
    }
    $python = def_GetPython
    if ($python) {
        $r1 = def_InvokeProcess -Name "ruff_fix_apply" -FilePath $python -ArgumentList @("-m", "ruff", "check", $Root, "--fix") -WorkingDirectory $Root -TimeoutSeconds 1200
        $st1 = "WARN_EXIT"
        $risk1 = "MEDIUM"
        if ($r1.ExitCode -eq 0) { $st1 = "OK_REPAIR_APPLIED"; $risk1 = "LOW" }
        def_AddRow "Round2" "REPAIR" "ruff --fix" $st1 $risk1 "SEQUENTIAL_GATED" "P1" "exit" $r1.ExitCode "ruff fix after gate clear." $Root
    }
}

# =============================================================================
# def ROUND3 - reusable bridge generation + final classification
# =============================================================================
function def_Round3_GenerateBridge {
    def_ShowProgress -Step 9 -Total 12 -Status "Round3 generate reusable bridge"
    $bridgeContent = @'
# VIA_NexusToolBridge.psm1  (generated by Invoke-VIA-NexusToolBridge-Unified-v02.ps1)
# Stable wrapper so other VIA scripts import ONE module instead of raw tool paths.
# LL-compliant child invocation via ProcessStartInfo (no Start-Process for subprocess).

function def_InvokeVIACommandSafe {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = "",
        [int]$TimeoutSec = 300
    )
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
        return [pscustomobject]@{ Status = "WARN_SCRIPT_MISSING"; ExitCode = $null; Path = $ScriptPath }
    }
    $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue)
    if (-not $pwsh) {
        return [pscustomobject]@{ Status = "FAIL_PWSH_MISSING"; ExitCode = $null; Path = $ScriptPath }
    }
    if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) { $WorkingDirectory = Split-Path $ScriptPath -Parent }
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $pwsh.Source
    foreach ($a in (@("-NoProfile","-ExecutionPolicy","Bypass","-File",$ScriptPath) + $Arguments)) { [void]$psi.ArgumentList.Add($a) }
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::new()
    $p.StartInfo = $psi
    [void]$p.Start()
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $finished = $p.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        try { $p.Kill($true) } catch { }
        return [pscustomobject]@{ Status = "WARN_TIMEOUT"; ExitCode = 124; Path = $ScriptPath; Stdout = $outTask.Result; Stderr = $errTask.Result }
    }
    return [pscustomobject]@{ Status = ("OK_EXIT_{0}" -f $p.ExitCode); ExitCode = $p.ExitCode; Path = $ScriptPath; Stdout = $outTask.Result; Stderr = $errTask.Result }
}

function def_InvokeNexusCore {
    param([string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules", [int]$TimeoutSec = 300)
    return def_InvokeVIACommandSafe -ScriptPath (Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1") -WorkingDirectory $SupportiveDir -TimeoutSec $TimeoutSec
}

function def_InvokePolyglotCTR {
    param([string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules", [int]$TimeoutSec = 300)
    return def_InvokeVIACommandSafe -ScriptPath (Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1") -WorkingDirectory $SupportiveDir -TimeoutSec $TimeoutSec
}

Export-ModuleMember -Function def_InvokeVIACommandSafe, def_InvokeNexusCore, def_InvokePolyglotCTR
'@

    try {
        def_SaveText -Path $script:def_BridgePsm1 -Text $bridgeContent

        $supportItems = @()
        foreach ($s in $script:def_SupportiveFiles) {
            $p = Join-Path $SupportiveDir $s.Name
            $supportItems += [pscustomobject]@{ name = $s.Name; kind = $s.Kind; path = $p; exists = (Test-Path -LiteralPath $p); sha256 = (def_GetSha256 -Path $p) }
        }
        $bridgeMeta = [ordered]@{
            schema = "VIA.NexusToolBridge"
            version = "v0.2.0"
            generated = (Get-Date).ToString("s")
            run_id = $script:def_RunId
            root = $Root
            supportive_dir = $SupportiveDir
            bridge_module = $script:def_BridgePsm1
            supportive_items = $supportItems
            accelerators = $script:def_Accelerators
            policy = $script:def_Policy
        }
        $json = $bridgeMeta | ConvertTo-Json -Depth 12
        def_SaveText -Path $script:def_BridgeJson -Text $json

        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge.psm1" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "module" "ready" "Reusable bridge module generated (A07)." $script:def_BridgePsm1
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge.json" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "manifest" "ready" "Bridge manifest with sha256 inventory generated." $script:def_BridgeJson
    } catch {
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge" "FAIL_WRITE_ERROR" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" "exception" $_.Exception.Message $script:def_BridgePsm1
    }
}

function def_Round3_Classify {
    def_ShowProgress -Step 10 -Total 12 -Status "Round3 classification"
    $rows = def_AsArraySafe $script:def_Rows
    $parallel = def_CountSafe ($rows | Where-Object { $_.Class -eq "PARALLEL_SAFE" -and $_.Risk -ne "HIGH" })
    $sequential = def_CountSafe ($rows | Where-Object { $_.Class -like "SEQUENTIAL*" -or $_.Risk -eq "HIGH" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })

    def_AddRow "Round3" "CLASSIFY" "Parallel-Safe Items" "OK_CLASSIFIED" "LOW" "PARALLEL_SAFE" "P1" "count" $parallel "Independent; can be handled together." ""
    $seqStatus = "OK_CLASSIFIED"
    $seqRisk = "LOW"
    if ($high -gt 0) { $seqStatus = "WARN_REVIEW_REQUIRED"; $seqRisk = "HIGH" }
    def_AddRow "Round3" "CLASSIFY" "Sequential / Gated Items" $seqStatus $seqRisk "SEQUENTIAL_GATED" "P0" "count" $sequential "Handle in order to avoid Hydra risk." ""
    $hydraStatus = "OK_HYDRA_CLEAR"
    $hydraRisk = "LOW"
    if ($high -gt 0) { $hydraStatus = "WARN_HYDRA_REVIEW"; $hydraRisk = "HIGH" }
    def_AddRow "Round3" "CLASSIFY" "Hydra Risk Gate" $hydraStatus $hydraRisk "SEQUENTIAL_GATED" "P0" "high_risk" $high "High-risk items isolated before broader integration." ""
}

# =============================================================================
# def OUTPUT - CSV / JSON / Visual Lock HTML
# =============================================================================
function def_SaveCsv {
    param([string]$Path, [object[]]$Rows)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    $rowsArr = def_AsArraySafe $Rows
    if ((def_CountSafe $rowsArr) -eq 0) {
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
    # CSV uses UTF-8 BOM so Excel renders zh-TW correctly (written via [IO.File]::WriteAllText).
    def_SaveText -Path $Path -Text $sb.ToString() -BomSwitch
}

function def_ExportMatrix {
    $rows = def_AsArraySafe $script:def_Rows
    def_SaveCsv -Path $script:def_MatrixCsv -Rows $rows
    $json = $rows | ConvertTo-Json -Depth 8
    def_SaveText -Path $script:def_MatrixJson -Text $json
}

function def_RiskColor {
    param([string]$Risk)
    $c = switch ($Risk) {
        'HIGH'   { $script:def_ColUp }
        'MEDIUM' { $script:def_ColGrey }
        default  { $script:def_ColDown }
    }
    return $c
}

function def_BuildMatrixRows {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($r in $script:def_Rows) {
        $rc = def_RiskColor -Risk $r.Risk
        [void]$sb.AppendLine("<tr>")
        [void]$sb.AppendLine("<td class='mono'>$(def_HtmlEncode $r.Round)</td>")
        [void]$sb.AppendLine("<td class='mono'>$(def_HtmlEncode $r.Layer)</td>")
        [void]$sb.AppendLine("<td>$(def_HtmlEncode $r.Name)</td>")
        [void]$sb.AppendLine("<td class='mono'>$(def_HtmlEncode $r.Status)</td>")
        [void]$sb.AppendLine("<td><span class='pill' style='background:$rc'>$(def_HtmlEncode $r.Risk)</span></td>")
        [void]$sb.AppendLine("<td class='mono small'>$(def_HtmlEncode $r.Class)</td>")
        [void]$sb.AppendLine("<td class='mono'>$(def_HtmlEncode $r.Priority)</td>")
        [void]$sb.AppendLine("<td class='mono small'>$(def_HtmlEncode $r.Metric)</td>")
        [void]$sb.AppendLine("<td class='mono small'>$(def_HtmlEncode $r.Value)</td>")
        [void]$sb.AppendLine("<td class='small'>$(def_HtmlEncode $r.Message)</td>")
        [void]$sb.AppendLine("</tr>")
    }
    return $sb.ToString()
}

function def_BuildAccelCards {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($a in $script:def_Accelerators) {
        [void]$sb.AppendLine("<div class='accel'><b>$(def_HtmlEncode $a.ID) &middot; $(def_HtmlEncode $a.Name)</b><br><span>$(def_HtmlEncode $a.Detail)</span></div>")
    }
    return $sb.ToString()
}

function def_WriteHtmlReport {
    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    $risk = "LOW"
    if ($fail -gt 0) {
        $risk = "HIGH"
    } elseif ($warn -gt 0) {
        $risk = "MEDIUM"
    }
    $status = "READY"
    if ($fail -gt 0) {
        $status = "REVIEW"
    } elseif ($warn -gt 0) {
        $status = "READY_WARN"
    }
    $policyJson = ($script:def_Policy | ConvertTo-Json -Compress)

    $tpl = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Nexus ToolBridge Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;700;800&display=swap');
:root{ --blue:@@BLUE@@; --grey:@@GREY@@; --teal:@@TEAL@@; --up:@@UP@@; --down:@@DOWN@@; }
*{ box-sizing:border-box; }
body{ margin:0; padding:34px 40px; background:#13161a; color:#e7e9ec; font-family:'DM Sans',sans-serif; }
h1{ font-family:'Syne',sans-serif; font-weight:800; font-size:25px; margin:0 0 4px; color:#fff; }
.sub{ color:var(--grey); font-size:13px; margin-bottom:18px; }
.grid{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:18px 0; }
.card{ background:#1b1f24; border:1px solid #2a2f36; border-radius:14px; padding:14px 16px; }
.k{ font-size:12px; color:var(--grey); } .v{ font-size:22px; font-weight:700; margin-top:4px; font-family:'DM Mono',monospace; color:var(--teal); }
.accels{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin-bottom:18px; }
.accel{ background:#171b20; border:1px solid #2a2f36; border-radius:12px; padding:10px; font-size:11px; }
.accel b{ color:var(--teal); font-family:'DM Mono',monospace; } .accel span{ color:#aab0b6; }
h2{ font-family:'Syne',sans-serif; font-weight:700; font-size:16px; color:var(--blue); border-bottom:1px solid #2a2f36; padding-bottom:8px; margin:26px 0 12px; }
table{ border-collapse:collapse; width:100%; background:#171b20; border:1px solid #2a2f36; border-radius:10px; overflow:hidden; font-size:12px; }
th{ position:sticky; top:0; background:#1d2228; color:var(--teal); text-align:left; padding:9px 10px; font-family:'DM Mono',monospace; font-size:11px; }
td{ padding:8px 10px; border-bottom:1px solid #23282e; vertical-align:top; }
tr:hover td{ background:#1b2026; }
.mono{ font-family:'DM Mono',monospace; } .small{ font-size:11px; color:#aab0b6; }
.pill{ display:inline-block; padding:2px 9px; border-radius:11px; color:#13161a; font-weight:700; font-size:10.5px; font-family:'DM Mono',monospace; }
.foot{ color:var(--grey); font-size:11px; margin-top:22px; line-height:1.6; }
code{ background:#23282e; padding:2px 6px; border-radius:4px; font-family:'DM Mono',monospace; color:#e7e9ec; }
</style>
</head>
<body>
<h1>理 &middot; VIA Nexus ToolBridge &middot; Unified v0.2</h1>
<div class="sub">integrate strengths &middot; remove weaknesses &middot; 判天地之美，析萬物之理 &middot; run @@RUNID@@</div>
<div class="grid">
  <div class="card"><div class="k">Status</div><div class="v">@@STATUS@@</div></div>
  <div class="card"><div class="k">Risk</div><div class="v">@@RISK@@</div></div>
  <div class="card"><div class="k">OK</div><div class="v">@@OK@@</div></div>
  <div class="card"><div class="k">WARN / HIGH</div><div class="v">@@WARN@@ / @@FAIL@@</div></div>
</div>
<h2>Accelerators</h2>
<div class="accels">@@ACCELS@@</div>
<h2>Panoramic matrix</h2>
<table>
<thead><tr><th>round</th><th>layer</th><th>name</th><th>status</th><th>risk</th><th>class</th><th>pri</th><th>metric</th><th>value</th><th>message</th></tr></thead>
<tbody>@@ROWS@@</tbody>
</table>
<div class="foot">
Generated @@GENERATED@@ &middot; policy <code>@@POLICY@@</code><br>
Default run analyzes + imports modules + invokes the three supportive modules (child-isolated) + generates the reusable bridge.
Repairs apply ONLY with <code>-ApplyRepairsSwitch -ApprovalToken @@APPROVAL@@</code> AND a clean parse gate.
Reusable bridge written to <code>@@BRIDGE@@</code> &mdash; other scripts use <code>Import-Module</code> then <code>def_InvokeNexusCore</code> / <code>def_InvokePolyglotCTR</code>.
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
    $html = $html.Replace('@@STATUS@@', (def_HtmlEncode $status))
    $html = $html.Replace('@@RISK@@', (def_HtmlEncode $risk))
    $html = $html.Replace('@@OK@@', [string]$ok)
    $html = $html.Replace('@@WARN@@', [string]$warn)
    $html = $html.Replace('@@FAIL@@', [string]$fail)
    $html = $html.Replace('@@ACCELS@@', (def_BuildAccelCards))
    $html = $html.Replace('@@ROWS@@', (def_BuildMatrixRows))
    $html = $html.Replace('@@GENERATED@@', (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
    $html = $html.Replace('@@POLICY@@', (def_HtmlEncode $policyJson))
    $html = $html.Replace('@@APPROVAL@@', (def_HtmlEncode $script:def_ApprovalRequired))
    $html = $html.Replace('@@BRIDGE@@', (def_HtmlEncode $script:def_BridgePsm1))
    def_SaveText -Path $script:def_ReportHtml -Text $html
}

function def_Finalize {
    def_ShowProgress -Step 11 -Total 12 -Status "finalize: export matrix + report"
    def_ExportMatrix
    def_WriteHtmlReport
    def_ShowProgress -Step 12 -Total 12 -Status "done"
    Write-Progress -Id 1 -Activity "VIA Nexus ToolBridge Unified v0.2" -Completed

    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " VIA Nexus ToolBridge Unified v0.2 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Run root    : {0}" -f $script:def_RunRoot)
    Write-Host ("Bridge PSM1 : {0}" -f $script:def_BridgePsm1)
    Write-Host ("Bridge JSON : {0}" -f $script:def_BridgeJson)
    Write-Host ("HTML        : {0}" -f $script:def_ReportHtml)
    Write-Host ("OK/WARN/HIGH: {0} / {1} / {2}" -f $ok, $warn, $fail)
    Write-Host ""
    Write-Host "Reuse in other scripts:" -ForegroundColor Green
    Write-Host ("  Import-Module `"{0}`" -Force" -f $script:def_BridgePsm1) -ForegroundColor DarkGreen
    Write-Host "  def_InvokeNexusCore ; def_InvokePolyglotCTR" -ForegroundColor DarkGreen

    if (-not $NoOpenReportSwitch -and (Test-Path -LiteralPath $script:def_ReportHtml)) {
        try { Start-Process $script:def_ReportHtml | Out-Null } catch { }
    }
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " VIA Nexus ToolBridge Unified v0.2  (best-of integration)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ("Root        : {0}" -f $Root)
    Write-Host ("Supportive  : {0}" -f $SupportiveDir)
    Write-Host ("Tool root   : {0}" -f $ToolRoot)
    Write-Host ("Run ID      : {0}" -f $script:def_RunId)
    Write-Host ("Install/Invoke: {0} / {1}" -f $script:def_DoInstall, $script:def_DoInvoke)
    Write-Host ""

    def_Round0_Initialize
    def_Round0_CheckSupportiveAndTools
    def_Round1_InstallImportModules
    def_Round1_ImportSupportiveModules
    $parseBlock = def_Round2_ParseScan
    def_Round2_DryAnalyzers -ParseBlock $parseBlock
    def_Round2_Inventory
    def_Round2_RepairPlanAndApply -ParseBlock $parseBlock
    def_Round3_GenerateBridge
    def_Round3_Classify
    def_Finalize
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host ("[FATAL] {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddRow "FATAL" "RUNTIME" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" "exception" $_.Exception.Message ""
        def_Finalize
    } catch { }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
