param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114A_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114B_CANDIDATE_VALIDATION_SEAL" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114B_candidate_validation_seal"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_SEAL_DIR = Join-Path $def_RUN_DIR "_validation_seal"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114B_CandidateValidationSeal.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114A auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 artifact existence gate",
    "A06 row/policy/alias count gate",
    "A07 unique candidate id gate",
    "A08 mutation flag scanner",
    "A09 canonical merge flag scanner",
    "A10 DB write flag scanner",
    "A11 disabled apply boundary AST gate",
    "A12 FRED raw secret forbidden scanner",
    "A13 MACRO_CHINA exclusion gate",
    "A14 alias path safety gate",
    "A15 compact HTML validation report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_SEAL_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114B Candidate Validation Seal" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0114A {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114A_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114A_ROOT) {
            return $def_PARAM_V0114A_ROOT
        }
        throw "Specified v0114A root does not exist: $def_PARAM_V0114A_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0114A_hotfix_sandbox_patch_candidate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0114A output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114A_HotfixSandboxPatchCandidate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0114A output found under: $root"
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

function def_CountUnsafeFlags {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_source_mutation") -ne "" -and (def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "" -and (def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "" -and (def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_existing_source_change") -eq "true")
    }).Count
}

function def_GetFileSha {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash } catch { return "" }
}

function def_AstCheckFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ Ok = $false; Message = "Missing file" }
    }

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null

    if ($errors -and @($errors).Count -gt 0) {
        return [pscustomobject]@{ Ok = $false; Message = ($errors[0].Message) }
    }

    return [pscustomobject]@{ Ok = $true; Message = "AST clean" }
}

function def_ScanDangerText {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ Ok = $false; Message = "Missing file" }
    }

    $t = Get-Content -LiteralPath $Path -Raw -Encoding UTF8

    $bad = @(
        "(?im)^\s*Remove-Item\b",
        "(?im)^\s*Stop-Process\b",
        "(?im)^\s*Restart-Computer\b",
        "(?im)^\s*shutdown\b",
        "(?im)^\s*exit\s+\d+",
        "(?im)^\s*Start-Process.+-WindowStyle\s+Hidden"
    )

    foreach ($p in $bad) {
        if ($t -match $p) {
            return [pscustomobject]@{ Ok = $false; Message = "Forbidden token matched: $p" }
        }
    }

    return [pscustomobject]@{ Ok = $true; Message = "No forbidden token" }
}

function def_ScanNoRawFred {
    param([string[]]$Paths)

    foreach ($p in $Paths) {
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $t = Get-Content -LiteralPath $p -Raw -Encoding UTF8

        if ($t -match "(?i)FRED_API_KEY\s*=\s*[A-Za-z0-9_\-]{16,}") {
            return [pscustomobject]@{ Ok = $false; Message = "Possible raw FRED assignment in $p" }
        }

        if ($t -match "(?i)api_key\s*[:=]\s*[A-Za-z0-9_\-]{24,}") {
            return [pscustomobject]@{ Ok = $false; Message = "Possible raw api_key in $p" }
        }
    }

    return [pscustomobject]@{ Ok = $true; Message = "No raw FRED key pattern detected" }
}

function def_BuildIntegrityManifest {
    param([string[]]$Paths)

    $rows = New-Object System.Collections.ArrayList

    foreach ($p in $Paths) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_path = $p
            def_exists = [string](Test-Path -LiteralPath $p)
            def_sha256 = def_GetFileSha $p
            def_length = $(if (Test-Path -LiteralPath $p) { [string]((Get-Item -LiteralPath $p).Length) } else { "0" })
            def_last_write_time = $(if (Test-Path -LiteralPath $p) { (Get-Item -LiteralPath $p).LastWriteTime.ToString("s") } else { "" })
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114C_SANDBOX_DRYRUN_SIMULATION"
    $allow = "true"
    $reason = "Sandbox candidate validation sealed. Next phase may run sandbox dry-run simulation only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_CANDIDATE_VALIDATION_FAILURE"
        $allow = "false"
        $reason = "Validation matrix has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114C = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114C sandbox dry-run simulation only"
        }
    )
}

function def_BuildPrecheck {
    param([string]$ReadinessCsv,[string]$Path)

    $safeCsv = def_EscapePsDouble $ReadinessCsv

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '$ReadinessCsv = "' + $safeCsv + '"',
        'if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }',
        '$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114C Precheck after v0114B" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114C)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114C -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114C." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114C_SANDBOX_DRYRUN_SIMULATION_ONLY" -ForegroundColor Green'
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
            if ($v.Length -gt 300) { $v = $v.Substring(0,300) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param($Summary,$Readiness,$Validation,$Integrity,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114C",$Summary.AllowV0114C),
        @("Fail",$Summary.ValidationFail),
        @("Rows",$Summary.RowRows),
        @("Policy",$Summary.PolicyRows),
        @("Alias",$Summary.AliasRows),
        @("Unsafe",$Summary.UnsafeFlags)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114B Candidate Validation Seal</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114B · Sandbox Candidate Validation Seal</h1>")
    [void]$html.AppendLine("<div class='sub'>Validation only · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114B 只驗證 v0114A 產生的 sandbox candidate。通過後下一步只能做 v0114C sandbox dry-run simulation，仍不可正式套用。</div><span class='tag'>Validation Seal</span><span class='tag'>No Source Mutation</span><span class='tag'>No Canonical Merge</span><span class='tag'>No DB Write</span><span class='tag'>NoClose</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114C','def_reason','def_validation_fail','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Integrity Manifest</h2>$(def_Table $Integrity @('def_exists','def_length','def_sha256','def_last_write_time','def_path') 60)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114A: $(def_Html $Summary.LatestV0114A)<br/>Seal Dir: $(def_Html $Summary.SealDir)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114B SANDBOX CANDIDATE VALIDATION SEAL · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Validation only. No source mutation. No canonical merge. No DB write. No close." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0114A output"
    $latest = def_GetLatestV0114A
    $outA = Join-Path $latest "output"
    $candA = Join-Path $latest "_sandbox_patch_candidate"
    $diffA = Join-Path $latest "_diff_preview"
    $applyA = Join-Path $latest "_disabled_apply_script"
    def_Log "OK" "Latest v0114A: $latest" Green

    def_Progress 2 10 "Resolve artifact paths"
    $policyCsv = Join-Path $candA "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv"
    $aliasCsv = Join-Path $candA "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv"
    $rowCsv = Join-Path $candA "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv"
    $manifestJson = Join-Path $candA "VIA_v0114A_SandboxPatchCandidate_Manifest.json"
    $diffCsv = Join-Path $diffA "VIA_v0114A_DIFF_PREVIEW.csv"
    $readinessCsvA = Join-Path $outA "VIA_v0114A_ReadinessGate.csv"
    $validationCsvA = Join-Path $outA "VIA_v0114A_ValidationMatrix.csv"
    $disabledApply = Join-Path $applyA "Invoke-VIA-v0114A-DISABLED-ApplyBoundary.ps1"

    $artifactPaths = @($policyCsv,$aliasCsv,$rowCsv,$manifestJson,$diffCsv,$readinessCsvA,$validationCsvA,$disabledApply)

    def_Progress 3 10 "Load candidate artifacts"
    $policyRows = def_LoadCsv $policyCsv
    $aliasRows = def_LoadCsv $aliasCsv
    $rowRows = def_LoadCsv $rowCsv
    $diffRows = def_LoadCsv $diffCsv
    $readinessA = def_LoadCsv $readinessCsvA
    $validationA = def_LoadCsv $validationCsvA
    def_Log "OK" "Loaded Policy=$(@($policyRows).Count), Alias=$(@($aliasRows).Count), Rows=$(@($rowRows).Count), Diff=$(@($diffRows).Count)" Green

    def_Progress 4 10 "Build integrity manifest"
    $integrity = def_BuildIntegrityManifest -Paths $artifactPaths

    def_Progress 5 10 "Run validation gates"
    $val = New-Object System.Collections.ArrayList

    foreach ($p in $artifactPaths) {
        def_AddValidation $val "ARTIFACT" "exists: $(Split-Path $p -Leaf)" (Test-Path -LiteralPath $p) "Artifact path check." $p
    }

    def_AddValidation $val "COUNT" "row patch plan count" (@($rowRows).Count -eq 149) "Rows=$(@($rowRows).Count)" $rowCsv
    def_AddValidation $val "COUNT" "policy candidate count" (@($policyRows).Count -eq 12) "Policy=$(@($policyRows).Count)" $policyCsv
    def_AddValidation $val "COUNT" "alias candidate count" (@($aliasRows).Count -eq 5) "Alias=$(@($aliasRows).Count)" $aliasCsv
    def_AddValidation $val "COUNT" "diff preview count" (@($diffRows).Count -ge 4) "Diff=$(@($diffRows).Count)" $diffCsv

    $idDupRows = @($rowRows | Group-Object def_candidate_id | Where-Object { $_.Count -gt 1 }).Count
    $idDupPolicy = @($policyRows | Group-Object def_candidate_id | Where-Object { $_.Count -gt 1 }).Count
    $idDupAlias = @($aliasRows | Group-Object def_candidate_id | Where-Object { $_.Count -gt 1 }).Count
    def_AddValidation $val "ID" "unique row candidate ids" ($idDupRows -eq 0) "Duplicate groups=$idDupRows" $rowCsv
    def_AddValidation $val "ID" "unique policy candidate ids" ($idDupPolicy -eq 0) "Duplicate groups=$idDupPolicy" $policyCsv
    def_AddValidation $val "ID" "unique alias candidate ids" ($idDupAlias -eq 0) "Duplicate groups=$idDupAlias" $aliasCsv

    def_Progress 6 10 "Run safety scanners"
    $allCandidateRows = @()
    $allCandidateRows += $policyRows
    $allCandidateRows += $aliasRows
    $allCandidateRows += $rowRows
    $allCandidateRows += $diffRows

    $unsafe = def_CountUnsafeFlags -Rows $allCandidateRows
    def_AddValidation $val "SAFETY" "no unsafe mutation flags" ($unsafe -eq 0) "UnsafeFlags=$unsafe"

    $macroRows = @($rowRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "MACRO_CHINA" }).Count
    def_AddValidation $val "SAFETY" "MACRO_CHINA excluded" ($macroRows -eq 0) "MACRO_CHINA row patch count=$macroRows" $rowCsv

    $badAliasPath = @($aliasRows | Where-Object {
        (def_GetProp $_ "def_alias_value") -match "\\dict\\VDF\\_active\\" -or
        (def_GetProp $_ "def_alias_value") -match "\\launchers\\" -or
        (def_GetProp $_ "def_alias_value") -match "RUN_\d{8}_\d{6}"
    }).Count
    def_AddValidation $val "SAFETY" "alias path safety" ($badAliasPath -eq 0) "Bad alias paths=$badAliasPath" $aliasCsv

    $fredScan = def_ScanNoRawFred -Paths @($policyCsv,$aliasCsv,$rowCsv,$diffCsv,$manifestJson)
    def_AddValidation $val "SECRET" "no raw FRED key pattern" $fredScan.Ok $fredScan.Message

    $disabledAst = def_AstCheckFile -Path $disabledApply
    def_AddValidation $val "APPLY_BOUNDARY" "disabled apply AST clean" $disabledAst.Ok $disabledAst.Message $disabledApply

    $danger = def_ScanDangerText -Path $disabledApply
    def_AddValidation $val "APPLY_BOUNDARY" "disabled apply no dangerous token" $danger.Ok $danger.Message $disabledApply

    def_AddValidation $val "APPLY_BOUNDARY" "disabled apply exists" (Test-Path -LiteralPath $disabledApply) "Apply boundary is disabled and present." $disabledApply

    $readinessA0 = $readinessA[0]
    def_AddValidation $val "UPSTREAM" "v0114A allow v0114B" ((def_GetProp $readinessA0 "def_allow_v0114B") -eq "true") ("Gate=" + (def_GetProp $readinessA0 "def_gate_status")) $readinessCsvA

    $upstreamFail = @($validationA | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    def_AddValidation $val "UPSTREAM" "v0114A validation pass" ($upstreamFail -eq 0) "Upstream fail=$upstreamFail" $validationCsvA

    def_Progress 7 10 "Build readiness seal"
    $readinessB = def_BuildReadiness -Validation $val

    def_Progress 8 10 "Write validation outputs"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114B_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114B_ReadinessGate.csv"
    $integrityCsv = Join-Path $def_SEAL_DIR "VIA_v0114B_IntegrityManifest.csv"
    $sealJson = Join-Path $def_SEAL_DIR "VIA_v0114B_ValidationSeal.json"

    def_WriteCsv $val $validationCsv
    def_WriteCsv $readinessB $readinessCsv
    def_WriteCsv $integrity $integrityCsv

    def_WriteJson $val (Join-Path $def_OUTPUT_DIR "VIA_v0114B_ValidationMatrix.json")
    def_WriteJson $readinessB (Join-Path $def_OUTPUT_DIR "VIA_v0114B_ReadinessGate.json")
    def_WriteJson $integrity (Join-Path $def_SEAL_DIR "VIA_v0114B_IntegrityManifest.json")

    $seal = [ordered]@{
        schema_version = "VIA_v0114B_CandidateValidationSeal"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114A = $latest
        validation_csv = $validationCsv
        readiness_csv = $readinessCsv
        integrity_csv = $integrityCsv
        validation_fail = (def_GetProp $readinessB[0] "def_validation_fail")
        allow_v0114C = (def_GetProp $readinessB[0] "def_allow_v0114C")
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

    def_Progress 9 10 "Build precheck, accelerators, next commands"
    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114C-Precheck-After-v0114B.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114B_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114B_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114B_CandidateValidationSeal_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114B.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_SEAL_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114C sandbox dry-run simulation only.',
        '# No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessB[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114B_CANDIDATE_VALIDATION_SEAL_READY"
        RunId = $def_RUN_ID
        LatestV0114A = $latest
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114C = def_GetProp $r0 "def_allow_v0114C"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        RowRows = "$(@($rowRows).Count)"
        PolicyRows = "$(@($policyRows).Count)"
        AliasRows = "$(@($aliasRows).Count)"
        UnsafeFlags = "$unsafe"
        ValidationCsv = $validationCsv
        ReadinessCsv = $readinessCsv
        IntegrityCsv = $integrityCsv
        SealJson = $sealJson
        SealDir = $def_SEAL_DIR
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; validation only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114B_CandidateValidationSeal_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessB -Validation $val -Integrity $integrity -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114B Candidate Validation Seal" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114B Candidate Validation Seal COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114C    : $($summary.AllowV0114C)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Rows            : $($summary.RowRows)" -ForegroundColor Cyan
    Write-Host "Policy          : $($summary.PolicyRows)" -ForegroundColor Cyan
    Write-Host "Alias           : $($summary.AliasRows)" -ForegroundColor Cyan
    Write-Host "Unsafe Flags    : $($summary.UnsafeFlags)" -ForegroundColor $(if ($summary.UnsafeFlags -eq "0") { "Green" } else { "Red" })
    Write-Host "Seal Dir        : $def_SEAL_DIR" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_SEAL_DIR } catch {}
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
