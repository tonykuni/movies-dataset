param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [int]$def_PARAM_MAX_SCAN_FILES = 8000,
    [int]$def_PARAM_MAX_READ_KB = 768,
    [switch]$def_PARAM_OPEN_HTML_REPORT = $true
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

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_FIRSTSTEP_v0106_WORKER" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_firststep_panorama"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_USED_TOOLS_DIR = Join-Path $def_RUN_DIR "_used_tools"
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"

$def_SUPPORTIVE_TOOLS = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_README.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_StaticValidation.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Read_Me_VeritasNexusCore.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
)

$def_FUNCTIONAL_TOOLS = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\UnifiedSpec.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\Invoke-VeritasCodexNexus.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\GovernanceRegistry.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\LayoutRegistry.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VisualRegistry.json"
)

$def_FIRSTSTEP_TOOLS = @(
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v044-RiskTriageTrueProgress.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v043-CompletionAnchorEngine.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v042-SafeHtmlRendererHotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v041-HistoryLensHotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v040.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v031-Hotfix (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v031-Hotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v030.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-RedFinding-Triage-v01 (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-RedFinding-Triage-v01.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-NexusToolBridge-Unified-v02.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v2.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v1.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v062-NullSafeStepSafe (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v062-NullSafeStepSafe.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v061-BoolParamHotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v060.ps1",
    "C:\Users\tonyk\Downloads\VIA_EngineForge_Config.template.json",
    "C:\Users\tonyk\Downloads\via_three_round_safe_convergence_spine.png"
)

$def_PS15_ACCELERATORS = @(
    "A01 Child-isolated execution through launcher",
    "A02 Dynamic Write-Progress in every major stage",
    "A03 Bounded text read to avoid memory spike",
    "A04 Extension filter to avoid binary scan explosion",
    "A05 Run-isolated used-tools staging",
    "A06 No delete / no cleanup mutation",
    "A07 No Stop-Process",
    "A08 No old v0103 dependency",
    "A09 No regex block patching old script",
    "A10 ArrayList row collector avoids type mismatch",
    "A11 Five-flow separation avoids Hydra risk",
    "A12 P0/P1/P2/P3 conflict triage",
    "A13 CSV + JSON + one-page HTML synchronized outputs",
    "A14 Small professional UI font and compact matrix",
    "A15 PowerShell remains open on failure"
)

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_USED_TOOLS_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_LOG_DIR)) {
    def_EnsureDir $d
}

$def_LOG = Join-Path $def_LOG_DIR "VIA_IntegrationFirstStep_v0106_Worker.log"

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
    Write-Progress -Activity "VIA Integration FirstStep v0106 Worker" -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
}

function def_Html {
    param([string]$Text)
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function def_Sha12 {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.Substring(0,12)
        }
    } catch {}
    return ""
}

function def_ReadBounded {
    param([string]$Path,[int]$MaxKB = 768)

    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($item.Length -le 0) { return "" }

        $maxBytes = [Math]::Max(1024, $MaxKB * 1024)
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $len = [Math]::Min([int64]$maxBytes, $fs.Length)
            $buf = New-Object byte[] $len
            [void]$fs.Read($buf, 0, $len)
            return [System.Text.Encoding]::UTF8.GetString($buf)
        } finally {
            $fs.Close()
        }
    } catch {
        return ""
    }
}

function def_Project {
    param([string]$Name,[string]$Path)
    $s = ($Name + " " + $Path).ToUpperInvariant()
    if ($s -match "VDF|DATAFORGE") { return "VDF" }
    if ($s -match "VRN|REPORTNOVA") { return "VRN" }
    if ($s -match "VIA|VERITASINTELLIGENCE") { return "VIA" }
    if ($s -match "VIS") { return "VIS" }
    if ($s -match "VEF|ENGINEFORGE") { return "VEF" }
    if ($s -match "VHS") { return "VHS" }
    if ($s -match "VPF") { return "VPF" }
    if ($s -match "VPL|VERITASPULSE") { return "VPL" }
    if ($s -match "LL34") { return "LL34" }
    return "UNKNOWN"
}

function def_Role {
    param([string]$Name,[string]$Ext)
    $s = $Name.ToLowerInvariant()
    if ($s -match "registry|schema|ssot") { return "REGISTRY" }
    if ($s -match "lock|freeze") { return "LOCK_REGISTRY" }
    if ($s -match "test|validation|verify|smoke|lint") { return "TEST_VALIDATION" }
    if ($s -match "report|summary|panorama") { return "REPORT" }
    if ($s -match "manifest|packlist") { return "MANIFEST" }
    if ($s -match "config|template|spec") { return "CONFIG_TEMPLATE" }
    if ($s -match "engine|forge|fetch|router|orchestrator") { return "ENGINE_MODULE" }
    if ($Ext -in @(".html",".png",".svg",".css")) { return "UI_VISUAL" }
    return "SOURCE"
}

function def_Group {
    param([string]$Key,[string]$Value)
    $s = ($Key + " " + $Value).ToLowerInvariant()
    if ($s -match "path|dir|folder|file|root|output|input|windows|c:\\") { return "PATH_IO" }
    if ($s -match "schema|field|column|table|uid|ticker|unit") { return "SCHEMA_FIELD" }
    if ($s -match "policy|hardgate|no delete|stop-process|governance|risk") { return "GOVERNANCE_POLICY" }
    if ($s -match "color|font|css|layout|visual|theme|html|ui|plotly|chart") { return "VISUAL_LOCK" }
    if ($s -match "engine|class|function|def_|invoke|module|import") { return "ENGINE" }
    if ($s -match "version|release|generated|run_id|v0|v1|v2|v\d") { return "VERSION_RELEASE" }
    if ($s -match "fred|yfinance|yf|akshare|api|source|twse|tpex|mops|eurostat|ecb") { return "DATA_SOURCE" }
    if ($s -match "stock|etf|market|universe|sector|industry|theme") { return "MARKET_UNIVERSE" }
    if ($s -match "sentiment|fear|greed|aaii|macro|gdp|cpi|pmi|fed|yield|vix") { return "MACRO_SENTIMENT" }
    return "GENERAL"
}

function def_WriteCsv {
    param([array]$Rows,[string]$Path)
    if ($Rows -and $Rows.Count -gt 0) {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    } else {
        @() | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function def_WriteJson {
    param($Object,[string]$Path,[int]$Depth = 8)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_StageTools {
    $rows = [System.Collections.ArrayList]::new()
    $sets = @(
        [pscustomobject]@{ Category = "supportive"; Paths = @($def_SUPPORTIVE_TOOLS) },
        [pscustomobject]@{ Category = "functional"; Paths = @($def_FUNCTIONAL_TOOLS) },
        [pscustomobject]@{ Category = "firststep"; Paths = @($def_FIRSTSTEP_TOOLS) }
    )

    foreach ($set in $sets) {
        $catDir = Join-Path $def_USED_TOOLS_DIR $set.Category
        def_EnsureDir $catDir

        foreach ($p0 in @($set.Paths)) {
            $p = ([string]$p0).Trim().Trim('"')
            if ([string]::IsNullOrWhiteSpace($p)) { continue }

            $exists = Test-Path -LiteralPath $p
            $leaf = Split-Path -Leaf $p
            $dst = Join-Path $catDir $leaf
            $status = "MISSING"
            $size = ""
            $sha = ""
            $msg = "Source missing."
            $staged = ""

            if ($exists) {
                try {
                    $item = Get-Item -LiteralPath $p -ErrorAction Stop
                    $size = [string]$item.Length
                    $sha = def_Sha12 $p
                    Copy-Item -LiteralPath $p -Destination $dst -Force
                    $status = "STAGED"
                    $msg = "Copied to isolated run folder."
                    $staged = $dst
                } catch {
                    $status = "STAGE_WARN"
                    $msg = $_.Exception.Message
                }
            }

            [void]$rows.Add([pscustomobject][ordered]@{
                def_category = [string]$set.Category
                def_file = [string]$leaf
                def_exists = [string]$exists
                def_status = [string]$status
                def_size_bytes = [string]$size
                def_sha12 = [string]$sha
                def_source_path = [string]$p
                def_staged_path = [string]$staged
                def_message = [string]$msg
            })
        }
    }

    return @($rows)
}

function def_ScanFiles {
    $rows = [System.Collections.ArrayList]::new()
    $allowed = @(".ps1",".py",".json",".md",".html",".js",".ts",".csv",".yaml",".yml",".log",".txt",".docx",".png")
    $skip = '\\(__pycache__|\.git|node_modules|\.venv|venv|_envs|dist|build)\\'

    $files = Get-ChildItem -LiteralPath $def_PARAM_VIA_ROOT -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $skip -and $allowed -contains $_.Extension.ToLowerInvariant() } |
        Select-Object -First $def_PARAM_MAX_SCAN_FILES

    $n = 0
    foreach ($f in $files) {
        $n++
        if (($n % 200) -eq 0) {
            Write-Progress -Activity "VIA Base file scan" -Status "Scanned $n / $($files.Count)" -PercentComplete ([int](($n / [Math]::Max(1,$files.Count))*100))
        }

        $sha = def_Sha12 $f.FullName
        $status = "OK"
        if ($f.Length -eq 0) { $status = "ZERO_BYTE_REVIEW" }
        elseif ($f.Length -lt 20) { $status = "TINY_FILE_REVIEW" }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = [string](def_Project $f.Name $f.FullName)
            def_file_role = [string](def_Role $f.Name $f.Extension)
            def_file_name = [string]$f.Name
            def_ext = [string]$f.Extension
            def_status = [string]$status
            def_size_bytes = [string]$f.Length
            def_modified_time = [string]$f.LastWriteTime.ToString("s")
            def_sha12 = [string]$sha
            def_path = [string]$f.FullName
        })
    }

    Write-Progress -Activity "VIA Base file scan" -Completed
    return @($rows)
}

function def_ExtractParams {
    param([array]$FileRows)

    $rows = [System.Collections.ArrayList]::new()
    $engineRows = [System.Collections.ArrayList]::new()
    $textExt = @(".ps1",".py",".json",".md",".html",".js",".ts",".yaml",".yml",".txt",".log",".csv")

    $i = 0
    foreach ($fr in $FileRows) {
        $i++
        if (($i % 200) -eq 0) {
            Write-Progress -Activity "VIA parameter extraction" -Status "Extracting $i / $($FileRows.Count)" -PercentComplete ([int](($i / [Math]::Max(1,$FileRows.Count))*100))
        }

        $ext = ([string]$fr.def_ext).ToLowerInvariant()
        if (-not ($textExt -contains $ext)) { continue }

        $text = def_ReadBounded -Path $fr.def_path -MaxKB $def_PARAM_MAX_READ_KB
        if ([string]::IsNullOrWhiteSpace($text)) { continue }

        $lines = $text -split "`r?`n"
        $maxLines = [Math]::Min($lines.Count, 1600)
        $localCount = 0
        $engineCount = 0

        for ($k=0; $k -lt $maxLines; $k++) {
            $line = ([string]$lines[$k]).Trim()
            if ([string]::IsNullOrWhiteSpace($line)) { continue }

            $key = $null
            $val = $null
            $source = "text"

            if ($line -match '^\s*(def_PARAM_[A-Za-z0-9_]+)\s*=') {
                $key = $matches[1]; $val = $line; $source = "param"
            } elseif ($line -match '^\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*=') {
                $key = $matches[1]; $val = $line; $source = "ps_assignment"
            } elseif ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
                $key = $matches[1]; $val = $line; $source = "py_assignment"
            } elseif ($line -match '^\s*function\s+([A-Za-z0-9_\-]+)') {
                $key = "function." + $matches[1]; $val = $matches[1]; $source = "function"; $engineCount++
            } elseif ($line -match '^\s*def\s+([A-Za-z0-9_]+)\s*\(') {
                $key = "function." + $matches[1]; $val = $matches[1]; $source = "py_function"; $engineCount++
            } elseif ($line -match '^\s*class\s+([A-Za-z0-9_]+)') {
                $key = "class." + $matches[1]; $val = $matches[1]; $source = "py_class"; $engineCount++
            } elseif ($line -match '^\s*import\s+(.+)$') {
                $key = "import"; $val = $matches[1]; $source = "py_import"; $engineCount++
            } elseif ($line -match '^\s*from\s+(.+?)\s+import\s+(.+)$') {
                $key = "import"; $val = $matches[1] + "." + $matches[2]; $source = "py_import"; $engineCount++
            } elseif ($line -match '^\s*["'']?([A-Za-z0-9_\.\-]+)["'']?\s*:\s*(.+?)[,\}]?\s*$') {
                $key = $matches[1]; $val = $matches[2]; $source = "json_yaml_key"
            } elseif ($line -match '<h([1-6])[^>]*>(.*?)</h\1>') {
                $key = "heading_" + $matches[1]; $val = (($matches[2] -replace '<[^>]+>','').Trim()); $source = "html_heading"
            } else {
                continue
            }

            if ($null -ne $key) {
                $preview = [string]$val
                if ($preview.Length -gt 180) { $preview = $preview.Substring(0,180) + "..." }
                $group = def_Group $key $preview
                $localCount++

                [void]$rows.Add([pscustomobject][ordered]@{
                    def_project = [string]$fr.def_project
                    def_file_role = [string]$fr.def_file_role
                    def_group = [string]$group
                    def_key = [string]$key
                    def_value_preview = [string]$preview
                    def_source_type = [string]$source
                    def_file_id = [string]("{0}::{1}" -f $fr.def_file_name,$fr.def_sha12)
                    def_file_name = [string]$fr.def_file_name
                    def_line = [string]($k+1)
                })
            }
        }

        if ($engineCount -gt 0 -or $fr.def_file_role -eq "ENGINE_MODULE") {
            [void]$engineRows.Add([pscustomobject][ordered]@{
                def_project = [string]$fr.def_project
                def_engine_file = [string]$fr.def_file_name
                def_file_role = [string]$fr.def_file_role
                def_engine_param_count = [string]$engineCount
                def_total_param_count = [string]$localCount
                def_path = [string]$fr.def_path
            })
        }
    }

    Write-Progress -Activity "VIA parameter extraction" -Completed

    return [pscustomobject]@{
        Parameters = @($rows)
        Engines = @($engineRows)
    }
}

function def_Conflicts {
    param([array]$Params)

    $rows = [System.Collections.ArrayList]::new()

    foreach ($g in ($Params | Group-Object def_key)) {
        $items = @($g.Group)
        if ($items.Count -lt 2) { continue }

        $vals = @($items | ForEach-Object { [string]$_.def_value_preview } | Select-Object -Unique)
        if ($vals.Count -lt 2) { continue }

        $key = [string]$g.Name
        $severity = "P3_NOISE_REFERENCE"

        if ($key -match "ticker|schema|field|unit|policy|hardgate|owner_engine|source_module|macro|sentiment|fred|yfinance|akshare") {
            $severity = "P0_DOMAIN_REVIEW"
        } elseif ($key -match "path|dir|root|file|output|input") {
            $severity = "P1_PATH_REVIEW"
        } elseif ($key -match "import|function|class|version|generated") {
            $severity = "P2_ENGINE_REVIEW"
        } elseif ($key -match "color|font|css|html|heading|line|padding|margin|background|border|display|x|y|w|h|id|name") {
            $severity = "P3_UI_OR_NOISE"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_severity = [string]$severity
            def_normalized_key = [string]$key
            def_occurrences = [string]$items.Count
            def_distinct_values = [string]$vals.Count
            def_groups = [string]((@($items | ForEach-Object { $_.def_group } | Select-Object -Unique | Select-Object -First 8)) -join ";")
            def_sample_values = [string](($vals | Select-Object -First 6) -join " || ")
            def_sample_files = [string]((@($items | ForEach-Object { $_.def_file_name } | Select-Object -Unique | Select-Object -First 8)) -join "; ")
        })
    }

    return @($rows | Sort-Object def_severity, {[int]$_.def_distinct_values} -Descending)
}

function def_FiveFlows {
    return @(
        [pscustomobject]@{ def_flow="FLOW_01_SUPPORTIVE_TOOLS"; def_scope="SafePolyglot / NexusCore / PolyglotCheck"; def_action="stage + audit + bridge later"; def_parallel_safe="YES"; def_hydra_risk="LOW" },
        [pscustomobject]@{ def_flow="FLOW_02_FUNCTIONAL_MODULES"; def_scope="UnifiedSpec / CodexNexus / Governance / Layout / Visual"; def_action="schema alignment only"; def_parallel_safe="YES_READONLY"; def_hydra_risk="MEDIUM" },
        [pscustomobject]@{ def_flow="FLOW_03_PARAMETERS_SSOT"; def_scope="canonical parameter registry"; def_action="P0/P1/P2/P3 triage"; def_parallel_safe="YES"; def_hydra_risk="LOW" },
        [pscustomobject]@{ def_flow="FLOW_04_ENGINE_BRIDGE"; def_scope="EngineForge / VDF / VRN / VIA / VPF"; def_action="engine matrix + adapter plan"; def_parallel_safe="SCAN_ONLY"; def_hydra_risk="MEDIUM" },
        [pscustomobject]@{ def_flow="FLOW_05_UI_REPORT_CLOSEOUT"; def_scope="one interface HTML"; def_action="compact small-font matrix"; def_parallel_safe="YES"; def_hydra_risk="LOW" }
    )
}

function def_Top10Libs {
    return @(
        [pscustomobject]@{ def_function_area="PowerShell Orchestration"; def_language="PowerShell"; def_top10_local_free_libs="Pester; PSScriptAnalyzer; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; BurntToast; PSReadLine; CompletionPredictor; SecretManagement" },
        [pscustomobject]@{ def_function_area="Python Data Engine"; def_language="Python"; def_top10_local_free_libs="pandas; polars; pyarrow; duckdb; numpy; pydantic; requests; httpx; tenacity; rich" },
        [pscustomobject]@{ def_function_area="Market Data"; def_language="Python"; def_top10_local_free_libs="yfinance; akshare; pandas-datareader; fredapi; pandasdmx; eurostat; exchange-calendars; pandas-market-calendars; beautifulsoup4; lxml" },
        [pscustomobject]@{ def_function_area="Static Analysis"; def_language="Python/PS"; def_top10_local_free_libs="ast; libcst; parso; rope; ruff; mypy; pyflakes; PSScriptAnalyzer; Pester; radon" },
        [pscustomobject]@{ def_function_area="HTML UI"; def_language="HTML/CSS/JS"; def_top10_local_free_libs="Plotly; D3; ECharts; Tabulator; Grid.js; DataTables; PapaParse; Fuse.js; Marked; Mermaid" },
        [pscustomobject]@{ def_function_area="UI Test"; def_language="JavaScript"; def_top10_local_free_libs="Playwright; Vitest; ESLint; Prettier; jsdom; axe-core; Lighthouse; Chart.js; PapaParse; fast-glob" },
        [pscustomobject]@{ def_function_area="Registry Schema"; def_language="JSON/YAML"; def_top10_local_free_libs="ajv; jsonschema; pydantic; ruamel.yaml; yq; jq; jsonlines; frictionless; csvkit; duckdb" },
        [pscustomobject]@{ def_function_area="PDF/Doc"; def_language="Python"; def_top10_local_free_libs="PyMuPDF; pdfplumber; pypdf; camelot; tabula-py; pdfminer.six; openpyxl; python-docx; beautifulsoup4; lxml" },
        [pscustomobject]@{ def_function_area="Visualization"; def_language="Python/JS"; def_top10_local_free_libs="matplotlib; plotly; altair; bokeh; pygal; networkx; graphviz; folium; D3; ECharts" },
        [pscustomobject]@{ def_function_area="Acceleration/Safety"; def_language="Mixed"; def_top10_local_free_libs="joblib; concurrent.futures; asyncio; tenacity; diskcache; sqlite; duckdb; tqdm; rich; psutil" }
    )
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=160)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) { [void]$sb.Append("<th>$(def_Html $c)</th>") }
    [void]$sb.Append("</tr></thead><tbody>")
    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = ""
            try { $v = [string]$r.$c } catch {}
            if ($v.Length -gt 200) { $v = $v.Substring(0,200) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }
    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_Report {
    param($Summary,$ToolRows,$FileRows,$ParamRows,$EngineRows,$ConflictRows,$FlowRows,$Top10Rows,$ReportPath)

    $projectCounts = @($FileRows | Group-Object def_project | Sort-Object Count -Descending | Select-Object Name,Count)
    $groupCounts = @($ParamRows | Group-Object def_group | Sort-Object Count -Descending | Select-Object Name,Count)
    $roleCounts = @($FileRows | Group-Object def_file_role | Sort-Object Count -Descending | Select-Object Name,Count)

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Files",$Summary.Files),
        @("Parameters",$Summary.Parameters),
        @("Engines",$Summary.Engines),
        @("P0 Review",$Summary.P0Review),
        @("P1 Path",$Summary.P1Path),
        @("Tools",$Summary.Tools),
        @("Run",$Summary.RunId)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html ([string]$x[1]))</div></div>"
    }

    $acc = ""
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        $acc += "<tr><td>$($i+1)</td><td>$(def_Html $def_PS15_ACCELERATORS[$i])</td></tr>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA Integration FirstStep v0106</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 12% 8%,rgba(143,184,200,.18),transparent 28%),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:9.5px;line-height:1.38}
.wrap{max-width:1680px;margin:0 auto;padding:18px}
h1{font-size:16px;margin:0 0 4px;font-weight:650}
.sub{font-size:9.5px;color:var(--mut);margin-bottom:12px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;margin-bottom:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:7px 8px;min-height:50px}
.k{font-size:8.5px;color:var(--mut)}.v{font:650 13px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:stretch}
.sec{background:rgba(255,255,255,.82);border:1px solid var(--line);border-radius:12px;padding:9px;min-height:230px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:10.5px;margin:0 0 7px}
.note{font-size:9.2px;color:var(--mut);margin-bottom:8px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:8.7px}
th,td{border-bottom:1px solid #ebe8df;padding:3.5px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.footer{margin-top:12px;color:var(--mut);font-size:8.8px}
@media(max-width:1100px){.cards{grid-template-columns:repeat(4,1fr)}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA Final Parameters One Interface · Integration FirstStep v0106</h1>
<div class="sub">Five independent flows · 15 PowerShell accelerators · no-stall launcher · canonical parameter registry · conflict triage · EngineForge/Nexus bridge</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Overview</h2>
<div class="note">本版避開舊 v0103，不使用 def_FindBestBackup，不 patch 舊檔；只做第一步全景檢視、工具分流、參數整合、衝突分級、後續五流程計畫。</div>
<div class="note">Canonical Accept: $($Summary.CanonicalAccept) · Canonical Review: $($Summary.CanonicalReview) · P0 Domain: $($Summary.P0Review) · P1 Path: $($Summary.P1Path) · P2 Engine: $($Summary.P2Review) · P3 Noise/UI: $($Summary.P3Review)</div>
</div>

<div class="grid">
<div class="sec"><h2>def Five Independent Flows</h2>$(def_Table $FlowRows @("def_flow","def_scope","def_action","def_parallel_safe","def_hydra_risk") 20)</div>
<div class="sec"><h2>def 15 PowerShell Accelerators</h2><table><thead><tr><th style="width:55px">#</th><th>Accelerator</th></tr></thead><tbody>$acc</tbody></table></div>
<div class="sec"><h2>def Project Counts</h2>$(def_Table $projectCounts @("Name","Count") 40)</div>
<div class="sec"><h2>def Parameter Groups</h2>$(def_Table $groupCounts @("Name","Count") 40)</div>
<div class="sec"><h2>def File Roles</h2>$(def_Table $roleCounts @("Name","Count") 40)</div>
<div class="sec"><h2>def Top 10 Local Free Libs</h2>$(def_Table $Top10Rows @("def_function_area","def_language","def_top10_local_free_libs") 40)</div>
<div class="sec wide"><h2>def Conflict Triage Matrix</h2>$(def_Table $ConflictRows @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") 180)</div>
<div class="sec wide"><h2>def Engine Matrix</h2>$(def_Table $EngineRows @("def_project","def_engine_file","def_file_role","def_engine_param_count","def_total_param_count","def_path") 180)</div>
<div class="sec wide"><h2>def Used Tools Staged</h2>$(def_Table $ToolRows @("def_category","def_file","def_exists","def_status","def_size_bytes","def_sha12","def_source_path","def_staged_path") 160)</div>
<div class="sec wide"><h2>def File Matrix Preview</h2>$(def_Table $FileRows @("def_project","def_file_role","def_file_name","def_ext","def_status","def_size_bytes","def_sha12","def_path") 220)</div>
</div>

<div class="footer">Output: $(def_Html $def_RUN_DIR)<br/>Policy: No delete · No Stop-Process · No destructive cleanup · first-step scan only.</div>
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · INTEGRATION FIRSTSTEP PANORAMA · v0106 WORKER" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Prepare run directories"
    def_Progress 2 9 "Stage used tools"
    $toolRows = def_StageTools

    def_Progress 3 9 "Scan BASE files"
    $fileRows = def_ScanFiles

    def_Progress 4 9 "Extract parameters and engines"
    $ex = def_ExtractParams $fileRows
    $paramRows = @($ex.Parameters)
    $engineRows = @($ex.Engines)

    def_Progress 5 9 "Build conflict triage"
    $conflictRows = def_Conflicts $paramRows

    def_Progress 6 9 "Build five independent flow plan"
    $flowRows = def_FiveFlows
    $top10Rows = def_Top10Libs

    def_Progress 7 9 "Write CSV/JSON outputs"

    $p0 = @($conflictRows | Where-Object { $_.def_severity -eq "P0_DOMAIN_REVIEW" }).Count
    $p1 = @($conflictRows | Where-Object { $_.def_severity -eq "P1_PATH_REVIEW" }).Count
    $p2 = @($conflictRows | Where-Object { $_.def_severity -eq "P2_ENGINE_REVIEW" }).Count
    $p3 = @($conflictRows | Where-Object { $_.def_severity -match "P3" }).Count

    $canonicalAccept = @($paramRows | Where-Object { $_.def_group -notin @("PATH_IO","VISUAL_LOCK") }).Count
    $canonicalReview = @($paramRows | Where-Object { $_.def_group -in @("PATH_IO","VISUAL_LOCK") }).Count

    $summary = [ordered]@{
        Status = "VIA_INTEGRATION_FIRSTSTEP_v0106_READY"
        RunId = $def_RUN_ID
        Files = @($fileRows).Count
        Parameters = @($paramRows).Count
        CanonicalAccept = $canonicalAccept
        CanonicalReview = $canonicalReview
        P0Review = $p0
        P1Path = $p1
        P2Review = $p2
        P3Review = $p3
        Engines = @($engineRows).Count
        Tools = @($toolRows).Count
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
    }

    def_WriteCsv $toolRows (Join-Path $def_OUTPUT_DIR "VIA_UsedTools_Staged.csv")
    def_WriteCsv $fileRows (Join-Path $def_OUTPUT_DIR "VIA_FileMatrix.csv")
    def_WriteCsv $paramRows (Join-Path $def_OUTPUT_DIR "VIA_ParametersConsolidated_Registry.csv")
    def_WriteCsv $engineRows (Join-Path $def_OUTPUT_DIR "VIA_EngineMatrix.csv")
    def_WriteCsv $conflictRows (Join-Path $def_OUTPUT_DIR "VIA_ConflictTriageMatrix.csv")
    def_WriteCsv $flowRows (Join-Path $def_OUTPUT_DIR "VIA_FiveFlow_IntegrationPlan.csv")
    def_WriteCsv $top10Rows (Join-Path $def_OUTPUT_DIR "VIA_Top10_LocalFreeLibs_ByFunction.csv")

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_IntegrationFirstStep_Summary.json")
    def_WriteJson $toolRows (Join-Path $def_OUTPUT_DIR "VIA_UsedTools_Staged.json")
    def_WriteJson $fileRows (Join-Path $def_OUTPUT_DIR "VIA_FileMatrix.json")
    def_WriteJson $paramRows (Join-Path $def_OUTPUT_DIR "VIA_ParametersConsolidated_Registry.json")
    def_WriteJson $engineRows (Join-Path $def_OUTPUT_DIR "VIA_EngineMatrix.json")
    def_WriteJson $conflictRows (Join-Path $def_OUTPUT_DIR "VIA_ConflictTriageMatrix.json")
    def_WriteJson $flowRows (Join-Path $def_OUTPUT_DIR "VIA_FiveFlow_IntegrationPlan.json")
    def_WriteJson $top10Rows (Join-Path $def_OUTPUT_DIR "VIA_Top10_LocalFreeLibs_ByFunction.json")

    def_Progress 8 9 "Write one-page small-font HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_IntegrationFirstStep_Panorama_Report_v0106.html"
    def_Report $summary $toolRows $fileRows $paramRows $engineRows $conflictRows $flowRows $top10Rows $report

    def_Progress 9 9 "Complete"
    Write-Progress -Activity "VIA Integration FirstStep v0106 Worker" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA Integration FirstStep v0106 WORKER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status     : $($summary.Status)" -ForegroundColor Green
    Write-Host "Files      : $($summary.Files)" -ForegroundColor Gray
    Write-Host "Parameters : $($summary.Parameters)" -ForegroundColor Gray
    Write-Host "Engines    : $($summary.Engines)" -ForegroundColor Gray
    Write-Host "P0 Review  : $($summary.P0Review)" -ForegroundColor Yellow
    Write-Host "P1 Path    : $($summary.P1Path)" -ForegroundColor Yellow
    Write-Host "Report     : $report" -ForegroundColor Cyan
    Write-Host "Output     : $def_OUTPUT_DIR" -ForegroundColor Cyan

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
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No destructive cleanup executed." -ForegroundColor Yellow
    exit 1
}

