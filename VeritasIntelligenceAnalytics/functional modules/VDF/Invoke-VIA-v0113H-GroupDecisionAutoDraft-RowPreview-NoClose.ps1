param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113G_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113H_GROUP_DECISION_AUTODRAFT" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113H_group_decision_autodraft"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_final_group_decision"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113H_GroupDecisionAutoDraft.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113G auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 secret gate final reuse",
    "A06 P0 group recommendation engine",
    "A07 P1 alias recommendation engine",
    "A08 duplicate alias conflict detection",
    "A09 run-specific path blocker",
    "A10 row-level expansion preview",
    "A11 formal accept fields kept blank",
    "A12 editable final decision CSV",
    "A13 v0114 precheck stays blocked",
    "A14 compact HTML matrix report",
    "A15 no delete / no Stop-Process"
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
    Write-Progress -Activity "VIA v0113H Group Decision AutoDraft" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113G {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113G_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113G_ROOT) {
            return $def_PARAM_V0113G_ROOT
        }
        throw "Specified v0113G root does not exist: $def_PARAM_V0113G_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113G_p0p1_gate_compression"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113G output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113G_P0P1GateCompression_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113G output found under: $root"
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

function def_RecommendP0Group {
    param($Row)

    $family = def_GetProp $Row "def_domain_family"
    $suggestedDecision = def_GetProp $Row "def_suggested_group_decision"
    $keys = def_GetProp $Row "def_sample_keys"
    $canonical = def_GetProp $Row "def_suggested_group_canonical_value"

    $recommend = "REVIEW"
    $reason = "Manual review required."
    $safeValue = $canonical

    if ($family -eq "MARKET_TICKER_IDENTITY") {
        $recommend = "YES"
        $reason = "Ticker identity policy is stable and row-level samples map to ticker/schema terms. Source rewrite still forbidden."
        if ($keys -match "ticker_tokens") {
            $reason = "ticker_tokens already resolved as false-positive; ticker identity policy can be accepted as group policy."
        }
    }
    elseif ($family -eq "SCHEMA_FIELD_CONTRACT") {
        $recommend = "YES"
        $reason = "Schema ownership policy is needed for VRN/VDF alignment; accept policy layer only, not raw sample values."
    }
    elseif ($family -eq "DATA_SOURCE_CONTRACT") {
        $recommend = "YES"
        $reason = "Provider contract policy can be accepted because FRED key policy is runtime UI secret parameter and raw secret is forbidden."
        $safeValue = "PROVIDER_REGISTRY_ONLY; API_KEYS_FROM_UI_RUNTIME_SECRET_OR_ENV_NAME_ONLY; RAW_SECRET_FORBIDDEN; FALLBACK_EXPLICIT"
    }
    elseif ($family -eq "GOVERNANCE_POLICY") {
        $recommend = "YES"
        $reason = "Governance policy should be registry-owned. No source mutation."
    }
    elseif ($family -eq "DOMAIN_GENERAL") {
        $recommend = "DEFER"
        $reason = "DOMAIN_GENERAL row such as MACRO_CHINA needs business-domain owner review; do not batch accept."
    }

    return [pscustomobject][ordered]@{
        def_recommended_group_accept = $recommend
        def_recommended_group_canonical_value = $safeValue
        def_recommendation_reason = $reason
    }
}

function def_RecommendP1Alias {
    param($Row)

    $alias = def_GetProp $Row "def_alias"
    $path = def_GetProp $Row "def_path_value"

    $recommend = "REVIEW"
    $selected = ""
    $reason = "Manual alias review required."

    if (def_IsRunSpecificPath $path) {
        $recommend = "NO"
        $selected = ""
        $reason = "Reject run-specific path or launcher file path. Do not promote to canonical alias."
    }
    elseif ($alias -eq "VIA_ROOT_DOWNLOADS") {
        $recommend = "YES"
        $selected = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
        $reason = "Accept only clean project root, not nested run path."
    }
    elseif ($alias -eq "VDF_DIR_DOWNLOADS") {
        $recommend = "YES"
        $selected = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF"
        $reason = "Active VDF module root."
    }
    elseif ($alias -eq "FUNCTIONAL_MODULES_DOWNLOADS") {
        $recommend = "YES"
        $selected = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules"
        $reason = "Active functional modules root."
    }
    elseif ($alias -eq "SUPPORTIVE_MODULES_DOWNLOADS") {
        $recommend = "YES"
        $selected = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules"
        $reason = "Active supportive modules root."
    }
    elseif ($alias -eq "USER_DOWNLOADS") {
        $recommend = "YES_REFERENCE_ONLY"
        $selected = "C:\Users\tonyk\Downloads"
        $reason = "Useful reference root only; not module canonical root."
    }
    elseif ($alias -match "ONEDRIVE|PYTHON_ENV") {
        $recommend = "DEFER"
        $selected = ""
        $reason = "OneDrive/Python env should be handled by EnvManager or legacy bridge, not promoted as active canonical root."
    }

    return [pscustomobject][ordered]@{
        def_recommended_alias_accept = $recommend
        def_recommended_selected_alias_value = $selected
        def_recommendation_reason = $reason
    }
}

function def_BuildP0AutoDraft {
    param([array]$Rows)

    $out = New-Object System.Collections.ArrayList

    foreach ($r in $Rows) {
        $rec = def_RecommendP0Group $r

        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_group_id = def_GetProp $r "def_group_id"
            def_group_user_accept = ""
            def_recommended_group_accept = def_GetProp $rec "def_recommended_group_accept"
            def_group_reject_reason = ""
            def_apply_to_rows = def_GetProp $r "def_apply_to_rows"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_group_risk = def_GetProp $r "def_group_risk"
            def_suggested_group_decision = def_GetProp $r "def_suggested_group_decision"
            def_selected_group_canonical_value = ""
            def_recommended_group_canonical_value = def_GetProp $rec "def_recommended_group_canonical_value"
            def_suggested_group_canonical_value = def_GetProp $r "def_suggested_group_canonical_value"
            def_recommendation_reason = def_GetProp $rec "def_recommendation_reason"
            def_group_note = def_GetProp $r "def_group_note"
            def_sample_keys = def_GetProp $r "def_sample_keys"
            def_auto_apply = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($out)
}

function def_BuildP1AutoDraft {
    param([array]$Rows)

    $out = New-Object System.Collections.ArrayList

    foreach ($r in $Rows) {
        $rec = def_RecommendP1Alias $r

        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_alias = def_GetProp $r "def_alias"
            def_alias_user_accept = ""
            def_recommended_alias_accept = def_GetProp $rec "def_recommended_alias_accept"
            def_alias_reject_reason = ""
            def_path_value = def_GetProp $r "def_path_value"
            def_status = def_GetProp $r "def_status"
            def_risk = def_GetProp $r "def_risk"
            def_suggested_alias_decision = def_GetProp $r "def_suggested_alias_decision"
            def_selected_alias_value = ""
            def_recommended_selected_alias_value = def_GetProp $rec "def_recommended_selected_alias_value"
            def_suggested_selected_alias_value = def_GetProp $r "def_suggested_selected_alias_value"
            def_recommendation_reason = def_GetProp $rec "def_recommendation_reason"
            def_alias_note = def_GetProp $r "def_alias_note"
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
            def_canonical_merge = "false"
        })
    }

    return @($out)
}

function def_BuildRowLevelPreview {
    param([array]$P0Map,[array]$P0Draft)

    $out = New-Object System.Collections.ArrayList

    foreach ($m in $P0Map) {
        $gid = def_GetProp $m "def_group_id"
        $g = @($P0Draft | Where-Object { (def_GetProp $_ "def_group_id") -eq $gid } | Select-Object -First 1)

        $recAccept = ""
        $recCanonical = ""
        $recReason = ""

        if (@($g).Count -gt 0) {
            $recAccept = def_GetProp $g[0] "def_recommended_group_accept"
            $recCanonical = def_GetProp $g[0] "def_recommended_group_canonical_value"
            $recReason = def_GetProp $g[0] "def_recommendation_reason"
        }

        [void]$out.Add([pscustomobject][ordered]@{
            def_preview_scope = "ROW_LEVEL_PREVIEW_ONLY"
            def_group_id = $gid
            def_recommended_group_accept = $recAccept
            def_normalized_key = def_GetProp $m "def_normalized_key"
            def_owner_engine = def_GetProp $m "def_owner_engine"
            def_domain_family = def_GetProp $m "def_domain_family"
            def_recommended_canonical_value = $recCanonical
            def_recommendation_reason = $recReason
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return @($out)
}

function def_BuildReadiness {
    param([array]$SecretRows,[array]$P0Draft,[array]$P1Draft,[array]$DirectRows)

    $directOk = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secretTotal = @($SecretRows).Count

    $p0RealYes = @($P0Draft | Where-Object { (def_GetProp $_ "def_group_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1RealYes = @($P1Draft | Where-Object { (def_GetProp $_ "def_alias_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $p0RecommendedYes = @($P0Draft | Where-Object { (def_GetProp $_ "def_recommended_group_accept") -eq "YES" }).Count
    $p0RecommendedDefer = @($P0Draft | Where-Object { (def_GetProp $_ "def_recommended_group_accept") -ne "YES" }).Count
    $p1RecommendedYes = @($P1Draft | Where-Object { (def_GetProp $_ "def_recommended_alias_accept") -match "^YES" }).Count
    $p1RecommendedNoDefer = @($P1Draft | Where-Object { (def_GetProp $_ "def_recommended_alias_accept") -notmatch "^YES" }).Count

    $gate = "BLOCKED_MANUAL_CONFIRM_REQUIRED_AUTODRAFT_READY"
    $reason = "Auto-draft recommendations generated. Formal accept fields remain blank by policy."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct smoke has review rows."
    }
    elseif ($secretYes -lt $secretTotal) {
        $gate = "BLOCKED_SECRET_GATE"
        $reason = "Secret gate is not fully resolved."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = "false"
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_secret_resolved = "$secretYes"
            def_secret_total = "$secretTotal"
            def_p0_real_yes = "$p0RealYes"
            def_p0_group_total = "$(@($P0Draft).Count)"
            def_p0_recommended_yes = "$p0RecommendedYes"
            def_p0_recommended_defer_or_review = "$p0RecommendedDefer"
            def_p1_real_yes = "$p1RealYes"
            def_p1_alias_total = "$(@($P1Draft).Count)"
            def_p1_recommended_yes_or_reference = "$p1RecommendedYes"
            def_p1_recommended_no_or_defer = "$p1RecommendedNoDefer"
            def_next_allowed_phase = "manual copy recommendations into accept fields, then v0113I formal accept precheck"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        }
    )
}

function def_BuildPrecheck {
    param([string]$P0DraftCsv,[string]$P1DraftCsv,[string]$SecretCsv,[string]$Path)

    $code = @"
`$ErrorActionPreference = "Stop"

`$P0DraftCsv = "$P0DraftCsv"
`$P1DraftCsv = "$P1DraftCsv"
`$SecretCsv = "$SecretCsv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$p0 = def_Load `$P0DraftCsv
`$p1 = def_Load `$P1DraftCsv
`$sec = def_Load `$SecretCsv

`$secPending = @(`$sec | Where-Object { ([string]`$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p0Pending = @(`$p0 | Where-Object { ([string]`$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending = @(`$p1 | Where-Object { ([string]`$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113I Precheck after v0113H" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_GATE."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_CONFIRM_REQUIRED. Copy chosen recommendations into formal accept fields first."
}

Write-Host "[OK] READY_FOR_v0113I_FORMAL_ACCEPT_EXPANSION" -ForegroundColor Green
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
    param($Summary,$Readiness,$P0Draft,$P1Draft,$RowPreview,$SecretRows,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("P0 Rec YES",$Summary.P0RecommendedYes),
        @("P0 Review",$Summary.P0RecommendedReview),
        @("P1 Rec YES",$Summary.P1RecommendedYes),
        @("P1 No/Defer",$Summary.P1RecommendedNoDefer),
        @("Row Preview",$Summary.RowPreview),
        @("NoClose","true")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113H Group Decision AutoDraft</title>
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
<h1>def VIA v0113H · Group Decision Auto-Draft + Row-Level Preview</h1>
<div class="sub">Recommendations only · formal accept remains blank · no mutation · no close</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
本輪只產生推薦草稿，不自動接受。你要把真正同意的列，手動把 def_group_user_accept / def_alias_user_accept 填 YES，才可進 v0113I。P1 中 run-specific path 已建議 NO，OneDrive/Python env 建議 DEFER。
</div>
<span class="tag">No Auto YES</span>
<span class="tag">Recommendation Draft</span>
<span class="tag">Row Preview Only</span>
<span class="tag">No Source Mutation</span>
<span class="tag">NoClose</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_secret_resolved","def_secret_total","def_p0_real_yes","def_p0_group_total","def_p0_recommended_yes","def_p0_recommended_defer_or_review","def_p1_real_yes","def_p1_alias_total","def_p1_recommended_yes_or_reference","def_p1_recommended_no_or_defer","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def P0 Auto-Draft Decision Board</h2>$(def_Table $P0Draft @("def_group_user_accept","def_recommended_group_accept","def_apply_to_rows","def_owner_engine","def_domain_family","def_group_risk","def_selected_group_canonical_value","def_recommended_group_canonical_value","def_recommendation_reason","def_sample_keys") 80)</div>
<div class="sec"><h2>def P1 Auto-Draft Alias Board</h2>$(def_Table $P1Draft @("def_alias_user_accept","def_recommended_alias_accept","def_alias","def_path_value","def_selected_alias_value","def_recommended_selected_alias_value","def_recommendation_reason","def_risk") 80)</div>
<div class="sec"><h2>def Row-Level Expansion Preview</h2>$(def_Table $RowPreview @("def_preview_scope","def_group_id","def_recommended_group_accept","def_normalized_key","def_owner_engine","def_domain_family","def_recommended_canonical_value","def_source_mutation","def_canonical_merge") 220)</div>
<div class="sec"><h2>def Secret Gate Final</h2>$(def_Table $SecretRows @("def_normalized_key","def_user_secret_resolved","def_selected_safe_canonical_value","def_value_printed","def_ui_secret_policy") 20)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113G: $(def_Html $Summary.LatestV0113G)<br/>
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
    Write-Host "def VIA · v0113H GROUP DECISION AUTODRAFT + ROW PREVIEW · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Recommendations only. Formal accept blank. No mutation. No close." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0113G output"
    $latest = def_GetLatestV0113G
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_group_decision"
    def_Log "OK" "Latest v0113G: $latest" Green

    def_Progress 2 9 "Load v0113G boards"
    $p0GroupRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv")
    $p1AliasRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113G_SecretGateFinal.csv")
    $p0Map = def_LoadCsv (Join-Path $latestOut "VIA_v0113G_P0_RowToGroupMap.csv")
    $directRows = def_LoadCsv (Join-Path $latestOut "VIA_v0113G_DirectSmokeBoard.csv")
    def_Log "OK" "Loaded P0Groups=$(@($p0GroupRows).Count), P1Aliases=$(@($p1AliasRows).Count), P0Map=$(@($p0Map).Count)" Green

    def_Progress 3 9 "Build P0 recommendation auto-draft"
    $p0Draft = def_BuildP0AutoDraft -Rows $p0GroupRows

    def_Progress 4 9 "Build P1 recommendation auto-draft"
    $p1Draft = def_BuildP1AutoDraft -Rows $p1AliasRows

    def_Progress 5 9 "Build row-level preview"
    $rowPreview = def_BuildRowLevelPreview -P0Map $p0Map -P0Draft $p0Draft

    def_Progress 6 9 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretRows $secretRows -P0Draft $p0Draft -P1Draft $p1Draft -DirectRows $directRows

    def_Progress 7 9 "Write editable draft boards"
    $p0DraftCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113H_USER_EDIT_P0_GroupDecision_AUTODRAFT.csv"
    $p1DraftCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113H_USER_EDIT_P1_AliasDecision_AUTODRAFT.csv"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113H_SecretGateFinal.csv"

    def_WriteCsv $p0Draft $p0DraftCsv
    def_WriteCsv $p1Draft $p1DraftCsv
    def_WriteCsv $secretRows $secretCsv

    def_Progress 8 9 "Write outputs, precheck, next commands"
    def_WriteCsv $p0Draft (Join-Path $def_OUTPUT_DIR "VIA_v0113H_P0_GroupDecision_AUTODRAFT.csv")
    def_WriteCsv $p1Draft (Join-Path $def_OUTPUT_DIR "VIA_v0113H_P1_AliasDecision_AUTODRAFT.csv")
    def_WriteCsv $rowPreview (Join-Path $def_OUTPUT_DIR "VIA_v0113H_RowLevelExpansion_PREVIEW.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113H_ReadinessGate.csv")
    def_WriteCsv $secretRows (Join-Path $def_OUTPUT_DIR "VIA_v0113H_SecretGateFinal.csv")
    def_WriteCsv $directRows (Join-Path $def_OUTPUT_DIR "VIA_v0113H_DirectSmokeBoard.csv")

    def_WriteJson $p0Draft (Join-Path $def_OUTPUT_DIR "VIA_v0113H_P0_GroupDecision_AUTODRAFT.json")
    def_WriteJson $p1Draft (Join-Path $def_OUTPUT_DIR "VIA_v0113H_P1_AliasDecision_AUTODRAFT.json")
    def_WriteJson $rowPreview (Join-Path $def_OUTPUT_DIR "VIA_v0113H_RowLevelExpansion_PREVIEW.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113H_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0113I-Precheck-After-v0113H.ps1"
    def_BuildPrecheck -P0DraftCsv $p0DraftCsv -P1DraftCsv $p1DraftCsv -SecretCsv $secretCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113H_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113H_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0113H_GroupDecisionAutoDraft_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113H.ps1"

    $next = @"
Start-Process "$report"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_USER_EDIT_DIR"

Import-Csv "$def_OUTPUT_DIR\VIA_v0113H_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$def_OUTPUT_DIR\VIA_v0113H_P0_GroupDecision_AUTODRAFT.csv" | Format-Table -AutoSize
Import-Csv "$def_OUTPUT_DIR\VIA_v0113H_P1_AliasDecision_AUTODRAFT.csv" | Format-Table -AutoSize

# Manual step:
# Copy chosen recommendations into:
#   def_group_user_accept
#   def_selected_group_canonical_value
#   def_alias_user_accept
#   def_selected_alias_value
Start-Process "$p0DraftCsv"
Start-Process "$p1DraftCsv"

# After manual edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$precheck"
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $p0RecYes = @($p0Draft | Where-Object { (def_GetProp $_ "def_recommended_group_accept") -eq "YES" }).Count
    $p0RecReview = @($p0Draft | Where-Object { (def_GetProp $_ "def_recommended_group_accept") -ne "YES" }).Count
    $p1RecYes = @($p1Draft | Where-Object { (def_GetProp $_ "def_recommended_alias_accept") -match "^YES" }).Count
    $p1RecNoDefer = @($p1Draft | Where-Object { (def_GetProp $_ "def_recommended_alias_accept") -notmatch "^YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113H_GROUP_DECISION_AUTODRAFT_READY"
        RunId = $def_RUN_ID
        LatestV0113G = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        P0RecommendedYes = "$p0RecYes"
        P0RecommendedReview = "$p0RecReview"
        P1RecommendedYes = "$p1RecYes"
        P1RecommendedNoDefer = "$p1RecNoDefer"
        RowPreview = "$(@($rowPreview).Count)"
        P0DraftCsv = $p0DraftCsv
        P1DraftCsv = $p1DraftCsv
        SecretCsv = $secretCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no auto YES; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113H_GroupDecisionAutoDraft_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readiness -P0Draft $p0Draft -P1Draft $p1Draft -RowPreview $rowPreview -SecretRows $secretRows -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0113H Group Decision AutoDraft" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113H Group Decision Auto-Draft COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "P0 Rec YES / Review : $($summary.P0RecommendedYes) / $($summary.P0RecommendedReview)" -ForegroundColor Cyan
    Write-Host "P1 Rec YES / Block  : $($summary.P1RecommendedYes) / $($summary.P1RecommendedNoDefer)" -ForegroundColor Cyan
    Write-Host "Row Preview         : $($summary.RowPreview)" -ForegroundColor Cyan
    Write-Host "P0 Draft            : $p0DraftCsv" -ForegroundColor Cyan
    Write-Host "P1 Draft            : $p1DraftCsv" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

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
