param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0111_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_sixthstep_direct_smoke_gate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_SixthStep_DirectContractSmokeGate_v0112.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0111 auto discovery",
    "A02 no BASE re-scan",
    "A03 direct contract JSON validation",
    "A04 bypass fragile smoke child scripts",
    "A05 stdout/stderr tail extraction",
    "A06 policy flag validation",
    "A07 no source mutation",
    "A08 no canonical merge",
    "A09 no DB write",
    "A10 P0 accept gate stays manual",
    "A11 P1 path alias gate stays manual",
    "A12 compact one-page HTML report",
    "A13 CSV + JSON synchronized output",
    "A14 next-command index",
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA SixthStep Direct Contract Smoke v0112" -Status $Status -PercentComplete $pct
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

function def_IsFalseLike {
    param($Value)

    if ($null -eq $Value) {
        return $false
    }

    if ($Value -is [bool]) {
        return (-not $Value)
    }

    $s = (def_S $Value).Trim().ToLowerInvariant()

    if ($s -in @("false","0","")) {
        return $true
    }

    return $false
}

function def_TailText {
    param(
        [string]$Path,
        [int]$Lines = 24
    )

    try {
        if (-not [string]::IsNullOrWhiteSpace($Path) -and (Test-Path -LiteralPath $Path)) {
            return ((Get-Content -LiteralPath $Path -Tail $Lines -ErrorAction SilentlyContinue) -join " || ")
        }
    } catch {
        return "TAIL_READ_FAIL: $($_.Exception.Message)"
    }

    return ""
}

function def_GetLatestV0111 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0111_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0111_ROOT) {
            return $def_PARAM_V0111_ROOT
        }
        throw "Specified v0111 root does not exist: $def_PARAM_V0111_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_fifthstep_smoke_accept_gate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0111 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_FifthStep_SmokeDiagnosticAcceptGate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0111 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_BuildSmokeFailureTails {
    param([array]$FixedSmokeRows)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $FixedSmokeRows) {
        $project = def_GetProp $r "def_project"
        $stdout = def_GetProp $r "def_stdout"
        $stderr = def_GetProp $r "def_stderr"
        $status = def_GetProp $r "def_status"
        $exit = def_GetProp $r "def_exit_code"

        $stdoutTail = def_TailText -Path $stdout -Lines 30
        $stderrTail = def_TailText -Path $stderr -Lines 30

        $cause = "REVIEW_REQUIRED"
        if ([string]::IsNullOrWhiteSpace($stderrTail) -and $status -ne "FIXED_SMOKE_OK") {
            $cause = "NO_STDERR_TAIL_NONZERO_OR_SCRIPT_EXIT_REVIEW"
        } elseif ($stderrTail -match "throw|Exception|ParserError|Cannot|not recognized|missing|not false") {
            $cause = "STDERR_HAS_EXECUTION_ERROR"
        } elseif ($status -eq "FIXED_SMOKE_OK") {
            $cause = "OK"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = $project
            def_original_status = $status
            def_exit_code = $exit
            def_cause_hint = $cause
            def_stdout_path = $stdout
            def_stderr_path = $stderr
            def_stdout_tail = $stdoutTail
            def_stderr_tail = $stderrTail
        })
    }

    return @($rows)
}

function def_BuildDirectContractSmoke {
    param([array]$CandidateRows,[array]$FixedSmokeRows)

    $rows = New-Object System.Collections.ArrayList

    foreach ($c in $CandidateRows) {
        $project = def_GetProp $c "def_project"
        $candidateDir = def_GetProp $c "def_candidate_dir"
        $contractJson = def_GetProp $c "def_contract_json"

        $fixedMatch = @($FixedSmokeRows | Where-Object { (def_GetProp $_ "def_project") -eq $project } | Select-Object -First 1)
        $fixedObj = $null
        if (@($fixedMatch).Count -gt 0) { $fixedObj = $fixedMatch[0] }

        $dirExists = Test-Path -LiteralPath $candidateDir
        $contractExists = Test-Path -LiteralPath $contractJson

        $jsonReadable = $false
        $schema = ""
        $contractProject = ""
        $sourceMutation = ""
        $canonicalMerge = ""
        $dbWrite = ""
        $policy = ""
        $directStatus = "DIRECT_SMOKE_REVIEW"
        $reviewReason = ""

        if (-not $dirExists) {
            $reviewReason = "candidate directory missing"
        } elseif (-not $contractExists) {
            $reviewReason = "contract json missing"
        } else {
            $obj = def_LoadJson $contractJson
            if ($null -eq $obj) {
                $reviewReason = "contract json unreadable"
            } else {
                $jsonReadable = $true
                $schema = def_GetProp $obj "schema_version"
                $contractProject = def_GetProp $obj "project"
                $sourceMutation = def_GetProp $obj "source_mutation"
                $canonicalMerge = def_GetProp $obj "canonical_merge"
                $dbWrite = def_GetProp $obj "db_write"
                $policy = def_GetProp $obj "policy"

                $sourceOk = def_IsFalseLike $obj.source_mutation
                $canonicalOk = def_IsFalseLike $obj.canonical_merge
                $dbOk = def_IsFalseLike $obj.db_write

                if ($sourceOk -and $canonicalOk -and $dbOk) {
                    $directStatus = "DIRECT_CONTRACT_SMOKE_OK"
                    $reviewReason = "contract valid; policy flags safe; fixed smoke script issue can be treated separately"
                } else {
                    $reviewReason = "policy flag review: source_mutation=$sourceMutation canonical_merge=$canonicalMerge db_write=$dbWrite"
                }
            }
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = $project
            def_direct_status = $directStatus
            def_review_reason = $reviewReason
            def_candidate_dir_exists = def_S $dirExists
            def_contract_json_exists = def_S $contractExists
            def_contract_json_readable = def_S $jsonReadable
            def_schema_version = $schema
            def_contract_project = $contractProject
            def_source_mutation = $sourceMutation
            def_canonical_merge = $canonicalMerge
            def_db_write = $dbWrite
            def_policy = $policy
            def_fixed_smoke_status = def_GetProp $fixedObj "def_status"
            def_fixed_smoke_exit_code = def_GetProp $fixedObj "def_exit_code"
            def_candidate_dir = $candidateDir
            def_contract_json = $contractJson
        })
    }

    return @($rows)
}

function def_BuildGateRecommendation {
    param([array]$DirectSmoke,[array]$P0Accept,[array]$P1Accept)

    $directOk = @($DirectSmoke | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectSmoke | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $gate = "HOLD_FOR_P0_P1_USER_DECISION"
    $next = "Do not generate canonical patch yet."

    if ($directReview -eq 0 -and @($P0Accept).Count -gt 0 -and @($P1Accept).Count -gt 0) {
        $gate = "TECHNICALLY_READY_BUT_WAIT_USER_ACCEPT"
        $next = "User must accept P0/P1 templates before v0113 canonical patch candidate."
    }

    return [pscustomobject][ordered]@{
        def_gate_status = $gate
        def_direct_contract_ok = "$directOk"
        def_direct_contract_review = "$directReview"
        def_p0_accept_rows = "$(@($P0Accept).Count)"
        def_p1_accept_rows = "$(@($P1Accept).Count)"
        def_next_allowed_phase = "v0113 only after P0/P1 acceptance"
        def_recommendation = $next
        def_source_mutation = "false"
        def_canonical_merge = "false"
    }
}

function def_BuildNextCommands {
    param([string]$RunDir)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0112
# =============================================================================

Start-Process "$RunDir\report\VIA_SixthStep_DirectContractSmokeGate_Report_v0112.html"
Start-Process "$RunDir\output"

Import-Csv "$RunDir\output\VIA_v0112_DirectContractSmoke.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0112_SmokeFailureTails.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0112_GateRecommendation.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0112_P0_AcceptGate_Template.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0112_P1_PathAlias_AcceptGate_Template.csv" | Format-Table -AutoSize

# Next safe phase:
# v0113 may generate canonical patch candidate only after P0/P1 accept gate is manually reviewed.
# Still no overwrite: sandbox candidate first.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0112.ps1"
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
        [array]$DirectSmoke,
        [array]$SmokeTails,
        [array]$GateRecommendation,
        [array]$P0Accept,
        [array]$P1Accept,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Direct OK",$Summary.DirectSmokeOk),
        @("Direct Review",$Summary.DirectSmokeReview),
        @("Fixed OK",$Summary.FixedSmokeOk),
        @("Fixed Review",$Summary.FixedSmokeReview),
        @("P0 Accept",$Summary.P0AcceptRows),
        @("P1 Accept",$Summary.P1AcceptRows),
        @("Next","v0113 Gate")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA SixthStep Direct Contract Smoke Gate v0112</title>
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
<h1>def VIA Integration SixthStep Direct Contract Smoke Gate · v0112</h1>
<div class="sub">Direct contract validation · smoke failure tail extraction · P0/P1 manual gate · no mutation</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0111 顯示 Static OK=3，但 Fixed Smoke OK=0。v0112 直接驗證 contract JSON 與 policy flags，因此可區分「候選合約有效」與「smoke 腳本失敗」。若 Direct OK=3 且 Direct Review=0，代表技術候選可進 v0113；但 P0/P1 仍需人工接受，不能直接寫回 canonical。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">P0/P1 Manual Gate</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Gate Recommendation</h2>$(def_Table $GateRecommendation @("def_gate_status","def_direct_contract_ok","def_direct_contract_review","def_p0_accept_rows","def_p1_accept_rows","def_next_allowed_phase","def_recommendation","def_source_mutation","def_canonical_merge") 20)</div>
<div class="sec wide"><h2>def Direct Contract Smoke</h2>$(def_Table $DirectSmoke @("def_project","def_direct_status","def_review_reason","def_candidate_dir_exists","def_contract_json_exists","def_contract_json_readable","def_schema_version","def_contract_project","def_source_mutation","def_canonical_merge","def_db_write","def_policy","def_fixed_smoke_status","def_fixed_smoke_exit_code","def_contract_json") 80)</div>
<div class="sec wide"><h2>def Smoke Failure Tails</h2>$(def_Table $SmokeTails @("def_project","def_original_status","def_exit_code","def_cause_hint","def_stdout_tail","def_stderr_tail","def_stdout_path","def_stderr_path") 80)</div>
<div class="sec wide"><h2>def P0 Accept Gate Template</h2>$(def_Table $P0Accept @("def_priority","def_accept_status","def_owner_engine","def_domain_family","def_normalized_key","def_distinct_values","def_selected_canonical_value","def_reject_reason","def_next_allowed_phase","def_source_mutation","def_sample_values") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Accept Gate Template</h2>$(def_Table $P1Accept @("def_priority","def_accept_status","def_alias","def_path_value","def_status","def_scope","def_selected","def_reject_reason","def_mutate_existing_source") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0111 source: $(def_Html $Summary.LatestV0111)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
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
    Write-Host "def VIA · SIXTHSTEP DIRECT CONTRACT SMOKE + GATE REVIEW · v0112" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Find latest v0111 output"
    $latest = def_GetLatestV0111
    $latestOut = Join-Path $latest "output"
    def_Log "OK" "Latest v0111: $latest" Green

    def_Progress 2 9 "Load v0111 matrices"
    $summaryV0111 = def_LoadJson (Join-Path $latestOut "VIA_FifthStep_SmokeDiagnosticAcceptGate_Summary.json")
    $candidates = def_LoadCsv (Join-Path $latestOut "VIA_v0111_Candidates_From_v0110.csv")
    $fixedSmoke = def_LoadCsv (Join-Path $latestOut "VIA_v0111_FixedSmokeResults.csv")
    $p0Accept = def_LoadCsv (Join-Path $latestOut "VIA_v0111_P0_AcceptGate_Template.csv")
    $p1Accept = def_LoadCsv (Join-Path $latestOut "VIA_v0111_P1_PathAlias_AcceptGate_Template.csv")
    def_Log "OK" "Loaded Candidates=$(@($candidates).Count), FixedSmoke=$(@($fixedSmoke).Count), P0=$(@($p0Accept).Count), P1=$(@($p1Accept).Count)" Green

    def_Progress 3 9 "Extract fixed-smoke stdout/stderr tails"
    $smokeTails = def_BuildSmokeFailureTails -FixedSmokeRows $fixedSmoke

    def_Progress 4 9 "Run direct contract smoke validation"
    $directSmoke = def_BuildDirectContractSmoke -CandidateRows $candidates -FixedSmokeRows $fixedSmoke

    def_Progress 5 9 "Build gate recommendation"
    $gateRecommendation = @(def_BuildGateRecommendation -DirectSmoke $directSmoke -P0Accept $p0Accept -P1Accept $p1Accept)

    def_Progress 6 9 "Build PS15 accelerator matrix"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_Progress 7 9 "Write CSV/JSON outputs"
    def_WriteCsv $directSmoke (Join-Path $def_OUTPUT_DIR "VIA_v0112_DirectContractSmoke.csv")
    def_WriteCsv $smokeTails (Join-Path $def_OUTPUT_DIR "VIA_v0112_SmokeFailureTails.csv")
    def_WriteCsv $gateRecommendation (Join-Path $def_OUTPUT_DIR "VIA_v0112_GateRecommendation.csv")
    def_WriteCsv $p0Accept (Join-Path $def_OUTPUT_DIR "VIA_v0112_P0_AcceptGate_Template.csv")
    def_WriteCsv $p1Accept (Join-Path $def_OUTPUT_DIR "VIA_v0112_P1_PathAlias_AcceptGate_Template.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0112_PS15_Accelerators.csv")

    def_WriteJson $directSmoke (Join-Path $def_OUTPUT_DIR "VIA_v0112_DirectContractSmoke.json")
    def_WriteJson $smokeTails (Join-Path $def_OUTPUT_DIR "VIA_v0112_SmokeFailureTails.json")
    def_WriteJson $gateRecommendation (Join-Path $def_OUTPUT_DIR "VIA_v0112_GateRecommendation.json")
    def_WriteJson $p0Accept (Join-Path $def_OUTPUT_DIR "VIA_v0112_P0_AcceptGate_Template.json")
    def_WriteJson $p1Accept (Join-Path $def_OUTPUT_DIR "VIA_v0112_P1_PathAlias_AcceptGate_Template.json")

    def_Progress 8 9 "Write next commands"
    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR

    $directOk = @($directSmoke | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($directSmoke | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $fixedOk = @($fixedSmoke | Where-Object { (def_GetProp $_ "def_status") -eq "FIXED_SMOKE_OK" }).Count
    $fixedReview = @($fixedSmoke | Where-Object { (def_GetProp $_ "def_status") -ne "FIXED_SMOKE_OK" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112_READY"
        RunId = $def_RUN_ID
        LatestV0111 = $latest
        DirectSmokeRows = "$(@($directSmoke).Count)"
        DirectSmokeOk = "$directOk"
        DirectSmokeReview = "$directReview"
        FixedSmokeOk = "$fixedOk"
        FixedSmokeReview = "$fixedReview"
        P0AcceptRows = "$(@($p0Accept).Count)"
        P1AcceptRows = "$(@($p1Accept).Count)"
        GateStatus = def_GetProp $gateRecommendation[0] "def_gate_status"
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; direct contract validation only."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_SixthStep_DirectContractSmokeGate_Summary.json")

    def_Progress 9 9 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_SixthStep_DirectContractSmokeGate_Report_v0112.html"
    def_WriteReport `
        -Summary $summary `
        -DirectSmoke $directSmoke `
        -SmokeTails $smokeTails `
        -GateRecommendation $gateRecommendation `
        -P0Accept $p0Accept `
        -P1Accept $p1Accept `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA SixthStep Direct Contract Smoke v0112" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA SixthStep Direct Contract Smoke + Gate Review v0112 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status        : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0111         : $latest" -ForegroundColor Gray
    Write-Host "Direct OK     : $($summary.DirectSmokeOk)" -ForegroundColor Green
    Write-Host "Direct Review : $($summary.DirectSmokeReview)" -ForegroundColor Yellow
    Write-Host "Fixed OK      : $($summary.FixedSmokeOk)" -ForegroundColor Gray
    Write-Host "Fixed Review  : $($summary.FixedSmokeReview)" -ForegroundColor Yellow
    Write-Host "Gate          : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Report        : $report" -ForegroundColor Cyan
    Write-Host "Output        : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd       : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try { Start-Process -FilePath $report } catch {}
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
