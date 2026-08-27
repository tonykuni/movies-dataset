param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113H_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113I_FORMAL_ACCEPT_DRAFT" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113I_formal_accept_draft"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_formal_accept_draft"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113I_FormalAcceptDraft.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113H auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 secret gate final reuse",
    "A06 P0 safe recommendation draft fill",
    "A07 P0 review group isolation",
    "A08 P1 clean root draft fill",
    "A09 P1 run-specific path draft reject",
    "A10 P1 legacy/env draft defer",
    "A11 edge review board",
    "A12 row-level draft expansion",
    "A13 v0113J precheck generated",
    "A14 compact HTML matrix report",
    "A15 no delete / no Stop-Process / no source mutation"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_USER_EDIT_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0113I Formal Accept Draft" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113H {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113H_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113H_ROOT) {
            return $def_PARAM_V0113H_ROOT
        }
        throw "Specified v0113H root does not exist: $def_PARAM_V0113H_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113H_group_decision_autodraft"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113H output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113H_GroupDecisionAutoDraft_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113H output found under: $root"
    }

    return $candidates[0].FullName
}

function def_IsRunSpecificPath {
    param([string]$PathText)
    $p = def_S $PathText
    if ($p -match "\\dict\\VDF\\_active\\") { return $true }
    if ($p -match "\\launchers\\Start-.*\.ps1$") { return $true }
    if ($p -match "RUN_\d{8}_\d{6}") { return $true }
    if ($p -match "_\d{8}_\d{6}") { return $true }
    return $false
}

function def_BuildP0FormalDraft {
    param([array]$P0Draft)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Draft) {
        $rec = def_GetProp $r "def_recommended_group_accept"
        $family = def_GetProp $r "def_domain_family"
        $gid = def_GetProp $r "def_group_id"
        $canonical = def_GetProp $r "def_recommended_group_canonical_value"

        $draftAccept = "REVIEW"
        $edge = "true"
        $edgeReason = "Manual review required."

        if ($rec -eq "YES" -and -not [string]::IsNullOrWhiteSpace($canonical)) {
            $draftAccept = "YES"
            $edge = "false"
            $edgeReason = "Recommended YES with safe policy-level canonical value."
        }

        if ($family -eq "DOMAIN_GENERAL") {
            $draftAccept = "DEFER"
            $edge = "true"
            $edgeReason = "DOMAIN_GENERAL must be reviewed by business owner."
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P0_FORMAL_DRAFT"
            def_group_id = $gid
            def_group_user_accept = ""
            def_group_user_accept_draft = $draftAccept
            def_edge_review_required = $edge
            def_edge_review_reason = $edgeReason
            def_apply_to_rows = def_GetProp $r "def_apply_to_rows"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = $family
            def_group_risk = def_GetProp $r "def_group_risk"
            def_selected_group_canonical_value = ""
            def_selected_group_canonical_value_draft = $canonical
            def_recommended_group_canonical_value = $canonical
            def_recommendation_reason = def_GetProp $r "def_recommendation_reason"
            def_sample_keys = def_GetProp $r "def_sample_keys"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildP1FormalDraft {
    param([array]$P1Draft)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Draft) {
        $rec = def_GetProp $r "def_recommended_alias_accept"
        $alias = def_GetProp $r "def_alias"
        $path = def_GetProp $r "def_path_value"
        $selected = def_GetProp $r "def_recommended_selected_alias_value"

        $draftAccept = "REVIEW"
        $edge = "true"
        $edgeReason = "Manual alias review required."

        if (def_IsRunSpecificPath $path) {
            $draftAccept = "NO"
            $edge = "false"
            $edgeReason = "Run-specific or launcher path rejected by policy."
        }
        elseif ($rec -eq "YES" -and -not [string]::IsNullOrWhiteSpace($selected)) {
            $draftAccept = "YES"
            $edge = "false"
            $edgeReason = "Clean active root alias."
        }
        elseif ($rec -eq "YES_REFERENCE_ONLY" -and -not [string]::IsNullOrWhiteSpace($selected)) {
            $draftAccept = "YES_REFERENCE_ONLY"
            $edge = "false"
            $edgeReason = "Reference root accepted as non-canonical module root."
        }
        elseif ($rec -eq "DEFER") {
            $draftAccept = "DEFER"
            $edge = "true"
            $edgeReason = "Legacy/env path should stay under EnvManager or manual owner review."
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P1_FORMAL_DRAFT"
            def_alias = $alias
            def_alias_user_accept = ""
            def_alias_user_accept_draft = $draftAccept
            def_edge_review_required = $edge
            def_edge_review_reason = $edgeReason
            def_path_value = $path
            def_selected_alias_value = ""
            def_selected_alias_value_draft = $selected
            def_recommended_selected_alias_value = $selected
            def_recommendation_reason = def_GetProp $r "def_recommendation_reason"
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildEdgeReview {
    param([array]$P0Formal,[array]$P1Formal)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Formal) {
        if ((def_GetProp $r "def_edge_review_required") -eq "true") {
            [void]$rows.Add([pscustomobject][ordered]@{
                def_layer = "P0"
                def_id = def_GetProp $r "def_group_id"
                def_draft = def_GetProp $r "def_group_user_accept_draft"
                def_reason = def_GetProp $r "def_edge_review_reason"
                def_owner = def_GetProp $r "def_owner_engine"
                def_domain = def_GetProp $r "def_domain_family"
                def_sample = def_GetProp $r "def_sample_keys"
            })
        }
    }

    foreach ($r in $P1Formal) {
        if ((def_GetProp $r "def_edge_review_required") -eq "true") {
            [void]$rows.Add([pscustomobject][ordered]@{
                def_layer = "P1"
                def_id = def_GetProp $r "def_alias"
                def_draft = def_GetProp $r "def_alias_user_accept_draft"
                def_reason = def_GetProp $r "def_edge_review_reason"
                def_owner = "PATH_ALIAS"
                def_domain = "PATH_IO"
                def_sample = def_GetProp $r "def_path_value"
            })
        }
    }

    return @($rows)
}

function def_BuildRowPreview {
    param([array]$RowPreview,[array]$P0Formal)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $RowPreview) {
        $gid = def_GetProp $r "def_group_id"
        $g = @($P0Formal | Where-Object { (def_GetProp $_ "def_group_id") -eq $gid } | Select-Object -First 1)

        $draft = ""
        $canonical = ""
        if (@($g).Count -gt 0) {
            $draft = def_GetProp $g[0] "def_group_user_accept_draft"
            $canonical = def_GetProp $g[0] "def_selected_group_canonical_value_draft"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_preview_scope = "ROW_LEVEL_DRAFT_PREVIEW_ONLY"
            def_group_id = $gid
            def_row_accept_draft = $draft
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_draft_canonical_value = $canonical
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$SecretRows,[array]$P0Formal,[array]$P1Formal,[array]$EdgeRows)

    $secretYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secretTotal = @($SecretRows).Count

    $p0FormalYes = @($P0Formal | Where-Object { (def_GetProp $_ "def_group_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1FormalYes = @($P1Formal | Where-Object { (def_GetProp $_ "def_alias_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $p0DraftYes = @($P0Formal | Where-Object { (def_GetProp $_ "def_group_user_accept_draft") -eq "YES" }).Count
    $p0DraftDeferReview = @($P0Formal | Where-Object { (def_GetProp $_ "def_group_user_accept_draft") -ne "YES" }).Count

    $p1DraftYesRef = @($P1Formal | Where-Object { (def_GetProp $_ "def_alias_user_accept_draft") -match "^YES" }).Count
    $p1DraftNoDefer = @($P1Formal | Where-Object { (def_GetProp $_ "def_alias_user_accept_draft") -notmatch "^YES" }).Count

    $gate = "BLOCKED_FORMAL_ACCEPT_REQUIRED_DRAFT_READY"
    $reason = "Draft decisions generated. Formal accept fields remain blank by policy."

    if ($secretYes -lt $secretTotal) {
        $gate = "BLOCKED_SECRET_GATE"
        $reason = "Secret gate not fully resolved."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0113J = "false"
            def_reason = $reason
            def_secret_resolved = "$secretYes"
            def_secret_total = "$secretTotal"
            def_p0_formal_yes = "$p0FormalYes"
            def_p0_total = "$(@($P0Formal).Count)"
            def_p0_draft_yes = "$p0DraftYes"
            def_p0_draft_defer_or_review = "$p0DraftDeferReview"
            def_p1_formal_yes = "$p1FormalYes"
            def_p1_total = "$(@($P1Formal).Count)"
            def_p1_draft_yes_or_reference = "$p1DraftYesRef"
            def_p1_draft_no_or_defer = "$p1DraftNoDefer"
            def_edge_review_rows = "$(@($EdgeRows).Count)"
            def_next_allowed_phase = "v0113J manual promotion from draft to formal accept"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        }
    )
}

function def_BuildPrecheck {
    param([string]$P0FormalCsv,[string]$P1FormalCsv,[string]$SecretCsv,[string]$Path)

    $code = @"
`$ErrorActionPreference = "Stop"

`$P0FormalCsv = "$P0FormalCsv"
`$P1FormalCsv = "$P1FormalCsv"
`$SecretCsv = "$SecretCsv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$p0 = def_Load `$P0FormalCsv
`$p1 = def_Load `$P1FormalCsv
`$sec = def_Load `$SecretCsv

`$secPending = @(`$sec | Where-Object { ([string]`$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p0Pending = @(`$p0 | Where-Object { ([string]`$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending = @(`$p1 | Where-Object { ([string]`$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113J Precheck after v0113I" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_GATE."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_FORMAL_ACCEPT_REQUIRED. Promote draft choices to formal accept fields first."
}

Write-Host "[OK] READY_FOR_v0113J_FORMAL_ACCEPT_ROW_EXPANSION" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=220)

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
    param($Summary,$Readiness,$P0Formal,$P1Formal,$EdgeRows,$RowDraftPreview,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("P0 Draft YES",$Summary.P0DraftYes),
        @("P0 Review",$Summary.P0DraftReview),
        @("P1 Draft YES",$Summary.P1DraftYes),
        @("P1 No/Defer",$Summary.P1DraftNoDefer),
        @("Edge Review",$Summary.EdgeRows),
        @("NoClose","true")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113I Formal Accept Draft</title>
<style>
body{margin:0;background:#f7f6f2;color:#24231f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.4px;line-height:1.32}
.wrap{max-width:1800px;margin:0 auto;padding:15px}
h1{font-size:14.5px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:#706d64;margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}
.footer{margin-top:11px;color:#706d64;font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA v0113I · Formal Accept Draft + Edge Review Gate</h1>
<div class="sub">Draft decisions only · formal accept blank · no mutation · no close</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
v0113I 已把建議轉成 draft 欄位。正式欄位仍空白，所以還不會通過 v0113J。你要人工把同意的 draft 值升成 formal accept，下一輪才會展開 row-level formal preview。
</div>
<span class="tag">Draft Only</span>
<span class="tag">Formal Blank</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">NoClose</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0113J","def_reason","def_secret_resolved","def_secret_total","def_p0_formal_yes","def_p0_total","def_p0_draft_yes","def_p0_draft_defer_or_review","def_p1_formal_yes","def_p1_total","def_p1_draft_yes_or_reference","def_p1_draft_no_or_defer","def_edge_review_rows","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def P0 Formal Accept Draft</h2>$(def_Table $P0Formal @("def_group_user_accept","def_group_user_accept_draft","def_edge_review_required","def_apply_to_rows","def_owner_engine","def_domain_family","def_selected_group_canonical_value","def_selected_group_canonical_value_draft","def_edge_review_reason","def_sample_keys") 80)</div>
<div class="sec"><h2>def P1 Formal Accept Draft</h2>$(def_Table $P1Formal @("def_alias_user_accept","def_alias_user_accept_draft","def_edge_review_required","def_alias","def_path_value","def_selected_alias_value","def_selected_alias_value_draft","def_edge_review_reason") 80)</div>
<div class="sec"><h2>def Edge Review Board</h2>$(def_Table $EdgeRows @("def_layer","def_id","def_draft","def_reason","def_owner","def_domain","def_sample") 80)</div>
<div class="sec"><h2>def Row-Level Draft Preview</h2>$(def_Table $RowDraftPreview @("def_preview_scope","def_group_id","def_row_accept_draft","def_normalized_key","def_owner_engine","def_domain_family","def_draft_canonical_value","def_source_mutation","def_canonical_merge") 220)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113H: $(def_Html $Summary.LatestV0113H)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit: $(def_Html $Summary.UserEditDir)<br/>
Report: $(def_Html $ReportPath)
</div>
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0113I FORMAL ACCEPT DRAFT + EDGE REVIEW · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Draft only. Formal accept blank. No mutation. No close." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0113H output"
    $latest = def_GetLatestV0113H
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_final_group_decision"
    def_Log "OK" "Latest v0113H: $latest" Green

    def_Progress 2 9 "Load v0113H boards"
    $p0Draft = def_LoadCsv (Join-Path $latestEdit "VIA_v0113H_USER_EDIT_P0_GroupDecision_AUTODRAFT.csv")
    $p1Draft = def_LoadCsv (Join-Path $latestEdit "VIA_v0113H_USER_EDIT_P1_AliasDecision_AUTODRAFT.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113H_SecretGateFinal.csv")
    $rowPreview = def_LoadCsv (Join-Path $latestOut "VIA_v0113H_RowLevelExpansion_PREVIEW.csv")
    def_Log "OK" "Loaded P0Draft=$(@($p0Draft).Count), P1Draft=$(@($p1Draft).Count), RowPreview=$(@($rowPreview).Count)" Green

    def_Progress 3 9 "Build P0 formal accept draft"
    $p0Formal = def_BuildP0FormalDraft -P0Draft $p0Draft

    def_Progress 4 9 "Build P1 formal accept draft"
    $p1Formal = def_BuildP1FormalDraft -P1Draft $p1Draft

    def_Progress 5 9 "Build edge review board"
    $edgeRows = def_BuildEdgeReview -P0Formal $p0Formal -P1Formal $p1Formal

    def_Progress 6 9 "Build row-level draft preview"
    $rowDraftPreview = def_BuildRowPreview -RowPreview $rowPreview -P0Formal $p0Formal

    def_Progress 7 9 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretRows $secretRows -P0Formal $p0Formal -P1Formal $p1Formal -EdgeRows $edgeRows

    def_Progress 8 9 "Write outputs, precheck, next commands"
    $p0FormalCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113I_USER_EDIT_P0_FormalAcceptDraft.csv"
    $p1FormalCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113I_USER_EDIT_P1_FormalAcceptDraft.csv"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113I_SecretGateFinal.csv"
    $edgeCsv = Join-Path $def_OUTPUT_DIR "VIA_v0113I_EdgeReviewBoard.csv"

    def_WriteCsv $p0Formal $p0FormalCsv
    def_WriteCsv $p1Formal $p1FormalCsv
    def_WriteCsv $secretRows $secretCsv
    def_WriteCsv $edgeRows $edgeCsv
    def_WriteCsv $rowDraftPreview (Join-Path $def_OUTPUT_DIR "VIA_v0113I_RowLevelDraftPreview.csv")
    def_WriteCsv $p0Formal (Join-Path $def_OUTPUT_DIR "VIA_v0113I_P0_FormalAcceptDraft.csv")
    def_WriteCsv $p1Formal (Join-Path $def_OUTPUT_DIR "VIA_v0113I_P1_FormalAcceptDraft.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113I_ReadinessGate.csv")
    def_WriteCsv $secretRows (Join-Path $def_OUTPUT_DIR "VIA_v0113I_SecretGateFinal.csv")

    def_WriteJson $p0Formal (Join-Path $def_OUTPUT_DIR "VIA_v0113I_P0_FormalAcceptDraft.json")
    def_WriteJson $p1Formal (Join-Path $def_OUTPUT_DIR "VIA_v0113I_P1_FormalAcceptDraft.json")
    def_WriteJson $edgeRows (Join-Path $def_OUTPUT_DIR "VIA_v0113I_EdgeReviewBoard.json")
    def_WriteJson $rowDraftPreview (Join-Path $def_OUTPUT_DIR "VIA_v0113I_RowLevelDraftPreview.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113I_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0113J-Precheck-After-v0113I.ps1"
    def_BuildPrecheck -P0FormalCsv $p0FormalCsv -P1FormalCsv $p1FormalCsv -SecretCsv $secretCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113I_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113I_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0113I_FormalAcceptDraft_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113I.ps1"

    $next = @"
Start-Process "$report"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_USER_EDIT_DIR"

Import-Csv "$def_OUTPUT_DIR\VIA_v0113I_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$edgeCsv" | Format-Table -AutoSize

Start-Process "$p0FormalCsv"
Start-Process "$p1FormalCsv"

# Manual promotion:
# Copy def_group_user_accept_draft into def_group_user_accept for accepted P0 rows.
# Copy def_selected_group_canonical_value_draft into def_selected_group_canonical_value.
# Copy def_alias_user_accept_draft into def_alias_user_accept for accepted P1 rows.
# Copy def_selected_alias_value_draft into def_selected_alias_value.
#
# Then run:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$precheck"
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $p0DraftYes = @($p0Formal | Where-Object { (def_GetProp $_ "def_group_user_accept_draft") -eq "YES" }).Count
    $p0DraftReview = @($p0Formal | Where-Object { (def_GetProp $_ "def_group_user_accept_draft") -ne "YES" }).Count
    $p1DraftYes = @($p1Formal | Where-Object { (def_GetProp $_ "def_alias_user_accept_draft") -match "^YES" }).Count
    $p1DraftNoDefer = @($p1Formal | Where-Object { (def_GetProp $_ "def_alias_user_accept_draft") -notmatch "^YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113I_FORMAL_ACCEPT_DRAFT_READY"
        RunId = $def_RUN_ID
        LatestV0113H = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        P0DraftYes = "$p0DraftYes"
        P0DraftReview = "$p0DraftReview"
        P1DraftYes = "$p1DraftYes"
        P1DraftNoDefer = "$p1DraftNoDefer"
        EdgeRows = "$(@($edgeRows).Count)"
        RowDraftPreview = "$(@($rowDraftPreview).Count)"
        P0FormalCsv = $p0FormalCsv
        P1FormalCsv = $p1FormalCsv
        EdgeCsv = $edgeCsv
        SecretCsv = $secretCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; draft only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113I_FormalAcceptDraft_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readiness -P0Formal $p0Formal -P1Formal $p1Formal -EdgeRows $edgeRows -RowDraftPreview $rowDraftPreview -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0113I Formal Accept Draft" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113I Formal Accept Draft COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "P0 Draft YES    : $($summary.P0DraftYes)" -ForegroundColor Cyan
    Write-Host "P0 Review       : $($summary.P0DraftReview)" -ForegroundColor Yellow
    Write-Host "P1 Draft YES    : $($summary.P1DraftYes)" -ForegroundColor Cyan
    Write-Host "P1 No/Defer     : $($summary.P1DraftNoDefer)" -ForegroundColor Yellow
    Write-Host "Edge Rows       : $($summary.EdgeRows)" -ForegroundColor Yellow
    Write-Host "Row Preview     : $($summary.RowDraftPreview)" -ForegroundColor Cyan
    Write-Host "P0 Formal Draft : $p0FormalCsv" -ForegroundColor Cyan
    Write-Host "P1 Formal Draft : $p1FormalCsv" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_USER_EDIT_DIR } catch {}
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
