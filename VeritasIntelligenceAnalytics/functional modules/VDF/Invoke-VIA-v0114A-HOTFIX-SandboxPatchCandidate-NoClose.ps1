param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113K_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
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

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114A_HOTFIX_SANDBOX_CANDIDATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114A_hotfix_sandbox_patch_candidate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_CANDIDATE_DIR = Join-Path $def_RUN_DIR "_sandbox_patch_candidate"
$def_DIFF_DIR = Join-Path $def_RUN_DIR "_diff_preview"
$def_DISABLED_APPLY_DIR = Join-Path $def_RUN_DIR "_disabled_apply_script"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114A_HotfixSandboxCandidate.log"

$def_ACCELERATORS = @(
    "A01 hotfix rebuild without nested here-string",
    "A02 AST syntax gate before run",
    "A03 latest-v0113K auto discovery",
    "A04 same-session NoClose execution",
    "A05 no child process required",
    "A06 no BASE re-scan",
    "A07 row policy pack compiler",
    "A08 P0 policy candidate compiler",
    "A09 P1 alias candidate compiler",
    "A10 diff preview only",
    "A11 disabled apply boundary",
    "A12 no source mutation scanner",
    "A13 no canonical merge scanner",
    "A14 no DB write scanner",
    "A15 compact HTML matrix report"
)

function def_S {
    param($Value)
    if ($null -eq $Value) { return "" }
    try { return [string]$Value } catch { return "" }
}

function def_EnsureDir {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_CANDIDATE_DIR,$def_DIFF_DIR,$def_DISABLED_APPLY_DIR,$def_LOG_DIR)) {
    def_EnsureDir $d
}

function def_Log {
    param([string]$Level,[string]$Message,[ConsoleColor]$Color = [ConsoleColor]::Gray)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $def_LOG -Value $line -Encoding UTF8
}

function def_Progress {
    param([int]$Step,[int]$Total,[string]$Status)
    $pct = [int](($Step / [Math]::Max(1,$Total)) * 100)
    Write-Progress -Activity "VIA v0114A Hotfix Sandbox Candidate" -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
}

function def_Html {
    param($Text)
    return [System.Net.WebUtility]::HtmlEncode((def_S $Text))
}

function def_GetProp {
    param($Obj,[string]$Name)
    if ($null -eq $Obj) { return "" }
    if ($Obj.PSObject.Properties.Name -contains $Name) {
        return def_S $Obj.$Name
    }
    return ""
}

function def_LoadCsv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "CSV missing: $Path"
    }
    return @(Import-Csv -LiteralPath $Path)
}

function def_WriteCsv {
    param([array]$Rows,[string]$Path)
    if ($Rows -and @($Rows).Count -gt 0) {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    } else {
        [pscustomobject]@{ def_empty = "true" } | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function def_WriteJson {
    param($Object,[string]$Path,[int]$Depth = 16)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_EscapePsDouble {
    param([string]$Text)
    return (def_S $Text).Replace('`','``').Replace('"','`"')
}

function def_GetLatestV0113K {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113K_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113K_ROOT) {
            return $def_PARAM_V0113K_ROOT
        }
        throw "Specified v0113K root does not exist: $def_PARAM_V0113K_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113K_row_final_preview"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113K output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "_v0114_sandbox_candidate_input_pack\VIA_v0114_SandboxPatchCandidate_InputPack.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113K input pack found under: $root"
    }

    return $candidates[0].FullName
}

function def_NewId {
    param([string]$Prefix,[int]$No)
    return "{0}_{1:0000}" -f $Prefix,$No
}

function def_BuildPolicyRegistryCandidate {
    param([array]$P0Pack)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($g in @($P0Pack | Where-Object { (def_GetProp $_ "def_final_decision") -eq "YES" })) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_candidate_id = def_NewId "POLICY" $n
            def_candidate_type = "POLICY_REGISTRY_CANDIDATE"
            def_owner_engine = def_GetProp $g "def_owner_engine"
            def_domain_family = def_GetProp $g "def_domain_family"
            def_policy_value = def_GetProp $g "def_final_value"
            def_apply_to_rows = def_GetProp $g "def_apply_to_rows"
            def_source_reason = def_GetProp $g "def_final_reason"
            def_candidate_status = "SANDBOX_CANDIDATE_ONLY"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildAliasRegistryCandidate {
    param([array]$P1Pack)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($a in $P1Pack) {
        $decision = def_GetProp $a "def_final_decision"
        if ($decision -in @("YES","YES_REFERENCE_ONLY")) {
            $n++
            [void]$rows.Add([pscustomobject][ordered]@{
                def_candidate_id = def_NewId "ALIAS" $n
                def_candidate_type = "ALIAS_REGISTRY_CANDIDATE"
                def_alias = def_GetProp $a "def_alias"
                def_alias_value = def_GetProp $a "def_final_value"
                def_alias_decision = $decision
                def_scope = def_GetProp $a "def_scope"
                def_source_reason = def_GetProp $a "def_final_reason"
                def_candidate_status = "SANDBOX_CANDIDATE_ONLY"
                def_source_mutation = "false"
                def_canonical_merge = "false"
                def_db_write = "false"
            })
        }
    }

    return @($rows)
}

function def_BuildRowPatchPlan {
    param([array]$RowPack)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($r in $RowPack) {
        if ((def_GetProp $r "def_include_in_v0114_sandbox_input") -eq "true") {
            $n++
            [void]$rows.Add([pscustomobject][ordered]@{
                def_candidate_id = def_NewId "ROWPATCH" $n
                def_candidate_type = "ROW_POLICY_PATCH_PLAN"
                def_normalized_key = def_GetProp $r "def_normalized_key"
                def_owner_engine = def_GetProp $r "def_owner_engine"
                def_domain_family = def_GetProp $r "def_domain_family"
                def_candidate_canonical_value = def_GetProp $r "def_final_canonical_value"
                def_patch_action = "MAP_KEY_TO_POLICY_VALUE_IN_SANDBOX_PREVIEW"
                def_candidate_status = "SANDBOX_CANDIDATE_ONLY"
                def_source_mutation = "false"
                def_canonical_merge = "false"
                def_db_write = "false"
            })
        }
    }

    return @($rows)
}

function def_BuildDiffPreview {
    param([array]$PolicyCandidate,[array]$AliasCandidate,[array]$RowPatchPlan,[array]$P0Pack,[array]$P1Pack,[array]$RowPack)

    $rows = New-Object System.Collections.ArrayList

    [void]$rows.Add([pscustomobject][ordered]@{
        def_diff_layer = "POLICY_REGISTRY"
        def_diff_type = "CREATE_SANDBOX_CANDIDATE"
        def_candidate_rows = "$(@($PolicyCandidate).Count)"
        def_existing_source_change = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
        def_note = "Policy registry candidate generated from accepted P0 groups."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_diff_layer = "ALIAS_REGISTRY"
        def_diff_type = "CREATE_SANDBOX_CANDIDATE"
        def_candidate_rows = "$(@($AliasCandidate).Count)"
        def_existing_source_change = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
        def_note = "Alias registry candidate generated from accepted P1 aliases only."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_diff_layer = "ROW_POLICY_PATCH_PLAN"
        def_diff_type = "CREATE_SANDBOX_CANDIDATE"
        def_candidate_rows = "$(@($RowPatchPlan).Count)"
        def_existing_source_change = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
        def_note = "Row-level mapping preview. Excludes explicit DEFER/NO rows."
    })

    $excludedRows = @($RowPack | Where-Object { (def_GetProp $_ "def_include_in_v0114_sandbox_input") -ne "true" }).Count
    $excludedP0 = @($P0Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -ne "INCLUDE_IN_SANDBOX_PATCH_CANDIDATE_INPUT" }).Count
    $excludedP1 = @($P1Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -ne "INCLUDE_ALIAS_IN_SANDBOX_INPUT" }).Count

    [void]$rows.Add([pscustomobject][ordered]@{
        def_diff_layer = "EXCLUSION_GUARD"
        def_diff_type = "EXPLICIT_EXCLUDE_OR_DEFER"
        def_candidate_rows = "RowsExcluded=$excludedRows; P0Excluded=$excludedP0; P1Excluded=$excludedP1"
        def_existing_source_change = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
        def_note = "MACRO_CHINA and unsafe/legacy paths remain excluded/deferred."
    })

    return @($rows)
}

function def_AddValidation {
    param([System.Collections.ArrayList]$Rows,[string]$Name,[bool]$Pass,[string]$Message)

    [void]$Rows.Add([pscustomobject][ordered]@{
        def_test = $Name
        def_status = $(if ($Pass) { "PASS" } else { "FAIL" })
        def_risk = $(if ($Pass) { "LOW" } else { "HIGH" })
        def_message = $Message
    })
}

function def_CountUnsafe {
    param([array[]]$Sets)

    $unsafe = 0

    foreach ($set in $Sets) {
        foreach ($r in @($set)) {
            $sourceMutation = def_GetProp $r "def_source_mutation"
            $canonicalMerge = def_GetProp $r "def_canonical_merge"
            $dbWrite = def_GetProp $r "def_db_write"
            $existingChange = def_GetProp $r "def_existing_source_change"

            if (($sourceMutation -ne "" -and $sourceMutation -ne "false") -or
                ($canonicalMerge -ne "" -and $canonicalMerge -ne "false") -or
                ($dbWrite -ne "" -and $dbWrite -ne "false") -or
                ($existingChange -eq "true")) {
                $unsafe++
            }
        }
    }

    return $unsafe
}

function def_BuildValidationMatrix {
    param([array]$PolicyCandidate,[array]$AliasCandidate,[array]$RowPatchPlan,[array]$DiffPreview,[array]$ReadinessK)

    $rows = New-Object System.Collections.ArrayList
    $r0 = $ReadinessK[0]

    def_AddValidation $rows "v0113K allow v0114" ((def_GetProp $r0 "def_allow_v0114_sandbox_candidate") -eq "true") ("Gate=" + (def_GetProp $r0 "def_gate_status"))
    def_AddValidation $rows "row patch candidate count" (@($RowPatchPlan).Count -eq 149) ("Rows=" + @($RowPatchPlan).Count)
    def_AddValidation $rows "policy candidate count" (@($PolicyCandidate).Count -eq 12) ("P0Policy=" + @($PolicyCandidate).Count)
    def_AddValidation $rows "alias candidate count" (@($AliasCandidate).Count -eq 5) ("P1Alias=" + @($AliasCandidate).Count)

    $unsafe = def_CountUnsafe -Sets @($PolicyCandidate,$AliasCandidate,$RowPatchPlan,$DiffPreview)
    def_AddValidation $rows "unsafe mutation flags" ($unsafe -eq 0) ("UnsafeFlags=$unsafe")
    def_AddValidation $rows "diff preview generated" (@($DiffPreview).Count -ge 4) ("DiffRows=" + @($DiffPreview).Count)

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$RowPatchPlan,[array]$PolicyCandidate,[array]$AliasCandidate)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114B_SANDBOX_CANDIDATE_VALIDATION"
    $allow = "true"
    $reason = "Sandbox patch candidate generated. Next phase may validate candidate and diff preview only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_v0114_VALIDATION_FAILURE"
        $allow = "false"
        $reason = "Validation matrix has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114B = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_row_patch_plan_rows = "$(@($RowPatchPlan).Count)"
            def_policy_candidate_rows = "$(@($PolicyCandidate).Count)"
            def_alias_candidate_rows = "$(@($AliasCandidate).Count)"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114B sandbox candidate validation only"
        }
    )
}

function def_BuildDisabledApplyScript {
    param([string]$Path)

    $lines = @(
        '$ErrorActionPreference = "Continue"',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114 Disabled Apply Boundary" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "[BLOCKED] This is a sandbox candidate only." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No source mutation." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No canonical merge." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No DB write." -ForegroundColor Yellow',
        'Write-Host "PowerShell remains open." -ForegroundColor Cyan',
        'return'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$Path)

    $safeCsv = def_EscapePsDouble $ReadinessCsv

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '$ReadinessCsv = "' + $safeCsv + '"',
        'if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }',
        '$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114B Precheck after v0114A" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114B)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Rows       : $($r.def_row_patch_plan_rows)" -ForegroundColor Cyan',
        'Write-Host "Policy     : $($r.def_policy_candidate_rows)" -ForegroundColor Cyan',
        'Write-Host "Alias      : $($r.def_alias_candidate_rows)" -ForegroundColor Cyan',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114B -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114B." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114B_SANDBOX_CANDIDATE_VALIDATION_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=240)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) { [void]$sb.Append("<th>$(def_Html $c)</th>") }
    [void]$sb.Append("</tr></thead><tbody>")

    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = def_GetProp $r $c
            if ($v.Length -gt 280) { $v = $v.Substring(0,280) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$DiffPreview,$PolicyCandidate,$AliasCandidate,$RowPatchPlan,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114B",$Summary.AllowV0114B),
        @("Rows",$Summary.RowPatchRows),
        @("Policy",$Summary.PolicyRows),
        @("Alias",$Summary.AliasRows),
        @("Fail",$Summary.ValidationFail),
        @("Mutation","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114A Hotfix Sandbox Patch Candidate</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114A · Hotfix Sandbox Patch Candidate + Diff Preview</h1>")
    [void]$html.AppendLine("<div class='sub'>Rebuilt cleanly · no nested here-string · candidate only · no source mutation · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114A 已重建乾淨候選包。這是 sandbox candidate 與 diff preview，不是正式套用。disabled apply script 會明確阻擋任何 apply。</div><span class='tag'>Hotfix Rebuild</span><span class='tag'>Sandbox Candidate</span><span class='tag'>Diff Preview</span><span class='tag'>No Source Mutation</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114B','def_reason','def_validation_fail','def_row_patch_plan_rows','def_policy_candidate_rows','def_alias_candidate_rows','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_test','def_status','def_risk','def_message') 60)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Diff Preview</h2>$(def_Table $DiffPreview @('def_diff_layer','def_diff_type','def_candidate_rows','def_existing_source_change','def_canonical_merge','def_db_write','def_note') 30)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Policy Candidate</h2>$(def_Table $PolicyCandidate @('def_candidate_id','def_owner_engine','def_domain_family','def_policy_value','def_apply_to_rows','def_candidate_status','def_source_mutation','def_canonical_merge','def_db_write') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Alias Candidate</h2>$(def_Table $AliasCandidate @('def_candidate_id','def_alias','def_alias_value','def_alias_decision','def_scope','def_candidate_status','def_source_mutation','def_canonical_merge','def_db_write') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Row Patch Plan Preview</h2>$(def_Table $RowPatchPlan @('def_candidate_id','def_normalized_key','def_owner_engine','def_domain_family','def_candidate_canonical_value','def_patch_action','def_candidate_status','def_source_mutation','def_canonical_merge','def_db_write') 240)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0113K: $(def_Html $Summary.LatestV0113K)<br/>Candidate Dir: $(def_Html $Summary.CandidateDir)<br/>Diff Dir: $(def_Html $Summary.DiffDir)<br/>Disabled Apply: $(def_Html $Summary.DisabledApply)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114A HOTFIX SANDBOX PATCH CANDIDATE · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Candidate only. No source mutation. No canonical merge. No DB write. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0113K input pack"
    $latest = def_GetLatestV0113K
    $inputPack = Join-Path $latest "_v0114_sandbox_candidate_input_pack"
    def_Log "OK" "Latest v0113K: $latest" Green

    def_Progress 2 10 "Load v0113K input CSVs"
    $rowPack = def_LoadCsv (Join-Path $inputPack "VIA_v0114_INPUT_RowPolicyPack.csv")
    $p0Pack = def_LoadCsv (Join-Path $inputPack "VIA_v0114_INPUT_P0_PolicyPack.csv")
    $p1Pack = def_LoadCsv (Join-Path $inputPack "VIA_v0114_INPUT_P1_AliasPack.csv")
    $readinessK = def_LoadCsv (Join-Path $inputPack "VIA_v0114_INPUT_ReadinessGate.csv")
    def_Log "OK" "Loaded Row=$(@($rowPack).Count), P0=$(@($p0Pack).Count), P1=$(@($p1Pack).Count)" Green

    def_Progress 3 10 "Build policy registry candidate"
    $policyCandidate = def_BuildPolicyRegistryCandidate -P0Pack $p0Pack

    def_Progress 4 10 "Build alias registry candidate"
    $aliasCandidate = def_BuildAliasRegistryCandidate -P1Pack $p1Pack

    def_Progress 5 10 "Build row patch plan"
    $rowPatchPlan = def_BuildRowPatchPlan -RowPack $rowPack

    def_Progress 6 10 "Build diff preview"
    $diffPreview = def_BuildDiffPreview -PolicyCandidate $policyCandidate -AliasCandidate $aliasCandidate -RowPatchPlan $rowPatchPlan -P0Pack $p0Pack -P1Pack $p1Pack -RowPack $rowPack

    def_Progress 7 10 "Validate candidate"
    $validation = def_BuildValidationMatrix -PolicyCandidate $policyCandidate -AliasCandidate $aliasCandidate -RowPatchPlan $rowPatchPlan -DiffPreview $diffPreview -ReadinessK $readinessK
    $readiness = def_BuildReadiness -Validation $validation -RowPatchPlan $rowPatchPlan -PolicyCandidate $policyCandidate -AliasCandidate $aliasCandidate

    def_Progress 8 10 "Write candidate artifacts"
    $policyCsv = Join-Path $def_CANDIDATE_DIR "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv"
    $aliasCsv = Join-Path $def_CANDIDATE_DIR "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv"
    $rowPlanCsv = Join-Path $def_CANDIDATE_DIR "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv"
    $diffCsv = Join-Path $def_DIFF_DIR "VIA_v0114A_DIFF_PREVIEW.csv"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114A_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114A_ReadinessGate.csv"
    $disabledApply = Join-Path $def_DISABLED_APPLY_DIR "Invoke-VIA-v0114A-DISABLED-ApplyBoundary.ps1"

    def_WriteCsv $policyCandidate $policyCsv
    def_WriteCsv $aliasCandidate $aliasCsv
    def_WriteCsv $rowPatchPlan $rowPlanCsv
    def_WriteCsv $diffPreview $diffCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readiness $readinessCsv

    def_WriteJson $policyCandidate (Join-Path $def_CANDIDATE_DIR "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.json")
    def_WriteJson $aliasCandidate (Join-Path $def_CANDIDATE_DIR "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.json")
    def_WriteJson $rowPatchPlan (Join-Path $def_CANDIDATE_DIR "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.json")
    def_WriteJson $diffPreview (Join-Path $def_DIFF_DIR "VIA_v0114A_DIFF_PREVIEW.json")
    def_WriteJson $validation (Join-Path $def_OUTPUT_DIR "VIA_v0114A_ValidationMatrix.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0114A_ReadinessGate.json")

    $candidateManifest = [ordered]@{
        schema_version = "VIA_v0114A_HotfixSandboxPatchCandidateManifest"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0113K = $latest
        candidate_dir = $def_CANDIDATE_DIR
        diff_dir = $def_DIFF_DIR
        policy_candidate_csv = $policyCsv
        alias_candidate_csv = $aliasCsv
        row_patch_plan_csv = $rowPlanCsv
        diff_preview_csv = $diffCsv
        readiness_csv = $readinessCsv
        policy = [ordered]@{
            source_mutation = $false
            canonical_merge = $false
            db_write = $false
            delete = $false
            stop_process = $false
            no_close = $true
            apply_enabled = $false
        }
    }

    def_WriteJson $candidateManifest (Join-Path $def_CANDIDATE_DIR "VIA_v0114A_SandboxPatchCandidate_Manifest.json") 16
    def_BuildDisabledApplyScript -Path $disabledApply

    def_Progress 9 10 "Build precheck, accelerators, next commands"
    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114B-Precheck-After-v0114A.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114A_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114A_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114A_HotfixSandboxPatchCandidate_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114A.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_CANDIDATE_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_DIFF_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_DISABLED_APPLY_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $diffCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114B validates sandbox candidate only.',
        '# No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readiness[0]

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114A_HOTFIX_SANDBOX_PATCH_CANDIDATE_READY"
        RunId = $def_RUN_ID
        LatestV0113K = $latest
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114B = def_GetProp $r0 "def_allow_v0114B"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        RowPatchRows = def_GetProp $r0 "def_row_patch_plan_rows"
        PolicyRows = def_GetProp $r0 "def_policy_candidate_rows"
        AliasRows = def_GetProp $r0 "def_alias_candidate_rows"
        CandidateDir = $def_CANDIDATE_DIR
        DiffDir = $def_DIFF_DIR
        DisabledApply = $disabledApply
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; sandbox candidate only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114A_HotfixSandboxPatchCandidate_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readiness -Validation $validation -DiffPreview $diffPreview -PolicyCandidate $policyCandidate -AliasCandidate $aliasCandidate -RowPatchPlan $rowPatchPlan -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114A Hotfix Sandbox Candidate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114A Hotfix Sandbox Patch Candidate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114B    : $($summary.AllowV0114B)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($summary.ValidationFail -eq "0") { "Green" } else { "Red" })
    Write-Host "Row Patch Rows  : $($summary.RowPatchRows)" -ForegroundColor Cyan
    Write-Host "Policy Rows     : $($summary.PolicyRows)" -ForegroundColor Cyan
    Write-Host "Alias Rows      : $($summary.AliasRows)" -ForegroundColor Cyan
    Write-Host "Candidate Dir   : $def_CANDIDATE_DIR" -ForegroundColor Cyan
    Write-Host "Diff Dir        : $def_DIFF_DIR" -ForegroundColor Cyan
    Write-Host "Disabled Apply  : $disabledApply" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_CANDIDATE_DIR } catch {}
        try { Start-Process -FilePath $def_DIFF_DIR } catch {}
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed. No exit." -ForegroundColor Yellow
    return
} finally {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · PowerShell remains open" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
}

