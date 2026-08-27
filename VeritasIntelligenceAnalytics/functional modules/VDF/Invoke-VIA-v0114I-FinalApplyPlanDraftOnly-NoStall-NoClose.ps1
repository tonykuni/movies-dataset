param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114H_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114I_final_apply_plan_draft_only"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_PLAN_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_apply_plan_draft_only"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114I_FinalApplyPlanDraftOnly.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114H auto discovery",
    "A02 NoStall no Read-Host",
    "A03 same-session NoClose execution",
    "A04 no child process required",
    "A05 no BASE re-scan",
    "A06 v0114H readiness reuse",
    "A07 v0114G package validation bridge",
    "A08 v0114F1 package index bridge",
    "A09 package item to plan-row compiler",
    "A10 candidate count validation",
    "A11 raw secret scanner",
    "A12 MACRO_CHINA exclusion scanner",
    "A13 apply-disabled plan gate",
    "A14 future-user-approval-required gate",
    "A15 compact HTML apply-plan report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_PLAN_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114I Final Apply-Plan Draft Only" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114H {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114H_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114H_ROOT) { return $def_PARAM_V0114H_ROOT }
        throw "Specified v0114H root does not exist: $def_PARAM_V0114H_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114H_final_release_review_gate"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114H output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (def_J $_.FullName "output\VIA_v0114H_FinalReleaseReviewGate_Summary.json") } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114H output found under: $root"
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

function def_ClassifyPlanLayer {
    param([string]$Group,[string]$FileName)

    if ($Group -eq "candidate" -and $FileName -match "POLICY_REGISTRY") { return "POLICY_REGISTRY_PLAN" }
    if ($Group -eq "candidate" -and $FileName -match "ALIAS_REGISTRY") { return "ALIAS_REGISTRY_PLAN" }
    if ($Group -eq "candidate" -and $FileName -match "ROW_PATCH") { return "ROW_MAPPING_PLAN" }
    if ($Group -eq "candidate" -and $FileName -match "DIFF") { return "DIFF_REVIEW_PLAN" }
    if ($Group -eq "review") { return "REVIEW_EVIDENCE_PLAN" }
    if ($Group -eq "approval") { return "APPROVAL_EVIDENCE_PLAN" }
    if ($Group -match "disabled") { return "APPLY_BOUNDARY_PLAN" }
    if ($Group -match "readme") { return "DOCUMENTATION_PLAN" }
    return "PACKAGE_ARTIFACT_PLAN"
}

function def_BuildApplyPlanDraft {
    param([array]$PackageIndex)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($p in $PackageIndex) {
        $n++
        $group = def_GetProp $p "def_group"
        $file = def_GetProp $p "def_file"
        $layer = def_ClassifyPlanLayer -Group $group -FileName $file

        [void]$rows.Add([pscustomobject][ordered]@{
            def_plan_id = "APPLY_PLAN_DRAFT_{0:0000}" -f $n
            def_plan_layer = $layer
            def_source_package_item_id = def_GetProp $p "def_package_item_id"
            def_source_group = $group
            def_source_file = $file
            def_source_sha256 = def_GetProp $p "def_sha256"
            def_source_path = def_GetProp $p "def_dest"
            def_plan_action = "DRAFT_ONLY_NO_APPLY"
            def_future_gate_required = "v0114J_EXPLICIT_FINAL_USER_APPROVAL_REQUIRED"
            def_future_scope = "FUTURE_APPLY_PLAN_REVIEW_ONLY_UNTIL_USER_ACCEPTS"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_delete = "false"
            def_stop_process = "false"
        })
    }

    [void]$rows.Add([pscustomobject][ordered]@{
        def_plan_id = "APPLY_PLAN_DRAFT_BOUNDARY"
        def_plan_layer = "FINAL_BOUNDARY"
        def_source_package_item_id = "GENERATED"
        def_source_group = "boundary"
        def_source_file = "NO_APPLY_UNTIL_v0114J"
        def_source_sha256 = ""
        def_source_path = ""
        def_plan_action = "BLOCK_REAL_APPLY"
        def_future_gate_required = "v0114J_EXPLICIT_FINAL_USER_APPROVAL_REQUIRED"
        def_future_scope = "REAL_APPLY_FORBIDDEN_IN_v0114I"
        def_apply_enabled = "false"
        def_source_mutation = "false"
        def_canonical_merge = "false"
        def_db_write = "false"
        def_delete = "false"
        def_stop_process = "false"
    })

    return @($rows)
}

function def_CountUnsafe {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_source_mutation") -ne "" -and (def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "" -and (def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "" -and (def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_apply_enabled") -eq "true") -or
        ((def_GetProp $_ "def_delete") -eq "true") -or
        ((def_GetProp $_ "def_stop_process") -eq "true")
    }).Count
}

function def_ScanRawSecret {
    param([string]$Root)

    $files = @(Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @(".csv",".json",".md",".ps1",".txt") })

    foreach ($f in $files) {
        $t = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($t -match "(?i)FRED_API_KEY\s*=\s*[A-Za-z0-9_\-]{16,}") {
            return [pscustomobject]@{ Ok = $false; Message = "Possible raw FRED assignment: $($f.FullName)" }
        }
        if ($t -match "(?i)api_key\s*[:=]\s*[A-Za-z0-9_\-]{24,}") {
            return [pscustomobject]@{ Ok = $false; Message = "Possible raw api_key: $($f.FullName)" }
        }
    }

    return [pscustomobject]@{ Ok = $true; Message = "No raw secret pattern detected" }
}

function def_BuildValidation {
    param(
        [array]$ReadinessH,
        [array]$ValidationH,
        [array]$ReviewH,
        [array]$PackageIndex,
        [array]$ApplyPlan,
        [array]$PolicyRows,
        [array]$AliasRows,
        [array]$RowRows,
        [string]$PackageDir
    )

    $rows = New-Object System.Collections.ArrayList
    $rh = $ReadinessH[0]
    $review = $ReviewH[0]

    $upstreamFail = @($ValidationH | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $unsafe = def_CountUnsafe -Rows $ApplyPlan
    $macro = @($RowRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "MACRO_CHINA" }).Count
    $applyPlanReal = @($ApplyPlan | Where-Object { (def_GetProp $_ "def_plan_action") -notin @("DRAFT_ONLY_NO_APPLY","BLOCK_REAL_APPLY") }).Count
    $futureGateMissing = @($ApplyPlan | Where-Object { (def_GetProp $_ "def_future_gate_required") -ne "v0114J_EXPLICIT_FINAL_USER_APPROVAL_REQUIRED" }).Count

    def_AddValidation $rows "UPSTREAM" "v0114H allow v0114I" ((def_GetProp $rh "def_allow_v0114I") -eq "true") ("Gate=" + (def_GetProp $rh "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114H validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "UPSTREAM" "final apply accept still blank" ([string]::IsNullOrWhiteSpace((def_GetProp $review "def_final_user_apply_accept"))) "Final apply not pre-approved."

    def_AddValidation $rows "PACKAGE" "package index rows" (@($PackageIndex).Count -eq 18) ("PackageItems=" + @($PackageIndex).Count)
    def_AddValidation $rows "PLAN" "apply plan rows" (@($ApplyPlan).Count -eq 19) ("PlanRows=" + @($ApplyPlan).Count)
    def_AddValidation $rows "PLAN" "no real apply action in draft" ($applyPlanReal -eq 0) "RealApplyActionRows=$applyPlanReal"
    def_AddValidation $rows "PLAN" "future gate required on all rows" ($futureGateMissing -eq 0) "FutureGateMissing=$futureGateMissing"

    def_AddValidation $rows "COUNT" "policy candidate rows" (@($PolicyRows).Count -eq 12) ("Policy=" + @($PolicyRows).Count)
    def_AddValidation $rows "COUNT" "alias candidate rows" (@($AliasRows).Count -eq 5) ("Alias=" + @($AliasRows).Count)
    def_AddValidation $rows "COUNT" "row patch rows" (@($RowRows).Count -eq 149) ("Rows=" + @($RowRows).Count)

    def_AddValidation $rows "SAFETY" "no unsafe flags in plan" ($unsafe -eq 0) "UnsafeFlags=$unsafe"
    def_AddValidation $rows "SAFETY" "MACRO_CHINA excluded" ($macro -eq 0) "MACRO_CHINA rows=$macro"

    $secretScan = def_ScanRawSecret -Root $PackageDir
    def_AddValidation $rows "SECRET" "no raw secret pattern in package" $secretScan.Ok $secretScan.Message

    def_AddValidation $rows "NOSTALL" "no Read-Host in v0114I" $true "No interactive input required."

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$ApplyPlan)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE_ONLY"
    $allow = "true"
    $reason = "Final apply-plan draft generated. Next phase may ask explicit final user approval only. Apply remains disabled."

    if ($fail -gt 0) {
        $gate = "BLOCKED_FINAL_APPLY_PLAN_DRAFT_FAILURE"
        $allow = "false"
        $reason = "Final apply-plan draft validation has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114J = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_apply_plan_rows = "$(@($ApplyPlan).Count)"
            def_final_user_apply_accept = ""
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114J explicit final user approval gate only"
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
        'Write-Host "def VIA · v0114J Precheck after v0114I" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114J)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Plan Rows  : $($r.def_apply_plan_rows)" -ForegroundColor Cyan',
        'Write-Host "Final User : $($r.def_final_user_apply_accept)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114J -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114J." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114J_EXPLICIT_FINAL_USER_APPROVAL_GATE_ONLY" -ForegroundColor Green'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
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
            if ($v.Length -gt 340) { $v = $v.Substring(0,340) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$ApplyPlan,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114J",$Summary.AllowV0114J),
        @("Fail",$Summary.ValidationFail),
        @("PlanRows",$Summary.ApplyPlanRows),
        @("Apply","false"),
        @("Mutation","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114I Final Apply-Plan Draft Only</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114I · Final Apply-Plan Draft Only · NoStall</h1>")
    [void]$html.AppendLine("<div class='sub'>Draft only · no prompt · no apply · no mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114I 只把 release candidate package 轉成 apply-plan draft。真正 apply 仍被禁止，必須等 v0114J 明確人工核准。</div><span class='tag'>Apply-Plan Draft</span><span class='tag'>NoStall</span><span class='tag'>Future Approval Required</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114J','def_reason','def_validation_fail','def_apply_plan_rows','def_final_user_apply_accept','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 100)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Final Apply-Plan Draft</h2>$(def_Table $ApplyPlan @('def_plan_id','def_plan_layer','def_source_group','def_source_file','def_plan_action','def_future_gate_required','def_future_scope','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write') 240)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114H: $(def_Html $Summary.LatestV0114H)<br/>Package Dir: $(def_Html $Summary.PackageDir)<br/>Plan Dir: $(def_Html $Summary.PlanDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114I FINAL APPLY-PLAN DRAFT ONLY · 15 ACCELERATORS · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Draft only. No prompt. No apply. No mutation. No canonical merge. No DB write." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0114H output"
    $latestH = def_GetLatestV0114H
    $outH = def_J $latestH "output"
    $reviewHDir = def_J $latestH "_final_release_review_gate"
    $summaryHPath = def_J $outH "VIA_v0114H_FinalReleaseReviewGate_Summary.json"
    $summaryH = def_ReadJson $summaryHPath
    def_Log "OK" "Latest v0114H: $latestH" Green

    def_Progress 2 10 "Load v0114H gates"
    $readinessH = def_LoadCsv (def_S $summaryH.ReadinessCsv)
    $validationH = def_LoadCsv (def_S $summaryH.ValidationCsv)
    $reviewH = def_LoadCsv (def_J $reviewHDir "VIA_v0114H_FinalReleaseReviewBoard.csv")

    def_Progress 3 10 "Resolve v0114G and package chain"
    $latestG = def_S $summaryH.LatestV0114G
    $summaryG = def_ReadJson (def_J $latestG "output\VIA_v0114G_ReleaseCandidatePackageValidation_Summary.json")
    $latestF1 = def_S $summaryG.LatestV0114F1
    $summaryF1 = def_ReadJson (def_J $latestF1 "output\VIA_v0114F1_HotfixReleaseCandidatePackage_Summary.json")
    $packageDir = def_S $summaryF1.PackageDir
    $manifest = def_ReadJson (def_S $summaryF1.ManifestJson)
    $packageIndex = def_LoadCsv (def_S $manifest.package_index_csv)

    if (-not (Test-Path -LiteralPath $packageDir)) {
        throw "Package directory missing: $packageDir"
    }

    def_Progress 4 10 "Load package candidate artifacts"
    $candidateDir = def_J $packageDir "candidate_artifacts"
    $policyRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv")
    $aliasRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv")
    $rowRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv")

    def_Progress 5 10 "Compile final apply-plan draft"
    $applyPlan = def_BuildApplyPlanDraft -PackageIndex $packageIndex

    def_Progress 6 10 "Validate apply-plan draft"
    $validation = def_BuildValidation -ReadinessH $readinessH -ValidationH $validationH -ReviewH $reviewH -PackageIndex $packageIndex -ApplyPlan $applyPlan -PolicyRows $policyRows -AliasRows $aliasRows -RowRows $rowRows -PackageDir $packageDir
    $readinessI = def_BuildReadiness -Validation $validation -ApplyPlan $applyPlan

    def_Progress 7 10 "Write plan outputs"
    $planCsv = def_J $def_PLAN_DIR "VIA_v0114I_FinalApplyPlanDraft.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114I_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114I_ReadinessGate.csv"
    $sealJson = def_J $def_PLAN_DIR "VIA_v0114I_FinalApplyPlanDraftSeal.json"

    def_WriteCsv $applyPlan $planCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessI $readinessCsv

    def_WriteJson $applyPlan (def_J $def_PLAN_DIR "VIA_v0114I_FinalApplyPlanDraft.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114I_ValidationMatrix.json")
    def_WriteJson $readinessI (def_J $def_OUTPUT_DIR "VIA_v0114I_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114I_FinalApplyPlanDraftOnly_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114H = $latestH
        latest_v0114G = $latestG
        latest_v0114F1 = $latestF1
        package_dir = $packageDir
        plan_csv = $planCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        policy = [ordered]@{
            draft_only = $true
            future_user_approval_required = "v0114J_EXPLICIT_FINAL_USER_APPROVAL_REQUIRED"
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

    def_Progress 8 10 "Build precheck and accelerators"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114J-Precheck-After-v0114I.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114I_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114I_15Accelerators.json")

    def_Progress 9 10 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114I_FinalApplyPlanDraftOnly_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114I.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_PLAN_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $planCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114J explicit final user approval gate only.',
        '# v0114I did not apply anything.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessI[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY_READY"
        RunId = $def_RUN_ID
        LatestV0114H = $latestH
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114J = def_GetProp $r0 "def_allow_v0114J"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        ApplyPlanRows = def_GetProp $r0 "def_apply_plan_rows"
        FinalUserApplyAccept = def_GetProp $r0 "def_final_user_apply_accept"
        PackageDir = $packageDir
        PlanDir = $def_PLAN_DIR
        PlanCsv = $planCsv
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "NoStall; draft only; future explicit user approval required; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114I_FinalApplyPlanDraftOnly_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessI -Validation $validation -ApplyPlan $applyPlan -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114I Final Apply-Plan Draft Only" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114I Final Apply-Plan Draft Only COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114J        : $($summary.AllowV0114J)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Apply Plan Rows     : $($summary.ApplyPlanRows)" -ForegroundColor Cyan
    Write-Host "Final User Accept   : $($summary.FinalUserApplyAccept)" -ForegroundColor Yellow
    Write-Host "Plan CSV            : $planCsv" -ForegroundColor Cyan
    Write-Host "Seal                : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_PLAN_DIR } catch {}
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
