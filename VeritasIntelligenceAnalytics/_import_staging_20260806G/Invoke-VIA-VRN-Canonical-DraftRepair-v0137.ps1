#requires -Version 7.0
<#
====================================================================================================
def VIA · VRN CANONICAL RUNTIME DIAGNOSIS / DRAFT-ONLY REPAIR · v0137
====================================================================================================
Purpose
-------
- Confirm v0136A FULL_VRN_VDF_ACTIVATION_SUCCESS.
- Preserve the successful fallback runtime.
- Inspect only functional modules\VRN\Invoke-VRN.ps1.
- Capture the exact runtime exception line/column/stack in an isolated child process.
- Detect command-as-method syntax such as Command-Name(...).
- Generate a run-local repaired draft only when the runtime line maps to exactly one safe candidate.
- Validate the repaired draft with PowerShell AST.
- Never overwrite, rename, delete, move or execute the canonical file after diagnosis.
- No broad scan, no organization rerun, no VDF/VRN restart, no Stop-Process.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [bool]$OpenHtmlReport = $true,
    [bool]$KeepParentPowerShellOpen = $true,
    [int]$ProbeSeconds = 20,
    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0137_DRAFT_ONLY_CANONICAL_DIAGNOSIS"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0137_DRAFT_ONLY_CANONICAL_DIAGNOSIS"
$Version = "v0137"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$CanonicalPath = Join-Path $BaseDir "functional modules\VRN\Invoke-VRN.ps1"
$RunDir = Join-Path $BaseDir "_via_vrn_canonical_draft_repair_runs\RUN_${Stamp}_VIA_VRN_CANONICAL_DRAFT_REPAIR_v0137"

$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$SandboxDir = Join-Path $RunDir "sandbox"
$LogDir = Join-Path $RunDir "logs"

$RuntimeProbeScript = Join-Path $SandboxDir "Probe-Invoke-VRN-Canonical-v0137.ps1"
$RuntimeEvidenceJson = Join-Path $JsonDir "VRN_Canonical_RuntimeEvidence.v0137.json"
$StaticCandidatesCsv = Join-Path $CsvDir "VRN_Canonical_StaticCandidates.v0137.csv"
$StaticCandidatesJson = Join-Path $JsonDir "VRN_Canonical_StaticCandidates.v0137.json"
$PatchEvidenceJson = Join-Path $JsonDir "VRN_Canonical_DraftPatchEvidence.v0137.json"
$SummaryJson = Join-Path $JsonDir "summary.v0137.json"
$ReportHtml = Join-Path $HtmlDir "VIA_VRN_Canonical_DraftRepair_Matrix_v0137.html"

$DraftPath = Join-Path $SandboxDir "Invoke-VRN.v0137.proposed.ps1"
$OriginalSnapshotPath = Join-Path $SandboxDir "Invoke-VRN.v0137.original.snapshot.ps1"
$ProbeStdout = Join-Path $LogDir "canonical_probe.stdout.log"
$ProbeStderr = Join-Path $LogDir "canonical_probe.stderr.log"

function Ensure-Directory {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-JsonFile {
    param(
        $Data,

        [Parameter(Mandatory)]
        [string]$Path
    )

    Ensure-Directory -Path (Split-Path -Parent $Path)

    $Data |
        ConvertTo-Json -Depth 100 |
        Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-CsvFile {
    param(
        $Data,

        [Parameter(Mandatory)]
        [string]$Path
    )

    Ensure-Directory -Path (Split-Path -Parent $Path)

    @($Data) |
        Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function Test-PowerShellAst {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $tokens = $null
    $errors = $null

    try {
        [System.Management.Automation.Language.Parser]::ParseFile(
            $Path,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        return [pscustomobject]@{
            parse_ok = (@($errors).Count -eq 0)
            error_count = @($errors).Count
            first_error = if (@($errors).Count -gt 0) {
                [string]$errors[0].Message
            }
            else {
                ""
            }
        }
    }
    catch {
        return [pscustomobject]@{
            parse_ok = $false
            error_count = 1
            first_error = $_.Exception.Message
        }
    }
}

function Find-LatestV0136ASummary {
    $root = Join-Path $BaseDir "_via_vrn_fallback_activation_runs"

    if (-not (Test-Path -LiteralPath $root)) {
        return $null
    }

    $summaryFiles = @(
        Get-ChildItem `
            -LiteralPath $root `
            -Recurse `
            -File `
            -Filter "summary.v0136A.json" `
            -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    )

    foreach ($file in $summaryFiles) {
        try {
            $data = (
                Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 |
                ConvertFrom-Json
            )

            if ([string]$data.gate -eq "FULL_VRN_VDF_ACTIVATION_SUCCESS") {
                return [pscustomobject]@{
                    path = $file.FullName
                    data = $data
                }
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Get-StaticCommandAsMethodCandidates {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    $rows = @()

    $excludedCommands = @(
        "if",
        "elseif",
        "while",
        "for",
        "foreach",
        "switch",
        "function",
        "filter",
        "class",
        "enum",
        "return",
        "throw",
        "catch",
        "param",
        "begin",
        "process",
        "end",
        "data",
        "do",
        "until",
        "trap"
    )

    $pattern = '^(?<indent>\s*)(?<prefix>(?:\$[A-Za-z_][A-Za-z0-9_:]*\s*=\s*)?)(?<command>[A-Za-z_][A-Za-z0-9_-]*)\s*\((?<arguments>.*)\)(?<suffix>\s*(?:;.*|#.*)?)$'

    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = [string]$lines[$index]
        $match = [regex]::Match($line, $pattern)

        if (-not $match.Success) {
            continue
        }

        $command = [string]$match.Groups["command"].Value

        if ($excludedCommands -contains $command.ToLowerInvariant()) {
            continue
        }

        $arguments = [string]$match.Groups["arguments"].Value
        $prefix = [string]$match.Groups["prefix"].Value
        $indent = [string]$match.Groups["indent"].Value
        $suffix = [string]$match.Groups["suffix"].Value

        $proposedLine = "{0}{1}{2}" -f $indent, $prefix, $command

        if (-not [string]::IsNullOrWhiteSpace($arguments)) {
            $proposedLine += " " + $arguments.Trim()
        }

        $proposedLine += $suffix

        $rows += [pscustomobject]@{
            line_number = $index + 1
            command = $command
            original_line = $line
            proposed_line = $proposedLine
            rule = "REMOVE_COMMAND_CALL_PARENTHESES_DRAFT_ONLY"
        }
    }

    return @($rows)
}

function Write-RuntimeProbeScript {
    param(
        [Parameter(Mandatory)]
        [string]$Destination
    )

    $template = @'
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CanonicalPath = "__CANONICAL_PATH__"
$EvidencePath = "__EVIDENCE_PATH__"

$evidence = [ordered]@{
    canonical_path = $CanonicalPath
    probe_started_at = (Get-Date).ToString("o")
    completed_without_exception = $false
    exception_type = ""
    exception_message = ""
    script_name = ""
    script_line_number = 0
    offset_in_line = 0
    line_text = ""
    position_message = ""
    script_stack_trace = ""
    invocation_name = ""
    probe_pid = $PID
    probe_completed_at = ""
}

try {
    & $CanonicalPath
    $evidence.completed_without_exception = $true
}
catch {
    $evidence.exception_type = $_.Exception.GetType().FullName
    $evidence.exception_message = $_.Exception.Message
    $evidence.script_name = [string]$_.InvocationInfo.ScriptName
    $evidence.script_line_number = [int]$_.InvocationInfo.ScriptLineNumber
    $evidence.offset_in_line = [int]$_.InvocationInfo.OffsetInLine
    $evidence.line_text = [string]$_.InvocationInfo.Line
    $evidence.position_message = [string]$_.InvocationInfo.PositionMessage
    $evidence.script_stack_trace = [string]$_.ScriptStackTrace
    $evidence.invocation_name = [string]$_.InvocationInfo.InvocationName
}
finally {
    $evidence.probe_completed_at = (Get-Date).ToString("o")
    $temporaryPath = "$EvidencePath.tmp.$PID"

    $evidence |
        ConvertTo-Json -Depth 40 |
        Set-Content -LiteralPath $temporaryPath -Encoding UTF8

    Move-Item `
        -LiteralPath $temporaryPath `
        -Destination $EvidencePath `
        -Force
}
'@

    $content = $template.
        Replace("__CANONICAL_PATH__", $CanonicalPath).
        Replace("__EVIDENCE_PATH__", $RuntimeEvidenceJson)

    Set-Content -LiteralPath $Destination -Value $content -Encoding UTF8
}

function Invoke-RuntimeProbe {
    Write-RuntimeProbeScript -Destination $RuntimeProbeScript

    $probeCheck = Test-PowerShellAst -Path $RuntimeProbeScript

    if (-not $probeCheck.parse_ok) {
        throw "Runtime probe AST failed: $($probeCheck.first_error)"
    }

    if (Test-Path -LiteralPath $RuntimeEvidenceJson) {
        Remove-Item `
            -LiteralPath $RuntimeEvidenceJson `
            -Force `
            -ErrorAction SilentlyContinue
    }

    $pwsh = (Get-Command pwsh -ErrorAction Stop).Source

    $process = Start-Process `
        -FilePath $pwsh `
        -ArgumentList @(
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $RuntimeProbeScript
        ) `
        -RedirectStandardOutput $ProbeStdout `
        -RedirectStandardError $ProbeStderr `
        -PassThru

    $finished = $process.WaitForExit($ProbeSeconds * 1000)

    if (-not $finished) {
        return [pscustomobject]@{
            state = "PROBE_STILL_RUNNING_NO_STOP_PROCESS"
            process_id = $process.Id
            exit_code = $null
            evidence_exists = (Test-Path -LiteralPath $RuntimeEvidenceJson)
            error = "Probe did not exit within the configured interval. It was not terminated."
        }
    }

    $process.Refresh()

    return [pscustomobject]@{
        state = "PROBE_EXITED"
        process_id = $process.Id
        exit_code = $process.ExitCode
        evidence_exists = (Test-Path -LiteralPath $RuntimeEvidenceJson)
        error = ""
    }
}

function ConvertTo-HtmlEncoded {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function ConvertTo-SafeHtmlTable {
    param(
        $Rows
    )

    $array = @($Rows)

    if ($array.Count -eq 0) {
        return "<div class='empty'>No rows.</div>"
    }

    $propertyMap = [ordered]@{}

    foreach ($row in $array) {
        foreach ($propertyName in @($row.PSObject.Properties.Name)) {
            if (-not $propertyMap.Contains($propertyName)) {
                $propertyMap[$propertyName] = $true
            }
        }
    }

    $propertyNames = @($propertyMap.Keys)
    $builder = New-Object System.Text.StringBuilder

    [void]$builder.AppendLine("<div class='table-wrap'><table><thead><tr>")

    foreach ($propertyName in $propertyNames) {
        [void]$builder.AppendLine(
            "<th>$(ConvertTo-HtmlEncoded -Value $propertyName)</th>"
        )
    }

    [void]$builder.AppendLine("</tr></thead><tbody>")

    foreach ($row in $array) {
        [void]$builder.AppendLine("<tr>")

        foreach ($propertyName in $propertyNames) {
            $property = $row.PSObject.Properties[$propertyName]
            $value = if ($null -ne $property) {
                $property.Value
            }
            else {
                ""
            }

            [void]$builder.AppendLine(
                "<td>$(ConvertTo-HtmlEncoded -Value $value)</td>"
            )
        }

        [void]$builder.AppendLine("</tr>")
    }

    [void]$builder.AppendLine("</tbody></table></div>")
    return $builder.ToString()
}

function Write-HtmlReport {
    param(
        [Parameter(Mandatory)]
        $Summary,

        [Parameter(Mandatory)]
        $RuntimeEvidence,

        [Parameter(Mandatory)]
        $StaticCandidates,

        [Parameter(Mandatory)]
        $PatchEvidence
    )

    $gateClass = if ($Summary.gate -eq "DRAFT_REPAIR_READY_FOR_REVIEW") {
        "ok"
    }
    elseif ($Summary.gate -like "*REVIEW*") {
        "warn"
    }
    else {
        "bad"
    }

    $css = @'
<style>
body{margin:0;padding:24px;background:#f7f8f6;color:#24312f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:12px}
h1{font-size:23px;margin:0 0 6px}
h2{font-size:17px;margin-top:25px;border-left:5px solid #0f766e;padding-left:9px}
.card{background:#fff;border:1px solid #d8e2df;border-radius:13px;padding:14px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px}
.metric{border:1px solid #d8e2df;border-radius:10px;padding:10px;min-height:70px}
.k{font-size:10px;color:#63706d}.v{font-size:15px;font-weight:800;margin-top:4px;overflow-wrap:anywhere}
.ok{color:#18794e}.warn{color:#9a6700}.bad{color:#b42318}
.table-wrap{width:100%;overflow:auto;max-height:620px;border:1px solid #d8e2df;border-radius:9px}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th{position:sticky;top:0;background:#e7efed;padding:6px;border:1px solid #d2dfdc;text-align:left}
td{padding:5px 6px;border:1px solid #e2eae8;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:460px}
tr:nth-child(even){background:#fbfcfb}
.code{font-family:Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.empty{padding:14px;color:#63706d}
</style>
'@

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA VRN Canonical Draft Repair v0137</title>
$css
</head>
<body>
<h1>VIA · VRN Canonical Runtime Diagnosis / Draft-Only Repair · v0137</h1>

<div class="card">
<div class="grid">
<div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(ConvertTo-HtmlEncoded -Value $Summary.gate)</div></div>
<div class="metric"><div class="k">Fallback Runtime</div><div class="v">PRESERVED</div></div>
<div class="metric"><div class="k">Canonical Mutated</div><div class="v">NO</div></div>
<div class="metric"><div class="k">Runtime Line</div><div class="v">$($Summary.runtime_line)</div></div>
<div class="metric"><div class="k">Static Candidates</div><div class="v">$($Summary.static_candidates)</div></div>
<div class="metric"><div class="k">Draft AST</div><div class="v">$(ConvertTo-HtmlEncoded -Value $Summary.draft_ast)</div></div>
</div>
</div>

<h2>Decision</h2>
<div class="card code">$(ConvertTo-HtmlEncoded -Value $Summary.decision)

Next: $(ConvertTo-HtmlEncoded -Value $Summary.next_step)</div>

<h2>Runtime Exception Evidence</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows @($RuntimeEvidence))</div>

<h2>Static Command-as-Method Candidates</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows $StaticCandidates)</div>

<h2>Draft Patch Evidence</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows @($PatchEvidence))</div>

<h2>Output Paths</h2>
<div class="card code">
Canonical: $(ConvertTo-HtmlEncoded -Value $CanonicalPath)
Original snapshot: $(ConvertTo-HtmlEncoded -Value $OriginalSnapshotPath)
Draft candidate: $(ConvertTo-HtmlEncoded -Value $DraftPath)
RunDir: $(ConvertTo-HtmlEncoded -Value $RunDir)
HTML: $(ConvertTo-HtmlEncoded -Value $ReportHtml)
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportHtml -Value $html -Encoding UTF8
}

try {
    if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) {
        throw "Approval phrase mismatch."
    }

    foreach ($directory in @(
        $RunDir,
        $CsvDir,
        $JsonDir,
        $HtmlDir,
        $SandboxDir,
        $LogDir
    )) {
        Ensure-Directory -Path $directory
    }

    Write-Host "def [BOOT] v0137 draft-only canonical diagnosis started." -ForegroundColor Cyan

    $v0136ASummary = Find-LatestV0136ASummary

    if ($null -eq $v0136ASummary) {
        throw "No FULL_VRN_VDF_ACTIVATION_SUCCESS v0136A summary found."
    }

    Write-Host ("def [AUTHORITY] v0136A success confirmed: {0}" -f $v0136ASummary.path) -ForegroundColor Green

    if (-not (Test-Path -LiteralPath $CanonicalPath)) {
        throw "Canonical Invoke-VRN.ps1 is missing."
    }

    $canonicalAst = Test-PowerShellAst -Path $CanonicalPath

    if (-not $canonicalAst.parse_ok) {
        throw "Canonical AST is no longer clean: $($canonicalAst.first_error)"
    }

    $canonicalHash = (
        Get-FileHash -LiteralPath $CanonicalPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    Copy-Item `
        -LiteralPath $CanonicalPath `
        -Destination $OriginalSnapshotPath `
        -Force

    $staticCandidates = @(
        Get-StaticCommandAsMethodCandidates -Path $CanonicalPath
    )

    Write-CsvFile -Data $staticCandidates -Path $StaticCandidatesCsv
    Write-JsonFile -Data $staticCandidates -Path $StaticCandidatesJson

    Write-Host ("def [STATIC] Command-as-method candidates: {0}" -f $staticCandidates.Count) -ForegroundColor Cyan

    $probeResult = Invoke-RuntimeProbe
    Write-Host ("def [PROBE] {0}; PID={1}" -f $probeResult.state, $probeResult.process_id) -ForegroundColor Cyan

    $runtimeEvidence = if (Test-Path -LiteralPath $RuntimeEvidenceJson) {
        Get-Content -LiteralPath $RuntimeEvidenceJson -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    else {
        [pscustomobject]@{
            canonical_path = $CanonicalPath
            completed_without_exception = $false
            exception_type = ""
            exception_message = ""
            script_name = ""
            script_line_number = 0
            offset_in_line = 0
            line_text = ""
            position_message = ""
            script_stack_trace = ""
            invocation_name = ""
            probe_state = $probeResult.state
            probe_error = $probeResult.error
        }
    }

    $runtimeLine = [int]$runtimeEvidence.script_line_number
    $matchingCandidates = @(
        $staticCandidates |
        Where-Object { [int]$_.line_number -eq $runtimeLine }
    )

    $patchAppliedToDraft = $false
    $draftAstState = "NOT_CREATED"
    $patchReason = ""
    $originalLine = ""
    $proposedLine = ""
    $proposedHash = ""

    if (
        $runtimeLine -gt 0 -and
        $matchingCandidates.Count -eq 1
    ) {
        $selectedCandidate = $matchingCandidates[0]
        $lines = @(Get-Content -LiteralPath $CanonicalPath -Encoding UTF8)

        $originalLine = [string]$lines[$runtimeLine - 1]
        $proposedLine = [string]$selectedCandidate.proposed_line

        $lines[$runtimeLine - 1] = $proposedLine

        Set-Content `
            -LiteralPath $DraftPath `
            -Value $lines `
            -Encoding UTF8

        $draftCheck = Test-PowerShellAst -Path $DraftPath
        $draftAstState = if ($draftCheck.parse_ok) {
            "GREEN_POWERSHELL_AST_PASS"
        }
        else {
            "FAIL: $($draftCheck.first_error)"
        }

        if ($draftCheck.parse_ok) {
            $patchAppliedToDraft = $true
            $patchReason = "Runtime line matched exactly one static command-as-method candidate."
            $proposedHash = (
                Get-FileHash -LiteralPath $DraftPath -Algorithm SHA256
            ).Hash.ToLowerInvariant()
        }
        else {
            $patchReason = "Draft replacement failed AST validation."
        }
    }
    elseif ($runtimeLine -le 0) {
        $patchReason = "Runtime probe did not identify a canonical source line."
    }
    elseif ($matchingCandidates.Count -eq 0) {
        $patchReason = "Runtime line did not match the conservative command-as-method detector."
    }
    else {
        $patchReason = "Runtime line matched more than one candidate; no automatic draft was generated."
    }

    $patchEvidence = [pscustomobject]@{
        canonical_path = $CanonicalPath
        canonical_sha256 = $canonicalHash
        canonical_mutated = $false
        runtime_line = $runtimeLine
        runtime_line_text = [string]$runtimeEvidence.line_text
        matching_candidate_count = $matchingCandidates.Count
        draft_path = if ($patchAppliedToDraft) { $DraftPath } else { "" }
        draft_created = $patchAppliedToDraft
        draft_ast = $draftAstState
        original_line = $originalLine
        proposed_line = $proposedLine
        proposed_sha256 = $proposedHash
        reason = $patchReason
    }

    Write-JsonFile -Data $patchEvidence -Path $PatchEvidenceJson

    $gate = "CANONICAL_DIAGNOSIS_REVIEW_REQUIRED"
    $risk = "MEDIUM_REVIEW"
    $decision = "Runtime evidence was collected, but no single AST-clean repair draft was established."
    $nextStep = "Review runtime and static evidence; keep the v0136A fallback as the active VRN entrypoint."

    if ($patchAppliedToDraft) {
        $gate = "DRAFT_REPAIR_READY_FOR_REVIEW"
        $risk = "LOW_DRAFT_ONLY"
        $decision = "The runtime line matched exactly one conservative command-as-method candidate. An AST-clean draft was created; canonical Invoke-VRN.ps1 remains untouched."
        $nextStep = "Review original_line versus proposed_line before any hash-state canonical promotion."
    }

    $summary = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        gate = $gate
        risk = $risk
        decision = $decision
        next_step = $nextStep
        v0136A_gate = [string]$v0136ASummary.data.gate
        fallback_runtime_preserved = $true
        canonical_path = $CanonicalPath
        canonical_sha256 = $canonicalHash
        canonical_mutated = $false
        runtime_exception = [string]$runtimeEvidence.exception_message
        runtime_line = $runtimeLine
        static_candidates = $staticCandidates.Count
        matching_candidates = $matchingCandidates.Count
        draft_path = if ($patchAppliedToDraft) { $DraftPath } else { "" }
        draft_ast = $draftAstState
        run_dir = $RunDir
        html = $ReportHtml
    }

    Write-JsonFile -Data $summary -Path $SummaryJson

    Write-HtmlReport `
        -Summary ([pscustomobject]$summary) `
        -RuntimeEvidence $runtimeEvidence `
        -StaticCandidates $staticCandidates `
        -PatchEvidence $patchEvidence

    if ($OpenHtmlReport) {
        Start-Process -FilePath $ReportHtml
    }

    Write-Host ""
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
    Write-Host "def VIA · v0137 FINAL RESULT" -ForegroundColor Cyan
    Write-Host ("def Gate                    : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                    : {0}" -f $summary.risk) -ForegroundColor Yellow
    Write-Host "def FallbackRuntimePreserved: True" -ForegroundColor Green
    Write-Host "def CanonicalMutated        : False" -ForegroundColor Green
    Write-Host ("def CanonicalSHA256         : {0}" -f $summary.canonical_sha256) -ForegroundColor DarkGray
    Write-Host ("def RuntimeException        : {0}" -f $summary.runtime_exception) -ForegroundColor Red
    Write-Host ("def RuntimeLine             : {0}" -f $summary.runtime_line) -ForegroundColor White
    Write-Host ("def StaticCandidates        : {0}" -f $summary.static_candidates) -ForegroundColor White
    Write-Host ("def MatchingCandidates      : {0}" -f $summary.matching_candidates) -ForegroundColor White
    Write-Host ("def DraftAST                : {0}" -f $summary.draft_ast) -ForegroundColor Green
    Write-Host ("def DraftPath               : {0}" -f $summary.draft_path) -ForegroundColor Cyan
    Write-Host ("def RunDir                  : {0}" -f $summary.run_dir) -ForegroundColor Cyan
    Write-Host ("def HTML                    : {0}" -f $summary.html) -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "def VIA · v0137 OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def Canonical Invoke-VRN.ps1 was not modified." -ForegroundColor Yellow
}
finally {
    if ($KeepParentPowerShellOpen) {
        Write-Host ""
        Write-Host "def Parent PowerShell remains open. Fallback runtime remains authoritative." -ForegroundColor Cyan
    }
}
