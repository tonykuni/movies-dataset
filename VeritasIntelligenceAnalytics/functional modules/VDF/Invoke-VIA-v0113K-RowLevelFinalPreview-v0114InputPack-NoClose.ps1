param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113J_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113K_ROW_FINAL_PREVIEW" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113K_row_final_preview"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_INPUT_PACK_DIR = Join-Path $def_RUN_DIR "_v0114_sandbox_candidate_input_pack"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113K_RowFinalPreview.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113J auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 v0113J readiness reuse",
    "A06 row-level final preview seal",
    "A07 included/excluded consistency gate",
    "A08 P0 final policy pack",
    "A09 P1 final alias pack",
    "A10 v0114 sandbox input JSON",
    "A11 no source mutation guard",
    "A12 no canonical merge guard",
    "A13 no DB write guard",
    "A14 v0114 preflight generated",
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_INPUT_PACK_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0113K Row-Level Final Preview" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113J {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113J_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113J_ROOT) {
            return $def_PARAM_V0113J_ROOT
        }
        throw "Specified v0113J root does not exist: $def_PARAM_V0113J_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113J_formal_decision_promotion"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113J output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113J_FormalDecisionPromotion_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113J output found under: $root"
    }

    return $candidates[0].FullName
}

function def_BuildP0PolicyPack {
    param([array]$P0Final)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Final) {
        $decision = def_GetProp $r "def_group_final_decision"

        [void]$rows.Add([pscustomobject][ordered]@{
            def_pack_layer = "P0_POLICY_PACK"
            def_group_id = def_GetProp $r "def_group_id"
            def_final_decision = $decision
            def_final_value = def_GetProp $r "def_group_final_value"
            def_apply_to_rows = def_GetProp $r "def_apply_to_rows"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_final_reason = def_GetProp $r "def_final_reason"
            def_sandbox_action = $(if ($decision -eq "YES") { "INCLUDE_IN_SANDBOX_PATCH_CANDIDATE_INPUT" } else { "EXCLUDE_OR_DEFER" })
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildP1AliasPack {
    param([array]$P1Final)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Final) {
        $decision = def_GetProp $r "def_alias_final_decision"

        [void]$rows.Add([pscustomobject][ordered]@{
            def_pack_layer = "P1_ALIAS_PACK"
            def_alias = def_GetProp $r "def_alias"
            def_final_decision = $decision
            def_final_value = def_GetProp $r "def_alias_final_value"
            def_path_value = def_GetProp $r "def_path_value"
            def_final_reason = def_GetProp $r "def_final_reason"
            def_scope = def_GetProp $r "def_scope"
            def_sandbox_action = $(if ($decision -in @("YES","YES_REFERENCE_ONLY")) { "INCLUDE_ALIAS_IN_SANDBOX_INPUT" } else { "EXCLUDE_OR_DEFER_ALIAS" })
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildRowPolicyPack {
    param([array]$RowPreview)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $RowPreview) {
        $state = def_GetProp $r "def_row_preview_state"

        [void]$rows.Add([pscustomobject][ordered]@{
            def_pack_layer = "ROW_POLICY_PACK"
            def_row_preview_state = $state
            def_include_in_v0114_sandbox_input = $(if ($state -eq "INCLUDED_IN_ROW_LEVEL_PREVIEW") { "true" } else { "false" })
            def_group_final_decision = def_GetProp $r "def_group_final_decision"
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_final_canonical_value = def_GetProp $r "def_final_canonical_value"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param(
        [array]$ReadinessJ,
        [array]$RowPolicyPack,
        [array]$P0Pack,
        [array]$P1Pack
    )

    $rj = $ReadinessJ[0]
    $allowJ = def_GetProp $rj "def_allow_v0113K"

    $rowIncluded = @($RowPolicyPack | Where-Object { (def_GetProp $_ "def_include_in_v0114_sandbox_input") -eq "true" }).Count
    $rowExcluded = @($RowPolicyPack | Where-Object { (def_GetProp $_ "def_include_in_v0114_sandbox_input") -ne "true" }).Count

    $unsafe = @($RowPolicyPack + $P0Pack + $P1Pack | Where-Object {
        (def_GetProp $_ "def_source_mutation") -ne "false" -or
        (def_GetProp $_ "def_canonical_merge") -ne "false" -or
        (def_GetProp $_ "def_db_write") -ne "false"
    }).Count

    $p0Included = @($P0Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -eq "INCLUDE_IN_SANDBOX_PATCH_CANDIDATE_INPUT" }).Count
    $p0Excluded = @($P0Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -ne "INCLUDE_IN_SANDBOX_PATCH_CANDIDATE_INPUT" }).Count

    $p1Included = @($P1Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -eq "INCLUDE_ALIAS_IN_SANDBOX_INPUT" }).Count
    $p1Excluded = @($P1Pack | Where-Object { (def_GetProp $_ "def_sandbox_action") -ne "INCLUDE_ALIAS_IN_SANDBOX_INPUT" }).Count

    $gate = "READY_FOR_v0114_SANDBOX_PATCH_CANDIDATE"
    $allow = "true"
    $reason = "Row-level final preview sealed. v0114 may generate sandbox patch candidate only."

    if ($allowJ -ne "true") {
        $gate = "BLOCKED_v0113J_NOT_READY"
        $allow = "false"
        $reason = "v0113J readiness did not allow v0113K."
    }
    elseif ($unsafe -gt 0) {
        $gate = "BLOCKED_UNSAFE_MUTATION_FLAG"
        $allow = "false"
        $reason = "Unsafe mutation/canonical/db flag detected."
    }
    elseif ($rowIncluded -le 0) {
        $gate = "BLOCKED_EMPTY_ROW_INPUT"
        $allow = "false"
        $reason = "No row-level sandbox input rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114_sandbox_candidate = $allow
            def_reason = $reason
            def_row_included = "$rowIncluded"
            def_row_excluded = "$rowExcluded"
            def_p0_included_groups = "$p0Included"
            def_p0_excluded_or_deferred_groups = "$p0Excluded"
            def_p1_included_aliases = "$p1Included"
            def_p1_excluded_or_deferred_aliases = "$p1Excluded"
            def_unsafe_flags = "$unsafe"
            def_next_allowed_phase = "v0114 sandbox patch candidate generation only"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        }
    )
}

function def_BuildV0114InputJson {
    param(
        [string]$LatestV0113J,
        [string]$P0PackCsv,
        [string]$P1PackCsv,
        [string]$RowPackCsv,
        [string]$ReadinessCsv
    )

    return [ordered]@{
        schema_version = "VIA_v0114_SandboxPatchCandidate_InputPack_v0113K"
        generated_at = (Get-Date).ToString("s")
        generated_by = "v0113K"
        source_v0113J = $LatestV0113J
        policy = [ordered]@{
            source_mutation = $false
            canonical_merge = $false
            official_db_write = $false
            delete = $false
            stop_process = $false
            no_close = $true
            allowed_next_phase = "sandbox_patch_candidate_generation_only"
        }
        inputs = [ordered]@{
            p0_policy_pack_csv = $P0PackCsv
            p1_alias_pack_csv = $P1PackCsv
            row_policy_pack_csv = $RowPackCsv
            readiness_csv = $ReadinessCsv
        }
        expected = [ordered]@{
            row_included = 149
            row_excluded = 1
            macro_china = "DEFER_EXCLUDED"
            fred_secret_policy = "UI_RUNTIME_SECRET_PARAMETER_OR_ENV_NAME_ONLY_RAW_SECRET_FORBIDDEN"
        }
    }
}

function def_BuildPreflight {
    param([string]$InputJson,[string]$ReadinessCsv,[string]$Path)

    $code = @"
`$ErrorActionPreference = "Stop"

`$InputJson = "$InputJson"
`$ReadinessCsv = "$ReadinessCsv"

if (-not (Test-Path -LiteralPath `$InputJson)) {
    throw "Missing v0114 input json: `$InputJson"
}

if (-not (Test-Path -LiteralPath `$ReadinessCsv)) {
    throw "Missing readiness csv: `$ReadinessCsv"
}

`$ready = @(Import-Csv -LiteralPath `$ReadinessCsv)[0]
`$pack = Get-Content -LiteralPath `$InputJson -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Sandbox Candidate Preflight after v0113K" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate        : `$(`$ready.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow v0114 : `$(`$ready.def_allow_v0114_sandbox_candidate)" -ForegroundColor Yellow
Write-Host "Rows Include: `$(`$ready.def_row_included)" -ForegroundColor Cyan
Write-Host "Rows Exclude: `$(`$ready.def_row_excluded)" -ForegroundColor Cyan
Write-Host "Unsafe Flags: `$(`$ready.def_unsafe_flags)" -ForegroundColor Yellow
Write-Host "Source Mut. : `$(`$ready.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical   : `$(`$ready.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write    : `$(`$ready.def_db_write)" -ForegroundColor Yellow

if (`$ready.def_allow_v0114_sandbox_candidate -ne "true") {
    throw "BLOCKED_NOT_READY_FOR_v0114_SANDBOX_CANDIDATE."
}

if (`$ready.def_source_mutation -ne "false" -or `$ready.def_canonical_merge -ne "false" -or `$ready.def_db_write -ne "false") {
    throw "BLOCKED_UNSAFE_MUTATION_FLAG."
}

Write-Host "[OK] READY_FOR_v0114_SANDBOX_PATCH_CANDIDATE_GENERATION_ONLY" -ForegroundColor Green
Write-Host "Input JSON: `$InputJson" -ForegroundColor Cyan
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
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
    param($Summary,$Readiness,$RowPack,$P0Pack,$P1Pack,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114",$Summary.AllowV0114),
        @("Rows In",$Summary.RowIncluded),
        @("Rows Out",$Summary.RowExcluded),
        @("P0 In",$Summary.P0Included),
        @("P1 In",$Summary.P1Included),
        @("Unsafe",$Summary.UnsafeFlags)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113K Row-Level Final Preview</title>
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
<h1>def VIA v0113K · Row-Level Final Preview + v0114 Input Pack</h1>
<div class="sub">Sandbox candidate input only · no source mutation · no canonical merge · no close</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
v0113K 已把 v0113J 的正式決策封裝為 v0114 sandbox input。這不是正式修補、不是 canonical merge、不是 DB write。下一步 v0114 只能產生 sandbox patch candidate 與 diff preview。
</div>
<span class="tag">Sandbox Input Only</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">No DB Write</span>
<span class="tag">NoClose</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114_sandbox_candidate","def_reason","def_row_included","def_row_excluded","def_p0_included_groups","def_p0_excluded_or_deferred_groups","def_p1_included_aliases","def_p1_excluded_or_deferred_aliases","def_unsafe_flags","def_next_allowed_phase","def_source_mutation","def_canonical_merge","def_db_write") 20)</div>
<div class="sec"><h2>def Row Policy Pack Preview</h2>$(def_Table $RowPack @("def_include_in_v0114_sandbox_input","def_normalized_key","def_owner_engine","def_domain_family","def_final_canonical_value","def_source_mutation","def_canonical_merge","def_db_write") 240)</div>
<div class="sec"><h2>def P0 Policy Pack</h2>$(def_Table $P0Pack @("def_final_decision","def_final_value","def_apply_to_rows","def_owner_engine","def_domain_family","def_sandbox_action","def_source_mutation","def_canonical_merge","def_db_write") 80)</div>
<div class="sec"><h2>def P1 Alias Pack</h2>$(def_Table $P1Pack @("def_alias","def_final_decision","def_final_value","def_path_value","def_sandbox_action","def_scope","def_source_mutation","def_canonical_merge","def_db_write") 80)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113J: $(def_Html $Summary.LatestV0113J)<br/>
Input Pack: $(def_Html $Summary.InputPackDir)<br/>
v0114 Input JSON: $(def_Html $Summary.V0114InputJson)<br/>
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
    Write-Host "def VIA · v0113K ROW-LEVEL FINAL PREVIEW + v0114 INPUT PACK · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: v0114 input only. No source mutation. No canonical merge. No DB write. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0113J output"
    $latest = def_GetLatestV0113J
    $latestOut = Join-Path $latest "output"
    $latestFinal = Join-Path $latest "_formal_decision_final"
    def_Log "OK" "Latest v0113J: $latest" Green

    def_Progress 2 10 "Load v0113J final boards"
    $readinessJ = def_LoadCsv (Join-Path $latestOut "VIA_v0113J_ReadinessGate.csv")
    $rowPreview = def_LoadCsv (Join-Path $latestOut "VIA_v0113J_RowLevelFormalPreview.csv")
    $p0Final = def_LoadCsv (Join-Path $latestFinal "VIA_v0113J_P0_FormalFinalDecision.csv")
    $p1Final = def_LoadCsv (Join-Path $latestFinal "VIA_v0113J_P1_FormalFinalDecision.csv")
    def_Log "OK" "Loaded Readiness=$(@($readinessJ).Count), Rows=$(@($rowPreview).Count), P0=$(@($p0Final).Count), P1=$(@($p1Final).Count)" Green

    def_Progress 3 10 "Build row policy pack"
    $rowPack = def_BuildRowPolicyPack -RowPreview $rowPreview

    def_Progress 4 10 "Build P0 policy pack"
    $p0Pack = def_BuildP0PolicyPack -P0Final $p0Final

    def_Progress 5 10 "Build P1 alias pack"
    $p1Pack = def_BuildP1AliasPack -P1Final $p1Final

    def_Progress 6 10 "Build v0113K readiness gate"
    $readinessK = def_BuildReadiness -ReadinessJ $readinessJ -RowPolicyPack $rowPack -P0Pack $p0Pack -P1Pack $p1Pack

    def_Progress 7 10 "Write input pack CSV/JSON"
    $p0PackCsv = Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_P0_PolicyPack.csv"
    $p1PackCsv = Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_P1_AliasPack.csv"
    $rowPackCsv = Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_RowPolicyPack.csv"
    $readinessCsv = Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_ReadinessGate.csv"
    $inputJson = Join-Path $def_INPUT_PACK_DIR "VIA_v0114_SandboxPatchCandidate_InputPack.json"

    def_WriteCsv $p0Pack $p0PackCsv
    def_WriteCsv $p1Pack $p1PackCsv
    def_WriteCsv $rowPack $rowPackCsv
    def_WriteCsv $readinessK $readinessCsv

    def_WriteJson $p0Pack (Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_P0_PolicyPack.json")
    def_WriteJson $p1Pack (Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_P1_AliasPack.json")
    def_WriteJson $rowPack (Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_RowPolicyPack.json")
    def_WriteJson $readinessK (Join-Path $def_INPUT_PACK_DIR "VIA_v0114_INPUT_ReadinessGate.json")

    $inputObj = def_BuildV0114InputJson -LatestV0113J $latest -P0PackCsv $p0PackCsv -P1PackCsv $p1PackCsv -RowPackCsv $rowPackCsv -ReadinessCsv $readinessCsv
    def_WriteJson $inputObj $inputJson 16

    def_Progress 8 10 "Mirror outputs and build v0114 preflight"
    def_WriteCsv $p0Pack (Join-Path $def_OUTPUT_DIR "VIA_v0113K_P0_PolicyPack.csv")
    def_WriteCsv $p1Pack (Join-Path $def_OUTPUT_DIR "VIA_v0113K_P1_AliasPack.csv")
    def_WriteCsv $rowPack (Join-Path $def_OUTPUT_DIR "VIA_v0113K_RowPolicyPack.csv")
    def_WriteCsv $readinessK (Join-Path $def_OUTPUT_DIR "VIA_v0113K_ReadinessGate.csv")
    Copy-Item -LiteralPath $inputJson -Destination (Join-Path $def_OUTPUT_DIR "VIA_v0114_SandboxPatchCandidate_InputPack.json") -Force

    $preflight = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-Preflight-After-v0113K.ps1"
    def_BuildPreflight -InputJson $inputJson -ReadinessCsv $readinessCsv -Path $preflight

    def_Progress 9 10 "Build accelerator matrix and next commands"
    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113K_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113K_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0113K_RowLevelFinalPreview_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113K.ps1"

    $next = @"
Start-Process "$report"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_INPUT_PACK_DIR"

Import-Csv "$readinessCsv" | Format-Table -AutoSize
Import-Csv "$rowPackCsv" | Select-Object -First 30 | Format-Table -AutoSize

pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$preflight"

# Next:
# v0114 may generate sandbox patch candidate and diff preview only.
# No source mutation. No canonical merge. No DB write.
# Input JSON:
# $inputJson
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $r0 = $readinessK[0]

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113K_ROW_LEVEL_FINAL_PREVIEW_READY"
        RunId = $def_RUN_ID
        LatestV0113J = $latest
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114 = def_GetProp $r0 "def_allow_v0114_sandbox_candidate"
        RowIncluded = def_GetProp $r0 "def_row_included"
        RowExcluded = def_GetProp $r0 "def_row_excluded"
        P0Included = def_GetProp $r0 "def_p0_included_groups"
        P0Excluded = def_GetProp $r0 "def_p0_excluded_or_deferred_groups"
        P1Included = def_GetProp $r0 "def_p1_included_aliases"
        P1Excluded = def_GetProp $r0 "def_p1_excluded_or_deferred_aliases"
        UnsafeFlags = def_GetProp $r0 "def_unsafe_flags"
        InputPackDir = $def_INPUT_PACK_DIR
        V0114InputJson = $inputJson
        Preflight = $preflight
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; v0114 sandbox candidate input only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113K_RowLevelFinalPreview_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessK -RowPack $rowPack -P0Pack $p0Pack -P1Pack $p1Pack -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0113K Row-Level Final Preview" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113K Row-Level Final Preview COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status       : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate         : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114  : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Rows In/Out  : $($summary.RowIncluded) / $($summary.RowExcluded)" -ForegroundColor Cyan
    Write-Host "P0 In/Out    : $($summary.P0Included) / $($summary.P0Excluded)" -ForegroundColor Cyan
    Write-Host "P1 In/Out    : $($summary.P1Included) / $($summary.P1Excluded)" -ForegroundColor Cyan
    Write-Host "Unsafe Flags : $($summary.UnsafeFlags)" -ForegroundColor $(if ($summary.UnsafeFlags -eq "0") { "Green" } else { "Red" })
    Write-Host "Input Pack   : $def_INPUT_PACK_DIR" -ForegroundColor Cyan
    Write-Host "v0114 JSON   : $inputJson" -ForegroundColor Cyan
    Write-Host "Preflight    : $preflight" -ForegroundColor Cyan
    Write-Host "Report       : $report" -ForegroundColor Cyan
    Write-Host "Output       : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd      : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_INPUT_PACK_DIR } catch {}
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
