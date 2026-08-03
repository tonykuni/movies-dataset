param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114F1_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0114G_PACKAGE_VALIDATION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path -Path $def_PARAM_VIA_ROOT -ChildPath "functional modules\VDF"
$def_RUN_ROOT = Join-Path -Path $def_VDF -ChildPath "_integration_v0114G_package_validation"
$def_RUN_DIR = Join-Path -Path $def_RUN_ROOT -ChildPath $def_RUN_ID
$def_OUTPUT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "output"
$def_REPORT_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "report"
$def_VALIDATION_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "_package_validation_seal"
$def_LOG_DIR = Join-Path -Path $def_RUN_DIR -ChildPath "logs"
$def_LOG = Join-Path -Path $def_LOG_DIR -ChildPath "VIA_v0114G_PackageValidation.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114F1 auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 upstream readiness reuse",
    "A06 package index hash validation",
    "A07 ZIP integrity validation",
    "A08 ZIP entry inventory",
    "A09 candidate count validation",
    "A10 disabled apply AST validation",
    "A11 forbidden command scanner",
    "A12 raw secret scanner",
    "A13 MACRO_CHINA exclusion scanner",
    "A14 no mutation/canonical/db boundary seal",
    "A15 compact HTML validation report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_VALIDATION_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114G Package Validation" -Status $Status -PercentComplete $pct
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

function def_GetFileSha {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash } catch { return "" }
}

function def_GetLatestV0114F1 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114F1_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114F1_ROOT) { return $def_PARAM_V0114F1_ROOT }
        throw "Specified v0114F1 root does not exist: $def_PARAM_V0114F1_ROOT"
    }

    $root = def_J $def_VDF "_integration_v0114F1_hotfix_release_candidate_package"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114F1 output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (def_J $_.FullName "output\VIA_v0114F1_HotfixReleaseCandidatePackage_Summary.json") } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) { throw "No v0114F1 output found under: $root" }
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

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ Ok = $false; Message = "Missing file" }
    }

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null

    if ($errors -and @($errors).Count -gt 0) {
        return [pscustomobject]@{ Ok = $false; Message = $errors[0].Message }
    }

    return [pscustomobject]@{ Ok = $true; Message = "AST clean" }
}

function def_ScanDanger {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ Ok = $false; Message = "Missing file" }
    }

    $t = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $patterns = @(
        "(?im)^\s*Remove-Item\b",
        "(?im)^\s*Stop-Process\b",
        "(?im)^\s*Restart-Computer\b",
        "(?im)^\s*shutdown\b",
        "(?im)^\s*exit\s+\d+",
        "(?im)^\s*Set-Content\b.*canonical",
        "(?im)^\s*Copy-Item\b.*canonical",
        "(?im)^\s*Move-Item\b"
    )

    foreach ($p in $patterns) {
        if ($t -match $p) {
            return [pscustomobject]@{ Ok = $false; Message = "Forbidden command pattern: $p" }
        }
    }

    return [pscustomobject]@{ Ok = $true; Message = "No dangerous command pattern detected" }
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

function def_BuildZipInventory {
    param([string]$ZipPath)

    $rows = New-Object System.Collections.ArrayList

    if (-not (Test-Path -LiteralPath $ZipPath)) {
        return @($rows)
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue

    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        foreach ($e in $zip.Entries) {
            if ([string]::IsNullOrWhiteSpace($e.Name)) { continue }
            [void]$rows.Add([pscustomobject][ordered]@{
                def_zip_entry = $e.FullName
                def_name = $e.Name
                def_length = [string]$e.Length
                def_compressed_length = [string]$e.CompressedLength
                def_last_write_time = $e.LastWriteTime.ToString("s")
            })
        }
    } finally {
        $zip.Dispose()
    }

    return @($rows)
}

function def_ValidatePackageIndexHashes {
    param([array]$PackageIndex)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $PackageIndex) {
        $dest = def_GetProp $r "def_dest"
        $expected = def_GetProp $r "def_sha256"
        $exists = Test-Path -LiteralPath $dest
        $actual = ""
        if ($exists) { $actual = def_GetFileSha $dest }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_file = def_GetProp $r "def_file"
            def_exists = [string]$exists
            def_expected_sha256 = $expected
            def_actual_sha256 = $actual
            def_hash_match = [string]($exists -and ($expected -eq $actual) -and -not [string]::IsNullOrWhiteSpace($actual))
            def_dest = $dest
        })
    }

    return @($rows)
}

function def_CountUnsafe {
    param([array]$Rows)

    return @($Rows | Where-Object {
        ((def_GetProp $_ "def_source_mutation") -ne "" -and (def_GetProp $_ "def_source_mutation") -ne "false") -or
        ((def_GetProp $_ "def_canonical_merge") -ne "" -and (def_GetProp $_ "def_canonical_merge") -ne "false") -or
        ((def_GetProp $_ "def_db_write") -ne "" -and (def_GetProp $_ "def_db_write") -ne "false") -or
        ((def_GetProp $_ "def_apply_enabled") -eq "true") -or
        ((def_GetProp $_ "def_existing_source_change") -eq "true")
    }).Count
}

function def_BuildValidation {
    param(
        [array]$ReadinessF,
        [array]$ValidationF,
        [array]$PackageIndex,
        [array]$HashAudit,
        [array]$ZipInventory,
        [array]$PolicyRows,
        [array]$AliasRows,
        [array]$RowRows,
        [array]$ApprovalRows,
        [string]$ZipPath,
        [string]$PackageDir,
        [string]$DisabledBoundary
    )

    $rows = New-Object System.Collections.ArrayList
    $rf = $ReadinessF[0]

    $upstreamFail = @($ValidationF | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $hashFail = @($HashAudit | Where-Object { (def_GetProp $_ "def_hash_match") -ne "True" }).Count
    $zipExists = Test-Path -LiteralPath $ZipPath
    $zipLength = 0
    if ($zipExists) { $zipLength = (Get-Item -LiteralPath $ZipPath).Length }

    $allRows = @()
    $allRows += $PolicyRows
    $allRows += $AliasRows
    $allRows += $RowRows
    $allRows += $ApprovalRows

    $unsafe = def_CountUnsafe -Rows $allRows
    $macro = @($RowRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "MACRO_CHINA" }).Count

    def_AddValidation $rows "UPSTREAM" "v0114F1 allow v0114G" ((def_GetProp $rf "def_allow_v0114G") -eq "true") ("Gate=" + (def_GetProp $rf "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "v0114F1 validation pass" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"

    def_AddValidation $rows "PACKAGE" "package directory exists" (Test-Path -LiteralPath $PackageDir) $PackageDir $PackageDir
    def_AddValidation $rows "PACKAGE" "package index rows" (@($PackageIndex).Count -eq 18) ("PackageIndexRows=" + @($PackageIndex).Count)
    def_AddValidation $rows "PACKAGE" "package hash audit pass" ($hashFail -eq 0) "HashFail=$hashFail"
    def_AddValidation $rows "PACKAGE" "zip exists" $zipExists $ZipPath $ZipPath
    def_AddValidation $rows "PACKAGE" "zip non-empty" ($zipLength -gt 0) "ZipLength=$zipLength" $ZipPath
    def_AddValidation $rows "PACKAGE" "zip entry count" (@($ZipInventory).Count -ge 18) ("ZipEntries=" + @($ZipInventory).Count)

    def_AddValidation $rows "COUNT" "policy candidate count" (@($PolicyRows).Count -eq 12) ("Policy=" + @($PolicyRows).Count)
    def_AddValidation $rows "COUNT" "alias candidate count" (@($AliasRows).Count -eq 5) ("Alias=" + @($AliasRows).Count)
    def_AddValidation $rows "COUNT" "row patch count" (@($RowRows).Count -eq 149) ("Rows=" + @($RowRows).Count)

    def_AddValidation $rows "SAFETY" "no unsafe flags" ($unsafe -eq 0) "UnsafeFlags=$unsafe"
    def_AddValidation $rows "SAFETY" "MACRO_CHINA excluded" ($macro -eq 0) "MACRO_CHINA rows=$macro"

    $secretScan = def_ScanRawSecret -Root $PackageDir
    def_AddValidation $rows "SECRET" "no raw secret pattern" $secretScan.Ok $secretScan.Message

    $ast = def_AstCheck -Path $DisabledBoundary
    $danger = def_ScanDanger -Path $DisabledBoundary
    def_AddValidation $rows "APPLY_BOUNDARY" "disabled apply AST clean" $ast.Ok $ast.Message $DisabledBoundary
    def_AddValidation $rows "APPLY_BOUNDARY" "disabled apply no dangerous command" $danger.Ok $danger.Message $DisabledBoundary

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[string]$ZipPath,[array]$PackageIndex,[array]$ZipInventory)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114H_FINAL_RELEASE_REVIEW_GATE"
    $allow = "true"
    $reason = "Release candidate package validation passed. Next phase may create final release review gate only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_PACKAGE_VALIDATION_FAILURE"
        $allow = "false"
        $reason = "Package validation has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114H = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_package_items = "$(@($PackageIndex).Count)"
            def_zip_entries = "$(@($ZipInventory).Count)"
            def_zip_path = $ZipPath
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114H final release review gate only"
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
        'Write-Host "def VIA · v0114H Precheck after v0114G" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114H)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Items      : $($r.def_package_items)" -ForegroundColor Cyan',
        'Write-Host "ZipEntries : $($r.def_zip_entries)" -ForegroundColor Cyan',
        'Write-Host "Zip        : $($r.def_zip_path)" -ForegroundColor Cyan',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114H -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114H." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114H_FINAL_RELEASE_REVIEW_GATE_ONLY" -ForegroundColor Green'
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
    param($Summary,$Readiness,$Validation,$HashAudit,$ZipInventory,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114H",$Summary.AllowV0114H),
        @("Fail",$Summary.ValidationFail),
        @("Items",$Summary.PackageItems),
        @("ZipEntries",$Summary.ZipEntries),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114G Package Validation</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114G · Release Candidate Package Validation Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Validation only · no apply · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114G 只驗證 v0114F1 ZIP 與 package index。通過後下一步仍然只是 v0114H final release review gate，不是正式 apply。</div><span class='tag'>Package Validation</span><span class='tag'>ZIP Checked</span><span class='tag'>SHA256 Checked</span><span class='tag'>Apply Disabled</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114H','def_reason','def_validation_fail','def_package_items','def_zip_entries','def_zip_path','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 90)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def SHA256 Hash Audit</h2>$(def_Table $HashAudit @('def_file','def_exists','def_hash_match','def_expected_sha256','def_actual_sha256','def_dest') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def ZIP Inventory</h2>$(def_Table $ZipInventory @('def_zip_entry','def_name','def_length','def_compressed_length','def_last_write_time') 160)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114F1: $(def_Html $Summary.LatestV0114F1)<br/>ZIP: $(def_Html $Summary.ZipPath)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114G RELEASE CANDIDATE PACKAGE VALIDATION · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Validation only. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0114F1 output"
    $latestF1 = def_GetLatestV0114F1
    $outF1 = def_J $latestF1 "output"
    $summaryF1Path = def_J $outF1 "VIA_v0114F1_HotfixReleaseCandidatePackage_Summary.json"
    $summaryF1 = def_ReadJson $summaryF1Path

    $packageDir = def_S $summaryF1.PackageDir
    $zipPath = def_S $summaryF1.ZipPath
    $manifestJson = def_S $summaryF1.ManifestJson
    $readinessF1Csv = def_S $summaryF1.ReadinessCsv
    $validationF1Csv = def_S $summaryF1.ValidationCsv

    def_Log "OK" "Latest v0114F1: $latestF1" Green
    def_Log "OK" "Package Dir: $packageDir" Green
    def_Log "OK" "ZIP: $zipPath" Green

    def_Progress 2 10 "Load upstream readiness and package index"
    $readinessF1 = def_LoadCsv $readinessF1Csv
    $validationF1 = def_LoadCsv $validationF1Csv
    $manifest = def_ReadJson $manifestJson
    $packageIndexCsv = def_S $manifest.package_index_csv
    $packageIndex = def_LoadCsv $packageIndexCsv

    def_Progress 3 10 "Build hash audit"
    $hashAudit = def_ValidatePackageIndexHashes -PackageIndex $packageIndex

    def_Progress 4 10 "Build ZIP inventory"
    $zipInventory = def_BuildZipInventory -ZipPath $zipPath

    def_Progress 5 10 "Load package candidate rows"
    $candidateDir = def_J $packageDir "candidate_artifacts"
    $approvalDir = def_J $packageDir "approval_gate"
    $disabledDir = def_J $packageDir "disabled_apply_boundary"

    $policyRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv")
    $aliasRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv")
    $rowRows = def_LoadCsv (def_J $candidateDir "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv")
    $approvalRows = def_LoadCsv (def_J $approvalDir "VIA_v0114E_ManualReleaseApproval.csv")
    $disabledBoundary = def_J $disabledDir "Invoke-VIA-v0114F1-DISABLED-ApplyBoundary.ps1"

    def_Progress 6 10 "Validate package"
    $validation = def_BuildValidation -ReadinessF $readinessF1 -ValidationF $validationF1 -PackageIndex $packageIndex -HashAudit $hashAudit -ZipInventory $zipInventory -PolicyRows $policyRows -AliasRows $aliasRows -RowRows $rowRows -ApprovalRows $approvalRows -ZipPath $zipPath -PackageDir $packageDir -DisabledBoundary $disabledBoundary
    $readinessG = def_BuildReadiness -Validation $validation -ZipPath $zipPath -PackageIndex $packageIndex -ZipInventory $zipInventory

    def_Progress 7 10 "Write validation seal outputs"
    $hashAuditCsv = def_J $def_VALIDATION_DIR "VIA_v0114G_SHA256_HashAudit.csv"
    $zipInventoryCsv = def_J $def_VALIDATION_DIR "VIA_v0114G_ZipInventory.csv"
    $validationCsv = def_J $def_OUTPUT_DIR "VIA_v0114G_ValidationMatrix.csv"
    $readinessCsv = def_J $def_OUTPUT_DIR "VIA_v0114G_ReadinessGate.csv"

    def_WriteCsv $hashAudit $hashAuditCsv
    def_WriteCsv $zipInventory $zipInventoryCsv
    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessG $readinessCsv

    def_WriteJson $hashAudit (def_J $def_VALIDATION_DIR "VIA_v0114G_SHA256_HashAudit.json")
    def_WriteJson $zipInventory (def_J $def_VALIDATION_DIR "VIA_v0114G_ZipInventory.json")
    def_WriteJson $validation (def_J $def_OUTPUT_DIR "VIA_v0114G_ValidationMatrix.json")
    def_WriteJson $readinessG (def_J $def_OUTPUT_DIR "VIA_v0114G_ReadinessGate.json")

    def_Progress 8 10 "Write validation seal manifest"
    $sealJson = def_J $def_VALIDATION_DIR "VIA_v0114G_PackageValidationSeal.json"

    $seal = [ordered]@{
        schema_version = "VIA_v0114G_ReleaseCandidatePackageValidationSeal"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114F1 = $latestF1
        package_dir = $packageDir
        zip_path = $zipPath
        package_index_csv = $packageIndexCsv
        hash_audit_csv = $hashAuditCsv
        zip_inventory_csv = $zipInventoryCsv
        readiness_csv = $readinessCsv
        validation_csv = $validationCsv
        policy = [ordered]@{
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

    def_Progress 9 10 "Build precheck, accelerators, next commands"
    $precheck = def_J $def_OUTPUT_DIR "Invoke-VIA-v0114H-Precheck-After-v0114G.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114G_15Accelerators.csv")
    def_WriteJson $accelRows (def_J $def_OUTPUT_DIR "VIA_v0114G_15Accelerators.json")

    $report = def_J $def_REPORT_DIR "VIA_v0114G_ReleaseCandidatePackageValidation_Report.html"
    $nextCmd = def_J $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114G.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_VALIDATION_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114H final release review gate only.',
        '# No apply. No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessG[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114G_RELEASE_CANDIDATE_PACKAGE_VALIDATION_READY"
        RunId = $def_RUN_ID
        LatestV0114F1 = $latestF1
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114H = def_GetProp $r0 "def_allow_v0114H"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        PackageItems = def_GetProp $r0 "def_package_items"
        ZipEntries = def_GetProp $r0 "def_zip_entries"
        ZipPath = $zipPath
        ValidationDir = $def_VALIDATION_DIR
        SealJson = $sealJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; package validation only; NoExit."
    }

    def_WriteJson $summary (def_J $def_OUTPUT_DIR "VIA_v0114G_ReleaseCandidatePackageValidation_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessG -Validation $validation -HashAudit $hashAudit -ZipInventory $zipInventory -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114G Package Validation" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114G Package Validation COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114H    : $($summary.AllowV0114H)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Package Items   : $($summary.PackageItems)" -ForegroundColor Cyan
    Write-Host "ZIP Entries     : $($summary.ZipEntries)" -ForegroundColor Cyan
    Write-Host "ZIP             : $zipPath" -ForegroundColor Cyan
    Write-Host "Seal            : $sealJson" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_VALIDATION_DIR } catch {}
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
