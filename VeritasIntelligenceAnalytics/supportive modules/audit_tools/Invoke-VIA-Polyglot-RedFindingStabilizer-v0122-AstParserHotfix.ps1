#requires -Version 7.0
<#
Veritas Intelligence Analytics · Polyglot Red-Finding Stabilizer v01.2.2
Purpose:
  1) Locate PS AST parse errors precisely.
  2) Prevent Hydra risk by blocking broad repair while parse errors exist.
  3) Build sequential and parallel repair matrix.
  4) Optionally run guarded repairs only after explicit approval.
Policy:
  - Default dry-run
  - No DB write
  - No canonical merge
  - No destructive delete
  - No stop-process
  - Append-only outputs
#>

param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [switch]$RunVdfGate,
    [switch]$RunPolyglotBaseline,
    [switch]$RunTests,
    [switch]$ApplyRepairs,
    [string]$ApprovalToken = "",
    [switch]$OpenReport
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

# =============================================================================
# def PARAMETERS
# =============================================================================
$ErrorActionPreference = "Stop"

$def_PARAM_APPROVAL_TOKEN_REQUIRED = "APPROVE_VIA_POLYGLOT_REPAIR"
$def_PARAM_NO_DB_WRITE = $true
$def_PARAM_NO_CANONICAL_MERGE = $true
$def_PARAM_NO_DESTRUCTIVE_DELETE = $true
$def_PARAM_NO_STOP_PROCESS = $true
$def_PARAM_APPEND_ONLY = $true

$def_PARAM_ROOT = $Root
$def_PARAM_VDF_DIR = Join-Path $def_PARAM_ROOT "functional modules\VDF"
$def_PARAM_SUPPORTIVE_DIR = Join-Path $def_PARAM_ROOT "supportive modules"
$def_PARAM_TOOL_ROOT = Join-Path $def_PARAM_ROOT "tools\VIA_PolyglotCTR"
$def_PARAM_POLYGLOT_SCRIPT = Join-Path $def_PARAM_SUPPORTIVE_DIR "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
$def_PARAM_VDF_GATE_SCRIPT = Join-Path $def_PARAM_VDF_DIR "Invoke-VDF-Nexus-Panorama3RoundGate.ps1"

$def_PARAM_RUN_ID = "RUN_{0}_VIA_RED_FINDING_STABILIZER" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_PARAM_RUN_ROOT = Join-Path $def_PARAM_TOOL_ROOT ("runs\" + $def_PARAM_RUN_ID)
$def_PARAM_REPORT_DIR = Join-Path $def_PARAM_RUN_ROOT "report"
$def_PARAM_REGISTRY_DIR = Join-Path $def_PARAM_RUN_ROOT "registry"
$def_PARAM_RUNTIME_DIR = Join-Path $def_PARAM_RUN_ROOT "runtime"
$def_PARAM_LOG_DIR = Join-Path $def_PARAM_RUN_ROOT "logs"

$def_PARAM_EXCLUDE_DIR_NAMES = @(
    ".git", ".svn", ".hg",
    "__pycache__", ".pytest_cache", ".ruff_cache",
    "node_modules", ".next", "dist", "build",
    ".venv", "venv", "_envs", "env",
    "site-packages"
)

$def_PARAM_EXCLUDE_PATH_REGEX = @(
    "\\tools\\VIA_PolyglotCTR\\runs\\",
    "\\_vdf_system\\macro_manifest_fetch_runs\\",
    "\\_vdf_system\\panorama3round_gate_runs\\",
    "\\_sealed_command_engine_packages\\",
    "\\_pack_runs\\"
)

$def_PARAM_PS_EXTENSIONS = @(".ps1", ".psm1", ".psd1")
$def_PARAM_PY_EXTENSIONS = @(".py")
$def_PARAM_JS_EXTENSIONS = @(".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")
$def_PARAM_CS_EXTENSIONS = @(".cs")

$script:def_ROWS = New-Object System.Collections.Generic.List[object]

# =============================================================================
# def BASIC UTILITIES
# =============================================================================
function def_EnsureDir {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_WriteLine {
    param(
        [string]$Level,
        [string]$Message
    )
    $stamp = Get-Date -Format "HH:mm:ss.fff"
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host ("[{0}] [{1}] {2}" -f $stamp, $Level, $Message) -ForegroundColor $color
}


function def_CountSafe {
    param([AllowNull()][object]$InputObject)

    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [System.Array]) { return $InputObject.Length }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
        $n = 0
        foreach ($item in $InputObject) { $n++ }
        return $n
    }
    return 1
}

function def_AsArraySafe {
    param([AllowNull()][object]$InputObject)

    if ($null -eq $InputObject) { return @() }
    return @($InputObject)
}

function def_AddRow {
    param(
        [string]$Round,
        [string]$Lang,
        [string]$Module,
        [string]$Stage,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$FixClass,
        [string]$Mode,
        [string]$Metric,
        [string]$Value,
        [string]$Message,
        [string]$Path = ""
    )

    $row = [pscustomobject]@{
        Round = $Round
        Lang = $Lang
        Module = $Module
        Stage = $Stage
        Name = $Name
        Status = $Status
        Risk = $Risk
        FixClass = $FixClass
        Mode = $Mode
        Metric = $Metric
        Value = $Value
        Message = $Message
        Path = $Path
    }
    $script:def_ROWS.Add($row) | Out-Null
}

function def_SaveText {
    param(
        [Parameter(Mandatory)][string]$Path,
        [AllowNull()][string]$Text
    )
    $dir = Split-Path -Parent $Path
    def_EnsureDir -Path $dir
    Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function def_InvokeProcess {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = $def_PARAM_ROOT,
        [int]$TimeoutSec = 900
    )

    $stdout = Join-Path $def_PARAM_LOG_DIR ("{0}_stdout.txt" -f $Name)
    $stderr = Join-Path $def_PARAM_LOG_DIR ("{0}_stderr.txt" -f $Name)
    def_EnsureDir -Path $def_PARAM_LOG_DIR

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    foreach ($arg in $ArgumentList) { [void]$psi.ArgumentList.Add($arg) }
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()

    $finished = $p.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        try { $p.Kill($true) } catch {}
        def_SaveText -Path $stdout -Text $outTask.Result
        def_SaveText -Path $stderr -Text (($errTask.Result) + "`nTIMEOUT after $TimeoutSec sec")
        return [pscustomobject]@{
            Name = $Name
            ExitCode = 124
            TimedOut = $true
            Stdout = $stdout
            Stderr = $stderr
        }
    }

    def_SaveText -Path $stdout -Text $outTask.Result
    def_SaveText -Path $stderr -Text $errTask.Result

    return [pscustomobject]@{
        Name = $Name
        ExitCode = $p.ExitCode
        TimedOut = $false
        Stdout = $stdout
        Stderr = $stderr
    }
}

function def_GetPwsh {
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd2 = Get-Command powershell -ErrorAction SilentlyContinue
    if ($cmd2) { return $cmd2.Source }
    throw "PowerShell executable not found."
}

function def_GetPython {
    $candidates = @(
        (Join-Path $def_PARAM_ROOT "_envs\via_operation_optimizer_2026\Scripts\python.exe"),
        "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd3 = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd3) { return $cmd3.Source }
    return $null
}

function def_IsExcludedPath {
    param([Parameter(Mandatory)][string]$Path)

    foreach ($name in $def_PARAM_EXCLUDE_DIR_NAMES) {
        if ($Path -match ("\\{0}(\z|\\)" -f [regex]::Escape($name))) { return $true }
    }
    foreach ($rx in $def_PARAM_EXCLUDE_PATH_REGEX) {
        if ($Path -match $rx) { return $true }
    }
    return $false
}

function def_GetSourceFiles {
    param([string[]]$Extensions)

    $all = Get-ChildItem -LiteralPath $def_PARAM_ROOT -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $ext = $_.Extension.ToLowerInvariant()
            ($Extensions -contains $ext) -and (-not (def_IsExcludedPath -Path $_.FullName))
        }

    return @($all)
}

# =============================================================================
# def HTML REPORT
# =============================================================================
function def_EscapeHtml {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return "" }
    return [System.Net.WebUtility]::HtmlEncode($Text)
}

function def_WriteHtmlReport {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][object[]]$Rows
    )

    $ok = @($Rows | Where-Object { $_.Status -like "OK*" }).Count
    $warn = @($Rows | Where-Object { $_.Status -like "WARN*" }).Count
    $fail = @($Rows | Where-Object { $_.Status -like "FAIL*" }).Count
    $high = @($Rows | Where-Object { $_.Risk -eq "HIGH" }).Count
    $medium = @($Rows | Where-Object { $_.Risk -eq "MEDIUM" }).Count

    $overallStatus = "VIA_RED_FINDING_STABILIZER_READY"
    $overallRisk = "LOW"
    if ($fail -gt 0 -or $high -gt 0) {
        $overallStatus = "VIA_RED_FINDING_STABILIZER_PARSE_BLOCKED"
        $overallRisk = "HIGH"
    } elseif ($warn -gt 0 -or $medium -gt 0) {
        $overallStatus = "VIA_RED_FINDING_STABILIZER_READY_WITH_WARNINGS"
        $overallRisk = "MEDIUM"
    }

    $tbody = New-Object System.Text.StringBuilder
    foreach ($r in $Rows) {
        $riskClass = "risk-low"
        if ($r.Risk -eq "HIGH") { $riskClass = "risk-high" }
        elseif ($r.Risk -eq "MEDIUM") { $riskClass = "risk-medium" }

        [void]$tbody.AppendLine("<tr class='$riskClass'><td>$(def_EscapeHtml $r.Round)</td><td>$(def_EscapeHtml $r.Lang)</td><td>$(def_EscapeHtml $r.Module)</td><td>$(def_EscapeHtml $r.Stage)</td><td>$(def_EscapeHtml $r.Name)</td><td>$(def_EscapeHtml $r.Status)</td><td>$(def_EscapeHtml $r.Risk)</td><td>$(def_EscapeHtml $r.FixClass)</td><td>$(def_EscapeHtml $r.Mode)</td><td>$(def_EscapeHtml $r.Metric)</td><td>$(def_EscapeHtml $r.Value)</td><td>$(def_EscapeHtml $r.Message)</td><td>$(def_EscapeHtml $r.Path)</td></tr>")
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Red-Finding Stabilizer</title>
<style>
:root{
  --paper:#f8f7f2;
  --ink:#17201c;
  --muted:#6b746f;
  --line:rgba(35,55,45,.16);
  --cyan:#7fb8b2;
  --red:#9d2f2f;
  --amber:#a87820;
  --green:#2f7656;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:
    radial-gradient(circle at 20% 10%, rgba(127,184,178,.18), transparent 32%),
    radial-gradient(circle at 85% 18%, rgba(160,120,70,.10), transparent 30%),
    linear-gradient(135deg, #fbfaf6, var(--paper));
  color:var(--ink);
  font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;
}
header{
  padding:28px 34px 18px;
  border-bottom:1px solid var(--line);
}
.seal{
  display:inline-flex;
  width:44px;height:44px;
  align-items:center;justify-content:center;
  border:2px solid var(--red);
  color:var(--red);
  font-weight:800;
  margin-right:14px;
}
h1{display:flex;align-items:center;margin:0;font-size:24px;letter-spacing:.02em}
.sub{margin-top:8px;color:var(--muted);font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:12px;padding:18px 34px}
.kpi{background:rgba(255,255,255,.62);border:1px solid var(--line);border-radius:18px;padding:14px}
.kpi .label{font-size:12px;color:var(--muted)}
.kpi .value{font-size:24px;font-weight:800;margin-top:4px}
main{padding:0 34px 34px}
.tablewrap{background:rgba(255,255,255,.68);border:1px solid var(--line);border-radius:22px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{position:sticky;top:0;background:#eef3f1;text-align:left;z-index:2}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;vertical-align:top}
tr.risk-high td{background:rgba(157,47,47,.08)}
tr.risk-medium td{background:rgba(168,120,32,.08)}
tr.risk-low td{background:rgba(47,118,86,.04)}
.badge{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:5px 10px;margin-right:8px;color:var(--muted)}
footer{padding:24px 34px;color:var(--muted);font-size:12px}
</style>
</head>
<body>
<header>
  <h1><span class="seal">理</span>Veritas Intelligence Analytics · Polyglot Red-Finding Stabilizer</h1>
  <div class="sub">Run ID: $def_PARAM_RUN_ID · Status: $overallStatus · Policy: dry-run by default · append-only · no DB write</div>
</header>
<section class="kpis">
  <div class="kpi"><div class="label">Status</div><div class="value">$overallStatus</div></div>
  <div class="kpi"><div class="label">Risk</div><div class="value">$overallRisk</div></div>
  <div class="kpi"><div class="label">OK</div><div class="value">$ok</div></div>
  <div class="kpi"><div class="label">WARN</div><div class="value">$warn</div></div>
  <div class="kpi"><div class="label">FAIL</div><div class="value">$fail</div></div>
</section>
<main>
  <p>
    <span class="badge">Round0 inventory</span>
    <span class="badge">Round1 locate red findings</span>
    <span class="badge">Round2 gated repair plan</span>
    <span class="badge">Round3 consolidate</span>
  </p>
  <div class="tablewrap">
    <table>
      <thead>
        <tr>
          <th>Round</th><th>Lang</th><th>Module</th><th>Stage</th><th>Name</th><th>Status</th><th>Risk</th><th>FixClass</th><th>Mode</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th>
        </tr>
      </thead>
      <tbody>
        $($tbody.ToString())
      </tbody>
    </table>
  </div>
</main>
<footer>
  Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight
</footer>
</body>
</html>
"@

    def_SaveText -Path $Path -Text $html
}

# =============================================================================
# def ROUND0 INVENTORY
# =============================================================================
function def_Round0_Inventory {
    def_WriteLine "RUN" "Round0 inventory started."

    foreach ($dir in @($def_PARAM_RUN_ROOT, $def_PARAM_REPORT_DIR, $def_PARAM_REGISTRY_DIR, $def_PARAM_RUNTIME_DIR, $def_PARAM_LOG_DIR)) {
        def_EnsureDir -Path $dir
    }

    $rootExists = Test-Path -LiteralPath $def_PARAM_ROOT
    def_AddRow "Round0" "VIA" "M01_CORE" "CONFIG" "Root" ($(if ($rootExists) { "OK_FOUND" } else { "FAIL_MISSING" })) ($(if ($rootExists) { "LOW" } else { "HIGH" })) "SEQUENTIAL_REQUIRED" "ANALYZE_ONLY" "path" $def_PARAM_ROOT ($(if ($rootExists) { "Root found." } else { "Root not found." })) $def_PARAM_ROOT

    $policy = "DB write=$(-not $def_PARAM_NO_DB_WRITE); canonical merge=$(-not $def_PARAM_NO_CANONICAL_MERGE); destructive delete=$(-not $def_PARAM_NO_DESTRUCTIVE_DELETE); stop-process=$(-not $def_PARAM_NO_STOP_PROCESS); append-only=$def_PARAM_APPEND_ONLY"
    def_AddRow "Round0" "VIA" "M01_CORE" "POLICY" "Safety Policy" "OK_POLICY_LOCKED" "LOW" "SEQUENTIAL_GATED" "ANALYZE_ONLY" "policy" "locked" $policy ""

    $psFiles = @(def_GetSourceFiles -Extensions $def_PARAM_PS_EXTENSIONS)
    $pyFiles = @(def_GetSourceFiles -Extensions $def_PARAM_PY_EXTENSIONS)
    $jsFiles = @(def_GetSourceFiles -Extensions $def_PARAM_JS_EXTENSIONS)
    $csFiles = @(def_GetSourceFiles -Extensions $def_PARAM_CS_EXTENSIONS)

    def_AddRow "Round0" "VIA" "M02_DETECT" "INVENTORY" "Source Inventory" "OK_CREATED" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "files" ("PS={0}; PY={1}; JS={2}; CS={3}" -f (def_CountSafe $psFiles), (def_CountSafe $pyFiles), (def_CountSafe $jsFiles), (def_CountSafe $csFiles)) "Inventory collected with run/cache exclusions." ""

    $invPath = Join-Path $def_PARAM_REGISTRY_DIR "VIA_SourceInventory.csv"
    @(
        $psFiles | ForEach-Object { [pscustomobject]@{ Lang="PS"; Path=$_.FullName; Bytes=$_.Length; Modified=$_.LastWriteTime } }
        $pyFiles | ForEach-Object { [pscustomobject]@{ Lang="PY"; Path=$_.FullName; Bytes=$_.Length; Modified=$_.LastWriteTime } }
        $jsFiles | ForEach-Object { [pscustomobject]@{ Lang="JS"; Path=$_.FullName; Bytes=$_.Length; Modified=$_.LastWriteTime } }
        $csFiles | ForEach-Object { [pscustomobject]@{ Lang="CS"; Path=$_.FullName; Bytes=$_.Length; Modified=$_.LastWriteTime } }
    ) | Export-Csv -LiteralPath $invPath -NoTypeInformation -Encoding UTF8BOM

    def_AddRow "Round0" "VIA" "M02_DETECT" "INVENTORY" "Inventory CSV" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "file" "ready" "Inventory exported." $invPath
}

# =============================================================================
# def OPTIONAL BASELINE RUNS
# =============================================================================
function def_Round0_OptionalBaselineRuns {
    $pwsh = def_GetPwsh

    if ($RunVdfGate) {
        if (Test-Path -LiteralPath $def_PARAM_VDF_GATE_SCRIPT) {
            def_WriteLine "RUN" "Running VDF Panorama Gate baseline."
            $r = def_InvokeProcess -Name "VDF_PanoramaGate_Baseline" -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$def_PARAM_VDF_GATE_SCRIPT) -WorkingDirectory $def_PARAM_VDF_DIR -TimeoutSec 1800
            def_AddRow "Round0" "VDF" "M00_BASELINE" "PROCESS" "VDF Panorama Gate" ($(if ($r.ExitCode -eq 0) { "OK_EXIT_0" } else { "WARN_EXIT_$($r.ExitCode)" })) ($(if ($r.ExitCode -eq 0) { "LOW" } else { "MEDIUM" })) "SEQUENTIAL_GATED" "BASELINE" "exit_code" ([string]$r.ExitCode) "stdout/stderr saved." $def_PARAM_VDF_GATE_SCRIPT
        } else {
            def_AddRow "Round0" "VDF" "M00_BASELINE" "PROCESS" "VDF Panorama Gate" "WARN_SCRIPT_MISSING" "MEDIUM" "SEQUENTIAL_GATED" "BASELINE" "exists" "false" "VDF gate script not found." $def_PARAM_VDF_GATE_SCRIPT
        }
    } else {
        def_AddRow "Round0" "VDF" "M00_BASELINE" "PROCESS" "VDF Panorama Gate" "WARN_SKIPPED_BY_PARAM" "LOW" "PARALLEL_SAFE" "BASELINE" "enabled" "false" "Use -RunVdfGate to rerun VDF gate." $def_PARAM_VDF_GATE_SCRIPT
    }

    if ($RunPolyglotBaseline) {
        if (Test-Path -LiteralPath $def_PARAM_POLYGLOT_SCRIPT) {
            def_WriteLine "RUN" "Running Polyglot CTR dry-run baseline."
            $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$def_PARAM_POLYGLOT_SCRIPT)
            if ($RunTests) { $args += "-RunTests" }
            $r = def_InvokeProcess -Name "PolyglotCTR_Baseline" -FilePath $pwsh -ArgumentList $args -WorkingDirectory $def_PARAM_ROOT -TimeoutSec 1800
            def_AddRow "Round0" "VIA" "M00_BASELINE" "PROCESS" "Polyglot CTR" ($(if ($r.ExitCode -eq 0) { "OK_EXIT_0" } else { "WARN_EXIT_$($r.ExitCode)" })) ($(if ($r.ExitCode -eq 0) { "LOW" } else { "MEDIUM" })) "SEQUENTIAL_GATED" "BASELINE" "exit_code" ([string]$r.ExitCode) "stdout/stderr saved." $def_PARAM_POLYGLOT_SCRIPT
        } else {
            def_AddRow "Round0" "VIA" "M00_BASELINE" "PROCESS" "Polyglot CTR" "WARN_SCRIPT_MISSING" "MEDIUM" "SEQUENTIAL_GATED" "BASELINE" "exists" "false" "Polyglot CTR script not found." $def_PARAM_POLYGLOT_SCRIPT
        }
    } else {
        def_AddRow "Round0" "VIA" "M00_BASELINE" "PROCESS" "Polyglot CTR" "WARN_SKIPPED_BY_PARAM" "LOW" "PARALLEL_SAFE" "BASELINE" "enabled" "false" "Use -RunPolyglotBaseline to rerun Polyglot CTR." $def_PARAM_POLYGLOT_SCRIPT
    }
}

# =============================================================================
# def ROUND1 LOCATE RED FINDINGS
# =============================================================================
function def_GetChildParserScript {
    $childPath = Join-Path $def_PARAM_RUNTIME_DIR "VIA_PS_ChildParser.ps1"
    if (Test-Path -LiteralPath $childPath) { return $childPath }

    $child = @'
param(
    [Parameter(Mandatory)][string]$LiteralPath
)
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
            EndLine = [int]$e.Extent.EndLineNumber
            EndColumn = [int]$e.Extent.EndColumnNumber
            ErrorId = [string]$e.ErrorId
            Message = [string]$e.Message
            Text = [string]$e.Extent.Text
        }
    }
    @($rows) | ConvertTo-Json -Depth 8 -Compress
    exit 0
}
catch {
    @([pscustomobject]@{
        Line = 0
        Column = 0
        EndLine = 0
        EndColumn = 0
        ErrorId = "ChildParserException"
        Message = [string]$_.Exception.Message
        Text = ""
    }) | ConvertTo-Json -Depth 8 -Compress
    exit 9
}
'@
    def_SaveText -Path $childPath -Text $child
    return $childPath
}

function def_ToSafeLogName {
    param([Parameter(Mandatory)][string]$Text)
    $safe = $Text -replace '[:\\/\*\?"<>\|\s]+', '_'
    if ($safe.Length -gt 90) { $safe = $safe.Substring($safe.Length - 90) }
    return $safe
}

function def_NewParseRow {
    param(
        [Parameter(Mandatory)][System.IO.FileInfo]$File,
        [int]$Line = 0,
        [int]$Column = 0,
        [int]$EndLine = 0,
        [int]$EndColumn = 0,
        [string]$ErrorId = "ParserException",
        [string]$Message = "",
        [string]$Text = ""
    )

    return [pscustomobject]@{
        Path = $File.FullName
        File = $File.Name
        Line = $Line
        Column = $Column
        EndLine = $EndLine
        EndColumn = $EndColumn
        ErrorId = $ErrorId
        Message = $Message
        Text = $Text
    }
}

function def_ParsePSFileWithChildProcess {
    param(
        [Parameter(Mandatory)][System.IO.FileInfo]$File,
        [string]$ParentError = ""
    )

    try {
        $pwsh = def_GetPwsh
        $childParser = def_GetChildParserScript
        $safe = def_ToSafeLogName -Text $File.FullName
        $result = def_InvokeProcess -Name ("ps_ast_child_{0}" -f $safe) -FilePath $pwsh -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $childParser, $File.FullName) -WorkingDirectory $def_PARAM_ROOT -TimeoutSec 120

        $jsonText = ""
        if (Test-Path -LiteralPath $result.Stdout) {
            $jsonText = Get-Content -LiteralPath $result.Stdout -Raw -ErrorAction SilentlyContinue
        }

        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            $stderrText = ""
            if (Test-Path -LiteralPath $result.Stderr) { $stderrText = Get-Content -LiteralPath $result.Stderr -Raw -ErrorAction SilentlyContinue }
            return @(def_NewParseRow -File $File -ErrorId "ChildParserNoOutput" -Message ("Parent parser failed: {0}; child exit={1}; stderr={2}" -f $ParentError, $result.ExitCode, $stderrText))
        }

        $childRows = @($jsonText | ConvertFrom-Json -ErrorAction Stop)
        $outRows = New-Object System.Collections.Generic.List[object]
        foreach ($r in $childRows) {
            $outRows.Add((def_NewParseRow -File $File -Line ([int]$r.Line) -Column ([int]$r.Column) -EndLine ([int]$r.EndLine) -EndColumn ([int]$r.EndColumn) -ErrorId ([string]$r.ErrorId) -Message ([string]$r.Message) -Text ([string]$r.Text))) | Out-Null
        }
        return @($outRows)
    }
    catch {
        return @(def_NewParseRow -File $File -ErrorId "ParserFallbackException" -Message ("Parent parser failed: {0}; fallback failed: {1}" -f $ParentError, $_.Exception.Message))
    }
}

function def_ParsePSFileSafe {
    param([Parameter(Mandatory)][System.IO.FileInfo]$File)

    $rows = New-Object System.Collections.Generic.List[object]
    try {
        # PowerShell AST ParseFile requires strongly typed ref parameters in some sessions.
        # Without these explicit types, PS7 can throw: "Argument types do not match".
        [System.Management.Automation.Language.Token[]]$tokens = $null
        [System.Management.Automation.Language.ParseError[]]$errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile([string]$File.FullName, [ref]$tokens, [ref]$errors) | Out-Null

        foreach ($e in @($errors)) {
            $rows.Add((def_NewParseRow -File $File -Line ([int]$e.Extent.StartLineNumber) -Column ([int]$e.Extent.StartColumnNumber) -EndLine ([int]$e.Extent.EndLineNumber) -EndColumn ([int]$e.Extent.EndColumnNumber) -ErrorId ([string]$e.ErrorId) -Message ([string]$e.Message) -Text ([string]$e.Extent.Text))) | Out-Null
        }
        return @($rows)
    }
    catch {
        return @(def_ParsePSFileWithChildProcess -File $File -ParentError $_.Exception.Message)
    }
}

function def_TestPSParseErrors {
    def_WriteLine "RUN" "Round1 locating PowerShell AST parse errors."

    $psFiles = @(def_GetSourceFiles -Extensions $def_PARAM_PS_EXTENSIONS)
    $parseRows = New-Object System.Collections.Generic.List[object]
    $i = 0
    $total = [Math]::Max(1, (def_CountSafe $psFiles))

    foreach ($file in $psFiles) {
        $i++
        if (($i -eq 1) -or ($i % 10 -eq 0) -or ($i -eq $total)) {
            Write-Progress -Activity "VIA PS AST Parse" -Status ("{0}/{1} {2}" -f $i, $total, $file.Name) -PercentComplete ([Math]::Min(100, [int](($i / $total) * 100)))
        }

        $rowsForFile = @(def_ParsePSFileSafe -File $file)
        foreach ($r in $rowsForFile) {
            if (($r.ErrorId -ne $null) -and ($r.ErrorId -ne "") -and (($r.Line -ne 0) -or ($r.Message -ne ""))) {
                $parseRows.Add($r) | Out-Null
            }
        }
    }
    Write-Progress -Activity "VIA PS AST Parse" -Completed

    $parseCsv = Join-Path $def_PARAM_REGISTRY_DIR "VIA_PS_ParseErrors.csv"
    @($parseRows) | Export-Csv -LiteralPath $parseCsv -NoTypeInformation -Encoding UTF8BOM

    $filesWithErrors = @($parseRows | Select-Object -ExpandProperty Path -Unique)
    if ((def_CountSafe $filesWithErrors) -gt 0) {
        def_AddRow "Round1" "PS" "M04_CHECK" "AST" "PowerShell AST Parse" "FAIL_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "ANALYZE_ONLY" "parse_files/errors" ("{0}/{1}" -f (def_CountSafe $filesWithErrors), (def_CountSafe $parseRows)) "Parse errors must be fixed before broad autofix." $parseCsv
        foreach ($f in $filesWithErrors) {
            $one = @($parseRows | Where-Object { $_.Path -eq $f })[0]
            def_AddRow "Round1" "PS" "M04_CHECK" "AST_DETAIL" $one.File "FAIL_PARSE_DETAIL" "HIGH" "SEQUENTIAL_REQUIRED" "MANUAL_FIRST" "line:col" ("{0}:{1}" -f $one.Line, $one.Column) $one.Message $f
        }
    } else {
        def_AddRow "Round1" "PS" "M04_CHECK" "AST" "PowerShell AST Parse" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "parse_files/errors" ("0/0") "All PowerShell files parse." $parseCsv
    }

    return @($parseRows)
}

function def_ReadLatestPolyglotMatrix {
    $runsDir = Join-Path $def_PARAM_TOOL_ROOT "runs"
    if (-not (Test-Path -LiteralPath $runsDir)) {
        def_AddRow "Round1" "VIA" "M04_CHECK" "REGISTRY" "Latest Polyglot Matrix" "WARN_NOT_FOUND" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "runs_dir" "missing" "No previous Polyglot run directory found." $runsDir
        return @()
    }

    $latest = Get-ChildItem -LiteralPath $runsDir -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $latest) {
        def_AddRow "Round1" "VIA" "M04_CHECK" "REGISTRY" "Latest Polyglot Matrix" "WARN_NOT_FOUND" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "run" "missing" "No previous Polyglot run found." $runsDir
        return @()
    }

    $csv = Get-ChildItem -LiteralPath $latest.FullName -Filter "VIA_PolyglotCTR_Matrix_*.csv" -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $csv) {
        def_AddRow "Round1" "VIA" "M04_CHECK" "REGISTRY" "Latest Polyglot Matrix" "WARN_NOT_FOUND" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "matrix" "missing" "Matrix CSV not found in latest run." $latest.FullName
        return @()
    }

    $rows = @(Import-Csv -LiteralPath $csv.FullName)
    def_AddRow "Round1" "VIA" "M04_CHECK" "REGISTRY" "Latest Polyglot Matrix" "OK_READ" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "rows" ([string](def_CountSafe $rows)) "Previous matrix read." $csv.FullName
    return $rows
}

# =============================================================================
# def ROUND2 REPAIR PLAN
# =============================================================================
function def_Round2_RepairPlan {
    param([object[]]$ParseErrors)

    def_WriteLine "RUN" "Round2 building gated repair plan."

    $parseFiles = @($ParseErrors | Select-Object -ExpandProperty Path -Unique)
    $parseBlock = (def_CountSafe $parseFiles) -gt 0

    if ($parseBlock) {
        def_AddRow "Round2" "VIA" "M06_REPAIR" "GATE" "Hydra Risk Gate" "FAIL_REPAIR_BLOCKED" "HIGH" "SEQUENTIAL_REQUIRED" "GATED" "parse_files" ([string](def_CountSafe $parseFiles)) "Broad PSSA/Ruff autofix is blocked until PS parse errors are repaired." ""
    } else {
        def_AddRow "Round2" "VIA" "M06_REPAIR" "GATE" "Hydra Risk Gate" "OK_REPAIR_ALLOWED" "LOW" "SEQUENTIAL_GATED" "GATED" "parse_files" "0" "No parse blocker. Guarded fixes may be considered." ""
    }

    $plan = New-Object System.Collections.Generic.List[object]
    if ($parseBlock) {
        foreach ($f in $parseFiles) {
            $errs = @($ParseErrors | Where-Object { $_.Path -eq $f })
            $first = $errs[0]
            $plan.Add([pscustomobject]@{
                Priority = "P0"
                FixClass = "SEQUENTIAL_REQUIRED"
                Lang = "PS"
                Path = $f
                Line = $first.Line
                Column = $first.Column
                ErrorId = $first.ErrorId
                Message = $first.Message
                Action = "Open file, fix syntax at first failing extent, rerun this stabilizer."
            }) | Out-Null
        }
    }

    $planCsv = Join-Path $def_PARAM_REGISTRY_DIR "VIA_SequentialRepairPlan.csv"
    $plan | Export-Csv -LiteralPath $planCsv -NoTypeInformation -Encoding UTF8BOM
    def_AddRow "Round2" "VIA" "M06_REPAIR" "PLAN" "Sequential Repair Plan" "OK_WRITTEN" ($(if ($parseBlock) { "HIGH" } else { "LOW" })) "SEQUENTIAL_REQUIRED" "PLAN_ONLY" "rows" ([string](def_CountSafe $plan)) "Sequential plan exported." $planCsv

    $parallelPlan = New-Object System.Collections.Generic.List[object]
    $parallelPlan.Add([pscustomobject]@{
        Priority = "P1"
        FixClass = "PARALLEL_SAFE"
        Lang = "PY"
        Action = "Ruff dry-run / report only until PS parse errors clear."
        Guard = "No write while parse blocker exists."
    }) | Out-Null
    $parallelPlan.Add([pscustomobject]@{
        Priority = "P1"
        FixClass = "PARALLEL_SAFE"
        Lang = "PS"
        Action = "PSScriptAnalyzer report can run; -Fix blocked while parse blocker exists."
        Guard = "No broad write while parse blocker exists."
    }) | Out-Null

    $parallelCsv = Join-Path $def_PARAM_REGISTRY_DIR "VIA_ParallelSafePlan.csv"
    $parallelPlan | Export-Csv -LiteralPath $parallelCsv -NoTypeInformation -Encoding UTF8BOM
    def_AddRow "Round2" "VIA" "M06_REPAIR" "PLAN" "Parallel Safe Plan" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "PLAN_ONLY" "rows" ([string](def_CountSafe $parallelPlan)) "Parallel-safe review plan exported." $parallelCsv

    return $parseBlock
}

function def_RunDryAnalyzers {
    param([bool]$ParseBlock)

    def_WriteLine "RUN" "Round2 running dry analyzers."

    $pssa = Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue
    if ($pssa) {
        $pssaCsv = Join-Path $def_PARAM_REGISTRY_DIR "VIA_PSScriptAnalyzer_Findings.csv"
        try {
            $findings = @(Invoke-ScriptAnalyzer -Path $def_PARAM_ROOT -Recurse -Severity Error,Warning -ErrorAction Continue)
            $findings | Export-Csv -LiteralPath $pssaCsv -NoTypeInformation -Encoding UTF8BOM
            $errCount = @($findings | Where-Object { $_.Severity -eq "Error" }).Count
            $warnCount = @($findings | Where-Object { $_.Severity -eq "Warning" }).Count
            def_AddRow "Round2" "PS" "M04_CHECK" "PSSA" "PSScriptAnalyzer" ($(if ($errCount -gt 0 -or $warnCount -gt 0) { "WARN_ANALYZER" } else { "OK_CLEAN" })) ($(if ($errCount -gt 0) { "MEDIUM" } else { "LOW" })) "PARALLEL_SAFE" "ANALYZE_ONLY" "error/warn" ("{0}/{1}" -f $errCount, $warnCount) "PSSA report generated. -Fix remains gated." $pssaCsv
        } catch {
            def_AddRow "Round2" "PS" "M04_CHECK" "PSSA" "PSScriptAnalyzer" "WARN_ANALYZER_FAILED" "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "error" "exception" $_.Exception.Message $def_PARAM_ROOT
        }
    } else {
        def_AddRow "Round2" "PS" "M04_CHECK" "PSSA" "PSScriptAnalyzer" "WARN_TOOL_MISSING" "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "tool" "missing" "PSScriptAnalyzer not available in this session." ""
    }

    $python = def_GetPython
    if ($python) {
        $ruffCheck = def_InvokeProcess -Name "ruff_check_dry" -FilePath $python -ArgumentList @("-m","ruff","check",$def_PARAM_ROOT,"--exit-zero","--output-format","json") -WorkingDirectory $def_PARAM_ROOT -TimeoutSec 1800
        $ruffJson = Join-Path $def_PARAM_REGISTRY_DIR "VIA_Ruff_Findings.json"
        if (Test-Path -LiteralPath $ruffCheck.Stdout) {
            Copy-Item -LiteralPath $ruffCheck.Stdout -Destination $ruffJson -Force
        }
        def_AddRow "Round2" "PY" "M04_CHECK" "RUFF" "ruff check" ($(if ($ruffCheck.ExitCode -eq 0) { "OK_EXIT_0" } else { "WARN_EXIT_$($ruffCheck.ExitCode)" })) "LOW" "PARALLEL_SAFE" "ANALYZE_ONLY" "exit_code" ([string]$ruffCheck.ExitCode) "ruff dry report generated if ruff is installed." $ruffJson
    } else {
        def_AddRow "Round2" "PY" "M04_CHECK" "RUFF" "ruff check" "WARN_PYTHON_MISSING" "MEDIUM" "PARALLEL_SAFE" "ANALYZE_ONLY" "python" "missing" "Python not resolved." ""
    }
}

function def_Round2_ApplyRepairsIfAllowed {
    param([bool]$ParseBlock)

    $approved = $ApplyRepairs -and ($ApprovalToken -eq $def_PARAM_APPROVAL_TOKEN_REQUIRED)
    if (-not $approved) {
        def_AddRow "Round2" "VIA" "M06_REPAIR" "APPLY" "Repair Mode" "OK_DRY_RUN" "LOW" "SEQUENTIAL_GATED" "REPAIR_DRYRUN" "apply" "false" "No write. To apply, use -ApplyRepairs -ApprovalToken APPROVE_VIA_POLYGLOT_REPAIR after parse errors are clean." ""
        return
    }

    if ($ParseBlock) {
        def_AddRow "Round2" "VIA" "M06_REPAIR" "APPLY" "Repair Mode" "FAIL_BLOCKED_BY_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "REPAIR_BLOCKED" "apply" "false" "Approval received, but parse errors still exist. No write performed." ""
        return
    }

    def_WriteLine "RUN" "Applying guarded repairs."

    $pssa = Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue
    if ($pssa) {
        try {
            Invoke-ScriptAnalyzer -Path $def_PARAM_ROOT -Recurse -Fix -ErrorAction Continue | Out-Null
            def_AddRow "Round2" "PS" "M06_REPAIR" "PSSA_FIX" "PSScriptAnalyzer -Fix" "OK_REPAIR_APPLIED" "LOW" "SEQUENTIAL_GATED" "REPAIR_APPLY" "fix" "done" "PSSA -Fix applied after parse gate clear." $def_PARAM_ROOT
        } catch {
            def_AddRow "Round2" "PS" "M06_REPAIR" "PSSA_FIX" "WARN_REPAIR_FAILED" "MEDIUM" "SEQUENTIAL_GATED" "REPAIR_APPLY" "error" "exception" $_.Exception.Message $def_PARAM_ROOT
        }
    }

    $python = def_GetPython
    if ($python) {
        $r1 = def_InvokeProcess -Name "ruff_fix_apply" -FilePath $python -ArgumentList @("-m","ruff","check",$def_PARAM_ROOT,"--fix") -WorkingDirectory $def_PARAM_ROOT -TimeoutSec 1800
        def_AddRow "Round2" "PY" "M06_REPAIR" "RUFF_FIX" "ruff --fix" ($(if ($r1.ExitCode -eq 0) { "OK_REPAIR_APPLIED" } else { "WARN_EXIT_$($r1.ExitCode)" })) ($(if ($r1.ExitCode -eq 0) { "LOW" } else { "MEDIUM" })) "SEQUENTIAL_GATED" "REPAIR_APPLY" "exit_code" ([string]$r1.ExitCode) "ruff fix attempted after parse gate clear." $def_PARAM_ROOT

        $r2 = def_InvokeProcess -Name "ruff_format_apply" -FilePath $python -ArgumentList @("-m","ruff","format",$def_PARAM_ROOT) -WorkingDirectory $def_PARAM_ROOT -TimeoutSec 1800
        def_AddRow "Round2" "PY" "M06_REPAIR" "RUFF_FORMAT" "ruff format" ($(if ($r2.ExitCode -eq 0) { "OK_REPAIR_APPLIED" } else { "WARN_EXIT_$($r2.ExitCode)" })) ($(if ($r2.ExitCode -eq 0) { "LOW" } else { "MEDIUM" })) "SEQUENTIAL_GATED" "REPAIR_APPLY" "exit_code" ([string]$r2.ExitCode) "ruff format attempted after parse gate clear." $def_PARAM_ROOT
    }
}

# =============================================================================
# def ROUND3 CONSOLIDATE
# =============================================================================
function def_Round3_Consolidate {
    def_WriteLine "RUN" "Round3 consolidation started."

    $rows = @($script:def_ROWS)
    $matrixCsv = Join-Path $def_PARAM_RUN_ROOT "VIA_RedFindingStabilizer_Matrix.csv"
    $matrixJson = Join-Path $def_PARAM_RUN_ROOT "VIA_RedFindingStabilizer_Matrix.json"
    $resultJson = Join-Path $def_PARAM_RUNTIME_DIR "via_red_finding_stabilizer_result.json"
    $reportHtml = Join-Path $def_PARAM_REPORT_DIR "VIA_RedFindingStabilizer_Report.html"

    $rows | Export-Csv -LiteralPath $matrixCsv -NoTypeInformation -Encoding UTF8BOM
    $rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $matrixJson -Encoding UTF8

    $ok = @($rows | Where-Object { $_.Status -like "OK*" }).Count
    $warn = @($rows | Where-Object { $_.Status -like "WARN*" }).Count
    $fail = @($rows | Where-Object { $_.Status -like "FAIL*" }).Count
    $high = @($rows | Where-Object { $_.Risk -eq "HIGH" }).Count
    $risk = if ($fail -gt 0 -or $high -gt 0) { "HIGH" } elseif ($warn -gt 0) { "MEDIUM" } else { "LOW" }
    $status = if ($risk -eq "HIGH") { "VIA_RED_FINDING_STABILIZER_PARSE_BLOCKED" } elseif ($risk -eq "MEDIUM") { "VIA_RED_FINDING_STABILIZER_READY_WITH_WARNINGS" } else { "VIA_RED_FINDING_STABILIZER_READY" }

    [pscustomobject]@{
        run_id = $def_PARAM_RUN_ID
        root = $def_PARAM_ROOT
        status = $status
        risk = $risk
        ok = $ok
        warn = $warn
        fail = $fail
        apply_repairs = [bool]$ApplyRepairs
        approved = ($ApprovalToken -eq $def_PARAM_APPROVAL_TOKEN_REQUIRED)
        report_html = $reportHtml
        matrix_csv = $matrixCsv
        matrix_json = $matrixJson
        policy = @{
            no_db_write = $def_PARAM_NO_DB_WRITE
            no_canonical_merge = $def_PARAM_NO_CANONICAL_MERGE
            no_destructive_delete = $def_PARAM_NO_DESTRUCTIVE_DELETE
            no_stop_process = $def_PARAM_NO_STOP_PROCESS
            append_only = $def_PARAM_APPEND_ONLY
        }
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultJson -Encoding UTF8

    def_WriteHtmlReport -Path $reportHtml -Rows $rows

    def_AddRow "Round3" "VIA" "M07_REPORT" "CONSOLIDATE" "Final Artifacts" "OK_CONSOLIDATED" "LOW" "PARALLEL_SAFE" "REPORT" "dir" "ready" "CSV/JSON/HTML report written." $def_PARAM_RUN_ROOT

    # Rewrite final report including the final artifact row.
    $rows = @($script:def_ROWS)
    $rows | Export-Csv -LiteralPath $matrixCsv -NoTypeInformation -Encoding UTF8BOM
    $rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $matrixJson -Encoding UTF8
    def_WriteHtmlReport -Path $reportHtml -Rows $rows

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA RED-FINDING STABILIZER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status      : $status"
    Write-Host "Risk        : $risk"
    Write-Host "OK/WARN/FAIL: $ok / $warn / $fail"
    Write-Host "Run Root    : $def_PARAM_RUN_ROOT"
    Write-Host "HTML        : $reportHtml"
    Write-Host "Matrix CSV  : $matrixCsv"
    Write-Host "Result JSON : $resultJson"
    Write-Host ""

    if ($OpenReport -and (Test-Path -LiteralPath $reportHtml)) {
        Start-Process $reportHtml
    }
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA Polyglot Red-Finding Stabilizer v01.2.2" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Root        : $def_PARAM_ROOT"
    Write-Host "Run ID      : $def_PARAM_RUN_ID"
    Write-Host "Repair mode : $(if ($ApplyRepairs) { 'APPLY_REQUESTED' } else { 'DRY_RUN' })"
    Write-Host "Policy      : no DB write · no canonical merge · no destructive delete · no stop-process · append-only"
    Write-Host ""

    def_Round0_Inventory
    def_Round0_OptionalBaselineRuns

    $previousMatrix = def_ReadLatestPolyglotMatrix
    if ((def_CountSafe $previousMatrix) -gt 0) {
        $redRows = @($previousMatrix | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
        def_AddRow "Round1" "VIA" "M04_CHECK" "PREVIOUS" "Previous Red Findings" ($(if ((def_CountSafe $redRows) -gt 0) { "WARN_PREVIOUS_RED" } else { "OK_PREVIOUS_CLEAR" })) ($(if ((def_CountSafe $redRows) -gt 0) { "MEDIUM" } else { "LOW" })) "SEQUENTIAL_GATED" "ANALYZE_ONLY" "rows" ([string](def_CountSafe $redRows)) "Previous Polyglot red findings summarized." ""
    }

    $parseErrors = def_TestPSParseErrors
    $parseBlock = def_Round2_RepairPlan -ParseErrors $parseErrors
    def_RunDryAnalyzers -ParseBlock $parseBlock
    def_Round2_ApplyRepairsIfAllowed -ParseBlock $parseBlock
    def_Round3_Consolidate
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddRow "FATAL" "VIA" "M99_FATAL" "EXCEPTION" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "STOP" "error" "exception" $_.Exception.Message ""
        def_Round3_Consolidate
    } catch {}
    Write-Host ""
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

