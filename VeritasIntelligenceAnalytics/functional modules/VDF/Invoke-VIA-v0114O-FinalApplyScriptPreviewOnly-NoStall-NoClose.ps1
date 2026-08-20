param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114N_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114O_FINAL_APPLY_SCRIPT_PREVIEW_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114O_final_apply_script_preview_only"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_PREVIEW_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_apply_script_preview_only"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114O_FinalApplyScriptPreviewOnly.log"

$def_ACCELERATORS = @(
    "A01 latest-ready-v0114N auto discovery",
    "A02 NoStall no Read-Host",
    "A03 same-session NoClose execution",
    "A04 no child process required",
    "A05 no BASE re-scan",
    "A06 v0114N readiness reuse",
    "A07 final package review carry-forward",
    "A08 preview-row compiler",
    "A09 disabled script preview generation",
    "A10 preview script AST validation",
    "A11 dangerous-command scanner",
    "A12 execution-disabled boundary gate",
    "A13 apply-disabled boundary gate",
    "A14 canonical/db-write boundary gate",
    "A15 compact HTML script preview report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_PREVIEW_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114O Final Apply Script Preview Only" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114N {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114N_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114N_ROOT) { return $def_PARAM_V0114N_ROOT }
        throw "Specified v0114N root does not exist: $def_PARAM_V0114N_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114N_final_apply_package_review_only"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114N output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $p = def_J $_.FullName "output\VIA_v0114N_ReadinessGate.csv"
            if (-not (Test-Path -LiteralPath $p)) {
                $false
            } else {
                try {
                    $r = @(Import-Csv -LiteralPath $p)[0]
                    (
                        $r.def_allow_v0114O -eq "true" -and
                        $r.def_execution_enabled -eq "false" -and
                        $r.def_apply_enabled -eq "false" -and
                        $r.def_db_write -eq "false"
                    )
                } catch {
                    $false
                }
            }
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No ready v0114N output found. Need Allow v0114O=true with execution/apply disabled."
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

function def_BuildScriptPreviewRows {
    param([array]$PackageReview)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($p in $PackageReview) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_script_preview_id = "FINAL_SCRIPT_PREVIEW_{0:0000}" -f $n
            def_source_package_review_id = def_GetProp $p "def_package_review_id"
            def_plan_layer = def_GetProp $p "def_plan_layer"
            def_source_file = def_GetProp $p "def_source_file"
            def_source_path = def_GetProp $p "def_source_path"
            def_source_exists = def_GetProp $p "def_source_exists"
            def_preview_type = "INERT_REVIEW_ONLY"
            def_preview_statement = "NO_EXECUTION_NO_APPLY"
            def_next_gate_required = "v0114P_FINAL_SCRIPT_PREVIEW_VALIDATION_ONLY"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_delete = "false"
            def_stop_process = "false"
        })
    }

    return @($rows)
}

function def_BuildDisabledScriptPreview {
    param([string]$Path,[string]$PreviewCsv)

    $safeCsv = def_EscapePsDouble $PreviewCsv

    $lines = @(
        '$ErrorActionPreference = "Continue"',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114O Final Apply Script Preview Only" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "[PREVIEW ONLY] This file is intentionally inert." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow',
        'Write-Host "Preview CSV:" -ForegroundColor Cyan',
        'Write-Host "' + $safeCsv + '" -ForegroundColor Cyan',
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

function def_ScanPreviewScript {
    param([string]$Path)

    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $danger = "(?i)\b(Remove-Item|Stop-Process|Copy-Item|Move-Item|Invoke-Expression|iex|Start-Job|Start-ThreadJob|Start-Process\s+pwsh|Start-Process\s+powershell)\b"

    if ($text -match $danger) {
        return [pscustomobject]@{ Ok = $false; Message = "Dangerous command pattern detected in preview script." }
    }

    return [pscustomobject]@{ Ok = $true; Message = "No dangerous command pattern detected." }
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

function def_BuildValidation {
    param(
        [array]$ReadinessN,
        [array]$ValidationN,
        [array]$PackageReview,
        [array]$ScriptPreview,
        [string]$PreviewScript
    )

    $rows = New-Object System.Collections.ArrayList
    $rn = $ReadinessN[0]

    $upstreamFail = @($ValidationN | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $unsafe = def_CountUnsafe -Rows $ScriptPreview
    $badPreview = @($ScriptPreview | Where-Object { (def_GetProp $_ "def_preview_statement") -ne "NO_EXECUTION_NO_APPLY" }).Count
    $missingNext = @($ScriptPreview | Where-Object { (def_GetProp $_ "def_next_gate_required") -ne "v0114P_FINAL_SCRIPT_PREVIEW_VALIDATION_ONLY" }).Count
    $missingSource = @($ScriptPreview | Where-Object { (def_GetProp $_ "def_source_exists") -eq "False" }).Count

    def_AddValidation $rows "UPSTREAM" "v0114N allow v0114O" ((def_GetProp $rn "def_allow_v0114O") -eq "true") ("Gate=" + (def_GetProp $rn "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114N validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "UPSTREAM" "execution disabled upstream" ((def_GetProp $rn "def_execution_enabled") -eq "false") "execution_enabled=false"
    def_AddValidation $rows "UPSTREAM" "apply disabled upstream" ((def_GetProp $rn "def_apply_enabled") -eq "false") "apply_enabled=false"

    def_AddValidation $rows "COUNT" "package review rows 19" (@($PackageReview).Count -eq 19) ("PackageReviewRows=" + @($PackageReview).Count)
    def_AddValidation $rows "COUNT" "script preview rows 19" (@($ScriptPreview).Count -eq 19) ("ScriptPreviewRows=" + @($ScriptPreview).Count)

    def_AddValidation $rows "SCRIPT_PREVIEW" "preview only statements" ($badPreview -eq 0) "BadPreviewRows=$badPreview"
    def_AddValidation $rows "SCRIPT_PREVIEW" "next preview validation gate required" ($missingNext -eq 0) "MissingNextGate=$missingNext"
    def_AddValidation $rows "SCRIPT_PREVIEW" "declared source paths exist" ($missingSource -eq 0) "MissingSourceRows=$missingSource"

    def_AddValidation $rows "SAFETY" "no unsafe flags in script preview rows" ($unsafe -eq 0) "UnsafeFlags=$unsafe"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $rn "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $rn "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $rn "def_db_write") -eq "false") "db_write=false"

    $ast = def_AstCheck -Path $PreviewScript
    def_AddValidation $rows "SCRIPT_PREVIEW" "preview script AST clean" $ast.Ok $ast.Message $PreviewScript

    $scan = def_ScanPreviewScript -Path $PreviewScript
    def_AddValidation $rows "SCRIPT_PREVIEW" "preview script no dangerous command" $scan.Ok $scan.Message $PreviewScript

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$ScriptPreview)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114P_FINAL_SCRIPT_PREVIEW_VALIDATION_ONLY"
    $allow = "true"
    $reason = "Final apply script preview generated and validated. Next phase may validate script preview only. No apply executed."

    if ($fail -gt 0) {
        $gate = "BLOCKED_FINAL_APPLY_SCRIPT_PREVIEW_FAILURE"
        $allow = "false"
        $reason = "Final apply script preview has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114P = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_script_preview_rows = "$(@($ScriptPreview).Count)"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114P final script preview validation only"
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
        'Write-Host "def VIA · v0114P Precheck after v0114O" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114P)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Rows       : $($r.def_script_preview_rows)" -ForegroundColor Cyan',
        'Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114P -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114P." }',
        'if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114P_FINAL_SCRIPT_PREVIEW_VALIDATION_ONLY" -ForegroundColor Green'
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
    param($Summary,$Readiness,$Validation,$ScriptPreview,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114P",$Summary.AllowV0114P),
        @("Fail",$Summary.ValidationFail),
        @("Rows",$Summary.ScriptPreviewRows),
        @("Execution","false"),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114O Final Apply Script Preview Only</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114O · Final Apply Script Preview Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Script preview only · no prompt · no execution · no apply · no mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114O 只產生 final apply script preview。預覽腳本為 inert/disabled，不會執行 apply。下一步 v0114P 仍是 script preview validation only。</div><span class='tag'>Script Preview</span><span class='tag'>NoStall</span><span class='tag'>Execution Disabled</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114P','def_reason','def_validation_fail','def_script_preview_rows','def_execution_enabled','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 140)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Final Script Preview Rows</h2>$(def_Table $ScriptPreview @('def_script_preview_id','def_source_package_review_id','def_plan_layer','def_source_file','def_source_exists','def_preview_type','def_preview_statement','def_next_gate_required','def_execution_enabled','def_apply_enabled','def_db_write') 220)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114N: $(def_Html $Summary.LatestV0114N)<br/>Preview Dir: $(def_Html $Summary.PreviewDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114O FINAL APPLY SCRIPT PREVIEW ONLY · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Script preview only. No prompt. No execution. No apply. No mutation. No DB write." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest ready v0114N output"
    $latestN = def_GetLatestV0114N
    $outN = def_J $latestN "output"
    $summaryN = def_ReadJson (def_J $outN "VIA_v0114N_FinalApplyPackageReviewOnly_Summary.json")
    def_Log "OK" "Latest ready v0114N: $latestN" Green

    def_Progress 2 10 "Load v0114N readiness and validation"
    $readinessN = def_LoadCsv (def_S $summaryN.ReadinessCsv)
    $validationN = def_LoadCsv (def_S $summaryN.ValidationCsv)

    def_Progress 3 10 "Load package review rows"
    $packageReview = def_LoadCsv (def_S $summaryN.PackageReviewCsv)

    def_Progress 4 10 "Compile script preview rows"
    $scriptPreview = def_BuildScriptPreviewRows -PackageReview $packageReview

    def_Progress 5 10 "Write script preview CSV before disabled script"
    $previewRowsCsv = def_J $def_PREVIEW_DIR "VIA_v0114O_FinalApplyScriptPreviewRows.csv"
    def_WriteCsv $scriptPreview $previewRowsCsv
    def_WriteJson $scriptPreview (def_J $def_PREVIEW_DIR "VIA_v0114O_FinalApplyScriptPreviewRows.json")

    def_Progress 6 10 "Generate inert disabled script preview"
    $previewScript = def_J $def_PREVIEW_DIR "Invoke-VIA-v0114O-FINAL-APPLY-SCRIPT-PREVIEW-ONLY-DISABLED.ps1"
    def_BuildDisabledScriptPreview -Path $previewScript -PreviewCsv $previewRowsCsv

    def_Progress 7 10 "Validate script preview"
    $validation = def_BuildValidation -ReadinessN $readinessN -ValidationN $validationN -PackageReview $packageReview -ScriptPreview $scriptPreview -PreviewScript $previewScript
    $readinessO = def_BuildReadiness -Validation $validation -ScriptPreview $scriptPreview

    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114O_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114O_ReadinessGate.csv"
    $sealJson = def_J $def_PREVIEW_DIR "VIA_v0114O_FinalApplyScriptPreviewSeal.json"

    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessO $readinessCsv
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114O_ValidationMatrix.json")
    def_WriteJson $readinessO (def_J $def_OUTPUT_DIR "VIA_v0114O_ReadinessGate.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114O_FinalApplyScriptPreviewOnly_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114N = $latestN
        preview_rows_csv = $previewRowsCsv
        preview_script = $previewScript
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        policy = [ordered]@{
            script_preview_only = $true
            preview_script_inert = $true
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
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114P-Precheck-After-v0114O.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114O_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114O_15Accelerators.json")

    def_Progress 9 10 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114O_FinalApplyScriptPreviewOnly_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114O.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_PREVIEW_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $previewRowsCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114P final script preview validation only.',
        '# v0114O did not execute apply.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessO[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114O_FINAL_APPLY_SCRIPT_PREVIEW_ONLY_READY"
        RunId = $def_RUN_ID
        LatestV0114N = $latestN
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114P = def_GetProp $r0 "def_allow_v0114P"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        ScriptPreviewRows = def_GetProp $r0 "def_script_preview_rows"
        ExecutionEnabled = def_GetProp $r0 "def_execution_enabled"
        PreviewDir = $def_PREVIEW_DIR
        PreviewRowsCsv = $previewRowsCsv
        PreviewScript = $previewScript
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "NoStall; final apply script preview only; inert preview script; no execution; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114O_FinalApplyScriptPreviewOnly_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessO -Validation $validation -ScriptPreview $scriptPreview -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114O Final Apply Script Preview Only" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114O Final Apply Script Preview Only COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114P        : $($summary.AllowV0114P)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Script Preview Rows : $($summary.ScriptPreviewRows)" -ForegroundColor Cyan
    Write-Host "Execution Enabled   : $($summary.ExecutionEnabled)" -ForegroundColor Yellow
    Write-Host "Preview CSV         : $previewRowsCsv" -ForegroundColor Cyan
    Write-Host "Preview Script      : $previewScript" -ForegroundColor Cyan
    Write-Host "Seal                : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_PREVIEW_DIR } catch {}
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
