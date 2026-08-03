param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114D_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114E_MANUAL_RELEASE_APPROVAL" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114E_manual_release_approval"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_APPROVAL_DIR = Join-Path $def_RUN_DIR "_manual_release_approval_gate"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114E_ManualReleaseApproval.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114D auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 v0114D readiness reuse",
    "A06 manual approval triple-confirm",
    "A07 no-apply boundary retained",
    "A08 mutation boundary retained",
    "A09 canonical merge boundary retained",
    "A10 DB write boundary retained",
    "A11 evidence carry-forward manifest",
    "A12 release approval CSV/JSON",
    "A13 v0114F precheck generated",
    "A14 blocked-if-no-user-YES",
    "A15 compact HTML approval report"
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
    Write-Progress -Activity "VIA v0114E Manual Release Approval Gate" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114D {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114D_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114D_ROOT) {
            return $def_PARAM_V0114D_ROOT
        }
        throw "Specified v0114D root does not exist: $def_PARAM_V0114D_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0114D_sandbox_review_seal"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114D output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114D_SandboxReviewSeal_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114D output found under: $root"
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

function def_BuildApprovalBoard {
    param(
        [bool]$ConfirmReview,
        [bool]$ConfirmNoApply,
        [bool]$ConfirmBoundary,
        [string]$LatestD,
        [array]$DecisionD,
        [array]$ReadinessD
    )

    $allYes = ($ConfirmReview -and $ConfirmNoApply -and $ConfirmBoundary)

    return @(
        [pscustomobject][ordered]@{
            def_release_gate = "v0114E_MANUAL_RELEASE_APPROVAL"
            def_user_release_accept = $(if ($allYes) { "YES" } else { "" })
            def_user_release_note = $(if ($allYes) { "Approved for v0114F release candidate package only. No apply." } else { "Not approved yet." })
            def_recommended_decision = def_GetProp $DecisionD[0] "def_recommended_decision"
            def_release_scope = "v0114F_release_candidate_package_only_no_apply"
            def_confirm_review_seal = [string]$ConfirmReview
            def_confirm_no_apply = [string]$ConfirmNoApply
            def_confirm_boundary = [string]$ConfirmBoundary
            def_latest_v0114D = $LatestD
            def_upstream_gate = def_GetProp $ReadinessD[0] "def_gate_status"
            def_upstream_allow = def_GetProp $ReadinessD[0] "def_allow_v0114E"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_phase = "v0114F release candidate package only"
        }
    )
}

function def_BuildValidation {
    param(
        [array]$ReadinessD,
        [array]$ValidationD,
        [array]$DecisionD,
        [array]$ApprovalBoard
    )

    $rows = New-Object System.Collections.ArrayList
    $rd = $ReadinessD[0]
    $ab = $ApprovalBoard[0]

    $upstreamFail = @($ValidationD | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    def_AddValidation $rows "UPSTREAM" "v0114D allow v0114E" ((def_GetProp $rd "def_allow_v0114E") -eq "true") ("Gate=" + (def_GetProp $rd "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114D validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "UPSTREAM" "v0114D recommended release review" ((def_GetProp $DecisionD[0] "def_recommended_decision") -eq "READY_FOR_MANUAL_RELEASE_REVIEW") ("Recommended=" + (def_GetProp $DecisionD[0] "def_recommended_decision"))

    def_AddValidation $rows "USER_APPROVAL" "manual release accept YES" ((def_GetProp $ab "def_user_release_accept") -eq "YES") ("UserReleaseAccept=" + (def_GetProp $ab "def_user_release_accept"))
    def_AddValidation $rows "BOUNDARY" "confirm no apply" ((def_GetProp $ab "def_confirm_no_apply") -eq "True") ("ConfirmNoApply=" + (def_GetProp $ab "def_confirm_no_apply"))
    def_AddValidation $rows "BOUNDARY" "confirm no mutation boundary" ((def_GetProp $ab "def_confirm_boundary") -eq "True") ("ConfirmBoundary=" + (def_GetProp $ab "def_confirm_boundary"))

    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $ab "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $ab "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $ab "def_db_write") -eq "false") "db_write=false"

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$ApprovalBoard)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114F_RELEASE_CANDIDATE_PACKAGE_ONLY"
    $allow = "true"
    $reason = "Manual release approval accepted for v0114F package generation only. Apply remains disabled."

    if ($fail -gt 0) {
        $gate = "BLOCKED_MANUAL_RELEASE_APPROVAL_REQUIRED"
        $allow = "false"
        $reason = "Manual release approval incomplete or boundary confirmation missing."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114F = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_user_release_accept = def_GetProp $ApprovalBoard[0] "def_user_release_accept"
            def_release_scope = def_GetProp $ApprovalBoard[0] "def_release_scope"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_apply_enabled = "false"
            def_next_allowed_phase = "v0114F release candidate package only"
        }
    )
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$ApprovalCsv,[string]$Path)

    $safeReady = def_EscapePsDouble $ReadinessCsv
    $safeApproval = def_EscapePsDouble $ApprovalCsv

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '$ReadinessCsv = "' + $safeReady + '"',
        '$ApprovalCsv = "' + $safeApproval + '"',
        'if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }',
        'if (-not (Test-Path -LiteralPath $ApprovalCsv)) { throw "Missing approval csv: $ApprovalCsv" }',
        '$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]',
        '$a = @(Import-Csv -LiteralPath $ApprovalCsv)[0]',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114F Precheck after v0114E" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114F)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "User Accept: $($a.def_user_release_accept)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114F -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114F." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114F_RELEASE_CANDIDATE_PACKAGE_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=200)

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
    param($Summary,$Readiness,$Validation,$ApprovalBoard,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114F",$Summary.AllowV0114F),
        @("Fail",$Summary.ValidationFail),
        @("Release",$Summary.UserReleaseAccept),
        @("Apply","false"),
        @("Mutation","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114E Manual Release Approval Gate</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114E · Manual Release Approval Gate</h1>")
    [void]$html.AppendLine("<div class='sub'>Approval gate only · no apply · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114E 只核准進入 v0114F package generation。這不是正式套用。Apply 仍然 disabled。</div><span class='tag'>Manual Approval</span><span class='tag'>Package Only</span><span class='tag'>Apply Disabled</span><span class='tag'>No Source Mutation</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114F','def_reason','def_validation_fail','def_user_release_accept','def_release_scope','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Approval Board</h2>$(def_Table $ApprovalBoard @('def_release_gate','def_user_release_accept','def_user_release_note','def_release_scope','def_confirm_review_seal','def_confirm_no_apply','def_confirm_boundary','def_upstream_gate','def_source_mutation','def_canonical_merge','def_db_write','def_next_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114D: $(def_Html $Summary.LatestV0114D)<br/>Approval Dir: $(def_Html $Summary.ApprovalDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114E MANUAL RELEASE APPROVAL GATE · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Approval gate only. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0114D output"
    $latestD = def_GetLatestV0114D
    $outD = Join-Path $latestD "output"
    $manualD = Join-Path $latestD "_manual_release_gate_draft"
    def_Log "OK" "Latest v0114D: $latestD" Green

    def_Progress 2 9 "Load v0114D gates"
    $readinessD = def_LoadCsv (Join-Path $outD "VIA_v0114D_ReadinessGate.csv")
    $validationD = def_LoadCsv (Join-Path $outD "VIA_v0114D_ValidationMatrix.csv")
    $decisionD = def_LoadCsv (Join-Path $manualD "VIA_v0114D_USER_EDIT_ManualReleaseDecision.csv")
    def_Log "OK" "Loaded Readiness=$(@($readinessD).Count), Validation=$(@($validationD).Count), Decision=$(@($decisionD).Count)" Green

    def_Progress 3 9 "Manual release confirmation"
    $confirmReview = def_AskYes -Title "CONFIRM v0114D REVIEW SEAL" -Message "確認 v0114D Review Seal 已通過，Fail=0，Evidence 完整。"
    $confirmNoApply = def_AskYes -Title "CONFIRM NO APPLY" -Message "確認 v0114E 只允許進入 v0114F package generation，不執行 apply。"
    $confirmBoundary = def_AskYes -Title "CONFIRM SAFETY BOUNDARY" -Message "確認 No source mutation / No canonical merge / No DB write / FRED raw value forbidden。"

    def_Progress 4 9 "Build approval board"
    $approvalBoard = def_BuildApprovalBoard -ConfirmReview $confirmReview -ConfirmNoApply $confirmNoApply -ConfirmBoundary $confirmBoundary -LatestD $latestD -DecisionD $decisionD -ReadinessD $readinessD

    def_Progress 5 9 "Build validation matrix"
    $validation = def_BuildValidation -ReadinessD $readinessD -ValidationD $validationD -DecisionD $decisionD -ApprovalBoard $approvalBoard

    def_Progress 6 9 "Build readiness gate"
    $readinessE = def_BuildReadiness -Validation $validation -ApprovalBoard $approvalBoard

    def_Progress 7 9 "Write approval outputs"
    $approvalCsv = Join-Path $def_APPROVAL_DIR "VIA_v0114E_ManualReleaseApproval.csv"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114E_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114E_ReadinessGate.csv"

    def_WriteCsv $approvalBoard $approvalCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessE $readinessCsv

    def_WriteJson $approvalBoard (Join-Path $def_APPROVAL_DIR "VIA_v0114E_ManualReleaseApproval.json")
    def_WriteJson $validation (Join-Path $def_OUTPUT_DIR "VIA_v0114E_ValidationMatrix.json")
    def_WriteJson $readinessE (Join-Path $def_OUTPUT_DIR "VIA_v0114E_ReadinessGate.json")

    def_Progress 8 9 "Build precheck, accelerators, next commands"
    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114F-Precheck-After-v0114E.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -ApprovalCsv $approvalCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114E_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114E_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114E_ManualReleaseApproval_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114E.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_APPROVAL_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114F release candidate package only.',
        '# No apply. No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessE[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114E_MANUAL_RELEASE_APPROVAL_READY"
        RunId = $def_RUN_ID
        LatestV0114D = $latestD
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114F = def_GetProp $r0 "def_allow_v0114F"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        UserReleaseAccept = def_GetProp $r0 "def_user_release_accept"
        ApprovalDir = $def_APPROVAL_DIR
        ApprovalCsv = $approvalCsv
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; approval gate only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114E_ManualReleaseApproval_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessE -Validation $validation -ApprovalBoard $approvalBoard -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114E Manual Release Approval Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114E Manual Release Approval COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114F        : $($summary.AllowV0114F)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "User Release Accept : $($summary.UserReleaseAccept)" -ForegroundColor Yellow
    Write-Host "Approval CSV        : $approvalCsv" -ForegroundColor Cyan
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
