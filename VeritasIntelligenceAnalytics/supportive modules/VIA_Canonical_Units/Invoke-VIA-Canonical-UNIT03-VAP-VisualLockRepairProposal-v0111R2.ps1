#requires -Version 7.0

[CmdletBinding()]
param(
    [string]$DownloadsRoot = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [string]$RepoProjectRoot = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$ReportRoot = "$env:USERPROFILE\VIA_Reports",
    [string]$RelativeEnginePath = 'functional modules\VAP\engine\VAP_ENG002_AutoplotEngine_v001.py',
    [string]$RequiredAdjudicationGate = 'UNIT03_VISUAL_SEMANTIC_REVIEW_BLOCKED',
    [double]$ObservedFillOpacity = 0.40,
    [double]$RequiredFillOpacity = 0.75,
    [int]$ContextLineCount = 3,
    [bool]$ExecuteCandidate = $false,
    [bool]$CreatePatchedCandidate = $false,
    [bool]$AllowNetwork = $false,
    [bool]$AllowDatabaseOrSSOTWrite = $false,
    [bool]$AllowCanonicalMutation = $false,
    [bool]$AllowPromotion = $false,
    [bool]$OpenReport = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'Continue'

# =============================================================================
# def 01 - Constants and proposal-only boundary
# =============================================================================

$Script:Version = '1.0.11R2'
$Script:Method = 'VIA_CANONICAL_UNIT03_VAP_VISUAL_LOCK_REPAIR_PROPOSAL_v0111'
$Script:Policy = 'SIX GOVERNED READ-ONLY LANES / APPEND-ONLY REPORT AND PATCH PROPOSAL / NO TARGET IMPORT / NO CANDIDATE EXECUTION / NO SOURCE COPY / NO SOURCE WRITE / NO NETWORK / NO DB OR SSOT WRITE / NO CANONICAL MUTATION / NO PROMOTION / NO ROLLBACK'
$Script:Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$Script:OutputDir = $null
$Script:LogRows = [System.Collections.Generic.List[string]]::new()

# =============================================================================
# def 02 - Logging, progress, paths, and append-only writers
# =============================================================================

function def_WriteLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet('INFO', 'PASS', 'WARN', 'FAIL')]
        [string]$Level = 'INFO'
    )

    $Line = '[{0}] [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    $Script:LogRows.Add($Line)
    $Color = switch ($Level) {
        'PASS' { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
        default { 'Gray' }
    }
    Write-Host "def $Line" -ForegroundColor $Color
}

function def_WriteProgress {
    param(
        [Parameter(Mandatory)]
        [int]$Percent,
        [Parameter(Mandatory)]
        [string]$Status
    )

    Write-Progress -Id 1110 -Activity 'VIA UNIT03 VAP visual-lock repair proposal' -Status $Status -PercentComplete $Percent
    def_WriteLog -Message "$Percent% - $Status"
}

function def_TestPathUnderRoot {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Root
    )

    $Separator = [System.IO.Path]::DirectorySeparatorChar
    $Alternate = [System.IO.Path]::AltDirectorySeparatorChar
    $TrimCharacters = [char[]]@($Separator, $Alternate)
    $FullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd($TrimCharacters)
    $FullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd($TrimCharacters)
    return $FullPath.Equals($FullRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $FullPath.StartsWith($FullRoot + $Separator, [System.StringComparison]::OrdinalIgnoreCase)
}

function def_AssertReportDestination {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (def_TestPathUnderRoot -Path $Path -Root $ReportRoot)) {
        throw "REPORT_RUN_OUTSIDE_REPORT_ROOT: $Path"
    }
    if (def_TestPathUnderRoot -Path $Path -Root $DownloadsRoot) {
        throw "REPORT_RUN_INSIDE_DOWNLOADS_SOURCE: $Path"
    }
    if (def_TestPathUnderRoot -Path $Path -Root $RepoProjectRoot) {
        throw "REPORT_RUN_INSIDE_CANONICAL_REPOSITORY: $Path"
    }
    if (Test-Path -LiteralPath $Path) {
        throw "APPEND_ONLY_RUN_DIRECTORY_ALREADY_EXISTS: $Path"
    }
}

function def_WriteUtf8File {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Content
    )

    if ([string]::IsNullOrWhiteSpace($Script:OutputDir)) { throw 'OUTPUT_DIRECTORY_NOT_INITIALIZED' }
    if (-not (def_TestPathUnderRoot -Path $Path -Root $Script:OutputDir)) {
        throw "REPORT_WRITE_OUTSIDE_RUN_DIRECTORY: $Path"
    }
    $Parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($Parent)) {
        [System.IO.Directory]::CreateDirectory($Parent) | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $Script:Utf8NoBom)
}

function def_GetValue {
    param(
        [Parameter(Mandatory)]
        [object]$Row,
        [Parameter(Mandatory)]
        [string]$Name
    )

    $Property = $Row.PSObject.Properties[$Name]
    if ($null -eq $Property -or $null -eq $Property.Value) { return '' }
    return $Property.Value
}

function def_HtmlEncode {
    param(
        [AllowEmptyString()]
        [string]$Value
    )

    return [System.Net.WebUtility]::HtmlEncode($Value)
}

function def_GetTextSha256 {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Text
    )

    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return [Convert]::ToHexString($Hasher.ComputeHash($Script:Utf8NoBom.GetBytes($Text))) }
    finally { $Hasher.Dispose() }
}

# =============================================================================
# def 03 - Configuration and immutable evidence resolution
# =============================================================================

function def_AssertConfiguration {
    if ($ExecuteCandidate) { throw 'CANDIDATE_EXECUTION_MUST_REMAIN_FALSE' }
    if ($CreatePatchedCandidate) { throw 'PATCHED_CANDIDATE_CREATION_MUST_REMAIN_FALSE' }
    if ($AllowNetwork) { throw 'NETWORK_MUST_REMAIN_FALSE' }
    if ($AllowDatabaseOrSSOTWrite) { throw 'DB_OR_SSOT_WRITE_MUST_REMAIN_FALSE' }
    if ($AllowCanonicalMutation) { throw 'CANONICAL_MUTATION_MUST_REMAIN_FALSE' }
    if ($AllowPromotion) { throw 'PROMOTION_MUST_REMAIN_FALSE' }
    if ($ContextLineCount -lt 0 -or $ContextLineCount -gt 10) { throw 'CONTEXT_LINE_COUNT_OUT_OF_RANGE' }
    if ([Math]::Abs($ObservedFillOpacity - 0.40) -gt 0.000001) { throw 'OBSERVED_OPACITY_CONTRACT_MUST_REMAIN_0_40' }
    if ([Math]::Abs($RequiredFillOpacity - 0.75) -gt 0.000001) { throw 'REQUIRED_OPACITY_CONTRACT_MUST_REMAIN_0_75' }
    foreach ($Root in @($DownloadsRoot, $RepoProjectRoot, $ReportRoot)) {
        if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
            throw "REQUIRED_ROOT_NOT_FOUND: $Root"
        }
    }
}

function def_GetLatestAuditRun {
    param(
        [Parameter(Mandatory)]
        [string]$Root
    )

    $Runs = @(
        Get-ChildItem -LiteralPath $Root -Directory -ErrorAction Stop |
        Where-Object Name -like 'RUN_*_VIA_DOWNLOADS_UIUX_CLOSEOUT_AUDIT_v0103' |
        Sort-Object LastWriteTime -Descending
    )
    if ($Runs.Count -eq 0) { throw 'V0103_AUDIT_RUN_NOT_FOUND' }
    return $Runs[0]
}

function def_ResolveAdjudicationSource {
    param(
        [Parameter(Mandatory)]
        [System.IO.DirectoryInfo]$AuditRun
    )

    $Candidates = @(
        Get-ChildItem -LiteralPath $AuditRun.FullName -Directory -ErrorAction Stop |
        Where-Object Name -like 'P0_UNIT03_VAP_VISUAL_SEMANTIC_ADJUDICATION_v0110_*' |
        Sort-Object LastWriteTime -Descending
    )
    foreach ($Directory in $Candidates) {
        $SummaryPath = Join-Path $Directory.FullName 'VIA_UNIT03_VAP_Visual_Semantic_Adjudication_Summary.json'
        if (-not (Test-Path -LiteralPath $SummaryPath -PathType Leaf)) { continue }
        try { $Summary = Get-Content -Raw -LiteralPath $SummaryPath | ConvertFrom-Json } catch { continue }
        try {
            $ContractPass =
                [string]$Summary.overlay_gate.gate -ceq $RequiredAdjudicationGate -and
                [bool]$Summary.source_gate.preserved -and
                -not [bool]$Summary.source_gate.source_report_mutated -and
                [bool]$Summary.safety.hash_lock_pass -and
                [bool]$Summary.safety.operational_pass -and
                [bool]$Summary.safety.candidate_deterministic -and
                [int]$Summary.safety.candidate_executions -eq 0 -and
                [int]$Summary.safety.canonical_mutations -eq 0 -and
                [int]$Summary.safety.promotions -eq 0 -and
                -not [bool]$Summary.visual.semantic_pass -and
                [string]$Summary.coverage.write_workbench -ceq 'NOT_FULLY_COVERED'
        }
        catch { $ContractPass = $false }
        if (-not $ContractPass) { continue }
        $DynamicRun = [string]$Summary.source_v0109_run
        $DynamicSummaryPath = Join-Path $DynamicRun 'VIA_UNIT03_VAP_Guarded_Dynamic_Summary.json'
        if (-not (Test-Path -LiteralPath $DynamicSummaryPath -PathType Leaf)) { continue }
        try { $DynamicSummary = Get-Content -Raw -LiteralPath $DynamicSummaryPath | ConvertFrom-Json } catch { continue }
        return [pscustomobject]@{
            Directory = $Directory
            SummaryPath = $SummaryPath
            Summary = $Summary
            DynamicRun = $DynamicRun
            DynamicSummaryPath = $DynamicSummaryPath
            DynamicSummary = $DynamicSummary
        }
    }
    throw 'COMPLETED_V0110_VISUAL_ADJUDICATION_SOURCE_NOT_FOUND'
}

# =============================================================================
# def 04 - Static Python line scanner; target code is never imported or executed
# =============================================================================

function def_GetFunctionNameFromLine {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Line,
        [Parameter(Mandatory)]
        [string]$CurrentFunction
    )

    $Match = [regex]::Match($Line, '^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')
    if ($Match.Success) { return $Match.Groups[1].Value }
    return $CurrentFunction
}

function def_GetDecimalTokenPattern {
    param(
        [Parameter(Mandatory)]
        [double]$Value
    )

    $Invariant = [System.Globalization.CultureInfo]::InvariantCulture
    $Full = $Value.ToString('0.################', $Invariant)
    $WithoutLeadingZero = if ($Full.StartsWith('0.')) { $Full.Substring(1) } else { $Full }
    $Alternatives = @([regex]::Escape($Full))
    if ($WithoutLeadingZero -cne $Full) { $Alternatives += [regex]::Escape($WithoutLeadingZero) }
    return '(?<![0-9.])(?:' + ($Alternatives -join '|') + ')(?:0+)?(?![0-9])'
}

function def_GetOpacityLineRecords {
    param(
        [Parameter(Mandatory)]
        [string]$Side,
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [double]$Observed,
        [Parameter(Mandatory)]
        [double]$Required
    )

    $Lines = @(Get-Content -LiteralPath $Path)
    $CurrentFunction = '<module>'
    $ObservedPattern = def_GetDecimalTokenPattern -Value $Observed
    $RequiredPattern = def_GetDecimalTokenPattern -Value $Required
    $Rows = [System.Collections.Generic.List[object]]::new()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        $Line = [string]$Lines[$Index]
        $CurrentFunction = def_GetFunctionNameFromLine -Line $Line -CurrentFunction $CurrentFunction
        $HasOpacityKeyword = $Line -match '(?i)(fill[-_ ]?opacity|opacity)'
        $HasObservedValue = $Line -match $ObservedPattern
        $HasRequiredValue = $Line -match $RequiredPattern
        if (-not $HasOpacityKeyword -and -not $HasObservedValue -and -not $HasRequiredValue) { continue }
        $Rows.Add([pscustomobject]@{
            Side = $Side
            LineNumber = $Index + 1
            Function = $CurrentFunction
            HasOpacityKeyword = $HasOpacityKeyword
            HasObservedValue = $HasObservedValue
            HasRequiredValue = $HasRequiredValue
            DirectObservedLock = $HasOpacityKeyword -and $HasObservedValue
            DirectRequiredLock = $HasOpacityKeyword -and $HasRequiredValue
            LineText = $Line.TrimEnd()
            LineSHA256 = def_GetTextSha256 -Text $Line
            Path = $Path
        })
    }
    return @($Rows)
}

function def_GetContextText {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [int]$LineNumber,
        [Parameter(Mandatory)]
        [int]$Radius
    )

    $Lines = @(Get-Content -LiteralPath $Path)
    $Start = [Math]::Max(1, $LineNumber - $Radius)
    $End = [Math]::Min($Lines.Count, $LineNumber + $Radius)
    $Output = for ($Number = $Start; $Number -le $End; $Number++) {
        $Prefix = if ($Number -eq $LineNumber) { '>' } else { ' ' }
        '{0}{1,6}: {2}' -f $Prefix, $Number, [string]$Lines[$Number - 1]
    }
    return $Output -join [Environment]::NewLine
}

function def_GetRepairCandidate {
    param(
        [Parameter(Mandatory)]
        [object[]]$Rows
    )

    $Direct = @($Rows | Where-Object DirectObservedLock -eq $true)
    if ($Direct.Count -eq 1) {
        return [pscustomobject]@{ Confidence = 'HIGH_DIRECT_SINGLETON'; Row = $Direct[0]; CandidateCount = 1 }
    }
    if ($Direct.Count -gt 1) {
        return [pscustomobject]@{ Confidence = 'BLOCK_MULTIPLE_DIRECT_LOCKS'; Row = $null; CandidateCount = $Direct.Count }
    }
    $Contextual = @($Rows | Where-Object { $_.Function -ceq 'chart_code' -and $_.HasObservedValue })
    if ($Contextual.Count -eq 1) {
        return [pscustomobject]@{ Confidence = 'MEDIUM_CHART_CODE_SINGLETON'; Row = $Contextual[0]; CandidateCount = 1 }
    }
    return [pscustomobject]@{ Confidence = 'BLOCK_NO_UNIQUE_REPAIR_LINE'; Row = $null; CandidateCount = $Contextual.Count }
}

function def_NewPatchProposal {
    param(
        [Parameter(Mandatory)]
        [object]$RepairCandidate,
        [Parameter(Mandatory)]
        [string]$CandidateHash,
        [Parameter(Mandatory)]
        [double]$ObservedOpacity,
        [Parameter(Mandatory)]
        [double]$RequiredOpacity
    )

    if ($null -eq $RepairCandidate.Row) {
        return [pscustomobject]@{
            Ready = $false
            Confidence = $RepairCandidate.Confidence
            LineNumber = 0
            OriginalLine = ''
            ProposedLine = ''
            OriginalLineSHA256 = ''
            ProposedLineSHA256 = ''
            ReplacementCount = 0
            CandidateSHA256 = $CandidateHash
        }
    }
    $OriginalLine = [string]$RepairCandidate.Row.LineText
    $Pattern = [regex](def_GetDecimalTokenPattern -Value $ObservedOpacity)
    $ReplacementCount = $Pattern.Matches($OriginalLine).Count
    $ProposedLine = if ($ReplacementCount -eq 1) {
        $Pattern.Replace($OriginalLine, $RequiredOpacity.ToString('0.00', [System.Globalization.CultureInfo]::InvariantCulture), 1)
    }
    else { '' }
    return [pscustomobject]@{
        Ready = $ReplacementCount -eq 1 -and -not [string]::IsNullOrWhiteSpace($ProposedLine)
        Confidence = $RepairCandidate.Confidence
        LineNumber = [int]$RepairCandidate.Row.LineNumber
        OriginalLine = $OriginalLine
        ProposedLine = $ProposedLine
        OriginalLineSHA256 = def_GetTextSha256 -Text $OriginalLine
        ProposedLineSHA256 = if ([string]::IsNullOrWhiteSpace($ProposedLine)) { '' } else { def_GetTextSha256 -Text $ProposedLine }
        ReplacementCount = $ReplacementCount
        CandidateSHA256 = $CandidateHash
    }
}

# =============================================================================
# def 05 - Six governed lanes, causality, and fail-closed decision
# =============================================================================

function def_NewLaneRow {
    param(
        [Parameter(Mandatory)]
        [string]$Lane,
        [Parameter(Mandatory)]
        [string]$Purpose,
        [Parameter(Mandatory)]
        [string]$Status,
        [Parameter(Mandatory)]
        [string]$Evidence,
        [Parameter(Mandatory)]
        [string]$GateImpact
    )

    return [pscustomobject]@{
        Lane = $Lane
        Purpose = $Purpose
        Status = $Status
        Evidence = $Evidence
        GateImpact = $GateImpact
        SourceMutation = 0
        CandidateExecution = 0
    }
}

function def_GetCausalityRows {
    param(
        [Parameter(Mandatory)]
        [bool]$SourceHashPass,
        [Parameter(Mandatory)]
        [object]$RepairCandidate,
        [Parameter(Mandatory)]
        [object]$PatchProposal,
        [Parameter(Mandatory)]
        [object[]]$CanonicalRows
    )

    $CanonicalRequired = @($CanonicalRows | Where-Object DirectRequiredLock -eq $true).Count -gt 0
    return @(
        [pscustomobject]@{ Check = 'SOURCE_HASH_LOCK'; Result = $SourceHashPass; Meaning = 'Static source equals the exact v1.0.9 tested source'; GateImpact = if ($SourceHashPass) { 'PASS' } else { 'BLOCK' } }
        [pscustomobject]@{ Check = 'CANDIDATE_OUTPUT_OBSERVED'; Result = $true; Meaning = 'Both deterministic candidate charts emitted fill-opacity 0.4'; GateImpact = 'CONFIRMED_REGRESSION' }
        [pscustomobject]@{ Check = 'CANONICAL_OUTPUT_REFERENCE'; Result = $true; Meaning = 'Canonical baseline emitted governed fill-opacity 0.75'; GateImpact = 'GOVERNANCE_REFERENCE' }
        [pscustomobject]@{ Check = 'CANONICAL_SOURCE_LITERAL'; Result = $CanonicalRequired; Meaning = if ($CanonicalRequired) { 'Canonical source contains a direct 0.75 opacity lock' } else { 'Canonical output remains the authority; source may derive the value indirectly' }; GateImpact = 'INFORMATIONAL' }
        [pscustomobject]@{ Check = 'UNIQUE_CANDIDATE_CAUSE'; Result = $null -ne $RepairCandidate.Row; Meaning = $RepairCandidate.Confidence; GateImpact = if ($null -ne $RepairCandidate.Row) { 'PASS' } else { 'BLOCK' } }
        [pscustomobject]@{ Check = 'SINGLE_TOKEN_PATCH_PROPOSAL'; Result = $PatchProposal.Ready; Meaning = "ReplacementCount=$($PatchProposal.ReplacementCount)"; GateImpact = if ($PatchProposal.Ready) { 'PROPOSAL_READY' } else { 'BLOCK' } }
        [pscustomobject]@{ Check = 'WRITE_WORKBENCH_SEQUENCE'; Result = $false; Meaning = 'write_workbench remains uncovered and must be tested only after the visual lock repair passes two isolated trials'; GateImpact = 'SEQUENCE_PENDING' }
    )
}

function def_GetPatchText {
    param(
        [Parameter(Mandatory)]
        [object]$PatchProposal,
        [Parameter(Mandatory)]
        [string]$RelativePath,
        [Parameter(Mandatory)]
        [string]$ContextText
    )

    if (-not $PatchProposal.Ready) {
        return @"
# VIA UNIT03 VAP visual-lock repair proposal v1.0.11
# STATE: NOT_READY
# CONFIDENCE: $($PatchProposal.Confidence)
# NO SOURCE MUTATION WAS EXECUTED.
"@
    }
    return @"
# VIA UNIT03 VAP visual-lock repair proposal v1.0.11
# STATE: PROPOSAL_ONLY_EXPLICIT_APPROVAL_REQUIRED
# SOURCE_SHA256: $($PatchProposal.CandidateSHA256)
# ORIGINAL_LINE_SHA256: $($PatchProposal.OriginalLineSHA256)
# PROPOSED_LINE_SHA256: $($PatchProposal.ProposedLineSHA256)
# RELATIVE_PATH: $RelativePath
# LINE: $($PatchProposal.LineNumber)
# REQUIRED_VISUAL_LOCK: fill-opacity=0.75
# NO SOURCE MUTATION WAS EXECUTED.

--- a/$($RelativePath.Replace('\', '/'))
+++ b/$($RelativePath.Replace('\', '/'))
@@ -$($PatchProposal.LineNumber),1 +$($PatchProposal.LineNumber),1 @@
-$($PatchProposal.OriginalLine)
+$($PatchProposal.ProposedLine)

# READ-ONLY CONTEXT
$ContextText
"@
}

# =============================================================================
# def 06 - HTML UI matrix
# =============================================================================

function def_ConvertRowsToHtmlTable {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyCollection()]
        [System.Collections.IEnumerable]$Rows,
        [Parameter(Mandatory)]
        [string[]]$Columns
    )

    $Items = @($Rows)
    if ($Items.Count -eq 0) { return '<p class="empty">No rows.</p>' }
    $Header = ($Columns | ForEach-Object { '<th>' + (def_HtmlEncode -Value $_) + '</th>' }) -join ''
    $Body = foreach ($Item in $Items) {
        $Cells = foreach ($Column in $Columns) {
            '<td>' + (def_HtmlEncode -Value ([string](def_GetValue -Row $Item -Name $Column))) + '</td>'
        }
        '<tr>' + ($Cells -join '') + '</tr>'
    }
    return '<div class="table-wrap"><table><thead><tr>' + $Header + '</tr></thead><tbody>' + ($Body -join '') + '</tbody></table></div>'
}

function def_WriteHtmlReport {
    param(
        [Parameter(Mandatory)]
        [object[]]$LaneRows,
        [Parameter(Mandatory)]
        [object[]]$HashRows,
        [Parameter(Mandatory)]
        [object[]]$CandidateRows,
        [Parameter(Mandatory)]
        [object[]]$CanonicalRows,
        [Parameter(Mandatory)]
        [object[]]$CausalityRows,
        [Parameter(Mandatory)]
        [object]$PatchProposal,
        [Parameter(Mandatory)]
        [string]$GateColor,
        [Parameter(Mandatory)]
        [string]$Gate,
        [Parameter(Mandatory)]
        [string]$PatchPath,
        [Parameter(Mandatory)]
        [string]$Path
    )

    $LaneTable = def_ConvertRowsToHtmlTable -Rows $LaneRows -Columns @('Lane', 'Purpose', 'Status', 'Evidence', 'GateImpact', 'SourceMutation', 'CandidateExecution')
    $HashTable = def_ConvertRowsToHtmlTable -Rows $HashRows -Columns @('Side', 'ExpectedSHA256', 'ActualSHA256', 'Match', 'Bytes', 'Path')
    $CandidateTable = def_ConvertRowsToHtmlTable -Rows $CandidateRows -Columns @('LineNumber', 'Function', 'HasOpacityKeyword', 'HasObservedValue', 'HasRequiredValue', 'DirectObservedLock', 'LineText', 'LineSHA256')
    $CanonicalTable = def_ConvertRowsToHtmlTable -Rows $CanonicalRows -Columns @('LineNumber', 'Function', 'HasOpacityKeyword', 'HasObservedValue', 'HasRequiredValue', 'DirectRequiredLock', 'LineText', 'LineSHA256')
    $CausalityTable = def_ConvertRowsToHtmlTable -Rows $CausalityRows -Columns @('Check', 'Result', 'Meaning', 'GateImpact')
    $PatchRows = @([pscustomobject]@{
        Ready = $PatchProposal.Ready
        Confidence = $PatchProposal.Confidence
        LineNumber = $PatchProposal.LineNumber
        OriginalLine = $PatchProposal.OriginalLine
        ProposedLine = $PatchProposal.ProposedLine
        ReplacementCount = $PatchProposal.ReplacementCount
        CandidateSHA256 = $PatchProposal.CandidateSHA256
        MutationAllowed = $false
    })
    $PatchTable = def_ConvertRowsToHtmlTable -Rows $PatchRows -Columns @('Ready', 'Confidence', 'LineNumber', 'OriginalLine', 'ProposedLine', 'ReplacementCount', 'CandidateSHA256', 'MutationAllowed')
    $ColorClass = $GateColor.ToLowerInvariant()
    $EncodedOutput = def_HtmlEncode -Value $Script:OutputDir
    $EncodedPatchPath = def_HtmlEncode -Value $PatchPath
    $Html = @"
<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA UNIT03 VAP Visual-Lock Repair Proposal v1.0.11</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#111b2d;--line:#2c3b54;--text:#dbe7f7;--muted:#93a4bc;--yellow:#f5c451;--red:#ef6b73;--green:#65d39a}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:11px/1.4 Segoe UI,Arial,sans-serif}.wrap{max-width:1900px;margin:auto;padding:16px}.hero,.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px;margin-bottom:11px}h1{font-size:19px;margin:0 0 7px}h2{font-size:14px;margin:0 0 9px}.status{font-size:13px;font-weight:700}.yellow{color:var(--yellow)}.red{color:var(--red)}.green{color:var(--green)}.muted{color:var(--muted)}.bar{height:7px;background:#202d43;border-radius:9px;overflow:hidden;margin:8px 0}.bar span{display:block;width:100%;height:100%;background:linear-gradient(90deg,var(--green),var(--yellow))}.table-wrap{max-height:540px;overflow:auto;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;table-layout:auto}th,td{padding:4px 6px;border-bottom:1px solid var(--line);border-right:1px solid #1e2b40;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere}th{position:sticky;top:0;background:#17243a;color:#fff;z-index:1}.empty{color:var(--muted)}code{color:#b8dbff}
</style></head><body><div class="wrap">
<section class="hero"><h1>VIA · UNIT03 VAP Visual-Lock Repair Proposal v1.0.11</h1><div class="status $ColorClass">$GateColor · $Gate</div><div class="bar"><span></span></div><p>Observed candidate fill-opacity <strong class="red">0.40</strong> · required visual lock <strong class="green">0.75</strong></p><p class="muted">Proposal only／candidate execution 0／source copy 0／source write 0／network 0／DB/SSOT write 0／canonical mutation 0／promotion 0</p></section>
<section class="panel"><h2>Six Governed Lanes</h2>$LaneTable</section>
<section class="panel"><h2>HASH-STATE · Source Authority</h2>$HashTable</section>
<section class="panel"><h2>MODULE · Candidate Opacity Scan</h2>$CandidateTable</section>
<section class="panel"><h2>ENGINE · Canonical Reference Scan</h2>$CanonicalTable</section>
<section class="panel"><h2>FUNCTION-LIB · Causality Matrix</h2>$CausalityTable</section>
<section class="panel"><h2>OTHERS · Single-Line Repair Proposal</h2>$PatchTable<p class="muted">Patch proposal: <code>$EncodedPatchPath</code></p></section>
<section class="panel"><h2>Dynamic Status Narration</h2><p>The v1.0.10 RED gate is confirmed as a real visual-lock regression, not a formatting false positive. This report only identifies a hash-locked single-line proposal. It does not create a patched candidate or authorize source mutation. After explicit approval, the next sequential stage may create one run-local patched candidate, execute two guarded visual trials, and then perform a separate write_workbench targeted test. Promotion remains blocked.</p><p class="muted">Output: $EncodedOutput</p></section>
</div></body></html>
"@
    def_WriteUtf8File -Path $Path -Content $Html
}

# =============================================================================
# def 07 - Main: one I/O lane, six governed decisions, zero source mutation
# =============================================================================

function def_Main {
    try {
        def_WriteLog -Message "VIA UNIT03 VAP visual-lock repair proposal v$Script:Version"
        def_WriteLog -Message "Policy: $Script:Policy"
        def_AssertConfiguration

        def_WriteProgress -Percent 5 -Status 'FLOW01 authority and source evidence'
        $AuditRun = def_GetLatestAuditRun -Root $ReportRoot
        $Source = def_ResolveAdjudicationSource -AuditRun $AuditRun
        $CandidatePath = Join-Path $DownloadsRoot $RelativeEnginePath
        $CanonicalPath = Join-Path $RepoProjectRoot $RelativeEnginePath
        foreach ($Path in @($CandidatePath, $CanonicalPath)) {
            if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "ENGINE_SOURCE_NOT_FOUND: $Path" }
        }
        $Script:OutputDir = Join-Path $AuditRun.FullName "P0_UNIT03_VAP_VISUAL_LOCK_REPAIR_PROPOSAL_v0111_$Script:Stamp"
        def_AssertReportDestination -Path $Script:OutputDir
        [System.IO.Directory]::CreateDirectory($Script:OutputDir) | Out-Null

        def_WriteProgress -Percent 17 -Status 'FLOW02 hash-lock tested candidate and canonical source'
        $ExpectedCandidateHash = [string]$Source.DynamicSummary.hashes.candidate
        $ExpectedCanonicalHash = [string]$Source.DynamicSummary.hashes.canonical
        $CandidateActualHash = (Get-FileHash -LiteralPath $CandidatePath -Algorithm SHA256).Hash
        $CanonicalActualHash = (Get-FileHash -LiteralPath $CanonicalPath -Algorithm SHA256).Hash
        $HashRows = @(
            [pscustomobject]@{
                Side = 'DOWNLOADS_CANDIDATE'; ExpectedSHA256 = $ExpectedCandidateHash; ActualSHA256 = $CandidateActualHash
                Match = $CandidateActualHash -ceq $ExpectedCandidateHash; Bytes = (Get-Item -LiteralPath $CandidatePath).Length; Path = $CandidatePath
            }
            [pscustomobject]@{
                Side = 'GIT_CANONICAL'; ExpectedSHA256 = $ExpectedCanonicalHash; ActualSHA256 = $CanonicalActualHash
                Match = $CanonicalActualHash -ceq $ExpectedCanonicalHash; Bytes = (Get-Item -LiteralPath $CanonicalPath).Length; Path = $CanonicalPath
            }
        )
        $SourceHashPass = $HashRows.Count -eq 2 -and @($HashRows | Where-Object Match -eq $false).Count -eq 0

        def_WriteProgress -Percent 32 -Status 'FLOW03 candidate opacity causality scan'
        $CandidateRows = @(def_GetOpacityLineRecords -Side 'DOWNLOADS_CANDIDATE' -Path $CandidatePath -Observed $ObservedFillOpacity -Required $RequiredFillOpacity)
        $RepairCandidate = def_GetRepairCandidate -Rows $CandidateRows
        $PatchProposal = def_NewPatchProposal -RepairCandidate $RepairCandidate -CandidateHash $CandidateActualHash `
            -ObservedOpacity $ObservedFillOpacity -RequiredOpacity $RequiredFillOpacity

        def_WriteProgress -Percent 47 -Status 'FLOW04 canonical visual-lock reference scan'
        $CanonicalRows = @(def_GetOpacityLineRecords -Side 'GIT_CANONICAL' -Path $CanonicalPath -Observed $ObservedFillOpacity -Required $RequiredFillOpacity)
        $CausalityRows = @(def_GetCausalityRows -SourceHashPass $SourceHashPass -RepairCandidate $RepairCandidate -PatchProposal $PatchProposal -CanonicalRows $CanonicalRows)

        def_WriteProgress -Percent 63 -Status 'FLOW05 construct append-only single-line patch proposal'
        $ContextText = if ($null -ne $RepairCandidate.Row) {
            def_GetContextText -Path $CandidatePath -LineNumber ([int]$RepairCandidate.Row.LineNumber) -Radius $ContextLineCount
        }
        else { 'No unique source line was admitted.' }
        $PatchText = def_GetPatchText -PatchProposal $PatchProposal -RelativePath $RelativeEnginePath -ContextText $ContextText

        if (-not $SourceHashPass) {
            $GateColor = 'RED'
            $Gate = 'UNIT03_VISUAL_LOCK_SOURCE_HASH_DRIFT_BLOCKED'
            $Decision = 'FAIL_CLOSED_REFRESH_EVIDENCE_NO_PATCH'
        }
        elseif (-not $PatchProposal.Ready) {
            $GateColor = 'RED'
            $Gate = 'UNIT03_VISUAL_LOCK_CAUSE_NOT_UNIQUE_BLOCKED'
            $Decision = 'FAIL_CLOSED_MANUAL_SOURCE_CAUSALITY_REVIEW'
        }
        else {
            $GateColor = 'YELLOW'
            $Gate = 'UNIT03_VISUAL_LOCK_REPAIR_PROPOSAL_READY_EXPLICIT_APPROVAL_REQUIRED'
            $Decision = 'PROPOSAL_ONLY_NO_SOURCE_MUTATION'
        }

        def_WriteProgress -Percent 78 -Status 'FLOW06 compute final fail-closed proposal gate'
        $LaneRows = @(
            def_NewLaneRow -Lane 'FLOW01_AUTHORITY' -Purpose 'Resolve v1.0.10 and v1.0.9 immutable evidence' -Status 'PASS' -Evidence $Source.Directory.FullName -GateImpact 'SOURCE_LOCKED'
            def_NewLaneRow -Lane 'FLOW02_HASH_STATE' -Purpose 'Lock candidate and canonical Python SHA256' -Status $(if ($SourceHashPass) { 'PASS' } else { 'BLOCK' }) -Evidence "Candidate=$CandidateActualHash;Canonical=$CanonicalActualHash" -GateImpact $(if ($SourceHashPass) { 'NONE' } else { 'RED' })
            def_NewLaneRow -Lane 'FLOW03_CANDIDATE_SCAN' -Purpose 'Locate the 0.40 opacity cause without import' -Status $(if ($null -ne $RepairCandidate.Row) { 'PASS' } else { 'BLOCK' }) -Evidence $RepairCandidate.Confidence -GateImpact $(if ($null -ne $RepairCandidate.Row) { 'NONE' } else { 'RED' })
            def_NewLaneRow -Lane 'FLOW04_CANONICAL_REFERENCE' -Purpose 'Confirm the 0.75 canonical reference' -Status 'PASS' -Evidence "CanonicalOutput=0.75;SourceRows=$($CanonicalRows.Count)" -GateImpact 'REFERENCE_ONLY'
            def_NewLaneRow -Lane 'FLOW05_PATCH_PROPOSAL' -Purpose 'Generate one hash-locked append-only patch proposal' -Status $(if ($PatchProposal.Ready) { 'PASS' } else { 'BLOCK' }) -Evidence "Line=$($PatchProposal.LineNumber);Replacements=$($PatchProposal.ReplacementCount)" -GateImpact $(if ($PatchProposal.Ready) { 'YELLOW_REVIEW' } else { 'RED' })
            def_NewLaneRow -Lane 'FLOW06_SEQUENCE_GATE' -Purpose 'Keep guarded repair test and write_workbench test sequential' -Status 'HOLD' -Evidence 'Visual repair test first; write_workbench targeted test second' -GateImpact 'NO_PROMOTION'
        )

        def_WriteProgress -Percent 90 -Status 'Write append-only JSON, CSV, patch, HTML, and log'
        $LaneCsvPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_SixLane_Repair_Proposal.csv'
        $HashCsvPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_Source_Hash_Lock.csv'
        $CandidateCsvPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_Candidate_Opacity_Scan.csv'
        $CanonicalCsvPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_Canonical_Opacity_Scan.csv'
        $CausalityCsvPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Causality.csv'
        $PatchPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Repair_Proposal.patch.txt'
        $JsonPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Repair_Proposal_Summary.json'
        $HtmlPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Repair_Proposal_Matrix.html'
        $LogPath = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Repair_Proposal.log'
        $LaneRows | Export-Csv -LiteralPath $LaneCsvPath -NoTypeInformation -Encoding utf8BOM
        $HashRows | Export-Csv -LiteralPath $HashCsvPath -NoTypeInformation -Encoding utf8BOM
        $CandidateRows | Export-Csv -LiteralPath $CandidateCsvPath -NoTypeInformation -Encoding utf8BOM
        $CanonicalRows | Export-Csv -LiteralPath $CanonicalCsvPath -NoTypeInformation -Encoding utf8BOM
        $CausalityRows | Export-Csv -LiteralPath $CausalityCsvPath -NoTypeInformation -Encoding utf8BOM
        def_WriteUtf8File -Path $PatchPath -Content $PatchText

        $Summary = [ordered]@{
            schema_version = 'VIA_CANONICAL_UNIT03_VAP_VISUAL_LOCK_REPAIR_PROPOSAL_1.0.11'
            generated_utc = (Get-Date).ToUniversalTime().ToString('o')
            method = $Script:Method
            policy = $Script:Policy
            source_v0110_run = $Source.Directory.FullName
            source_v0109_run = $Source.DynamicRun
            output_directory = $Script:OutputDir
            visual_lock = [ordered]@{
                observed_candidate_fill_opacity = $ObservedFillOpacity
                required_fill_opacity = $RequiredFillOpacity
                v0110_gate_confirmed = $RequiredAdjudicationGate
                regression_is_real = $true
            }
            gate = [ordered]@{
                color = $GateColor
                gate = $Gate
                decision = $Decision
                explicit_approval_required = $true
            }
            safety = [ordered]@{
                source_hash_pass = $SourceHashPass
                target_imports = 0
                candidate_executions = 0
                patched_candidates_created = 0
                source_copies = 0
                source_writes = 0
                network_allowed = $false
                database_or_ssot_write_allowed = $false
                canonical_mutations = 0
                promotions = 0
                rollbacks = 0
            }
            patch_proposal = $PatchProposal
            next_sequence = @(
                'EXPLICIT_APPROVAL_FOR_RUN_LOCAL_PATCHED_CANDIDATE_ONLY'
                'TWO_GUARDED_VISUAL_TRIALS_REQUIRE_FILL_OPACITY_0_75'
                'SEPARATE_WRITE_WORKBENCH_TARGETED_TEST'
                'POST_TEST_PROMOTION_PROPOSAL_REVIEW_ONLY'
            )
            lanes = $LaneRows
            source_hashes = $HashRows
            candidate_opacity_scan = $CandidateRows
            canonical_opacity_scan = $CanonicalRows
            causality = $CausalityRows
        }
        def_WriteUtf8File -Path $JsonPath -Content ($Summary | ConvertTo-Json -Depth 15)
        def_WriteHtmlReport -LaneRows $LaneRows -HashRows $HashRows -CandidateRows $CandidateRows -CanonicalRows $CanonicalRows `
            -CausalityRows $CausalityRows -PatchProposal $PatchProposal -GateColor $GateColor -Gate $Gate `
            -PatchPath $PatchPath -Path $HtmlPath
        def_WriteUtf8File -Path $LogPath -Content ($Script:LogRows -join [Environment]::NewLine)

        def_WriteProgress -Percent 100 -Status 'Visual-lock repair proposal complete'
        Write-Progress -Id 1110 -Activity 'VIA UNIT03 VAP visual-lock repair proposal' -Completed
        Write-Host ''
        Write-Host 'def VIA · UNIT03 VAP VISUAL-LOCK REPAIR PROPOSAL v1.0.11' -ForegroundColor Cyan
        Write-Host "def Gate                    : $GateColor / $Gate" -ForegroundColor $(if ($GateColor -eq 'RED') { 'Red' } else { 'Yellow' })
        Write-Host "def Source Hash Lock        : $(@($HashRows | Where-Object Match -eq $true).Count) / 2"
        Write-Host "def Cause Confidence        : $($RepairCandidate.Confidence)"
        Write-Host "def Repair Line             : $($PatchProposal.LineNumber)"
        Write-Host "def Original                : $($PatchProposal.OriginalLine)"
        Write-Host "def Proposed                : $($PatchProposal.ProposedLine)"
        Write-Host "def Replacement Count       : $($PatchProposal.ReplacementCount)"
        Write-Host 'def Candidate Executions    : 0'
        Write-Host 'def Patched Candidate       : 0'
        Write-Host 'def Source Mutation         : 0'
        Write-Host 'def Promotion               : 0'
        Write-Host "def Patch Proposal          : $PatchPath"
        Write-Host "def Report                  : $HtmlPath"
        Write-Host "def Summary                 : $JsonPath"
        Write-Host ''
        $LaneRows | Format-Table -AutoSize -Wrap
        if ($OpenReport) { Start-Process -FilePath $HtmlPath | Out-Null }
    }
    catch {
        def_WriteLog -Level 'FAIL' -Message "Unhandled repair-proposal error: $($_.Exception.Message)"
        if (-not [string]::IsNullOrWhiteSpace($Script:OutputDir) -and (Test-Path -LiteralPath $Script:OutputDir -PathType Container)) {
            $FailLog = Join-Path $Script:OutputDir 'VIA_UNIT03_VAP_VisualLock_Repair_Proposal_FAILED.log'
            try { def_WriteUtf8File -Path $FailLog -Content (($Script:LogRows -join [Environment]::NewLine) + [Environment]::NewLine + ($_ | Out-String)) } catch {}
        }
        Write-Progress -Id 1110 -Activity 'VIA UNIT03 VAP visual-lock repair proposal' -Completed
        throw
    }
}

def_Main

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
