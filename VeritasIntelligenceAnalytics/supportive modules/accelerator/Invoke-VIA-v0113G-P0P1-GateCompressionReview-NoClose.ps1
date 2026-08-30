param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113F_ROOT = "",
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

$def_RUN_ID = "RUN_{0}_VIA_v0113G_P0P1_GATE_COMPRESSION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113G_p0p1_gate_compression"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_group_decision"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113G_P0P1GateCompression.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113F auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 secret gate pass reuse",
    "A06 P0 domain-family grouping",
    "A07 P0 owner-engine grouping",
    "A08 P0 key-risk classifier",
    "A09 P1 alias compression",
    "A10 safe default suggestions only",
    "A11 no auto YES guard",
    "A12 editable group-decision CSV",
    "A13 row-to-group trace matrix",
    "A14 v0114 precheck stays blocked",
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
    Write-Progress -Activity "VIA v0113G P0/P1 Gate Compression" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113F {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113F_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113F_ROOT) {
            return $def_PARAM_V0113F_ROOT
        }
        throw "Specified v0113F root does not exist: $def_PARAM_V0113F_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113F_test_debug_hardening"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113F output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113F_TestDebugHardening_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113F output found under: $root"
    }

    return $candidates[0].FullName
}

function def_NormalizeGroupText {
    param([string]$Text)
    $s = (def_S $Text).Trim()
    if ([string]::IsNullOrWhiteSpace($s)) { return "UNKNOWN" }
    $s = $s -replace '[^\p{L}\p{Nd}_\-]+','_'
    $s = $s.Trim("_")
    if ([string]::IsNullOrWhiteSpace($s)) { return "UNKNOWN" }
    return $s
}

function def_P0GroupId {
    param($Row)

    $family = def_NormalizeGroupText (def_GetProp $Row "def_domain_family")
    $owner = def_NormalizeGroupText (def_GetProp $Row "def_owner_engine")
    $suggest = def_NormalizeGroupText (def_GetProp $Row "def_suggested_action")

    return "P0::$family::$owner::$suggest"
}

function def_P0SuggestionForGroup {
    param([string]$Family,[string]$Owner,[string]$SuggestedAction)

    $risk = "MEDIUM"
    $decision = "REVIEW"
    $canonical = ""
    $note = "Manual review required."

    if ($Family -eq "MARKET_TICKER_IDENTITY") {
        $risk = "LOW_MEDIUM"
        $decision = "SUGGEST_ACCEPT_GROUP_POLICY"
        $canonical = "TW_TICKER=4_DIGITS; TWSE_YF={TW_TICKER}.TW; TPEX_YF={TW_TICKER}.TWO; OVERSEAS=PROVIDER_NATIVE_TICKER"
        $note = "Ticker identity policy can be accepted as group policy. Do not rewrite raw rows."
    }
    elseif ($Family -eq "DATA_SOURCE_CONTRACT") {
        $risk = "MEDIUM"
        $decision = "SUGGEST_ACCEPT_PROVIDER_CONTRACT"
        $canonical = "PROVIDER_REGISTRY_ONLY; API_KEYS_FROM_UI_RUNTIME_SECRET_OR_ENV_NAME_ONLY; RAW_SECRET_FORBIDDEN; FALLBACK_EXPLICIT"
        $note = "Accept provider contract only. FRED key stays UI runtime password parameter."
    }
    elseif ($Family -eq "SCHEMA_FIELD_CONTRACT") {
        $risk = "MEDIUM"
        $decision = "SUGGEST_ACCEPT_SCHEMA_OWNER_POLICY"
        $canonical = "OWNER_SCHEMA_REGISTRY; FIELD_ALIAS_MAP; UNIT_NORMALIZATION_TABLE"
        $note = "Accept schema ownership policy, not every observed field sample."
    }
    elseif ($Family -eq "GOVERNANCE_POLICY") {
        $risk = "LOW_MEDIUM"
        $decision = "SUGGEST_ACCEPT_GOVERNANCE_REGISTRY"
        $canonical = "VIA_GOVERNANCE_POLICY_REGISTRY"
        $note = "Governance policy should be centralized. No direct source rewrite."
    }
    elseif ($Family -eq "DOMAIN_GENERAL") {
        $risk = "HIGH"
        $decision = "REVIEW_OR_DEFER"
        $canonical = ""
        $note = "General domain row needs owner decision; do not batch accept blindly."
    }

    return [pscustomobject][ordered]@{
        def_group_risk = $risk
        def_suggested_group_decision = $decision
        def_suggested_group_canonical_value = $canonical
        def_group_note = $note
    }
}

function def_BuildP0GroupBoards {
    param([array]$P0Rows)

    $mapRows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Rows) {
        $gid = def_P0GroupId $r

        [void]$mapRows.Add([pscustomobject][ordered]@{
            def_group_id = $gid
            def_priority = "P0"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_suggested_action = def_GetProp $r "def_suggested_action"
            def_secret_block = def_GetProp $r "def_secret_block"
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_current_user_accept = def_GetProp $r "def_user_accept"
            def_selected_canonical_value = def_GetProp $r "def_selected_canonical_value"
            def_suggested_canonical_value = def_GetProp $r "def_suggested_canonical_value"
            def_sample_values_masked = def_GetProp $r "def_sample_values_masked"
        })
    }

    $groupRows = New-Object System.Collections.ArrayList

    $groups = @($mapRows | Group-Object -Property def_group_id | Sort-Object Count -Descending)

    foreach ($g in $groups) {
        $first = $g.Group[0]
        $family = def_GetProp $first "def_domain_family"
        $owner = def_GetProp $first "def_owner_engine"
        $suggest = def_GetProp $first "def_suggested_action"
        $policy = def_P0SuggestionForGroup -Family $family -Owner $owner -SuggestedAction $suggest

        $keys = @($g.Group | Select-Object -ExpandProperty def_normalized_key -Unique | Select-Object -First 18)
        $sampleKeys = ($keys -join "; ")

        [void]$groupRows.Add([pscustomobject][ordered]@{
            def_priority = "P0_GROUP"
            def_group_id = $g.Name
            def_group_user_accept = ""
            def_group_reject_reason = ""
            def_apply_to_rows = "$($g.Count)"
            def_owner_engine = $owner
            def_domain_family = $family
            def_suggested_action = $suggest
            def_group_risk = def_GetProp $policy "def_group_risk"
            def_suggested_group_decision = def_GetProp $policy "def_suggested_group_decision"
            def_selected_group_canonical_value = ""
            def_suggested_group_canonical_value = def_GetProp $policy "def_suggested_group_canonical_value"
            def_group_note = def_GetProp $policy "def_group_note"
            def_sample_keys = $sampleKeys
            def_auto_apply = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        })
    }

    return [pscustomobject][ordered]@{
        Groups = @($groupRows)
        Map = @($mapRows)
    }
}

function def_P1Suggestion {
    param($Row)

    $alias = def_GetProp $Row "def_alias"
    $path = def_GetProp $Row "def_path_value"
    $status = def_GetProp $Row "def_status"

    $risk = "MEDIUM"
    $decision = "REVIEW"
    $selected = ""
    $note = "Manual alias decision required."

    if ($alias -match "VIA_ROOT_DOWNLOADS|VDF_DIR_DOWNLOADS|FUNCTIONAL_MODULES_DOWNLOADS|SUPPORTIVE_MODULES_DOWNLOADS") {
        $risk = "LOW_MEDIUM"
        $decision = "SUGGEST_ACCEPT_ACTIVE_DOWNLOADS_ROOT"
        $selected = $path
        $note = "Active Downloads root appears consistent with current run path."
    }
    elseif ($alias -match "USER_DOWNLOADS") {
        $risk = "LOW"
        $decision = "SUGGEST_ACCEPT_REFERENCE_ONLY"
        $selected = $path
        $note = "Useful reference root, but not module canonical root."
    }
    elseif ($alias -match "ONEDRIVE|LEGACY") {
        $risk = "MEDIUM_HIGH"
        $decision = "SUGGEST_DEFER_OR_REJECT"
        $selected = ""
        $note = "Legacy/OneDrive root should not be promoted unless still required."
    }
    elseif ($alias -match "PYTHON|ENV") {
        $risk = "MEDIUM"
        $decision = "SUGGEST_DEFER_TO_ENVMANAGER"
        $selected = ""
        $note = "Environment path should be managed by EnvManager, not hard-coded."
    }
    elseif ($status -match "REVIEW_ALIAS") {
        $risk = "MEDIUM"
        $decision = "REVIEW_ALIAS"
        $selected = ""
        $note = "Needs visible path review."
    }

    return [pscustomobject][ordered]@{
        def_alias_risk = $risk
        def_suggested_alias_decision = $decision
        def_suggested_selected_alias_value = $selected
        def_alias_note = $note
    }
}

function def_BuildP1AliasBoard {
    param([array]$P1Rows)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Rows) {
        $s = def_P1Suggestion $r

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P1_ALIAS"
            def_alias = def_GetProp $r "def_alias"
            def_alias_user_accept = ""
            def_alias_reject_reason = ""
            def_path_value = def_GetProp $r "def_path_value"
            def_status = def_GetProp $r "def_status"
            def_risk = def_GetProp $s "def_alias_risk"
            def_suggested_alias_decision = def_GetProp $s "def_suggested_alias_decision"
            def_selected_alias_value = ""
            def_suggested_selected_alias_value = def_GetProp $s "def_suggested_selected_alias_value"
            def_alias_note = def_GetProp $s "def_alias_note"
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
            def_canonical_merge = "false"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param(
        [array]$SecretRows,
        [array]$P0GroupBoard,
        [array]$P1AliasBoard,
        [array]$DirectRows
    )

    $directOk = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $secretYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secretTotal = @($SecretRows).Count

    $p0GroupYes = @($P0GroupBoard | Where-Object { (def_GetProp $_ "def_group_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1AliasYes = @($P1AliasBoard | Where-Object { (def_GetProp $_ "def_alias_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $gate = "BLOCKED_GROUP_ACCEPT_REQUIRED"
    $allow = "false"
    $reason = "Secret gate cleared. P0/P1 group decisions are blank."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct smoke has review rows."
    }
    elseif ($secretYes -lt $secretTotal) {
        $gate = "BLOCKED_SECRET_RESOLUTION_REQUIRED"
        $reason = "Secret gate not fully resolved."
    }
    elseif ($p0GroupYes -eq @($P0GroupBoard).Count -and $p1AliasYes -eq @($P1AliasBoard).Count) {
        $gate = "READY_FOR_ROW_LEVEL_APPLY_PREVIEW"
        $allow = "true"
        $reason = "All compressed P0/P1 groups accepted. Next step may expand to row-level preview only."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_row_level_preview = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_secret_resolved = "$secretYes"
            def_secret_total = "$secretTotal"
            def_p0_group_yes = "$p0GroupYes"
            def_p0_group_total = "$(@($P0GroupBoard).Count)"
            def_p1_alias_yes = "$p1AliasYes"
            def_p1_alias_total = "$(@($P1AliasBoard).Count)"
            def_next_allowed_phase = "v0113H row-level accept expansion preview only"
            def_source_mutation = "false"
            def_canonical_merge = "false"
        }
    )
}

function def_BuildPrecheck {
    param(
        [string]$P0GroupCsv,
        [string]$P1AliasCsv,
        [string]$SecretCsv,
        [string]$Path
    )

    $code = @"
`$ErrorActionPreference = "Stop"

`$P0GroupCsv = "$P0GroupCsv"
`$P1AliasCsv = "$P1AliasCsv"
`$SecretCsv = "$SecretCsv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$p0 = def_Load `$P0GroupCsv
`$p1 = def_Load `$P1AliasCsv
`$sec = def_Load `$SecretCsv

`$secPending = @(`$sec | Where-Object { ([string]`$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p0Pending = @(`$p0 | Where-Object { ([string]`$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending = @(`$p1 | Where-Object { ([string]`$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113H Precheck after v0113G" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending  : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 group pending: `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 alias pending: `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_GROUP_ACCEPT_REQUIRED. Edit compressed group boards and set accepted groups to YES."
}

Write-Host "[OK] READY_FOR_v0113H_ROW_LEVEL_ACCEPT_EXPANSION_PREVIEW" -ForegroundColor Green
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
    param(
        $Summary,
        [array]$Readiness,
        [array]$P0Groups,
        [array]$P1Aliases,
        [array]$P0Map,
        [array]$SecretRows,
        [array]$DirectRows,
        [array]$AccelRows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("P0 Groups",$Summary.P0Groups),
        @("P1 Aliases",$Summary.P1Aliases),
        @("P0 Rows",$Summary.P0Rows),
        @("Secret",$Summary.SecretResolved),
        @("Direct OK",$Summary.DirectOk),
        @("NoClose","true")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113G P0/P1 Gate Compression</title>
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
<h1>def VIA v0113G · P0/P1 Gate Compression Review Board</h1>
<div class="sub">Compress manual decision load · no auto YES · no mutation · no close</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
v0113F 已完成 Secret Gate。v0113G 不做 source mutation，也不把 P0/P1 自動改 YES；它只把 P0 150 筆壓縮成群組決策，把 P1 12 筆整理成 alias 決策，讓下一步可以人工審核。
</div>
<span class="tag">No Auto YES</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">Group Review</span>
<span class="tag">NoClose</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_row_level_preview","def_reason","def_direct_ok","def_secret_resolved","def_secret_total","def_p0_group_yes","def_p0_group_total","def_p1_alias_yes","def_p1_alias_total","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def P0 Group Decision Board</h2>$(def_Table $P0Groups @("def_priority","def_group_user_accept","def_apply_to_rows","def_owner_engine","def_domain_family","def_suggested_action","def_group_risk","def_suggested_group_decision","def_selected_group_canonical_value","def_suggested_group_canonical_value","def_group_note","def_sample_keys") 80)</div>
<div class="sec"><h2>def P1 Alias Decision Board</h2>$(def_Table $P1Aliases @("def_priority","def_alias_user_accept","def_alias","def_path_value","def_risk","def_suggested_alias_decision","def_selected_alias_value","def_suggested_selected_alias_value","def_alias_note","def_scope") 80)</div>
<div class="sec"><h2>def Secret Gate Final</h2>$(def_Table $SecretRows @("def_normalized_key","def_user_secret_resolved","def_selected_safe_canonical_value","def_value_printed","def_ui_secret_policy") 20)</div>
<div class="sec"><h2>def Direct Smoke Board</h2>$(def_Table $DirectRows @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 40)</div>
<div class="sec"><h2>def P0 Row-to-Group Map Preview</h2>$(def_Table $P0Map @("def_group_id","def_owner_engine","def_domain_family","def_suggested_action","def_normalized_key","def_suggested_canonical_value") 220)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113F: $(def_Html $Summary.LatestV0113F)<br/>
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
    Write-Host "def VIA · v0113G P0/P1 GATE COMPRESSION REVIEW · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: No close. No auto YES. No source mutation. No canonical merge." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0113F output"
    $latest = def_GetLatestV0113F
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_after_secret_gate_cleared"
    def_Log "OK" "Latest v0113F: $latest" Green

    def_Progress 2 9 "Load v0113F boards"
    $directRows = def_LoadCsv (Join-Path $latestOut "VIA_v0113F_DirectSmokeBoard.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113F_USER_EDIT_SecretResolution_FINAL.csv")
    $p0Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113F_USER_EDIT_P0_RefinedManualGate.csv")
    $p1Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113F_USER_EDIT_P1_RefinedManualGate.csv")
    def_Log "OK" "Loaded Direct=$(@($directRows).Count), Secret=$(@($secretRows).Count), P0=$(@($p0Rows).Count), P1=$(@($p1Rows).Count)" Green

    def_Progress 3 9 "Build P0 compressed group board"
    $p0Bundle = def_BuildP0GroupBoards -P0Rows $p0Rows
    $p0Groups = @($p0Bundle.Groups)
    $p0Map = @($p0Bundle.Map)

    def_Progress 4 9 "Build P1 compressed alias board"
    $p1AliasBoard = def_BuildP1AliasBoard -P1Rows $p1Rows

    def_Progress 5 9 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretRows $secretRows -P0GroupBoard $p0Groups -P1AliasBoard $p1AliasBoard -DirectRows $directRows

    def_Progress 6 9 "Write editable decision boards"
    $p0GroupCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv"
    $p1AliasCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113G_SecretGateFinal.csv"

    def_WriteCsv $p0Groups $p0GroupCsv
    def_WriteCsv $p1AliasBoard $p1AliasCsv
    def_WriteCsv $secretRows $secretCsv

    def_Progress 7 9 "Write outputs and precheck"
    def_WriteCsv $p0Groups (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P0_GroupDecisionBoard.csv")
    def_WriteCsv $p0Map (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P0_RowToGroupMap.csv")
    def_WriteCsv $p1AliasBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P1_AliasDecisionBoard.csv")
    def_WriteCsv $secretRows (Join-Path $def_OUTPUT_DIR "VIA_v0113G_SecretGateFinal.csv")
    def_WriteCsv $directRows (Join-Path $def_OUTPUT_DIR "VIA_v0113G_DirectSmokeBoard.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113G_ReadinessGate.csv")

    def_WriteJson $p0Groups (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P0_GroupDecisionBoard.json")
    def_WriteJson $p0Map (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P0_RowToGroupMap.json")
    def_WriteJson $p1AliasBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P1_AliasDecisionBoard.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113G_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0113H-Precheck-After-v0113G.ps1"
    def_BuildPrecheck -P0GroupCsv $p0GroupCsv -P1AliasCsv $p1AliasCsv -SecretCsv $secretCsv -Path $precheck

    def_Progress 8 9 "Build accelerator matrix and next commands"
    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113G_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113G_15Accelerators.json")

    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113G.ps1"
    $next = @"
Start-Process "$def_REPORT_DIR\VIA_v0113G_P0P1GateCompression_Report.html"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_USER_EDIT_DIR"

Import-Csv "$def_OUTPUT_DIR\VIA_v0113G_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$def_OUTPUT_DIR\VIA_v0113G_P0_GroupDecisionBoard.csv" | Format-Table -AutoSize
Import-Csv "$def_OUTPUT_DIR\VIA_v0113G_P1_AliasDecisionBoard.csv" | Format-Table -AutoSize

# Manual edit required:
Start-Process "$p0GroupCsv"
Start-Process "$p1AliasCsv"

# After manual group edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$precheck"

# Next phase:
# v0113H expands accepted groups to row-level preview only.
# No source mutation. No canonical merge.
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $directOk = @($directRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretYes = @($secretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113G_P0P1_GATE_COMPRESSION_READY"
        RunId = $def_RUN_ID
        LatestV0113F = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowRowLevelPreview = def_GetProp $readiness[0] "def_allow_row_level_preview"
        DirectOk = "$directOk"
        SecretResolved = "$secretYes / $(@($secretRows).Count)"
        P0Rows = "$(@($p0Rows).Count)"
        P0Groups = "$(@($p0Groups).Count)"
        P1Rows = "$(@($p1Rows).Count)"
        P1Aliases = "$(@($p1AliasBoard).Count)"
        P0GroupCsv = $p0GroupCsv
        P1AliasCsv = $p1AliasCsv
        SecretCsv = $secretCsv
        Precheck = $precheck
        Report = Join-Path $def_REPORT_DIR "VIA_v0113G_P0P1GateCompression_Report.html"
        OutputDir = $def_OUTPUT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; no auto YES; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113G_P0P1GateCompression_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    $report = $summary.Report
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -P0Groups $p0Groups `
        -P1Aliases $p1AliasBoard `
        -P0Map $p0Map `
        -SecretRows $secretRows `
        -DirectRows $directRows `
        -AccelRows $accelRows `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113G P0/P1 Gate Compression" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113G P0/P1 Gate Compression COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow Row Preview   : $($summary.AllowRowLevelPreview)" -ForegroundColor Yellow
    Write-Host "Direct OK           : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "Secret Resolved     : $($summary.SecretResolved)" -ForegroundColor Green
    Write-Host "P0 Rows -> Groups   : $($summary.P0Rows) -> $($summary.P0Groups)" -ForegroundColor Cyan
    Write-Host "P1 Rows -> Aliases  : $($summary.P1Rows) -> $($summary.P1Aliases)" -ForegroundColor Cyan
    Write-Host "P0 Group Edit       : $p0GroupCsv" -ForegroundColor Cyan
    Write-Host "P1 Alias Edit       : $p1AliasCsv" -ForegroundColor Cyan
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
