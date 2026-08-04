param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114I_ROOT = "",
    [string]$def_PARAM_FINAL_USER_APPLY_ACCEPT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_APPROVAL_PHRASE = "YES_I_ACCEPT_FINAL_APPLY_REVIEW_NEXT_ONLY_NO_APPLY_IN_v0114J"
$def_RUN_ID = "RUN_{0}_VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")

$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114J_explicit_final_user_approval_gate"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_APPROVAL_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_explicit_final_user_approval_gate"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114J_ExplicitFinalUserApprovalGate.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114I auto discovery",
    "A02 NoStall no Read-Host",
    "A03 exact approval phrase gate",
    "A04 same-session NoClose execution",
    "A05 no child process required",
    "A06 no BASE re-scan",
    "A07 v0114I readiness reuse",
    "A08 apply-plan draft carry-forward",
    "A09 future gate validation",
    "A10 fail-zero gate",
    "A11 apply-disabled boundary gate",
    "A12 source-mutation boundary gate",
    "A13 canonical-merge boundary gate",
    "A14 DB-write boundary gate",
    "A15 compact HTML approval report"
)

function def_S {
    param($Value)
    if ($null -eq $Value) { return "" }
    try { return [string]$Value } catch { return "" }
}

function def_J {
    param([string]$Base,[string]$Child)
    return (Join-Path -Path $Base -ChildPath $Child)
}

function def_EnsureDir {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_APPROVAL_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114J Explicit Final User Approval Gate" -Status $Status -PercentComplete $pct
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
    if (-not (Test-Path -LiteralPath $Path)) { throw "CSV missing: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

function def_ReadJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "JSON missing: $Path" }
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
    param($Object,[string]$Path,[int]$Depth = 18)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_EscapePsDouble {
    param([string]$Text)
    return (def_S $Text).Replace('`','``').Replace('"','`"')
}

function def_GetLatestV0114I {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114I_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114I_ROOT) { return $def_PARAM_V0114I_ROOT }
        throw "Specified v0114I root does not exist: $def_PARAM_V0114I_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114I_final_apply_plan_draft_only"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114I output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (def_J $_.FullName "output\VIA_v0114I_FinalApplyPlanDraftOnly_Summary.json") } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114I output found under: $root"
    }

    return $candidates[0].FullName
}

function def_AddValidation {
    param([System.Collections.ArrayList]$Rows,[string]$Layer,[string]$Name,[bool]$Pass,[string]$Message,[string]$Path = "")

    [void]$Rows.Add([pscustomobject][ordered]@{
        def_layer = $Layer
        def_test = $Name
        def_status = $(if ($Pass) { "PASS" } else { "FAIL" })
        def_risk = $(if ($Pass) { "LOW" } else { "HIGH" })
        def_message = $Message
        def_path = $Path
    })
}

function def_BuildApprovalBoard {
    param([string]$LatestI,[array]$ReadinessI,[array]$ApplyPlan)

    $approved = (($def_PARAM_FINAL_USER_APPLY_ACCEPT.Trim()) -eq $def_APPROVAL_PHRASE)

    return @(
        [pscustomobject][ordered]@{
            def_approval_gate = "v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE_ONLY"
            def_approval_mode = "NOSTALL_EXACT_PARAMETER_ONLY"
            def_required_phrase = $def_APPROVAL_PHRASE
            def_final_user_apply_accept = $(if ($approved) { "YES" } else { "" })
            def_user_input_value = $(if ($approved) { "MATCHED_APPROVAL_PHRASE" } else { "NOT_PROVIDED_OR_NOT_MATCHED" })
            def_approval_result = $(if ($approved) { "APPROVED_FOR_v0114K_REVIEW_ONLY" } else { "BLOCKED_EXPLICIT_APPROVAL_REQUIRED" })
            def_latest_v0114I = $LatestI
            def_apply_plan_rows = "$(@($ApplyPlan).Count)"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_phase = $(if ($approved) { "v0114K final apply execution candidate review only" } else { "manual explicit approval still required" })
        }
    )
}

function def_BuildValidation {
    param([array]$ReadinessI,[array]$ValidationI,[array]$ApplyPlan,[array]$ApprovalBoard)

    $rows = New-Object System.Collections.ArrayList
    $ri = $ReadinessI[0]
    $ab = $ApprovalBoard[0]

    $upstreamFail = @($ValidationI | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $realApplyRows = @($ApplyPlan | Where-Object { (def_GetProp $_ "def_plan_action") -notin @("DRAFT_ONLY_NO_APPLY","BLOCK_REAL_APPLY") }).Count
    $unsafeRows = @($ApplyPlan | Where-Object {
        (def_GetProp $_ "def_apply_enabled") -ne "false" -or
        (def_GetProp $_ "def_source_mutation") -ne "false" -or
        (def_GetProp $_ "def_canonical_merge") -ne "false" -or
        (def_GetProp $_ "def_db_write") -ne "false" -or
        (def_GetProp $_ "def_delete") -ne "false" -or
        (def_GetProp $_ "def_stop_process") -ne "false"
    }).Count

    def_AddValidation $rows "UPSTREAM" "v0114I allow v0114J" ((def_GetProp $ri "def_allow_v0114J") -eq "true") ("Gate=" + (def_GetProp $ri "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114I validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "PLAN" "apply plan rows 19" (@($ApplyPlan).Count -eq 19) ("PlanRows=" + @($ApplyPlan).Count)
    def_AddValidation $rows "PLAN" "no real apply action in v0114I plan" ($realApplyRows -eq 0) "RealApplyRows=$realApplyRows"
    def_AddValidation $rows "SAFETY" "no unsafe flags in plan" ($unsafeRows -eq 0) "UnsafeRows=$unsafeRows"
    def_AddValidation $rows "NOSTALL" "no Read-Host in v0114J" $true "Approval is parameter-only; no blocking prompt."

    $approved = ((def_GetProp $ab "def_final_user_apply_accept") -eq "YES")
    def_AddValidation $rows "USER_APPROVAL" "explicit final approval phrase matched" $approved ("ApprovalResult=" + (def_GetProp $ab "def_approval_result"))

    def_AddValidation $rows "SAFETY" "apply disabled in v0114J" ((def_GetProp $ab "def_apply_enabled") -eq "false") "apply_enabled=false"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $ab "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $ab "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $ab "def_db_write") -eq "false") "db_write=false"

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$ApprovalBoard)

    $approvalYes = ((def_GetProp $ApprovalBoard[0] "def_final_user_apply_accept") -eq "YES")
    $hardFail = @($Validation | Where-Object {
        (def_GetProp $_ "def_status") -ne "PASS" -and
        (def_GetProp $_ "def_layer") -ne "USER_APPROVAL"
    }).Count

    $approvalFail = @($Validation | Where-Object {
        (def_GetProp $_ "def_status") -ne "PASS" -and
        (def_GetProp $_ "def_layer") -eq "USER_APPROVAL"
    }).Count

    if ($hardFail -eq 0 -and $approvalYes) {
        $gate = "READY_FOR_v0114K_FINAL_APPLY_EXECUTION_CANDIDATE_REVIEW_ONLY"
        $allow = "true"
        $reason = "Explicit approval phrase matched. Next phase may generate final execution candidate review only. v0114J still did not apply."
    } elseif ($hardFail -eq 0 -and -not $approvalYes) {
        $gate = "BLOCKED_EXPLICIT_FINAL_USER_APPROVAL_REQUIRED"
        $allow = "false"
        $reason = "All technical gates pass, but explicit final approval phrase is missing. This is expected default NoStall state."
    } else {
        $gate = "BLOCKED_FINAL_APPROVAL_GATE_TECHNICAL_FAILURE"
        $allow = "false"
        $reason = "Technical validation failed."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114K = $allow
            def_reason = $reason
            def_validation_fail = "$($hardFail + $approvalFail)"
            def_technical_fail = "$hardFail"
            def_approval_fail = "$approvalFail"
            def_final_user_apply_accept = def_GetProp $ApprovalBoard[0] "def_final_user_apply_accept"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = $(if ($allow -eq "true") { "v0114K final apply execution candidate review only" } else { "rerun v0114J with exact approval phrase if truly intended" })
        }
    )
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$Path)

    $safeReady = def_EscapePsDouble $ReadinessCsv

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '$ReadinessCsv = "' + $safeReady + '"',
        'if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }',
        '$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114K Precheck after v0114J" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114K)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Tech Fail  : $($r.def_technical_fail)" -ForegroundColor Yellow',
        'Write-Host "Approval   : $($r.def_final_user_apply_accept)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114K -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114K. Explicit final approval may be missing." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114K_FINAL_APPLY_EXECUTION_CANDIDATE_REVIEW_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
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
            if ($v.Length -gt 340) { $v = $v.Substring(0,340) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$ApprovalBoard,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114K",$Summary.AllowV0114K),
        @("TechFail",$Summary.TechnicalFail),
        @("Approval",$Summary.FinalUserApplyAccept),
        @("Apply","false"),
        @("Mutation","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114J Explicit Final User Approval Gate</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114J · Explicit Final User Approval Gate · NoStall</h1>")
    [void]$html.AppendLine("<div class='sub'>Approval gate only · parameter-only · no prompt · no apply · no mutation · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114J 不會自動核准，也不會 apply。預設會被 explicit approval gate 擋下；若使用 exact phrase 參數，才允許進 v0114K review-only。</div><span class='tag'>Explicit Approval Gate</span><span class='tag'>NoStall</span><span class='tag'>Parameter Only</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114K','def_reason','def_validation_fail','def_technical_fail','def_approval_fail','def_final_user_apply_accept','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Approval Board</h2>$(def_Table $ApprovalBoard @('def_approval_gate','def_approval_mode','def_required_phrase','def_final_user_apply_accept','def_user_input_value','def_approval_result','def_apply_plan_rows','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114I: $(def_Html $Summary.LatestV0114I)<br/>Approval Dir: $(def_Html $Summary.ApprovalDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114J EXPLICIT FINAL USER APPROVAL GATE · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Approval gate only. No prompt. No apply. No mutation. No canonical merge. No DB write." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0114I output"
    $latestI = def_GetLatestV0114I
    $outI = def_J $latestI "output"
    $planI = def_J $latestI "_final_apply_plan_draft_only"
    $summaryI = def_ReadJson (def_J $outI "VIA_v0114I_FinalApplyPlanDraftOnly_Summary.json")
    def_Log "OK" "Latest v0114I: $latestI" Green

    def_Progress 2 9 "Load v0114I readiness, validation, plan"
    $readinessI = def_LoadCsv (def_S $summaryI.ReadinessCsv)
    $validationI = def_LoadCsv (def_S $summaryI.ValidationCsv)
    $applyPlan = def_LoadCsv (def_S $summaryI.PlanCsv)

    def_Progress 3 9 "Build explicit approval board"
    $approvalBoard = def_BuildApprovalBoard -LatestI $latestI -ReadinessI $readinessI -ApplyPlan $applyPlan

    def_Progress 4 9 "Build validation matrix"
    $validation = def_BuildValidation -ReadinessI $readinessI -ValidationI $validationI -ApplyPlan $applyPlan -ApprovalBoard $approvalBoard

    def_Progress 5 9 "Build readiness gate"
    $readinessJ = def_BuildReadiness -Validation $validation -ApprovalBoard $approvalBoard

    def_Progress 6 9 "Write approval outputs"
    $approvalCsv = def_J $def_APPROVAL_DIR "VIA_v0114J_ExplicitFinalUserApprovalGate.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114J_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114J_ReadinessGate.csv"
    $sealJson = def_J $def_APPROVAL_DIR "VIA_v0114J_ExplicitFinalUserApprovalSeal.json"

    def_WriteCsv $approvalBoard $approvalCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessJ $readinessCsv

    def_WriteJson $approvalBoard (def_J $def_APPROVAL_DIR "VIA_v0114J_ExplicitFinalUserApprovalGate.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114J_ValidationMatrix.json")
    def_WriteJson $readinessJ (def_J $def_OUTPUT_DIR "VIA_v0114J_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114J_ExplicitFinalUserApprovalGate_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114I = $latestI
        approval_csv = $approvalCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        exact_required_phrase = $def_APPROVAL_PHRASE
        policy = [ordered]@{
            approval_gate_only = $true
            interactive_prompt = $false
            apply_enabled = $false
            source_mutation = $false
            canonical_merge = $false
            db_write = $false
            delete = $false
            stop_process = $false
            no_close = $true
        }
    }

    def_WriteJson $seal $sealJson 18

    def_Progress 7 9 "Build precheck and accelerators"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114K-Precheck-After-v0114J.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114J_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114J_15Accelerators.json")

    def_Progress 8 9 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114J_ExplicitFinalUserApprovalGate_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114J.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_APPROVAL_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# If blocked only by approval, rerun v0114J with:',
        '# -def_PARAM_FINAL_USER_APPLY_ACCEPT "YES_I_ACCEPT_FINAL_APPLY_REVIEW_NEXT_ONLY_NO_APPLY_IN_v0114J"',
        '# v0114J never applies anything.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessJ[0]
    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE_READY"
        RunId = $def_RUN_ID
        LatestV0114I = $latestI
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114K = def_GetProp $r0 "def_allow_v0114K"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        TechnicalFail = def_GetProp $r0 "def_technical_fail"
        ApprovalFail = def_GetProp $r0 "def_approval_fail"
        FinalUserApplyAccept = def_GetProp $r0 "def_final_user_apply_accept"
        ApprovalDir = $def_APPROVAL_DIR
        ApprovalCsv = $approvalCsv
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        RequiredPhrase = $def_APPROVAL_PHRASE
        Policy = "NoStall; exact parameter approval only; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114J_ExplicitFinalUserApprovalGate_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessJ -Validation $validation -ApprovalBoard $approvalBoard -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114J Explicit Final User Approval Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114J Explicit Final User Approval Gate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114K        : $($summary.AllowV0114K)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor Yellow
    Write-Host "Technical Fail      : $($summary.TechnicalFail)" -ForegroundColor Yellow
    Write-Host "Approval Fail       : $($summary.ApprovalFail)" -ForegroundColor Yellow
    Write-Host "Final User Accept   : $($summary.FinalUserApplyAccept)" -ForegroundColor Yellow
    Write-Host "Required Phrase     : $def_APPROVAL_PHRASE" -ForegroundColor Cyan
    Write-Host "Approval CSV        : $approvalCsv" -ForegroundColor Cyan
    Write-Host "Seal                : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_APPROVAL_DIR } catch {}
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
