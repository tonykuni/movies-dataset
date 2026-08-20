param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0106_ROOT = "",
    [switch]$def_PARAM_OPEN_HTML_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0107" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_secondstep_closeout"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_TOOLBOX_DIR = Join-Path $def_RUN_DIR "_toolbox_used"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_SecondStep_CloseoutPlanner_v0107.log"

$def_PS15_ACCELERATORS = @(
    "A01 Latest v0106 output auto-detection",
    "A02 CSV-only lightweight load; no full source re-scan",
    "A03 Child-isolated launcher",
    "A04 Dynamic Write-Progress every major stage",
    "A05 Read-only plan generation",
    "A06 No delete / no cleanup mutation",
    "A07 No Stop-Process",
    "A08 Five independent flow separation",
    "A09 P0/P1/P2/P3 conflict triage",
    "A10 Subsystem-level integration matrix",
    "A11 Used-toolbox folder reconstruction",
    "A12 Next command index generation",
    "A13 One-page compact professional HTML UI",
    "A14 CSV + JSON + HTML synchronized output",
    "A15 Hydra-risk guard: parallel-safe vs sequential-required split"
)

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_TOOLBOX_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA SecondStep Closeout Planner v0107" -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
}

function def_Html {
    param([string]$Text)
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
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
        [PSCustomObject]@{ def_empty = "true" } | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function def_WriteJson {
    param($Object,[string]$Path,[int]$Depth = 10)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_GetLatestV0106 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0106_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0106_ROOT) {
            return $def_PARAM_V0106_ROOT
        }
        throw "Specified v0106 root does not exist: $def_PARAM_V0106_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_firststep_panorama"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0106 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_IntegrationFirstStep_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0106 worker output found under: $root"
    }

    return $candidates[0].FullName
}

function def_CountBy {
    param([array]$Rows,[string]$Property)
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($g in ($Rows | Group-Object $Property | Sort-Object Count -Descending)) {
        $out.Add([PSCustomObject]([ordered]@{
            def_name = [string]$g.Name
            def_count = [string]$g.Count
        }))
    }
    return @($out)
}

function def_BuildSubsystemPlan {
    param([array]$FileRows,[array]$EngineRows,[array]$ConflictRows)

    $out = New-Object System.Collections.Generic.List[object]
    $projects = @($FileRows | ForEach-Object { $_.def_project } | Where-Object { $_ } | Select-Object -Unique | Sort-Object)

    foreach ($p in $projects) {
        $fr = @($FileRows | Where-Object { $_.def_project -eq $p })
        $er = @($EngineRows | Where-Object { $_.def_project -eq $p })
        $p0 = @($ConflictRows | Where-Object { $_.def_severity -eq "P0_DOMAIN_REVIEW" -and $_.def_sample_files -match $p }).Count
        $p1 = @($ConflictRows | Where-Object { $_.def_severity -eq "P1_PATH_REVIEW" -and $_.def_sample_files -match $p }).Count
        $zero = @($fr | Where-Object { $_.def_status -match "ZERO|TINY" }).Count
        $ui = @($fr | Where-Object { $_.def_file_role -eq "UI_VISUAL" }).Count
        $reg = @($fr | Where-Object { $_.def_file_role -eq "REGISTRY" }).Count
        $test = @($fr | Where-Object { $_.def_file_role -eq "TEST_VALIDATION" }).Count

        $lane = "SCAN_ONLY"
        $risk = "LOW"
        $next = "Keep read-only. Build bridge plan."

        if ($p -eq "UNKNOWN") {
            $lane = "CLASSIFICATION_LANE"
            $risk = "MEDIUM"
            $next = "Classify UNKNOWN files before integration."
        } elseif ($p0 -gt 0) {
            $lane = "SEQUENTIAL_DOMAIN_REVIEW"
            $risk = "HIGH_REVIEW"
            $next = "Resolve P0 domain parameters before any write integration."
        } elseif ($p1 -gt 0) {
            $lane = "PATH_ALIAS_REVIEW"
            $risk = "MEDIUM"
            $next = "Normalize path aliases and active root mapping."
        } elseif (@($er).Count -gt 0) {
            $lane = "PARALLEL_ENGINE_BRIDGE"
            $risk = "MEDIUM_LOW"
            $next = "Create adapter bridge and smoke-test independently."
        }

        $out.Add([PSCustomObject]([ordered]@{
            def_project = [string]$p
            def_files = [string]@($fr).Count
            def_engines = [string]@($er).Count
            def_ui_files = [string]$ui
            def_registry_files = [string]$reg
            def_test_files = [string]$test
            def_zero_or_tiny_review = [string]$zero
            def_p0_domain_review = [string]$p0
            def_p1_path_review = [string]$p1
            def_parallel_lane = [string]$lane
            def_hydra_risk = [string]$risk
            def_next_action = [string]$next
        }))
    }

    return @($out)
}

function def_BuildFiveFlowPlan {
    param([array]$SubsystemPlan)

    return @(
        [PSCustomObject]([ordered]@{
            def_flow = "FLOW_01_SUPPORTIVE_TOOLS"
            def_scope = "SafePolyglot / NexusCore / PolyglotCheck / EnvManager / Aegis / Celeritas"
            def_input = "UsedTools_Staged + Supportive module scan"
            def_output = "supportive_toolbox_index + parameter bridge"
            def_parallel_policy = "Parallel-safe for scan; sequential for repair"
            def_next_action = "Build active pointer and invocation contract; do not execute repair yet"
        }),
        [PSCustomObject]([ordered]@{
            def_flow = "FLOW_02_FUNCTIONAL_MODULES"
            def_scope = "UnifiedSpec / CodexNexus / GovernanceRegistry / LayoutRegistry / VisualRegistry"
            def_input = "functional modules registry"
            def_output = "functional_contract_matrix"
            def_parallel_policy = "Read-only parallel scan"
            def_next_action = "Verify schema owners and registry consistency"
        }),
        [PSCustomObject]([ordered]@{
            def_flow = "FLOW_03_PARAMETERS_SSOT"
            def_scope = "Canonical parameter registry / P0/P1/P2/P3 split"
            def_input = "VIA_ParametersConsolidated_Registry + ConflictTriage"
            def_output = "SSOT candidate map + review queue"
            def_parallel_policy = "P3 noise parallel; P0 sequential"
            def_next_action = "Freeze P0 domain decisions before code mutation"
        }),
        [PSCustomObject]([ordered]@{
            def_flow = "FLOW_04_ENGINE_BRIDGE"
            def_scope = "VDF / VRN / VIA / VEF / VPF / VIS / VPL"
            def_input = "EngineMatrix"
            def_output = "engine_adapter_bridge_plan"
            def_parallel_policy = "Independent subsystem smoke tests only"
            def_next_action = "Create adapter shims, not direct canonical merge"
        }),
        [PSCustomObject]([ordered]@{
            def_flow = "FLOW_05_UI_CLOSEOUT"
            def_scope = "One Interface / VisualLock / HTML reports"
            def_input = "UI files + VisualRegistry + LayoutRegistry"
            def_output = "compact one-page matrix UI"
            def_parallel_policy = "Safe after data contract stable"
            def_next_action = "Apply small-font equal-height UI only after SSOT review"
        })
    )
}

function def_BuildSequentialCloseoutPlan {
    return @(
        [PSCustomObject]([ordered]@{ def_order="00"; def_stage="Evidence Freeze"; def_mode="READ_ONLY"; def_goal="Keep v0106/v0107 outputs as evidence"; def_hydra_guard="No mutation" }),
        [PSCustomObject]([ordered]@{ def_order="01"; def_stage="P0 Domain Review"; def_mode="SEQUENTIAL"; def_goal="Resolve ticker/schema/source/policy conflicts"; def_hydra_guard="One owner per key" }),
        [PSCustomObject]([ordered]@{ def_order="02"; def_stage="P1 Path Alias Review"; def_mode="SEQUENTIAL"; def_goal="Normalize Downloads/OneDrive/functional/supportive roots"; def_hydra_guard="No direct file move" }),
        [PSCustomObject]([ordered]@{ def_order="03"; def_stage="P2 Engine Bridge"; def_mode="PARALLEL_SAFE_SMOKE"; def_goal="Adapter bridge for each engine"; def_hydra_guard="Child isolated" }),
        [PSCustomObject]([ordered]@{ def_order="04"; def_stage="P3 UI/Noise Suppression"; def_mode="PARALLEL"; def_goal="Hide false conflicts from HTML/CSS/import/heading"; def_hydra_guard="No source rewrite" }),
        [PSCustomObject]([ordered]@{ def_order="05"; def_stage="First Safe Patch Candidate"; def_mode="SANDBOX_ONLY"; def_goal="Generate patch candidate in sandbox folder"; def_hydra_guard="No canonical overwrite" }),
        [PSCustomObject]([ordered]@{ def_order="06"; def_stage="User Test Gate"; def_mode="MANUAL_CONFIRM"; def_goal="Open report and verify matrix"; def_hydra_guard="Human confirmation before repair" })
    )
}

function def_BuildToolbox {
    param([array]$ToolRows)

    $out = New-Object System.Collections.Generic.List[object]

    foreach ($t in $ToolRows) {
        $src = [string]$t.def_staged_path
        $cat = [string]$t.def_category
        $leaf = [string]$t.def_file

        $catDir = Join-Path $def_TOOLBOX_DIR $cat
        def_EnsureDir $catDir

        $dst = Join-Path $catDir $leaf
        $copyStatus = "SKIPPED_NOT_STAGED"

        if (-not [string]::IsNullOrWhiteSpace($src) -and (Test-Path -LiteralPath $src)) {
            try {
                Copy-Item -LiteralPath $src -Destination $dst -Force
                $copyStatus = "COPIED_FROM_V0106_STAGED"
            } catch {
                $copyStatus = "COPY_WARN: " + $_.Exception.Message
            }
        }

        $out.Add([PSCustomObject]([ordered]@{
            def_category = [string]$cat
            def_file = [string]$leaf
            def_original_source_path = [string]$t.def_source_path
            def_v0106_staged_path = [string]$src
            def_v0107_toolbox_path = [string]$dst
            def_status = [string]$copyStatus
            def_role = [string]$t.def_status
            def_sha12 = [string]$t.def_sha12
        }))
    }

    return @($out)
}

function def_BuildNextCommands {
    param([string]$LatestV0106,[string]$RunDir)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0107
# =============================================================================

# 1. Open v0107 report
Start-Process "$RunDir\report\VIA_SecondStep_CloseoutPlanner_Report_v0107.html"

# 2. Open v0107 output folder
Start-Process "$RunDir\output"

# 3. Open v0107 toolbox folder
Start-Process "$RunDir\_toolbox_used"

# 4. Open latest v0106 report
Start-Process "$LatestV0106\report\VIA_IntegrationFirstStep_Panorama_Report_v0106.html"

# 5. Review P0 domain conflicts first
Import-Csv "$RunDir\output\VIA_P0_DomainReview.csv" | Select-Object -First 30 | Format-Table -AutoSize

# 6. Review P1 path conflicts second
Import-Csv "$RunDir\output\VIA_P1_PathReview.csv" | Select-Object -First 30 | Format-Table -AutoSize

# 7. Review subsystem plan
Import-Csv "$RunDir\output\VIA_SubsystemIntegrationPlan.csv" | Format-Table -AutoSize

# Policy reminder:
# No delete. No Stop-Process. No canonical overwrite. No source mutation before P0/P1 review.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0107.ps1"
    Set-Content -LiteralPath $path -Value $cmd -Encoding UTF8
    return $path
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=160)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) {
        [void]$sb.Append("<th>$(def_Html $c)</th>")
    }
    [void]$sb.Append("</tr></thead><tbody>")

    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = ""
            try { $v = [string]$r.$c } catch {}
            if ($v.Length -gt 220) { $v = $v.Substring(0,220) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_Report {
    param(
        $Summary,
        [array]$P0,
        [array]$P1,
        [array]$P2,
        [array]$P3,
        [array]$SubsystemPlan,
        [array]$FiveFlowPlan,
        [array]$SequentialPlan,
        [array]$ToolboxIndex,
        [array]$ProjectCounts,
        [array]$RoleCounts,
        [array]$EngineRows,
        [array]$PS15,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("v0106 Files",$Summary.V0106Files),
        @("v0106 Parameters",$Summary.V0106Parameters),
        @("Engines",$Summary.Engines),
        @("P0 Domain",$Summary.P0Domain),
        @("P1 Path",$Summary.P1Path),
        @("P2 Engine",$Summary.P2Engine),
        @("P3 Noise/UI",$Summary.P3Noise)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html ([string]$x[1]))</div></div>"
    }

    $accRows = New-Object System.Collections.Generic.List[object]
    for ($i=0; $i -lt $PS15.Count; $i++) {
        $accRows.Add([PSCustomObject]([ordered]@{
            def_no = [string]($i+1)
            def_accelerator = [string]$PS15[$i]
        }))
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA SecondStep Closeout Planner v0107</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0;--cyan:#6fa8ad}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 10% 6%,rgba(111,168,173,.16),transparent 26%),linear-gradient(135deg,rgba(255,255,255,.4),rgba(230,226,216,.22)),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:9.2px;line-height:1.36}
.wrap{max-width:1720px;margin:0 auto;padding:16px}
h1{font-size:15.5px;margin:0 0 4px;font-weight:650;letter-spacing:.01em}
.sub{font-size:9px;color:var(--mut);margin-bottom:11px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:rgba(255,254,250,.92);border:1px solid var(--line);border-radius:9px;padding:6px 7px;min-height:46px}
.k{font-size:8px;color:var(--mut)}
.v{font:650 12px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-items:stretch}
.sec{background:rgba(255,254,250,.88);border:1px solid var(--line);border-radius:11px;padding:8px;min-height:235px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:10px;margin:0 0 6px;font-weight:650}
.note{font-size:8.8px;color:var(--mut);margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:8.35px}
th,td{border-bottom:1px solid #ebe8df;padding:3.2px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:var(--mut)}
.footer{margin-top:11px;color:var(--mut);font-size:8.5px}
@media(max-width:1100px){.cards{grid-template-columns:repeat(4,1fr)}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA Integration SecondStep Closeout Planner · v0107</h1>
<div class="sub">Five independent flows · P0/P1/P2/P3 triage · subsystem plan · toolbox index · next commands · no source mutation</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0106 已完成 8000-file 第一輪全景掃描。v0107 的判斷是：目前不可直接進入自動修正；應先把 P0 domain review 與 P1 path review 分離，P2 engine bridge 可子流程平行煙測，P3 UI/CSS/import/heading 多數視為 noise/reference，不應干擾主線。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Canonical Overwrite</span>
<span class="tag">Child Isolated</span>
<span class="tag">Three-Round Ready</span>
</div>
</div>

<div class="grid">
<div class="sec"><h2>def Five Independent Flows</h2>$(def_Table $FiveFlowPlan @("def_flow","def_scope","def_input","def_output","def_parallel_policy","def_next_action") 20)</div>
<div class="sec"><h2>def Sequential Closeout Plan</h2>$(def_Table $SequentialPlan @("def_order","def_stage","def_mode","def_goal","def_hydra_guard") 20)</div>
<div class="sec"><h2>def Project Counts</h2>$(def_Table $ProjectCounts @("def_name","def_count") 40)</div>
<div class="sec"><h2>def File Role Counts</h2>$(def_Table $RoleCounts @("def_name","def_count") 40)</div>
<div class="sec wide"><h2>def Subsystem Integration Plan</h2>$(def_Table $SubsystemPlan @("def_project","def_files","def_engines","def_ui_files","def_registry_files","def_test_files","def_zero_or_tiny_review","def_p0_domain_review","def_p1_path_review","def_parallel_lane","def_hydra_risk","def_next_action") 80)</div>
<div class="sec wide"><h2>def P0 Domain Review</h2>$(def_Table $P0 @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") 160)</div>
<div class="sec wide"><h2>def P1 Path Review</h2>$(def_Table $P1 @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") 160)</div>
<div class="sec wide"><h2>def P2 Engine Review</h2>$(def_Table $P2 @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") 160)</div>
<div class="sec wide"><h2>def P3 UI / Noise Reference</h2>$(def_Table $P3 @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") 160)</div>
<div class="sec wide"><h2>def Engine Matrix</h2>$(def_Table $EngineRows @("def_project","def_engine_file","def_file_role","def_engine_param_count","def_total_param_count","def_path") 220)</div>
<div class="sec wide"><h2>def Used Toolbox Index</h2>$(def_Table $ToolboxIndex @("def_category","def_file","def_status","def_role","def_sha12","def_v0107_toolbox_path","def_original_source_path") 160)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $accRows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0106 source: $(def_Html $Summary.LatestV0106)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
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
    Write-Host "def VIA · INTEGRATION SECONDSTEP CLOSEOUT PLANNER · v0107" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 10 "Find latest v0106 output"
    $latest = def_GetLatestV0106
    $latestOut = Join-Path $latest "output"

    $summaryPath = Join-Path $latestOut "VIA_IntegrationFirstStep_Summary.json"
    $fileCsv = Join-Path $latestOut "VIA_FileMatrix.csv"
    $engineCsv = Join-Path $latestOut "VIA_EngineMatrix.csv"
    $conflictCsv = Join-Path $latestOut "VIA_ConflictTriageMatrix.csv"
    $toolCsv = Join-Path $latestOut "VIA_UsedTools_Staged.csv"

    def_Log "OK" "Latest v0106: $latest" Green

    def_Progress 2 10 "Load v0106 matrices"
    $v0106Summary = def_LoadJson $summaryPath
    $fileRows = def_LoadCsv $fileCsv
    $engineRows = def_LoadCsv $engineCsv
    $conflictRows = def_LoadCsv $conflictCsv
    $toolRows = def_LoadCsv $toolCsv

    def_Log "OK" "Loaded FileRows=$(@($fileRows).Count), EngineRows=$(@($engineRows).Count), ConflictRows=$(@($conflictRows).Count), ToolRows=$(@($toolRows).Count)" Green

    def_Progress 3 10 "Split P0/P1/P2/P3 conflict queues"
    $p0 = @($conflictRows | Where-Object { $_.def_severity -eq "P0_DOMAIN_REVIEW" })
    $p1 = @($conflictRows | Where-Object { $_.def_severity -eq "P1_PATH_REVIEW" })
    $p2 = @($conflictRows | Where-Object { $_.def_severity -eq "P2_ENGINE_REVIEW" })
    $p3 = @($conflictRows | Where-Object { $_.def_severity -match "P3" })

    def_Progress 4 10 "Build subsystem integration plan"
    $subsystemPlan = def_BuildSubsystemPlan -FileRows $fileRows -EngineRows $engineRows -ConflictRows $conflictRows

    def_Progress 5 10 "Build five-flow and sequential closeout plan"
    $fiveFlowPlan = def_BuildFiveFlowPlan -SubsystemPlan $subsystemPlan
    $sequentialPlan = def_BuildSequentialCloseoutPlan

    def_Progress 6 10 "Reconstruct used toolbox folder"
    $toolboxIndex = def_BuildToolbox -ToolRows $toolRows

    def_Progress 7 10 "Build counts and next commands"
    $projectCounts = def_CountBy -Rows $fileRows -Property "def_project"
    $roleCounts = def_CountBy -Rows $fileRows -Property "def_file_role"
    $nextCmd = def_BuildNextCommands -LatestV0106 $latest -RunDir $def_RUN_DIR

    def_Progress 8 10 "Write CSV and JSON outputs"
    def_WriteCsv $p0 (Join-Path $def_OUTPUT_DIR "VIA_P0_DomainReview.csv")
    def_WriteCsv $p1 (Join-Path $def_OUTPUT_DIR "VIA_P1_PathReview.csv")
    def_WriteCsv $p2 (Join-Path $def_OUTPUT_DIR "VIA_P2_EngineReview.csv")
    def_WriteCsv $p3 (Join-Path $def_OUTPUT_DIR "VIA_P3_UI_NoiseReference.csv")
    def_WriteCsv $subsystemPlan (Join-Path $def_OUTPUT_DIR "VIA_SubsystemIntegrationPlan.csv")
    def_WriteCsv $fiveFlowPlan (Join-Path $def_OUTPUT_DIR "VIA_FiveFlowPlan.csv")
    def_WriteCsv $sequentialPlan (Join-Path $def_OUTPUT_DIR "VIA_SequentialCloseoutPlan.csv")
    def_WriteCsv $toolboxIndex (Join-Path $def_OUTPUT_DIR "VIA_ToolboxUsed_Index.csv")
    def_WriteCsv $projectCounts (Join-Path $def_OUTPUT_DIR "VIA_ProjectCounts.csv")
    def_WriteCsv $roleCounts (Join-Path $def_OUTPUT_DIR "VIA_FileRoleCounts.csv")

    $v0106Files = ""
    $v0106Params = ""
    try { $v0106Files = [string]$v0106Summary.Files } catch {}
    try { $v0106Params = [string]$v0106Summary.Parameters } catch {}

    $summary = [ordered]@{
        Status = "VIA_INTEGRATION_SECONDSTEP_CLOSEOUT_v0107_READY"
        RunId = $def_RUN_ID
        LatestV0106 = $latest
        V0106Files = $v0106Files
        V0106Parameters = $v0106Params
        Engines = @($engineRows).Count
        P0Domain = @($p0).Count
        P1Path = @($p1).Count
        P2Engine = @($p2).Count
        P3Noise = @($p3).Count
        Subsystems = @($subsystemPlan).Count
        Tools = @($toolboxIndex).Count
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        ToolboxDir = $def_TOOLBOX_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; plan-only closeout."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_SecondStep_CloseoutPlanner_Summary.json")
    def_WriteJson $p0 (Join-Path $def_OUTPUT_DIR "VIA_P0_DomainReview.json")
    def_WriteJson $p1 (Join-Path $def_OUTPUT_DIR "VIA_P1_PathReview.json")
    def_WriteJson $p2 (Join-Path $def_OUTPUT_DIR "VIA_P2_EngineReview.json")
    def_WriteJson $p3 (Join-Path $def_OUTPUT_DIR "VIA_P3_UI_NoiseReference.json")
    def_WriteJson $subsystemPlan (Join-Path $def_OUTPUT_DIR "VIA_SubsystemIntegrationPlan.json")
    def_WriteJson $fiveFlowPlan (Join-Path $def_OUTPUT_DIR "VIA_FiveFlowPlan.json")
    def_WriteJson $sequentialPlan (Join-Path $def_OUTPUT_DIR "VIA_SequentialCloseoutPlan.json")
    def_WriteJson $toolboxIndex (Join-Path $def_OUTPUT_DIR "VIA_ToolboxUsed_Index.json")

    def_Progress 9 10 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_SecondStep_CloseoutPlanner_Report_v0107.html"
    def_Report `
        -Summary ([PSCustomObject]$summary) `
        -P0 $p0 `
        -P1 $p1 `
        -P2 $p2 `
        -P3 $p3 `
        -SubsystemPlan $subsystemPlan `
        -FiveFlowPlan $fiveFlowPlan `
        -SequentialPlan $sequentialPlan `
        -ToolboxIndex $toolboxIndex `
        -ProjectCounts $projectCounts `
        -RoleCounts $roleCounts `
        -EngineRows $engineRows `
        -PS15 $def_PS15_ACCELERATORS `
        -ReportPath $report

    def_Progress 10 10 "Complete"
    Write-Progress -Activity "VIA SecondStep Closeout Planner v0107" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA SecondStep Closeout Planner v0107 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status   : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0106    : $latest" -ForegroundColor Gray
    Write-Host "P0       : $($summary.P0Domain)" -ForegroundColor Yellow
    Write-Host "P1       : $($summary.P1Path)" -ForegroundColor Yellow
    Write-Host "P2       : $($summary.P2Engine)" -ForegroundColor Gray
    Write-Host "P3       : $($summary.P3Noise)" -ForegroundColor Gray
    Write-Host "Report   : $report" -ForegroundColor Cyan
    Write-Host "Output   : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "Toolbox  : $def_TOOLBOX_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd  : $nextCmd" -ForegroundColor Cyan

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
