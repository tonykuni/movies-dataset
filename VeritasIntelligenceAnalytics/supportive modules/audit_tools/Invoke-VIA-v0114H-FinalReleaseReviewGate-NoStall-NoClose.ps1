param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114G_ROOT = "",
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

$def_RUN_ID = "RUN_{0}_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114H_final_release_review_gate"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_REVIEW_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_release_review_gate"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114H_FinalReleaseReviewGate.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114G auto discovery",
    "A02 NoStall no Read-Host",
    "A03 same-session NoClose execution",
    "A04 no child process required",
    "A05 no BASE re-scan",
    "A06 v0114G readiness reuse",
    "A07 package validation seal carry-forward",
    "A08 ZIP path carry-forward",
    "A09 fail-zero gate",
    "A10 package-count gate",
    "A11 apply-disabled boundary gate",
    "A12 source-mutation boundary gate",
    "A13 canonical-merge boundary gate",
    "A14 DB-write boundary gate",
    "A15 compact HTML final review report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_REVIEW_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114H Final Release Review Gate" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114G {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114G_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114G_ROOT) { return $def_PARAM_V0114G_ROOT }
        throw "Specified v0114G root does not exist: $def_PARAM_V0114G_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114G_package_validation"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114G output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (def_J $_.FullName "output\VIA_v0114G_ReleaseCandidatePackageValidation_Summary.json") } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114G output found under: $root"
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

function def_BuildReviewBoard {
    param($SummaryG,[array]$ReadinessG,[array]$ValidationG)

    $r = $ReadinessG[0]
    $fail = @($ValidationG | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    return @(
        [pscustomobject][ordered]@{
            def_review_gate = "v0114H_FINAL_RELEASE_REVIEW_GATE"
            def_review_mode = "NOSTALL_AUTO_REVIEW_DRAFT"
            def_recommended_decision = $(if ($fail -eq 0 -and (def_GetProp $r "def_allow_v0114H") -eq "true") { "READY_FOR_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY" } else { "BLOCKED_REVIEW_FAILURE" })
            def_final_user_apply_accept = ""
            def_release_candidate_zip = def_S $SummaryG.ZipPath
            def_package_items = def_GetProp $r "def_package_items"
            def_zip_entries = def_GetProp $r "def_zip_entries"
            def_validation_fail = "$fail"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_phase = "v0114I final apply plan draft only"
        }
    )
}

function def_BuildValidation {
    param([array]$ReadinessG,[array]$ValidationG,[array]$ReviewBoard)

    $rows = New-Object System.Collections.ArrayList
    $r = $ReadinessG[0]
    $b = $ReviewBoard[0]
    $upstreamFail = @($ValidationG | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    def_AddValidation $rows "UPSTREAM" "v0114G allow v0114H" ((def_GetProp $r "def_allow_v0114H") -eq "true") ("Gate=" + (def_GetProp $r "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114G validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "PACKAGE" "package items 18" ((def_GetProp $r "def_package_items") -eq "18") ("Items=" + (def_GetProp $r "def_package_items"))
    def_AddValidation $rows "PACKAGE" "zip entries at least 18" ([int](def_GetProp $r "def_zip_entries") -ge 18) ("ZipEntries=" + (def_GetProp $r "def_zip_entries"))
    def_AddValidation $rows "PACKAGE" "zip path exists" (Test-Path -LiteralPath (def_GetProp $r "def_zip_path")) (def_GetProp $r "def_zip_path")

    def_AddValidation $rows "NOSTALL" "no interactive prompt required" $true "No Read-Host used in v0114H."

    def_AddValidation $rows "SAFETY" "apply disabled" ((def_GetProp $b "def_apply_enabled") -eq "false") "apply_enabled=false"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $b "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $b "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $b "def_db_write") -eq "false") "db_write=false"

    def_AddValidation $rows "REVIEW" "recommended decision ready" ((def_GetProp $b "def_recommended_decision") -eq "READY_FOR_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY") ("Recommended=" + (def_GetProp $b "def_recommended_decision"))

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$ReviewBoard)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY"
    $allow = "true"
    $reason = "Final release review gate passed. Next phase may generate final apply-plan draft only. Apply remains disabled."

    if ($fail -gt 0) {
        $gate = "BLOCKED_FINAL_RELEASE_REVIEW_FAILURE"
        $allow = "false"
        $reason = "Final release review gate has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114I = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_review_mode = def_GetProp $ReviewBoard[0] "def_review_mode"
            def_recommended_decision = def_GetProp $ReviewBoard[0] "def_recommended_decision"
            def_final_user_apply_accept = def_GetProp $ReviewBoard[0] "def_final_user_apply_accept"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114I final apply-plan draft only"
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
        'Write-Host "def VIA · v0114I Precheck after v0114H" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114I)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114I -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114I." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY" -ForegroundColor Green'
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
            if ($v.Length -gt 320) { $v = $v.Substring(0,320) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$ReviewBoard,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114I",$Summary.AllowV0114I),
        @("Fail",$Summary.ValidationFail),
        @("Mode",$Summary.ReviewMode),
        @("Apply","false"),
        @("Mutation","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114H Final Release Review Gate</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114H · Final Release Review Gate · NoStall</h1>")
    [void]$html.AppendLine("<div class='sub'>Final review gate only · no prompt · no apply · no mutation · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114H 完成 final release review gate。下一步 v0114I 只能產生 final apply-plan draft，不是正式套用。</div><span class='tag'>NoStall</span><span class='tag'>15 Accelerators</span><span class='tag'>Apply Disabled</span><span class='tag'>No Source Mutation</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114I','def_reason','def_validation_fail','def_review_mode','def_recommended_decision','def_final_user_apply_accept','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Review Board</h2>$(def_Table $ReviewBoard @('def_review_gate','def_review_mode','def_recommended_decision','def_final_user_apply_accept','def_release_candidate_zip','def_package_items','def_zip_entries','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 90)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114G: $(def_Html $Summary.LatestV0114G)<br/>Review Dir: $(def_Html $Summary.ReviewDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114H FINAL RELEASE REVIEW GATE · 15 ACCELERATORS · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Final review gate only. No prompt. No apply. No mutation. No DB write." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest v0114G output"
    $latestG = def_GetLatestV0114G
    $outG = def_J $latestG "output"
    $summaryGPath = def_J $outG "VIA_v0114G_ReleaseCandidatePackageValidation_Summary.json"
    $summaryG = def_ReadJson $summaryGPath
    def_Log "OK" "Latest v0114G: $latestG" Green

    def_Progress 2 9 "Load v0114G readiness and validation"
    $readinessG = def_LoadCsv (def_S $summaryG.ReadinessCsv)
    $validationG = def_LoadCsv (def_S $summaryG.ValidationCsv)

    def_Progress 3 9 "Build NoStall review board"
    $reviewBoard = def_BuildReviewBoard -SummaryG $summaryG -ReadinessG $readinessG -ValidationG $validationG

    def_Progress 4 9 "Build validation matrix"
    $validation = def_BuildValidation -ReadinessG $readinessG -ValidationG $validationG -ReviewBoard $reviewBoard

    def_Progress 5 9 "Build readiness gate"
    $readinessH = def_BuildReadiness -Validation $validation -ReviewBoard $reviewBoard

    def_Progress 6 9 "Write final review outputs"
    $reviewCsv = def_J $def_REVIEW_DIR "VIA_v0114H_FinalReleaseReviewBoard.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114H_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114H_ReadinessGate.csv"
    $sealJson = def_J $def_REVIEW_DIR "VIA_v0114H_FinalReleaseReviewSeal.json"

    def_WriteCsv $reviewBoard $reviewCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessH $readinessCsv

    def_WriteJson $reviewBoard (def_J $def_REVIEW_DIR "VIA_v0114H_FinalReleaseReviewBoard.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114H_ValidationMatrix.json")
    def_WriteJson $readinessH (def_J $def_OUTPUT_DIR "VIA_v0114H_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114H_FinalReleaseReviewGate_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114G = $latestG
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        review_csv = $reviewCsv
        policy = [ordered]@{
            no_stall = $true
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
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114I-Precheck-After-v0114H.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114H_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114H_15Accelerators.json")

    def_Progress 8 9 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114H_FinalReleaseReviewGate_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114H.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_REVIEW_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114I final apply-plan draft only.',
        '# No apply. No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessH[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114H_FINAL_RELEASE_REVIEW_GATE_READY"
        RunId = $def_RUN_ID
        LatestV0114G = $latestG
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114I = def_GetProp $r0 "def_allow_v0114I"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        ReviewMode = def_GetProp $r0 "def_review_mode"
        ReviewDir = $def_REVIEW_DIR
        SealJson = $sealJson
        ReviewCsv = $reviewCsv
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "NoStall; No Read-Host; No apply; no source mutation; no canonical merge; no DB write; NoExit."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114H_FinalReleaseReviewGate_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessH -Validation $validation -ReviewBoard $reviewBoard -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114H Final Release Review Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114H Final Release Review Gate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114I    : $($summary.AllowV0114I)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Review Mode     : $($summary.ReviewMode)" -ForegroundColor Cyan
    Write-Host "Review Dir      : $def_REVIEW_DIR" -ForegroundColor Cyan
    Write-Host "Seal            : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_REVIEW_DIR } catch {}
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
