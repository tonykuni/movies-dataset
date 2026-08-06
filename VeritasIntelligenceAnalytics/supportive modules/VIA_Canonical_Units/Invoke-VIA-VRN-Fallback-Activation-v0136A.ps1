#requires -Version 7.0
<#
====================================================================================================
def VIA · VRN FALLBACK ENTRYPOINT RESOLVER / ACTIVATION · v0136A
====================================================================================================
Continuation policy:
- Reuse v0134 organization evidence. Do not rescan or reorganize.
- Preserve v0135 VDF COMPLETED state.
- Exclude the runtime-failed canonical Invoke-VRN.ps1 from retry.
- Evaluate only the known VRN entrypoint candidates.
- Import the approved supportive set: non-empty modules load; empty placeholders skip.
- Attempt candidates sequentially using EncodedCommand.
- Stop after the first candidate reaches ENTRYPOINT_STARTED or COMPLETED.
- No delete, no Stop-Process, no canonical edit.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [bool]$ActivateVrn = $true,
    [bool]$OpenHtmlReport = $true,
    [bool]$KeepParentPowerShellOpen = $true,
    [int]$ProbeSeconds = 12,
    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0136A_VRN_FALLBACK_ACTIVATION"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0136A_VRN_FALLBACK_ACTIVATION"
$Version = "v0136A"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$RunDir = Join-Path $BaseDir "_via_vrn_fallback_activation_runs\RUN_${Stamp}_VIA_VRN_FALLBACK_ACTIVATION_v0136A"
$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$CandidateDir = Join-Path $RunDir "runtime_candidate"

$PersistentRoot = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0136A"
$PersistentLauncherDir = Join-Path $PersistentRoot "launcher"
$PersistentLogDir = Join-Path $PersistentRoot "logs"
$PersistentManifestDir = Join-Path $PersistentRoot "manifests"
$PersistentHtmlDir = Join-Path $PersistentRoot "html"

$SupportiveSource = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\manifests\supportive_loaded_modules.v0135.json"
$SupportiveDeployed = Join-Path $PersistentManifestDir "supportive_loaded_modules.v0136A.json"

$CandidateCsv = Join-Path $CsvDir "VRN_EntrypointCandidateMatrix.v0136A.csv"
$CandidateJson = Join-Path $JsonDir "VRN_EntrypointCandidateMatrix.v0136A.json"
$AttemptCsv = Join-Path $CsvDir "VRN_ActivationAttemptEvidence.v0136A.csv"
$AttemptJson = Join-Path $JsonDir "VRN_ActivationAttemptEvidence.v0136A.json"
$SummaryJson = Join-Path $JsonDir "summary.v0136A.json"
$ReportHtml = Join-Path $HtmlDir "VIA_VRN_Fallback_Activation_Matrix_v0136A.html"

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
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $Path,
            [ref]$tokens,
            [ref]$errors
        )

        return [pscustomobject]@{
            ast = $ast
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
            ast = $null
            parse_ok = $false
            error_count = 1
            first_error = $_.Exception.Message
        }
    }
}

function Get-ParameterMetadata {
    param(
        $Ast
    )

    $allNames = @()
    $mandatoryWithoutDefault = @()
    $defaultedNames = @()

    if ($null -ne $Ast -and $null -ne $Ast.ParamBlock) {
        foreach ($parameter in @($Ast.ParamBlock.Parameters)) {
            $name = [string]$parameter.Name.VariablePath.UserPath
            $allNames += $name

            if ($null -ne $parameter.DefaultValue) {
                $defaultedNames += $name
            }

            $mandatory = $false

            foreach ($attribute in @($parameter.Attributes)) {
                if ([string]$attribute.TypeName.FullName -match "Parameter") {
                    foreach ($namedArgument in @($attribute.NamedArguments)) {
                        if (
                            [string]$namedArgument.ArgumentName -eq "Mandatory" -and
                            [string]$namedArgument.Argument.Extent.Text -match "(?i)\$?true"
                        ) {
                            $mandatory = $true
                        }
                    }
                }
            }

            if ($mandatory -and $null -eq $parameter.DefaultValue) {
                $mandatoryWithoutDefault += $name
            }
        }
    }

    return [pscustomobject]@{
        parameters = ($allNames -join ";")
        mandatory_without_default = ($mandatoryWithoutDefault -join ";")
        mandatory_count = @($mandatoryWithoutDefault).Count
        defaulted_parameters = ($defaultedNames -join ";")
    }
}

function ConvertTo-EncodedCommand {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptPath
    )

    $escaped = $ScriptPath.Replace("'", "''")
    $command = "& '$escaped'"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($command)

    return [Convert]::ToBase64String($bytes)
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
        $Rows,
        [int]$MaxRows = 500
    )

    $array = @($Rows)

    if ($array.Count -eq 0) {
        return "<div class='empty'>No rows.</div>"
    }

    $propertyMap = [ordered]@{}

    foreach ($row in $array) {
        if ($null -eq $row) {
            continue
        }

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

    foreach ($row in @($array | Select-Object -First $MaxRows)) {
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

function Get-VrnCandidateMatrix {
    $vrnRoot = Join-Path $BaseDir "functional modules\VRN"

    $candidateDefinitions = @(
        [pscustomobject]@{
            priority = 10
            name = "Invoke-VRN-PURE-NOHANG-v2192.ps1"
            role = "NOHANG_PRIMARY_FALLBACK"
        },
        [pscustomobject]@{
            priority = 20
            name = "Invoke-VRN-Guarded-Entry-v217.ps1"
            role = "GUARDED_FALLBACK"
        },
        [pscustomobject]@{
            priority = 30
            name = "Start-VRN-Lane3-EngineCapability.ps1"
            role = "ENGINE_CAPABILITY_START"
        },
        [pscustomobject]@{
            priority = 40
            name = "Start-VRN-Lane2-IOInventory.ps1"
            role = "IO_INVENTORY_START"
        },
        [pscustomobject]@{
            priority = 50
            name = "Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
            role = "NO_OCR_STAGING"
        },
        [pscustomobject]@{
            priority = 999
            name = "Invoke-VRN.ps1"
            role = "CANONICAL_RUNTIME_FAILED_DO_NOT_RETRY"
        }
    )

    $rows = @()

    foreach ($definition in $candidateDefinitions) {
        $path = Join-Path $vrnRoot $definition.name
        $exists = Test-Path -LiteralPath $path
        $parseOk = $false
        $errorCount = 0
        $firstError = ""
        $metadata = [pscustomobject]@{
            parameters = ""
            mandatory_without_default = ""
            mandatory_count = 0
            defaulted_parameters = ""
        }

        if ($exists) {
            $check = Test-PowerShellAst -Path $path
            $parseOk = $check.parse_ok
            $errorCount = $check.error_count
            $firstError = $check.first_error
            $metadata = Get-ParameterMetadata -Ast $check.ast
        }

        $eligible = (
            $exists -and
            $parseOk -and
            $metadata.mandatory_count -eq 0 -and
            $definition.name -ne "Invoke-VRN.ps1"
        )

        $decision = if ($definition.name -eq "Invoke-VRN.ps1") {
            "EXCLUDE_RUNTIME_FAILED_CANONICAL"
        }
        elseif (-not $exists) {
            "EXCLUDE_MISSING"
        }
        elseif (-not $parseOk) {
            "EXCLUDE_AST_ERROR"
        }
        elseif ($metadata.mandatory_count -gt 0) {
            "EXCLUDE_MANDATORY_PARAMETERS"
        }
        else {
            "ELIGIBLE_SEQUENTIAL_ATTEMPT"
        }

        $rows += [pscustomobject]@{
            priority = $definition.priority
            name = $definition.name
            role = $definition.role
            path = $path
            exists = $exists
            parse_ok = $parseOk
            error_count = $errorCount
            first_error = $firstError
            parameters = $metadata.parameters
            mandatory_without_default = $metadata.mandatory_without_default
            mandatory_count = $metadata.mandatory_count
            defaulted_parameters = $metadata.defaulted_parameters
            eligible = $eligible
            decision = $decision
        }
    }

    return @($rows | Sort-Object priority)
}

function Write-VrnChildLauncher {
    param(
        [Parameter(Mandatory)]
        [string]$Destination,

        [Parameter(Mandatory)]
        [string]$CandidatePath,

        [Parameter(Mandatory)]
        [string]$CandidateName,

        [Parameter(Mandatory)]
        [string]$StatusPath,

        [Parameter(Mandatory)]
        [string]$TranscriptPath
    )

    $template = @'
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CandidatePath = "__CANDIDATE_PATH__"
$CandidateName = "__CANDIDATE_NAME__"
$SupportiveManifestPath = "__SUPPORTIVE_MANIFEST__"
$StatusPath = "__STATUS_PATH__"
$TranscriptPath = "__TRANSCRIPT_PATH__"

function Ensure-ChildDirectory {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-ChildStatus {
    param(
        [Parameter(Mandatory)]
        [string]$State,

        [Parameter(Mandatory)]
        [bool]$Success,

        [string]$ErrorText = "",

        [int]$Loaded = 0,

        [int]$EmptySkipped = 0
    )

    $payload = [ordered]@{
        subsystem = "VRN"
        candidate = $CandidateName
        candidate_path = $CandidatePath
        state = $State
        success = $Success
        error = $ErrorText
        loaded = $Loaded
        empty_skipped = $EmptySkipped
        pid = $PID
        timestamp = (Get-Date).ToString("o")
    }

    $temporaryPath = "$StatusPath.tmp.$PID"

    $payload |
        ConvertTo-Json -Depth 30 |
        Set-Content -LiteralPath $temporaryPath -Encoding UTF8

    Move-Item -LiteralPath $temporaryPath -Destination $StatusPath -Force
}

Ensure-ChildDirectory -Path (Split-Path -Parent $StatusPath)
Ensure-ChildDirectory -Path (Split-Path -Parent $TranscriptPath)

$loadedCount = 0
$emptySkippedCount = 0

try {
    try {
        Start-Transcript -LiteralPath $TranscriptPath -Append | Out-Null
    }
    catch {}

    Write-ChildStatus `
        -State "BOOTSTRAP_STARTED" `
        -Success $true

    if (-not (Test-Path -LiteralPath $SupportiveManifestPath)) {
        throw "Supportive manifest missing: $SupportiveManifestPath"
    }

    $modules = @(
        Get-Content -LiteralPath $SupportiveManifestPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    )

    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()

        if (-not (Test-Path -LiteralPath $modulePath)) {
            throw "Supportive module missing: $modulePath"
        }

        $item = Get-Item -LiteralPath $modulePath -ErrorAction Stop

        if ($extension -in @(".psm1", ".psd1")) {
            Import-Module -Name $modulePath -Force -ErrorAction Stop
            $loadedCount++
            continue
        }

        if ($extension -eq ".ps1") {
            if ($item.Length -eq 0) {
                $emptySkippedCount++
                continue
            }

            $text = [string](
                Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8
            )

            if ([string]::IsNullOrWhiteSpace($text)) {
                $emptySkippedCount++
                continue
            }

            $tokens = $null
            $errors = $null

            [System.Management.Automation.Language.Parser]::ParseInput(
                $text,
                [ref]$tokens,
                [ref]$errors
            ) | Out-Null

            if (@($errors).Count -gt 0) {
                throw "Supportive AST error: $([string]$errors[0].Message)"
            }

            $scriptBlock = [scriptblock]::Create($text)

            if ($null -eq $scriptBlock) {
                throw "ScriptBlock.Create returned null."
            }

            $dynamicModule = New-Module `
                -Name ("VIA_SAFE_" + [guid]::NewGuid().ToString("N")) `
                -ScriptBlock $scriptBlock

            if ($null -eq $dynamicModule) {
                throw "New-Module returned null."
            }

            Import-Module `
                -ModuleInfo $dynamicModule `
                -Force `
                -ErrorAction Stop

            $loadedCount++
        }
    }

    Write-ChildStatus `
        -State "SUPPORTIVE_IMPORTED" `
        -Success $true `
        -Loaded $loadedCount `
        -EmptySkipped $emptySkippedCount

    if (-not (Test-Path -LiteralPath $CandidatePath)) {
        throw "VRN candidate missing: $CandidatePath"
    }

    $candidateTokens = $null
    $candidateErrors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $CandidatePath,
        [ref]$candidateTokens,
        [ref]$candidateErrors
    ) | Out-Null

    if (@($candidateErrors).Count -gt 0) {
        throw "Candidate AST error: $([string]$candidateErrors[0].Message)"
    }

    Write-ChildStatus `
        -State "ENTRYPOINT_STARTED" `
        -Success $true `
        -Loaded $loadedCount `
        -EmptySkipped $emptySkippedCount

    Write-Host "def VRN Candidate           : $CandidateName" -ForegroundColor Cyan
    Write-Host "def VRN Supportive Modules : Loaded=$loadedCount / EmptySkipped=$emptySkippedCount" -ForegroundColor Green

    & $CandidatePath

    Write-ChildStatus `
        -State "COMPLETED" `
        -Success $true `
        -Loaded $loadedCount `
        -EmptySkipped $emptySkippedCount
}
catch {
    Write-ChildStatus `
        -State "FAILED" `
        -Success $false `
        -ErrorText $_.Exception.Message `
        -Loaded $loadedCount `
        -EmptySkipped $emptySkippedCount

    Write-Host "def VRN Candidate ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {}
}
'@

    $content = $template.
        Replace("__CANDIDATE_PATH__", $CandidatePath).
        Replace("__CANDIDATE_NAME__", $CandidateName).
        Replace("__SUPPORTIVE_MANIFEST__", $SupportiveDeployed).
        Replace("__STATUS_PATH__", $StatusPath).
        Replace("__TRANSCRIPT_PATH__", $TranscriptPath)

    Set-Content -LiteralPath $Destination -Value $content -Encoding UTF8
}

function Invoke-VrnCandidateAttempt {
    param(
        [Parameter(Mandatory)]
        $Candidate
    )

    $safeName = (
        [System.IO.Path]::GetFileNameWithoutExtension([string]$Candidate.name) `
            -replace "[^A-Za-z0-9_]", "_"
    )

    $candidateLauncher = Join-Path $CandidateDir "Start-${safeName}-v0136A.ps1"
    $deployedLauncher = Join-Path $PersistentLauncherDir "Start-${safeName}-v0136A.ps1"
    $statusPath = Join-Path $PersistentLogDir "${safeName}_status.v0136A.json"
    $transcriptPath = Join-Path $PersistentLogDir "${safeName}_transcript.v0136A.txt"

    Write-VrnChildLauncher `
        -Destination $candidateLauncher `
        -CandidatePath ([string]$Candidate.path) `
        -CandidateName ([string]$Candidate.name) `
        -StatusPath $statusPath `
        -TranscriptPath $transcriptPath

    $launcherCheck = Test-PowerShellAst -Path $candidateLauncher

    if (-not $launcherCheck.parse_ok) {
        return [pscustomobject]@{
            candidate = $Candidate.name
            candidate_path = $Candidate.path
            process_state = "NOT_STARTED"
            child_state = "LAUNCHER_AST_FAILED"
            loaded = 0
            empty_skipped = 0
            success = $false
            error = $launcherCheck.first_error
            launcher = $candidateLauncher
            status = $statusPath
            transcript = $transcriptPath
        }
    }

    Copy-Item `
        -LiteralPath $candidateLauncher `
        -Destination $deployedLauncher `
        -Force

    if (Test-Path -LiteralPath $statusPath) {
        Remove-Item -LiteralPath $statusPath -Force -ErrorAction SilentlyContinue
    }

    $pwsh = (Get-Command pwsh -ErrorAction Stop).Source
    $encodedCommand = ConvertTo-EncodedCommand -ScriptPath $deployedLauncher

    $process = Start-Process `
        -FilePath $pwsh `
        -ArgumentList @(
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            $encodedCommand
        ) `
        -PassThru

    Start-Sleep -Seconds $ProbeSeconds
    $process.Refresh()

    $processState = if ($process.HasExited) {
        "EXITED_$($process.ExitCode)"
    }
    else {
        "RUNNING"
    }

    $childState = "STATUS_NOT_WRITTEN"
    $loaded = 0
    $emptySkipped = 0
    $errorText = ""
    $success = $false

    if (Test-Path -LiteralPath $statusPath) {
        try {
            $status = (
                Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 |
                ConvertFrom-Json
            )

            $childState = [string]$status.state
            $loaded = [int]$status.loaded
            $emptySkipped = [int]$status.empty_skipped
            $errorText = [string]$status.error
            $success = $childState -in @("ENTRYPOINT_STARTED", "COMPLETED")
        }
        catch {
            $childState = "STATUS_PARSE_ERROR"
            $errorText = $_.Exception.Message
        }
    }

    return [pscustomobject]@{
        candidate = $Candidate.name
        candidate_path = $Candidate.path
        process_state = $processState
        child_state = $childState
        loaded = $loaded
        empty_skipped = $emptySkipped
        success = $success
        error = $errorText
        launcher = $deployedLauncher
        status = $statusPath
        transcript = $transcriptPath
    }
}

function Write-HtmlReport {
    param(
        [Parameter(Mandatory)]
        $Summary,

        [Parameter(Mandatory)]
        $CandidateRows,

        [Parameter(Mandatory)]
        $AttemptRows
    )

    $gateClass = if ($Summary.gate -eq "FULL_VRN_VDF_ACTIVATION_SUCCESS") {
        "ok"
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
.ok{color:#18794e}.bad{color:#b42318}
.table-wrap{width:100%;overflow:auto;max-height:620px;border:1px solid #d8e2df;border-radius:9px}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th{position:sticky;top:0;background:#e7efed;padding:6px;border:1px solid #d2dfdc;text-align:left}
td{padding:5px 6px;border:1px solid #e2eae8;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:450px}
tr:nth-child(even){background:#fbfcfb}
.empty{padding:14px;color:#63706d}
</style>
'@

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA VRN Fallback v0136A</title>
$css
</head>
<body>
<h1>VIA · VRN Fallback Entrypoint Resolver / Activation · v0136A</h1>

<div class="card">
<div class="grid">
<div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(ConvertTo-HtmlEncoded -Value $Summary.gate)</div></div>
<div class="metric"><div class="k">VDF</div><div class="v">COMPLETED_FROM_v0135</div></div>
<div class="metric"><div class="k">VRN Selected</div><div class="v">$(ConvertTo-HtmlEncoded -Value $Summary.vrn_selected)</div></div>
<div class="metric"><div class="k">VRN State</div><div class="v">$(ConvertTo-HtmlEncoded -Value $Summary.vrn_state)</div></div>
<div class="metric"><div class="k">Attempts</div><div class="v">$($Summary.attempts)</div></div>
<div class="metric"><div class="k">Organization Repeated</div><div class="v">NO</div></div>
</div>
</div>

<h2>Decision</h2>
<div class="card">
$(ConvertTo-HtmlEncoded -Value $Summary.decision)
<br/><br/>
Next: $(ConvertTo-HtmlEncoded -Value $Summary.next_step)
</div>

<h2>VRN Candidate Matrix</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows $CandidateRows)</div>

<h2>Sequential Activation Attempts</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows $AttemptRows)</div>

<h2>Output</h2>
<div class="card">
RunDir: $(ConvertTo-HtmlEncoded -Value $RunDir)<br/>
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
        $CandidateDir,
        $PersistentRoot,
        $PersistentLauncherDir,
        $PersistentLogDir,
        $PersistentManifestDir,
        $PersistentHtmlDir
    )) {
        Ensure-Directory -Path $directory
    }

    Write-Host "def [BOOT] v0136A started. v0134 organization will NOT repeat." -ForegroundColor Cyan

    $vdfStatusPath = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\logs\VDF_activation_status.v0135.json"
    $vrnStatusPath = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\logs\VRN_activation_status.v0135.json"

    if (-not (Test-Path -LiteralPath $vdfStatusPath)) {
        throw "v0135 VDF status missing."
    }

    if (-not (Test-Path -LiteralPath $vrnStatusPath)) {
        throw "v0135 VRN status missing."
    }

    $vdfStatus = (
        Get-Content -LiteralPath $vdfStatusPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    )

    $vrnStatus = (
        Get-Content -LiteralPath $vrnStatusPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    )

    if ([string]$vdfStatus.state -ne "COMPLETED") {
        throw "VDF is not COMPLETED in v0135."
    }

    if ([string]$vrnStatus.state -ne "FAILED") {
        throw "VRN is not FAILED in v0135; fallback is unnecessary."
    }

    Write-Host "def [V0135] VDF COMPLETED; canonical VRN runtime failure confirmed." -ForegroundColor Yellow

    if (-not (Test-Path -LiteralPath $SupportiveSource)) {
        throw "Approved supportive manifest missing."
    }

    Copy-Item `
        -LiteralPath $SupportiveSource `
        -Destination $SupportiveDeployed `
        -Force

    $supportiveRows = @(
        Get-Content -LiteralPath $SupportiveDeployed -Raw -Encoding UTF8 |
        ConvertFrom-Json
    )

    $candidateRows = @(Get-VrnCandidateMatrix)
    Write-CsvFile -Data $candidateRows -Path $CandidateCsv
    Write-JsonFile -Data $candidateRows -Path $CandidateJson

    $eligibleRows = @(
        $candidateRows |
        Where-Object { $_.eligible -eq $true } |
        Sort-Object priority
    )

    Write-Host ("def [CANDIDATES] Eligible fallback candidates: {0}" -f $eligibleRows.Count) -ForegroundColor Green

    $attemptRows = @()
    $selectedAttempt = $null

    if ($ActivateVrn) {
        foreach ($candidate in $eligibleRows) {
            Write-Host ("def [ATTEMPT] {0}" -f $candidate.name) -ForegroundColor Cyan

            $attempt = Invoke-VrnCandidateAttempt -Candidate $candidate
            $attemptRows += $attempt

            if ($attempt.success) {
                $selectedAttempt = $attempt
                break
            }

            Write-Host ("def [ATTEMPT FAILED] {0}: {1}" -f $attempt.candidate, $attempt.error) -ForegroundColor Yellow
        }
    }

    Write-CsvFile -Data $attemptRows -Path $AttemptCsv
    Write-JsonFile -Data $attemptRows -Path $AttemptJson

    $gate = "VRN_FALLBACK_REVIEW_REQUIRED"
    $risk = "MEDIUM_REVIEW"
    $decision = "No VRN fallback candidate reached ENTRYPOINT_STARTED or COMPLETED."
    $nextStep = "Review the final candidate transcript."
    $selectedName = ""
    $vrnState = "NOT_ACTIVATED"

    if ($null -ne $selectedAttempt) {
        $gate = "FULL_VRN_VDF_ACTIVATION_SUCCESS"
        $risk = "LOW_CONTROLLED_WITH_HYDRA_MONITORING"
        $decision = "VDF remained completed; VRN activated through a parse-clean fallback without changing canonical Invoke-VRN.ps1."
        $nextStep = "Repair canonical Invoke-VRN.ps1 separately in draft-only mode."
        $selectedName = [string]$selectedAttempt.candidate
        $vrnState = "{0}/{1}/Loaded={2}/EmptySkipped={3}" -f `
            $selectedAttempt.process_state,
            $selectedAttempt.child_state,
            $selectedAttempt.loaded,
            $selectedAttempt.empty_skipped
    }
    elseif (-not $ActivateVrn) {
        $gate = "VRN_FALLBACK_ELIGIBLE_NOT_REQUESTED"
        $risk = "LOW_REVIEW"
        $decision = "Fallback candidates were evaluated, but activation was disabled."
        $nextStep = "Run v0136A with ActivateVrn=true."
    }

    $summary = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        gate = $gate
        risk = $risk
        decision = $decision
        next_step = $nextStep
        organization_repeated = $false
        vdf_state = "COMPLETED_FROM_v0135"
        vrn_canonical_state = "FAILED_RUNTIME_FROM_v0135"
        vrn_selected = $selectedName
        vrn_state = $vrnState
        attempts = @($attemptRows).Count
        eligible_candidates = @($eligibleRows).Count
        supportive_approved = @($supportiveRows).Count
        run_dir = $RunDir
        html = $ReportHtml
    }

    Write-JsonFile -Data $summary -Path $SummaryJson

    Write-HtmlReport `
        -Summary ([pscustomobject]$summary) `
        -CandidateRows $candidateRows `
        -AttemptRows $attemptRows

    Copy-Item `
        -LiteralPath $ReportHtml `
        -Destination (Join-Path $PersistentHtmlDir (Split-Path -Leaf $ReportHtml)) `
        -Force

    if ($OpenHtmlReport) {
        Start-Process -FilePath $ReportHtml
    }

    Write-Host ""
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
    Write-Host "def VIA · v0136A FINAL RESULT" -ForegroundColor Cyan
    Write-Host ("def Gate                 : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host "def OrganizationRepeated : False" -ForegroundColor Green
    Write-Host "def VDFState             : COMPLETED_FROM_v0135" -ForegroundColor Green
    Write-Host ("def VRNSelected          : {0}" -f $summary.vrn_selected) -ForegroundColor Green
    Write-Host ("def VRNState             : {0}" -f $summary.vrn_state) -ForegroundColor Green
    Write-Host ("def Attempts             : {0}" -f $summary.attempts) -ForegroundColor White
    Write-Host ("def EligibleCandidates   : {0}" -f $summary.eligible_candidates) -ForegroundColor White
    Write-Host ("def RunDir               : {0}" -f $summary.run_dir) -ForegroundColor Cyan
    Write-Host ("def HTML                 : {0}" -f $summary.html) -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "def VIA · v0136A OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def No organization, delete, canonical mutation or Stop-Process was executed." -ForegroundColor Yellow
}
finally {
    if ($KeepParentPowerShellOpen) {
        Write-Host ""
        Write-Host "def Parent PowerShell remains open. v0134 organization was not repeated." -ForegroundColor Cyan
    }
}
