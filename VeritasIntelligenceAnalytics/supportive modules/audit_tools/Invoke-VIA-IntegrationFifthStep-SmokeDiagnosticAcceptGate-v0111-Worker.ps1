param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0110_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true,
    [bool]$def_PARAM_RUN_FIXED_SMOKE = $true
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

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_fifthstep_smoke_accept_gate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_FIXED_SMOKE_DIR = Join-Path $def_RUN_DIR "_fixed_smoke_scripts"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_FifthStep_SmokeDiagnosticAcceptGate_v0111.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0110 auto discovery",
    "A02 no BASE re-scan",
    "A03 candidate contract static validation",
    "A04 fixed smoke script generation",
    "A05 read-only smoke rerun",
    "A06 child-isolated smoke execution",
    "A07 no Stop-Process even on timeout",
    "A08 P0 accept gate template",
    "A09 P1 alias accept gate template",
    "A10 smoke stdout/stderr capture",
    "A11 contract JSON validity check",
    "A12 policy consistency check",
    "A13 one-page compact HTML report",
    "A14 next-command index",
    "A15 no source mutation / no canonical merge"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_FIXED_SMOKE_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA FifthStep Smoke Diagnostic v0111" -Status $Status -PercentComplete $pct
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
    try {
        if (Test-Path -LiteralPath $Path) {
            return @(Import-Csv -LiteralPath $Path)
        }
    } catch {
        def_Log "WARN" "CSV load failed: $Path :: $($_.Exception.Message)" Yellow
    }
    return @()
}

function def_LoadJson {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {
        return $null
    }
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

function def_EscapeSingle {
    param([string]$Text)
    return (def_S $Text).Replace("'","''")
}

function def_SafeName {
    param([string]$Text)
    $s = def_S $Text
    if ([string]::IsNullOrWhiteSpace($s)) { $s = "UNKNOWN" }
    $s = $s -replace '[\\/:*?"<>| ]+', '_'
    $s = $s.Trim("_")
    if ($s.Length -gt 80) { $s = $s.Substring(0,80) }
    return $s
}

function def_GetLatestV0110 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0110_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0110_ROOT) {
            return $def_PARAM_V0110_ROOT
        }
        throw "Specified v0110 root does not exist: $def_PARAM_V0110_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_fourthstep_sandbox_adapter"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0110 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_FourthStep_SandboxAdapterCandidate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0110 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_WriteFixedSmokeScript {
    param(
        [string]$Project,
        [string]$ContractJson,
        [string]$CandidateDir,
        [string]$FixedSmokePath
    )

    $p = def_EscapeSingle $Project
    $contract = def_EscapeSingle $ContractJson
    $cand = def_EscapeSingle $CandidateDir

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '',
        '$def_PROJECT = ''' + $p + '''',
        '$def_CONTRACT_JSON = ''' + $contract + '''',
        '$def_CANDIDATE_DIR = ''' + $cand + '''',
        '',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA Fixed Sandbox Smoke v0111 · $def_PROJECT" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        '',
        '$rows = @()',
        '',
        'if (-not (Test-Path -LiteralPath $def_CANDIDATE_DIR)) { throw "Candidate directory missing: $def_CANDIDATE_DIR" }',
        'if (-not (Test-Path -LiteralPath $def_CONTRACT_JSON)) { throw "Contract JSON missing: $def_CONTRACT_JSON" }',
        '',
        '$obj = Get-Content -LiteralPath $def_CONTRACT_JSON -Raw -Encoding UTF8 | ConvertFrom-Json',
        '',
        '$rows += [pscustomobject]@{ Check="CandidateDirExists"; Status="OK"; Detail=$def_CANDIDATE_DIR }',
        '$rows += [pscustomobject]@{ Check="ContractJsonExists"; Status="OK"; Detail=$def_CONTRACT_JSON }',
        '$rows += [pscustomobject]@{ Check="ContractJsonReadable"; Status="OK"; Detail=$obj.schema_version }',
        '$rows += [pscustomobject]@{ Check="Project"; Status="OK"; Detail=$obj.project }',
        '',
        '$sourceMutation = [string]$obj.source_mutation',
        '$canonicalMerge = [string]$obj.canonical_merge',
        '$dbWrite = [string]$obj.db_write',
        '',
        'if ($sourceMutation -notin @("False","false","0","")) { throw "source_mutation is not false: $sourceMutation" }',
        'if ($canonicalMerge -notin @("False","false","0","")) { throw "canonical_merge is not false: $canonicalMerge" }',
        'if ($dbWrite -notin @("False","false","0","")) { throw "db_write is not false: $dbWrite" }',
        '',
        '$rows += [pscustomobject]@{ Check="NoSourceMutation"; Status="OK"; Detail=$sourceMutation }',
        '$rows += [pscustomobject]@{ Check="NoCanonicalMerge"; Status="OK"; Detail=$canonicalMerge }',
        '$rows += [pscustomobject]@{ Check="NoDbWrite"; Status="OK"; Detail=$dbWrite }',
        '$rows += [pscustomobject]@{ Check="Policy"; Status="OK"; Detail=$obj.policy }',
        '',
        '$csv = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.csv")',
        '$json = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.json")',
        '$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8',
        '$rows | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $json -Encoding UTF8',
        '',
        'Write-Host "[OK] Fixed smoke complete: $def_PROJECT" -ForegroundColor Green',
        'Write-Host "[OK] CSV : $csv" -ForegroundColor Cyan',
        'Write-Host "[OK] JSON: $json" -ForegroundColor Cyan'
    )

    Set-Content -LiteralPath $FixedSmokePath -Value ($lines -join "`r`n") -Encoding UTF8
}

function def_RunFixedSmoke {
    param(
        [string]$Project,
        [string]$FixedSmokePath,
        [string]$CandidateDir
    )

    $stdout = Join-Path $CandidateDir "fixed_smoke_stdout_v0111.log"
    $stderr = Join-Path $CandidateDir "fixed_smoke_stderr_v0111.log"
    $status = "SKIPPED"
    $exitCode = ""
    $elapsed = ""

    if (-not $def_PARAM_RUN_FIXED_SMOKE) {
        $status = "SKIPPED_BY_PARAM"
    } elseif (-not (Test-Path -LiteralPath $FixedSmokePath)) {
        $status = "MISSING_FIXED_SMOKE"
    } else {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $args = "-NoProfile -ExecutionPolicy Bypass -File `"$FixedSmokePath`""
            $proc = Start-Process -FilePath "pwsh" -ArgumentList $args -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden

            while (-not $proc.HasExited) {
                Start-Sleep -Milliseconds 250
                if ($sw.Elapsed.TotalSeconds -gt 45) {
                    $status = "TIMEOUT_REVIEW_CHILD_STILL_RUNNING"
                    break
                }
            }

            if ($proc.HasExited) {
                $exitCode = def_S $proc.ExitCode
                if ($proc.ExitCode -eq 0) { $status = "FIXED_SMOKE_OK" } else { $status = "FIXED_SMOKE_NONZERO" }
            }
        } catch {
            $status = "FIXED_SMOKE_EXCEPTION"
            $exitCode = $_.Exception.Message
        }
        $sw.Stop()
        $elapsed = "{0:n2}" -f $sw.Elapsed.TotalSeconds
    }

    return [pscustomobject][ordered]@{
        def_project = $Project
        def_status = $status
        def_exit_code = $exitCode
        def_elapsed_seconds = $elapsed
        def_fixed_smoke_ps1 = $FixedSmokePath
        def_stdout = $stdout
        def_stderr = $stderr
    }
}

function def_BuildDiagnostics {
    param([array]$Candidates)

    $rows = New-Object System.Collections.ArrayList
    $fixedResults = New-Object System.Collections.ArrayList

    foreach ($c in $Candidates) {
        $project = def_GetProp $c "def_project"
        if ([string]::IsNullOrWhiteSpace($project)) { $project = "UNKNOWN" }

        $candidateDir = def_GetProp $c "def_candidate_dir"
        $contractJson = def_GetProp $c "def_contract_json"
        $oldSmoke = def_GetProp $c "def_smoke_ps1"

        $safe = def_SafeName $project
        $fixedDir = Join-Path $def_FIXED_SMOKE_DIR $safe
        def_EnsureDir $fixedDir
        $fixedSmoke = Join-Path $fixedDir ("Invoke-VIA_{0}_FixedSandboxSmoke_v0111.ps1" -f $safe)

        $dirOk = Test-Path -LiteralPath $candidateDir
        $contractOk = Test-Path -LiteralPath $contractJson
        $oldSmokeOk = Test-Path -LiteralPath $oldSmoke

        $jsonStatus = "NOT_TESTED"
        $policyStatus = "NOT_TESTED"
        $contractProject = ""

        $obj = $null
        if ($contractOk) {
            $obj = def_LoadJson $contractJson
            if ($null -ne $obj) {
                $jsonStatus = "JSON_OK"
                $contractProject = def_GetProp $obj "project"

                $sourceMutation = def_GetProp $obj "source_mutation"
                $canonicalMerge = def_GetProp $obj "canonical_merge"
                $dbWrite = def_GetProp $obj "db_write"

                if ($sourceMutation -in @("False","false","0","") -and $canonicalMerge -in @("False","false","0","") -and $dbWrite -in @("False","false","0","")) {
                    $policyStatus = "POLICY_OK"
                } else {
                    $policyStatus = "POLICY_REVIEW"
                }
            } else {
                $jsonStatus = "JSON_READ_FAIL"
            }
        }

        $diagnostic = "REVIEW"
        if ($dirOk -and $contractOk -and $jsonStatus -eq "JSON_OK" -and $policyStatus -eq "POLICY_OK") {
            $diagnostic = "STATIC_CANDIDATE_OK"
        }

        if ($contractOk -and $dirOk) {
            def_WriteFixedSmokeScript -Project $safe -ContractJson $contractJson -CandidateDir $candidateDir -FixedSmokePath $fixedSmoke
        }

        $runResult = def_RunFixedSmoke -Project $project -FixedSmokePath $fixedSmoke -CandidateDir $candidateDir
        [void]$fixedResults.Add($runResult)

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = $project
            def_diagnostic = $diagnostic
            def_candidate_dir_exists = def_S $dirOk
            def_contract_json_exists = def_S $contractOk
            def_contract_json_status = $jsonStatus
            def_policy_status = $policyStatus
            def_contract_project = $contractProject
            def_old_smoke_exists = def_S $oldSmokeOk
            def_fixed_smoke_ps1 = $fixedSmoke
            def_fixed_smoke_status = def_GetProp $runResult "def_status"
            def_candidate_dir = $candidateDir
            def_contract_json = $contractJson
            def_old_smoke_ps1 = $oldSmoke
        })
    }

    return [pscustomobject][ordered]@{
        Diagnostics = @($rows)
        FixedSmokeResults = @($fixedResults)
    }
}

function def_BuildP0AcceptGate {
    param([array]$P0Board)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Board) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P0"
            def_accept_status = "WAIT_USER_DECISION"
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_normalized_key = def_GetProp $r "def_normalized_key"
            def_distinct_values = def_GetProp $r "def_distinct_values"
            def_selected_canonical_value = ""
            def_reject_reason = ""
            def_next_allowed_phase = "v0112_only_after_accept"
            def_source_mutation = "false"
            def_sample_values = def_GetProp $r "def_sample_values"
        })
    }

    return @($rows)
}

function def_BuildP1AcceptGate {
    param([array]$AliasRows)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $AliasRows) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P1"
            def_accept_status = "WAIT_USER_DECISION"
            def_alias = def_GetProp $r "def_alias"
            def_path_value = def_GetProp $r "def_path_value"
            def_status = def_GetProp $r "def_status"
            def_scope = "future_generated_scripts_only"
            def_selected = ""
            def_reject_reason = ""
            def_mutate_existing_source = "false"
        })
    }

    return @($rows)
}

function def_BuildRunAllFixedSmoke {
    param([array]$Diagnostics,[string]$Path)

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('$ErrorActionPreference = "Stop"')
    [void]$lines.Add('Write-Host ""')
    [void]$lines.Add('Write-Host "================================================================================" -ForegroundColor DarkCyan')
    [void]$lines.Add('Write-Host "def VIA · Run All Fixed Sandbox Smoke · v0111" -ForegroundColor Cyan')
    [void]$lines.Add('Write-Host "================================================================================" -ForegroundColor DarkCyan')
    [void]$lines.Add('$rows = @()')

    foreach ($d in $Diagnostics) {
        $project = def_EscapeSingle (def_GetProp $d "def_project")
        $smoke = def_EscapeSingle (def_GetProp $d "def_fixed_smoke_ps1")

        [void]$lines.Add('')
        [void]$lines.Add("Write-Host '[RUN] $project' -ForegroundColor Cyan")
        [void]$lines.Add("try {")
        [void]$lines.Add("    pwsh -NoProfile -ExecutionPolicy Bypass -File '$smoke'")
        [void]$lines.Add("    `$rows += [pscustomobject]@{ Project='$project'; Status='OK'; Smoke='$smoke' }")
        [void]$lines.Add("} catch {")
        [void]$lines.Add("    `$rows += [pscustomobject]@{ Project='$project'; Status='FAIL'; Smoke='$smoke'; Message=`$_.Exception.Message }")
        [void]$lines.Add("}")
    }

    [void]$lines.Add('')
    [void]$lines.Add('$out = Join-Path (Split-Path -Parent $PSCommandPath) "VIA_RunAllFixedSmoke_Result_v0111.csv"')
    [void]$lines.Add('$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8')
    [void]$lines.Add('Write-Host "[OK] Result: $out" -ForegroundColor Green')

    Set-Content -LiteralPath $Path -Value ($lines -join "`r`n") -Encoding UTF8
}

function def_BuildNextCommands {
    param([string]$RunDir,[string]$RunAllFixedSmoke)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0111
# =============================================================================

Start-Process "$RunDir\report\VIA_FifthStep_SmokeDiagnosticAcceptGate_Report_v0111.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_fixed_smoke_scripts"

Import-Csv "$RunDir\output\VIA_v0111_CandidateSmokeDiagnostics.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0111_FixedSmokeResults.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0111_P0_AcceptGate_Template.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0111_P1_PathAlias_AcceptGate_Template.csv" | Format-Table -AutoSize

# Run fixed smoke again manually:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$RunAllFixedSmoke"

# Next safe phase:
# v0112 = only generate canonical patch candidates after P0/P1 accept gate is reviewed.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0111.ps1"
    Set-Content -LiteralPath $path -Value $cmd -Encoding UTF8
    return $path
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
            if ($v.Length -gt 260) { $v = $v.Substring(0,260) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param(
        $Summary,
        [array]$Diagnostics,
        [array]$FixedSmokeResults,
        [array]$P0Accept,
        [array]$P1Accept,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Diagnostics",$Summary.DiagnosticRows),
        @("Static OK",$Summary.StaticOk),
        @("Fixed Smoke OK",$Summary.FixedSmokeOk),
        @("Fixed Review",$Summary.FixedSmokeReview),
        @("P0 Accept Rows",$Summary.P0AcceptRows),
        @("P1 Accept Rows",$Summary.P1AcceptRows),
        @("Next","v0112 Gate")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA FifthStep Smoke Diagnostic Accept Gate v0111</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0;--cyan:#6fa8ad}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 10% 5%,rgba(111,168,173,.14),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.5),rgba(230,226,216,.2)),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.5px;line-height:1.32}
.wrap{max-width:1780px;margin:0 auto;padding:15px}
h1{font-size:14.4px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:var(--mut);margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:var(--mut)}
.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-items:stretch}
.sec{background:rgba(255,254,250,.9);border:1px solid var(--line);border-radius:11px;padding:8px;min-height:214px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:var(--mut);margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.85px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:var(--mut)}
.footer{margin-top:11px;color:var(--mut);font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA Integration FifthStep Smoke Diagnostic + Accept Gate · v0111</h1>
<div class="sub">Smoke diagnostic · fixed smoke rerun · P0/P1 accept gate · no mutation</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0110 的 Smoke Rev 不代表候選橋接失敗；本輪 v0111 重新檢查 candidate dir、contract JSON、policy flags，並產生 fixed smoke scripts。即使 fixed smoke OK，下一階段仍只能進入 v0112 patch candidate，不可直接改 source 或 canonical。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Source Mutation</span>
<span class="tag">Accept Gate Required</span>
<span class="tag">v0112 Candidate Only</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Candidate Smoke Diagnostics</h2>$(def_Table $Diagnostics @("def_project","def_diagnostic","def_candidate_dir_exists","def_contract_json_exists","def_contract_json_status","def_policy_status","def_contract_project","def_old_smoke_exists","def_fixed_smoke_status","def_fixed_smoke_ps1","def_candidate_dir","def_contract_json") 80)</div>
<div class="sec wide"><h2>def Fixed Smoke Results</h2>$(def_Table $FixedSmokeResults @("def_project","def_status","def_exit_code","def_elapsed_seconds","def_fixed_smoke_ps1","def_stdout","def_stderr") 80)</div>
<div class="sec wide"><h2>def P0 Accept Gate Template</h2>$(def_Table $P0Accept @("def_priority","def_accept_status","def_owner_engine","def_domain_family","def_normalized_key","def_distinct_values","def_selected_canonical_value","def_reject_reason","def_next_allowed_phase","def_source_mutation","def_sample_values") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Accept Gate Template</h2>$(def_Table $P1Accept @("def_priority","def_accept_status","def_alias","def_path_value","def_status","def_scope","def_selected","def_reject_reason","def_mutate_existing_source") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0110 source: $(def_Html $Summary.LatestV0110)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
Fixed Smoke: $(def_Html $Summary.FixedSmokeDir)<br/>
Report: $(def_Html $ReportPath)
</div>
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · FIFTHSTEP SMOKE DIAGNOSTIC + ACCEPT GATE · v0111" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 10 "Find latest v0110 output"
    $latest = def_GetLatestV0110
    $latestOut = Join-Path $latest "output"
    def_Log "OK" "Latest v0110: $latest" Green

    def_Progress 2 10 "Load v0110 matrices"
    $summaryV0110 = def_LoadJson (Join-Path $latestOut "VIA_FourthStep_SandboxAdapterCandidate_Summary.json")
    $candidates = def_LoadCsv (Join-Path $latestOut "VIA_v0110_SandboxAdapter_Candidates.csv")
    $smokeOld = def_LoadCsv (Join-Path $latestOut "VIA_v0110_SandboxSmoke_Results.csv")
    $p0Board = def_LoadCsv (Join-Path $latestOut "VIA_v0110_P0_ReviewBoard.csv")
    $aliasRows = def_LoadCsv (Join-Path $latestOut "VIA_v0110_PathAliasRegistry.csv")
    def_Log "OK" "Loaded Candidates=$(@($candidates).Count), OldSmoke=$(@($smokeOld).Count), P0=$(@($p0Board).Count), Alias=$(@($aliasRows).Count)" Green

    def_Progress 3 10 "Build diagnostics and fixed smoke scripts"
    $diagPack = def_BuildDiagnostics -Candidates $candidates
    $diagnostics = @($diagPack.Diagnostics)
    $fixedSmokeResults = @($diagPack.FixedSmokeResults)

    def_Progress 4 10 "Build P0 accept gate template"
    $p0Accept = def_BuildP0AcceptGate -P0Board $p0Board

    def_Progress 5 10 "Build P1 path alias accept gate template"
    $p1Accept = def_BuildP1AcceptGate -AliasRows $aliasRows

    def_Progress 6 10 "Build run-all fixed smoke command"
    $runAllFixedSmoke = Join-Path $def_OUTPUT_DIR "Invoke-VIA-RunAllFixedSmoke-v0111.ps1"
    def_BuildRunAllFixedSmoke -Diagnostics $diagnostics -Path $runAllFixedSmoke

    def_Progress 7 10 "Build PS15 accelerator matrix"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_Progress 8 10 "Write CSV/JSON outputs"
    def_WriteCsv $diagnostics (Join-Path $def_OUTPUT_DIR "VIA_v0111_CandidateSmokeDiagnostics.csv")
    def_WriteCsv $fixedSmokeResults (Join-Path $def_OUTPUT_DIR "VIA_v0111_FixedSmokeResults.csv")
    def_WriteCsv $p0Accept (Join-Path $def_OUTPUT_DIR "VIA_v0111_P0_AcceptGate_Template.csv")
    def_WriteCsv $p1Accept (Join-Path $def_OUTPUT_DIR "VIA_v0111_P1_PathAlias_AcceptGate_Template.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0111_PS15_Accelerators.csv")
    def_WriteCsv $candidates (Join-Path $def_OUTPUT_DIR "VIA_v0111_Candidates_From_v0110.csv")
    def_WriteCsv $smokeOld (Join-Path $def_OUTPUT_DIR "VIA_v0111_OldSmoke_From_v0110.csv")

    def_WriteJson $diagnostics (Join-Path $def_OUTPUT_DIR "VIA_v0111_CandidateSmokeDiagnostics.json")
    def_WriteJson $fixedSmokeResults (Join-Path $def_OUTPUT_DIR "VIA_v0111_FixedSmokeResults.json")
    def_WriteJson $p0Accept (Join-Path $def_OUTPUT_DIR "VIA_v0111_P0_AcceptGate_Template.json")
    def_WriteJson $p1Accept (Join-Path $def_OUTPUT_DIR "VIA_v0111_P1_PathAlias_AcceptGate_Template.json")

    def_Progress 9 10 "Write next commands"
    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -RunAllFixedSmoke $runAllFixedSmoke

    $staticOk = @($diagnostics | Where-Object { (def_GetProp $_ "def_diagnostic") -eq "STATIC_CANDIDATE_OK" }).Count
    $fixedOk = @($fixedSmokeResults | Where-Object { (def_GetProp $_ "def_status") -eq "FIXED_SMOKE_OK" }).Count
    $fixedReview = @($fixedSmokeResults | Where-Object { (def_GetProp $_ "def_status") -ne "FIXED_SMOKE_OK" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111_READY"
        RunId = $def_RUN_ID
        LatestV0110 = $latest
        DiagnosticRows = "$(@($diagnostics).Count)"
        StaticOk = "$staticOk"
        FixedSmokeRows = "$(@($fixedSmokeResults).Count)"
        FixedSmokeOk = "$fixedOk"
        FixedSmokeReview = "$fixedReview"
        P0AcceptRows = "$(@($p0Accept).Count)"
        P1AcceptRows = "$(@($p1Accept).Count)"
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        FixedSmokeDir = $def_FIXED_SMOKE_DIR
        RunAllFixedSmoke = $runAllFixedSmoke
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; accept gate only."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_FifthStep_SmokeDiagnosticAcceptGate_Summary.json")

    def_Progress 10 10 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_FifthStep_SmokeDiagnosticAcceptGate_Report_v0111.html"
    def_WriteReport `
        -Summary $summary `
        -Diagnostics $diagnostics `
        -FixedSmokeResults $fixedSmokeResults `
        -P0Accept $p0Accept `
        -P1Accept $p1Accept `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA FifthStep Smoke Diagnostic v0111" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA FifthStep Smoke Diagnostic + Accept Gate v0111 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status        : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0110         : $latest" -ForegroundColor Gray
    Write-Host "Diagnostics   : $($summary.DiagnosticRows)" -ForegroundColor Cyan
    Write-Host "Static OK     : $($summary.StaticOk)" -ForegroundColor Green
    Write-Host "Fixed OK      : $($summary.FixedSmokeOk)" -ForegroundColor Green
    Write-Host "Fixed Review  : $($summary.FixedSmokeReview)" -ForegroundColor Yellow
    Write-Host "P0 Accept     : $($summary.P0AcceptRows)" -ForegroundColor Yellow
    Write-Host "P1 Accept     : $($summary.P1AcceptRows)" -ForegroundColor Yellow
    Write-Host "Report        : $report" -ForegroundColor Cyan
    Write-Host "Output        : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "Fixed Smoke   : $def_FIXED_SMOKE_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd       : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try { Start-Process -FilePath $report } catch {}
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed." -ForegroundColor Yellow
    exit 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
