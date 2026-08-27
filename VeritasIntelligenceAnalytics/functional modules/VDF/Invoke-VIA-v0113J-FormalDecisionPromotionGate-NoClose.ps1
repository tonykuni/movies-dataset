param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113I_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113J_FORMAL_DECISION_PROMOTION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113J_formal_decision_promotion"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_formal_decision_final"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113J_FormalDecisionPromotion.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113I auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 explicit final-state decision model",
    "A06 P0 YES/DEFER/NO allowed-state gate",
    "A07 P1 YES/YES_REFERENCE_ONLY/NO/DEFER allowed-state gate",
    "A08 run-specific path remains NO",
    "A09 legacy/env path remains DEFER",
    "A10 MACRO_CHINA remains DEFER",
    "A11 row-level final preview only",
    "A12 no source mutation guard",
    "A13 no canonical merge guard",
    "A14 v0113K precheck generated",
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
    Write-Progress -Activity "VIA v0113J Formal Decision Promotion Gate" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113I {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113I_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113I_ROOT) {
            return $def_PARAM_V0113I_ROOT
        }
        throw "Specified v0113I root does not exist: $def_PARAM_V0113I_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113I_formal_accept_draft"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113I output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113I_FormalAcceptDraft_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113I output found under: $root"
    }

    return $candidates[0].FullName
}

function def_AskYes {
    param([string]$Title,[string]$Message)

    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host $Title -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host $Message -ForegroundColor Gray
    Write-Host ""
    $ans = Read-Host "Type YES to confirm"
    return (($ans.Trim().ToUpperInvariant()) -eq "YES")
}

function def_PromoteP0 {
    param([array]$P0Rows,[bool]$ConfirmSafe,[bool]$ConfirmEdge)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Rows) {
        $draft = (def_GetProp $r "def_group_user_accept_draft").Trim().ToUpperInvariant()
        $edge = (def_GetProp $r "def_edge_review_required").Trim().ToLowerInvariant()
        $final = ""
        $finalValue = ""
        $finalReason = "Not promoted."

        if ($draft -eq "YES" -and $ConfirmSafe) {
            $final = "YES"
            $finalValue = def_GetProp $r "def_selected_group_canonical_value_draft"
            $finalReason = "Promoted from safe draft YES by user confirmation."
        }
        elseif ($draft -in @("DEFER","NO") -and $ConfirmEdge) {
            $final = $draft
            $finalValue = ""
            $finalReason = "Edge decision retained as explicit $draft by user confirmation."
        }
        elseif ($draft -eq "REVIEW") {
            $final = ""
            $finalValue = ""
            $finalReason = "Draft REVIEW remains pending."
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P0_FORMAL_FINAL"
            def_group_id = def_GetProp $r "def_group_id"
            def_group_final_decision = $final
            def_group_final_value = $finalValue
            def_group_draft_decision = $draft
            def_edge_review_required = def_GetProp $r "def_edge_review_required"
            def_edge_review_reason = def_GetProp $r "def_edge_review_reason"
            def_apply_to_rows = def_GetProp $r "def_apply_to_rows"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_group_risk = def_GetProp $r "def_group_risk"
            def_final_reason = $finalReason
            def_sample_keys = def_GetProp $r "def_sample_keys"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_PromoteP1 {
    param([array]$P1Rows,[bool]$ConfirmClean,[bool]$ConfirmEdge)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Rows) {
        $draft = (def_GetProp $r "def_alias_user_accept_draft").Trim().ToUpperInvariant()
        $final = ""
        $finalValue = ""
        $finalReason = "Not promoted."

        if ($draft -in @("YES","YES_REFERENCE_ONLY") -and $ConfirmClean) {
            $final = $draft
            $finalValue = def_GetProp $r "def_selected_alias_value_draft"
            $finalReason = "Promoted from clean/reference alias draft by user confirmation."
        }
        elseif ($draft -in @("NO","DEFER") -and $ConfirmEdge) {
            $final = $draft
            $finalValue = ""
            $finalReason = "Edge alias decision retained as explicit $draft by user confirmation."
        }
        elseif ($draft -eq "REVIEW") {
            $final = ""
            $finalValue = ""
            $finalReason = "Draft REVIEW remains pending."
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P1_FORMAL_FINAL"
            def_alias = def_GetProp $r "def_alias"
            def_alias_final_decision = $final
            def_alias_final_value = $finalValue
            def_alias_draft_decision = $draft
            def_edge_review_required = def_GetProp $r "def_edge_review_required"
            def_edge_review_reason = def_GetProp $r "def_edge_review_reason"
            def_path_value = def_GetProp $r "def_path_value"
            def_final_reason = $finalReason
            def_scope = "future_generated_scripts_only"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildRowFinalPreview {
    param([array]$RowDraftPreview,[array]$P0Final)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $RowDraftPreview) {
        $gid = def_GetProp $r "def_group_id"
        $g = @($P0Final | Where-Object { (def_GetProp $_ "def_group_id") -eq $gid } | Select-Object -First 1)

        $decision = ""
        $value = ""
        $state = "PENDING"

        if (@($g).Count -gt 0) {
            $decision = def_GetProp $g[0] "def_group_final_decision"
            $value = def_GetProp $g[0] "def_group_final_value"

            if ($decision -eq "YES") {
                $state = "INCLUDED_IN_ROW_LEVEL_PREVIEW"
            }
            elseif ($decision -in @("DEFER","NO")) {
                $state = "EXCLUDED_BY_EXPLICIT_$decision"
            }
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_preview_scope = "ROW_LEVEL_FORMAL_PREVIEW_ONLY"
            def_row_preview_state = $state
            def_group_id = $gid
            def_group_final_decision = $decision
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_final_canonical_value = $value
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$SecretRows,[array]$P0Final,[array]$P1Final,[array]$RowFinalPreview)

    $secretYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secretTotal = @($SecretRows).Count

    $p0Pending = @($P0Final | Where-Object { [string]::IsNullOrWhiteSpace((def_GetProp $_ "def_group_final_decision")) }).Count
    $p1Pending = @($P1Final | Where-Object { [string]::IsNullOrWhiteSpace((def_GetProp $_ "def_alias_final_decision")) }).Count

    $p0Yes = @($P0Final | Where-Object { (def_GetProp $_ "def_group_final_decision") -eq "YES" }).Count
    $p0DeferNo = @($P0Final | Where-Object { (def_GetProp $_ "def_group_final_decision") -in @("DEFER","NO") }).Count

    $p1YesRef = @($P1Final | Where-Object { (def_GetProp $_ "def_alias_final_decision") -in @("YES","YES_REFERENCE_ONLY") }).Count
    $p1NoDefer = @($P1Final | Where-Object { (def_GetProp $_ "def_alias_final_decision") -in @("NO","DEFER") }).Count

    $rowIncluded = @($RowFinalPreview | Where-Object { (def_GetProp $_ "def_row_preview_state") -eq "INCLUDED_IN_ROW_LEVEL_PREVIEW" }).Count
    $rowExcluded = @($RowFinalPreview | Where-Object { (def_GetProp $_ "def_row_preview_state") -match "^EXCLUDED_BY_EXPLICIT_" }).Count

    $gate = "READY_FOR_v0113K_ROW_LEVEL_FINAL_PREVIEW"
    $allow = "true"
    $reason = "All gates have explicit final decisions. Next phase may generate row-level final preview only."

    if ($secretYes -lt $secretTotal) {
        $gate = "BLOCKED_SECRET_GATE"
        $allow = "false"
        $reason = "Secret gate is not fully resolved."
    }
    elseif ($p0Pending -gt 0 -or $p1Pending -gt 0) {
        $gate = "BLOCKED_PENDING_FORMAL_DECISIONS"
        $allow = "false"
        $reason = "At least one P0/P1 formal decision is still blank."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0113K = $allow
            def_reason = $reason
            def_secret_resolved = "$secretYes"
            def_secret_total = "$secretTotal"
            def_p0_yes = "$p0Yes"
            def_p0_defer_or_no = "$p0DeferNo"
            def_p0_pending = "$p0Pending"
            def_p0_total = "$(@($P0Final).Count)"
            def_p1_yes_or_reference = "$p1YesRef"
            def_p1_no_or_defer = "$p1NoDefer"
            def_p1_pending = "$p1Pending"
            def_p1_total = "$(@($P1Final).Count)"
            def_row_included = "$rowIncluded"
            def_row_excluded = "$rowExcluded"
            def_next_allowed_phase = "v0113K row-level final preview only; still no source mutation"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        }
    )
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$Path)

    $code = @"
`$ErrorActionPreference = "Stop"

`$ReadinessCsv = "$ReadinessCsv"

if (-not (Test-Path -LiteralPath `$ReadinessCsv)) {
    throw "Missing readiness CSV: `$ReadinessCsv"
}

`$r = @(Import-Csv -LiteralPath `$ReadinessCsv)[0]

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113K Precheck after v0113J" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate        : `$(`$r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow v0113K: `$(`$r.def_allow_v0113K)" -ForegroundColor Yellow
Write-Host "P0 pending  : `$(`$r.def_p0_pending) / `$(`$r.def_p0_total)" -ForegroundColor Yellow
Write-Host "P1 pending  : `$(`$r.def_p1_pending) / `$(`$r.def_p1_total)" -ForegroundColor Yellow

if (`$r.def_allow_v0113K -ne "true") {
    throw "BLOCKED_NOT_READY_FOR_v0113K."
}

Write-Host "[OK] READY_FOR_v0113K_ROW_LEVEL_FINAL_PREVIEW" -ForegroundColor Green
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
    param($Summary,$Readiness,$P0Final,$P1Final,$RowFinalPreview,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0113K",$Summary.AllowV0113K),
        @("P0 YES",$Summary.P0Yes),
        @("P0 Defer/No",$Summary.P0DeferNo),
        @("P1 YES/Ref",$Summary.P1YesRef),
        @("P1 No/Defer",$Summary.P1NoDefer),
        @("Row Included",$Summary.RowIncluded)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113J Formal Decision Promotion Gate</title>
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
<h1>def VIA v0113J · Formal Decision Promotion Gate</h1>
<div class="sub">Explicit final decisions · row-level final preview only · no mutation · no close</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
本輪只把 draft 決策提升為 formal decision。YES 會進 row-level preview；DEFER/NO 會明確排除。這仍不是 canonical merge，也不是 source mutation。
</div>
<span class="tag">Formal Decision</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">Row Preview Only</span>
<span class="tag">NoClose</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0113K","def_reason","def_secret_resolved","def_secret_total","def_p0_yes","def_p0_defer_or_no","def_p0_pending","def_p0_total","def_p1_yes_or_reference","def_p1_no_or_defer","def_p1_pending","def_p1_total","def_row_included","def_row_excluded","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def P0 Formal Final Decision</h2>$(def_Table $P0Final @("def_group_final_decision","def_group_final_value","def_apply_to_rows","def_owner_engine","def_domain_family","def_final_reason","def_sample_keys") 80)</div>
<div class="sec"><h2>def P1 Formal Final Decision</h2>$(def_Table $P1Final @("def_alias_final_decision","def_alias_final_value","def_alias","def_path_value","def_final_reason","def_scope") 80)</div>
<div class="sec"><h2>def Row-Level Formal Preview</h2>$(def_Table $RowFinalPreview @("def_row_preview_state","def_group_final_decision","def_normalized_key","def_owner_engine","def_domain_family","def_final_canonical_value","def_source_mutation","def_canonical_merge") 220)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113I: $(def_Html $Summary.LatestV0113I)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
Formal final: $(def_Html $Summary.UserEditDir)<br/>
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
    Write-Host "def VIA · v0113J FORMAL DECISION PROMOTION GATE · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Formal explicit decisions only. No source mutation. No canonical merge. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0113I output"
    $latest = def_GetLatestV0113I
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_formal_accept_draft"
    def_Log "OK" "Latest v0113I: $latest" Green

    def_Progress 2 10 "Load v0113I boards"
    $p0Draft = def_LoadCsv (Join-Path $latestEdit "VIA_v0113I_USER_EDIT_P0_FormalAcceptDraft.csv")
    $p1Draft = def_LoadCsv (Join-Path $latestEdit "VIA_v0113I_USER_EDIT_P1_FormalAcceptDraft.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113I_SecretGateFinal.csv")
    $rowDraftPreview = def_LoadCsv (Join-Path $latestOut "VIA_v0113I_RowLevelDraftPreview.csv")
    def_Log "OK" "Loaded P0=$(@($p0Draft).Count), P1=$(@($p1Draft).Count), RowDraft=$(@($rowDraftPreview).Count)" Green

    def_Progress 3 10 "Interactive confirmation"
    $confirmP0Safe = def_AskYes -Title "PROMOTE P0 SAFE DRAFT YES" -Message "確認將 P0 的 12 組安全 YES draft 轉成 formal YES。MACRO_CHINA 不會變 YES。"
    $confirmEdge = def_AskYes -Title "KEEP EDGE DECISIONS EXPLICIT" -Message "確認 MACRO_CHINA=DEFER、OneDrive/env=DEFER、run-specific paths=NO。這些不會進 canonical active root。"
    $confirmP1Clean = def_AskYes -Title "PROMOTE P1 CLEAN ROOT ALIASES" -Message "確認將 Downloads active roots 轉成 formal YES，USER_DOWNLOADS 轉成 YES_REFERENCE_ONLY。"

    def_Progress 4 10 "Promote P0 formal decisions"
    $p0Final = def_PromoteP0 -P0Rows $p0Draft -ConfirmSafe $confirmP0Safe -ConfirmEdge $confirmEdge

    def_Progress 5 10 "Promote P1 formal decisions"
    $p1Final = def_PromoteP1 -P1Rows $p1Draft -ConfirmClean $confirmP1Clean -ConfirmEdge $confirmEdge

    def_Progress 6 10 "Build row-level formal preview"
    $rowFinalPreview = def_BuildRowFinalPreview -RowDraftPreview $rowDraftPreview -P0Final $p0Final

    def_Progress 7 10 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretRows $secretRows -P0Final $p0Final -P1Final $p1Final -RowFinalPreview $rowFinalPreview

    def_Progress 8 10 "Write outputs and precheck"
    $p0FinalCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113J_P0_FormalFinalDecision.csv"
    $p1FinalCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113J_P1_FormalFinalDecision.csv"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113J_SecretGateFinal.csv"
    $rowPreviewCsv = Join-Path $def_OUTPUT_DIR "VIA_v0113J_RowLevelFormalPreview.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0113J_ReadinessGate.csv"

    def_WriteCsv $p0Final $p0FinalCsv
    def_WriteCsv $p1Final $p1FinalCsv
    def_WriteCsv $secretRows $secretCsv
    def_WriteCsv $rowFinalPreview $rowPreviewCsv
    def_WriteCsv $readiness $readinessCsv

    def_WriteJson $p0Final (Join-Path $def_OUTPUT_DIR "VIA_v0113J_P0_FormalFinalDecision.json")
    def_WriteJson $p1Final (Join-Path $def_OUTPUT_DIR "VIA_v0113J_P1_FormalFinalDecision.json")
    def_WriteJson $rowFinalPreview (Join-Path $def_OUTPUT_DIR "VIA_v0113J_RowLevelFormalPreview.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113J_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0113K-Precheck-After-v0113J.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    def_Progress 9 10 "Build accelerator matrix and next commands"
    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113J_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113J_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0113J_FormalDecisionPromotion_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113J.ps1"

    $next = @"
Start-Process "$report"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_USER_EDIT_DIR"

Import-Csv "$readinessCsv" | Format-Table -AutoSize
Import-Csv "$p0FinalCsv" | Format-Table -AutoSize
Import-Csv "$p1FinalCsv" | Format-Table -AutoSize

pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$precheck"

# Next:
# v0113K will generate final row-level preview and v0114 sandbox patch candidate input only.
# No source mutation. No canonical merge.
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $r0 = $readiness[0]

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113J_FORMAL_DECISION_PROMOTION_READY"
        RunId = $def_RUN_ID
        LatestV0113I = $latest
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0113K = def_GetProp $r0 "def_allow_v0113K"
        P0Yes = def_GetProp $r0 "def_p0_yes"
        P0DeferNo = def_GetProp $r0 "def_p0_defer_or_no"
        P0Pending = def_GetProp $r0 "def_p0_pending"
        P1YesRef = def_GetProp $r0 "def_p1_yes_or_reference"
        P1NoDefer = def_GetProp $r0 "def_p1_no_or_defer"
        P1Pending = def_GetProp $r0 "def_p1_pending"
        RowIncluded = def_GetProp $r0 "def_row_included"
        RowExcluded = def_GetProp $r0 "def_row_excluded"
        P0FinalCsv = $p0FinalCsv
        P1FinalCsv = $p1FinalCsv
        RowPreviewCsv = $rowPreviewCsv
        ReadinessCsv = $readinessCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; formal decisions only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113J_FormalDecisionPromotion_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readiness -P0Final $p0Final -P1Final $p1Final -RowFinalPreview $rowFinalPreview -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0113J Formal Decision Promotion Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113J Formal Decision Promotion COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status        : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate          : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0113K  : $($summary.AllowV0113K)" -ForegroundColor Yellow
    Write-Host "P0 YES        : $($summary.P0Yes)" -ForegroundColor Cyan
    Write-Host "P0 Defer/No   : $($summary.P0DeferNo)" -ForegroundColor Yellow
    Write-Host "P0 Pending    : $($summary.P0Pending)" -ForegroundColor Yellow
    Write-Host "P1 YES/Ref    : $($summary.P1YesRef)" -ForegroundColor Cyan
    Write-Host "P1 No/Defer   : $($summary.P1NoDefer)" -ForegroundColor Yellow
    Write-Host "P1 Pending    : $($summary.P1Pending)" -ForegroundColor Yellow
    Write-Host "Row Included  : $($summary.RowIncluded)" -ForegroundColor Cyan
    Write-Host "Row Excluded  : $($summary.RowExcluded)" -ForegroundColor Yellow
    Write-Host "Precheck      : $precheck" -ForegroundColor Cyan
    Write-Host "Report        : $report" -ForegroundColor Cyan
    Write-Host "Output        : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd       : $nextCmd" -ForegroundColor Cyan

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
