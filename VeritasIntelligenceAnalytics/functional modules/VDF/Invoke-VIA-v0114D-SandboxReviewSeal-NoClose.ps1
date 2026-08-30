param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114C_ROOT = "",
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

$def_RUN_ID = "RUN_{0}_VIA_v0114D_SANDBOX_REVIEW_SEAL" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114D_sandbox_review_seal"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_SEAL_DIR = Join-Path $def_RUN_DIR "_review_seal_package"
$def_MANUAL_GATE_DIR = Join-Path $def_RUN_DIR "_manual_release_gate_draft"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114D_SandboxReviewSeal.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114C auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 v0114C readiness reuse",
    "A06 dry-run evidence inventory",
    "A07 count consistency seal",
    "A08 mutation boundary seal",
    "A09 canonical merge boundary seal",
    "A10 DB write boundary seal",
    "A11 secret policy seal",
    "A12 MACRO_CHINA exclusion seal",
    "A13 manual release gate draft",
    "A14 v0114E precheck generated",
    "A15 compact HTML review seal report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_SEAL_DIR,$def_MANUAL_GATE_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114D Sandbox Review Seal" -Status $Status -PercentComplete $pct
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

function def_ReadJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "JSON missing: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
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

function def_GetFileSha {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash } catch { return "" }
}

function def_GetLatestV0114C {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114C_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114C_ROOT) {
            return $def_PARAM_V0114C_ROOT
        }
        throw "Specified v0114C root does not exist: $def_PARAM_V0114C_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0114C_sandbox_dryrun_simulation"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114C output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114C_SandboxDryRunSimulation_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114C output found under: $root"
    }

    return $candidates[0].FullName
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

function def_CountUnsafe {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_source_mutation") -ne "" -and (def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "" -and (def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "" -and (def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_existing_source_change") -eq "true")
    }).Count
}

function def_BuildEvidenceManifest {
    param([string[]]$Paths)

    $rows = New-Object System.Collections.ArrayList

    foreach ($p in $Paths) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_artifact = Split-Path $p -Leaf
            def_exists = [string](Test-Path -LiteralPath $p)
            def_length = $(if (Test-Path -LiteralPath $p) { [string]((Get-Item -LiteralPath $p).Length) } else { "0" })
            def_sha256 = def_GetFileSha $p
            def_path = $p
        })
    }

    return @($rows)
}

function def_BuildReviewDecisionBoard {
    param([string]$LatestC,[string]$SummaryPath,[array]$Readiness,[array]$Validation)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $ready = $false
    if (@($Readiness).Count -gt 0) {
        $ready = ((def_GetProp $Readiness[0] "def_allow_v0114D") -eq "true")
    }

    return @(
        [pscustomobject][ordered]@{
            def_review_gate = "SANDBOX_REVIEW_SEAL"
            def_user_release_accept = ""
            def_user_release_note = ""
            def_recommended_decision = $(if ($ready -and $fail -eq 0) { "READY_FOR_MANUAL_RELEASE_REVIEW" } else { "BLOCKED_REVIEW_FAILURE" })
            def_release_scope = "review_only_no_apply"
            def_latest_v0114C = $LatestC
            def_summary_path = $SummaryPath
            def_validation_fail = "$fail"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_phase = "v0114E manual release approval gate only"
        }
    )
}

function def_BuildReadiness {
    param([array]$Validation,[array]$DecisionBoard)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114E_MANUAL_RELEASE_APPROVAL_GATE"
    $allow = "true"
    $reason = "Sandbox review seal passed. Next phase may create manual release approval gate only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_REVIEW_SEAL_FAILURE"
        $allow = "false"
        $reason = "Review seal validation has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114E = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_user_release_accept = def_GetProp $DecisionBoard[0] "def_user_release_accept"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114E manual release approval gate only"
        }
    )
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$DecisionCsv,[string]$Path)

    $safeReady = def_EscapePsDouble $ReadinessCsv
    $safeDecision = def_EscapePsDouble $DecisionCsv

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '$ReadinessCsv = "' + $safeReady + '"',
        '$DecisionCsv = "' + $safeDecision + '"',
        'if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }',
        'if (-not (Test-Path -LiteralPath $DecisionCsv)) { throw "Missing decision csv: $DecisionCsv" }',
        '$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]',
        '$d = @(Import-Csv -LiteralPath $DecisionCsv)[0]',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114E Precheck after v0114D" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114E)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "User Accept: $($d.def_user_release_accept)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114E -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114E." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114E_MANUAL_RELEASE_APPROVAL_GATE_ONLY" -ForegroundColor Green'
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
            if ($v.Length -gt 320) { $v = $v.Substring(0,320) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$DecisionBoard,$Evidence,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114E",$Summary.AllowV0114E),
        @("Fail",$Summary.ValidationFail),
        @("Evidence",$Summary.EvidenceRows),
        @("Release",$Summary.UserReleaseAccept),
        @("Mutation","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114D Sandbox Review Seal</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114D · Sandbox Review Seal</h1>")
    [void]$html.AppendLine("<div class='sub'>Review seal only · no apply · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114D 只是審核封存包。下一步 v0114E 仍然只是人工 release approval gate，不是正式 apply。</div><span class='tag'>Review Seal</span><span class='tag'>Manual Gate Draft</span><span class='tag'>No Source Mutation</span><span class='tag'>No Canonical Merge</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114E','def_reason','def_validation_fail','def_user_release_accept','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Manual Release Decision Draft</h2>$(def_Table $DecisionBoard @('def_review_gate','def_user_release_accept','def_user_release_note','def_recommended_decision','def_release_scope','def_validation_fail','def_source_mutation','def_canonical_merge','def_db_write','def_next_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Review Seal Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Evidence Manifest</h2>$(def_Table $Evidence @('def_artifact','def_exists','def_length','def_sha256','def_path') 60)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114C: $(def_Html $Summary.LatestV0114C)<br/>Seal Dir: $(def_Html $Summary.SealDir)<br/>Manual Gate Dir: $(def_Html $Summary.ManualGateDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114D SANDBOX REVIEW SEAL · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Review seal only. No source mutation. No canonical merge. No DB write. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0114C output"
    $latestC = def_GetLatestV0114C
    $outC = Join-Path $latestC "output"
    $sandboxC = Join-Path $latestC "_dryrun_sandbox_only"
    $summaryCPath = Join-Path $outC "VIA_v0114C_SandboxDryRunSimulation_Summary.json"
    $summaryC = def_ReadJson $summaryCPath
    def_Log "OK" "Latest v0114C: $latestC" Green

    def_Progress 2 10 "Resolve v0114C evidence artifacts"
    $readinessCsvC = Join-Path $outC "VIA_v0114C_ReadinessGate.csv"
    $validationCsvC = Join-Path $outC "VIA_v0114C_ValidationMatrix.csv"
    $policyCsv = Join-Path $sandboxC "VIA_v0114C_SIMULATED_POLICY_REGISTRY.csv"
    $aliasCsv = Join-Path $sandboxC "VIA_v0114C_SIMULATED_ALIAS_REGISTRY.csv"
    $rowsCsv = Join-Path $sandboxC "VIA_v0114C_SIMULATED_ROW_MAPPING.csv"
    $actionCsv = Join-Path $sandboxC "VIA_v0114C_DRYRUN_ACTION_PLAN.csv"

    $evidencePaths = @($summaryCPath,$readinessCsvC,$validationCsvC,$policyCsv,$aliasCsv,$rowsCsv,$actionCsv)

    def_Progress 3 10 "Load v0114C evidence"
    $readinessC = def_LoadCsv $readinessCsvC
    $validationC = def_LoadCsv $validationCsvC
    $policyRows = def_LoadCsv $policyCsv
    $aliasRows = def_LoadCsv $aliasCsv
    $simRows = def_LoadCsv $rowsCsv
    $actionRows = def_LoadCsv $actionCsv
    def_Log "OK" "Loaded Policy=$(@($policyRows).Count), Alias=$(@($aliasRows).Count), Rows=$(@($simRows).Count), Actions=$(@($actionRows).Count)" Green

    def_Progress 4 10 "Build evidence manifest"
    $evidence = def_BuildEvidenceManifest -Paths $evidencePaths

    def_Progress 5 10 "Run review seal validation"
    $val = New-Object System.Collections.ArrayList

    foreach ($p in $evidencePaths) {
        def_AddValidation $val "EVIDENCE" "exists: $(Split-Path $p -Leaf)" (Test-Path -LiteralPath $p) "Evidence path check." $p
    }

    $rc = $readinessC[0]
    def_AddValidation $val "UPSTREAM" "v0114C allow v0114D" ((def_GetProp $rc "def_allow_v0114D") -eq "true") ("Gate=" + (def_GetProp $rc "def_gate_status")) $readinessCsvC

    $upstreamFail = @($validationC | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    def_AddValidation $val "UPSTREAM" "v0114C validation pass" ($upstreamFail -eq 0) "Upstream fail=$upstreamFail" $validationCsvC

    def_AddValidation $val "COUNT" "sim policy rows" (@($policyRows).Count -eq 12) "Policy=$(@($policyRows).Count)" $policyCsv
    def_AddValidation $val "COUNT" "sim alias rows" (@($aliasRows).Count -eq 5) "Alias=$(@($aliasRows).Count)" $aliasCsv
    def_AddValidation $val "COUNT" "sim row mapping rows" (@($simRows).Count -eq 149) "Rows=$(@($simRows).Count)" $rowsCsv

    def_Progress 6 10 "Run boundary validation"
    $allRows = @()
    $allRows += $policyRows
    $allRows += $aliasRows
    $allRows += $simRows
    $allRows += $actionRows

    $unsafe = def_CountUnsafe -Rows $allRows
    def_AddValidation $val "SAFETY" "no unsafe flags" ($unsafe -eq 0) "UnsafeFlags=$unsafe"

    $macroChina = @($simRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "MACRO_CHINA" }).Count
    def_AddValidation $val "SAFETY" "MACRO_CHINA excluded" ($macroChina -eq 0) "MACRO_CHINA rows=$macroChina" $rowsCsv

    $rawFred = @($simRows | Where-Object {
        (def_GetProp $_ "def_candidate_canonical_value") -match "(?i)FRED_API_KEY\s*=\s*[A-Za-z0-9_\-]{16,}"
    }).Count
    def_AddValidation $val "SECRET" "FRED raw value not present" ($rawFred -eq 0) "Raw FRED rows=$rawFred" $rowsCsv

    $applyBlocked = @($actionRows | Where-Object { (def_GetProp $_ "def_action") -eq "BLOCK_REAL_APPLY" -and (def_GetProp $_ "def_result") -eq "REAL_APPLY_DISABLED" }).Count
    def_AddValidation $val "APPLY_BOUNDARY" "real apply blocked" ($applyBlocked -eq 1) "Blocked rows=$applyBlocked" $actionCsv

    def_Progress 7 10 "Build manual release gate draft"
    $decisionBoard = def_BuildReviewDecisionBoard -LatestC $latestC -SummaryPath $summaryCPath -Readiness $readinessC -Validation $val

    def_Progress 8 10 "Build readiness seal"
    $readinessD = def_BuildReadiness -Validation $val -DecisionBoard $decisionBoard

    def_Progress 9 10 "Write review seal outputs"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114D_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114D_ReadinessGate.csv"
    $evidenceCsv = Join-Path $def_SEAL_DIR "VIA_v0114D_EvidenceManifest.csv"
    $decisionCsv = Join-Path $def_MANUAL_GATE_DIR "VIA_v0114D_USER_EDIT_ManualReleaseDecision.csv"
    $sealJson = Join-Path $def_SEAL_DIR "VIA_v0114D_ReviewSeal.json"

    def_WriteCsv $val $validationCsv
    def_WriteCsv $readinessD $readinessCsv
    def_WriteCsv $evidence $evidenceCsv
    def_WriteCsv $decisionBoard $decisionCsv

    def_WriteJson $val (Join-Path $def_OUTPUT_DIR "VIA_v0114D_ValidationMatrix.json")
    def_WriteJson $readinessD (Join-Path $def_OUTPUT_DIR "VIA_v0114D_ReadinessGate.json")
    def_WriteJson $evidence (Join-Path $def_SEAL_DIR "VIA_v0114D_EvidenceManifest.json")
    def_WriteJson $decisionBoard (Join-Path $def_MANUAL_GATE_DIR "VIA_v0114D_USER_EDIT_ManualReleaseDecision.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114D_SandboxReviewSeal"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114C = $latestC
        validation_csv = $validationCsv
        readiness_csv = $readinessCsv
        evidence_csv = $evidenceCsv
        decision_csv = $decisionCsv
        validation_fail = (def_GetProp $readinessD[0] "def_validation_fail")
        allow_v0114E = (def_GetProp $readinessD[0] "def_allow_v0114E")
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

    def_WriteJson $seal $sealJson 16

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114E-Precheck-After-v0114D.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -DecisionCsv $decisionCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114D_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114D_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114D_SandboxReviewSeal_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114D.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_SEAL_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_MANUAL_GATE_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Start-Process "' + (def_EscapePsDouble $decisionCsv) + '"',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114E manual release approval gate only.',
        '# No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessD[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114D_SANDBOX_REVIEW_SEAL_READY"
        RunId = $def_RUN_ID
        LatestV0114C = $latestC
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114E = def_GetProp $r0 "def_allow_v0114E"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        UserReleaseAccept = def_GetProp $decisionBoard[0] "def_user_release_accept"
        EvidenceRows = "$(@($evidence).Count)"
        SealDir = $def_SEAL_DIR
        ManualGateDir = $def_MANUAL_GATE_DIR
        DecisionCsv = $decisionCsv
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        SealJson = $sealJson
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; review seal only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114D_SandboxReviewSeal_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessD -Validation $val -DecisionBoard $decisionBoard -Evidence $evidence -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114D Sandbox Review Seal" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114D Sandbox Review Seal COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114E        : $($summary.AllowV0114E)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "User Release Accept : $($summary.UserReleaseAccept)" -ForegroundColor Yellow
    Write-Host "Evidence Rows       : $($summary.EvidenceRows)" -ForegroundColor Cyan
    Write-Host "Decision CSV        : $decisionCsv" -ForegroundColor Cyan
    Write-Host "Seal Dir            : $def_SEAL_DIR" -ForegroundColor Cyan
    Write-Host "Manual Gate Dir     : $def_MANUAL_GATE_DIR" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_SEAL_DIR } catch {}
        try { Start-Process -FilePath $def_MANUAL_GATE_DIR } catch {}
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

