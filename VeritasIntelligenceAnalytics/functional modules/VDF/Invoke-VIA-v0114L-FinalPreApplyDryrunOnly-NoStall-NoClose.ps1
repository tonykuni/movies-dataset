param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114K_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114L_final_pre_apply_dryrun_only"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_DRYRUN_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_pre_apply_dryrun_only"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114L_FinalPreApplyDryrunOnly.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114K auto discovery",
    "A02 NoStall no Read-Host",
    "A03 same-session NoClose execution",
    "A04 no child process required",
    "A05 no BASE re-scan",
    "A06 v0114K readiness reuse",
    "A07 execution candidate review carry-forward",
    "A08 source path existence validation",
    "A09 dryrun row compiler",
    "A10 dryrun action-only validation",
    "A11 execution-disabled boundary gate",
    "A12 apply-disabled boundary gate",
    "A13 source-mutation boundary gate",
    "A14 canonical/db-write boundary gate",
    "A15 compact HTML dryrun report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_DRYRUN_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114L Final Pre-Apply Dryrun Only" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114K {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114K_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114K_ROOT) { return $def_PARAM_V0114K_ROOT }
        throw "Specified v0114K root does not exist: $def_PARAM_V0114K_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114K_execution_candidate_review_only"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114K output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $p = def_J $_.FullName "output\VIA_v0114K_ReadinessGate.csv"
            if (-not (Test-Path -LiteralPath $p)) { return $false }
            try {
                $r = @(Import-Csv -LiteralPath $p)[0]
                return ($r.def_allow_v0114L -eq "true" -and $r.def_execution_enabled -eq "false" -and $r.def_apply_enabled -eq "false")
            } catch {
                return $false
            }
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No ready v0114K output found. Need Allow v0114L=true with execution/apply disabled."
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

function def_BuildDryrunRows {
    param([array]$ExecReview)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($e in $ExecReview) {
        $n++
        $srcPath = def_GetProp $e "def_source_path"
        $srcExists = "SKIPPED_EMPTY_SOURCE"
        if (-not [string]::IsNullOrWhiteSpace($srcPath)) {
            $srcExists = [string](Test-Path -LiteralPath $srcPath)
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_dryrun_id = "PRE_APPLY_DRYRUN_{0:0000}" -f $n
            def_source_execution_candidate_id = def_GetProp $e "def_execution_candidate_id"
            def_source_plan_id = def_GetProp $e "def_source_plan_id"
            def_plan_layer = def_GetProp $e "def_plan_layer"
            def_source_file = def_GetProp $e "def_source_file"
            def_source_path = $srcPath
            def_source_exists = $srcExists
            def_dryrun_action = "SIMULATE_ONLY_NO_APPLY"
            def_dryrun_result = "WOULD_PREPARE_FOR_FINAL_AUTHORIZATION_REVIEW"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_delete = "false"
            def_stop_process = "false"
            def_next_gate_required = "v0114M_FINAL_APPLY_AUTHORIZATION_GATE_ONLY"
        })
    }

    return @($rows)
}

function def_CountUnsafe {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_execution_enabled") -eq "true") -or
        ((def_GetProp $_ "def_apply_enabled") -eq "true") -or
        ((def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_delete") -ne "false") -or
        ((def_GetProp $_ "def_stop_process") -ne "false")
    }).Count
}

function def_BuildDisabledDryrunBoundary {
    param([string]$Path)

    $lines = @(
        '$ErrorActionPreference = "Continue"',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114L Disabled Apply Boundary" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "[BLOCKED] v0114L is final pre-apply dryrun only." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow',
        'Write-Host "PowerShell remains open." -ForegroundColor Cyan',
        'return'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_AstCheck {
    param([string]$Path)

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null

    if ($errors -and @($errors).Count -gt 0) {
        return [pscustomobject]@{ Ok = $false; Message = $errors[0].Message }
    }

    return [pscustomobject]@{ Ok = $true; Message = "AST clean" }
}

function def_BuildValidation {
    param(
        [array]$ReadinessK,
        [array]$ValidationK,
        [array]$ExecReview,
        [array]$DryrunRows,
        [string]$DisabledBoundary
    )

    $rows = New-Object System.Collections.ArrayList
    $rk = $ReadinessK[0]

    $upstreamFail = @($ValidationK | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $unsafe = def_CountUnsafe -Rows $DryrunRows
    $badAction = @($DryrunRows | Where-Object { (def_GetProp $_ "def_dryrun_action") -ne "SIMULATE_ONLY_NO_APPLY" }).Count
    $missingGate = @($DryrunRows | Where-Object { (def_GetProp $_ "def_next_gate_required") -ne "v0114M_FINAL_APPLY_AUTHORIZATION_GATE_ONLY" }).Count
    $sourceMissing = @($DryrunRows | Where-Object {
        (def_GetProp $_ "def_source_exists") -eq "False"
    }).Count

    def_AddValidation $rows "UPSTREAM" "v0114K allow v0114L" ((def_GetProp $rk "def_allow_v0114L") -eq "true") ("Gate=" + (def_GetProp $rk "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114K validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "UPSTREAM" "execution disabled upstream" ((def_GetProp $rk "def_execution_enabled") -eq "false") "execution_enabled=false"
    def_AddValidation $rows "UPSTREAM" "apply disabled upstream" ((def_GetProp $rk "def_apply_enabled") -eq "false") "apply_enabled=false"

    def_AddValidation $rows "COUNT" "execution review rows 19" (@($ExecReview).Count -eq 19) ("ExecRows=" + @($ExecReview).Count)
    def_AddValidation $rows "COUNT" "dryrun rows 19" (@($DryrunRows).Count -eq 19) ("DryrunRows=" + @($DryrunRows).Count)

    def_AddValidation $rows "DRYRUN" "dryrun simulate-only actions" ($badAction -eq 0) "BadActionRows=$badAction"
    def_AddValidation $rows "DRYRUN" "next authorization gate required" ($missingGate -eq 0) "MissingNextGate=$missingGate"
    def_AddValidation $rows "DRYRUN" "declared source paths exist" ($sourceMissing -eq 0) "MissingSourceRows=$sourceMissing"

    def_AddValidation $rows "SAFETY" "no unsafe flags in dryrun" ($unsafe -eq 0) "UnsafeFlags=$unsafe"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $rk "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $rk "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $rk "def_db_write") -eq "false") "db_write=false"

    $ast = def_AstCheck -Path $DisabledBoundary
    def_AddValidation $rows "APPLY_BOUNDARY" "disabled dryrun boundary AST clean" $ast.Ok $ast.Message $DisabledBoundary

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$DryrunRows)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114M_FINAL_APPLY_AUTHORIZATION_GATE_ONLY"
    $allow = "true"
    $reason = "Final pre-apply dryrun passed. Next phase may create final apply authorization gate only. No apply executed."

    if ($fail -gt 0) {
        $gate = "BLOCKED_FINAL_PRE_APPLY_DRYRUN_FAILURE"
        $allow = "false"
        $reason = "Final pre-apply dryrun has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114M = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_dryrun_rows = "$(@($DryrunRows).Count)"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114M final apply authorization gate only"
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
        'Write-Host "def VIA · v0114M Precheck after v0114L" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114M)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "DryrunRows : $($r.def_dryrun_rows)" -ForegroundColor Cyan',
        'Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114M -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114M." }',
        'if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114M_FINAL_APPLY_AUTHORIZATION_GATE_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
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
            if ($v.Length -gt 340) { $v = $v.Substring(0,340) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$DryrunRows,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114M",$Summary.AllowV0114M),
        @("Fail",$Summary.ValidationFail),
        @("DryrunRows",$Summary.DryrunRows),
        @("Execution","false"),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114L Final Pre-Apply Dryrun Only</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114L · Final Pre-Apply Dryrun Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Dryrun only · no prompt · no execution · no apply · no mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114L 完成 final pre-apply dryrun。這不是正式 apply。下一步 v0114M 仍然只是 final apply authorization gate。</div><span class='tag'>Dryrun Only</span><span class='tag'>NoStall</span><span class='tag'>Execution Disabled</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114M','def_reason','def_validation_fail','def_dryrun_rows','def_execution_enabled','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Final Pre-Apply Dryrun Rows</h2>$(def_Table $DryrunRows @('def_dryrun_id','def_source_execution_candidate_id','def_plan_layer','def_source_file','def_source_exists','def_dryrun_action','def_dryrun_result','def_next_gate_required','def_execution_enabled','def_apply_enabled','def_db_write') 220)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114K: $(def_Html $Summary.LatestV0114K)<br/>Dryrun Dir: $(def_Html $Summary.DryrunDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114L FINAL PRE-APPLY DRYRUN ONLY · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Dryrun only. No prompt. No execution. No apply. No mutation. No DB write." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest ready v0114K output"
    $latestK = def_GetLatestV0114K
    $outK = def_J $latestK "output"
    $summaryK = def_ReadJson (def_J $outK "VIA_v0114K_ExecutionCandidateReviewOnly_Summary.json")
    def_Log "OK" "Latest ready v0114K: $latestK" Green

    def_Progress 2 10 "Load v0114K readiness and validation"
    $readinessK = def_LoadCsv (def_S $summaryK.ReadinessCsv)
    $validationK = def_LoadCsv (def_S $summaryK.ValidationCsv)

    def_Progress 3 10 "Load execution candidate review"
    $execReview = def_LoadCsv (def_S $summaryK.ExecutionReviewCsv)

    def_Progress 4 10 "Compile final pre-apply dryrun rows"
    $dryrunRows = def_BuildDryrunRows -ExecReview $execReview

    def_Progress 5 10 "Generate disabled dryrun boundary"
    $disabledBoundary = def_J $def_DRYRUN_DIR "Invoke-VIA-v0114L-DISABLED-ApplyBoundary.ps1"
    def_BuildDisabledDryrunBoundary -Path $disabledBoundary

    def_Progress 6 10 "Validate dryrun"
    $validation = def_BuildValidation -ReadinessK $readinessK -ValidationK $validationK -ExecReview $execReview -DryrunRows $dryrunRows -DisabledBoundary $disabledBoundary
    $readinessL = def_BuildReadiness -Validation $validation -DryrunRows $dryrunRows

    def_Progress 7 10 "Write dryrun outputs"
    $dryrunCsv = def_J $def_DRYRUN_DIR "VIA_v0114L_FinalPreApplyDryrunRows.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114L_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114L_ReadinessGate.csv"
    $sealJson = def_J $def_DRYRUN_DIR "VIA_v0114L_FinalPreApplyDryrunSeal.json"

    def_WriteCsv $dryrunRows $dryrunCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessL $readinessCsv

    def_WriteJson $dryrunRows (def_J $def_DRYRUN_DIR "VIA_v0114L_FinalPreApplyDryrunRows.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114L_ValidationMatrix.json")
    def_WriteJson $readinessL (def_J $def_OUTPUT_DIR "VIA_v0114L_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114L_FinalPreApplyDryrunOnly_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114K = $latestK
        dryrun_csv = $dryrunCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        disabled_boundary = $disabledBoundary
        policy = [ordered]@{
            dryrun_only = $true
            execution_enabled = $false
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

    def_Progress 8 10 "Build precheck and accelerators"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114M-Precheck-After-v0114L.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114L_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114L_15Accelerators.json")

    def_Progress 9 10 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114L_FinalPreApplyDryrunOnly_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114L.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_DRYRUN_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $dryrunCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114M final apply authorization gate only.',
        '# v0114L did not execute apply.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessL[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY_READY"
        RunId = $def_RUN_ID
        LatestV0114K = $latestK
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114M = def_GetProp $r0 "def_allow_v0114M"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        DryrunRows = def_GetProp $r0 "def_dryrun_rows"
        ExecutionEnabled = def_GetProp $r0 "def_execution_enabled"
        DryrunDir = $def_DRYRUN_DIR
        DryrunCsv = $dryrunCsv
        DisabledBoundary = $disabledBoundary
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "NoStall; dryrun only; execution disabled; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114L_FinalPreApplyDryrunOnly_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessL -Validation $validation -DryrunRows $dryrunRows -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114L Final Pre-Apply Dryrun Only" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114L Final Pre-Apply Dryrun Only COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114M        : $($summary.AllowV0114M)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Dryrun Rows         : $($summary.DryrunRows)" -ForegroundColor Cyan
    Write-Host "Execution Enabled   : $($summary.ExecutionEnabled)" -ForegroundColor Yellow
    Write-Host "Dryrun CSV          : $dryrunCsv" -ForegroundColor Cyan
    Write-Host "Disabled Boundary   : $disabledBoundary" -ForegroundColor Cyan
    Write-Host "Seal                : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_DRYRUN_DIR } catch {}
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
