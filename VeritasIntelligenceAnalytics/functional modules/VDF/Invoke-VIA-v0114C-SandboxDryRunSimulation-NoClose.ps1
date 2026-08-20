param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114B_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114C_sandbox_dryrun_simulation"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_SANDBOX_DIR = Join-Path $def_RUN_DIR "_dryrun_sandbox_only"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114C_SandboxDryRunSimulation.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114B auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 v0114B readiness reuse",
    "A06 v0114A candidate path bridge",
    "A07 sandbox-only policy registry simulation",
    "A08 sandbox-only alias registry simulation",
    "A09 sandbox-only row mapping simulation",
    "A10 count consistency gate",
    "A11 unsafe flag scanner",
    "A12 no source mutation scanner",
    "A13 no canonical merge scanner",
    "A14 no DB write scanner",
    "A15 compact HTML dry-run report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_SANDBOX_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114C Sandbox Dry-Run Simulation" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114B {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114B_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114B_ROOT) {
            return $def_PARAM_V0114B_ROOT
        }
        throw "Specified v0114B root does not exist: $def_PARAM_V0114B_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0114B_candidate_validation_seal"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114B output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114B_CandidateValidationSeal_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114B output found under: $root"
    }

    return $candidates[0].FullName
}

function def_ReadJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "JSON missing: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function def_AddValidation {
    param(
        [System.Collections.ArrayList]$Rows,
        [string]$Layer,
        [string]$Name,
        [bool]$Pass,
        [string]$Message,
        [string]$Path = ""
    )

    [void]$Rows.Add([pscustomobject][ordered]@{
        def_layer = $Layer
        def_test = $Name
        def_status = $(if ($Pass) { "PASS" } else { "FAIL" })
        def_risk = $(if ($Pass) { "LOW" } else { "HIGH" })
        def_message = $Message
        def_path = $Path
    })
}

function def_CountUnsafeFlags {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_source_mutation") -ne "" -and (def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "" -and (def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "" -and (def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_existing_source_change") -eq "true")
    }).Count
}

function def_BuildSimulatedPolicyRegistry {
    param([array]$PolicyCandidate)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($p in $PolicyCandidate) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_sim_id = "SIM_POLICY_{0:0000}" -f $n
            def_source_candidate_id = def_GetProp $p "def_candidate_id"
            def_registry_type = "SANDBOX_POLICY_REGISTRY_SIMULATION"
            def_owner_engine = def_GetProp $p "def_owner_engine"
            def_domain_family = def_GetProp $p "def_domain_family"
            def_policy_value = def_GetProp $p "def_policy_value"
            def_apply_to_rows = def_GetProp $p "def_apply_to_rows"
            def_simulation_action = "WOULD_REGISTER_POLICY_IN_SANDBOX_ONLY"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildSimulatedAliasRegistry {
    param([array]$AliasCandidate)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($a in $AliasCandidate) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_sim_id = "SIM_ALIAS_{0:0000}" -f $n
            def_source_candidate_id = def_GetProp $a "def_candidate_id"
            def_registry_type = "SANDBOX_ALIAS_REGISTRY_SIMULATION"
            def_alias = def_GetProp $a "def_alias"
            def_alias_value = def_GetProp $a "def_alias_value"
            def_alias_decision = def_GetProp $a "def_alias_decision"
            def_scope = def_GetProp $a "def_scope"
            def_simulation_action = "WOULD_REGISTER_ALIAS_IN_SANDBOX_ONLY"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildSimulatedRowMapping {
    param([array]$RowPatchPlan)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($r in $RowPatchPlan) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_sim_id = "SIM_ROW_{0:0000}" -f $n
            def_source_candidate_id = def_GetProp $r "def_candidate_id"
            def_registry_type = "SANDBOX_ROW_MAPPING_SIMULATION"
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_candidate_canonical_value = def_GetProp $r "def_candidate_canonical_value"
            def_simulation_action = "WOULD_MAP_KEY_TO_POLICY_VALUE_IN_SANDBOX_ONLY"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
        })
    }

    return @($rows)
}

function def_BuildDryRunActionPlan {
    param([array]$SimPolicy,[array]$SimAlias,[array]$SimRows)

    $rows = New-Object System.Collections.ArrayList

    [void]$rows.Add([pscustomobject][ordered]@{
        def_phase = "DRYRUN_POLICY"
        def_action = "SIMULATE_POLICY_REGISTRY_LOAD"
        def_rows = "$(@($SimPolicy).Count)"
        def_result = "SIMULATED_ONLY"
        def_source_mutation = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_phase = "DRYRUN_ALIAS"
        def_action = "SIMULATE_ALIAS_REGISTRY_LOAD"
        def_rows = "$(@($SimAlias).Count)"
        def_result = "SIMULATED_ONLY"
        def_source_mutation = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_phase = "DRYRUN_ROW_MAPPING"
        def_action = "SIMULATE_ROW_MAPPING_LOAD"
        def_rows = "$(@($SimRows).Count)"
        def_result = "SIMULATED_ONLY"
        def_source_mutation = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_phase = "APPLY_BOUNDARY"
        def_action = "BLOCK_REAL_APPLY"
        def_rows = "0"
        def_result = "REAL_APPLY_DISABLED"
        def_source_mutation = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
    })

    return @($rows)
}

function def_BuildValidation {
    param(
        [array]$ReadinessB,
        [array]$PolicyCandidate,
        [array]$AliasCandidate,
        [array]$RowPatchPlan,
        [array]$SimPolicy,
        [array]$SimAlias,
        [array]$SimRows,
        [array]$ActionPlan
    )

    $rows = New-Object System.Collections.ArrayList
    $rb = $ReadinessB[0]

    def_AddValidation $rows "UPSTREAM" "v0114B allow v0114C" ((def_GetProp $rb "def_allow_v0114C") -eq "true") ("Gate=" + (def_GetProp $rb "def_gate_status"))

    def_AddValidation $rows "COUNT" "candidate policy count" (@($PolicyCandidate).Count -eq 12) ("Policy=" + @($PolicyCandidate).Count)
    def_AddValidation $rows "COUNT" "candidate alias count" (@($AliasCandidate).Count -eq 5) ("Alias=" + @($AliasCandidate).Count)
    def_AddValidation $rows "COUNT" "candidate row count" (@($RowPatchPlan).Count -eq 149) ("Rows=" + @($RowPatchPlan).Count)

    def_AddValidation $rows "COUNT" "sim policy count match" (@($SimPolicy).Count -eq @($PolicyCandidate).Count) ("SimPolicy=" + @($SimPolicy).Count)
    def_AddValidation $rows "COUNT" "sim alias count match" (@($SimAlias).Count -eq @($AliasCandidate).Count) ("SimAlias=" + @($SimAlias).Count)
    def_AddValidation $rows "COUNT" "sim row count match" (@($SimRows).Count -eq @($RowPatchPlan).Count) ("SimRows=" + @($SimRows).Count)

    $allRows = @()
    $allRows += $PolicyCandidate
    $allRows += $AliasCandidate
    $allRows += $RowPatchPlan
    $allRows += $SimPolicy
    $allRows += $SimAlias
    $allRows += $SimRows
    $allRows += $ActionPlan

    $unsafe = def_CountUnsafeFlags -Rows $allRows
    def_AddValidation $rows "SAFETY" "no unsafe flags in simulation" ($unsafe -eq 0) "UnsafeFlags=$unsafe"

    $macroChina = @($SimRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "MACRO_CHINA" }).Count
    def_AddValidation $rows "SAFETY" "MACRO_CHINA still excluded" ($macroChina -eq 0) "MACRO_CHINA rows=$macroChina"

    $rawFred = @($SimRows | Where-Object {
        (def_GetProp $_ "def_candidate_canonical_value") -match "(?i)FRED_API_KEY\s*=\s*[A-Za-z0-9_\-]{16,}"
    }).Count
    def_AddValidation $rows "SECRET" "FRED raw value still forbidden" ($rawFred -eq 0) "Raw FRED pattern rows=$rawFred"

    $actionApply = @($ActionPlan | Where-Object { (def_GetProp $_ "def_action") -eq "BLOCK_REAL_APPLY" }).Count
    def_AddValidation $rows "APPLY_BOUNDARY" "real apply blocked" ($actionApply -eq 1) "Block rows=$actionApply"

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$SimPolicy,[array]$SimAlias,[array]$SimRows)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114D_SANDBOX_REVIEW_SEAL"
    $allow = "true"
    $reason = "Sandbox dry-run simulation passed. Next phase may create review seal only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_DRYRUN_SIMULATION_FAILURE"
        $allow = "false"
        $reason = "Dry-run validation has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114D = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_sim_policy_rows = "$(@($SimPolicy).Count)"
            def_sim_alias_rows = "$(@($SimAlias).Count)"
            def_sim_row_rows = "$(@($SimRows).Count)"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114D sandbox review seal only"
        }
    )
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
        'Write-Host "def VIA · v0114D Precheck after v0114C" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114D)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Policy     : $($r.def_sim_policy_rows)" -ForegroundColor Cyan',
        'Write-Host "Alias      : $($r.def_sim_alias_rows)" -ForegroundColor Cyan',
        'Write-Host "Rows       : $($r.def_sim_row_rows)" -ForegroundColor Cyan',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114D -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114D." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114D_SANDBOX_REVIEW_SEAL_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=260)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) { [void]$sb.Append("<th>$(def_Html $c)</th>") }
    [void]$sb.Append("</tr></thead><tbody>")

    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = def_GetProp $r $c
            if ($v.Length -gt 300) { $v = $v.Substring(0,300) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$ActionPlan,$SimPolicy,$SimAlias,$SimRows,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114D",$Summary.AllowV0114D),
        @("Fail",$Summary.ValidationFail),
        @("Policy",$Summary.PolicyRows),
        @("Alias",$Summary.AliasRows),
        @("Rows",$Summary.RowRows),
        @("Mutation","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114C Sandbox Dry-Run Simulation</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114C · Sandbox Dry-Run Simulation</h1>")
    [void]$html.AppendLine("<div class='sub'>Simulation only · sandbox output only · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114C 只在 dryrun sandbox 內模擬 registry load 與 row mapping。這不是正式 apply；下一步 v0114D 只能做 review seal。</div><span class='tag'>Dry-Run Only</span><span class='tag'>Sandbox Only</span><span class='tag'>No Source Mutation</span><span class='tag'>No DB Write</span><span class='tag'>NoClose</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114D','def_reason','def_validation_fail','def_sim_policy_rows','def_sim_alias_rows','def_sim_row_rows','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Dry-Run Action Plan</h2>$(def_Table $ActionPlan @('def_phase','def_action','def_rows','def_result','def_source_mutation','def_canonical_merge','def_db_write') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Simulated Policy Registry</h2>$(def_Table $SimPolicy @('def_sim_id','def_owner_engine','def_domain_family','def_policy_value','def_apply_to_rows','def_simulation_action','def_source_mutation','def_canonical_merge','def_db_write') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Simulated Alias Registry</h2>$(def_Table $SimAlias @('def_sim_id','def_alias','def_alias_value','def_alias_decision','def_scope','def_simulation_action','def_source_mutation','def_canonical_merge','def_db_write') 40)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Simulated Row Mapping Preview</h2>$(def_Table $SimRows @('def_sim_id','def_normalized_key','def_owner_engine','def_domain_family','def_candidate_canonical_value','def_simulation_action','def_source_mutation','def_canonical_merge','def_db_write') 240)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114B: $(def_Html $Summary.LatestV0114B)<br/>Latest v0114A: $(def_Html $Summary.LatestV0114A)<br/>Sandbox Dir: $(def_Html $Summary.SandboxDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114C SANDBOX DRY-RUN SIMULATION · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Simulation only. No source mutation. No canonical merge. No DB write. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0114B output"
    $latestB = def_GetLatestV0114B
    $summaryBPath = Join-Path $latestB "output\VIA_v0114B_CandidateValidationSeal_Summary.json"
    $summaryB = def_ReadJson $summaryBPath
    $latestA = def_S $summaryB.LatestV0114A
    if (-not (Test-Path -LiteralPath $latestA)) {
        throw "Latest v0114A path from v0114B summary does not exist: $latestA"
    }
    def_Log "OK" "Latest v0114B: $latestB" Green
    def_Log "OK" "Latest v0114A: $latestA" Green

    def_Progress 2 10 "Resolve v0114A candidate paths"
    $outB = Join-Path $latestB "output"
    $candA = Join-Path $latestA "_sandbox_patch_candidate"

    $readinessBCsv = Join-Path $outB "VIA_v0114B_ReadinessGate.csv"
    $policyCsv = Join-Path $candA "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv"
    $aliasCsv = Join-Path $candA "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv"
    $rowCsv = Join-Path $candA "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv"

    def_Progress 3 10 "Load validation and candidate inputs"
    $readinessB = def_LoadCsv $readinessBCsv
    $policyCandidate = def_LoadCsv $policyCsv
    $aliasCandidate = def_LoadCsv $aliasCsv
    $rowPatchPlan = def_LoadCsv $rowCsv
    def_Log "OK" "Loaded Policy=$(@($policyCandidate).Count), Alias=$(@($aliasCandidate).Count), Rows=$(@($rowPatchPlan).Count)" Green

    def_Progress 4 10 "Simulate policy registry"
    $simPolicy = def_BuildSimulatedPolicyRegistry -PolicyCandidate $policyCandidate

    def_Progress 5 10 "Simulate alias registry"
    $simAlias = def_BuildSimulatedAliasRegistry -AliasCandidate $aliasCandidate

    def_Progress 6 10 "Simulate row mapping registry"
    $simRows = def_BuildSimulatedRowMapping -RowPatchPlan $rowPatchPlan

    def_Progress 7 10 "Build dry-run action plan"
    $actionPlan = def_BuildDryRunActionPlan -SimPolicy $simPolicy -SimAlias $simAlias -SimRows $simRows

    def_Progress 8 10 "Validate dry-run simulation"
    $validation = def_BuildValidation -ReadinessB $readinessB -PolicyCandidate $policyCandidate -AliasCandidate $aliasCandidate -RowPatchPlan $rowPatchPlan -SimPolicy $simPolicy -SimAlias $simAlias -SimRows $simRows -ActionPlan $actionPlan
    $readinessC = def_BuildReadiness -Validation $validation -SimPolicy $simPolicy -SimAlias $simAlias -SimRows $simRows

    def_Progress 9 10 "Write dry-run outputs and precheck"
    $simPolicyCsv = Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_POLICY_REGISTRY.csv"
    $simAliasCsv = Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_ALIAS_REGISTRY.csv"
    $simRowsCsv = Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_ROW_MAPPING.csv"
    $actionCsv = Join-Path $def_SANDBOX_DIR "VIA_v0114C_DRYRUN_ACTION_PLAN.csv"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114C_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114C_ReadinessGate.csv"

    def_WriteCsv $simPolicy $simPolicyCsv
    def_WriteCsv $simAlias $simAliasCsv
    def_WriteCsv $simRows $simRowsCsv
    def_WriteCsv $actionPlan $actionCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessC $readinessCsv

    def_WriteJson $simPolicy (Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_POLICY_REGISTRY.json")
    def_WriteJson $simAlias (Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_ALIAS_REGISTRY.json")
    def_WriteJson $simRows (Join-Path $def_SANDBOX_DIR "VIA_v0114C_SIMULATED_ROW_MAPPING.json")
    def_WriteJson $actionPlan (Join-Path $def_SANDBOX_DIR "VIA_v0114C_DRYRUN_ACTION_PLAN.json")
    def_WriteJson $validation (Join-Path $def_OUTPUT_DIR "VIA_v0114C_ValidationMatrix.json")
    def_WriteJson $readinessC (Join-Path $def_OUTPUT_DIR "VIA_v0114C_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114D-Precheck-After-v0114C.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }
    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114C_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114C_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114C_SandboxDryRunSimulation_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114C.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_SANDBOX_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114D sandbox review seal only.',
        '# No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessC[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114C_SANDBOX_DRYRUN_SIMULATION_READY"
        RunId = $def_RUN_ID
        LatestV0114B = $latestB
        LatestV0114A = $latestA
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114D = def_GetProp $r0 "def_allow_v0114D"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        PolicyRows = def_GetProp $r0 "def_sim_policy_rows"
        AliasRows = def_GetProp $r0 "def_sim_alias_rows"
        RowRows = def_GetProp $r0 "def_sim_row_rows"
        SandboxDir = $def_SANDBOX_DIR
        ValidationCsv = $validationCsv
        ReadinessCsv = $readinessCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; dry-run simulation only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114C_SandboxDryRunSimulation_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessC -Validation $validation -ActionPlan $actionPlan -SimPolicy $simPolicy -SimAlias $simAlias -SimRows $simRows -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114C Sandbox Dry-Run Simulation" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114C Sandbox Dry-Run Simulation COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114D    : $($summary.AllowV0114D)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Policy Rows     : $($summary.PolicyRows)" -ForegroundColor Cyan
    Write-Host "Alias Rows      : $($summary.AliasRows)" -ForegroundColor Cyan
    Write-Host "Row Rows        : $($summary.RowRows)" -ForegroundColor Cyan
    Write-Host "Sandbox Dir     : $def_SANDBOX_DIR" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_SANDBOX_DIR } catch {}
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
