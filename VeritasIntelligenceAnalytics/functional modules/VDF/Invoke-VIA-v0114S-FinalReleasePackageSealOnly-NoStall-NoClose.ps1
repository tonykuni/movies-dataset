param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114R_ROOT = "",
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

$def_RUN_ID = "RUN_{0}_VIA_v0114S_FINAL_RELEASE_PACKAGE_SEAL_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114S_final_release_package_seal_only"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_PACKAGE_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_final_release_package_seal_only"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114S_FinalReleasePackageSealOnly.log"

$def_ACCELERATORS = @(
    "A01 latest-ready-v0114R auto discovery",
    "A02 NoStall no Read-Host",
    "A03 same-session NoClose execution",
    "A04 no child process required",
    "A05 no BASE re-scan",
    "A06 v0114R readiness reuse",
    "A07 release review rows carry-forward",
    "A08 v0114R hash ledger carry-forward",
    "A09 final package seal compiler",
    "A10 final package hash ledger",
    "A11 execution-disabled boundary gate",
    "A12 apply-disabled boundary gate",
    "A13 source-mutation boundary gate",
    "A14 canonical/db-write boundary gate",
    "A15 compact HTML package-seal report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_PACKAGE_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114S Final Release Package Seal Only" -Status $Status -PercentComplete $pct
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

function def_FileHash {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer) { return "" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function def_GetLatestV0114R {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114R_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114R_ROOT) { return $def_PARAM_V0114R_ROOT }
        throw "Specified v0114R root does not exist: $def_PARAM_V0114R_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114R_final_release_review_seal_only"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114R output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $p = def_J $_.FullName "output\VIA_v0114R_ReadinessGate.csv"
            if (-not (Test-Path -LiteralPath $p)) {
                $false
            } else {
                try {
                    $r = @(Import-Csv -LiteralPath $p)[0]
                    (
                        $r.def_allow_v0114S -eq "true" -and
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
        throw "No ready v0114R output found. Need Allow v0114S=true with execution/apply disabled."
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

function def_CountUnsafeRows {
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

function def_BuildPackageSealRows {
    param([array]$ReleaseReviewRows)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($r in $ReleaseReviewRows) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_release_package_seal_id = "FINAL_RELEASE_PACKAGE_SEAL_{0:0000}" -f $n
            def_source_release_review_id = def_GetProp $r "def_release_review_id"
            def_source_script_seal_id = def_GetProp $r "def_source_script_seal_id"
            def_plan_layer = def_GetProp $r "def_plan_layer"
            def_source_file = def_GetProp $r "def_source_file"
            def_release_review_result = def_GetProp $r "def_release_review_result"
            def_package_seal_action = "FINAL_RELEASE_PACKAGE_SEAL_ONLY"
            def_package_seal_result = "PACKAGE_SEALED_NO_APPLY"
            def_next_gate_required = "v0114T_FINAL_RELEASE_PACKAGE_VALIDATION_ONLY"
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

function def_BuildHashLedger {
    param($SummaryR,[string]$LatestR,[string]$PackageSealRowsCsv)

    $items = @(
        [pscustomobject]@{ def_item = "latest_v0114R_root"; def_path = $LatestR },
        [pscustomobject]@{ def_item = "v0114R_readiness_csv"; def_path = def_S $SummaryR.ReadinessCsv },
        [pscustomobject]@{ def_item = "v0114R_validation_csv"; def_path = def_S $SummaryR.ValidationCsv },
        [pscustomobject]@{ def_item = "v0114R_release_review_csv"; def_path = def_S $SummaryR.ReleaseReviewCsv },
        [pscustomobject]@{ def_item = "v0114R_hash_ledger_csv"; def_path = def_S $SummaryR.HashLedgerCsv },
        [pscustomobject]@{ def_item = "v0114R_final_release_review_seal_json"; def_path = def_S $SummaryR.FinalReleaseReviewSealJson },
        [pscustomobject]@{ def_item = "v0114S_release_package_seal_rows_csv"; def_path = $PackageSealRowsCsv }
    )

    $rows = New-Object System.Collections.ArrayList

    foreach ($i in $items) {
        $path = def_S $i.def_path
        $exists = $false
        $isDir = $false
        $hash = ""

        if (-not [string]::IsNullOrWhiteSpace($path) -and (Test-Path -LiteralPath $path)) {
            $exists = $true
            $item = Get-Item -LiteralPath $path
            $isDir = $item.PSIsContainer
            if (-not $isDir) { $hash = def_FileHash $path }
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_item = def_S $i.def_item
            def_path = $path
            def_exists = [string]$exists
            def_is_directory = [string]$isDir
            def_sha256 = $hash
        })
    }

    return @($rows)
}

function def_BuildDisabledBoundary {
    param([string]$Path)

    $lines = @(
        '$ErrorActionPreference = "Continue"',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114S Disabled Final Release Package Boundary" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "[BLOCKED] v0114S is final release package seal only." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow',
        'Write-Host "PowerShell remains open." -ForegroundColor Cyan',
        'return'
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_BuildValidation {
    param(
        [array]$ReadinessR,
        [array]$ValidationR,
        [array]$ReleaseReviewRows,
        [array]$PackageSealRows,
        [array]$HashLedger,
        [string]$DisabledBoundary
    )

    $rows = New-Object System.Collections.ArrayList
    $rr = $ReadinessR[0]

    $upstreamFail = @($ValidationR | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $unsafePackage = def_CountUnsafeRows -Rows $PackageSealRows
    $badAction = @($PackageSealRows | Where-Object { (def_GetProp $_ "def_package_seal_action") -ne "FINAL_RELEASE_PACKAGE_SEAL_ONLY" }).Count
    $missingNext = @($PackageSealRows | Where-Object { (def_GetProp $_ "def_next_gate_required") -ne "v0114T_FINAL_RELEASE_PACKAGE_VALIDATION_ONLY" }).Count
    $missingHashItems = @($HashLedger | Where-Object { (def_GetProp $_ "def_exists") -ne "True" }).Count
    $missingHash = @($HashLedger | Where-Object {
        (def_GetProp $_ "def_exists") -eq "True" -and
        (def_GetProp $_ "def_is_directory") -ne "True" -and
        [string]::IsNullOrWhiteSpace((def_GetProp $_ "def_sha256"))
    }).Count

    def_AddValidation $rows "UPSTREAM" "v0114R allow v0114S" ((def_GetProp $rr "def_allow_v0114S") -eq "true") ("Gate=" + (def_GetProp $rr "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114R validation fail zero" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"
    def_AddValidation $rows "UPSTREAM" "execution disabled upstream" ((def_GetProp $rr "def_execution_enabled") -eq "false") "execution_enabled=false"
    def_AddValidation $rows "UPSTREAM" "apply disabled upstream" ((def_GetProp $rr "def_apply_enabled") -eq "false") "apply_enabled=false"

    def_AddValidation $rows "COUNT" "release review rows 19" (@($ReleaseReviewRows).Count -eq 19) ("ReleaseReviewRows=" + @($ReleaseReviewRows).Count)
    def_AddValidation $rows "COUNT" "release package seal rows 19" (@($PackageSealRows).Count -eq 19) ("PackageSealRows=" + @($PackageSealRows).Count)

    def_AddValidation $rows "PACKAGE_SEAL" "package seal-only action" ($badAction -eq 0) "BadActionRows=$badAction"
    def_AddValidation $rows "PACKAGE_SEAL" "next package validation gate required" ($missingNext -eq 0) "MissingNextGate=$missingNext"

    def_AddValidation $rows "HASH" "hash ledger all declared items exist" ($missingHashItems -eq 0) "MissingHashItems=$missingHashItems"
    def_AddValidation $rows "HASH" "hash ledger non-directory hashes present" ($missingHash -eq 0) "MissingHash=$missingHash"

    def_AddValidation $rows "SAFETY" "no unsafe package seal rows" ($unsafePackage -eq 0) "UnsafePackageRows=$unsafePackage"
    def_AddValidation $rows "SAFETY" "source mutation false" ((def_GetProp $rr "def_source_mutation") -eq "false") "source_mutation=false"
    def_AddValidation $rows "SAFETY" "canonical merge false" ((def_GetProp $rr "def_canonical_merge") -eq "false") "canonical_merge=false"
    def_AddValidation $rows "SAFETY" "db write false" ((def_GetProp $rr "def_db_write") -eq "false") "db_write=false"

    $astBoundary = def_AstCheck -Path $DisabledBoundary
    def_AddValidation $rows "APPLY_BOUNDARY" "disabled boundary AST clean" $astBoundary.Ok $astBoundary.Message $DisabledBoundary

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[array]$PackageSealRows)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114T_FINAL_RELEASE_PACKAGE_VALIDATION_ONLY"
    $allow = "true"
    $reason = "Final release package seal passed. Next phase may validate final release package only. No apply executed."

    if ($fail -gt 0) {
        $gate = "BLOCKED_FINAL_RELEASE_PACKAGE_SEAL_FAILURE"
        $allow = "false"
        $reason = "Final release package seal has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114T = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_release_package_seal_rows = "$(@($PackageSealRows).Count)"
            def_execution_enabled = "false"
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114T final release package validation only"
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
        'Write-Host "def VIA · v0114T Precheck after v0114S" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114T)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Rows       : $($r.def_release_package_seal_rows)" -ForegroundColor Cyan',
        'Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114T -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114T." }',
        'if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114T_FINAL_RELEASE_PACKAGE_VALIDATION_ONLY" -ForegroundColor Green'
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
    param($Summary,$Readiness,$Validation,$PackageSealRows,$HashLedger,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114T",$Summary.AllowV0114T),
        @("Fail",$Summary.ValidationFail),
        @("Rows",$Summary.PackageSealRows),
        @("Execution","false"),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114S Final Release Package Seal Only</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114S · Final Release Package Seal Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Package seal only · no prompt · no execution · no apply · no mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114S 只建立 final release package seal 與 hash ledger。這不是正式 apply。下一步 v0114T 仍然只是 final release package validation only。</div><span class='tag'>Package Seal</span><span class='tag'>Hash Ledger</span><span class='tag'>Execution Disabled</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114T','def_reason','def_validation_fail','def_release_package_seal_rows','def_execution_enabled','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 160)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Final Release Package Seal Rows</h2>$(def_Table $PackageSealRows @('def_release_package_seal_id','def_source_release_review_id','def_plan_layer','def_source_file','def_release_review_result','def_package_seal_action','def_package_seal_result','def_next_gate_required','def_execution_enabled','def_apply_enabled','def_db_write') 220)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Hash Ledger</h2>$(def_Table $HashLedger @('def_item','def_path','def_exists','def_is_directory','def_sha256') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114R: $(def_Html $Summary.LatestV0114R)<br/>Package Dir: $(def_Html $Summary.PackageDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114S FINAL RELEASE PACKAGE SEAL ONLY · NOSTALL" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Package seal only. No prompt. No execution. No apply. No mutation. No DB write." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest ready v0114R output"
    $latestR = def_GetLatestV0114R
    $outR = def_J $latestR "output"
    $summaryR = def_ReadJson (def_J $outR "VIA_v0114R_FinalReleaseReviewSealOnly_Summary.json")
    def_Log "OK" "Latest ready v0114R: $latestR" Green

    def_Progress 2 10 "Load v0114R readiness and validation"
    $readinessR = def_LoadCsv (def_S $summaryR.ReadinessCsv)
    $validationR = def_LoadCsv (def_S $summaryR.ValidationCsv)

    def_Progress 3 10 "Load final release review rows"
    $releaseReviewRows = def_LoadCsv (def_S $summaryR.ReleaseReviewCsv)

    def_Progress 4 10 "Compile final release package seal rows"
    $packageSealRows = def_BuildPackageSealRows -ReleaseReviewRows $releaseReviewRows
    $packageSealRowsCsv = def_J $def_PACKAGE_DIR "VIA_v0114S_FinalReleasePackageSealRows.csv"
    def_WriteCsv $packageSealRows $packageSealRowsCsv
    def_WriteJson $packageSealRows (def_J $def_PACKAGE_DIR "VIA_v0114S_FinalReleasePackageSealRows.json")

    def_Progress 5 10 "Build package hash ledger"
    $hashLedger = def_BuildHashLedger -SummaryR $summaryR -LatestR $latestR -PackageSealRowsCsv $packageSealRowsCsv

    def_Progress 6 10 "Generate disabled package boundary"
    $disabledBoundary = def_J $def_PACKAGE_DIR "Invoke-VIA-v0114S-DISABLED-FinalReleasePackageBoundary.ps1"
    def_BuildDisabledBoundary -Path $disabledBoundary

    def_Progress 7 10 "Validate final release package seal"
    $validation = def_BuildValidation -ReadinessR $readinessR -ValidationR $validationR -ReleaseReviewRows $releaseReviewRows -PackageSealRows $packageSealRows -HashLedger $hashLedger -DisabledBoundary $disabledBoundary
    $readinessS = def_BuildReadiness -Validation $validation -PackageSealRows $packageSealRows

    $hashCsv = def_J $def_PACKAGE_DIR "VIA_v0114S_HashLedger.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114S_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114S_ReadinessGate.csv"
    $sealJson = def_J $def_PACKAGE_DIR "VIA_v0114S_FinalReleasePackageSeal.json"

    def_WriteCsv $hashLedger $hashCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessS $readinessCsv

    def_WriteJson $hashLedger (def_J $def_PACKAGE_DIR "VIA_v0114S_HashLedger.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114S_ValidationMatrix.json")
    def_WriteJson $readinessS (def_J $def_OUTPUT_DIR "VIA_v0114S_ReadinessGate.json")

    $finalSeal = [ordered]@{
        schema_version = "VIA_v0114S_FinalReleasePackageSealOnly_NoStall"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114R = $latestR
        package_seal_rows_csv = $packageSealRowsCsv
        hash_ledger_csv = $hashCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        disabled_boundary = $disabledBoundary
        policy = [ordered]@{
            final_release_package_seal_only = $true
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

    def_WriteJson $finalSeal $sealJson 18

    def_Progress 8 10 "Build precheck and accelerators"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114T-Precheck-After-v0114S.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114S_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114S_15Accelerators.json")

    def_Progress 9 10 "Build next commands"
    $report = def_J $def_REPORT_DIR "VIA_v0114S_FinalReleasePackageSealOnly_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114S.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_PACKAGE_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $packageSealRowsCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $hashCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114T final release package validation only.',
        '# v0114S did not execute apply.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessS[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114S_FINAL_RELEASE_PACKAGE_SEAL_ONLY_READY"
        RunId = $def_RUN_ID
        LatestV0114R = $latestR
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114T = def_GetProp $r0 "def_allow_v0114T"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        PackageSealRows = def_GetProp $r0 "def_release_package_seal_rows"
        ExecutionEnabled = def_GetProp $r0 "def_execution_enabled"
        PackageDir = $def_PACKAGE_DIR
        PackageSealRowsCsv = $packageSealRowsCsv
        HashLedgerCsv = $hashCsv
        FinalReleasePackageSealJson = $sealJson
        DisabledBoundary = $disabledBoundary
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "NoStall; final release package seal only; no execution; no apply; no mutation; no canonical merge; no DB write."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114S_FinalReleasePackageSealOnly_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessS -Validation $validation -PackageSealRows $packageSealRows -HashLedger $hashLedger -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114S Final Release Package Seal Only" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114S Final Release Package Seal Only COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status              : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate                : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114T        : $($summary.AllowV0114T)" -ForegroundColor Yellow
    Write-Host "Validation Fail     : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Package Rows        : $($summary.PackageSealRows)" -ForegroundColor Cyan
    Write-Host "Execution Enabled   : $($summary.ExecutionEnabled)" -ForegroundColor Yellow
    Write-Host "Package CSV         : $packageSealRowsCsv" -ForegroundColor Cyan
    Write-Host "Hash Ledger CSV     : $hashCsv" -ForegroundColor Cyan
    Write-Host "Final Seal JSON     : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck            : $precheck" -ForegroundColor Cyan
    Write-Host "Report              : $report" -ForegroundColor Cyan
    Write-Host "Output              : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd             : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_PACKAGE_DIR } catch {}
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
