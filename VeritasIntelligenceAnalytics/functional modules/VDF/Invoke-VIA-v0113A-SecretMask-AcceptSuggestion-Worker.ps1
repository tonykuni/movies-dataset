param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
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

$def_RUN_ID = "RUN_{0}_VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113A_secretmask_accept_suggestion"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_sanitized"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113A_SecretMask_AcceptSuggestion.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0113 auto discovery",
    "A02 no BASE re-scan",
    "A03 secret/API-key masking",
    "A04 P0 suggestion classification",
    "A05 P1 path alias suggestion classification",
    "A06 user_accept kept blank",
    "A07 no automatic YES",
    "A08 sanitized editable CSV generation",
    "A09 secret leak review matrix",
    "A10 v0114 remains blocked until manual edit",
    "A11 no source mutation",
    "A12 no canonical merge",
    "A13 no DB write",
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
    Write-Progress -Activity "VIA v0113A SecretMask AcceptSuggestion" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113_ROOT) {
            return $def_PARAM_V0113_ROOT
        }
        throw "Specified v0113 root does not exist: $def_PARAM_V0113_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_seventhstep_accept_gate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_SeventhStep_AcceptGateBoard_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_MaskSecrets {
    param([string]$Text)

    $s = def_S $Text

    $s = [regex]::Replace($s, '(?i)(FRED_API_KEY\s*=\s*["'']?)[A-Za-z0-9_\-]{16,}(["'']?)', '$1***MASKED_SECRET***$2')
    $s = [regex]::Replace($s, '(?i)((api[_-]?key|token|secret|password|passwd|credential)\s*[:=]\s*["'']?)[A-Za-z0-9_\-\.]{12,}(["'']?)', '$1***MASKED_SECRET***$3')
    $s = [regex]::Replace($s, '\b[a-fA-F0-9]{32,}\b', '***MASKED_HEX_SECRET***')
    $s = [regex]::Replace($s, '\b[A-Za-z0-9_\-]{40,}\b', '***MASKED_LONG_TOKEN***')

    return $s
}

function def_HasSecretRisk {
    param([string]$Text)

    $s = def_S $Text

    if ($s -match '(?i)api[_-]?key|token|secret|password|passwd|credential') { return $true }
    if ($s -match '\b[a-fA-F0-9]{32,}\b') { return $true }
    if ($s -match '\b[A-Za-z0-9_\-]{48,}\b') { return $true }

    return $false
}

function def_SuggestP0 {
    param($Row)

    $family = def_GetProp $Row "def_domain_family"
    $owner  = def_GetProp $Row "def_owner_engine"
    $key    = def_GetProp $Row "def_normalized_key"
    $sample = def_GetProp $Row "def_sample_values"

    $suggest = "REVIEW"
    $canonical = ""
    $note = "Manual decision required."

    if (def_HasSecretRisk $sample) {
        $suggest = "MASK_SECRET_AND_DEFER"
        $canonical = "USE_ENV_VAR_OR_SECRET_STORE; DO_NOT_PRINT_VALUE"
        $note = "Potential secret/API key appears in sample values. Rotate key if real; do not propagate into canonical registry."
    } elseif ($family -eq "MARKET_TICKER_IDENTITY") {
        $suggest = "ACCEPT_GROUP_POLICY_AFTER_REVIEW"
        $canonical = "TW_TICKER=4_DIGITS; TWSE_YF={TW_TICKER}.TW; TPEX_YF={TW_TICKER}.TWO; OVERSEAS=PROVIDER_NATIVE_TICKER"
        $note = "Accept as policy group, not each observed sample value."
    } elseif ($family -eq "DATA_SOURCE_CONTRACT") {
        $suggest = "ACCEPT_PROVIDER_CONTRACT_AFTER_REVIEW"
        $canonical = "PROVIDER_REGISTRY_ONLY; API_KEYS_FROM_ENV; FALLBACK_EXPLICIT"
        $note = "Accept only provider contract and env-key policy. Do not accept raw credentials."
    } elseif ($family -eq "SCHEMA_FIELD_CONTRACT") {
        $suggest = "ACCEPT_SCHEMA_OWNER_AFTER_REVIEW"
        $canonical = "OWNER_SCHEMA_REGISTRY; FIELD_ALIAS_MAP; UNIT_NORMALIZATION_TABLE"
        $note = "Accept schema ownership, not every conflicting field value."
    } elseif ($family -eq "GOVERNANCE_POLICY") {
        $suggest = "ACCEPT_POLICY_OWNER_AFTER_REVIEW"
        $canonical = "VIA_GOVERNANCE_POLICY_REGISTRY"
        $note = "Policy should remain registry-owned; no auto merge."
    } elseif ($family -eq "VISUAL_LOCK") {
        $suggest = "DEFER_TO_VISUAL_LOCK"
        $canonical = "VISUAL_LOCK_REGISTRY_ONLY"
        $note = "Visual conflicts should not block data/engine integration."
    } elseif ($family -eq "ENGINE_INTERFACE") {
        $suggest = "REVIEW_ENGINE_INTERFACE"
        $canonical = "ADAPTER_CONTRACT_ONLY"
        $note = "Engine interfaces need adapter bridge, not direct rewrite."
    }

    return [pscustomobject][ordered]@{
        def_suggested_action = $suggest
        def_suggested_canonical_value = $canonical
        def_suggestion_note = $note
    }
}

function def_SuggestP1 {
    param($Row)

    $alias = def_GetProp $Row "def_alias"
    $path  = def_GetProp $Row "def_path_value"
    $status = def_GetProp $Row "def_status"

    $suggest = "REVIEW"
    $selected = ""
    $note = "Manual path decision required."

    if ($alias -in @("VIA_ROOT_DOWNLOADS","VDF_DIR_DOWNLOADS","FUNCTIONAL_MODULES_DOWNLOADS","SUPPORTIVE_MODULES_DOWNLOADS")) {
        $suggest = "ACCEPT_RECOMMENDED"
        $selected = $path
        $note = "Canonical active Downloads root."
    } elseif ($alias -eq "USER_DOWNLOADS") {
        $suggest = "ACCEPT_AS_REFERENCE_ONLY"
        $selected = $path
        $note = "Reference root only; avoid using as canonical module root."
    } elseif ($alias -match "ONEDRIVE|LEGACY") {
        $suggest = "DEFER_OR_REJECT"
        $selected = ""
        $note = "Legacy/OneDrive root should not be canonical unless still required."
    } elseif ($alias -match "PYTHON_ENV") {
        $suggest = "DEFER_ENV_REVIEW"
        $selected = ""
        $note = "Environment path should be resolved by EnvManager, not hard-coded as canonical."
    } elseif ($status -match "REVIEW_ALIAS" -and $path -match "\\dict\\VDF\\_active\\") {
        $suggest = "REJECT_RUN_SPECIFIC_PATH"
        $selected = ""
        $note = "Run-specific active path; do not promote to alias root."
    }

    return [pscustomobject][ordered]@{
        def_suggested_action = $suggest
        def_suggested_alias_value = $selected
        def_suggestion_note = $note
    }
}

function def_BuildP0SuggestionBoard {
    param([array]$P0Board)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Board) {
        $sug = def_SuggestP0 $r
        $sample = def_GetProp $r "def_sample_values"
        $masked = def_MaskSecrets $sample
        $secretRisk = def_HasSecretRisk $sample

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_gate_type = def_GetProp $r "def_gate_type"
            def_accept_status = "WAIT_USER_DECISION"
            def_user_accept = ""
            def_suggested_action = def_GetProp $sug "def_suggested_action"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_distinct_values = def_GetProp $r "def_distinct_values"
            def_selected_canonical_value = ""
            def_suggested_canonical_value = def_GetProp $sug "def_suggested_canonical_value"
            def_reject_reason = ""
            def_secret_risk = def_S $secretRisk
            def_suggestion_note = def_GetProp $sug "def_suggestion_note"
            def_next_allowed_phase = "v0114_only_after_MANUAL_YES"
            def_sample_values_masked = $masked
        })
    }

    return @($rows)
}

function def_BuildP1SuggestionBoard {
    param([array]$P1Board)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Board) {
        $sug = def_SuggestP1 $r

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = def_GetProp $r "def_priority"
            def_gate_type = def_GetProp $r "def_gate_type"
            def_accept_status = "WAIT_USER_DECISION"
            def_user_accept = ""
            def_suggested_action = def_GetProp $sug "def_suggested_action"
            def_recommendation = def_GetProp $r "def_recommendation"
            def_risk = def_GetProp $r "def_risk"
            def_alias = def_GetProp $r "def_alias"
            def_path_value = def_GetProp $r "def_path_value"
            def_status = def_GetProp $r "def_status"
            def_selected_alias_value = ""
            def_suggested_alias_value = def_GetProp $sug "def_suggested_alias_value"
            def_reject_reason = ""
            def_suggestion_note = def_GetProp $sug "def_suggestion_note"
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
        })
    }

    return @($rows)
}

function def_BuildSecretReview {
    param([array]$P0Suggestion)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Suggestion) {
        if ((def_GetProp $r "def_secret_risk") -eq "True") {
            [void]$rows.Add([pscustomobject][ordered]@{
                def_priority = "SECRET_REVIEW"
                def_normalized_key = def_GetProp $r "def_normalized_key"
                def_owner_engine = def_GetProp $r "def_owner_engine"
                def_domain_family = def_GetProp $r "def_domain_family"
                def_action = "MASKED_IN_v0113A_OUTPUT; ROTATE_IF_REAL; USE_ENV_OR_SECRET_STORE"
                def_user_accept = ""
                def_sample_values_masked = def_GetProp $r "def_sample_values_masked"
            })
        }
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$DirectBoard,[array]$P0Suggestion,[array]$P1Suggestion)

    $directOk = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $p0Yes = @($P0Suggestion | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Suggestion | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $p0Total = @($P0Suggestion).Count
    $p1Total = @($P1Suggestion).Count

    $secretRows = @($P0Suggestion | Where-Object { (def_GetProp $_ "def_secret_risk") -eq "True" }).Count

    $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED"
    $allow = "false"
    $reason = "Suggestions generated, but user_accept remains blank by policy."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct contract smoke has review rows."
    } elseif ($secretRows -gt 0) {
        $gate = "BLOCKED_SECRET_REVIEW_REQUIRED"
        $reason = "Potential secret/API key detected in P0 samples. Masked output generated; rotate key if real."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_p0_yes = "$p0Yes"
            def_p0_total = "$p0Total"
            def_p1_yes = "$p1Yes"
            def_p1_total = "$p1Total"
            def_secret_review_rows = "$secretRows"
            def_next_allowed_phase = "v0114 sandbox patch candidate only after manual YES and secret review"
        }
    )
}

function def_BuildNextCommands {
    param(
        [string]$RunDir,
        [string]$P0Edit,
        [string]$P1Edit,
        [string]$SecretReview
    )

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0113A
# =============================================================================

Start-Process "$RunDir\report\VIA_v0113A_SecretMask_AcceptSuggestion_Report.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_user_edit_sanitized"

# Review safe boards
Import-Csv "$RunDir\output\VIA_v0113A_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$SecretReview" | Format-Table -AutoSize

# Open editable sanitized CSVs
Start-Process "$P0Edit"
Start-Process "$P1Edit"

# Important:
# Keep def_user_accept blank until you manually decide.
# Do not set all rows to YES automatically.
# For secret rows, rotate external key if the value was real.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113A.ps1"
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
        [array]$SecretReview,
        [array]$P0Suggestion,
        [array]$P1Suggestion,
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
        @("P0 Rows",$Summary.P0Rows),
        @("P1 Rows",$Summary.P1Rows),
        @("Secret Review",$Summary.SecretReviewRows),
        @("Auto Accept","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113A SecretMask AcceptSuggestion</title>
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
<h1>def VIA v0113A Secret Mask + Accept Suggestion Review Pack</h1>
<div class="sub">Sanitized manual gate · no auto accept · no mutation · no canonical merge</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0113 的 BLOCKED 狀態是正確的。v0113A 只做遮罩與建議，不自動填 YES。若 Secret Review Rows 大於 0，先處理外部 key 風險，再決定 P0/P1 是否接受。
</div>
<div>
<span class="tag">No Auto YES</span>
<span class="tag">Secrets Masked</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">Manual Gate Required</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_secret_review_rows","def_next_allowed_phase") 20)</div>
<div class="sec wide"><h2>def Secret Review</h2>$(def_Table $SecretReview @("def_priority","def_normalized_key","def_owner_engine","def_domain_family","def_action","def_user_accept","def_sample_values_masked") 80)</div>
<div class="sec wide"><h2>def Direct Smoke Board</h2>$(def_Table $DirectBoard @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_review_reason","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 80)</div>
<div class="sec wide"><h2>def P0 Suggestion Board</h2>$(def_Table $P0Suggestion @("def_priority","def_accept_status","def_user_accept","def_suggested_action","def_owner_engine","def_domain_family","def_normalized_key","def_distinct_values","def_selected_canonical_value","def_suggested_canonical_value","def_secret_risk","def_suggestion_note","def_sample_values_masked") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Suggestion Board</h2>$(def_Table $P1Suggestion @("def_priority","def_accept_status","def_user_accept","def_suggested_action","def_recommendation","def_risk","def_alias","def_path_value","def_status","def_selected_alias_value","def_suggested_alias_value","def_suggestion_note") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113 source: $(def_Html $Summary.LatestV0113)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit sanitized: $(def_Html $Summary.UserEditDir)<br/>
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
    Write-Host "def VIA · v0113A SECRET MASK + ACCEPT SUGGESTION REVIEW PACK" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Find latest v0113 output"
    $latest = def_GetLatestV0113
    $latestOut = Join-Path $latest "output"
    $latestGate = Join-Path $latest "_accept_gate_user_edit"
    def_Log "OK" "Latest v0113: $latest" Green

    def_Progress 2 9 "Load v0113 boards"
    $summaryV0113 = def_LoadJson (Join-Path $latestOut "VIA_SeventhStep_AcceptGateBoard_Summary.json")
    $directBoard = def_LoadCsv (Join-Path $latestOut "VIA_v0113_DirectSmokeBoard.csv")
    $p0Board = def_LoadCsv (Join-Path $latestOut "VIA_v0113_P0_ManualAcceptBoard.csv")
    $p1Board = def_LoadCsv (Join-Path $latestOut "VIA_v0113_P1_PathAliasAcceptBoard.csv")
    def_Log "OK" "Loaded Direct=$(@($directBoard).Count), P0=$(@($p0Board).Count), P1=$(@($p1Board).Count)" Green

    def_Progress 3 9 "Build P0 sanitized suggestion board"
    $p0Suggestion = def_BuildP0SuggestionBoard -P0Board $p0Board

    def_Progress 4 9 "Build P1 path alias suggestion board"
    $p1Suggestion = def_BuildP1SuggestionBoard -P1Board $p1Board

    def_Progress 5 9 "Build secret review"
    $secretReview = def_BuildSecretReview -P0Suggestion $p0Suggestion

    def_Progress 6 9 "Build readiness gate"
    $readiness = def_BuildReadiness -DirectBoard $directBoard -P0Suggestion $p0Suggestion -P1Suggestion $p1Suggestion

    def_Progress 7 9 "Write sanitized user-edit CSVs"
    $p0Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113A_USER_EDIT_P0_Suggestion_SANITIZED.csv"
    $p1Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113A_USER_EDIT_P1_PathAlias_Suggestion.csv"
    $secretCsv = Join-Path $def_OUTPUT_DIR "VIA_v0113A_SecretReview.csv"

    def_WriteCsv $p0Suggestion $p0Edit
    def_WriteCsv $p1Suggestion $p1Edit
    def_WriteCsv $secretReview $secretCsv

    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -P0Edit $p0Edit -P1Edit $p1Edit -SecretReview $secretCsv

    def_Progress 8 9 "Write CSV/JSON outputs"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $p0Suggestion (Join-Path $def_OUTPUT_DIR "VIA_v0113A_P0_SuggestionBoard_SANITIZED.csv")
    def_WriteCsv $p1Suggestion (Join-Path $def_OUTPUT_DIR "VIA_v0113A_P1_PathAliasSuggestionBoard.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113A_ReadinessGate.csv")
    def_WriteCsv $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113A_DirectSmokeBoard_From_v0113.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0113A_PS15_Accelerators.csv")

    def_WriteJson $p0Suggestion (Join-Path $def_OUTPUT_DIR "VIA_v0113A_P0_SuggestionBoard_SANITIZED.json")
    def_WriteJson $p1Suggestion (Join-Path $def_OUTPUT_DIR "VIA_v0113A_P1_PathAliasSuggestionBoard.json")
    def_WriteJson $secretReview (Join-Path $def_OUTPUT_DIR "VIA_v0113A_SecretReview.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113A_ReadinessGate.json")

    $directOk = @($directBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretRows = @($secretReview).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113A_SECRETMASK_ACCEPT_SUGGESTION_READY"
        RunId = $def_RUN_ID
        LatestV0113 = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        DirectOk = "$directOk"
        P0Rows = "$(@($p0Suggestion).Count)"
        P1Rows = "$(@($p1Suggestion).Count)"
        SecretReviewRows = "$secretRows"
        AutoAccept = "false"
        P0EditCsv = $p0Edit
        P1EditCsv = $p1Edit
        SecretReviewCsv = $secretCsv
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; suggestions only; user_accept remains blank."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113A_SecretMask_AcceptSuggestion_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_v0113A_SecretMask_AcceptSuggestion_Report.html"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -SecretReview $secretReview `
        -P0Suggestion $p0Suggestion `
        -P1Suggestion $p1Suggestion `
        -DirectBoard $directBoard `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113A SecretMask AcceptSuggestion" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113A Secret Mask + Accept Suggestion COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status       : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate         : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114  : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Direct OK    : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "P0 Rows      : $($summary.P0Rows)" -ForegroundColor Gray
    Write-Host "P1 Rows      : $($summary.P1Rows)" -ForegroundColor Gray
    Write-Host "Secret Rows  : $($summary.SecretReviewRows)" -ForegroundColor Yellow
    Write-Host "P0 Edit      : $p0Edit" -ForegroundColor Cyan
    Write-Host "P1 Edit      : $p1Edit" -ForegroundColor Cyan
    Write-Host "Secret CSV   : $secretCsv" -ForegroundColor Cyan
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
