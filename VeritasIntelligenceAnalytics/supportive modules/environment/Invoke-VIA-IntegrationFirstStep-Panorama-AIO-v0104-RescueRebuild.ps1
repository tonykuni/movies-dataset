param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_DOWNLOADS_ROOT = "C:\Users\tonyk\Downloads",
    [int]$def_PARAM_MAX_FILE_READ_MB = 2,
    [int]$def_PARAM_MAX_SCAN_FILES = 5000,
    [switch]$def_PARAM_OPEN_HTML_REPORT = $true
)

$ErrorActionPreference = "Stop"

# =============================================================================
# def VIA · Integration FirstStep Panorama AIO · v0104 Rescue Rebuild
# Five independent flows · 15 PS accelerators · One-page small-font matrix report
# =============================================================================

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_FIRSTSTEP_v0104_RESCUE" -f (Get-Date -Format "yyyyMMdd_HHmmss")

$def_PARAM_VDF_ROOT = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_PARAM_RUN_ROOT = Join-Path $def_PARAM_VDF_ROOT "_integration_firststep_panorama"
$def_PARAM_RUN_DIR = Join-Path $def_PARAM_RUN_ROOT $def_RUN_ID
$def_PARAM_USED_TOOLS_DIR = Join-Path $def_PARAM_RUN_DIR "_used_tools"
$def_PARAM_OUTPUT_DIR = Join-Path $def_PARAM_RUN_DIR "output"
$def_PARAM_REPORT_DIR = Join-Path $def_PARAM_RUN_DIR "report"
$def_PARAM_LOG_DIR = Join-Path $def_PARAM_RUN_DIR "logs"

$def_PARAM_SUPPORTIVE_MODULES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_README.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_StaticValidation.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Read_Me_VeritasNexusCore.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
)

$def_PARAM_FUNCTIONAL_MODULES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\UnifiedSpec.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\Invoke-VeritasCodexNexus.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\GovernanceRegistry.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\LayoutRegistry.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VisualRegistry.json"
)

$def_PARAM_FIRSTSTEP_COMMANDS = @(
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v041-HistoryLensHotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v040.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v031-Hotfix (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-RedFinding-Triage-v01 (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-RedFinding-Triage-v01.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v031-Hotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v030.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-NexusToolBridge-Unified-v02.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v2.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v1.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v062-NullSafeStepSafe (1).ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v062-NullSafeStepSafe.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v061-BoolParamHotfix.ps1",
    "C:\Users\tonyk\Downloads\via_three_round_safe_convergence_spine.png",
    "C:\Users\tonyk\Downloads\VIA_EngineForge_Config.template.json",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v060.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v044-RiskTriageTrueProgress.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v043-CompletionAnchorEngine.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v042-SafeHtmlRendererHotfix.ps1"
)

$def_PS15_ACCELERATORS = @(
    "A01 ArrayList rows: avoid Generic.List type binding issue",
    "A02 Bounded file read: max MB per file",
    "A03 Extension filter: skip binary-heavy files",
    "A04 Run-isolated staging: copy tools only into RUN folder",
    "A05 No destructive command policy",
    "A06 No Stop-Process policy",
    "A07 No network execution in first-step scan",
    "A08 Path normalization and duplicate collapse",
    "A09 Regex timeout avoided by line-based extraction",
    "A10 Small-font one-page HTML matrix",
    "A11 Five-flow sequential gate to avoid Hydra risk",
    "A12 Source audit before engine bridge",
    "A13 P0/P1/P3 triage instead of treating all conflicts as fatal",
    "A14 JSON/CSV/HTML synchronized outputs",
    "A15 PowerShell remains open on failure"
)

function def_EnsureDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_Log {
    param(
        [string]$Level,
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath (Join-Path $def_PARAM_LOG_DIR "VIA_IntegrationFirstStep_v0104.log") -Value $line -Encoding UTF8
}

function def_ShowProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Activity,
        [string]$Status
    )
    $pct = [int](($Step / [Math]::Max(1, $Total)) * 100)
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
}

function def_GetSha12 {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.Substring(0, 12)
        }
    } catch {}
    return ""
}

function def_ReadTextBounded {
    param(
        [string]$Path,
        [int]$MaxMB = 2
    )

    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($item.Length -le 0) { return "" }

        $maxBytes = [Math]::Max(1024, $MaxMB * 1024 * 1024)
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

function def_ClassifyProject {
    param([string]$Name, [string]$Path)

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

function def_ClassifyRole {
    param([string]$Name, [string]$Ext)

    $s = $Name.ToLowerInvariant()

    if ($s -match "registry|schema|ssot") { return "REGISTRY" }
    if ($s -match "lock|freeze") { return "LOCK_REGISTRY" }
    if ($s -match "test|validation|verify|smoke|lint") { return "TEST_VALIDATION" }
    if ($s -match "report|summary|panorama") { return "REPORT" }
    if ($s -match "manifest|packlist") { return "MANIFEST" }
    if ($s -match "config|template|spec") { return "CONFIG_TEMPLATE" }
    if ($s -match "engine|forge|fetch|router|orchestrator") { return "ENGINE_MODULE" }
    if ($Ext -in @(".html", ".png", ".svg", ".css")) { return "UI_VISUAL" }
    if ($Ext -in @(".py", ".ps1", ".js", ".ts")) { return "SOURCE" }

    return "SOURCE"
}

function def_ClassifyParamGroup {
    param([string]$Key, [string]$Value)

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

function def_ExtractParamsFromText {
    param(
        [string]$Text,
        [string]$Project,
        [string]$Role,
        [string]$FileName,
        [string]$FileId
    )

    $rows = [System.Collections.ArrayList]::new()

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return @($rows)
    }

    $lines = $Text -split "`r?`n"
    $maxLines = [Math]::Min($lines.Count, 2000)

    for ($i = 0; $i -lt $maxLines; $i++) {
        $line = [string]$lines[$i]
        $trim = $line.Trim()

        if ([string]::IsNullOrWhiteSpace($trim)) {
            continue
        }

        $key = $null
        $value = $null
        $sourceType = "text_line"

        if ($trim -match '^\s*(def_PARAM_[A-Za-z0-9_]+)\s*=') {
            $key = $matches[1]; $value = $trim; $sourceType = "ps_param"
        } elseif ($trim -match '^\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $key = $matches[1]; $value = $trim; $sourceType = "ps_assignment"
        } elseif ($trim -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $key = $matches[1]; $value = $trim; $sourceType = "python_assignment"
        } elseif ($trim -match '^\s*function\s+([A-Za-z0-9_\-]+)') {
            $key = "function." + $matches[1]; $value = $matches[1]; $sourceType = "function"
        } elseif ($trim -match '^\s*def\s+([A-Za-z0-9_]+)\s*\(') {
            $key = "function." + $matches[1]; $value = $matches[1]; $sourceType = "python_function"
        } elseif ($trim -match '^\s*class\s+([A-Za-z0-9_]+)') {
            $key = "class." + $matches[1]; $value = $matches[1]; $sourceType = "python_class"
        } elseif ($trim -match '^\s*import\s+(.+)$') {
            $key = "import"; $value = $matches[1]; $sourceType = "python_import"
        } elseif ($trim -match '^\s*from\s+(.+?)\s+import\s+(.+)$') {
            $key = "import"; $value = $matches[1] + "." + $matches[2]; $sourceType = "python_import"
        } elseif ($trim -match '^\s*["'']?([A-Za-z0-9_\.\-]+)["'']?\s*:\s*(.+?)[,\}]?\s*$') {
            $key = $matches[1]; $value = $matches[2]; $sourceType = "json_yaml_key"
        } elseif ($trim -match '<h([1-6])[^>]*>(.*?)</h\1>') {
            $key = "heading_" + $matches[1]; $value = ($matches[2] -replace '<[^>]+>', '').Trim(); $sourceType = "html_heading"
        } else {
            continue
        }

        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $preview = [string]$value
            if ($preview.Length -gt 160) { $preview = $preview.Substring(0, 160) + "..." }

            $group = def_ClassifyParamGroup -Key $key -Value $preview

            $row = [pscustomobject][ordered]@{
                def_project       = [string]$Project
                def_file_role     = [string]$Role
                def_group         = [string]$group
                def_key           = [string]$key
                def_value_preview = [string]$preview
                def_source_type   = [string]$sourceType
                def_file_id       = [string]$FileId
                def_file_name     = [string]$FileName
                def_line          = [string]($i + 1)
            }

            [void]$rows.Add($row)
        }
    }

    return @($rows)
}

function def_WriteCsv {
    param(
        [array]$Rows,
        [string]$Path
    )
    if (-not $Rows) {
        @() | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function def_WriteJson {
    param(
        $Object,
        [string]$Path,
        [int]$Depth = 8
    )
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_HtmlEncode {
    param([string]$Text)
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function def_TableHtml {
    param(
        [array]$Rows,
        [string[]]$Cols,
        [int]$Max = 160
    )

    $html = New-Object System.Text.StringBuilder
    [void]$html.Append("<table><thead><tr>")
    foreach ($c in $Cols) {
        [void]$html.Append("<th>$(def_HtmlEncode $c)</th>")
    }
    [void]$html.Append("</tr></thead><tbody>")

    $take = @($Rows | Select-Object -First $Max)
    foreach ($r in $take) {
        [void]$html.Append("<tr>")
        foreach ($c in $Cols) {
            $v = ""
            try { $v = [string]$r.$c } catch { $v = "" }
            if ($v.Length -gt 180) { $v = $v.Substring(0, 180) + "..." }
            [void]$html.Append("<td>$(def_HtmlEncode $v)</td>")
        }
        [void]$html.Append("</tr>")
    }

    [void]$html.Append("</tbody></table>")
    return $html.ToString()
}

function def_StageUsedTools {
    $rows = [System.Collections.ArrayList]::new()

    $sets = @(
        [pscustomobject]@{ category = "supportive_modules"; paths = @($def_PARAM_SUPPORTIVE_MODULES) },
        [pscustomobject]@{ category = "functional_modules"; paths = @($def_PARAM_FUNCTIONAL_MODULES) },
        [pscustomobject]@{ category = "firststep_commands"; paths = @($def_PARAM_FIRSTSTEP_COMMANDS) }
    )

    foreach ($set in $sets) {
        $category = [string]$set.category
        $catDir = Join-Path $def_PARAM_USED_TOOLS_DIR $category
        def_EnsureDirectory -Path $catDir

        foreach ($srcRaw in @($set.paths)) {
            $src = ([string]$srcRaw).Trim().Trim('"')
            if ([string]::IsNullOrWhiteSpace($src)) { continue }

            $exists = Test-Path -LiteralPath $src
            $leaf = Split-Path -Leaf $src
            if ([string]::IsNullOrWhiteSpace($leaf)) {
                $leaf = "UNKNOWN_TOOL_{0}.txt" -f ([guid]::NewGuid().ToString("N").Substring(0, 8))
            }

            $dst = Join-Path $catDir $leaf
            $status = "MISSING"
            $msg = "Source file missing."
            $sha = ""
            $sizeBytes = ""
            $modified = ""
            $stagedPath = ""

            if ($exists) {
                try {
                    $it = Get-Item -LiteralPath $src -ErrorAction Stop
                    $sha = def_GetSha12 -Path $src
                    $sizeBytes = [string]$it.Length
                    $modified = $it.LastWriteTime.ToString("s")
                    Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
                    $status = "COPIED_READONLY_SOURCE"
                    $msg = "Copied to run-isolated used tools folder."
                    $stagedPath = $dst
                } catch {
                    $status = "COPY_WARN"
                    $msg = $_.Exception.Message
                }
            }

            [void]$rows.Add([pscustomobject][ordered]@{
                def_category      = [string]$category
                def_file          = [string]$leaf
                def_source_path   = [string]$src
                def_staged_path   = [string]$stagedPath
                def_exists        = [string]$exists
                def_status        = [string]$status
                def_size_bytes    = [string]$sizeBytes
                def_modified_time = [string]$modified
                def_sha12         = [string]$sha
                def_message       = [string]$msg
            })
        }
    }

    return @($rows)
}

function def_ScanBaseFiles {
    $rows = [System.Collections.ArrayList]::new()

    $roots = @(
        $def_PARAM_VIA_ROOT,
        $def_PARAM_DOWNLOADS_ROOT
    ) | Select-Object -Unique

    $skipDirRegex = '\\(__pycache__|\.git|node_modules|\.venv|venv|_envs|dist|build)\\'
    $allowedExt = @(".ps1", ".py", ".json", ".md", ".html", ".js", ".ts", ".csv", ".yaml", ".yml", ".log", ".txt", ".docx", ".png")

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }

        $files = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch $skipDirRegex -and
                $allowedExt -contains $_.Extension.ToLowerInvariant()
            } |
            Select-Object -First $def_PARAM_MAX_SCAN_FILES

        foreach ($f in $files) {
            $proj = def_ClassifyProject -Name $f.Name -Path $f.FullName
            $role = def_ClassifyRole -Name $f.Name -Ext $f.Extension
            $sha = def_GetSha12 -Path $f.FullName
            $status = "OK"

            if ($f.Length -eq 0) { $status = "ZERO_BYTE_REVIEW" }
            elseif ($f.Length -lt 20) { $status = "TINY_FILE_REVIEW" }

            [void]$rows.Add([pscustomobject][ordered]@{
                def_project       = [string]$proj
                def_file_role     = [string]$role
                def_file_name     = [string]$f.Name
                def_ext           = [string]$f.Extension
                def_status        = [string]$status
                def_size_bytes    = [string]$f.Length
                def_modified_time = [string]$f.LastWriteTime.ToString("s")
                def_sha12         = [string]$sha
                def_path          = [string]$f.FullName
            })
        }
    }

    return @($rows)
}

function def_ParameterConsolidation {
    param([array]$FileRows)

    $params = [System.Collections.ArrayList]::new()
    $engineRows = [System.Collections.ArrayList]::new()

    $textExt = @(".ps1", ".py", ".json", ".md", ".html", ".js", ".ts", ".yaml", ".yml", ".txt", ".log", ".csv")

    $idx = 0
    foreach ($fr in $FileRows) {
        $idx++
        if (($idx % 100) -eq 0) {
            Write-Progress -Activity "Parameter consolidation" -Status "Scanning $idx / $($FileRows.Count)" -PercentComplete ([int](($idx / [Math]::Max(1, $FileRows.Count)) * 100))
        }

        $ext = ([string]$fr.def_ext).ToLowerInvariant()
        if (-not ($textExt -contains $ext)) {
            continue
        }

        $text = def_ReadTextBounded -Path $fr.def_path -MaxMB $def_PARAM_MAX_FILE_READ_MB
        if ([string]::IsNullOrWhiteSpace($text)) {
            continue
        }

        $fileId = "{0}::{1}" -f $fr.def_file_name, $fr.def_sha12
        $extracted = def_ExtractParamsFromText -Text $text -Project $fr.def_project -Role $fr.def_file_role -FileName $fr.def_file_name -FileId $fileId

        foreach ($p in $extracted) {
            [void]$params.Add($p)
        }

        $engineCount = @($extracted | Where-Object { $_.def_group -eq "ENGINE" -or $_.def_source_type -match "function|class|import" }).Count
        if ($engineCount -gt 0 -or $fr.def_file_role -eq "ENGINE_MODULE") {
            [void]$engineRows.Add([pscustomobject][ordered]@{
                def_project            = [string]$fr.def_project
                def_engine_file        = [string]$fr.def_file_name
                def_file_role          = [string]$fr.def_file_role
                def_engine_param_count = [string]$engineCount
                def_total_param_count  = [string]@($extracted).Count
                def_path               = [string]$fr.def_path
            })
        }
    }

    Write-Progress -Activity "Parameter consolidation" -Completed

    return [pscustomobject]@{
        parameters = @($params)
        engines    = @($engineRows)
    }
}

function def_BuildConflictTriage {
    param([array]$Params)

    $rows = [System.Collections.ArrayList]::new()

    $groups = $Params | Group-Object def_key
    foreach ($g in $groups) {
        $items = @($g.Group)
        if ($items.Count -lt 2) { continue }

        $values = @($items | ForEach-Object { [string]$_.def_value_preview } | Select-Object -Unique)
        if ($values.Count -lt 2) { continue }

        $key = [string]$g.Name
        $groups2 = @($items | ForEach-Object { [string]$_.def_group } | Select-Object -Unique)
        $files = @($items | ForEach-Object { [string]$_.def_file_name } | Select-Object -Unique | Select-Object -First 8)

        $severity = "P3_NOISE_REFERENCE"

        if ($key -match "ticker|schema|field|unit|policy|hardgate|owner_engine|source_module|macro|sentiment|fred|yfinance|akshare") {
            $severity = "P0_DOMAIN_REVIEW"
        } elseif ($key -match "path|dir|root|file|output|input") {
            $severity = "P1_PATH_REVIEW"
        } elseif ($key -match "color|font|css|html|heading|line|padding|margin|background|border|display|x|y|w|h|id|name") {
            $severity = "P3_UI_OR_NOISE"
        } elseif ($key -match "import|function|class|version|generated") {
            $severity = "P2_ENGINE_REVIEW"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_severity        = [string]$severity
            def_normalized_key  = [string]$key
            def_occurrences     = [string]$items.Count
            def_distinct_values = [string]$values.Count
            def_groups          = [string](($groups2 | Select-Object -First 8) -join ";")
            def_sample_values   = [string](($values | Select-Object -First 6) -join " || ")
            def_sample_files    = [string]($files -join "; ")
        })
    }

    return @($rows | Sort-Object def_severity, {[int]$_.def_distinct_values} -Descending)
}

function def_BuildFlowPlan {
    param([array]$FileRows, [array]$ParamRows, [array]$ConflictRows, [array]$EngineRows)

    $rows = [System.Collections.ArrayList]::new()

    [void]$rows.Add([pscustomobject][ordered]@{
        def_flow = "FLOW_01_SUPPORTIVE_TOOLS"
        def_scope = "supportive modules + NexusCore + SafePolyglot"
        def_action = "Run-isolated staging, source audit, no direct mutation."
        def_parallel_safe = "YES"
        def_hydra_risk = "LOW"
        def_next_step = "Confirm missing supportive files, then connect bridge inputs."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_flow = "FLOW_02_FUNCTIONAL_MODULES"
        def_scope = "UnifiedSpec / GovernanceRegistry / LayoutRegistry / VisualRegistry / CodexNexus"
        def_action = "Audit schema existence and unify registry references."
        def_parallel_safe = "YES_WITH_READONLY"
        def_hydra_risk = "MEDIUM"
        def_next_step = "Patch only registry pointers, not engine internals."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_flow = "FLOW_03_PARAMETER_SSOT"
        def_scope = "Canonical parameter registry"
        def_action = "Accept clear canonical keys; isolate P0 domain and P1 path review."
        def_parallel_safe = "YES"
        def_hydra_risk = "LOW"
        def_next_step = "Build SSOT JSON from accepted parameter groups."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_flow = "FLOW_04_ENGINE_BRIDGE"
        def_scope = "EngineForge / VDF / VRN / VPF / VIA engines"
        def_action = "Map engine files, function/class inventory, router entry candidates."
        def_parallel_safe = "NO_FOR_WRITE_YES_FOR_SCAN"
        def_hydra_risk = "MEDIUM"
        def_next_step = "Only generate bridge adapters after AST smoke test."
    })

    [void]$rows.Add([pscustomobject][ordered]@{
        def_flow = "FLOW_05_UI_REPORT_CLOSEOUT"
        def_scope = "One interface, HTML UI, visual lock, small professional font"
        def_action = "Consolidate report, compress table text, equal-height cards."
        def_parallel_safe = "YES"
        def_hydra_risk = "LOW"
        def_next_step = "Open one-page report and review P0/P1 before any repair."
    })

    return @($rows)
}

function def_BuildTop10Libs {
    $rows = [System.Collections.ArrayList]::new()

    $matrix = @(
        @("PowerShell Orchestration","PowerShell","Pester; PSScriptAnalyzer; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; BurntToast; PSReadLine; CompletionPredictor; Microsoft.PowerShell.SecretManagement"),
        @("Python Data Engine","Python","pandas; polars; pyarrow; duckdb; numpy; pydantic; requests; httpx; tenacity; rich"),
        @("Python Market Data","Python","yfinance; akshare; pandas-datareader; fredapi; pandasdmx; eurostat; exchange-calendars; pandas-market-calendars; curl_cffi; beautifulsoup4"),
        @("Python Static Analysis","Python","ast; libcst; parso; rope; ruff; mypy; pyflakes; bandit; radon; vulture"),
        @("HTML UI","HTML/CSS/JS","Plotly; D3; Apache ECharts; Tabulator; DataTables; Grid.js; PapaParse; Fuse.js; Marked; Mermaid"),
        @("Node UI Test","JavaScript","playwright; vitest; eslint; prettier; jsdom; axe-core; lighthouse; chart.js; papaparse; fast-glob"),
        @("Registry/Schema","JSON/YAML","ajv; jsonschema; pydantic; ruamel.yaml; yq; jq; jsonlines; frictionless; csvkit; duckdb"),
        @("Document/PDF","Python","PyMuPDF; pdfplumber; pypdf; camelot; tabula-py; pdfminer.six; openpyxl; python-docx; beautifulsoup4; lxml"),
        @("Visualization","Python","matplotlib; plotly; altair; bokeh; pygal; networkx; graphviz; folium; squarify; seaborn"),
        @("Acceleration/Safety","Mixed","joblib; concurrent.futures; asyncio; tenacity; diskcache; sqlite; duckdb; tqdm; rich; psutil")
    )

    foreach ($m in $matrix) {
        [void]$rows.Add([pscustomobject][ordered]@{
            def_function_area = $m[0]
            def_language = $m[1]
            def_top10_local_free_libs = $m[2]
        })
    }

    return @($rows)
}

function def_WriteHtmlReport {
    param(
        [hashtable]$Summary,
        [array]$ToolRows,
        [array]$FileRows,
        [array]$ProjectCounts,
        [array]$GroupCounts,
        [array]$RoleCounts,
        [array]$EngineRows,
        [array]$ConflictRows,
        [array]$FlowRows,
        [array]$Top10Rows,
        [string]$ReportPath
    )

    $cards = @(
        @("Status", $Summary.Status),
        @("Files", $Summary.Files),
        @("Parameters", $Summary.Parameters),
        @("Canonical", $Summary.Canonical),
        @("P0 Review", $Summary.P0Review),
        @("P1 Path", $Summary.P1Path),
        @("Engines", $Summary.Engines),
        @("Tools", $Summary.Tools)
    )

    $cardHtml = ""
    foreach ($c in $cards) {
        $cardHtml += "<div class='card'><div class='k'>$(def_HtmlEncode $c[0])</div><div class='v'>$(def_HtmlEncode ([string]$c[1]))</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>VIA Integration FirstStep Panorama v0104</title>
<style>
:root{
  --bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;
  --sky:#8fb8c8;--blue:#4c72b0;--red:#c96b5a;--green:#5a9e6f;--amber:#c4943a;
}
*{box-sizing:border-box}
body{
  margin:0;background:radial-gradient(circle at 12% 8%,rgba(143,184,200,.18),transparent 26%),
  radial-gradient(circle at 88% 12%,rgba(196,148,58,.10),transparent 28%),var(--bg);
  color:var(--ink);
  font-family:"Microsoft JhengHei","Noto Sans TC",Arial,sans-serif;
  font-size:10px;line-height:1.42;
}
.wrap{max-width:1680px;margin:0 auto;padding:20px}
.hero{display:flex;justify-content:space-between;gap:18px;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:14px}
h1{font-size:17px;margin:0;font-weight:650;letter-spacing:.02em}
.sub{font-size:10px;color:var(--mut);margin-top:4px}
.badge{font-family:Consolas,monospace;font-size:9px;border:1px solid var(--line);padding:5px 8px;border-radius:999px;background:rgba(255,255,255,.65)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;margin:10px 0 14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 9px;min-height:54px}
.card .k{font-size:9px;color:var(--mut)}
.card .v{font-size:15px;font-weight:650;margin-top:4px;font-family:Consolas,monospace}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:stretch}
.section{background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:12px;padding:10px;min-height:260px;overflow:hidden}
.section.wide{grid-column:1 / -1}
h2{font-size:11px;margin:0 0 8px;font-weight:650}
.note{color:var(--mut);font-size:9.5px;margin:6px 0 9px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:9px}
th,td{border-bottom:1px solid #ebe8df;padding:4px 5px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{position:sticky;top:0;background:#f1efe8;color:#555149;text-align:left;font-weight:650}
td{color:#2f2d28}
tr:hover td{background:#faf8f1}
.pill{display:inline-block;border-radius:999px;padding:2px 6px;border:1px solid var(--line);background:#fff;font-size:9px}
.footer{margin-top:14px;color:var(--mut);font-size:9px}
@media(max-width:1100px){.cards{grid-template-columns:repeat(4,1fr)}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div>
      <h1>def VIA Final Parameters One Interface · Integration FirstStep Panorama v0104</h1>
      <div class="sub">Five independent flows · 15 PowerShell accelerators · Canonical parameter registry · Conflict triage · EngineForge/Nexus bridge</div>
    </div>
    <div class="badge">$($Summary.RunId)</div>
  </div>

  <div class="cards">$cardHtml</div>

  <div class="section wide">
    <h2>def Overview</h2>
    <div class="note">
      判斷：上一輪 Conflicts 不應直接視為真錯誤；HTML/CSS/JS/import/path/heading 多數屬於 P3 noise reference。
      本版先做第一步全景現況、工具分流、P0/P1/P2/P3 triage、五流程後續整合計畫。沒有刪除、沒有 Stop-Process、沒有修原始工具。
    </div>
    <div class="note">
      Canonical Accept: $($Summary.CanonicalAccept) · Canonical Review: $($Summary.CanonicalReview) · P0 Domain: $($Summary.P0Review) · P1 Path: $($Summary.P1Path) · P2 Engine: $($Summary.P2Engine) · P3 Noise/UI: $($Summary.P3Noise)
    </div>
  </div>

  <div class="grid">
    <div class="section">
      <h2>def Five Independent Flows</h2>
      $(def_TableHtml -Rows $FlowRows -Cols @("def_flow","def_scope","def_action","def_parallel_safe","def_hydra_risk","def_next_step") -Max 20)
    </div>

    <div class="section">
      <h2>def 15 PowerShell Accelerators</h2>
      <table><thead><tr><th>def_order</th><th>def_accelerator</th></tr></thead><tbody>
      $(
        $tmp = ""
        for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
            $tmp += "<tr><td>$($i+1)</td><td>$(def_HtmlEncode $def_PS15_ACCELERATORS[$i])</td></tr>"
        }
        $tmp
      )
      </tbody></table>
    </div>

    <div class="section">
      <h2>def Project Counts</h2>
      $(def_TableHtml -Rows $ProjectCounts -Cols @("Name","Count") -Max 40)
    </div>

    <div class="section">
      <h2>def Parameter Groups</h2>
      $(def_TableHtml -Rows $GroupCounts -Cols @("Name","Count") -Max 40)
    </div>

    <div class="section">
      <h2>def File Roles</h2>
      $(def_TableHtml -Rows $RoleCounts -Cols @("Name","Count") -Max 40)
    </div>

    <div class="section">
      <h2>def Top 10 Local Free Libs by Function</h2>
      $(def_TableHtml -Rows $Top10Rows -Cols @("def_function_area","def_language","def_top10_local_free_libs") -Max 40)
    </div>

    <div class="section wide">
      <h2>def Conflict Triage Matrix</h2>
      $(def_TableHtml -Rows $ConflictRows -Cols @("def_severity","def_normalized_key","def_occurrences","def_distinct_values","def_groups","def_sample_values","def_sample_files") -Max 160)
    </div>

    <div class="section wide">
      <h2>def Engine Matrix</h2>
      $(def_TableHtml -Rows $EngineRows -Cols @("def_project","def_engine_file","def_file_role","def_engine_param_count","def_total_param_count","def_path") -Max 160)
    </div>

    <div class="section wide">
      <h2>def Used Tools Staged</h2>
      $(def_TableHtml -Rows $ToolRows -Cols @("def_category","def_file","def_exists","def_status","def_size_bytes","def_sha12","def_source_path","def_staged_path") -Max 120)
    </div>

    <div class="section wide">
      <h2>def File Matrix Preview</h2>
      $(def_TableHtml -Rows $FileRows -Cols @("def_project","def_file_role","def_file_name","def_ext","def_status","def_size_bytes","def_sha12","def_path") -Max 180)
    </div>
  </div>

  <div class="footer">
    Output root: $(def_HtmlEncode $def_PARAM_RUN_DIR)<br/>
    Policy: No delete · No Stop-Process · No destructive cleanup · First-step scan and report only.
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
    Write-Host "def VIA · INTEGRATION FIRSTSTEP PANORAMA · v0104 RESCUE REBUILD" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    foreach ($d in @($def_PARAM_RUN_DIR,$def_PARAM_USED_TOOLS_DIR,$def_PARAM_OUTPUT_DIR,$def_PARAM_REPORT_DIR,$def_PARAM_LOG_DIR)) {
        def_EnsureDirectory -Path $d
    }

    def_ShowProgress -Step 1 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Prepare run directories"

    def_ShowProgress -Step 2 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Stage used tools into run folder"
    $toolRows = def_StageUsedTools

    def_ShowProgress -Step 3 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Scan BASE files panorama"
    $fileRows = def_ScanBaseFiles

    def_ShowProgress -Step 4 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Extract and consolidate parameters"
    $pc = def_ParameterConsolidation -FileRows $fileRows
    $paramRows = @($pc.parameters)
    $engineRows = @($pc.engines)

    def_ShowProgress -Step 5 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Build conflict triage"
    $conflictRows = def_BuildConflictTriage -Params $paramRows

    def_ShowProgress -Step 6 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Build five-flow integration plan"
    $flowRows = def_BuildFlowPlan -FileRows $fileRows -ParamRows $paramRows -ConflictRows $conflictRows -EngineRows $engineRows
    $top10Rows = def_BuildTop10Libs

    def_ShowProgress -Step 7 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Write CSV and JSON outputs"

    $projectCounts = @($fileRows | Group-Object def_project | Sort-Object Count -Descending | Select-Object Name, Count)
    $groupCounts = @($paramRows | Group-Object def_group | Sort-Object Count -Descending | Select-Object Name, Count)
    $roleCounts = @($fileRows | Group-Object def_file_role | Sort-Object Count -Descending | Select-Object Name, Count)

    $p0 = @($conflictRows | Where-Object { $_.def_severity -eq "P0_DOMAIN_REVIEW" }).Count
    $p1 = @($conflictRows | Where-Object { $_.def_severity -eq "P1_PATH_REVIEW" }).Count
    $p2 = @($conflictRows | Where-Object { $_.def_severity -eq "P2_ENGINE_REVIEW" }).Count
    $p3 = @($conflictRows | Where-Object { $_.def_severity -match "P3" }).Count

    $canonicalAccept = @($paramRows | Where-Object { $_.def_group -notin @("PATH_IO","VISUAL_LOCK") }).Count
    $canonicalReview = @($paramRows | Where-Object { $_.def_group -in @("PATH_IO","VISUAL_LOCK") }).Count

    $summary = [ordered]@{
        Status = "VIA_INTEGRATION_FIRSTSTEP_v0104_READY"
        RunId = $def_RUN_ID
        Files = @($fileRows).Count
        Parameters = @($paramRows).Count
        Canonical = $canonicalAccept + $canonicalReview
        CanonicalAccept = $canonicalAccept
        CanonicalReview = $canonicalReview
        P0Review = $p0
        P1Path = $p1
        P2Engine = $p2
        P3Noise = $p3
        Engines = @($engineRows).Count
        Tools = @($toolRows).Count
        OutputDir = $def_PARAM_OUTPUT_DIR
        ReportDir = $def_PARAM_REPORT_DIR
        Policy = "No delete; No Stop-Process; No destructive cleanup; First-step scan only."
    }

    def_WriteCsv -Rows $toolRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_UsedTools_Staged.csv")
    def_WriteCsv -Rows $fileRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_FileMatrix.csv")
    def_WriteCsv -Rows $paramRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_ParametersConsolidated_Registry.csv")
    def_WriteCsv -Rows $engineRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_EngineMatrix.csv")
    def_WriteCsv -Rows $conflictRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_ConflictTriageMatrix.csv")
    def_WriteCsv -Rows $flowRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_FiveFlow_IntegrationPlan.csv")
    def_WriteCsv -Rows $top10Rows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_Top10_LocalFreeLibs_ByFunction.csv")

    def_WriteJson -Object $summary -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_IntegrationFirstStep_Summary.json") -Depth 8
    def_WriteJson -Object $toolRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_UsedTools_Staged.json") -Depth 8
    def_WriteJson -Object $fileRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_FileMatrix.json") -Depth 8
    def_WriteJson -Object $paramRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_ParametersConsolidated_Registry.json") -Depth 8
    def_WriteJson -Object $engineRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_EngineMatrix.json") -Depth 8
    def_WriteJson -Object $conflictRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_ConflictTriageMatrix.json") -Depth 8
    def_WriteJson -Object $flowRows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_FiveFlow_IntegrationPlan.json") -Depth 8
    def_WriteJson -Object $top10Rows -Path (Join-Path $def_PARAM_OUTPUT_DIR "VIA_Top10_LocalFreeLibs_ByFunction.json") -Depth 8

    def_ShowProgress -Step 8 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Write one-page HTML report"

    $reportHtml = Join-Path $def_PARAM_REPORT_DIR "VIA_IntegrationFirstStep_Panorama_Report_v0104.html"

    def_WriteHtmlReport `
        -Summary $summary `
        -ToolRows $toolRows `
        -FileRows $fileRows `
        -ProjectCounts $projectCounts `
        -GroupCounts $groupCounts `
        -RoleCounts $roleCounts `
        -EngineRows $engineRows `
        -ConflictRows $conflictRows `
        -FlowRows $flowRows `
        -Top10Rows $top10Rows `
        -ReportPath $reportHtml

    def_ShowProgress -Step 9 -Total 9 -Activity "VIA Integration FirstStep v0104" -Status "Complete"

    Write-Progress -Activity "VIA Integration FirstStep v0104" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA Integration FirstStep v0104 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status     : $($summary.Status)" -ForegroundColor Green
    Write-Host "Files      : $($summary.Files)" -ForegroundColor Gray
    Write-Host "Parameters : $($summary.Parameters)" -ForegroundColor Gray
    Write-Host "Engines    : $($summary.Engines)" -ForegroundColor Gray
    Write-Host "P0 Review  : $($summary.P0Review)" -ForegroundColor Yellow
    Write-Host "P1 Path    : $($summary.P1Path)" -ForegroundColor Yellow
    Write-Host "Report     : $reportHtml" -ForegroundColor Cyan
    Write-Host "Output     : $def_PARAM_OUTPUT_DIR" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try {
            Start-Process -FilePath $reportHtml
        } catch {
            Write-Host "[WARN] Could not auto-open HTML report: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    return [pscustomobject]$summary
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No destructive cleanup executed." -ForegroundColor Yellow
}
