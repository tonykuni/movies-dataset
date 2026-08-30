param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114L_ROOT = "",
    [string]$def_PARAM_FINAL_APPLY_AUTHORIZATION = "",
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

$def_AUTH_PHRASE = "YES_I_AUTHORIZE_v0114N_FINAL_APPLY_PACKAGE_REVIEW_ONLY_NO_APPLY_IN_v0114M"
$def_RUN_ID = "RUN_{0}_VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")

$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114M_final_apply_authorization_gate"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_AUTH_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_apply_authorization_gate"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114M_FinalApplyAuthorizationGate.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114L auto discovery",
    "A02 NoStall no Read-Host",
    "A03 exact final authorization phrase gate",
    "A04 same-session NoClose execution",
    "A05 no child process required",
    "A06 no BASE re-scan",
    "A07 v0114L readiness reuse",
    "A08 final dryrun seal carry-forward",
    "A09 dryrun row count validation",
    "A10 simulate-only validation",
    "A11 execution-disabled boundary gate",
    "A12 apply-disabled boundary gate",
    "A13 source-mutation boundary gate",
    "A14 canonical/db-write boundary gate",
    "A15 compact HTML authorization report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_AUTH_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114M Final Apply Authorization Gate" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114L {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114L_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114L_ROOT) { return $def_PARAM_V0114L_ROOT }
        throw "Specified v0114L root does not exist: $def_PARAM_V0114L_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114L_final_pre_apply_dryrun_only"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114L output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $p = def_J $_.FullName "output\VIA_v0114L_ReadinessGate.csv"
            if (-not (Test-Path -LiteralPath $p)) { return $false }
            try {
                $r = @(Import-Csv -LiteralPath $p)[0]
                return ($r.def_allow_v0114M -eq "true" -and $r.def_execution_enabled -eq "false" -and $r.def_apply_enabled -eq "false")
            } catch {
                return $false
            }
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No ready v0114L output found. Need Allow v0114M=true with execution/apply disabled."
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

function def_BuildAuthorizationBoard {
    param([string]$LatestL,[array]$ReadinessL,[array]$DryrunRows)

    $authorized = (($def_PARAM_FINAL_APPLY_AUTHORIZATION.Trim()) -eq $def_AUTH_PHRASE)

    return @(
        [pscustomobject][ordered]@{
            def_authorization_gate = "v0114M_FINAL_APPLY_AUTHORIZATION_GATE_ONLY"
            def_authorization_mode = "NOSTALL_EXACT_PARAMETER_ONLY"
            def_required_phrase = $def_AUTH_PHRASE
            def_final_apply_authorization = $(if ($authorized) { "YES" } else { "" })
            def_user_input_value = $(if ($authorized) { "MATCHED_AUTHORIZATION_PHRASE" } else { "NOT_PROVIDED_OR_NOT_MATCHED" })
            def_authorization_result = $(if ($authorized) { "AUTHORIZED_FOR_v0114N_REVIEW_ONLY" } else { "BLOCKED_FINAL_AUTHORIZATION_REQUIRED" })
            def_latest_v0114L = $LatestL
            def_dryrun_rows = "$(@($DryrunRows).Count)"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_phase = $(if ($authorized) { "v0114N final apply package review only" } else { "manual explicit authorization still required" })
        }
    )
}

function def_BuildValidation {
    param([array]$ReadinessL,[array]$ValidationL,[array]$DryrunRows,[array]$AuthorizationBoard)

    $rows = New-Object System.Collections.ArrayList
    $rl = $ReadinessL[0]
    $ab = $AuthorizationBoard[0]

    $upstreamFail = @($ValidationL | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $badDryrun = @($DryrunRows | Where-Object { (def_GetProp $_ "def_dryrun_action") -ne "SIMULATE_ONLY_NO_APPLY" }).Count
    $unsafeDryrun = @($DryrunRows | Where-Object {
        (def_GetProp $_ "def_execution_enabled") -ne "false" -or
        (def_GetProp $_ "def_apply_enabled") -ne "false" -or
        (def_GetProp $_ "def_source_mutation") -ne "false" -or
        (def_GetProp $_ "def_canonical_merge") -ne "false" -or
        (def_GetProp $_ "def_db_write") -ne "false"
    }).Count

    def_AddValidation $rows "UPSTREAM" "v0114L allow v0114M" ((def_GetProp $rl "def_allow_v0114M") -eq "true") ("Gate=" + (def_GetProp $rl "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114L validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "DRYRUN" "dryrun rows 19" (@($DryrunRows).Count -eq 19) ("DryrunRows=" + @($DryrunRows).Count)
    def_AddValidation $rows "DRYRUN" "dryrun simulate-only" ($badDryrun -eq 0) "BadDryrunRows=$badDryrun"
    def_AddValidation $rows "SAFETY" "no unsafe dryrun flags" ($unsafeDryrun -eq 0) "UnsafeDryrunRows=$unsafeDryrun"
    def_AddValidation $rows "NOSTALL" "no Read-Host in v0114M" $true "Authorization is parameter-only; no blocking prompt."

    $authorized = ((def_GetProp $ab "def_final_apply_authorization") -eq "YES")
    def_AddValidation $rows "FINAL_AUTHORIZATION" "exact final authorization phrase matched" $authorized ("AuthorizationResult=" + (def_GetProp $ab "def_authorization_result"))

    def_AddValidation $rows "SAFETY" "execution disabled in v0114M" ((def_GetProp $ab "def_execution_enabled") -eq "false") "execution_enabled=false"
    def_AddValidation $rows "SAFETY" "apply disabled in v0114M" ((def_GetProp $ab "def_apply_enabled") -eq "false") "apply_enabled=false"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $ab "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $ab "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $ab "def_db_write") -eq "false") "db_write=false"

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$AuthorizationBoard)

    $authorized = ((def_GetProp $AuthorizationBoard[0] "def_final_apply_authorization") -eq "YES")
    $hardFail = @($Validation | Where-Object {
        (def_GetProp $_ "def_status") -ne "PASS" -and
        (def_GetProp $_ "def_layer") -ne "FINAL_AUTHORIZATION"
    }).Count

    $authFail = @($Validation | Where-Object {
        (def_GetProp $_ "def_status") -ne "PASS" -and
        (def_GetProp $_ "def_layer") -eq "FINAL_AUTHORIZATION"
    }).Count

    if ($hardFail -eq 0 -and $authorized) {
        $gate = "READY_FOR_v0114N_FINAL_APPLY_PACKAGE_REVIEW_ONLY"
        $allow = "true"
        $reason = "Exact final authorization phrase matched. Next phase may generate final apply package review only. v0114M still did not apply."
    } elseif ($hardFail -eq 0 -and -not $authorized) {
        $gate = "BLOCKED_FINAL_APPLY_AUTHORIZATION_REQUIRED"
        $allow = "false"
        $reason = "All technical gates pass, but exact final authorization phrase is missing. This is expected default NoStall state."
    } else {
        $gate = "BLOCKED_FINAL_AUTHORIZATION_TECHNICAL_FAILURE"
        $allow = "false"
        $reason = "Technical validation failed."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114N = $allow
            def_reason = $reason
            def_validation_fail = "$($hardFail + $authFail)"
            def_technical_fail = "$hardFail"
            def_authorization_fail = "$authFail"
            def_final_apply_authorization = def_GetProp $AuthorizationBoard[0] "def_final_apply_authorization"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = $(if ($allow -eq "true") { "v0114N final apply package review only" } else { "rerun v0114M with exact authorization phrase if truly intended" })
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
        'Write-Host "def VIA · v0114N Precheck after v0114M" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114N)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Tech Fail  : $($r.def_technical_fail)" -ForegroundColor Yellow',
        'Write-Host "Auth       : $($r.def_final_apply_authorization)" -ForegroundColor Yellow',
        'Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114N -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114N. Final authorization may be missing." }',
        'if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114N_FINAL_APPLY_PACKAGE_REVIEW_ONLY" -ForegroundColor Green'
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
    param($Summary,$Readiness,$Validation,$AuthorizationBoard,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114N",$Summary.AllowV0114N),
        @("TechFail",$Summary.TechnicalFail),
        @("Auth",$Summary.FinalApplyAuthorization),
        @("Execution","false"),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114M Final Apply Authorization Gate</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114M · Final Apply Authorization Gate Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Authorization gate only · parameter-only · no prompt · no execution · no apply · no mutation · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114M 是最後授權 Gate。預設阻擋；只有 exact phrase 才允許進 v0114N review-only。v0114M 本身不 apply。</div><span class='tag'>Final Authorization Gate</span><span class='tag'>NoStall</span><span class='tag'>Exact Phrase</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114N','def_reason','def_validation_fail','def_technical_fail','def_authorization_fail','def_final_apply_authorization','def_execution_enabled','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Authorization Board</h2>$(def_Table $AuthorizationBoard @('def_authorization_gate','def_authorization_mode','def_required_phrase','def_final_apply_authorization','def_user_input_value','def_authorization_result','def_dryrun_rows','def_execution_enabled','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114L: $(def_Html $Summary.LatestV0114L)<br/>Authorization Dir: $(def_Html $Summary.AuthorizationDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114M FINAL APPLY AUTHORIZATION GATE · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Authorization gate only. No prompt. No execution. No apply. No mutation. No DB write." -ForegroundColor Yellow

    def_Progress 1 9 "Find latest ready v0114L output"
    $latestL = def_GetLatestV0114L
    $outL = def_J $latestL "output"
    $dryrunL = def_J $latestL "_final_pre_apply_dryrun_only"
    $summaryL = def_ReadJson (def_J $outL "VIA_v0114L_FinalPreApplyDryrunOnly_Summary.json")
    def_Log "OK" "Latest ready v0114L: $latestL" Green

    def_Progress 2 9 "Load v0114L readiness, validation, dryrun rows"
    $readinessL = def_LoadCsv (def_S $summaryL.ReadinessCsv)
    $validationL = def_LoadCsv (def_S $summaryL.ValidationCsv)
    $dryrunRows = def_LoadCsv (def_S $summaryL.DryrunCsv)

    def_Progress 3 9 "Build final authorization board"
    $authorizationBoard = def_BuildAuthorizationBoard -LatestL $latestL -ReadinessL $readinessL -DryrunRows $dryrunRows

    def_Progress 4 9 "Build validation matrix"
    $validation = def_BuildValidation -ReadinessL $readinessL -ValidationL $validationL -DryrunRows $dryrunRows -AuthorizationBoard $authorizationBoard

    def_Progress 5 9 "Build readiness gate"
    $readinessM = def_BuildReadiness -Validation $validation -AuthorizationBoard $authorizationBoard

    def_Progress 6 9 "Write authorization outputs"
    $authCsv = def_J $def_AUTH_DIR "VIA_v0114M_FinalApplyAuthorizationGate.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114M_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114M_ReadinessGate.csv"
    $sealJson = def_J $def_AUTH_DIR "VIA_v0114M_FinalApplyAuthorizationSeal.json"

    def_WriteCsv $authorizationBoard $authCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessM $readinessCsv

    def_WriteJson $authorizationBoard (def_J $def_AUTH_DIR "VIA_v0114M_FinalApplyAuthorizationGate.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114M_ValidationMatrix.json")
    def_WriteJson $readinessM (def_J $def_OUTPUT_DIR "VIA_v0114M_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114M_FinalApplyAuthorizationGate_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114L = $latestL
        authorization_csv = $authCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        exact_required_phrase = $def_AUTH_PHRASE
        policy = [ordered]@{
            authorization_gate_only = $true
            interactive_prompt = $false
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

    def_Progress 7 9 "Build precheck and accelerators"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114N-Precheck-After-v0114M.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114M_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114M_15Accelerators.json")

    def_Progress 8 9 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114M_FinalApplyAuthorizationGate_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114M.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_AUTH_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# If blocked only by final authorization, rerun v0114M with:',
        '# -def_PARAM_FINAL_APPLY_AUTHORIZATION "YES_I_AUTHORIZE_v0114N_FINAL_APPLY_PACKAGE_REVIEW_ONLY_NO_APPLY_IN_v0114M"',
        '# v0114M never applies anything.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessM[0]

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114M_FINAL_APPLY_AUTHORIZATION_GATE_READY"
        RunId = $def_RUN_ID
        LatestV0114L = $latestL
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114N = def_GetProp $r0 "def_allow_v0114N"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        TechnicalFail = def_GetProp $r0 "def_technical_fail"
        AuthorizationFail = def_GetProp $r0 "def_authorization_fail"
        FinalApplyAuthorization = def_GetProp $r0 "def_final_apply_authorization"
        AuthorizationDir = $def_AUTH_DIR
        AuthorizationCsv = $authCsv
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        RequiredPhrase = $def_AUTH_PHRASE
        Policy = "NoStall; exact parameter authorization only; no execution; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114M_FinalApplyAuthorizationGate_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessM -Validation $validation -AuthorizationBoard $authorizationBoard -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114M Final Apply Authorization Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114M Final Apply Authorization Gate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114N        : $($summary.AllowV0114N)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor Yellow
    Write-Host "Technical Fail      : $($summary.TechnicalFail)" -ForegroundColor Yellow
    Write-Host "Authorization Fail  : $($summary.AuthorizationFail)" -ForegroundColor Yellow
    Write-Host "Authorization       : $($summary.FinalApplyAuthorization)" -ForegroundColor Yellow
    Write-Host "Required Phrase     : $def_AUTH_PHRASE" -ForegroundColor Cyan
    Write-Host "Authorization CSV   : $authCsv" -ForegroundColor Cyan
    Write-Host "Seal                : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_AUTH_DIR } catch {}
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
