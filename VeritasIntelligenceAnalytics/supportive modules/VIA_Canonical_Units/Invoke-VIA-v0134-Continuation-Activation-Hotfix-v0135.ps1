#requires -Version 7.0
<#
====================================================================================================
def VIA · v0134 CONTINUATION / ACTIVATION HOTFIX · v0135
====================================================================================================
Purpose
-------
- Continue from the latest completed v0134 organization run.
- Do NOT repeat inventory or the 12,157 organization actions.
- Fix empty .ps1 supportive placeholders that caused ScriptBlock.Create($null).
- Generate fresh v0135 VRN/VDF bootstrap launchers.
- Use PowerShell EncodedCommand for paths containing spaces.
- Write child status JSON, module-import evidence, transcript logs and HTML.
- Fix mixed-object HTML rendering by using a union of all property names.

Safety
------
- No broad rescan.
- No organization move.
- No delete.
- No Stop-Process.
- No canonical mutation.
- No forced bypass.
- v0133 FULL_ACTIVATION_ELIGIBLE remains the activation authority.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [bool]$ActivateVrnVdf = $true,
    [bool]$OpenHtmlReport = $true,
    [bool]$KeepParentPowerShellOpen = $true,
    [int]$ActivationProbeSeconds = 10,
    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0135_CONTINUE_WITHOUT_REORGANIZATION"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0135_CONTINUE_WITHOUT_REORGANIZATION"
$Version = "v0135"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunName = "RUN_${RunStamp}_VIA_v0134_CONTINUATION_ACTIVATION_HOTFIX_v0135"

$RunRoot = Join-Path $BaseDir "_via_governance_activation_hotfix_runs"
$RunDir = Join-Path $RunRoot $RunName
$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$RuntimeCandidateDir = Join-Path $RunDir "runtime_candidate"

$PersistentRoot = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135"
$PersistentLauncherDir = Join-Path $PersistentRoot "launcher"
$PersistentLogDir = Join-Path $PersistentRoot "logs"
$PersistentManifestDir = Join-Path $PersistentRoot "manifests"
$PersistentHtmlDir = Join-Path $PersistentRoot "html"

$SupportiveListCandidate = Join-Path $RuntimeCandidateDir "supportive_loaded_modules.v0135.json"
$VrnLauncherCandidate = Join-Path $RuntimeCandidateDir "Start-VIA-VRN-With-Supportive-v0135.ps1"
$VdfLauncherCandidate = Join-Path $RuntimeCandidateDir "Start-VIA-VDF-With-Supportive-v0135.ps1"
$ManifestCandidate = Join-Path $RuntimeCandidateDir "VIA_v0135_ContinuationManifest.json"

$SupportiveListDeployed = Join-Path $PersistentManifestDir "supportive_loaded_modules.v0135.json"
$VrnLauncherDeployed = Join-Path $PersistentLauncherDir "Start-VIA-VRN-With-Supportive-v0135.ps1"
$VdfLauncherDeployed = Join-Path $PersistentLauncherDir "Start-VIA-VDF-With-Supportive-v0135.ps1"
$ManifestDeployed = Join-Path $PersistentManifestDir "VIA_v0135_ContinuationManifest.json"

$VrnStatusPath = Join-Path $PersistentLogDir "VRN_activation_status.v0135.json"
$VdfStatusPath = Join-Path $PersistentLogDir "VDF_activation_status.v0135.json"
$VrnTranscriptPath = Join-Path $PersistentLogDir "VRN_transcript.v0135.txt"
$VdfTranscriptPath = Join-Path $PersistentLogDir "VDF_transcript.v0135.txt"

$ActivationEvidenceCsv = Join-Path $CsvDir "activation_evidence.v0135.csv"
$SupportiveEvidenceCsv = Join-Path $CsvDir "supportive_precheck.v0135.csv"
$SummaryJson = Join-Path $JsonDir "summary.v0135.json"
$ActivationEvidenceJson = Join-Path $JsonDir "activation_evidence.v0135.json"
$SupportiveEvidenceJson = Join-Path $JsonDir "supportive_precheck.v0135.json"
$ReportHtml = Join-Path $HtmlDir "VIA_v0134_Continuation_Activation_Hotfix_v0135.html"

$script:ActivationEvidence = New-Object System.Collections.Generic.List[object]
$script:Narration = New-Object System.Collections.Generic.List[object]

function def_EnsureDir {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_Banner {
    param([Parameter(Mandatory)][string]$Title)

    Write-Host ""
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
    Write-Host ("def {0}" -f $Title) -ForegroundColor Cyan
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
}

function def_Narrate {
    param(
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet("INFO","OK","WARN","ERROR")][string]$Level = "INFO"
    )

    $row = [pscustomobject]@{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
        stage = $Stage
        level = $Level
        message = $Message
    }

    $script:Narration.Add($row)

    $color = switch ($Level) {
        "OK"    { "Green" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        default { "Cyan" }
    }

    Write-Host ("def [{0}] {1}" -f $Stage,$Message) -ForegroundColor $color
}

function def_WriteJson {
    param(
        $Data,
        [Parameter(Mandatory)][string]$Path
    )

    def_EnsureDir -Path (Split-Path -Parent $Path)
    $Data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_WriteCsv {
    param(
        $Data,
        [Parameter(Mandatory)][string]$Path
    )

    def_EnsureDir -Path (Split-Path -Parent $Path)
    @($Data) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function def_HtmlEncode {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_GetPropertyValueSafe {
    param(
        $Object,
        [Parameter(Mandatory)][string]$PropertyName
    )

    if ($null -eq $Object) {
        return $null
    }

    $property = $Object.PSObject.Properties[$PropertyName]

    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function def_ToHtmlTableSafe {
    param(
        $Rows,
        [int]$MaxRows = 1000
    )

    $array = @($Rows)

    if ($array.Count -eq 0) {
        return "<div class='empty'>No rows.</div>"
    }

    $propertySet = [ordered]@{}

    foreach ($row in $array) {
        if ($null -eq $row) {
            continue
        }

        foreach ($property in $row.PSObject.Properties.Name) {
            if (-not $propertySet.Contains($property)) {
                $propertySet[$property] = $true
            }
        }
    }

    $properties = @($propertySet.Keys)

    if ($properties.Count -eq 0) {
        return "<div class='empty'>Rows contain no readable properties.</div>"
    }

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("<div class='table-wrap'><table><thead><tr>")

    foreach ($property in $properties) {
        [void]$sb.AppendLine("<th>$(def_HtmlEncode $property)</th>")
    }

    [void]$sb.AppendLine("</tr></thead><tbody>")

    foreach ($row in @($array | Select-Object -First $MaxRows)) {
        [void]$sb.AppendLine("<tr>")

        foreach ($property in $properties) {
            $value = def_GetPropertyValueSafe -Object $row -PropertyName $property
            [void]$sb.AppendLine("<td>$(def_HtmlEncode $value)</td>")
        }

        [void]$sb.AppendLine("</tr>")
    }

    [void]$sb.AppendLine("</tbody></table></div>")
    return $sb.ToString()
}

function def_TestPowerShellFile {
    param([Parameter(Mandatory)][string]$Path)

    $tokens = $null
    $errors = $null

    try {
        [System.Management.Automation.Language.Parser]::ParseFile(
            $Path,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        return [pscustomobject]@{
            exists = $true
            parse_ok = (@($errors).Count -eq 0)
            error_count = @($errors).Count
            first_error = if (@($errors).Count -gt 0) { [string]$errors[0].Message } else { "" }
        }
    }
    catch {
        return [pscustomobject]@{
            exists = (Test-Path -LiteralPath $Path)
            parse_ok = $false
            error_count = 1
            first_error = $_.Exception.Message
        }
    }
}

function def_FindLatestV0134Run {
    $root = Join-Path $BaseDir "_via_governance_organization_runs"

    if (-not (Test-Path -LiteralPath $root)) {
        return $null
    }

    $run = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*v0134*" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -eq $run) {
        return $null
    }

    $moveEvidence = Join-Path $run.FullName "csv\VIA_OrganizationMoveEvidence.v0134.csv"
    $inventory = Join-Path $run.FullName "csv\VIA_FileRegistry.v0134.csv"
    $actions = Join-Path $run.FullName "csv\VIA_OrganizationActions.v0134.csv"

    return [pscustomobject]@{
        run_dir = $run.FullName
        move_evidence_csv = $moveEvidence
        inventory_csv = $inventory
        actions_csv = $actions
    }
}

function def_FindV0133Gate {
    $preferred = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime\v0133\activation_gate.v0133.json"

    if (Test-Path -LiteralPath $preferred) {
        try {
            $data = Get-Content -LiteralPath $preferred -Raw -Encoding UTF8 | ConvertFrom-Json

            if ([string]$data.gate -eq "FULL_ACTIVATION_ELIGIBLE") {
                return [pscustomobject]@{
                    path = $preferred
                    data = $data
                }
            }
        }
        catch {}
    }

    $root = Join-Path $BaseDir "_via_live_blocker_adjudication_runs"

    if (Test-Path -LiteralPath $root) {
        $files = Get-ChildItem -LiteralPath $root -Recurse -File -Filter "activation_gate.v0133.json" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending

        foreach ($file in $files) {
            try {
                $data = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json

                if ([string]$data.gate -eq "FULL_ACTIVATION_ELIGIBLE") {
                    return [pscustomobject]@{
                        path = $file.FullName
                        data = $data
                    }
                }
            }
            catch {}
        }
    }

    return $null
}

function def_FindSupportiveList {
    $preferred = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime\v0133\supportive_loaded_modules.v0133.json"

    if (Test-Path -LiteralPath $preferred) {
        return $preferred
    }

    $root = Join-Path $BaseDir "_via_live_blocker_adjudication_runs"

    if (Test-Path -LiteralPath $root) {
        $file = Get-ChildItem -LiteralPath $root -Recurse -File -Filter "supportive_loaded_modules.v0133.json" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($null -ne $file) {
            return $file.FullName
        }
    }

    return ""
}

function def_GetMoveSummary {
    param([Parameter(Mandatory)]$V0134Run)

    if (-not (Test-Path -LiteralPath $V0134Run.move_evidence_csv)) {
        return [pscustomobject]@{
            evidence_exists = $false
            rows = 0
            success = 0
            fail = 0
            note = "Move evidence missing; activation may proceed only from v0133 authority."
        }
    }

    try {
        $rows = @(Import-Csv -LiteralPath $V0134Run.move_evidence_csv -Encoding UTF8)
        $success = @(
            $rows |
            Where-Object { [string]$_.success -eq "True" }
        ).Count
        $fail = @(
            $rows |
            Where-Object { [string]$_.success -ne "True" }
        ).Count

        return [pscustomobject]@{
            evidence_exists = $true
            rows = @($rows).Count
            success = $success
            fail = $fail
            note = "v0134 organization evidence reused; no organization action repeated."
        }
    }
    catch {
        return [pscustomobject]@{
            evidence_exists = $true
            rows = 0
            success = 0
            fail = 1
            note = $_.Exception.Message
        }
    }
}

function def_PrecheckSupportiveList {
    param([Parameter(Mandatory)][string]$Path)

    $rows = @()

    try {
        $modules = @(Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
    catch {
        throw "Unable to parse supportive list: $($_.Exception.Message)"
    }

    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()
        $exists = Test-Path -LiteralPath $modulePath
        $size = 0
        $parseOk = $false
        $mode = ""
        $firstError = ""

        if ($exists) {
            try {
                $item = Get-Item -LiteralPath $modulePath -ErrorAction Stop
                $size = [int64]$item.Length

                if ($extension -in @(".ps1",".psm1",".psd1")) {
                    $check = def_TestPowerShellFile -Path $modulePath
                    $parseOk = $check.parse_ok
                    $firstError = $check.first_error
                }
                else {
                    $parseOk = $true
                }

                if ($extension -in @(".psm1",".psd1")) {
                    $mode = "IMPORT_MODULE"
                }
                elseif ($extension -eq ".ps1" -and $size -eq 0) {
                    $mode = "EMPTY_SAFE_PLACEHOLDER_SKIP"
                }
                elseif ($extension -eq ".ps1") {
                    $text = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8 -ErrorAction Stop

                    if ([string]::IsNullOrWhiteSpace([string]$text)) {
                        $mode = "WHITESPACE_SAFE_PLACEHOLDER_SKIP"
                    }
                    else {
                        $mode = "IMPORT_SAFE_PS1_DYNAMIC_MODULE"
                    }
                }
                else {
                    $mode = "REGISTER_ONLY"
                }
            }
            catch {
                $firstError = $_.Exception.Message
            }
        }
        else {
            $firstError = "File missing."
        }

        $rows += [pscustomobject]@{
            path = $modulePath
            extension = $extension
            exists = $exists
            size_bytes = $size
            parse_ok = $parseOk
            planned_mode = $mode
            first_error = $firstError
        }
    }

    return @($rows)
}

function def_WriteChildLauncher {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Subsystem,
        [Parameter(Mandatory)][string]$EntrypointPath,
        [Parameter(Mandatory)][string]$SupportiveListPath,
        [Parameter(Mandatory)][string]$StatusPath,
        [Parameter(Mandatory)][string]$TranscriptPath
    )

    $template = @'
#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EntrypointPath = "__ENTRYPOINT__",
    [string]$SupportiveListPath = "__SUPPORTIVE_LIST__",
    [string]$StatusPath = "__STATUS__",
    [string]$TranscriptPath = "__TRANSCRIPT__"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function EnsureDir([string]$PathValue) {
    if (-not (Test-Path -LiteralPath $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function WriteStatus(
    [string]$State,
    [bool]$Success,
    [string]$Message,
    [string]$ErrorText,
    [int]$Loaded,
    [int]$SkippedEmpty,
    [int]$Failed
) {
    $payload = [ordered]@{
        subsystem = "__SUBSYSTEM__"
        state = $State
        success = $Success
        message = $Message
        error = $ErrorText
        loaded = $Loaded
        skipped_empty = $SkippedEmpty
        failed = $Failed
        pid = $PID
        timestamp = (Get-Date).ToString("o")
        entrypoint = $EntrypointPath
        supportive_list = $SupportiveListPath
    }

    $temp = "$StatusPath.tmp.$PID"
    $payload | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $StatusPath -Force
}

EnsureDir (Split-Path -Parent $StatusPath)
EnsureDir (Split-Path -Parent $TranscriptPath)

$loadedCount = 0
$skippedEmptyCount = 0
$failedCount = 0
$events = @()

try {
    try {
        Start-Transcript -LiteralPath $TranscriptPath -Append | Out-Null
    }
    catch {}

    WriteStatus -State "BOOTSTRAP_STARTED" -Success $true -Message "Child bootstrap started." -ErrorText "" -Loaded 0 -SkippedEmpty 0 -Failed 0

    if (-not (Test-Path -LiteralPath $SupportiveListPath)) {
        throw "Approved supportive list missing: $SupportiveListPath"
    }

    $modules = @(Get-Content -LiteralPath $SupportiveListPath -Raw -Encoding UTF8 | ConvertFrom-Json)

    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()

        try {
            if (-not (Test-Path -LiteralPath $modulePath)) {
                throw "Supportive module missing: $modulePath"
            }

            $item = Get-Item -LiteralPath $modulePath -ErrorAction Stop

            if ($extension -in @(".psm1",".psd1")) {
                Import-Module -Name $modulePath -Force -ErrorAction Stop
                $loadedCount++

                $events += [pscustomobject]@{
                    path = $modulePath
                    state = "IMPORTED_MODULE"
                    success = $true
                    error = ""
                }

                continue
            }

            if ($extension -eq ".ps1") {
                if ($item.Length -eq 0) {
                    $skippedEmptyCount++

                    $events += [pscustomobject]@{
                        path = $modulePath
                        state = "EMPTY_SAFE_PLACEHOLDER_SKIPPED"
                        success = $true
                        error = ""
                    }

                    continue
                }

                $text = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8 -ErrorAction Stop
                $safeText = [string]$text

                if ([string]::IsNullOrWhiteSpace($safeText)) {
                    $skippedEmptyCount++

                    $events += [pscustomobject]@{
                        path = $modulePath
                        state = "WHITESPACE_SAFE_PLACEHOLDER_SKIPPED"
                        success = $true
                        error = ""
                    }

                    continue
                }

                $tokens = $null
                $errors = $null

                [System.Management.Automation.Language.Parser]::ParseInput(
                    $safeText,
                    [ref]$tokens,
                    [ref]$errors
                ) | Out-Null

                if (@($errors).Count -gt 0) {
                    throw "Supportive .ps1 AST failed: $([string]$errors[0].Message)"
                }

                $scriptBlock = [scriptblock]::Create($safeText)

                if ($null -eq $scriptBlock) {
                    throw "ScriptBlock.Create returned null."
                }

                $dynamicName = "VIA_SAFE_" +
                    ([System.IO.Path]::GetFileNameWithoutExtension($modulePath) -replace '[^A-Za-z0-9_]','_') +
                    "_" +
                    ([guid]::NewGuid().ToString("N").Substring(0,8))

                $dynamicModule = New-Module -Name $dynamicName -ScriptBlock $scriptBlock

                if ($null -eq $dynamicModule) {
                    throw "New-Module returned null."
                }

                Import-Module -ModuleInfo $dynamicModule -Force -ErrorAction Stop
                $loadedCount++

                $events += [pscustomobject]@{
                    path = $modulePath
                    state = "IMPORTED_SAFE_DYNAMIC_MODULE"
                    success = $true
                    error = ""
                }

                continue
            }

            $events += [pscustomobject]@{
                path = $modulePath
                state = "REGISTERED_ONLY_NOT_IMPORTABLE"
                success = $true
                error = ""
            }
        }
        catch {
            $failedCount++

            $events += [pscustomobject]@{
                path = $modulePath
                state = "SUPPORTIVE_IMPORT_FAILED"
                success = $false
                error = $_.Exception.Message
            }
        }
    }

    $eventPath = Join-Path (Split-Path -Parent $StatusPath) "__SUBSYSTEM___supportive_imports.v0135.json"
    $events | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $eventPath -Encoding UTF8

    if ($failedCount -gt 0) {
        throw "One or more approved supportive modules failed to import. Failed=$failedCount"
    }

    WriteStatus `
        -State "SUPPORTIVE_IMPORTED" `
        -Success $true `
        -Message ("Loaded={0}; EmptyPlaceholderSkipped={1}; Failed={2}" -f $loadedCount,$skippedEmptyCount,$failedCount) `
        -ErrorText "" `
        -Loaded $loadedCount `
        -SkippedEmpty $skippedEmptyCount `
        -Failed $failedCount

    if (-not (Test-Path -LiteralPath $EntrypointPath)) {
        throw "Entrypoint missing: $EntrypointPath"
    }

    $entryTokens = $null
    $entryErrors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $EntrypointPath,
        [ref]$entryTokens,
        [ref]$entryErrors
    ) | Out-Null

    if (@($entryErrors).Count -gt 0) {
        throw "Entrypoint AST failed: $([string]$entryErrors[0].Message)"
    }

    WriteStatus `
        -State "ENTRYPOINT_STARTED" `
        -Success $true `
        -Message "Canonical entrypoint invoked." `
        -ErrorText "" `
        -Loaded $loadedCount `
        -SkippedEmpty $skippedEmptyCount `
        -Failed $failedCount

    Write-Host "def __SUBSYSTEM__ Supportive Modules : Loaded=$loadedCount / EmptySkipped=$skippedEmptyCount" -ForegroundColor Green
    Write-Host "def __SUBSYSTEM__ Entrypoint          : $EntrypointPath" -ForegroundColor Cyan

    & $EntrypointPath

    WriteStatus `
        -State "COMPLETED" `
        -Success $true `
        -Message "Entrypoint returned without uncaught exception." `
        -ErrorText "" `
        -Loaded $loadedCount `
        -SkippedEmpty $skippedEmptyCount `
        -Failed $failedCount
}
catch {
    WriteStatus `
        -State "FAILED" `
        -Success $false `
        -Message "Bootstrap or runtime failed." `
        -ErrorText $_.Exception.Message `
        -Loaded $loadedCount `
        -SkippedEmpty $skippedEmptyCount `
        -Failed $failedCount

    Write-Host "def __SUBSYSTEM__ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {}

    Write-Host "def __SUBSYSTEM__ child PowerShell remains open for operator review." -ForegroundColor Cyan
}
'@

    $content = $template.
        Replace("__ENTRYPOINT__",$EntrypointPath).
        Replace("__SUPPORTIVE_LIST__",$SupportiveListPath).
        Replace("__STATUS__",$StatusPath).
        Replace("__TRANSCRIPT__",$TranscriptPath).
        Replace("__SUBSYSTEM__",$Subsystem)

    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function def_DeployFileHashState {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $row = [ordered]@{
        row_type = "DEPLOYMENT"
        source = $Source
        destination = $Destination
        state = ""
        success = $false
        source_sha256 = ""
        destination_sha256 = ""
        backup_path = ""
        error = ""
    }

    try {
        if (-not (Test-Path -LiteralPath $Source)) {
            throw "Deployment source missing: $Source"
        }

        def_EnsureDir -Path (Split-Path -Parent $Destination)

        $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
        $row.source_sha256 = $sourceHash

        if (-not (Test-Path -LiteralPath $Destination)) {
            Copy-Item -LiteralPath $Source -Destination $Destination -Force
            $row.state = "ORIGINAL_TO_APPLY"
        }
        else {
            $destinationHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()

            if ($destinationHash -eq $sourceHash) {
                $row.state = "PROPOSED_ALREADY_APPLIED_SKIP"
                $row.destination_sha256 = $destinationHash
                $row.success = $true
                return [pscustomobject]$row
            }

            $backupPath = "{0}.backup.{1}.{2}" -f $Destination,(Get-Date -Format "yyyyMMdd_HHmmss"),$destinationHash.Substring(0,12)
            Copy-Item -LiteralPath $Destination -Destination $backupPath -Force
            $row.backup_path = $backupPath

            Copy-Item -LiteralPath $Source -Destination $Destination -Force
            $row.state = "OTHER_TO_BACKUP_APPLY"
        }

        $deployedHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        $row.destination_sha256 = $deployedHash

        if ($deployedHash -ne $sourceHash) {
            throw "Deployment hash verification failed."
        }

        $row.success = $true
    }
    catch {
        $row.state = if ([string]::IsNullOrWhiteSpace([string]$row.state)) { "DEPLOY_ERROR" } else { $row.state }
        $row.error = $_.Exception.Message
    }

    return [pscustomobject]$row
}

function def_NewEncodedCommand {
    param([Parameter(Mandatory)][string]$ScriptPath)

    $escaped = $ScriptPath.Replace("'","''")
    $command = "& '$escaped'"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($command)
    return [Convert]::ToBase64String($bytes)
}

function def_StartSubsystem {
    param(
        [Parameter(Mandatory)][string]$Subsystem,
        [Parameter(Mandatory)][string]$LauncherPath,
        [Parameter(Mandatory)][string]$StatusPath
    )

    $row = [ordered]@{
        row_type = "SUBSYSTEM_ACTIVATION"
        subsystem = $Subsystem
        launcher = $LauncherPath
        status_path = $StatusPath
        pid = 0
        process_state = ""
        child_state = ""
        child_loaded = 0
        child_skipped_empty = 0
        child_failed = 0
        success = $false
        error = ""
    }

    try {
        if (Test-Path -LiteralPath $StatusPath) {
            Remove-Item -LiteralPath $StatusPath -Force -ErrorAction SilentlyContinue
        }

        $pwsh = (Get-Command pwsh -ErrorAction Stop).Source
        $encoded = def_NewEncodedCommand -ScriptPath $LauncherPath

        $process = Start-Process `
            -FilePath $pwsh `
            -ArgumentList @(
                "-NoLogo",
                "-NoProfile",
                "-NoExit",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                $encoded
            ) `
            -PassThru

        $row.pid = $process.Id

        Start-Sleep -Seconds $ActivationProbeSeconds

        $process.Refresh()

        if ($process.HasExited) {
            $row.process_state = "EXITED_$($process.ExitCode)"
        }
        else {
            $row.process_state = "RUNNING_WINDOW"
        }

        if (Test-Path -LiteralPath $StatusPath) {
            try {
                $status = Get-Content -LiteralPath $StatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $row.child_state = [string]$status.state
                $row.child_loaded = [int]$status.loaded
                $row.child_skipped_empty = [int]$status.skipped_empty
                $row.child_failed = [int]$status.failed

                if ([string]$status.state -eq "FAILED") {
                    $row.success = $false
                    $row.error = [string]$status.error
                }
                elseif ([string]$status.state -in @("SUPPORTIVE_IMPORTED","ENTRYPOINT_STARTED","COMPLETED")) {
                    $row.success = $true
                }
                else {
                    $row.success = (-not $process.HasExited)
                }
            }
            catch {
                $row.child_state = "STATUS_PARSE_ERROR"
                $row.success = (-not $process.HasExited)
                $row.error = $_.Exception.Message
            }
        }
        else {
            $row.child_state = "STATUS_NOT_WRITTEN"
            $row.success = (-not $process.HasExited)
        }
    }
    catch {
        $row.process_state = "START_ERROR"
        $row.child_state = "NOT_STARTED"
        $row.success = $false
        $row.error = $_.Exception.Message
    }

    return [pscustomobject]$row
}

function def_WriteHtml {
    param(
        [Parameter(Mandatory)]$Summary,
        [Parameter(Mandatory)]$MoveSummary,
        [Parameter(Mandatory)]$SupportiveRows,
        [Parameter(Mandatory)]$ActivationRows,
        [Parameter(Mandatory)]$NarrationRows
    )

    $css = @'
<style>
body{margin:0;padding:24px;background:#f7f8f6;color:#24312f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:12px}
h1{font-size:23px;margin:0 0 6px}
h2{font-size:17px;margin-top:25px;border-left:5px solid #0f766e;padding-left:9px}
.card{background:#fff;border:1px solid #d8e2df;border-radius:13px;padding:14px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:9px}
.metric{border:1px solid #d8e2df;border-radius:10px;padding:10px;min-height:70px}
.k{font-size:10px;color:#63706d;text-transform:uppercase}
.v{font-size:15px;font-weight:800;margin-top:4px;overflow-wrap:anywhere}
.ok{color:#18794e}.warn{color:#9a6700}.bad{color:#b42318}
.table-wrap{width:100%;overflow:auto;max-height:620px;border:1px solid #d8e2df;border-radius:9px}
table{width:100%;border-collapse:collapse;table-layout:auto;font-size:10.5px}
th{position:sticky;top:0;background:#e7efed;text-align:left;padding:6px;border:1px solid #d2dfdc;white-space:normal}
td{padding:5px 6px;border:1px solid #e2eae8;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:440px}
tr:nth-child(even){background:#fbfcfb}
.code{font-family:Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.empty{padding:14px;color:#63706d}
</style>
'@

    $gateClass = if ($Summary.gate -eq "FULL_ACTIVATION_SUCCESS") {
        "ok"
    }
    elseif ($Summary.gate -like "*REVIEW*") {
        "warn"
    }
    else {
        "bad"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>VIA v0135 Continuation</title>
$css
</head>
<body>
<h1>VIA · v0134 Continuation / Activation Hotfix · v0135</h1>

<div class="card">
<div class="grid">
<div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(def_HtmlEncode $Summary.gate)</div></div>
<div class="metric"><div class="k">v0134 Move Rows</div><div class="v">$($MoveSummary.rows)</div></div>
<div class="metric"><div class="k">v0134 Move Success</div><div class="v">$($MoveSummary.success)</div></div>
<div class="metric"><div class="k">v0134 Move Fail</div><div class="v">$($MoveSummary.fail)</div></div>
<div class="metric"><div class="k">Supportive Approved</div><div class="v">$($Summary.supportive_approved)</div></div>
<div class="metric"><div class="k">VRN</div><div class="v">$(def_HtmlEncode $Summary.vrn_activation)</div></div>
<div class="metric"><div class="k">VDF</div><div class="v">$(def_HtmlEncode $Summary.vdf_activation)</div></div>
<div class="metric"><div class="k">Organization Repeated</div><div class="v">NO</div></div>
</div>
</div>

<h2>Decision</h2>
<div class="card code">$(def_HtmlEncode $Summary.decision)

Next: $(def_HtmlEncode $Summary.next_step)</div>

<h2>Reused v0134 Organization Evidence</h2>
<div class="card">$(def_ToHtmlTableSafe -Rows @($MoveSummary) -MaxRows 10)</div>

<h2>Supportive Precheck</h2>
<div class="card">$(def_ToHtmlTableSafe -Rows $SupportiveRows -MaxRows 100)</div>

<h2>Deployment and Activation Evidence</h2>
<div class="card">$(def_ToHtmlTableSafe -Rows $ActivationRows -MaxRows 200)</div>

<h2>Dynamic Status Narration</h2>
<div class="card">$(def_ToHtmlTableSafe -Rows $NarrationRows -MaxRows 300)</div>

<h2>Output Paths</h2>
<div class="card code">
RunDir: $(def_HtmlEncode $Summary.run_dir)
PersistentRuntime: $(def_HtmlEncode $Summary.persistent_runtime)
VRNStatus: $(def_HtmlEncode $Summary.vrn_status)
VDFStatus: $(def_HtmlEncode $Summary.vdf_status)
VRNTranscript: $(def_HtmlEncode $Summary.vrn_transcript)
VDFTranscript: $(def_HtmlEncode $Summary.vdf_transcript)
HTML: $(def_HtmlEncode $ReportHtml)
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportHtml -Value $html -Encoding UTF8
}

function def_Main {
    def_Banner -Title "VIA · v0134 CONTINUATION / ACTIVATION HOTFIX v0135"

    if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) {
        throw "Approval phrase mismatch."
    }

    if (-not (Test-Path -LiteralPath $BaseDir)) {
        throw "BaseDir missing: $BaseDir"
    }

    foreach ($directory in @(
        $RunDir,
        $CsvDir,
        $JsonDir,
        $HtmlDir,
        $RuntimeCandidateDir,
        $PersistentRoot,
        $PersistentLauncherDir,
        $PersistentLogDir,
        $PersistentManifestDir,
        $PersistentHtmlDir
    )) {
        def_EnsureDir -Path $directory
    }

    def_Narrate -Stage "BOOT" -Message "Continuing from v0134; inventory and organization actions will not be repeated."

    $v0134Run = def_FindLatestV0134Run

    if ($null -eq $v0134Run) {
        throw "No v0134 organization run found."
    }

    $moveSummary = def_GetMoveSummary -V0134Run $v0134Run
    def_Narrate -Stage "V0134" -Message ("Reusing move evidence rows={0}, success={1}, fail={2}" -f $moveSummary.rows,$moveSummary.success,$moveSummary.fail) -Level "OK"

    $v0133Gate = def_FindV0133Gate

    if ($null -eq $v0133Gate) {
        throw "No FULL_ACTIVATION_ELIGIBLE v0133 gate found."
    }

    def_Narrate -Stage "GATE" -Message ("v0133 authority confirmed: {0}" -f $v0133Gate.path) -Level "OK"

    $supportiveListSource = def_FindSupportiveList

    if ([string]::IsNullOrWhiteSpace($supportiveListSource)) {
        throw "Approved supportive list not found."
    }

    $supportiveRows = @(def_PrecheckSupportiveList -Path $supportiveListSource)
    $supportiveMissing = @($supportiveRows | Where-Object { -not ($_.exists -eq $true -or $_.exists -eq "True") }).Count
    $supportiveParseBad = @(
        $supportiveRows |
        Where-Object {
            $_.extension -in @(".ps1",".psm1",".psd1") -and
            -not ($_.parse_ok -eq $true -or $_.parse_ok -eq "True")
        }
    ).Count

    def_WriteCsv -Data $supportiveRows -Path $SupportiveEvidenceCsv
    def_WriteJson -Data $supportiveRows -Path $SupportiveEvidenceJson

    def_Narrate -Stage "SUPPORTIVE" -Message ("Approved={0}, missing={1}, parse_bad={2}" -f @($supportiveRows).Count,$supportiveMissing,$supportiveParseBad) -Level $(if ($supportiveMissing -eq 0 -and $supportiveParseBad -eq 0) { "OK" } else { "ERROR" })

    $supportivePayload = @(Get-Content -LiteralPath $supportiveListSource -Raw -Encoding UTF8 | ConvertFrom-Json)
    def_WriteJson -Data $supportivePayload -Path $SupportiveListCandidate

    $vrnEntrypoint = Join-Path $BaseDir "functional modules\VRN\Invoke-VRN.ps1"
    $vdfEntrypoint = Join-Path $BaseDir "functional modules\VDF\Invoke-VDF.ps1"

    $vrnEntryCheck = def_TestPowerShellFile -Path $vrnEntrypoint
    $vdfEntryCheck = def_TestPowerShellFile -Path $vdfEntrypoint

    def_WriteChildLauncher `
        -Path $VrnLauncherCandidate `
        -Subsystem "VRN" `
        -EntrypointPath $vrnEntrypoint `
        -SupportiveListPath $SupportiveListDeployed `
        -StatusPath $VrnStatusPath `
        -TranscriptPath $VrnTranscriptPath

    def_WriteChildLauncher `
        -Path $VdfLauncherCandidate `
        -Subsystem "VDF" `
        -EntrypointPath $vdfEntrypoint `
        -SupportiveListPath $SupportiveListDeployed `
        -StatusPath $VdfStatusPath `
        -TranscriptPath $VdfTranscriptPath

    $vrnLauncherCheck = def_TestPowerShellFile -Path $VrnLauncherCandidate
    $vdfLauncherCheck = def_TestPowerShellFile -Path $VdfLauncherCandidate

    $manifest = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        continuation_from_v0134_run = $v0134Run.run_dir
        repeated_inventory = $false
        repeated_organization = $false
        v0134_move_rows = $moveSummary.rows
        v0134_move_success = $moveSummary.success
        v0134_move_fail = $moveSummary.fail
        v0133_gate_path = $v0133Gate.path
        v0133_gate = [string]$v0133Gate.data.gate
        supportive_list_source = $supportiveListSource
        supportive_approved = @($supportivePayload).Count
        supportive_missing = $supportiveMissing
        supportive_parse_bad = $supportiveParseBad
        empty_ps1_policy = "SKIP_EMPTY_PLACEHOLDER_WITH_SUCCESS_EVIDENCE"
        html_mixed_object_policy = "UNION_ALL_PROPERTY_NAMES_AND_SAFE_LOOKUP"
        vrn_entrypoint = $vrnEntrypoint
        vdf_entrypoint = $vdfEntrypoint
        vrn_entrypoint_parse_ok = $vrnEntryCheck.parse_ok
        vdf_entrypoint_parse_ok = $vdfEntryCheck.parse_ok
        vrn_launcher_parse_ok = $vrnLauncherCheck.parse_ok
        vdf_launcher_parse_ok = $vdfLauncherCheck.parse_ok
    }

    def_WriteJson -Data $manifest -Path $ManifestCandidate

    $deployPlan = @(
        [pscustomobject]@{source=$SupportiveListCandidate;destination=$SupportiveListDeployed},
        [pscustomobject]@{source=$VrnLauncherCandidate;destination=$VrnLauncherDeployed},
        [pscustomobject]@{source=$VdfLauncherCandidate;destination=$VdfLauncherDeployed},
        [pscustomobject]@{source=$ManifestCandidate;destination=$ManifestDeployed}
    )

    foreach ($item in $deployPlan) {
        $result = def_DeployFileHashState -Source $item.source -Destination $item.destination
        $script:ActivationEvidence.Add($result)
    }

    $deployRows = @($script:ActivationEvidence.ToArray())
    $deployFail = @($deployRows | Where-Object { -not ($_.success -eq $true -or $_.success -eq "True") }).Count

    $eligible = (
        [string]$v0133Gate.data.gate -eq "FULL_ACTIVATION_ELIGIBLE" -and
        $supportiveMissing -eq 0 -and
        $supportiveParseBad -eq 0 -and
        $vrnEntryCheck.parse_ok -and
        $vdfEntryCheck.parse_ok -and
        $vrnLauncherCheck.parse_ok -and
        $vdfLauncherCheck.parse_ok -and
        $deployFail -eq 0
    )

    $vrnActivation = "NOT_EXECUTED"
    $vdfActivation = "NOT_EXECUTED"

    if ($eligible -and $ActivateVrnVdf) {
        def_Narrate -Stage "ACTIVATE" -Message "Launching VRN and VDF with corrected empty-module handling."

        $vrnResult = def_StartSubsystem `
            -Subsystem "VRN" `
            -LauncherPath $VrnLauncherDeployed `
            -StatusPath $VrnStatusPath

        $script:ActivationEvidence.Add($vrnResult)

        $vdfResult = def_StartSubsystem `
            -Subsystem "VDF" `
            -LauncherPath $VdfLauncherDeployed `
            -StatusPath $VdfStatusPath

        $script:ActivationEvidence.Add($vdfResult)

        $vrnActivation = "{0}/{1}/Loaded={2}/EmptySkipped={3}" -f $vrnResult.process_state,$vrnResult.child_state,$vrnResult.child_loaded,$vrnResult.child_skipped_empty
        $vdfActivation = "{0}/{1}/Loaded={2}/EmptySkipped={3}" -f $vdfResult.process_state,$vdfResult.child_state,$vdfResult.child_loaded,$vdfResult.child_skipped_empty

        def_Narrate -Stage "VRN" -Message $vrnActivation -Level $(if ($vrnResult.success) { "OK" } else { "ERROR" })
        def_Narrate -Stage "VDF" -Message $vdfActivation -Level $(if ($vdfResult.success) { "OK" } else { "ERROR" })
    }
    elseif ($eligible) {
        $vrnActivation = "ELIGIBLE_NOT_REQUESTED"
        $vdfActivation = "ELIGIBLE_NOT_REQUESTED"
        def_Narrate -Stage "ACTIVATE" -Message "Activation eligible but disabled by parameter." -Level "WARN"
    }
    else {
        def_Narrate -Stage "ACTIVATE" -Message "Activation blocked by precheck; no bypass executed." -Level "ERROR"
    }

    $activationRows = @($script:ActivationEvidence.ToArray())
    def_WriteCsv -Data $activationRows -Path $ActivationEvidenceCsv
    def_WriteJson -Data $activationRows -Path $ActivationEvidenceJson

    $startRows = @(
        $activationRows |
        Where-Object { [string](def_GetPropertyValueSafe -Object $_ -PropertyName "row_type") -eq "SUBSYSTEM_ACTIVATION" }
    )

    $activationFail = @(
        $startRows |
        Where-Object { -not ((def_GetPropertyValueSafe -Object $_ -PropertyName "success") -eq $true) }
    ).Count

    $gate = "BLOCKED_REVIEW_REQUIRED"
    $risk = "HIGH_REVIEW"
    $decision = "Continuation evidence generated, but activation precheck or child runtime failed."
    $nextStep = "Read child status JSON and transcripts; do not rerun v0134 organization."

    if ($eligible -and $ActivateVrnVdf -and @($startRows).Count -eq 2 -and $activationFail -eq 0) {
        $gate = "FULL_ACTIVATION_SUCCESS"
        $risk = if ($moveSummary.fail -eq 0) {
            "LOW_CONTROLLED_WITH_HYDRA_MONITORING"
        }
        else {
            "LOW_RUNTIME_WITH_ORGANIZATION_REVIEW"
        }
        $decision = "v0134 organization evidence was reused without rerun; empty supportive placeholders were safely skipped; VRN and VDF reached successful child states."
        $nextStep = "Use VRN/VDF status JSON and transcripts for operational monitoring."
    }
    elseif ($eligible -and -not $ActivateVrnVdf) {
        $gate = "ACTIVATION_ELIGIBLE_NOT_REQUESTED"
        $risk = "LOW_REVIEW"
        $decision = "All continuation checks passed; activation was disabled by parameter."
        $nextStep = "Run v0135 with ActivateVrnVdf=true."
    }

    $summary = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        gate = $gate
        risk = $risk
        decision = $decision
        next_step = $nextStep
        v0134_run_dir = $v0134Run.run_dir
        v0134_move_rows = $moveSummary.rows
        v0134_move_success = $moveSummary.success
        v0134_move_fail = $moveSummary.fail
        organization_repeated = $false
        v0133_gate = [string]$v0133Gate.data.gate
        supportive_approved = @($supportivePayload).Count
        supportive_missing = $supportiveMissing
        supportive_parse_bad = $supportiveParseBad
        vrn_activation = $vrnActivation
        vdf_activation = $vdfActivation
        run_dir = $RunDir
        persistent_runtime = $PersistentRoot
        vrn_status = $VrnStatusPath
        vdf_status = $VdfStatusPath
        vrn_transcript = $VrnTranscriptPath
        vdf_transcript = $VdfTranscriptPath
        html = $ReportHtml
    }

    def_WriteJson -Data $summary -Path $SummaryJson

    def_WriteHtml `
        -Summary ([pscustomobject]$summary) `
        -MoveSummary $moveSummary `
        -SupportiveRows $supportiveRows `
        -ActivationRows $activationRows `
        -NarrationRows @($script:Narration.ToArray())

    $htmlDeploy = def_DeployFileHashState `
        -Source $ReportHtml `
        -Destination (Join-Path $PersistentHtmlDir (Split-Path -Leaf $ReportHtml))

    $script:ActivationEvidence.Add($htmlDeploy)

    $activationRows = @($script:ActivationEvidence.ToArray())
    def_WriteCsv -Data $activationRows -Path $ActivationEvidenceCsv
    def_WriteJson -Data $activationRows -Path $ActivationEvidenceJson

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $ReportHtml)) {
        Start-Process -FilePath $ReportHtml
    }

    def_Banner -Title "VIA · v0135 FINAL RESULT"

    Write-Host ("def Gate                    : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                    : {0}" -f $summary.risk) -ForegroundColor Yellow
    Write-Host ("def OrganizationRepeated    : False") -ForegroundColor Green
    Write-Host ("def v0134MoveRows           : {0}" -f $summary.v0134_move_rows) -ForegroundColor White
    Write-Host ("def v0134MoveSuccess        : {0}" -f $summary.v0134_move_success) -ForegroundColor Green
    Write-Host ("def v0134MoveFail           : {0}" -f $summary.v0134_move_fail) -ForegroundColor Yellow
    Write-Host ("def SupportiveApproved      : {0}" -f $summary.supportive_approved) -ForegroundColor White
    Write-Host ("def SupportiveMissing       : {0}" -f $summary.supportive_missing) -ForegroundColor Red
    Write-Host ("def SupportiveParseBad      : {0}" -f $summary.supportive_parse_bad) -ForegroundColor Red
    Write-Host ("def VRNActivation           : {0}" -f $summary.vrn_activation) -ForegroundColor Green
    Write-Host ("def VDFActivation           : {0}" -f $summary.vdf_activation) -ForegroundColor Green
    Write-Host ("def VRNStatus               : {0}" -f $summary.vrn_status) -ForegroundColor Cyan
    Write-Host ("def VDFStatus               : {0}" -f $summary.vdf_status) -ForegroundColor Cyan
    Write-Host ("def RunDir                  : {0}" -f $summary.run_dir) -ForegroundColor Cyan
    Write-Host ("def HTML                    : {0}" -f $summary.html) -ForegroundColor Green
}
try {
    def_Main
}
catch {
    def_Banner -Title "VIA · v0135 OUTER SAFE CATCH"

    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def v0134 organization was not repeated. No delete, Stop-Process or forced activation was executed." -ForegroundColor Yellow

    try {
        $fallback = [ordered]@{
            version = $Version
            generated_at = (Get-Date).ToString("o")
            gate = "OUTER_SAFE_CATCH"
            risk = "HIGH_REVIEW"
            error_type = $_.Exception.GetType().FullName
            error_message = $_.Exception.Message
            stack_trace = $_.ScriptStackTrace
            run_dir = $RunDir
            organization_repeated = $false
        }

        def_WriteJson -Data $fallback -Path $SummaryJson
    }
    catch {}
}
finally {
    if ($KeepParentPowerShellOpen) {
        Write-Host ""
        Write-Host "def Parent PowerShell remains open. v0134 organization was not repeated." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
