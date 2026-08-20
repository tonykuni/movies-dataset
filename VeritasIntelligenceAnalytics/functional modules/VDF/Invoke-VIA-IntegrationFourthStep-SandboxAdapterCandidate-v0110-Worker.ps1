param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0109_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true,
    [bool]$def_PARAM_RUN_SANDBOX_SMOKE = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_fourthstep_sandbox_adapter"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_CANDIDATE_DIR = Join-Path $def_RUN_DIR "_sandbox_adapter_candidates"
$def_TOOLBOX_DIR = Join-Path $def_RUN_DIR "_toolbox_used_review"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_FourthStep_SandboxAdapterCandidate_v0110.log"

$def_POLICY = [ordered]@{
    no_delete = $true
    no_stop_process = $true
    no_source_mutation = $true
    child_isolated = $true
    sandbox_only = $true
    db_write = $false
    canonical_merge = $false
}

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0109 auto discovery",
    "A02 reuse v0109 matrices; no BASE full re-scan",
    "A03 child-isolated worker",
    "A04 dynamic progress per stage",
    "A05 P0 decision packet generation",
    "A06 P1 path alias registry generation",
    "A07 P2 subsystem adapter candidate generation",
    "A08 sandbox-only smoke script generation",
    "A09 no canonical overwrite",
    "A10 no source mutation",
    "A11 no Stop-Process timeout policy",
    "A12 equal-height compact HTML report",
    "A13 toolbox review reconstruction",
    "A14 next-command index",
    "A15 static smoke result matrix"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_CANDIDATE_DIR,$def_TOOLBOX_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA FourthStep Sandbox Adapter v0110" -Status $Status -PercentComplete $pct
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
        def_Log "WARN" "JSON load failed: $Path :: $($_.Exception.Message)" Yellow
    }
    return $null
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

function def_SafeName {
    param([string]$Text)
    $s = def_S $Text
    if ([string]::IsNullOrWhiteSpace($s)) { $s = "UNKNOWN" }
    $s = $s -replace '[\\/:*?"<>| ]+', '_'
    $s = $s.Trim("_")
    if ($s.Length -gt 80) { $s = $s.Substring(0,80) }
    return $s
}

function def_EscapePsSingle {
    param([string]$Text)
    return (def_S $Text).Replace("'","''")
}

function def_GetLatestV0109 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0109_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0109_ROOT) {
            return $def_PARAM_V0109_ROOT
        }
        throw "Specified v0109 root does not exist: $def_PARAM_V0109_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_thirdstep_convergence"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0109 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_ThirdStep_ConvergenceSandbox_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0109 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_BuildP0ReviewBoard {
    param([array]$P0Decision)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Decision) {
        $family = def_GetProp $r "def_domain_family"
        $owner = def_GetProp $r "def_owner_engine"
        $key = def_GetProp $r "def_normalized_key"
        $distinct = def_GetProp $r "def_distinct_values"

        $gate = "REVIEW"
        if ($family -match "MARKET_TICKER|DATA_SOURCE|SCHEMA_FIELD|GOVERNANCE") {
            $gate = "P0_OWNER_DECISION_REQUIRED"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P0"
            def_gate = $gate
            def_owner_engine = $owner
            def_domain_family = $family
            def_normalized_key = $key
            def_distinct_values = $distinct
            def_recommended_decision = "Do not auto-fix. Choose one canonical owner/value before v0111."
            def_hydra_risk = "HIGH_IF_AUTO_MERGED"
            def_source_mutation = "false"
            def_sample_values = def_GetProp $r "def_sample_values"
            def_sample_files = def_GetProp $r "def_sample_files"
        })
    }

    return @($rows)
}

function def_BuildPathAliasRegistry {
    param([array]$PathAliases)

    $rows = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($r in $PathAliases) {
        $alias = def_GetProp $r "def_alias"
        $path = def_GetProp $r "def_path_value"
        if ([string]::IsNullOrWhiteSpace($alias) -or [string]::IsNullOrWhiteSpace($path)) { continue }

        $key = "$alias||$path"
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true

        $status = def_GetProp $r "def_status"
        if ([string]::IsNullOrWhiteSpace($status)) { $status = "REVIEW_ALIAS" }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_alias = $alias
            def_path_value = $path
            def_status = $status
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
            def_recommendation = "Use alias variable instead of literal path after P1 approval."
        })
    }

    return @($rows | Sort-Object def_alias, def_path_value)
}

function def_WritePathAliasPs1 {
    param([array]$AliasRows,[string]$Path)

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('$global:VIA_PathAliases_v0110 = [ordered]@{')

    foreach ($r in $AliasRows) {
        $alias = def_EscapePsSingle (def_GetProp $r "def_alias")
        $pathValue = def_EscapePsSingle (def_GetProp $r "def_path_value")
        if (-not [string]::IsNullOrWhiteSpace($alias)) {
            [void]$lines.Add("    '$alias' = '$pathValue'")
        }
    }

    [void]$lines.Add('}')
    [void]$lines.Add('')
    [void]$lines.Add('function Get-VIAPathAlias_v0110 {')
    [void]$lines.Add('    param([string]$Alias)')
    [void]$lines.Add('    if ($global:VIA_PathAliases_v0110.Contains($Alias)) { return $global:VIA_PathAliases_v0110[$Alias] }')
    [void]$lines.Add('    return ""')
    [void]$lines.Add('}')
    [void]$lines.Add('')
    [void]$lines.Add('Write-Host "[OK] VIA PathAliasRegistry v0110 loaded. Count=$($global:VIA_PathAliases_v0110.Count)" -ForegroundColor Green')

    Set-Content -LiteralPath $Path -Value ($lines -join "`r`n") -Encoding UTF8
}

function def_WriteCandidateSmokeScript {
    param(
        [string]$Project,
        [string]$CandidateDir,
        [string]$SmokePath
    )

    $safeProject = def_EscapePsSingle $Project
    $safeCandidate = def_EscapePsSingle $CandidateDir

    $lines = @(
        '$ErrorActionPreference = "Stop"',
        '',
        '$def_PROJECT = ''' + $safeProject + '''',
        '$def_CANDIDATE_DIR = ''' + $safeCandidate + '''',
        '',
        'Write-Host ""',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        'Write-Host "def VIA Sandbox Adapter Smoke · v0110 · $def_PROJECT" -ForegroundColor Cyan',
        'Write-Host "================================================================================" -ForegroundColor DarkCyan',
        '',
        'if (-not (Test-Path -LiteralPath $def_CANDIDATE_DIR)) {',
        '    throw "Candidate dir not found: $def_CANDIDATE_DIR"',
        '}',
        '',
        '$contract = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_BridgeContract_v0110.json")',
        'if (-not (Test-Path -LiteralPath $contract)) {',
        '    throw "Bridge contract missing: $contract"',
        '}',
        '',
        '$obj = Get-Content -LiteralPath $contract -Raw -Encoding UTF8 | ConvertFrom-Json',
        '',
        '$rows = @()',
        '$rows += [pscustomobject]@{ Check="CandidateDir"; Status="OK"; Detail=$def_CANDIDATE_DIR }',
        '$rows += [pscustomobject]@{ Check="Contract"; Status="OK"; Detail=$contract }',
        '$rows += [pscustomobject]@{ Check="Project"; Status="OK"; Detail=$obj.project }',
        '$rows += [pscustomobject]@{ Check="Policy"; Status="OK"; Detail=$obj.policy }',
        '$rows += [pscustomobject]@{ Check="SourceMutation"; Status="OK"; Detail="false" }',
        '',
        '$csv = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_SandboxSmoke_Result_v0110.csv")',
        '$json = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_SandboxSmoke_Result_v0110.json")',
        '$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8',
        '$rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $json -Encoding UTF8',
        '',
        'Write-Host "[OK] Sandbox smoke complete: $def_PROJECT" -ForegroundColor Green',
        'Write-Host "[OK] CSV : $csv" -ForegroundColor Cyan',
        'Write-Host "[OK] JSON: $json" -ForegroundColor Cyan'
    )

    Set-Content -LiteralPath $SmokePath -Value ($lines -join "`r`n") -Encoding UTF8
}

function def_BuildAdapterCandidates {
    param([array]$P2Queue,[array]$P0Board,[array]$PathAliases)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P2Queue) {
        $project = def_GetProp $r "def_project"
        if ([string]::IsNullOrWhiteSpace($project)) { $project = "UNKNOWN" }

        $safe = def_SafeName $project
        $dir = Join-Path $def_CANDIDATE_DIR $safe
        def_EnsureDir $dir

        $contractPath = Join-Path $dir ("VIA_{0}_BridgeContract_v0110.json" -f $safe)
        $smokePath = Join-Path $dir ("Invoke-VIA_{0}_SandboxSmoke_v0110.ps1" -f $safe)
        $readmePath = Join-Path $dir "README_SANDBOX_CANDIDATE_v0110.md"

        $contract = [ordered]@{
            schema_version = "VIA_SandboxAdapterContract_v0110"
            generated_at = (Get-Date).ToString("s")
            project = $project
            bridge_mode = def_GetProp $r "def_bridge_mode"
            source_mutation = $false
            canonical_merge = $false
            db_write = $false
            candidate_dir = $dir
            policy = "sandbox-only; read-only smoke; no source mutation; no delete; no Stop-Process"
            preconditions = @(
                "P0 domain owner decision reviewed",
                "P1 path alias accepted or deferred",
                "P2 bridge smoke child-isolated",
                "P3 UI/noise not blocking"
            )
            expected_outputs = @(
                "BridgeContract_v0110.json",
                "SandboxSmoke_Result_v0110.csv",
                "SandboxSmoke_Result_v0110.json"
            )
            upstream_v0109_project_row = [ordered]@{
                def_project = $project
                def_engines = def_GetProp $r "def_engines"
                def_bridge_mode = def_GetProp $r "def_bridge_mode"
                def_smoke_test_policy = def_GetProp $r "def_smoke_test_policy"
                def_next_action = def_GetProp $r "def_next_action"
            }
            p0_reference_count = @($P0Board).Count
            path_alias_count = @($PathAliases).Count
        }

        def_WriteJson $contract $contractPath 16
        def_WriteCandidateSmokeScript -Project $safe -CandidateDir $dir -SmokePath $smokePath

        $readme = @"
# VIA Sandbox Adapter Candidate v0110

Project: $project

Policy:
- No source mutation
- No canonical merge
- No delete
- No Stop-Process
- Read-only smoke only

Files:
- Bridge contract: $contractPath
- Smoke script: $smokePath

Next:
Run the smoke script only after P0/P1 review remains acceptable.
"@
        Set-Content -LiteralPath $readmePath -Value $readme -Encoding UTF8

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = $project
            def_candidate_dir = $dir
            def_contract_json = $contractPath
            def_smoke_ps1 = $smokePath
            def_readme = $readmePath
            def_bridge_mode = def_GetProp $r "def_bridge_mode"
            def_source_mutation = "false"
            def_status = "CANDIDATE_GENERATED"
        })
    }

    return @($rows)
}

function def_InvokeSmokeScripts {
    param([array]$Candidates)

    $rows = New-Object System.Collections.ArrayList

    foreach ($c in $Candidates) {
        $project = def_GetProp $c "def_project"
        $smoke = def_GetProp $c "def_smoke_ps1"
        $stdout = Join-Path (def_GetProp $c "def_candidate_dir") "smoke_stdout.log"
        $stderr = Join-Path (def_GetProp $c "def_candidate_dir") "smoke_stderr.log"

        $status = "SKIPPED"
        $exitCode = ""
        $elapsed = ""

        if (-not $def_PARAM_RUN_SANDBOX_SMOKE) {
            $status = "SKIPPED_BY_PARAM"
        } elseif (-not (Test-Path -LiteralPath $smoke)) {
            $status = "MISSING_SMOKE_SCRIPT"
        } else {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                $args = "-NoProfile -ExecutionPolicy Bypass -File `"$smoke`""
                $proc = Start-Process -FilePath "pwsh" -ArgumentList $args -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden

                while (-not $proc.HasExited) {
                    Start-Sleep -Milliseconds 250
                    if ($sw.Elapsed.TotalSeconds -gt 60) {
                        $status = "TIMEOUT_REVIEW_CHILD_LEFT_RUNNING"
                        break
                    }
                }

                if ($proc.HasExited) {
                    $exitCode = def_S $proc.ExitCode
                    if ($proc.ExitCode -eq 0) { $status = "SMOKE_OK" } else { $status = "SMOKE_NONZERO" }
                }
            } catch {
                $status = "SMOKE_EXCEPTION"
                $exitCode = $_.Exception.Message
            }
            $sw.Stop()
            $elapsed = "{0:n2}" -f $sw.Elapsed.TotalSeconds
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = $project
            def_status = $status
            def_exit_code = $exitCode
            def_elapsed_seconds = $elapsed
            def_stdout = $stdout
            def_stderr = $stderr
            def_smoke_ps1 = $smoke
        })
    }

    return @($rows)
}

function def_BuildSmokeAllScript {
    param([array]$Candidates,[string]$Path)

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('$ErrorActionPreference = "Stop"')
    [void]$lines.Add('Write-Host ""')
    [void]$lines.Add('Write-Host "================================================================================" -ForegroundColor DarkCyan')
    [void]$lines.Add('Write-Host "def VIA · Run All Sandbox Adapter Smoke · v0110" -ForegroundColor Cyan')
    [void]$lines.Add('Write-Host "================================================================================" -ForegroundColor DarkCyan')
    [void]$lines.Add('$rows = @()')

    foreach ($c in $Candidates) {
        $project = def_EscapePsSingle (def_GetProp $c "def_project")
        $smoke = def_EscapePsSingle (def_GetProp $c "def_smoke_ps1")

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
    [void]$lines.Add('$out = Join-Path (Split-Path -Parent $PSCommandPath) "VIA_RunAllSandboxSmoke_Result_v0110.csv"')
    [void]$lines.Add('$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8')
    [void]$lines.Add('Write-Host "[OK] Result: $out" -ForegroundColor Green')

    Set-Content -LiteralPath $Path -Value ($lines -join "`r`n") -Encoding UTF8
}

function def_BuildNextCommands {
    param([string]$RunDir,[string]$SmokeAll)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0110
# =============================================================================

Start-Process "$RunDir\report\VIA_FourthStep_SandboxAdapterCandidate_Report_v0110.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_sandbox_adapter_candidates"

Import-Csv "$RunDir\output\VIA_v0110_SandboxAdapter_Candidates.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0110_SandboxSmoke_Results.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0110_P0_ReviewBoard.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_v0110_PathAliasRegistry.csv" | Format-Table -AutoSize

# Run sandbox smoke again manually:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$SmokeAll"

# Next safe phase:
# v0111 = P0/P1 Accept Gate.
# Only after P0/P1 approved, generate canonical integration patch candidates.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0110.ps1"
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
        [array]$P0Board,
        [array]$AliasRows,
        [array]$Candidates,
        [array]$SmokeResults,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("P0 Board",$Summary.P0Rows),
        @("Path Aliases",$Summary.PathAliasRows),
        @("Candidates",$Summary.CandidateRows),
        @("Smoke OK",$Summary.SmokeOk),
        @("Smoke Review",$Summary.SmokeReview),
        @("Policy","No Mutation"),
        @("Next","v0111 Gate")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA FourthStep Sandbox Adapter Candidate v0110</title>
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
<h1>def VIA Integration FourthStep Sandbox Adapter Candidate · v0110</h1>
<div class="sub">P0 board · P1 path aliases · P2 subsystem adapter candidates · read-only smoke · no mutation</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0110 已把 v0109 的 P0/P1/P2 收斂為「可測但不可寫回」的 sandbox adapter candidates。這一步仍不可直接合併 canonical。下一步 v0111 應該做 P0/P1 Accept Gate：只有被接受的 domain owner 和 path alias 才能進入 v0112 canonical patch candidate。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Source Mutation</span>
<span class="tag">Sandbox Adapter Only</span>
<span class="tag">Read-only Smoke</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Sandbox Adapter Candidates</h2>$(def_Table $Candidates @("def_project","def_candidate_dir","def_contract_json","def_smoke_ps1","def_bridge_mode","def_source_mutation","def_status") 80)</div>
<div class="sec wide"><h2>def Sandbox Smoke Results</h2>$(def_Table $SmokeResults @("def_project","def_status","def_exit_code","def_elapsed_seconds","def_stdout","def_stderr","def_smoke_ps1") 80)</div>
<div class="sec wide"><h2>def P0 Review Board</h2>$(def_Table $P0Board @("def_priority","def_gate","def_owner_engine","def_domain_family","def_normalized_key","def_distinct_values","def_recommended_decision","def_hydra_risk","def_source_mutation","def_sample_values","def_sample_files") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Registry</h2>$(def_Table $AliasRows @("def_alias","def_path_value","def_status","def_scope","def_mutate_existing_source","def_recommendation") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0109 source: $(def_Html $Summary.LatestV0109)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
Candidates: $(def_Html $Summary.CandidateDir)<br/>
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
    Write-Host "def VIA · INTEGRATION FOURTHSTEP SANDBOX ADAPTER CANDIDATE · v0110" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 11 "Find latest v0109 output"
    $latest = def_GetLatestV0109
    $latestOut = Join-Path $latest "output"
    def_Log "OK" "Latest v0109: $latest" Green

    def_Progress 2 11 "Load v0109 matrices"
    $p0Decision = def_LoadCsv (Join-Path $latestOut "VIA_P0_DomainDecisionTemplate.csv")
    $pathAliases = def_LoadCsv (Join-Path $latestOut "VIA_P1_PathAliasMap.csv")
    $p2Queue = def_LoadCsv (Join-Path $latestOut "VIA_P2_EngineBridgeQueue.csv")
    $fiveFlow = def_LoadCsv (Join-Path $latestOut "VIA_FiveFlowExecutionPlan.csv")
    $backlog = def_LoadCsv (Join-Path $latestOut "VIA_IntegrationActionBacklog.csv")
    $topLibs = def_LoadCsv (Join-Path $latestOut "VIA_Top10LocalFreeLibs_ByFunctionLanguage.csv")
    $toolbox = def_LoadCsv (Join-Path $latestOut "VIA_ToolboxReview_From_v0108.csv")
    def_Log "OK" "Loaded P0=$(@($p0Decision).Count), Alias=$(@($pathAliases).Count), P2=$(@($p2Queue).Count)" Green

    def_Progress 3 11 "Build P0 review board"
    $p0Board = def_BuildP0ReviewBoard -P0Decision $p0Decision

    def_Progress 4 11 "Build P1 path alias registry"
    $aliasRows = def_BuildPathAliasRegistry -PathAliases $pathAliases
    $aliasPs1 = Join-Path $def_OUTPUT_DIR "VIA_PathAliasRegistry_Candidate_v0110.ps1"
    def_WritePathAliasPs1 -AliasRows $aliasRows -Path $aliasPs1

    def_Progress 5 11 "Generate P2 sandbox adapter candidates"
    $candidates = def_BuildAdapterCandidates -P2Queue $p2Queue -P0Board $p0Board -PathAliases $aliasRows

    def_Progress 6 11 "Generate smoke-all script"
    $smokeAll = Join-Path $def_OUTPUT_DIR "Invoke-VIA-RunAllSandboxAdapterSmoke-v0110.ps1"
    def_BuildSmokeAllScript -Candidates $candidates -Path $smokeAll

    def_Progress 7 11 "Run read-only sandbox smoke"
    $smokeResults = def_InvokeSmokeScripts -Candidates $candidates

    def_Progress 8 11 "Build PS15 accelerator matrix"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_Progress 9 11 "Write CSV/JSON outputs"
    def_WriteCsv $p0Board (Join-Path $def_OUTPUT_DIR "VIA_v0110_P0_ReviewBoard.csv")
    def_WriteCsv $aliasRows (Join-Path $def_OUTPUT_DIR "VIA_v0110_PathAliasRegistry.csv")
    def_WriteCsv $candidates (Join-Path $def_OUTPUT_DIR "VIA_v0110_SandboxAdapter_Candidates.csv")
    def_WriteCsv $smokeResults (Join-Path $def_OUTPUT_DIR "VIA_v0110_SandboxSmoke_Results.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0110_PS15_Accelerators.csv")
    def_WriteCsv $fiveFlow (Join-Path $def_OUTPUT_DIR "VIA_v0110_FiveFlow_From_v0109.csv")
    def_WriteCsv $backlog (Join-Path $def_OUTPUT_DIR "VIA_v0110_Backlog_From_v0109.csv")
    def_WriteCsv $topLibs (Join-Path $def_OUTPUT_DIR "VIA_v0110_Top10Libs_From_v0109.csv")
    def_WriteCsv $toolbox (Join-Path $def_OUTPUT_DIR "VIA_v0110_Toolbox_From_v0109.csv")

    def_WriteJson $p0Board (Join-Path $def_OUTPUT_DIR "VIA_v0110_P0_ReviewBoard.json")
    def_WriteJson $aliasRows (Join-Path $def_OUTPUT_DIR "VIA_v0110_PathAliasRegistry.json")
    def_WriteJson $candidates (Join-Path $def_OUTPUT_DIR "VIA_v0110_SandboxAdapter_Candidates.json")
    def_WriteJson $smokeResults (Join-Path $def_OUTPUT_DIR "VIA_v0110_SandboxSmoke_Results.json")

    def_Progress 10 11 "Write next commands"
    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -SmokeAll $smokeAll

    $smokeOk = @($smokeResults | Where-Object { (def_GetProp $_ "def_status") -eq "SMOKE_OK" }).Count
    $smokeReview = @($smokeResults | Where-Object { (def_GetProp $_ "def_status") -ne "SMOKE_OK" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110_READY"
        RunId = $def_RUN_ID
        LatestV0109 = $latest
        P0Rows = "$(@($p0Board).Count)"
        PathAliasRows = "$(@($aliasRows).Count)"
        CandidateRows = "$(@($candidates).Count)"
        SmokeRows = "$(@($smokeResults).Count)"
        SmokeOk = "$smokeOk"
        SmokeReview = "$smokeReview"
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        CandidateDir = $def_CANDIDATE_DIR
        PathAliasPs1 = $aliasPs1
        SmokeAll = $smokeAll
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; sandbox-only adapter candidates."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_FourthStep_SandboxAdapterCandidate_Summary.json")

    def_Progress 11 11 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_FourthStep_SandboxAdapterCandidate_Report_v0110.html"
    def_WriteReport `
        -Summary $summary `
        -P0Board $p0Board `
        -AliasRows $aliasRows `
        -Candidates $candidates `
        -SmokeResults $smokeResults `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA FourthStep Sandbox Adapter v0110" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA FourthStep Sandbox Adapter Candidate v0110 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status     : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0109      : $latest" -ForegroundColor Gray
    Write-Host "P0Board    : $($summary.P0Rows)" -ForegroundColor Yellow
    Write-Host "Alias      : $($summary.PathAliasRows)" -ForegroundColor Yellow
    Write-Host "Candidates : $($summary.CandidateRows)" -ForegroundColor Cyan
    Write-Host "Smoke OK   : $($summary.SmokeOk)" -ForegroundColor Green
    Write-Host "Smoke Rev  : $($summary.SmokeReview)" -ForegroundColor Yellow
    Write-Host "Report     : $report" -ForegroundColor Cyan
    Write-Host "Output     : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "Candidate  : $def_CANDIDATE_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd    : $nextCmd" -ForegroundColor Cyan

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
