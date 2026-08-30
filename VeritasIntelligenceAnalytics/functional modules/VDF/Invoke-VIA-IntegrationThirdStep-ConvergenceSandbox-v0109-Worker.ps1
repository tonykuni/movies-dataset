param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0108_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
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

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_thirdstep_convergence"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_SANDBOX_DIR = Join-Path $def_RUN_DIR "_sandbox_patch_candidates"
$def_TOOLBOX_DIR = Join-Path $def_RUN_DIR "_toolbox_review"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_ThirdStep_ConvergenceSandbox_v0109.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0108 auto discovery",
    "A02 CSV-only incremental load; no BASE full re-scan",
    "A03 child-isolated execution",
    "A04 dynamic progress on every stage",
    "A05 no delete / no cleanup mutation",
    "A06 no Stop-Process",
    "A07 P0 domain keys sequential review",
    "A08 P1 path aliases separated from domain conflicts",
    "A09 P2 engine bridge queue parallel-safe smoke only",
    "A10 P3 UI/noise suppressed from blocking lane",
    "A11 subsystem five-flow plan",
    "A12 sandbox-only patch candidate folders",
    "A13 Top10 local free libs matrix by function and language",
    "A14 one-page compact professional HTML report",
    "A15 next-command index generation"
)

function def_EnsureDir {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_SANDBOX_DIR,$def_TOOLBOX_DIR,$def_LOG_DIR)) {
    def_EnsureDir $d
}

function def_S {
    param($Value)
    if ($null -eq $Value) { return "" }
    try { return [string]$Value } catch { return "" }
}

function def_Html {
    param($Text)
    return [System.Net.WebUtility]::HtmlEncode((def_S $Text))
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
    Write-Progress -Activity "VIA ThirdStep Convergence Sandbox v0109" -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
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
    param($Object,[string]$Path,[int]$Depth = 12)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_GetProp {
    param($Obj,[string]$Name)
    if ($null -eq $Obj) { return "" }
    if ($Obj.PSObject.Properties.Name -contains $Name) {
        return def_S $Obj.$Name
    }
    return ""
}

function def_GetLatestV0108 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0108_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0108_ROOT) {
            return $def_PARAM_V0108_ROOT
        }
        throw "Specified v0108 root does not exist: $def_PARAM_V0108_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_secondstep_closeout"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0108 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_SecondStep_CloseoutPlanner_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0108 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_ClassifyDomainFamily {
    param([string]$Key,[string]$Groups,[string]$Samples)

    $t = ((def_S $Key) + " " + (def_S $Groups) + " " + (def_S $Samples)).ToLowerInvariant()

    if ($t -match "ticker|tw_ticker|bloomberg|yfinance|market_universe|symbol|代號") { return "MARKET_TICKER_IDENTITY" }
    if ($t -match "source|provider|api|fred|akshare|yfinance|url|data_source|official|資料源") { return "DATA_SOURCE_CONTRACT" }
    if ($t -match "schema|field|column|type|unit|category|def_|uid|official_en|official_zh|科目") { return "SCHEMA_FIELD_CONTRACT" }
    if ($t -match "policy|risk|hardgate|governance|mutability|status|validate|rule") { return "GOVERNANCE_POLICY" }
    if ($t -match "visual|color|font|bg|ink|layout|html|css|display|chart") { return "VISUAL_LOCK" }
    if ($t -match "engine|module|function|class|import|argparse|owner_engine") { return "ENGINE_INTERFACE" }
    return "DOMAIN_GENERAL"
}

function def_SuggestOwner {
    param([string]$Family,[string]$Groups,[string]$Key)

    $g = ((def_S $Family) + " " + (def_S $Groups) + " " + (def_S $Key)).ToUpperInvariant()

    if ($g -match "MARKET|TICKER|DATA_SOURCE|VDF") { return "VDF" }
    if ($g -match "SCHEMA|FIELD|VRN|FINANCIAL|REPORT") { return "VRN/VDF" }
    if ($g -match "VISUAL|LAYOUT|HTML|CSS|VIS") { return "VIS" }
    if ($g -match "ENGINE|VEF") { return "VEF/VIA" }
    if ($g -match "GOVERNANCE|POLICY|HARDGATE|VIA") { return "VIA" }
    return "VIA_REVIEW_BOARD"
}

function def_BuildP0DecisionTemplate {
    param([array]$P0)

    $out = New-Object System.Collections.ArrayList
    foreach ($r in $P0) {
        $key = def_GetProp $r "def_normalized_key"
        $groups = def_GetProp $r "def_groups"
        $samples = def_GetProp $r "def_sample_values"
        $family = def_ClassifyDomainFamily -Key $key -Groups $groups -Samples $samples
        $owner = def_SuggestOwner -Family $family -Groups $groups -Key $key

        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = "P0"
            def_domain_family = $family
            def_owner_engine = $owner
            def_normalized_key = $key
            def_occurrences = def_GetProp $r "def_occurrences"
            def_distinct_values = def_GetProp $r "def_distinct_values"
            def_decision_needed = "YES"
            def_default_action = "REVIEW_AND_FREEZE_OWNER"
            def_parallel_safe = "false"
            def_hydra_guard = "One key, one owner, one canonical decision. Never patch by fuzzy label."
            def_sample_values = $samples
            def_sample_files = def_GetProp $r "def_sample_files"
        })
    }
    return @($out)
}

function def_ClassifyPathAlias {
    param([string]$PathValue)

    $p = def_S $PathValue
    $pl = $p.ToLowerInvariant()

    if ($pl -match "\\downloads\\veritasintelligenceanalytics\\functional modules\\vdf") { return "VDF_DIR_DOWNLOADS" }
    if ($pl -match "\\downloads\\veritasintelligenceanalytics\\functional modules") { return "FUNCTIONAL_MODULES_DOWNLOADS" }
    if ($pl -match "\\downloads\\veritasintelligenceanalytics\\supportive modules") { return "SUPPORTIVE_MODULES_DOWNLOADS" }
    if ($pl -match "\\downloads\\veritasintelligenceanalytics") { return "VIA_ROOT_DOWNLOADS" }
    if ($pl -match "\\onedrive\\veritasintelligenceanalytics") { return "VIA_ROOT_ONEDRIVE_LEGACY" }
    if ($pl -match "\\users\\tonyk\\downloads") { return "USER_DOWNLOADS" }
    if ($pl -match "\\envs\\|\\scripts\\python\.exe") { return "PYTHON_ENV_PATH" }
    return "PATH_OTHER_REVIEW"
}

function def_ExtractWindowsPaths {
    param([array]$Rows)

    $out = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($r in $Rows) {
        $samples = def_GetProp $r "def_sample_values"
        $files = def_GetProp $r "def_sample_files"
        $tokens = @($samples -split "\s*\|\|\s*")

        foreach ($tokRaw in $tokens) {
            $tok = (def_S $tokRaw).Trim()
            if ($tok -match "^[A-Za-z]:\\") {
                $alias = def_ClassifyPathAlias -PathValue $tok
                $key = "$alias||$tok"
                if (-not $seen.ContainsKey($key)) {
                    $seen[$key] = $true
                    [void]$out.Add([pscustomobject][ordered]@{
                        def_alias = $alias
                        def_path_value = $tok
                        def_status = "REVIEW_ALIAS"
                        def_recommendation = "Convert to variable reference before any source mutation."
                        def_source_conflict_key = def_GetProp $r "def_normalized_key"
                        def_sample_files = $files
                    })
                }
            }
        }
    }

    $static = @(
        @("VIA_ROOT_DOWNLOADS","C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics","ACCEPT_CANONICAL_ROOT"),
        @("VDF_DIR_DOWNLOADS","C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF","ACCEPT_CANONICAL_ROOT"),
        @("FUNCTIONAL_MODULES_DOWNLOADS","C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules","ACCEPT_CANONICAL_ROOT"),
        @("SUPPORTIVE_MODULES_DOWNLOADS","C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules","ACCEPT_CANONICAL_ROOT"),
        @("USER_DOWNLOADS","C:\Users\tonyk\Downloads","REFERENCE_ONLY"),
        @("VIA_ROOT_ONEDRIVE_LEGACY","C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics","LEGACY_REVIEW"),
        @("PYTHON_ENV_ONEDRIVE","C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe","ENV_REVIEW")
    )

    foreach ($s in $static) {
        $key = "$($s[0])||$($s[1])"
        if (-not $seen.ContainsKey($key)) {
            [void]$out.Add([pscustomobject][ordered]@{
                def_alias = $s[0]
                def_path_value = $s[1]
                def_status = $s[2]
                def_recommendation = "Use alias in future generated scripts."
                def_source_conflict_key = "STATIC_ALIAS"
                def_sample_files = ""
            })
        }
    }

    return @($out | Sort-Object def_alias, def_path_value)
}

function def_BuildP2EngineBridgeQueue {
    param([array]$P2,[array]$SubsystemPlan)

    $out = New-Object System.Collections.ArrayList

    foreach ($s in $SubsystemPlan) {
        $project = def_GetProp $s "def_project"
        if ([string]::IsNullOrWhiteSpace($project)) { continue }

        $engineCount = def_GetProp $s "def_engines"
        $risk = def_GetProp $s "def_hydra_risk"

        $mode = "PARALLEL_SAFE_SMOKE"
        if ($risk -match "HIGH") { $mode = "SEQUENTIAL_REVIEW_FIRST" }
        if ($project -eq "UNKNOWN") { $mode = "CLASSIFY_BEFORE_BRIDGE" }

        $candidateDir = Join-Path $def_SANDBOX_DIR $project
        def_EnsureDir $candidateDir

        [void]$out.Add([pscustomobject][ordered]@{
            def_project = $project
            def_engines = $engineCount
            def_bridge_mode = $mode
            def_candidate_dir = $candidateDir
            def_source_mutation = "false"
            def_smoke_test_policy = "child isolated; read-only; no DB write"
            def_next_action = "Generate adapter contract only. Do not merge canonical code yet."
        })
    }

    return @($out)
}

function def_BuildFiveFlowExecutionPlan {
    return @(
        [pscustomobject][ordered]@{
            def_flow = "FLOW_01_SUPPORTIVE_MODULES"
            def_scope = "SafePolyglot / NexusCore / PolyglotCheck / EnvManager / Aegis / Celeritas"
            def_current_status = "toolbox staged and readable"
            def_next_gate = "parameter contract + invocation contract"
            def_parallel = "scan parallel; repair sequential"
            def_output = "supportive_active_pointer_candidate.json"
        },
        [pscustomobject][ordered]@{
            def_flow = "FLOW_02_FUNCTIONAL_MODULES"
            def_scope = "UnifiedSpec / CodexNexus / GovernanceRegistry / LayoutRegistry / VisualRegistry"
            def_current_status = "registry review required"
            def_next_gate = "schema owner and visual owner lock"
            def_parallel = "read-only parallel"
            def_output = "functional_contract_candidate.json"
        },
        [pscustomobject][ordered]@{
            def_flow = "FLOW_03_PARAMETERS_SSOT"
            def_scope = "P0/P1/P2/P3 parameter triage"
            def_current_status = "P0=manual/sequential, P1=path alias, P2=engine bridge, P3=noise"
            def_next_gate = "freeze P0 owner decisions"
            def_parallel = "P0 sequential; P3 parallel"
            def_output = "parameter_ssot_decision_template.csv"
        },
        [pscustomobject][ordered]@{
            def_flow = "FLOW_04_ENGINE_BRIDGE"
            def_scope = "VDF / VRN / VIA / VIS / VEF / VPF / VPL / VHS"
            def_current_status = "engine rows loaded from v0106/v0108"
            def_next_gate = "adapter bridge smoke test"
            def_parallel = "one child per subsystem after P0/P1"
            def_output = "engine_bridge_queue.csv"
        },
        [pscustomobject][ordered]@{
            def_flow = "FLOW_05_UI_ONE_INTERFACE"
            def_scope = "Final Parameters One Interface / VisualLock / compact matrix HTML"
            def_current_status = "small-font one-page report generated"
            def_next_gate = "equal-height layout + no-wrap overflow control"
            def_parallel = "safe after data contract stable"
            def_output = "one_interface_closeout_ui_candidate.html"
        }
    )
}

function def_BuildTop10Libs {
    $rows = New-Object System.Collections.ArrayList

    $data = @(
        @("PowerShell Orchestration","PowerShell","Pester; PSScriptAnalyzer; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; Pode; BurntToast; SecretManagement; PSReadLine","test, lint, parallel child jobs, Excel/CSV, HTML reports, local UI, notifications"),
        @("PowerShell Windows Governance","PowerShell","Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; ThreadJob; CimCmdlets; PSReadLine; CompletionPredictor; PSWindowsUpdate; WinGet.Client; SecretStore; ImportExcel","safe Windows I/O, environment detection, update planning, local registry reports"),
        @("Python Data Core","Python","pandas; polars; duckdb; pyarrow; numpy; scipy; pydantic; pandera; rich; tqdm","dataframes, local DB, parquet, schema validation, CLI matrix progress"),
        @("Python Web/API Fetch","Python","requests; httpx; aiohttp; urllib3; tenacity; requests-cache; cachetools; beautifulsoup4; lxml; feedparser","official API fetch, retry, local cache, HTML/XML parsing"),
        @("Python PDF/OCR VRN","Python","pdfplumber; PyMuPDF; pdfminer.six; pypdf; camelot-py; tabula-py; pytesseract; easyocr; opencv-python; Pillow","PDF table/text extraction, OCR, image layout, table reconstruction"),
        @("Python CV/Layout","Python","opencv-python; scikit-image; Pillow; imageio; numpy; scipy; layoutparser; shapely; networkx; matplotlib","layout detection, image preprocessing, geometric reconstruction, diagnostics"),
        @("Python Testing/Quality","Python","pytest; hypothesis; coverage; ruff; black; mypy; bandit; tox; nox; deepdiff","test, property checks, coverage, lint, type checks, diff audit"),
        @("Python Config/Registry","Python","jsonschema; fastjsonschema; pydantic; cerberus; voluptuous; ruamel.yaml; PyYAML; tomli; orjson; msgspec","schema validation, YAML/JSON registry, fast serialization"),
        @("JavaScript UI Matrix","JavaScript","Vanilla JS; Plotly.js; D3.js; ECharts; Tabulator; AG Grid Community; PapaParse; SheetJS; Fuse.js; Mermaid","local dashboards, charts, tables, CSV/XLSX parsing, search, flow diagrams"),
        @("HTML/CSS One Interface","HTML/CSS","CSS Grid; Flexbox; CSS variables; clamp(); container queries; media queries; sticky table headers; overflow-wrap; backdrop-filter; local fonts fallback","compact one-page reports, equal-height panels, small-font professional UI"),
        @("Local DB/Storage","Python/SQL","DuckDB; SQLite; pyarrow; parquet-tools; pandas; polars; sqlite-utils; datasette; csvkit; frictionless","local analytics DB, parquet/csv registry, validation and browser inspection"),
        @("Visualization/Report","Python/JS","Plotly; matplotlib; bokeh; altair; pyecharts; networkx; graphviz; Mermaid; Tabulator; PSWriteHTML","matrix reports, chart reports, dependency graph, one-page UI")
    )

    foreach ($d in $data) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_function_area = $d[0]
            def_language = $d[1]
            def_top10_local_free_libs = $d[2]
            def_use_case = $d[3]
        })
    }

    return @($rows)
}

function def_BuildActionBacklog {
    param([array]$P0Decision,[array]$PathAliases,[array]$P2Queue,[array]$FiveFlow)

    $out = New-Object System.Collections.ArrayList

    foreach ($r in @($P0Decision | Select-Object -First 80)) {
        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = "P0"
            def_lane = "DOMAIN_DECISION"
            def_target = def_GetProp $r "def_normalized_key"
            def_owner = def_GetProp $r "def_owner_engine"
            def_action = "Review and freeze canonical owner/value"
            def_parallel_safe = "false"
        })
    }

    foreach ($r in @($PathAliases | Select-Object -First 80)) {
        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = "P1"
            def_lane = "PATH_ALIAS"
            def_target = def_GetProp $r "def_alias"
            def_owner = "VIA/VDF"
            def_action = "Replace hard path with alias in future generated scripts only"
            def_parallel_safe = "false"
        })
    }

    foreach ($r in @($P2Queue)) {
        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = "P2"
            def_lane = "ENGINE_BRIDGE"
            def_target = def_GetProp $r "def_project"
            def_owner = def_GetProp $r "def_project"
            def_action = "Create sandbox adapter bridge and smoke test"
            def_parallel_safe = "true_after_P0_P1"
        })
    }

    foreach ($r in @($FiveFlow)) {
        [void]$out.Add([pscustomobject][ordered]@{
            def_priority = "P3"
            def_lane = "FLOW_CLOSEOUT"
            def_target = def_GetProp $r "def_flow"
            def_owner = "VIA"
            def_action = def_GetProp $r "def_next_gate"
            def_parallel_safe = def_GetProp $r "def_parallel"
        })
    }

    return @($out)
}

function def_BuildNextCommands {
    param([string]$RunDir)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0109
# =============================================================================

Start-Process "$RunDir\report\VIA_ThirdStep_ConvergenceSandbox_Report_v0109.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_sandbox_patch_candidates"
Start-Process "$RunDir\_toolbox_review"

Import-Csv "$RunDir\output\VIA_P0_DomainDecisionTemplate.csv" | Select-Object -First 40 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_P1_PathAliasMap.csv" | Select-Object -First 40 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_P2_EngineBridgeQueue.csv" | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_IntegrationActionBacklog.csv" | Select-Object -First 80 | Format-Table -AutoSize
Import-Csv "$RunDir\output\VIA_Top10LocalFreeLibs_ByFunctionLanguage.csv" | Format-Table -AutoSize

# Next safe phase:
# v0110 should generate sandbox-only adapter candidates.
# It must not overwrite canonical files until P0/P1 review is accepted.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0109.ps1"
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
            if ($v.Length -gt 240) { $v = $v.Substring(0,240) + "..." }
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
        [array]$P0Decision,
        [array]$PathAliases,
        [array]$P2Queue,
        [array]$FiveFlow,
        [array]$Backlog,
        [array]$TopLibs,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("P0 Decisions",$Summary.P0DecisionRows),
        @("P1 Path Aliases",$Summary.P1PathAliasRows),
        @("P2 Engine Queue",$Summary.P2EngineQueueRows),
        @("P3 Noise Ref",$Summary.P3NoiseRows),
        @("Action Backlog",$Summary.ActionBacklogRows),
        @("Top10 Lib Rows",$Summary.Top10LibRows),
        @("Policy","No Mutation")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA ThirdStep Convergence Sandbox v0109</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0;--cyan:#6fa8ad}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 12% 7%,rgba(111,168,173,.15),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.45),rgba(230,226,216,.24)),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.6px;line-height:1.34}
.wrap{max-width:1780px;margin:0 auto;padding:15px}
h1{font-size:14.5px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.3px;color:var(--mut);margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:rgba(255,254,250,.92);border:1px solid var(--line);border-radius:9px;padding:6px 7px;min-height:42px}
.k{font-size:7.6px;color:var(--mut)}
.v{font:650 10.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-items:stretch}
.sec{background:rgba(255,254,250,.9);border:1px solid var(--line);border-radius:11px;padding:8px;min-height:220px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:9.6px;margin:0 0 6px;font-weight:650}
.note{font-size:8.2px;color:var(--mut);margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.95px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:var(--mut)}
.footer{margin-top:11px;color:var(--mut);font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA Integration ThirdStep Convergence Sandbox · v0109</h1>
<div class="sub">P0/P1/P2/P3 closeout plan · five independent flows · sandbox-only candidates · Top10 local free libs · PS15 accelerators</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0108 已完成第二步 closeout planner。v0109 不修 source，只把 P0 domain 決策、P1 path alias、P2 engine bridge、P3 UI/noise reference 拆成可執行的收斂沙盒計畫。下一版 v0110 才能生成 sandbox adapter candidate；正式改 canonical 仍需 P0/P1 人工確認。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Source Mutation</span>
<span class="tag">Sandbox Only</span>
<span class="tag">Hydra Guard</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Five Independent Flows</h2>$(def_Table $FiveFlow @("def_flow","def_scope","def_current_status","def_next_gate","def_parallel","def_output") 20)</div>
<div class="sec wide"><h2>def Integration Action Backlog</h2>$(def_Table $Backlog @("def_priority","def_lane","def_target","def_owner","def_action","def_parallel_safe") 180)</div>
<div class="sec wide"><h2>def P0 Domain Decision Template</h2>$(def_Table $P0Decision @("def_priority","def_domain_family","def_owner_engine","def_normalized_key","def_occurrences","def_distinct_values","def_decision_needed","def_default_action","def_parallel_safe","def_hydra_guard","def_sample_values","def_sample_files") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Map</h2>$(def_Table $PathAliases @("def_alias","def_path_value","def_status","def_recommendation","def_source_conflict_key","def_sample_files") 180)</div>
<div class="sec wide"><h2>def P2 Engine Bridge Queue</h2>$(def_Table $P2Queue @("def_project","def_engines","def_bridge_mode","def_candidate_dir","def_source_mutation","def_smoke_test_policy","def_next_action") 80)</div>
<div class="sec wide"><h2>def Top 10 Local Free Libs by Function and Language</h2>$(def_Table $TopLibs @("def_function_area","def_language","def_top10_local_free_libs","def_use_case") 40)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0108 source: $(def_Html $Summary.LatestV0108)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
Sandbox: $(def_Html $Summary.SandboxDir)<br/>
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
    Write-Host "def VIA · INTEGRATION THIRDSTEP CONVERGENCE SANDBOX · v0109" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 10 "Find latest v0108 output"
    $latest = def_GetLatestV0108
    $latestOut = Join-Path $latest "output"

    def_Log "OK" "Latest v0108: $latest" Green

    def_Progress 2 10 "Load v0108 matrices"
    $summaryV0108 = def_LoadJson (Join-Path $latestOut "VIA_SecondStep_CloseoutPlanner_Summary.json")
    $p0 = def_LoadCsv (Join-Path $latestOut "VIA_P0_DomainReview.csv")
    $p1 = def_LoadCsv (Join-Path $latestOut "VIA_P1_PathReview.csv")
    $p2 = def_LoadCsv (Join-Path $latestOut "VIA_P2_EngineReview.csv")
    $p3 = def_LoadCsv (Join-Path $latestOut "VIA_P3_UI_NoiseReference.csv")
    $subsystemPlan = def_LoadCsv (Join-Path $latestOut "VIA_SubsystemIntegrationPlan.csv")
    $toolboxIndex = def_LoadCsv (Join-Path $latestOut "VIA_ToolboxUsed_Index.csv")

    def_Log "OK" "Loaded P0=$(@($p0).Count), P1=$(@($p1).Count), P2=$(@($p2).Count), P3=$(@($p3).Count), Subsystems=$(@($subsystemPlan).Count)" Green

    def_Progress 3 10 "Build P0 domain decision template"
    $p0Decision = def_BuildP0DecisionTemplate -P0 $p0

    def_Progress 4 10 "Build P1 path alias map"
    $pathAliases = def_ExtractWindowsPaths -Rows $p1

    def_Progress 5 10 "Build P2 engine bridge queue"
    $p2Queue = def_BuildP2EngineBridgeQueue -P2 $p2 -SubsystemPlan $subsystemPlan

    def_Progress 6 10 "Build five-flow execution plan"
    $fiveFlow = def_BuildFiveFlowExecutionPlan

    def_Progress 7 10 "Build Top10 local free libs and PS15 matrix"
    $topLibs = def_BuildTop10Libs

    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_Progress 8 10 "Build integration action backlog and next commands"
    $backlog = def_BuildActionBacklog -P0Decision $p0Decision -PathAliases $pathAliases -P2Queue $p2Queue -FiveFlow $fiveFlow
    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR

    def_Progress 9 10 "Write CSV/JSON outputs"
    def_WriteCsv $p0Decision (Join-Path $def_OUTPUT_DIR "VIA_P0_DomainDecisionTemplate.csv")
    def_WriteCsv $pathAliases (Join-Path $def_OUTPUT_DIR "VIA_P1_PathAliasMap.csv")
    def_WriteCsv $p2Queue (Join-Path $def_OUTPUT_DIR "VIA_P2_EngineBridgeQueue.csv")
    def_WriteCsv $fiveFlow (Join-Path $def_OUTPUT_DIR "VIA_FiveFlowExecutionPlan.csv")
    def_WriteCsv $topLibs (Join-Path $def_OUTPUT_DIR "VIA_Top10LocalFreeLibs_ByFunctionLanguage.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_PS15_Accelerators.csv")
    def_WriteCsv $backlog (Join-Path $def_OUTPUT_DIR "VIA_IntegrationActionBacklog.csv")
    def_WriteCsv $toolboxIndex (Join-Path $def_OUTPUT_DIR "VIA_ToolboxReview_From_v0108.csv")

    def_WriteJson $p0Decision (Join-Path $def_OUTPUT_DIR "VIA_P0_DomainDecisionTemplate.json")
    def_WriteJson $pathAliases (Join-Path $def_OUTPUT_DIR "VIA_P1_PathAliasMap.json")
    def_WriteJson $p2Queue (Join-Path $def_OUTPUT_DIR "VIA_P2_EngineBridgeQueue.json")
    def_WriteJson $fiveFlow (Join-Path $def_OUTPUT_DIR "VIA_FiveFlowExecutionPlan.json")
    def_WriteJson $topLibs (Join-Path $def_OUTPUT_DIR "VIA_Top10LocalFreeLibs_ByFunctionLanguage.json")
    def_WriteJson $backlog (Join-Path $def_OUTPUT_DIR "VIA_IntegrationActionBacklog.json")

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_INTEGRATION_THIRDSTEP_CONVERGENCE_v0109_READY"
        RunId = $def_RUN_ID
        LatestV0108 = $latest
        P0DecisionRows = "$(@($p0Decision).Count)"
        P1PathAliasRows = "$(@($pathAliases).Count)"
        P2EngineQueueRows = "$(@($p2Queue).Count)"
        P3NoiseRows = "$(@($p3).Count)"
        FiveFlowRows = "$(@($fiveFlow).Count)"
        ActionBacklogRows = "$(@($backlog).Count)"
        Top10LibRows = "$(@($topLibs).Count)"
        PS15Rows = "$(@($ps15Rows).Count)"
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        SandboxDir = $def_SANDBOX_DIR
        ToolboxDir = $def_TOOLBOX_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; sandbox candidate planning only."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_ThirdStep_ConvergenceSandbox_Summary.json")

    def_Progress 10 10 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_ThirdStep_ConvergenceSandbox_Report_v0109.html"
    def_WriteReport `
        -Summary $summary `
        -P0Decision $p0Decision `
        -PathAliases $pathAliases `
        -P2Queue $p2Queue `
        -FiveFlow $fiveFlow `
        -Backlog $backlog `
        -TopLibs $topLibs `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA ThirdStep Convergence Sandbox v0109" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA ThirdStep Convergence Sandbox v0109 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status     : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0108      : $latest" -ForegroundColor Gray
    Write-Host "P0Decision : $($summary.P0DecisionRows)" -ForegroundColor Yellow
    Write-Host "PathAlias  : $($summary.P1PathAliasRows)" -ForegroundColor Yellow
    Write-Host "P2Queue    : $($summary.P2EngineQueueRows)" -ForegroundColor Cyan
    Write-Host "Backlog    : $($summary.ActionBacklogRows)" -ForegroundColor Cyan
    Write-Host "Top10Libs  : $($summary.Top10LibRows)" -ForegroundColor Cyan
    Write-Host "Report     : $report" -ForegroundColor Cyan
    Write-Host "Output     : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "Sandbox    : $def_SANDBOX_DIR" -ForegroundColor Cyan
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
