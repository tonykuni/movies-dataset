param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113A_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113B_secret_triage_manual_gate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_refined"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113B_SecretTriage_ManualGate.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0113A auto discovery",
    "A02 no BASE re-scan",
    "A03 secret false-positive classifier",
    "A04 true secret blocker isolation",
    "A05 RUN_ID/path token false-positive classification",
    "A06 policy text false-positive classification",
    "A07 env-var reference classification",
    "A08 P0 refined manual gate",
    "A09 P1 refined manual gate",
    "A10 user_accept remains blank",
    "A11 no automatic YES",
    "A12 no source mutation",
    "A13 no canonical merge",
    "A14 compact HTML report",
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
    Write-Progress -Activity "VIA v0113B Secret Triage Manual Gate" -Status $Status -PercentComplete $pct
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
    try {
        if (Test-Path -LiteralPath $Path) {
            return @(Import-Csv -LiteralPath $Path)
        }
    } catch {
        def_Log "WARN" "CSV load failed: $Path :: $($_.Exception.Message)" Yellow
    }
    return @()
}

function def_LoadJson {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {
        return $null
    }
    return $null
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

function def_GetLatestV0113A {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113A_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113A_ROOT) {
            return $def_PARAM_V0113A_ROOT
        }
        throw "Specified v0113A root does not exist: $def_PARAM_V0113A_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113A_secretmask_accept_suggestion"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113A output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113A_SecretMask_AcceptSuggestion_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113A output found under: $root"
    }

    return $candidates[0].FullName
}

function def_ClassifySecretRisk {
    param(
        [string]$Key,
        [string]$Owner,
        [string]$Family,
        [string]$MaskedSample
    )

    $k = (def_S $Key).Trim()
    $kl = $k.ToLowerInvariant()
    $s = (def_S $MaskedSample)
    $sl = $s.ToLowerInvariant()

    $class = "REVIEW"
    $block = "true"
    $action = "MANUAL_SECRET_REVIEW_REQUIRED"
    $reason = "Conservative default: keep blocked until reviewed."

    if ($s -match "\*\*\*MASKED_SECRET\*\*\*") {
        $class = "TRUE_SECRET_OR_RAW_VALUE_PRESENT"
        $block = "true"
        $action = "ROTATE_IF_REAL_AND_USE_ENV_OR_SECRET_STORE"
        $reason = "Masked raw-looking secret was detected. Never write this value into canonical registry."
    }
    elseif ($kl -eq "fred_api_key" -or $kl -eq "fred_api_key_env") {
        $class = "ENV_SECRET_REFERENCE"
        $block = "true"
        $action = "CONFIRM_ENV_ONLY_NO_RAW_VALUE"
        $reason = "API-key related key. Keep blocked until confirmed as env-only."
    }
    elseif ($kl -in @("fred_keys","fred_api_key_exists","fred_api_key_sources_checked","fred_api_key_value_not_printed")) {
        $class = "ENV_REFERENCE_OR_BOOLEAN_FLAG"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "Looks like env key names or boolean capability flags, not a raw credential."
    }
    elseif ($sl -match "\\_runs\\|\\_active\\|\\_freeze\\|\\_route_lock_runs\\|\\_vrn_operation_ui_runs\\|\\_vrn_integrated_trust_runs\\|\\dict\\|\\output\\|\\registry\\|\\parquet\\|\.csv|\.json|\.parquet") {
        $class = "FALSE_POSITIVE_PATH_OR_RUN_ID"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "Masked long token appears inside local path/RUN_ID/file name."
    }
    elseif ($kl -match "csv|json|path|dir|run|seal|matrix|schema_map|schema_audit|ticker_regex|unit_review|summary") {
        $class = "LIKELY_FALSE_POSITIVE_FILE_OR_REGISTRY_REFERENCE"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "Key name indicates file/registry/path reference rather than credential."
    }
    elseif ($kl -match "policy|hardgate|source_policy|mixing_policy|collision_policy") {
        $class = "LIKELY_FALSE_POSITIVE_POLICY_TEXT"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "Policy text or governance phrase was masked as long token."
    }
    elseif ($sl -match "env:|environment|環境變數|os\.environ|getenv") {
        $class = "ENV_REFERENCE_ONLY"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "References environment variable usage, not a printed raw value."
    }
    elseif ($s -match "\*\*\*MASKED_LONG_TOKEN\*\*\*") {
        $class = "MASKED_LONG_TOKEN_REVIEW_LIKELY_FALSE_POSITIVE"
        $block = "false"
        $action = "CLEAR_SECRET_BLOCK_KEEP_MANUAL_ACCEPT"
        $reason = "Long token was masked, but no raw secret marker detected."
    }

    return [pscustomobject][ordered]@{
        def_secret_class = $class
        def_secret_block = $block
        def_secret_action = $action
        def_secret_reason = $reason
    }
}

function def_BuildSecretTriage {
    param([array]$SecretReview)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $SecretReview) {
        $key = def_GetProp $r "def_normalized_key"
        $owner = def_GetProp $r "def_owner_engine"
        $family = def_GetProp $r "def_domain_family"
        $sample = def_GetProp $r "def_sample_values_masked"

        $c = def_ClassifySecretRisk -Key $key -Owner $owner -Family $family -MaskedSample $sample

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "SECRET_TRIAGE"
            def_normalized_key = $key
            def_owner_engine = $owner
            def_domain_family = $family
            def_secret_class = def_GetProp $c "def_secret_class"
            def_secret_block = def_GetProp $c "def_secret_block"
            def_secret_action = def_GetProp $c "def_secret_action"
            def_secret_reason = def_GetProp $c "def_secret_reason"
            def_user_accept = ""
            def_sample_values_masked = $sample
        })
    }

    return @($rows)
}

function def_BuildP0Refined {
    param(
        [array]$P0Suggestion,
        [array]$SecretTriage
    )

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Suggestion) {
        $key = def_GetProp $r "def_normalized_key"
        $match = @($SecretTriage | Where-Object { (def_GetProp $_ "def_normalized_key") -eq $key } | Select-Object -First 1)

        $secretClass = "NOT_SECRET_FLAGGED"
        $secretBlock = "false"
        $secretAction = "NO_SECRET_BLOCK"
        $secretReason = ""

        if (@($match).Count -gt 0) {
            $secretClass = def_GetProp $match[0] "def_secret_class"
            $secretBlock = def_GetProp $match[0] "def_secret_block"
            $secretAction = def_GetProp $match[0] "def_secret_action"
            $secretReason = def_GetProp $match[0] "def_secret_reason"
        }

        $suggest = def_GetProp $r "def_suggested_action"

        if ($secretBlock -eq "true") {
            $suggest = "SECRET_REVIEW_BEFORE_ACCEPT"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_accept_status = "WAIT_USER_DECISION"
            def_user_accept = ""
            def_suggested_action = $suggest
            def_secret_class = $secretClass
            def_secret_block = $secretBlock
            def_secret_action = $secretAction
            def_secret_reason = $secretReason
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_normalized_key = $key
            def_distinct_values = def_GetProp $r "def_distinct_values"
            def_selected_canonical_value = ""
            def_suggested_canonical_value = def_GetProp $r "def_suggested_canonical_value"
            def_reject_reason = ""
            def_next_allowed_phase = "v0114_only_after_MANUAL_YES_AND_SECRET_CLEAR"
            def_sample_values_masked = def_GetProp $r "def_sample_values_masked"
        })
    }

    return @($rows)
}

function def_BuildP1Refined {
    param([array]$P1Suggestion)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Suggestion) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_accept_status = "WAIT_USER_DECISION"
            def_user_accept = ""
            def_suggested_action = def_GetProp $r "def_suggested_action"
            def_recommendation = def_GetProp $r "def_recommendation"
            def_risk = def_GetProp $r "def_risk"
            def_alias = def_GetProp $r "def_alias"
            def_path_value = def_GetProp $r "def_path_value"
            def_status = def_GetProp $r "def_status"
            def_selected_alias_value = ""
            def_suggested_alias_value = def_GetProp $r "def_suggested_alias_value"
            def_reject_reason = ""
            def_suggestion_note = def_GetProp $r "def_suggestion_note"
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param(
        [array]$DirectBoard,
        [array]$P0Refined,
        [array]$P1Refined,
        [array]$SecretTriage
    )

    $directOk = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $secretBlock = @($SecretTriage | Where-Object { (def_GetProp $_ "def_secret_block") -eq "true" }).Count
    $secretClear = @($SecretTriage | Where-Object { (def_GetProp $_ "def_secret_block") -ne "true" }).Count

    $p0Yes = @($P0Refined | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Refined | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED"
    $allow = "false"
    $reason = "Secret triage completed. User accept fields remain blank."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct smoke has review rows."
    }
    elseif ($secretBlock -gt 0) {
        $gate = "BLOCKED_TRUE_SECRET_REVIEW_REQUIRED"
        $reason = "True secret or env-secret reference remains. Confirm env-only or rotate if raw value was real."
    }
    else {
        $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED_SECRET_TRIAGE_CLEARED"
        $reason = "Secret blocker cleared except manual P0/P1 acceptance. No automatic YES."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_secret_block = "$secretBlock"
            def_secret_clear = "$secretClear"
            def_p0_yes = "$p0Yes"
            def_p0_total = "$(@($P0Refined).Count)"
            def_p1_yes = "$p1Yes"
            def_p1_total = "$(@($P1Refined).Count)"
            def_next_allowed_phase = "v0114 sandbox patch candidate only after manual YES"
        }
    )
}

function def_BuildV0114Precheck {
    param(
        [string]$P0Csv,
        [string]$P1Csv,
        [string]$SecretTriageCsv,
        [string]$Path
    )

    $code = @"
`$ErrorActionPreference = "Stop"

`$P0Csv = "$P0Csv"
`$P1Csv = "$P1Csv"
`$SecretTriageCsv = "$SecretTriageCsv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$p0 = def_Load `$P0Csv
`$p1 = def_Load `$P1Csv
`$sec = def_Load `$SecretTriageCsv

`$secretBlock = @(`$sec | Where-Object { ([string]`$_.def_secret_block).Trim().ToLowerInvariant() -eq "true" }).Count
`$p0Pending = @(`$p0 | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending = @(`$p1 | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck after v0113B" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret blockers : `$secretBlock" -ForegroundColor Yellow
Write-Host "P0 pending      : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending      : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secretBlock -gt 0) {
    throw "BLOCKED_TRUE_SECRET_REVIEW_REQUIRED. Resolve/confirm env-only/rotate before v0114."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 refined CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_BuildNextCommands {
    param(
        [string]$RunDir,
        [string]$P0Edit,
        [string]$P1Edit,
        [string]$SecretTriage,
        [string]$Precheck
    )

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0113B
# =============================================================================

Start-Process "$RunDir\report\VIA_v0113B_SecretTriage_ManualGate_Report.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_user_edit_refined"

# Review secret split
Import-Csv "$SecretTriage" | Format-Table -AutoSize

# Review readiness
Import-Csv "$RunDir\output\VIA_v0113B_ReadinessGate.csv" | Format-Table -AutoSize

# Open refined edit boards
Start-Process "$P0Edit"
Start-Process "$P1Edit"

# After manual review/edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$Precheck"

# Only after precheck returns OK:
# v0114 may generate sandbox patch candidate.
# Still no canonical overwrite.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113B.ps1"
    Set-Content -LiteralPath $path -Value $cmd -Encoding UTF8
    return $path
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=120)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) { [void]$sb.Append("<th>$(def_Html $c)</th>") }
    [void]$sb.Append("</tr></thead><tbody>")

    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = def_GetProp $r $c
            if ($v.Length -gt 260) { $v = $v.Substring(0,260) + "..." }
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
        [array]$SecretTriage,
        [array]$P0Refined,
        [array]$P1Refined,
        [array]$DirectBoard,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114",$Summary.AllowV0114),
        @("Direct OK",$Summary.DirectOk),
        @("Secret Block",$Summary.SecretBlock),
        @("Secret Clear",$Summary.SecretClear),
        @("P0 Rows",$Summary.P0Rows),
        @("P1 Rows",$Summary.P1Rows)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113B Secret Triage Manual Gate</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0;--cyan:#6fa8ad}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 10% 5%,rgba(111,168,173,.14),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.5),rgba(230,226,216,.2)),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.5px;line-height:1.32}
.wrap{max-width:1780px;margin:0 auto;padding:15px}
h1{font-size:14.4px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:var(--mut);margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:var(--mut)}
.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-items:stretch}
.sec{background:rgba(255,254,250,.9);border:1px solid var(--line);border-radius:11px;padding:8px;min-height:214px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:var(--mut);margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.85px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:var(--mut)}
.footer{margin-top:11px;color:var(--mut);font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA v0113B Secret False-Positive Triage + Manual Gate Refinement</h1>
<div class="sub">True secret blocker isolation · false-positive path/RUN_ID split · no auto accept · no mutation</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0113A 的 24 筆 Secret Review 經 v0113B 拆成 true secret blockers 與 false-positive path/RUN_ID/policy/env references。即使 Secret Block=0，P0/P1 仍必須人工填 YES 才能進 v0114；本輪不自動接受。
</div>
<div>
<span class="tag">No Auto YES</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">Secret Triage</span>
<span class="tag">Manual Gate Required</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_secret_block","def_secret_clear","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_next_allowed_phase") 20)</div>
<div class="sec wide"><h2>def Secret Triage</h2>$(def_Table $SecretTriage @("def_priority","def_normalized_key","def_owner_engine","def_domain_family","def_secret_class","def_secret_block","def_secret_action","def_secret_reason","def_user_accept","def_sample_values_masked") 120)</div>
<div class="sec wide"><h2>def Direct Smoke Board</h2>$(def_Table $DirectBoard @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_review_reason","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 40)</div>
<div class="sec wide"><h2>def P0 Refined Manual Gate</h2>$(def_Table $P0Refined @("def_priority","def_accept_status","def_user_accept","def_suggested_action","def_secret_class","def_secret_block","def_owner_engine","def_domain_family","def_normalized_key","def_selected_canonical_value","def_suggested_canonical_value","def_reject_reason","def_sample_values_masked") 180)</div>
<div class="sec wide"><h2>def P1 Refined Manual Gate</h2>$(def_Table $P1Refined @("def_priority","def_accept_status","def_user_accept","def_suggested_action","def_recommendation","def_risk","def_alias","def_path_value","def_selected_alias_value","def_suggested_alias_value","def_reject_reason") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113A source: $(def_Html $Summary.LatestV0113A)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit refined: $(def_Html $Summary.UserEditDir)<br/>
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
    Write-Host "def VIA · v0113B SECRET TRIAGE + MANUAL GATE REFINEMENT" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Find latest v0113A output"
    $latest = def_GetLatestV0113A
    $latestOut = Join-Path $latest "output"
    def_Log "OK" "Latest v0113A: $latest" Green

    def_Progress 2 9 "Load v0113A boards"
    $summaryV0113A = def_LoadJson (Join-Path $latestOut "VIA_v0113A_SecretMask_AcceptSuggestion_Summary.json")
    $directBoard = def_LoadCsv (Join-Path $latestOut "VIA_v0113A_DirectSmokeBoard_From_v0113.csv")
    $secretReview = def_LoadCsv (Join-Path $latestOut "VIA_v0113A_SecretReview.csv")
    $p0Suggestion = def_LoadCsv (Join-Path $latestOut "VIA_v0113A_P0_SuggestionBoard_SANITIZED.csv")
    $p1Suggestion = def_LoadCsv (Join-Path $latestOut "VIA_v0113A_P1_PathAliasSuggestionBoard.csv")
    def_Log "OK" "Loaded Direct=$(@($directBoard).Count), Secret=$(@($secretReview).Count), P0=$(@($p0Suggestion).Count), P1=$(@($p1Suggestion).Count)" Green

    def_Progress 3 9 "Classify secret false positives"
    $secretTriage = def_BuildSecretTriage -SecretReview $secretReview

    def_Progress 4 9 "Build P0 refined manual gate"
    $p0Refined = def_BuildP0Refined -P0Suggestion $p0Suggestion -SecretTriage $secretTriage

    def_Progress 5 9 "Build P1 refined manual gate"
    $p1Refined = def_BuildP1Refined -P1Suggestion $p1Suggestion

    def_Progress 6 9 "Build readiness gate"
    $readiness = def_BuildReadiness -DirectBoard $directBoard -P0Refined $p0Refined -P1Refined $p1Refined -SecretTriage $secretTriage

    def_Progress 7 9 "Write refined user-edit CSVs and precheck"
    $p0Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113B_USER_EDIT_P0_RefinedManualGate.csv"
    $p1Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113B_USER_EDIT_P1_RefinedManualGate.csv"
    $secretTriageCsv = Join-Path $def_OUTPUT_DIR "VIA_v0113B_SecretTriage.csv"

    def_WriteCsv $p0Refined $p0Edit
    def_WriteCsv $p1Refined $p1Edit
    def_WriteCsv $secretTriage $secretTriageCsv

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-Precheck-After-v0113B.ps1"
    def_BuildV0114Precheck -P0Csv $p0Edit -P1Csv $p1Edit -SecretTriageCsv $secretTriageCsv -Path $precheck

    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -P0Edit $p0Edit -P1Edit $p1Edit -SecretTriage $secretTriageCsv -Precheck $precheck

    def_Progress 8 9 "Write CSV/JSON outputs"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $p0Refined (Join-Path $def_OUTPUT_DIR "VIA_v0113B_P0_RefinedManualGate.csv")
    def_WriteCsv $p1Refined (Join-Path $def_OUTPUT_DIR "VIA_v0113B_P1_RefinedManualGate.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113B_ReadinessGate.csv")
    def_WriteCsv $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113B_DirectSmokeBoard_From_v0113A.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0113B_PS15_Accelerators.csv")

    def_WriteJson $secretTriage (Join-Path $def_OUTPUT_DIR "VIA_v0113B_SecretTriage.json")
    def_WriteJson $p0Refined (Join-Path $def_OUTPUT_DIR "VIA_v0113B_P0_RefinedManualGate.json")
    def_WriteJson $p1Refined (Join-Path $def_OUTPUT_DIR "VIA_v0113B_P1_RefinedManualGate.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113B_ReadinessGate.json")

    $directOk = @($directBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretBlock = @($secretTriage | Where-Object { (def_GetProp $_ "def_secret_block") -eq "true" }).Count
    $secretClear = @($secretTriage | Where-Object { (def_GetProp $_ "def_secret_block") -ne "true" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE_READY"
        RunId = $def_RUN_ID
        LatestV0113A = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        DirectOk = "$directOk"
        SecretRows = "$(@($secretTriage).Count)"
        SecretBlock = "$secretBlock"
        SecretClear = "$secretClear"
        P0Rows = "$(@($p0Refined).Count)"
        P1Rows = "$(@($p1Refined).Count)"
        AutoAccept = "false"
        P0EditCsv = $p0Edit
        P1EditCsv = $p1Edit
        SecretTriageCsv = $secretTriageCsv
        Precheck = $precheck
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; no auto accept."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113B_SecretTriage_ManualGate_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_v0113B_SecretTriage_ManualGate_Report.html"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -SecretTriage $secretTriage `
        -P0Refined $p0Refined `
        -P1Refined $p1Refined `
        -DirectBoard $directBoard `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113B Secret Triage Manual Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113B Secret Triage + Manual Gate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status       : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate         : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114  : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Direct OK    : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "Secret Block : $($summary.SecretBlock)" -ForegroundColor Yellow
    Write-Host "Secret Clear : $($summary.SecretClear)" -ForegroundColor Green
    Write-Host "P0 Rows      : $($summary.P0Rows)" -ForegroundColor Gray
    Write-Host "P1 Rows      : $($summary.P1Rows)" -ForegroundColor Gray
    Write-Host "P0 Edit      : $p0Edit" -ForegroundColor Cyan
    Write-Host "P1 Edit      : $p1Edit" -ForegroundColor Cyan
    Write-Host "Secret CSV   : $secretTriageCsv" -ForegroundColor Cyan
    Write-Host "Precheck     : $precheck" -ForegroundColor Cyan
    Write-Host "Report       : $report" -ForegroundColor Cyan
    Write-Host "Output       : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd      : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try { Start-Process -FilePath $report } catch {}
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
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed." -ForegroundColor Yellow
    exit 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
