param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0114E_ROOT = "",
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

$def_RUN_ID = "RUN_{0}_VIA_v0114F_RELEASE_CANDIDATE_PACKAGE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0114F_release_candidate_package"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_PACKAGE_DIR = Join-Path $def_RUN_DIR "_release_candidate_package_only"
$def_CANDIDATE_COPY_DIR = Join-Path $def_PACKAGE_DIR "candidate_artifacts"
$def_REVIEW_COPY_DIR = Join-Path $def_PACKAGE_DIR "review_evidence"
$def_APPROVAL_COPY_DIR = Join-Path $def_PACKAGE_DIR "approval_gate"
$def_DISABLED_COPY_DIR = Join-Path $def_PACKAGE_DIR "disabled_apply_boundary"
$def_MANIFEST_DIR = Join-Path $def_PACKAGE_DIR "manifest"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0114F_ReleaseCandidatePackage.log"

$def_ACCELERATORS = @(
    "A01 latest-v0114E auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 v0114E approval gate reuse",
    "A06 v0114D review seal carry-forward",
    "A07 v0114C dry-run evidence carry-forward",
    "A08 v0114A candidate artifact carry-forward",
    "A09 disabled apply boundary included",
    "A10 package checksum matrix",
    "A11 ZIP package generation",
    "A12 no source mutation scanner",
    "A13 no canonical merge scanner",
    "A14 no DB write scanner",
    "A15 compact HTML package report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_PACKAGE_DIR,$def_CANDIDATE_COPY_DIR,$def_REVIEW_COPY_DIR,$def_APPROVAL_COPY_DIR,$def_DISABLED_COPY_DIR,$def_MANIFEST_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0114F Release Candidate Package" -Status $Status -PercentComplete $pct
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
    param($Object,[string]$Path,[int]$Depth = 16)
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

function def_GetLatestV0114E {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0114E_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0114E_ROOT) { return $def_PARAM_V0114E_ROOT }
        throw "Specified v0114E root does not exist: $def_PARAM_V0114E_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0114E_manual_release_approval"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0114E output root not found: $root" }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0114E_ManualReleaseApproval_Summary.json") } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) { throw "No v0114E output found under: $root" }
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

function def_CopyArtifact {
    param([string]$Source,[string]$DestDir,[string]$Prefix)

    if (-not (Test-Path -LiteralPath $Source)) {
        return [pscustomobject][ordered]@{
            def_source = $Source
            def_dest = ""
            def_exists = "false"
            def_copied = "false"
            def_sha256 = ""
            def_length = "0"
            def_group = $Prefix
        }
    }

    $name = Split-Path $Source -Leaf
    $dest = Join-Path $DestDir $name
    Copy-Item -LiteralPath $Source -Destination $dest -Force

    return [pscustomobject][ordered]@{
        def_source = $Source
        def_dest = $dest
        def_exists = "true"
        def_copied = [string](Test-Path -LiteralPath $dest)
        def_sha256 = def_GetFileSha $dest
        def_length = [string]((Get-Item -LiteralPath $dest).Length)
        def_group = $Prefix
    }
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

function def_BuildPackageIndex {
    param([array]$CopyRows)

    $rows = New-Object System.Collections.ArrayList
    $n = 0

    foreach ($r in $CopyRows) {
        $n++
        [void]$rows.Add([pscustomobject][ordered]@{
            def_package_item_id = "PKG_{0:0000}" -f $n
            def_group = def_GetProp $r "def_group"
            def_file = Split-Path (def_GetProp $r "def_dest") -Leaf
            def_copied = def_GetProp $r "def_copied"
            def_length = def_GetProp $r "def_length"
            def_sha256 = def_GetProp $r "def_sha256"
            def_dest = def_GetProp $r "def_dest"
            def_source = def_GetProp $r "def_source"
        })
    }

    return @($rows)
}

function def_BuildReadme {
    param([string]$Path,[string]$RunId)

    $lines = @(
        "# VIA v0114F Release Candidate Package Only",
        "",
        "Run ID: $RunId",
        "",
        "This package is a release candidate package only.",
        "",
        "Policy:",
        "- No apply",
        "- No source mutation",
        "- No canonical merge",
        "- No DB write",
        "- Disabled apply boundary retained",
        "- FRED raw value forbidden",
        "- MACRO_CHINA remains excluded",
        "",
        "Next allowed phase: v0114G release candidate package validation only."
    )

    Set-Content -LiteralPath $Path -Value $lines -Encoding UTF8
}

function def_BuildDisabledApplyBoundary {
    param([string]$Path)

    $lines = @(
        '$ErrorActionPreference = "Continue"',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA · v0114F Release Candidate Package · Disabled Apply Boundary" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "[BLOCKED] Package only. Apply is disabled." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No source mutation." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No canonical merge." -ForegroundColor Yellow',
        'Write-Host "[BLOCKED] No DB write." -ForegroundColor Yellow',
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
        [array]$ReadinessE,
        [array]$ValidationE,
        [array]$ApprovalE,
        [array]$PackageIndex,
        [array]$AllLoadedRows,
        [string]$ZipPath,
        [string]$DisabledBoundary
    )

    $rows = New-Object System.Collections.ArrayList
    $re = $ReadinessE[0]
    $ae = $ApprovalE[0]

    $upstreamFail = @($ValidationE | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $copyFail = @($PackageIndex | Where-Object { (def_GetProp $_ "def_copied") -ne "true" }).Count
    $unsafe = def_CountUnsafe -Rows $AllLoadedRows

    def_AddValidation $rows "UPSTREAM" "v0114E allow v0114F" ((def_GetProp $re "def_allow_v0114F") -eq "true") ("Gate=" + (def_GetProp $re "def_gate_status"))
    def_AddValidation $rows "UPSTREAM" "manual release YES" ((def_GetProp $ae "def_user_release_accept") -eq "YES") ("Release=" + (def_GetProp $ae "def_user_release_accept"))
    def_AddValidation $rows "UPSTREAM" "v0114E validation pass" ($upstreamFail -eq 0) "UpstreamFail=$upstreamFail"

    def_AddValidation $rows "PACKAGE" "package files copied" ($copyFail -eq 0) "CopyFail=$copyFail"
    def_AddValidation $rows "PACKAGE" "package index non-empty" (@($PackageIndex).Count -ge 18) ("PackageItems=" + @($PackageIndex).Count)
    def_AddValidation $rows "PACKAGE" "zip package exists" (Test-Path -LiteralPath $ZipPath) $ZipPath $ZipPath
    def_AddValidation $rows "PACKAGE" "zip package non-empty" ($(if (Test-Path -LiteralPath $ZipPath) { ((Get-Item -LiteralPath $ZipPath).Length -gt 0) } else { $false })) ("ZipLength=" + $(if (Test-Path -LiteralPath $ZipPath) { (Get-Item -LiteralPath $ZipPath).Length } else { 0 })) $ZipPath

    def_AddValidation $rows "SAFETY" "no unsafe flags carried" ($unsafe -eq 0) "UnsafeFlags=$unsafe"

    $ast = def_AstCheck -Path $DisabledBoundary
    def_AddValidation $rows "APPLY_BOUNDARY" "disabled apply AST clean" $ast.Ok $ast.Message $DisabledBoundary

    return @($rows)
}

function def_BuildReadiness {
    param([array]$Validation,[string]$ZipPath,[array]$PackageIndex)

    $fail = @($Validation | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count

    $gate = "READY_FOR_v0114G_RELEASE_CANDIDATE_PACKAGE_VALIDATION"
    $allow = "true"
    $reason = "Release candidate package generated. Next phase may validate package only."

    if ($fail -gt 0) {
        $gate = "BLOCKED_RELEASE_PACKAGE_VALIDATION_FAILURE"
        $allow = "false"
        $reason = "Package validation has fail rows."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114G = $allow
            def_reason = $reason
            def_validation_fail = "$fail"
            def_package_items = "$(@($PackageIndex).Count)"
            def_zip_path = $ZipPath
            def_apply_enabled = "false"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_db_write = "false"
            def_next_allowed_phase = "v0114G release candidate package validation only"
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
        'Write-Host "def VIA · v0114G Precheck after v0114F" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow',
        'Write-Host "Allow      : $($r.def_allow_v0114G)" -ForegroundColor Yellow',
        'Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow',
        'Write-Host "Items      : $($r.def_package_items)" -ForegroundColor Cyan',
        'Write-Host "Zip        : $($r.def_zip_path)" -ForegroundColor Cyan',
        'Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow',
        'Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow',
        'Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow',
        'Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow',
        'if ($r.def_allow_v0114G -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114G." }',
        'if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }',
        'if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }',
        'Write-Host "[OK] READY_FOR_v0114G_RELEASE_CANDIDATE_PACKAGE_VALIDATION_ONLY" -ForegroundColor Green'
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
    param($Summary,$Readiness,$Validation,$PackageIndex,$AccelRows,$ReportPath)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114G",$Summary.AllowV0114G),
        @("Fail",$Summary.ValidationFail),
        @("Items",$Summary.PackageItems),
        @("ZIP","ready"),
        @("Apply","false"),
        @("DB Write","false")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>")
    [void]$html.AppendLine("<title>VIA v0114F Release Candidate Package</title>")
    [void]$html.AppendLine("<style>body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.4px;line-height:1.32}.wrap{max-width:1800px;margin:0 auto;padding:15px}h1{font-size:14.5px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}h2{font-size:9.5px;margin:0 0 6px;font-weight:650}.note{font-size:8.1px;color:#706d64;margin:0 0 7px}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.75px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}.footer{margin-top:11px;color:#706d64;font-size:8px}</style>")
    [void]$html.AppendLine("</head><body><div class='wrap'>")
    [void]$html.AppendLine("<h1>def VIA v0114F · Release Candidate Package Only</h1>")
    [void]$html.AppendLine("<div class='sub'>Package only · no apply · no source mutation · no canonical merge · no DB write · no close</div>")
    [void]$html.AppendLine("<div class='cards'>$cards</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Executive Judgment</h2><div class='note'>v0114F 只產生 release candidate package 與 ZIP。這不是正式 apply。下一步 v0114G 仍然只驗證 package。</div><span class='tag'>Package Only</span><span class='tag'>ZIP Ready</span><span class='tag'>Apply Disabled</span><span class='tag'>No Source Mutation</span><span class='tag'>No DB Write</span></div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Readiness Gate</h2>$(def_Table $Readiness @('def_gate_status','def_allow_v0114G','def_reason','def_validation_fail','def_package_items','def_zip_path','def_apply_enabled','def_source_mutation','def_canonical_merge','def_db_write','def_next_allowed_phase') 20)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Validation Matrix</h2>$(def_Table $Validation @('def_layer','def_test','def_status','def_risk','def_message','def_path') 80)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def Package Index</h2>$(def_Table $PackageIndex @('def_package_item_id','def_group','def_file','def_copied','def_length','def_sha256','def_dest') 120)</div>")
    [void]$html.AppendLine("<div class='sec'><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @('def_no','def_accelerator') 20)</div>")
    [void]$html.AppendLine("<div class='footer'>Run: $(def_Html $Summary.RunId)<br/>Latest v0114E: $(def_Html $Summary.LatestV0114E)<br/>Package Dir: $(def_Html $Summary.PackageDir)<br/>ZIP: $(def_Html $Summary.ZipPath)<br/>Report: $(def_Html $ReportPath)</div>")
    [void]$html.AppendLine("</div></body></html>")

    Set-Content -LiteralPath $ReportPath -Value $html.ToString() -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0114F RELEASE CANDIDATE PACKAGE ONLY · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: Package only. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow

    def_Progress 1 11 "Find latest v0114E output"
    $latestE = def_GetLatestV0114E
    $outE = Join-Path $latestE "output"
    $approvalEdir = Join-Path $latestE "_manual_release_approval_gate"
    $summaryEPath = Join-Path $outE "VIA_v0114E_ManualReleaseApproval_Summary.json"
    $summaryE = def_ReadJson $summaryEPath
    $latestD = def_S $summaryE.LatestV0114D
    def_Log "OK" "Latest v0114E: $latestE" Green
    def_Log "OK" "Latest v0114D: $latestD" Green

    def_Progress 2 11 "Resolve upstream chain"
    $summaryDPath = Join-Path $latestD "output\VIA_v0114D_SandboxReviewSeal_Summary.json"
    $summaryD = def_ReadJson $summaryDPath
    $latestC = def_S $summaryD.LatestV0114C

    $summaryCPath = Join-Path $latestC "output\VIA_v0114C_SandboxDryRunSimulation_Summary.json"
    $summaryC = def_ReadJson $summaryCPath
    $latestA = def_S $summaryC.LatestV0114A

    if (-not (Test-Path -LiteralPath $latestC)) { throw "Latest v0114C missing: $latestC" }
    if (-not (Test-Path -LiteralPath $latestA)) { throw "Latest v0114A missing: $latestA" }

    def_Log "OK" "Latest v0114C: $latestC" Green
    def_Log "OK" "Latest v0114A: $latestA" Green

    def_Progress 3 11 "Load v0114E approval gate"
    $readinessE = def_LoadCsv (Join-Path $outE "VIA_v0114E_ReadinessGate.csv")
    $validationE = def_LoadCsv (Join-Path $outE "VIA_v0114E_ValidationMatrix.csv")
    $approvalE = def_LoadCsv (Join-Path $approvalEdir "VIA_v0114E_ManualReleaseApproval.csv")

    def_Progress 4 11 "Resolve package source artifacts"
    $candA = Join-Path $latestA "_sandbox_patch_candidate"
    $diffA = Join-Path $latestA "_diff_preview"
    $disabledA = Join-Path $latestA "_disabled_apply_script"
    $sandboxC = Join-Path $latestC "_dryrun_sandbox_only"
    $sealD = Join-Path $latestD "_review_seal_package"
    $manualD = Join-Path $latestD "_manual_release_gate_draft"

    $candidateSources = @(
        Join-Path $candA "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv",
        Join-Path $candA "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv",
        Join-Path $candA "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv",
        Join-Path $candA "VIA_v0114A_SandboxPatchCandidate_Manifest.json",
        Join-Path $diffA "VIA_v0114A_DIFF_PREVIEW.csv"
    )

    $reviewSources = @(
        Join-Path $sandboxC "VIA_v0114C_SIMULATED_POLICY_REGISTRY.csv",
        Join-Path $sandboxC "VIA_v0114C_SIMULATED_ALIAS_REGISTRY.csv",
        Join-Path $sandboxC "VIA_v0114C_SIMULATED_ROW_MAPPING.csv",
        Join-Path $sandboxC "VIA_v0114C_DRYRUN_ACTION_PLAN.csv",
        Join-Path $sealD "VIA_v0114D_ReviewSeal.json",
        Join-Path $sealD "VIA_v0114D_EvidenceManifest.csv"
    )

    $approvalSources = @(
        Join-Path $approvalEdir "VIA_v0114E_ManualReleaseApproval.csv",
        Join-Path $outE "VIA_v0114E_ReadinessGate.csv",
        Join-Path $outE "VIA_v0114E_ValidationMatrix.csv",
        $summaryEPath
    )

    $disabledSources = @(
        Join-Path $disabledA "Invoke-VIA-v0114A-DISABLED-ApplyBoundary.ps1"
    )

    def_Progress 5 11 "Copy candidate artifacts into package"
    $copyRows = New-Object System.Collections.ArrayList

    foreach ($p in $candidateSources) { [void]$copyRows.Add((def_CopyArtifact -Source $p -DestDir $def_CANDIDATE_COPY_DIR -Prefix "candidate")) }
    foreach ($p in $reviewSources) { [void]$copyRows.Add((def_CopyArtifact -Source $p -DestDir $def_REVIEW_COPY_DIR -Prefix "review")) }
    foreach ($p in $approvalSources) { [void]$copyRows.Add((def_CopyArtifact -Source $p -DestDir $def_APPROVAL_COPY_DIR -Prefix "approval")) }
    foreach ($p in $disabledSources) { [void]$copyRows.Add((def_CopyArtifact -Source $p -DestDir $def_DISABLED_COPY_DIR -Prefix "disabled_apply")) }

    def_Progress 6 11 "Build package index and manifest"
    $packageIndex = def_BuildPackageIndex -CopyRows $copyRows
    $packageIndexCsv = Join-Path $def_MANIFEST_DIR "VIA_v0114F_PackageIndex.csv"
    $readmePath = Join-Path $def_PACKAGE_DIR "README_v0114F_RELEASE_CANDIDATE_PACKAGE_ONLY.md"
    $disabledBoundary = Join-Path $def_DISABLED_COPY_DIR "Invoke-VIA-v0114F-DISABLED-ApplyBoundary.ps1"

    def_WriteCsv $packageIndex $packageIndexCsv
    def_WriteJson $packageIndex (Join-Path $def_MANIFEST_DIR "VIA_v0114F_PackageIndex.json")
    def_BuildReadme -Path $readmePath -RunId $def_RUN_ID
    def_BuildDisabledApplyBoundary -Path $disabledBoundary

    def_Progress 7 11 "Load candidate rows for safety validation"
    $policyRows = def_LoadCsv (Join-Path $def_CANDIDATE_COPY_DIR "VIA_v0114A_POLICY_REGISTRY_CANDIDATE.csv")
    $aliasRows = def_LoadCsv (Join-Path $def_CANDIDATE_COPY_DIR "VIA_v0114A_ALIAS_REGISTRY_CANDIDATE.csv")
    $rowRows = def_LoadCsv (Join-Path $def_CANDIDATE_COPY_DIR "VIA_v0114A_ROW_PATCH_PLAN_CANDIDATE.csv")
    $approvalRows = def_LoadCsv (Join-Path $def_APPROVAL_COPY_DIR "VIA_v0114E_ManualReleaseApproval.csv")

    $allLoadedRows = @()
    $allLoadedRows += $policyRows
    $allLoadedRows += $aliasRows
    $allLoadedRows += $rowRows
    $allLoadedRows += $approvalRows

    def_Progress 8 11 "Generate ZIP package"
    $zipPath = Join-Path $def_OUTPUT_DIR ("VIA_v0114F_ReleaseCandidatePackageOnly_{0}.zip" -f $def_RUN_ID)

    try {
        Compress-Archive -Path (Join-Path $def_PACKAGE_DIR "*") -DestinationPath $zipPath -CompressionLevel Optimal
    } catch {
        throw "ZIP generation failed: $($_.Exception.Message)"
    }

    def_Progress 9 11 "Validate package"
    $validation = def_BuildValidation -ReadinessE $readinessE -ValidationE $validationE -ApprovalE $approvalE -PackageIndex $packageIndex -AllLoadedRows $allLoadedRows -ZipPath $zipPath -DisabledBoundary $disabledBoundary
    $readinessF = def_BuildReadiness -Validation $validation -ZipPath $zipPath -PackageIndex $packageIndex

    def_Progress 10 11 "Write outputs and precheck"
    $validationCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114F_ValidationMatrix.csv"
    $readinessCsv = Join-Path $def_OUTPUT_DIR "VIA_v0114F_ReadinessGate.csv"
    $manifestJson = Join-Path $def_MANIFEST_DIR "VIA_v0114F_ReleaseCandidatePackage_Manifest.json"

    def_WriteCsv $validation $validationCsv
    def_WriteCsv $readinessF $readinessCsv
    def_WriteJson $validation (Join-Path $def_OUTPUT_DIR "VIA_v0114F_ValidationMatrix.json")
    def_WriteJson $readinessF (Join-Path $def_OUTPUT_DIR "VIA_v0114F_ReadinessGate.json")

    $manifest = [ordered]@{
        schema_version = "VIA_v0114F_ReleaseCandidatePackageOnly"
        run_id = $def_RUN_ID
        generated_at = (Get-Date).ToString("s")
        latest_v0114E = $latestE
        latest_v0114D = $latestD
        latest_v0114C = $latestC
        latest_v0114A = $latestA
        package_dir = $def_PACKAGE_DIR
        zip_path = $zipPath
        package_index_csv = $packageIndexCsv
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

    def_WriteJson $manifest $manifestJson 18

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114G-Precheck-After-v0114F.ps1"
    def_BuildPrecheck -ReadinessCsv $readinessCsv -Path $precheck

    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114F_15Accelerators.csv")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0114F_15Accelerators.json")

    $report = Join-Path $def_REPORT_DIR "VIA_v0114F_ReleaseCandidatePackage_Report.html"
    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0114F.ps1"

    $nextLines = @(
        'Start-Process "' + (def_EscapePsDouble $report) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_OUTPUT_DIR) + '"',
        'Start-Process "' + (def_EscapePsDouble $def_PACKAGE_DIR) + '"',
        'Import-Csv "' + (def_EscapePsDouble $readinessCsv) + '" | Format-Table -AutoSize',
        'Import-Csv "' + (def_EscapePsDouble $validationCsv) + '" | Format-Table -AutoSize',
        'pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "' + (def_EscapePsDouble $precheck) + '"',
        '# Next: v0114G release candidate package validation only.',
        '# No apply. No source mutation. No canonical merge. No DB write.'
    )
    Set-Content -LiteralPath $nextCmd -Value $nextLines -Encoding UTF8

    $r0 = $readinessF[0]
    $failCount = [int](def_GetProp $r0 "def_validation_fail")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0114F_RELEASE_CANDIDATE_PACKAGE_READY"
        RunId = $def_RUN_ID
        LatestV0114E = $latestE
        GateStatus = def_GetProp $r0 "def_gate_status"
        AllowV0114G = def_GetProp $r0 "def_allow_v0114G"
        ValidationFail = def_GetProp $r0 "def_validation_fail"
        PackageItems = def_GetProp $r0 "def_package_items"
        PackageDir = $def_PACKAGE_DIR
        ZipPath = $zipPath
        ManifestJson = $manifestJson
        ReadinessCsv = $readinessCsv
        ValidationCsv = $validationCsv
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; no source mutation; no canonical merge; no DB write; release candidate package only; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0114F_ReleaseCandidatePackage_Summary.json")

    def_Progress 11 11 "Write compact HTML report"
    def_WriteReport -Summary $summary -Readiness $readinessF -Validation $validation -PackageIndex $packageIndex -AccelRows $accelRows -ReportPath $report

    Write-Progress -Activity "VIA v0114F Release Candidate Package" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0114F Release Candidate Package COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114G    : $($summary.AllowV0114G)" -ForegroundColor Yellow
    Write-Host "Validation Fail : $($summary.ValidationFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Package Items   : $($summary.PackageItems)" -ForegroundColor Cyan
    Write-Host "Package Dir     : $def_PACKAGE_DIR" -ForegroundColor Cyan
    Write-Host "ZIP             : $zipPath" -ForegroundColor Cyan
    Write-Host "Manifest        : $manifestJson" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

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
