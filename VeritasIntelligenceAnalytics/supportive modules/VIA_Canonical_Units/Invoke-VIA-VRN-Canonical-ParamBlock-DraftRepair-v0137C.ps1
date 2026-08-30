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
====================================================================================================
def VIA · VRN CANONICAL PARAMBLOCK DRAFT REPAIR · v0137C
====================================================================================================
Root cause
----------
Invoke-VRN.ps1 has a syntactically parseable `param(...)` command at runtime line 14,
but it is not the script ParamBlock because executable statements occur before it.
PowerShell therefore invokes `param(...)` as a command/method-style call and throws:

"The function or command was called as if it were a method."

Policy
------
- Verify the exact canonical SHA256 observed by v0137.
- Read only functional modules\VRN\Invoke-VRN.ps1.
- Locate exactly one CommandAst whose command name is `param`.
- Relocate that complete extent to the legal script-prolog position.
- Preserve #requires, comments, blank lines and using statements ahead of ParamBlock.
- Generate run-local snapshot, proposed draft, unified diff and HTML evidence.
- Validate:
    1. PowerShell AST has zero errors.
    2. ScriptBlockAst.ParamBlock is no longer null.
    3. The old command-style `param` CommandAst count becomes zero.
    4. Canonical file hash remains unchanged.
- Do NOT execute the proposed draft.
- Do NOT overwrite, rename, move or delete the canonical file.
- Do NOT restart VRN or VDF.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",

    [string]$ExpectedCanonicalSha256 = "6cce939718d9fe263f379df430c298080b4b30c91bbd0c3cdbf9ea5340bef85b",

    [bool]$OpenHtmlReport = $true,
    [bool]$KeepParentPowerShellOpen = $true,

    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0137C_DRAFT_ONLY_PARAMBLOCK_RELOCATION"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0137C_DRAFT_ONLY_PARAMBLOCK_RELOCATION"
$Version = "v0137C"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$CanonicalPath = Join-Path $BaseDir "functional modules\VRN\Invoke-VRN.ps1"
$RunDir = Join-Path $BaseDir "_via_vrn_canonical_draft_repair_runs\RUN_${Stamp}_VIA_VRN_PARAMBLOCK_DRAFT_REPAIR_v0137C"

$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$SandboxDir = Join-Path $RunDir "sandbox"
$DiffDir = Join-Path $RunDir "diff"

$OriginalSnapshot = Join-Path $SandboxDir "Invoke-VRN.v0137C.original.snapshot.ps1"
$ProposedDraft = Join-Path $SandboxDir "Invoke-VRN.v0137C.proposed.ps1"
$UnifiedDiff = Join-Path $DiffDir "Invoke-VRN.v0137C.paramblock.diff.txt"

$EvidenceJson = Join-Path $JsonDir "VRN_Canonical_ParamBlockRepairEvidence.v0137C.json"
$SummaryJson = Join-Path $JsonDir "summary.v0137C.json"
$ReportHtml = Join-Path $HtmlDir "VIA_VRN_Canonical_ParamBlock_DraftRepair_v0137C.html"

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

function Get-ParsedPowerShell {
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
            tokens = @($tokens)
            errors = @($errors)
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
            tokens = @()
            errors = @()
            parse_ok = $false
            error_count = 1
            first_error = $_.Exception.Message
        }
    }
}

function Get-CommandStyleParamNodes {
    param(
        [Parameter(Mandatory)]
        $Ast
    )

    if ($null -eq $Ast) {
        return @()
    }

    return @(
        $Ast.FindAll(
            {
                param($node)

                if (-not ($node -is [System.Management.Automation.Language.CommandAst])) {
                    return $false
                }

                $commandName = $node.GetCommandName()

                return (
                    -not [string]::IsNullOrWhiteSpace([string]$commandName) -and
                    [string]$commandName -ieq "param"
                )
            },
            $true
        )
    )
}

function Get-PrologInsertionLine {
    param(
        [Parameter(Mandatory)]
        [string[]]$Lines
    )

    $inBlockComment = $false
    $index = 0

    while ($index -lt $Lines.Count) {
        $line = [string]$Lines[$index]
        $trimmed = $line.Trim()

        if ($inBlockComment) {
            if ($trimmed -match '#>') {
                $inBlockComment = $false
            }

            $index++
            continue
        }

        if ($trimmed -eq "") {
            $index++
            continue
        }

        if ($trimmed -match '^<#') {
            if ($trimmed -notmatch '#>') {
                $inBlockComment = $true
            }

            $index++
            continue
        }

        if ($trimmed -match '^#') {
            $index++
            continue
        }

        if ($trimmed -match '^using\s+(assembly|module|namespace)\b') {
            $index++
            continue
        }

        break
    }

    return $index
}

function Normalize-Newlines {
    param(
        [Parameter(Mandatory)]
        [string]$Text
    )

    return ($Text -replace "`r`n", "`n" -replace "`r", "`n")
}

function New-RelocatedDraftText {
    param(
        [Parameter(Mandatory)]
        [string]$OriginalText,

        [Parameter(Mandatory)]
        $ParamCommandNode
    )

    $normalized = Normalize-Newlines -Text $OriginalText
    $startOffset = [int]$ParamCommandNode.Extent.StartOffset
    $endOffset = [int]$ParamCommandNode.Extent.EndOffset

    if (
        $startOffset -lt 0 -or
        $endOffset -le $startOffset -or
        $endOffset -gt $OriginalText.Length
    ) {
        throw "Param command extent is outside the canonical text."
    }

    # Extent offsets were calculated against the original text. Preserve the original
    # representation until removal, then normalize for deterministic draft output.
    $paramText = $OriginalText.Substring(
        $startOffset,
        $endOffset - $startOffset
    ).Trim()

    if ($paramText -notmatch '^(?is)param\s*\(') {
        throw "Located command extent does not begin with param(...)."
    }

    $before = $OriginalText.Substring(0, $startOffset)
    $after = $OriginalText.Substring($endOffset)

    # Remove surrounding blank-only lines left by the old param location.
    $withoutOldParam = $before + $after
    $withoutOldParamNormalized = Normalize-Newlines -Text $withoutOldParam
    $lines = @($withoutOldParamNormalized -split "`n", -1)

    $insertionIndex = Get-PrologInsertionLine -Lines $lines

    # PowerShell enumerates output from an if-expression during assignment.
    # Keep both variables explicitly typed so one-element slices remain arrays.
    [string[]]$leading = @()
    [string[]]$trailing = @()
    $lineCount = @($lines).Count

    if ($insertionIndex -gt 0) {
        $leading = [string[]]@(
            $lines[0..($insertionIndex - 1)]
        )
    }

    if ($insertionIndex -lt $lineCount) {
        $trailing = [string[]]@(
            $lines[$insertionIndex..($lineCount - 1)]
        )
    }

    while (@($leading).Count -gt 0) {
        $leadingCount = @($leading).Count
        $lastLeading = [string]$leading[$leadingCount - 1]

        if (-not [string]::IsNullOrWhiteSpace($lastLeading)) {
            break
        }

        if ($leadingCount -eq 1) {
            $leading = [string[]]@()
        }
        else {
            $leading = [string[]]@(
                $leading[0..($leadingCount - 2)]
            )
        }
    }

    while (@($trailing).Count -gt 0) {
        $trailingCount = @($trailing).Count
        $firstTrailing = [string]$trailing[0]

        if (-not [string]::IsNullOrWhiteSpace($firstTrailing)) {
            break
        }

        if ($trailingCount -eq 1) {
            $trailing = [string[]]@()
        }
        else {
            $trailing = [string[]]@(
                $trailing[1..($trailingCount - 1)]
            )
        }
    }

    $resultLines = @()

    if (@($leading).Count -gt 0) {
        $resultLines += $leading
        $resultLines += ""
    }

    $resultLines += @($paramText -split "`r?`n")
    $resultLines += ""

    if (@($trailing).Count -gt 0) {
        $resultLines += $trailing
    }

    $result = ($resultLines -join "`r`n").TrimEnd() + "`r`n"

    return [pscustomobject]@{
        text = $result
        param_text = $paramText
        insertion_line = @($leading).Count + $(if (@($leading).Count -gt 0) { 2 } else { 1 })
        original_start_line = [int]$ParamCommandNode.Extent.StartLineNumber
        original_end_line = [int]$ParamCommandNode.Extent.EndLineNumber
    }
}

function Get-ContextLines {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [int]$CenterLine,

        [int]$Radius = 5
    )

    $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    $start = [Math]::Max(1, $CenterLine - $Radius)
    $end = [Math]::Min($lines.Count, $CenterLine + $Radius)
    $rows = @()

    for ($lineNumber = $start; $lineNumber -le $end; $lineNumber++) {
        $rows += [pscustomobject]@{
            line = $lineNumber
            text = [string]$lines[$lineNumber - 1]
        }
    }

    return @($rows)
}

function New-SimpleUnifiedDiff {
    param(
        [Parameter(Mandatory)]
        [string]$OriginalPath,

        [Parameter(Mandatory)]
        [string]$ProposedPath,

        [Parameter(Mandatory)]
        [int]$OriginalParamStartLine,

        [Parameter(Mandatory)]
        [int]$ProposedParamStartLine
    )

    $originalContext = Get-ContextLines `
        -Path $OriginalPath `
        -CenterLine $OriginalParamStartLine `
        -Radius 7

    $proposedContext = Get-ContextLines `
        -Path $ProposedPath `
        -CenterLine $ProposedParamStartLine `
        -Radius 7

    $builder = New-Object System.Text.StringBuilder

    [void]$builder.AppendLine("--- canonical/Invoke-VRN.ps1")
    [void]$builder.AppendLine("+++ proposed/Invoke-VRN.v0137C.proposed.ps1")
    [void]$builder.AppendLine("")
    [void]$builder.AppendLine("@@ ORIGINAL PARAM LOCATION @@")

    foreach ($row in $originalContext) {
        [void]$builder.AppendLine(
            ("- {0,4}: {1}" -f $row.line, $row.text)
        )
    }

    [void]$builder.AppendLine("")
    [void]$builder.AppendLine("@@ PROPOSED SCRIPT PROLOG @@")

    foreach ($row in $proposedContext) {
        [void]$builder.AppendLine(
            ("+ {0,4}: {1}" -f $row.line, $row.text)
        )
    }

    return $builder.ToString()
}

function ConvertTo-HtmlEncoded {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function ConvertTo-SafeHtmlTable {
    param($Rows)

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
        $Evidence,

        [Parameter(Mandatory)]
        $OriginalContext,

        [Parameter(Mandatory)]
        $ProposedContext,

        [Parameter(Mandatory)]
        [string]$DiffText
    )

    $gateClass = if ($Summary.gate -eq "DRAFT_PARAMBLOCK_REPAIR_READY_FOR_REVIEW") {
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
td{padding:5px 6px;border:1px solid #e2eae8;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:520px}
tr:nth-child(even){background:#fbfcfb}
.code{font-family:Consolas,"Cascadia Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.empty{padding:14px;color:#63706d}
</style>
'@

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA VRN ParamBlock Draft Repair v0137C</title>
$css
</head>
<body>
<h1>VIA · VRN Canonical ParamBlock Draft Repair · v0137C</h1>

<div class="card">
<div class="grid">
<div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(ConvertTo-HtmlEncoded -Value $Summary.gate)</div></div>
<div class="metric"><div class="k">Canonical Mutated</div><div class="v">NO</div></div>
<div class="metric"><div class="k">Canonical Hash Stable</div><div class="v">$($Summary.canonical_hash_stable)</div></div>
<div class="metric"><div class="k">Original Param Line</div><div class="v">$($Summary.original_param_line)</div></div>
<div class="metric"><div class="k">Proposed Param Line</div><div class="v">$($Summary.proposed_param_line)</div></div>
<div class="metric"><div class="k">Draft AST</div><div class="v">$($Summary.draft_ast)</div></div>
<div class="metric"><div class="k">Draft ParamBlock</div><div class="v">$($Summary.draft_paramblock_present)</div></div>
<div class="metric"><div class="k">Draft Command-Param Count</div><div class="v">$($Summary.draft_command_param_count)</div></div>
</div>
</div>

<h2>Decision</h2>
<div class="card code">$(ConvertTo-HtmlEncoded -Value $Summary.decision)

Next: $(ConvertTo-HtmlEncoded -Value $Summary.next_step)</div>

<h2>Repair Evidence</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows @($Evidence))</div>

<h2>Original Context</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows $OriginalContext)</div>

<h2>Proposed Context</h2>
<div class="card">$(ConvertTo-SafeHtmlTable -Rows $ProposedContext)</div>

<h2>Diff</h2>
<div class="card code">$(ConvertTo-HtmlEncoded -Value $DiffText)</div>

<h2>Output Paths</h2>
<div class="card code">
Canonical: $(ConvertTo-HtmlEncoded -Value $CanonicalPath)
Original snapshot: $(ConvertTo-HtmlEncoded -Value $OriginalSnapshot)
Proposed draft: $(ConvertTo-HtmlEncoded -Value $ProposedDraft)
Diff: $(ConvertTo-HtmlEncoded -Value $UnifiedDiff)
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
        $JsonDir,
        $HtmlDir,
        $SandboxDir,
        $DiffDir
    )) {
        Ensure-Directory -Path $directory
    }

    Write-Host "def [BOOT] v0137C ParamBlock draft repair started." -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $CanonicalPath)) {
        throw "Canonical Invoke-VRN.ps1 is missing."
    }

    $canonicalHashBefore = (
        Get-FileHash -LiteralPath $CanonicalPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    Write-Host ("def [HASH] Canonical SHA256: {0}" -f $canonicalHashBefore) -ForegroundColor DarkGray

    if ($canonicalHashBefore -ne $ExpectedCanonicalSha256.ToLowerInvariant()) {
        throw "Canonical hash drift detected. Expected=$ExpectedCanonicalSha256 Actual=$canonicalHashBefore"
    }

    Copy-Item `
        -LiteralPath $CanonicalPath `
        -Destination $OriginalSnapshot `
        -Force

    $originalParse = Get-ParsedPowerShell -Path $CanonicalPath

    if (-not $originalParse.parse_ok) {
        throw "Canonical AST is not clean: $($originalParse.first_error)"
    }

    $originalParamBlockPresent = ($null -ne $originalParse.ast.ParamBlock)
    [object[]]$paramCommandNodes = @(
        Get-CommandStyleParamNodes -Ast $originalParse.ast
    )
    [int]$paramCommandNodeCount = @($paramCommandNodes).Count

    Write-Host ("def [DIAGNOSIS] Ast.ParamBlock present: {0}" -f $originalParamBlockPresent) -ForegroundColor Yellow
    Write-Host ("def [DIAGNOSIS] command-style param nodes: {0}" -f $paramCommandNodeCount) -ForegroundColor Yellow

    if ($originalParamBlockPresent) {
        throw "Canonical already has a legal Ast.ParamBlock; no relocation is necessary."
    }

    if ($paramCommandNodeCount -ne 1) {
        throw "Expected exactly one command-style param node; found $paramCommandNodeCount."
    }

    $canonicalText = Get-Content -LiteralPath $CanonicalPath -Raw -Encoding UTF8
    $relocation = New-RelocatedDraftText `
        -OriginalText $canonicalText `
        -ParamCommandNode $paramCommandNodes[0]

    Set-Content `
        -LiteralPath $ProposedDraft `
        -Value $relocation.text `
        -Encoding UTF8

    $draftParse = Get-ParsedPowerShell -Path $ProposedDraft
    $draftParamBlockPresent = (
        $draftParse.parse_ok -and
        $null -ne $draftParse.ast.ParamBlock
    )

    [object[]]$draftCommandParamNodes = @()

    if ($draftParse.parse_ok) {
        $draftCommandParamNodes = [object[]]@(
            Get-CommandStyleParamNodes -Ast $draftParse.ast
        )
    }

    [int]$draftCommandParamNodeCount = @($draftCommandParamNodes).Count

    $canonicalHashAfter = (
        Get-FileHash -LiteralPath $CanonicalPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    $canonicalHashStable = ($canonicalHashAfter -eq $canonicalHashBefore)
    $draftHash = (
        Get-FileHash -LiteralPath $ProposedDraft -Algorithm SHA256
    ).Hash.ToLowerInvariant()

    $allDraftChecksPass = (
        $draftParse.parse_ok -and
        $draftParamBlockPresent -and
        $draftCommandParamNodeCount -eq 0 -and
        $canonicalHashStable
    )

    $originalContext = Get-ContextLines `
        -Path $OriginalSnapshot `
        -CenterLine $relocation.original_start_line `
        -Radius 7

    $proposedContext = Get-ContextLines `
        -Path $ProposedDraft `
        -CenterLine $relocation.insertion_line `
        -Radius 7

    $diffText = New-SimpleUnifiedDiff `
        -OriginalPath $OriginalSnapshot `
        -ProposedPath $ProposedDraft `
        -OriginalParamStartLine $relocation.original_start_line `
        -ProposedParamStartLine $relocation.insertion_line

    Set-Content `
        -LiteralPath $UnifiedDiff `
        -Value $diffText `
        -Encoding UTF8

    Write-Host ("def [DRAFT] AST={0}; ParamBlock={1}; CommandParamCount={2}" -f `
        $draftParse.parse_ok,
        $draftParamBlockPresent,
        $draftCommandParamNodeCount
    ) -ForegroundColor Cyan

    $evidence = [pscustomobject]@{
        version = $Version
        canonical_path = $CanonicalPath
        canonical_sha256_before = $canonicalHashBefore
        canonical_sha256_after = $canonicalHashAfter
        canonical_hash_stable = $canonicalHashStable
        canonical_mutated = $false

        original_parse_ok = $originalParse.parse_ok
        original_ast_paramblock_present = $originalParamBlockPresent
        original_command_param_count = $paramCommandNodeCount
        original_param_start_line = $relocation.original_start_line
        original_param_end_line = $relocation.original_end_line

        proposed_path = $ProposedDraft
        proposed_sha256 = $draftHash
        proposed_parse_ok = $draftParse.parse_ok
        proposed_first_error = $draftParse.first_error
        proposed_ast_paramblock_present = $draftParamBlockPresent
        proposed_command_param_count = $draftCommandParamNodeCount
        proposed_param_start_line = $relocation.insertion_line

        draft_executed = $false
        promotion_executed = $false
        all_draft_checks_pass = $allDraftChecksPass
    }

    Write-JsonFile -Data $evidence -Path $EvidenceJson

    $gate = "DRAFT_PARAMBLOCK_REPAIR_REVIEW_REQUIRED"
    $risk = "MEDIUM_REVIEW"
    $decision = "A ParamBlock relocation draft was generated, but one or more structural checks failed."
    $nextStep = "Review evidence. Keep v0136A fallback authoritative."

    if ($allDraftChecksPass) {
        $gate = "DRAFT_PARAMBLOCK_REPAIR_READY_FOR_REVIEW"
        $risk = "LOW_DRAFT_ONLY"
        $decision = "The unique command-style param extent was relocated to the legal script prolog. The draft has a real Ast.ParamBlock, zero command-style param nodes and a clean PowerShell AST. Canonical remains unchanged."
        $nextStep = "Review the diff, then use a separate original-hash → backup → promote gate. Do not directly copy the draft."
    }

    $summary = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        gate = $gate
        risk = $risk
        decision = $decision
        next_step = $nextStep

        canonical_path = $CanonicalPath
        canonical_sha256 = $canonicalHashBefore
        canonical_hash_stable = $canonicalHashStable
        canonical_mutated = $false

        original_param_line = $relocation.original_start_line
        proposed_param_line = $relocation.insertion_line

        draft_path = $ProposedDraft
        draft_sha256 = $draftHash
        draft_ast = if ($draftParse.parse_ok) {
            "GREEN_POWERSHELL_AST_PASS"
        }
        else {
            "FAIL: $($draftParse.first_error)"
        }
        draft_paramblock_present = $draftParamBlockPresent
        draft_command_param_count = $draftCommandParamNodeCount
        draft_executed = $false
        promotion_executed = $false

        run_dir = $RunDir
        diff = $UnifiedDiff
        html = $ReportHtml
    }

    Write-JsonFile -Data $summary -Path $SummaryJson

    Write-HtmlReport `
        -Summary ([pscustomobject]$summary) `
        -Evidence $evidence `
        -OriginalContext $originalContext `
        -ProposedContext $proposedContext `
        -DiffText $diffText

    if ($OpenHtmlReport) {
        Start-Process -FilePath $ReportHtml
    }

    Write-Host ""
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
    Write-Host "def VIA · v0137C FINAL RESULT" -ForegroundColor Cyan
    Write-Host ("def Gate                    : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                    : {0}" -f $summary.risk) -ForegroundColor Yellow
    Write-Host "def CanonicalMutated        : False" -ForegroundColor Green
    Write-Host ("def CanonicalHashStable     : {0}" -f $summary.canonical_hash_stable) -ForegroundColor Green
    Write-Host ("def OriginalParamLine       : {0}" -f $summary.original_param_line) -ForegroundColor White
    Write-Host ("def ProposedParamLine       : {0}" -f $summary.proposed_param_line) -ForegroundColor White
    Write-Host ("def DraftAST                : {0}" -f $summary.draft_ast) -ForegroundColor Green
    Write-Host ("def DraftParamBlockPresent  : {0}" -f $summary.draft_paramblock_present) -ForegroundColor Green
    Write-Host ("def DraftCommandParamCount  : {0}" -f $summary.draft_command_param_count) -ForegroundColor Green
    Write-Host "def DraftExecuted           : False" -ForegroundColor Yellow
    Write-Host "def PromotionExecuted       : False" -ForegroundColor Yellow
    Write-Host ("def DraftPath               : {0}" -f $summary.draft_path) -ForegroundColor Cyan
    Write-Host ("def Diff                    : {0}" -f $summary.diff) -ForegroundColor Cyan
    Write-Host ("def RunDir                  : {0}" -f $summary.run_dir) -ForegroundColor Cyan
    Write-Host ("def HTML                    : {0}" -f $summary.html) -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "def VIA · v0137C OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def Canonical Invoke-VRN.ps1 was not modified or executed." -ForegroundColor Yellow
}
finally {
    if ($KeepParentPowerShellOpen) {
        Write-Host ""
        Write-Host "def Parent PowerShell remains open. v0136A fallback remains authoritative." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
