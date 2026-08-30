#requires -Version 7.0

# =============================================================================
# def PARAMETERS
# =============================================================================

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
$def_PARAM_RUN_ID = "RUN_{0}_VIA_INTEGRATION_FIRSTSTEP_PANORAMA_v0104" -f (Get-Date -Format "yyyyMMdd_HHmmss")

$def_PARAM_BASE_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_PARAM_DOWNLOADS_ROOT = "C:\Users\tonyk\Downloads"
$def_PARAM_VDF_DIR = Join-Path $def_PARAM_BASE_ROOT "functional modules\VDF"

$def_PARAM_PREVIOUS_ONE_INTERFACE_ROOT = Join-Path $def_PARAM_VDF_DIR "_vdf_final_parameters_one_interface"

$def_PARAM_WORK_DIR = Join-Path $def_PARAM_VDF_DIR "_vdf_integration_firststep_panorama"
$def_PARAM_RUN_DIR = Join-Path $def_PARAM_WORK_DIR "runs\$def_PARAM_RUN_ID"
$def_PARAM_USED_TOOLS_DIR = Join-Path $def_PARAM_RUN_DIR "_used_tools"
$def_PARAM_OUTPUT_DIR = Join-Path $def_PARAM_RUN_DIR "output"
$def_PARAM_REPORT_DIR = Join-Path $def_PARAM_RUN_DIR "report"
$def_PARAM_LOG_DIR = Join-Path $def_PARAM_RUN_DIR "logs"
$def_PARAM_POINTER_DIR = Join-Path $def_PARAM_WORK_DIR "pointer"

$def_PARAM_LOG_FILE = Join-Path $def_PARAM_LOG_DIR "VIA_IntegrationFirstStep_Panorama.log"

$def_PARAM_FILE_MATRIX_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_Base_FileMatrix.csv"
$def_PARAM_TOOL_STAGING_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_UsedTools_StagingMatrix.csv"
$def_PARAM_SUBSYSTEM_FLOW_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_Subsystem_FiveFlowMatrix.csv"
$def_PARAM_INTEGRATION_PLAN_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_Integration_ActionPlan.csv"
$def_PARAM_TOP10_LIBS_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
$def_PARAM_PS15_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_PS15_AcceleratorMatrix.csv"
$def_PARAM_PREVIOUS_STATE_CSV = Join-Path $def_PARAM_OUTPUT_DIR "VIA_Previous_v0102_StateMatrix.csv"
$def_PARAM_SUMMARY_JSON = Join-Path $def_PARAM_OUTPUT_DIR "VIA_IntegrationFirstStep_Summary.json"
$def_PARAM_REPORT_HTML = Join-Path $def_PARAM_REPORT_DIR "VIA_IntegrationFirstStep_Panorama_Report.html"
$def_PARAM_ACTIVE_POINTER = Join-Path $def_PARAM_POINTER_DIR "VIA_IntegrationFirstStep_ActivePointer.json"

$def_PARAM_ENABLE_OPEN_REPORT = $true
$def_PARAM_ENABLE_CHILD_EXECUTION = $false
$def_PARAM_ENABLE_REPAIR = $false
$def_PARAM_MAX_READ_BYTES = 3145728
$def_PARAM_SCAN_EXTENSIONS = @(".ps1",".py",".json",".md",".html",".js",".csv",".yaml",".yml",".txt",".png",".jpg",".jpeg",".webp",".docx")
$def_PARAM_HTML_TABLE_LIMIT = 2500

# v0104 E1: exclude self-generated run outputs and noise dirs from the panoramic scan,
# so Base Files reflects real source — not re-scanned reports/logs/used-tools copies.
$def_PARAM_SCAN_EXCLUDE_REGEX = @(
    "\\_vdf_[^\\]*\\",
    "\\_vrn_[^\\]*\\",
    "\\runs\\",
    "\\_used_tools\\",
    "\\report\\",
    "\\reports\\",
    "\\logs\\",
    "\\output\\",
    "\\outputs\\",
    "\\pointer\\",
    "\\__pycache__\\",
    "\\node_modules\\",
    "\\\.git\\",
    "\\\.venv\\",
    "\\envs\\"
)

$def_PARAM_SUPPORTIVE_MODULES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_README.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_StaticValidation.json"
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
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v061-BoolParamHotfix.ps1",
    "C:\Users\tonyk\Downloads\via_three_round_safe_convergence_spine.png",
    "C:\Users\tonyk\Downloads\VIA_EngineForge_Config.template.json",
    "C:\Users\tonyk\Downloads\Invoke-VIA-UltimateEngineForge-AIO-v060.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v044-RiskTriageTrueProgress.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v043-CompletionAnchorEngine.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-MultiProject-PanoramaSync-AIO-v042-SafeHtmlRendererHotfix.ps1"
)

$def_PARAM_PROJECT_ORDER = @("VIA","VDF","VRN","VIS","VEF","VPF","VHS","VPL","LL34","UNKNOWN")

# =============================================================================
# def BASIC UTILITIES
# =============================================================================

function def_EnsureDirectory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_WriteLine {
    param(
        [string]$Level,
        [string]$Message
    )

    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[{0}] [{1}] {2}" -f $ts, $Level, $Message

    switch ($Level) {
        "OK" { Write-Host $line -ForegroundColor Green }
        "WARN" { Write-Host $line -ForegroundColor Yellow }
        "FAIL" { Write-Host $line -ForegroundColor Red }
        "RUN" { Write-Host $line -ForegroundColor Cyan }
        default { Write-Host $line }
    }

    if (Test-Path -LiteralPath $def_PARAM_LOG_DIR) {
        Add-Content -LiteralPath $def_PARAM_LOG_FILE -Value $line -Encoding UTF8
    }
}

function def_ShowProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Status
    )

    $pct = [math]::Round(($Step / [math]::Max($Total, 1)) * 100, 0)
    Write-Progress -Id 1 -Activity "VIA Integration FirstStep Panorama" -Status $Status -PercentComplete $pct
    def_WriteLine "RUN" ("[{0}/{1}] {2}" -f $Step, $Total, $Status)
}

function def_WriteJson {
    param(
        [object]$Object,
        [string]$Path,
        [int]$Depth = 100
    )

    def_EnsureDirectory -Path (Split-Path -Parent $Path)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_ExportCsvSafe {
    param(
        [object[]]$Rows,
        [string]$Path
    )

    def_EnsureDirectory -Path (Split-Path -Parent $Path)

    if ($null -eq $Rows) {
        $Rows = @()
    }

    @($Rows) | Export-Csv -LiteralPath $Path -Encoding UTF8 -NoTypeInformation
}

function def_ImportCsvSafe {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    try {
        return @(Import-Csv -LiteralPath $Path -Encoding UTF8)
    } catch {
        def_WriteLine "WARN" "CSV read failed: $Path · $($_.Exception.Message)"
        return @()
    }
}

function def_ReadJsonSafe {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        def_WriteLine "WARN" "JSON read failed: $Path · $($_.Exception.Message)"
        return $null
    }
}

function def_GetSha12 {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    try {
        $h = Get-FileHash -LiteralPath $Path -Algorithm SHA256
        return $h.Hash.Substring(0, 12).ToLowerInvariant()
    } catch {
        return ""
    }
}

function def_EscapeHtml {
    param([object]$Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_Truncate {
    param(
        [object]$Value,
        [int]$Max = 360
    )

    if ($null -eq $Value) {
        return ""
    }

    $s = ([string]$Value) -replace "\s+", " "
    $s = $s.Trim()

    if ($s.Length -gt $Max) {
        return $s.Substring(0, $Max) + "..."
    }

    return $s
}

function def_ReadTextHeadSafe {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop

        if ($item.Length -gt $def_PARAM_MAX_READ_BYTES) {
            $fs = [System.IO.File]::OpenRead($Path)
            try {
                $buf = New-Object byte[] $def_PARAM_MAX_READ_BYTES
                $read = $fs.Read($buf, 0, $buf.Length)
                return [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
            } finally {
                $fs.Dispose()
            }
        }

        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    } catch {
        return ""
    }
}

# =============================================================================
# def CLASSIFIERS
# =============================================================================

function def_GetProject {
    param([string]$Path)

    $s = $Path.ToLowerInvariant()

    if ($s -match "veritasreportnova|\\vrn\\|_vrn|vrn_") { return "VRN" }
    if ($s -match "veritasdataforge|\\vdf\\|_vdf|vdf_") { return "VDF" }
    if ($s -match "\\vis\\|_vis|vis_") { return "VIS" }
    if ($s -match "\\vef\\|_vef|engineforge|ultimateengineforge") { return "VEF" }
    if ($s -match "\\vpf\\|_vpf|vpf_") { return "VPF" }
    if ($s -match "\\vhs\\|_vhs|vhs_") { return "VHS" }
    if ($s -match "\\vpl\\|_vpl|veritaspulse|vpl_") { return "VPL" }
    if ($s -match "ll34") { return "LL34" }
    if ($s -match "\\via|via_|veritasintelligenceanalytics|nexuscore|safe-polyglot|safepolyglot|codexnexus") { return "VIA" }

    return "UNKNOWN"
}

function def_IsExcludedPath {
    param([string]$Path)

    foreach ($rx in $def_PARAM_SCAN_EXCLUDE_REGEX) {
        if ($Path -match $rx) {
            return $true
        }
    }
    return $false
}

function def_GetFileRole {
    param(
        [string]$Path,
        [string]$Ext
    )

    $name = (Split-Path -Leaf $Path).ToLowerInvariant()
    $p = $Path.ToLowerInvariant()

    if ($Ext -in @(".png",".jpg",".jpeg",".webp")) { return "VISUAL_ASSET" }
    if ($name -match "registry|unifiedspec|governance|layout|visual|schema") { return "REGISTRY" }
    if ($name -match "report|summary|panorama|matrix") { return "REPORT" }
    if ($name -match "lock|freeze|seal") { return "LOCK_REGISTRY" }
    if ($name -match "test|validation|validate|lint|e2e|harness") { return "TEST_VALIDATION" }
    if ($Ext -eq ".html") { return "UI_VISUAL" }
    if ($Ext -eq ".ps1" -and $name -match "^invoke-") { return "ENTRY_SCRIPT" }
    if ($Ext -eq ".ps1") { return "SOURCE_SCRIPT" }
    if ($Ext -eq ".py" -and $name -match "engine|mdl|forge|fetch|resolver|filter|manager") { return "ENGINE_MODULE" }
    if ($Ext -eq ".py") { return "SOURCE" }
    if ($Ext -eq ".json") { return "CONFIG_OR_DATA" }
    if ($Ext -eq ".md") { return "README_OR_METHOD" }
    if ($Ext -eq ".csv") { return "DATA_MATRIX" }

    return "SOURCE"
}

function def_GetStaticMetrics {
    param(
        [string]$Path,
        [string]$Ext,
        [long]$SizeBytes,
        [string]$Role = "SOURCE"
    )

    $textExt = @(".ps1",".py",".json",".md",".html",".js",".csv",".yaml",".yml",".txt")
    $text = ""

    if ($textExt -contains $Ext) {
        $text = def_ReadTextHeadSafe -Path $Path
    }

    $lineCount = 0
    if (-not [string]::IsNullOrEmpty($text)) {
        $lineCount = (($text -split "`r?`n").Count)
    }

    $dangerTokens = @(
        ("Remove" + "-Item"),
        ("Stop" + "-Process"),
        ("Clear" + "-RecycleBin"),
        ("docker system prune"),
        ("rmdir /s"),
        ("del /f")
    )

    $dangerHits = New-Object System.Collections.Generic.List[string]
    foreach ($t in $dangerTokens) {
        if ($text -match [regex]::Escape($t)) {
            [void]$dangerHits.Add($t)
        }
    }

    $functionCount = 0
    $classCount = 0
    $importCount = 0
    $paramCount = 0

    if (-not [string]::IsNullOrEmpty($text)) {
        $functionCount = ([regex]::Matches($text, "(?m)^\s*function\s+|(?m)^\s*def\s+\w+\s*\(")).Count
        $classCount = ([regex]::Matches($text, "(?m)^\s*class\s+\w+")).Count
        $importCount = ([regex]::Matches($text, "(?m)^\s*import\s+|(?m)^\s*from\s+\S+\s+import|Import-Module")).Count
        $paramCount = ([regex]::Matches($text, "def_PARAM_|param\s*\(")).Count
    }

    $risk = "LOW"
    $status = "OK"
    $message = "Static readable."

    if ($textExt -contains $Ext -and [string]::IsNullOrEmpty($text)) {
        $risk = "MEDIUM"
        $status = "READ_WARN"
        $message = "Text file could not be read as UTF8 or is empty."
    }

    if ($SizeBytes -gt 10485760) {
        $risk = "MEDIUM"
        $message = "Large file; head-only scan."
    }

    if ($dangerHits.Count -gt 0) {
        $risk = "HIGH"
        $status = "REVIEW_DANGER_TOKEN"
        $message = "Potential destructive tokens detected in static text."
    }

    # v0104 E3/O1: role-aware triage. Danger tokens inside output/content/data files
    # (HTML reports, CSV matrices, READMEs, JSON config, images) are REFERENCE_ONLY noise,
    # not real executable risk. Real review applies only to executable logic roles.
    $executableRoles = @("SOURCE_SCRIPT", "ENTRY_SCRIPT", "ENGINE_MODULE", "SOURCE")
    $contentRoles = @("UI_VISUAL", "REPORT", "DATA_MATRIX", "README_OR_METHOD", "CONFIG_OR_DATA", "VISUAL_ASSET", "REGISTRY", "LOCK_REGISTRY")

    $riskTriage = "LOW"
    $isNoise = $false

    if ($dangerHits.Count -gt 0) {
        if ($executableRoles -contains $Role) {
            $riskTriage = "REVIEW_REAL"
            $isNoise = $false
        } elseif ($contentRoles -contains $Role) {
            $riskTriage = "REFERENCE_ONLY"
            $isNoise = $true
        } else {
            $riskTriage = "REVIEW_GENERIC"
            $isNoise = $false
        }
    } elseif ($risk -eq "MEDIUM") {
        $riskTriage = "MEDIUM"
        $isNoise = $false
    }

    return [pscustomobject]@{
        line_count = $lineCount
        function_count = $functionCount
        class_count = $classCount
        import_count = $importCount
        param_count = $paramCount
        danger_hits = ($dangerHits -join "; ")
        risk = $risk
        risk_triage = $riskTriage
        is_noise = $isNoise
        status = $status
        message = $message
    }
}

# =============================================================================
# def DISCOVERY
# =============================================================================

function def_PrepareDirectories {
    foreach ($d in @(
        $def_PARAM_WORK_DIR,
        $def_PARAM_RUN_DIR,
        $def_PARAM_USED_TOOLS_DIR,
        $def_PARAM_OUTPUT_DIR,
        $def_PARAM_REPORT_DIR,
        $def_PARAM_LOG_DIR,
        $def_PARAM_POINTER_DIR
    )) {
        def_EnsureDirectory -Path $d
    }
}

function def_FindPreviousState {
    $rows = @()

    $outputRoot = Join-Path $def_PARAM_PREVIOUS_ONE_INTERFACE_ROOT "output"

    if (-not (Test-Path -LiteralPath $outputRoot)) {
        $rows += [pscustomobject]@{
            def_item = "Previous v0102 output root"
            def_status = "MISSING"
            def_value = $outputRoot
        }
        return $rows
    }

    $latest = @(Get-ChildItem -LiteralPath $outputRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1)

    if ($latest.Count -eq 0) {
        $rows += [pscustomobject]@{
            def_item = "Previous v0102 run"
            def_status = "MISSING"
            def_value = $outputRoot
        }
        return $rows
    }

    $sumPath = Join-Path $latest[0].FullName "VIA_FinalParameters_OneInterface_Summary.json"
    $summary = def_ReadJsonSafe -Path $sumPath

    $rows += [pscustomobject]@{ def_item="previous_run_dir"; def_status="OK"; def_value=$latest[0].FullName }
    $rows += [pscustomobject]@{ def_item="summary_json"; def_status=$(if ($summary) {"OK"} else {"MISSING"}); def_value=$sumPath }

    if ($summary) {
        $rows += [pscustomobject]@{ def_item="status"; def_status="OK"; def_value=$summary.status }
        $rows += [pscustomobject]@{ def_item="parameters"; def_status="OK"; def_value=$summary.parameter_count }
        $rows += [pscustomobject]@{ def_item="canonical"; def_status="OK"; def_value=$summary.canonical_count }
        $rows += [pscustomobject]@{ def_item="canonical_accept"; def_status="OK"; def_value=$summary.canonical_accept_count }
        $rows += [pscustomobject]@{ def_item="canonical_review"; def_status="OK"; def_value=$summary.canonical_review_count }
        $rows += [pscustomobject]@{ def_item="p0_review"; def_status="REVIEW"; def_value=$summary.conflict_p0_count }
        $rows += [pscustomobject]@{ def_item="p1_path"; def_status="REVIEW"; def_value=$summary.conflict_p1_count }
        $rows += [pscustomobject]@{ def_item="engines"; def_status="OK"; def_value=$summary.engine_bridge_count }
    }

    return $rows
}

function def_StageUsedTools {
    $rows = @()

    $sets = @(
        [pscustomobject]@{ category="supportive_modules"; paths=$def_PARAM_SUPPORTIVE_MODULES },
        [pscustomobject]@{ category="functional_modules"; paths=$def_PARAM_FUNCTIONAL_MODULES },
        [pscustomobject]@{ category="firststep_commands"; paths=$def_PARAM_FIRSTSTEP_COMMANDS }
    )

    foreach ($set in $sets) {
        $catDir = Join-Path $def_PARAM_USED_TOOLS_DIR $set.category
        def_EnsureDirectory -Path $catDir

        foreach ($src in $set.paths) {
            $exists = Test-Path -LiteralPath $src
            $leaf = Split-Path -Leaf $src
            $dst = Join-Path $catDir $leaf
            $status = "MISSING"
            $msg = ""

            if ($exists) {
                try {
                    Copy-Item -LiteralPath $src -Destination $dst -Force
                    $status = "COPIED_READONLY_SOURCE"
                    $msg = "Copied to run-isolated used tools folder."
                } catch {
                    $status = "COPY_WARN"
                    $msg = $_.Exception.Message
                }
            } else {
                $msg = "Source file missing."
            }

            $sha = ""
            $size = ""
            $modified = ""

            if ($exists) {
                try {
                    $it = Get-Item -LiteralPath $src
                    $sha = def_GetSha12 -Path $src
                    $size = $it.Length
                    $modified = $it.LastWriteTime.ToString("s")
                } catch {
                }
            }

            $rows += [pscustomobject]@{
                def_category = $set.category
                def_file = $leaf
                def_source_path = $src
                def_staged_path = $(if ($exists) { $dst } else { "" })
                def_exists = $exists
                def_status = $status
                def_size_bytes = $size
                def_modified_time = $modified
                def_sha12 = $sha
                def_message = $msg
            }
        }
    }

    return @($rows)
}

function def_ScanBaseFiles {
    if (-not (Test-Path -LiteralPath $def_PARAM_BASE_ROOT)) {
        throw "Base root not found: $def_PARAM_BASE_ROOT"
    }

    # v0104 E1: exclude self-generated run outputs / noise dirs from the panoramic scan.
    $files = @(Get-ChildItem -LiteralPath $def_PARAM_BASE_ROOT -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            ($def_PARAM_SCAN_EXTENSIONS -contains $_.Extension.ToLowerInvariant()) -and
            (-not (def_IsExcludedPath -Path $_.FullName))
        } |
        Sort-Object FullName)

    $total = [math]::Max($files.Count, 1)
    $i = 0

    # v0104 E2: collect via foreach-expression (no += O(n^2)); single object per iteration.
    $rows = foreach ($f in $files) {
        $i++

        if (($i % 50) -eq 0 -or $i -eq 1 -or $i -eq $files.Count) {
            $pct = [math]::Round(($i / $total) * 100, 0)
            Write-Progress -Id 2 -ParentId 1 -Activity "Scanning BASE files" -Status "$i / $total · $($f.Name)" -PercentComplete $pct
        }

        try {
            $ext = $f.Extension.ToLowerInvariant()
            $project = def_GetProject -Path $f.FullName
            $role = def_GetFileRole -Path $f.FullName -Ext $ext
            $metrics = def_GetStaticMetrics -Path $f.FullName -Ext $ext -SizeBytes $f.Length -Role $role

            [pscustomobject]@{
                def_project = $project
                def_role = $role
                def_file = $f.Name
                def_ext = $ext
                def_size_kb = [math]::Round($f.Length / 1KB, 1)
                def_line_count = $metrics.line_count
                def_function_count = $metrics.function_count
                def_class_count = $metrics.class_count
                def_import_count = $metrics.import_count
                def_param_count = $metrics.param_count
                def_risk = $metrics.risk
                def_risk_triage = $metrics.risk_triage
                def_is_noise = $metrics.is_noise
                def_status = $metrics.status
                def_danger_hits = $metrics.danger_hits
                def_modified_time = $f.LastWriteTime.ToString("s")
                def_sha12 = def_GetSha12 -Path $f.FullName
                def_path = $f.FullName
                def_message = $metrics.message
            }
        } catch {
            [pscustomobject]@{
                def_project = "UNKNOWN"
                def_role = "SCAN_ERROR"
                def_file = $f.Name
                def_ext = $f.Extension
                def_size_kb = ""
                def_line_count = ""
                def_function_count = ""
                def_class_count = ""
                def_import_count = ""
                def_param_count = ""
                def_risk = "MEDIUM"
                def_risk_triage = "MEDIUM"
                def_is_noise = $false
                def_status = "SCAN_ERROR"
                def_danger_hits = ""
                def_modified_time = $f.LastWriteTime.ToString("s")
                def_sha12 = ""
                def_path = $f.FullName
                def_message = $_.Exception.Message
            }
        }
    }

    Write-Progress -Id 2 -ParentId 1 -Activity "Scanning BASE files" -Completed

    return @($rows)
}

# =============================================================================
# def MATRIX BUILDERS
# =============================================================================

function def_BuildSubsystemFiveFlowMatrix {
    param([object[]]$FileRows)

    $rows = @()
    $groups = @($FileRows | Group-Object def_project)

    foreach ($g in $groups) {
        $project = $g.Name
        $items = @($g.Group)

        $total = $items.Count
        $engineCount = @($items | Where-Object { $_.def_role -eq "ENGINE_MODULE" }).Count
        $entryCount = @($items | Where-Object { $_.def_role -eq "ENTRY_SCRIPT" }).Count
        $registryCount = @($items | Where-Object { $_.def_role -eq "REGISTRY" }).Count
        $uiCount = @($items | Where-Object { $_.def_role -eq "UI_VISUAL" }).Count
        $testCount = @($items | Where-Object { $_.def_role -eq "TEST_VALIDATION" }).Count
        $highRisk = @($items | Where-Object { $_.def_risk -eq "HIGH" }).Count
        $mediumRisk = @($items | Where-Object { $_.def_risk -eq "MEDIUM" }).Count

        $rows += [pscustomobject]@{
            def_project = $project
            def_flow_id = "FLOW01"
            def_flow_name = "Inventory Panorama"
            def_scope = "Base 檔案全景盤點 / role / size / static metric"
            def_status = $(if ($total -gt 0) { "READY" } else { "EMPTY" })
            def_count = $total
            def_risk = $(if ($highRisk -gt 0) { "HIGH_REVIEW" } elseif ($mediumRisk -gt 0) { "MEDIUM_REVIEW" } else { "LOW" })
            def_parallel_policy = "READ_ONLY_PARALLEL_SAFE"
            def_next_action = "保留來源，先只看矩陣，不直接修"
        }

        $rows += [pscustomobject]@{
            def_project = $project
            def_flow_id = "FLOW02"
            def_flow_name = "Registry / SSOT Alignment"
            def_scope = "UnifiedSpec / Governance / Layout / Visual / module registry"
            def_status = $(if ($registryCount -gt 0) { "READY" } else { "REGISTRY_GAP" })
            def_count = $registryCount
            def_risk = $(if ($registryCount -eq 0) { "MEDIUM" } else { "LOW" })
            def_parallel_policy = "INDEPENDENT"
            def_next_action = "每個子系統建立自己的 registry pointer，再由 VIA 統合"
        }

        $rows += [pscustomobject]@{
            def_project = $project
            def_flow_id = "FLOW03"
            def_flow_name = "Engine / Entry Bridge"
            def_scope = "Engine modules + Invoke entry scripts + Supportive bridges"
            def_status = $(if (($engineCount + $entryCount) -gt 0) { "READY" } else { "ENGINE_GAP" })
            def_count = ($engineCount + $entryCount)
            def_risk = $(if (($engineCount + $entryCount) -eq 0) { "MEDIUM" } else { "LOW" })
            def_parallel_policy = "BRIDGE_ONLY_NO_CHILD_RUN"
            def_next_action = "先做 static bridge；child execution 預設鎖住"
        }

        $rows += [pscustomobject]@{
            def_project = $project
            def_flow_id = "FLOW04"
            def_flow_name = "Sandbox Test / Debug / Optimize"
            def_scope = "test debug upgrade / optimize / consolidate / user-test"
            def_status = $(if ($testCount -gt 0) { "READY" } else { "TEST_GAP" })
            def_count = $testCount
            def_risk = $(if ($highRisk -gt 0) { "HIGH_REVIEW_BEFORE_FIX" } else { "LOW" })
            def_parallel_policy = "SANDBOX_ONLY"
            def_next_action = "三輪：分析 → 分類 → 沙盒修正；不超過三輪"
        }

        $rows += [pscustomobject]@{
            def_project = $project
            def_flow_id = "FLOW05"
            def_flow_name = "One UI / Report / Final Seal"
            def_scope = "HTML Matrix Report + Active Pointer + Closeout"
            def_status = $(if ($uiCount -gt 0) { "READY" } else { "UI_GAP" })
            def_count = $uiCount
            def_risk = "LOW"
            def_parallel_policy = "OUTPUT_ONLY"
            def_next_action = "一頁式多矩陣報告，小字體、不卡版、同高卡片"
        }
    }

    return @($rows | Sort-Object def_project, def_flow_id)
}

function def_BuildIntegrationPlan {
    param(
        [object[]]$FileRows,
        [object[]]$ToolRows,
        [object[]]$PreviousRows
    )

    $rows = @()

    # FIX v0103: Select-Object was wrongly placed inside the Where-Object scriptblock
    # and the brace was unbalanced, which broke whole-file parse. Corrected + null-safe.
    $p0Row = @($PreviousRows | Where-Object { $_.def_item -eq "p0_review" } | Select-Object -First 1)
    $p0 = if ($p0Row.Count -gt 0) { $p0Row[0].def_value } else { "" }

    $canonicalReviewRow = @($PreviousRows | Where-Object { $_.def_item -eq "canonical_review" } | Select-Object -First 1)
    $canonicalReview = if ($canonicalReviewRow.Count -gt 0) { $canonicalReviewRow[0].def_value } else { "" }

    $rows += [pscustomobject]@{
        def_order = "P0-01"
        def_scope = "VIA Final Parameters v0102"
        def_current_state = "Parameters=77201; Canonical=34696; P0=$p0; CanonicalReview=$canonicalReview"
        def_action_type = "REVIEW_FIRST"
        def_independent_flow = "FLOW02 + FLOW03"
        def_next_action = "先鎖 DATA_SOURCE / MARKET_UNIVERSE / MACRO_SENTIMENT / SCHEMA_FIELD / ENGINE / GOVERNANCE_POLICY 的 SSOT；不要先大修 UI 或重跑全部"
        def_hydra_guard = "No direct repair; no child execution; output-only"
    }

    $rows += [pscustomobject]@{
        def_order = "P0-02"
        def_scope = "Supportive Modules"
        def_current_state = "SafePolyglotOptimizer + AIO + README + StaticValidation staged"
        def_action_type = "BRIDGE_SUPPORTIVE"
        def_independent_flow = "FLOW01 → FLOW03 → FLOW04"
        def_next_action = "建立 SupportiveToolRegistry，標示每個工具的用途、可否 child-run、timeout、輸出資料夾"
        def_hydra_guard = "工具只複製到 run folder；來源檔不改"
    }

    $rows += [pscustomobject]@{
        def_order = "P0-03"
        def_scope = "Functional Modules"
        def_current_state = "UnifiedSpec / GovernanceRegistry / LayoutRegistry / VisualRegistry / Invoke-VeritasCodexNexus"
        def_action_type = "FUNCTIONAL_SPEC_LOCK"
        def_independent_flow = "FLOW02"
        def_next_action = "UnifiedSpec 作總規格；Governance/Layout/Visual 分別成三個子 registry；CodexNexus 只做 bridge，不直接重寫"
        def_hydra_guard = "Spec lock before code generation"
    }

    $rows += [pscustomobject]@{
        def_order = "P1-01"
        def_scope = "VDF"
        def_current_state = "資料來源、YFinance、AKShare、SentimentStrength 已開始導入"
        def_action_type = "DATA_ENGINE_CONSOLIDATION"
        def_independent_flow = "FLOW01~FLOW05"
        def_next_action = "把 yfinance / akshare / FRED / AAII / CNN Fear & Greed 全放進 VDF DataSourceRegistry，標示可抓、替代源、不可抓"
        def_hydra_guard = "資料引擎分開測；不與 UI 同輪修"
    }

    $rows += [pscustomobject]@{
        def_order = "P1-02"
        def_scope = "VRN"
        def_current_state = "PDF 報告擷取、券商 alias、財務 SSOT、表格重建規則多版本並存"
        def_action_type = "REPORT_ENGINE_ROUTING"
        def_independent_flow = "FLOW01~FLOW04"
        def_next_action = "VRN 只接收 VDF 的 ticker/date/company SSOT，不反向覆寫 VDF"
        def_hydra_guard = "Route-only bridge; no canonical overwrite"
    }

    $rows += [pscustomobject]@{
        def_order = "P1-03"
        def_scope = "VIS / Visual Lock"
        def_current_state = "VisualRegistry + LayoutRegistry + 丹青水墨 UI lock"
        def_action_type = "UI_DENSE_MODE"
        def_independent_flow = "FLOW05"
        def_next_action = "統一小字體、nowrap table、equal-height cards、dense matrix、tab 一頁式報告"
        def_hydra_guard = "UI only; 不碰 data engine"
    }

    $rows += [pscustomobject]@{
        def_order = "P1-04"
        def_scope = "VEF / EngineForge"
        def_current_state = "v062 NullSafeStepSafe > v061 BoolParamHotfix > v060 methodology fallback"
        def_action_type = "ENGINE_FORGE_STACK"
        def_independent_flow = "FLOW03"
        def_next_action = "v062 作主引擎；v061 只補 bool param；v060 只保留方法論與 registry stub"
        def_hydra_guard = "Only one active engineforge pointer"
    }

    $rows += [pscustomobject]@{
        def_order = "P2-01"
        def_scope = "VPF / Signal & Rotation"
        def_current_state = "族群輪動、個股訊號已有獨立 engine"
        def_action_type = "DOWNSTREAM_CONSUMER"
        def_independent_flow = "FLOW03 + FLOW05"
        def_next_action = "VPF 只消費 VDF/VRN clean outputs；不參與資料抓取 SSOT"
        def_hydra_guard = "Consumer only"
    }

    $rows += [pscustomobject]@{
        def_order = "P2-02"
        def_scope = "VHS / Test Harness"
        def_current_state = "UI harness / e2e / visual extraction"
        def_action_type = "USER_TEST_LAYER"
        def_independent_flow = "FLOW04"
        def_next_action = "作為 UI user-test 與 HTML regression test；不要改資料引擎"
        def_hydra_guard = "Test-only"
    }

    $rows += [pscustomobject]@{
        def_order = "P2-03"
        def_scope = "VPL / VeritasPulse"
        def_current_state = "專案管理 UI 與 task ledger"
        def_action_type = "PROJECT_PLANNING_LAYER"
        def_independent_flow = "FLOW05"
        def_next_action = "接 integration plan，輸出任務與里程碑；不寫回 canonical registry"
        def_hydra_guard = "Planning only"
    }

    return @($rows)
}

function def_BuildTop10Libs {
    $rows = @()

    $rows += [pscustomobject]@{ def_function="PowerShell Orchestration"; def_language="PowerShell"; def_top10_local_free_libs="Pester; PSScriptAnalyzer; ThreadJob; ImportExcel; PSWriteHTML; Pode; PSFramework; BurntToast; SecretManagement; PSReadLine"; def_use_case="測試、lint、背景工作、Excel/HTML 報告、local UI、log、通知、互動輸入"; def_phase="FLOW03/FLOW04/FLOW05" }
    $rows += [pscustomobject]@{ def_function="Python Data Engine"; def_language="Python"; def_top10_local_free_libs="pandas; polars; duckdb; pyarrow; numpy; requests; httpx; pydantic; rich; tqdm"; def_use_case="資料抓取、轉換、Parquet/DuckDB、schema validation、進度條"; def_phase="FLOW01/FLOW02/FLOW03" }
    $rows += [pscustomobject]@{ def_function="Finance Market Fetch"; def_language="Python"; def_top10_local_free_libs="yfinance; akshare; pandas_datareader; fredapi; investpy; yahooquery; exchange_calendars; pandas-market-calendars; requests-cache; tenacity"; def_use_case="YFinance 優先、AKShare 次之、FRED/ETF/指數/商品/利率/重試快取"; def_phase="VDF FLOW03" }
    $rows += [pscustomobject]@{ def_function="Macro / Sentiment"; def_language="Python"; def_top10_local_free_libs="fredapi; pandas_datareader; requests; beautifulsoup4; lxml; trafilatura; feedparser; tenacity; requests-cache; python-dateutil"; def_use_case="FRED、AAII、CNN Fear & Greed proxy、官方頁面解析、日期標準化"; def_phase="VDF FLOW03/FLOW04" }
    $rows += [pscustomobject]@{ def_function="PDF / Report Extraction"; def_language="Python"; def_top10_local_free_libs="pdfplumber; PyMuPDF; pdfminer.six; pypdf; camelot-py; tabula-py; opencv-python; pillow; pytesseract; rapidfuzz"; def_use_case="VRN PDF 表格、文字、OCR、版面、券商 alias match"; def_phase="VRN FLOW03/FLOW04" }
    $rows += [pscustomobject]@{ def_function="Schema / Registry"; def_language="Python"; def_top10_local_free_libs="jsonschema; pydantic; ruamel.yaml; PyYAML; duckdb; sqlite-utils; deepdiff; rapidfuzz; orjson; msgspec"; def_use_case="UnifiedSpec、GovernanceRegistry、LayoutRegistry、VisualRegistry、差異比較"; def_phase="FLOW02" }
    $rows += [pscustomobject]@{ def_function="HTML UI / Dashboard"; def_language="JavaScript"; def_top10_local_free_libs="Vanilla JS; Plotly.js; D3.js; ECharts; Tabulator; Grid.js; Fuse.js; PapaParse; Day.js; Tippy.js"; def_use_case="一頁式多矩陣、搜尋、圖表、CSV preview、tooltip"; def_phase="FLOW05" }
    $rows += [pscustomobject]@{ def_function="CSS Visual Lock"; def_language="CSS/HTML"; def_top10_local_free_libs="CSS Grid; Flexbox; CSS variables; clamp(); container queries; sticky header; text-overflow; prefers-reduced-motion; local font-face; SVG pattern"; def_use_case="小字體、同高卡片、nowrap 表格、丹青水墨 visual lock"; def_phase="VIS FLOW05" }
    $rows += [pscustomobject]@{ def_function="Testing / Static Quality"; def_language="Python"; def_top10_local_free_libs="pytest; ruff; black; isort; mypy; pyright; bandit; vulture; coverage.py; hypothesis"; def_use_case="test debug upgrade optimize consolidate 前後檢查"; def_phase="FLOW04" }
    $rows += [pscustomobject]@{ def_function="Testing / Browser UI"; def_language="JavaScript"; def_top10_local_free_libs="Playwright; Vitest; Jest; ESLint; Prettier; axe-core; Lighthouse; jsdom; html-validate; pixelmatch"; def_use_case="HTML UI user-test、可讀性、可及性、版面回歸"; def_phase="VHS FLOW04" }
    $rows += [pscustomobject]@{ def_function="Performance / Cache"; def_language="Python"; def_top10_local_free_libs="joblib; diskcache; requests-cache; cachetools; lz4; zstandard; pyarrow; duckdb; polars; tqdm"; def_use_case="資料抓取快取、Parquet、DuckDB、增量輸出"; def_phase="FLOW03" }
    $rows += [pscustomobject]@{ def_function="Windows Integration"; def_language="PowerShell"; def_top10_local_free_libs="ThreadJob; ScheduledTasks; BurntToast; PSWindowsUpdate; WinGet.Client; SecretManagement; ImportExcel; PSScriptAnalyzer; Pester; PSReadLine"; def_use_case="Windows I/O、通知、環境偵測、安裝計劃、排程"; def_phase="Supportive FLOW03" }
    $rows += [pscustomobject]@{ def_function="Document / Methodology"; def_language="Python"; def_top10_local_free_libs="python-docx; mammoth; markdown; beautifulsoup4; lxml; mistune; pypandoc; rich; jinja2; weasyprint"; def_use_case="VEF.docx、methodology、README、HTML 報告產生"; def_phase="VEF FLOW02/FLOW05" }
    $rows += [pscustomobject]@{ def_function="Signal / Rotation"; def_language="Python"; def_top10_local_free_libs="pandas; polars; numpy; scipy; statsmodels; ta; pandas-ta; duckdb; pyarrow; plotly"; def_use_case="VPF 個股訊號、族群輪動、因子矩陣"; def_phase="VPF FLOW03/FLOW05" }

    return $rows
}

function def_BuildPS15Accelerators {
    return @(
        [pscustomobject]@{ def_id="PSA01"; def_name="Run-Isolated Output"; def_function="每次 RUN 獨立資料夾，不覆蓋舊結果"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA02"; def_name="No Child Execution Default"; def_function="只做 first-step scan，不直接跑其他大腳本"; def_status="LOCKED_SAFE" },
        [pscustomobject]@{ def_id="PSA03"; def_name="Used Tools Staging"; def_function="把本次用到的工具複製到 _used_tools"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA04"; def_name="Head-Only Large File Scan"; def_function="大型檔只讀前段，避免卡住"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA05"; def_name="Extension Filter"; def_function="只掃描可治理檔案類型"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA06"; def_name="Static Metrics"; def_function="函式、class、import、param、risk 快速統計"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA07"; def_name="Danger Token Review"; def_function="只標記高風險 token，不自動修"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA08"; def_name="Previous v0102 Bridge"; def_function="接上上一輪 parameters/canonical/P0 結果"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA09"; def_name="Five-Flow Matrix"; def_function="每個子系統 5 流程獨立列出"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA10"; def_name="Hydra Guard"; def_function="修正前先分類 parallel-safe / sequential-safe"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA11"; def_name="Dense HTML UI"; def_function="小字體、nowrap、ellipsis、sticky header"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA12"; def_name="Equal Height Layout"; def_function="左右卡片同高，自動 grid stretch"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA13"; def_name="Searchable Matrices"; def_function="每個矩陣可前端搜尋"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA14"; def_name="Active Pointer"; def_function="固定 pointer 指向最新報告與輸出"; def_status="ENABLED" },
        [pscustomobject]@{ def_id="PSA15"; def_name="PowerShell No Exit"; def_function="例外後保持 PowerShell 開啟"; def_status="ENABLED" }
    )
}

# =============================================================================
# def HTML REPORT
# =============================================================================

function def_TableHtml {
    param(
        [object[]]$Rows,
        [string]$TableId,
        [int]$Limit = 2000
    )

    $arr = @($Rows | Select-Object -First $Limit)

    if ($arr.Count -eq 0) {
        return "<p class='muted'>No rows.</p>"
    }

    $cols = @($arr[0].PSObject.Properties.Name)
    $thead = "<tr>" + (($cols | ForEach-Object { "<th title='$(def_EscapeHtml $_)'>$(def_EscapeHtml $_)</th>" }) -join "") + "</tr>"

    $body = New-Object System.Collections.Generic.List[string]

    foreach ($r in $arr) {
        $tds = foreach ($c in $cols) {
            $raw = [string]$r.$c
            $shown = def_Truncate -Value $raw -Max 260
            "<td title='$(def_EscapeHtml $raw)'>$(def_EscapeHtml $shown)</td>"
        }

        [void]$body.Add("<tr>$($tds -join '')</tr>")
    }

    return @"
<div class="tableTools">
  <input class="q" placeholder="Search matrix..." oninput="filterTable('$TableId', this.value)">
  <span class="rowhint">showing $($arr.Count) rows</span>
</div>
<div class="tablewrap">
<table id="$TableId">
<thead>$thead</thead>
<tbody>
$($body -join "`n")
</tbody>
</table>
</div>
"@
}

function def_WriteHtmlReport {
    param(
        [object]$Summary,
        [object[]]$FileRows,
        [object[]]$ToolRows,
        [object[]]$SubsystemFlowRows,
        [object[]]$IntegrationPlanRows,
        [object[]]$Top10Rows,
        [object[]]$PS15Rows,
        [object[]]$PreviousRows
    )

    def_EnsureDirectory -Path (Split-Path -Parent $def_PARAM_REPORT_HTML)

    $highCount = @($FileRows | Where-Object { $_.def_risk -eq "HIGH" }).Count
    $mediumCount = @($FileRows | Where-Object { $_.def_risk -eq "MEDIUM" }).Count
    $realHighCount = @($FileRows | Where-Object { $_.def_risk_triage -eq "REVIEW_REAL" }).Count
    $noiseHighCount = @($FileRows | Where-Object { $_.def_is_noise -eq $true }).Count
    $toolOk = @($ToolRows | Where-Object { $_.def_exists }).Count
    $toolMissing = @($ToolRows | Where-Object { -not $_.def_exists }).Count

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Integration FirstStep Panorama v0104</title>
<style>
:root{
  --bg:#f7f8f4;
  --paper:#ffffff;
  --ink:#1f2f34;
  --mut:#69787c;
  --line:#dfe8e4;
  --line2:#edf3f0;
  --teal:#007f73;
  --sky:#64b5cd;
  --amber:#c4943a;
  --red:#c96b5a;
  --green:#5a9e6f;
  --shadow:0 10px 26px rgba(31,47,54,.075);
  --fs-micro:9px;
  --fs-small:10px;
  --fs:10.8px;
  --fs-title:13px;
  --fs-hero:20px;
}
*{box-sizing:border-box}
body{
  margin:0;
  color:var(--ink);
  background:
    radial-gradient(circle at 10% 6%, rgba(100,181,205,.16), transparent 25%),
    radial-gradient(circle at 86% 12%, rgba(90,158,111,.12), transparent 26%),
    linear-gradient(135deg,#fbfbf7,#f4f8f6);
  font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;
  font-size:var(--fs);
}
header{
  padding:22px 28px 14px;
  border-bottom:1px solid var(--line);
}
h1{
  margin:0;
  color:var(--teal);
  font-size:var(--fs-hero);
  font-weight:520;
  letter-spacing:.02em;
}
.sub{
  margin-top:5px;
  color:var(--mut);
  font-size:var(--fs-small);
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.wrap{padding:18px 28px 34px}
.kpis{
  display:grid;
  grid-template-columns:repeat(10,minmax(96px,1fr));
  gap:10px;
  margin-bottom:14px;
  align-items:stretch;
}
.kpi{
  min-height:74px;
  background:rgba(255,255,255,.88);
  border:1px solid var(--line);
  border-radius:13px;
  padding:10px 12px;
  box-shadow:var(--shadow);
}
.kpi b{
  display:block;
  color:var(--mut);
  font-size:var(--fs-micro);
  font-weight:500;
  white-space:nowrap;
}
.kpi span{
  display:block;
  margin-top:5px;
  font-size:18px;
  color:var(--teal);
  font-family:Consolas,"DM Mono",monospace;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.tabs{
  display:flex;
  flex-wrap:wrap;
  gap:7px;
  margin:12px 0;
}
button.tab{
  border:1px solid var(--line);
  background:rgba(255,255,255,.84);
  color:var(--ink);
  border-radius:999px;
  padding:7px 11px;
  cursor:pointer;
  font-size:var(--fs-small);
}
button.tab.on{background:var(--teal);color:white;border-color:var(--teal)}
.panel{
  display:none;
  background:rgba(255,255,255,.88);
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  box-shadow:var(--shadow);
  margin-bottom:14px;
}
.panel.on{display:block}
h2{
  margin:0 0 10px;
  color:var(--teal);
  font-size:var(--fs-title);
  font-weight:560;
}
.grid2{
  display:grid;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  gap:12px;
  align-items:stretch;
}
.grid3{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:12px;
  align-items:stretch;
}
.card{
  height:100%;
  background:white;
  border:1px solid var(--line);
  border-radius:14px;
  padding:12px;
  overflow:hidden;
}
.card p{
  margin:0 0 9px;
  line-height:1.55;
}
.badge{
  display:inline-block;
  border-radius:999px;
  padding:3px 7px;
  margin:2px;
  border:1px solid var(--line);
  background:#f0f8f5;
  color:var(--teal);
  font-size:var(--fs-micro);
  white-space:nowrap;
}
.tableTools{
  display:flex;
  align-items:center;
  gap:8px;
  margin-bottom:8px;
}
.q{
  width:320px;
  max-width:60vw;
  border:1px solid var(--line);
  border-radius:10px;
  padding:7px 9px;
  font-size:var(--fs-small);
}
.rowhint{
  color:var(--mut);
  font-size:var(--fs-micro);
}
.tablewrap{
  overflow:auto;
  max-height:650px;
  border:1px solid var(--line);
  border-radius:13px;
  background:white;
}
table{
  width:100%;
  border-collapse:collapse;
  table-layout:fixed;
  font-size:10px;
}
th,td{
  padding:6px 7px;
  border-bottom:1px solid var(--line2);
  text-align:left;
  vertical-align:top;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
th{
  position:sticky;
  top:0;
  z-index:1;
  background:#f2f8f6;
  color:#006b60;
  font-weight:560;
}
td{max-width:280px}
.path{
  font-family:Consolas,"DM Mono",monospace;
  font-size:10px;
  white-space:pre-wrap;
  overflow:auto;
  max-height:320px;
}
.muted{color:var(--mut)}
.warn{color:var(--amber)}
.bad{color:var(--red)}
.good{color:var(--green)}
@media(max-width:1100px){
  .kpis{grid-template-columns:repeat(4,1fr)}
  .grid2,.grid3{grid-template-columns:1fr}
}
</style>
</head>
<body>
<header>
  <h1>def VIA Integration FirstStep Panorama · v0104</h1>
  <div class="sub">BASE panoramic static scan · used tools staging · subsystem five-flow matrix · no child execution · no repair · dense one-page report</div>
</header>

<div class="wrap">
  <div class="kpis">
    <div class="kpi"><b>Status</b><span>$($Summary.status)</span></div>
    <div class="kpi"><b>Base Files</b><span>$($Summary.base_file_count)</span></div>
    <div class="kpi"><b>Tools OK</b><span>$toolOk</span></div>
    <div class="kpi"><b>Tools Missing</b><span>$toolMissing</span></div>
    <div class="kpi"><b>High Risk</b><span>$highCount</span></div>
    <div class="kpi"><b>Real High</b><span>$realHighCount</span></div>
    <div class="kpi"><b>Noise (ref)</b><span>$noiseHighCount</span></div>
    <div class="kpi"><b>Medium</b><span>$mediumCount</span></div>
    <div class="kpi"><b>Flows</b><span>$($SubsystemFlowRows.Count)</span></div>
    <div class="kpi"><b>PS Accel</b><span>$($PS15Rows.Count)</span></div>
  </div>

  <div class="tabs">
    <button class="tab on" data-tab="overview">Overview</button>
    <button class="tab" data-tab="tools">Used Tools</button>
    <button class="tab" data-tab="files">Base File Matrix</button>
    <button class="tab" data-tab="flows">Subsystem Five Flows</button>
    <button class="tab" data-tab="plan">Integration Plan</button>
    <button class="tab" data-tab="libs">Top10 Local Libs</button>
    <button class="tab" data-tab="ps15">PS15</button>
    <button class="tab" data-tab="prev">Previous v0102</button>
    <button class="tab" data-tab="outputs">Outputs</button>
  </div>

  <section id="overview" class="panel on">
    <h2>def Overview</h2>
    <div class="grid2">
      <div class="card">
        <p><b>本輪定位：</b>整合第一步，只做全景檢視、工具收納、風險分類、後續動作計畫。預設不執行子腳本、不修原始檔，避免自桶與九頭龍風險。</p>
        <p>
          <span class="badge">Read-only</span>
          <span class="badge">No child execution</span>
          <span class="badge">No repair</span>
          <span class="badge">Run isolated</span>
          <span class="badge">HTML dense mode</span>
          <span class="badge">Equal-height cards</span>
        </p>
      </div>
      <div class="card">
        <p><b>下一步重點：</b>先把 v0102 的 P0 依 domain 拆開；VDF 資料源、Functional Registry、Supportive Tool Registry 先鎖 SSOT，再開沙盒修正。</p>
        <p class="muted">流程：三輪全景分析 → 分類 parallel-safe / sequential-safe → 沙盒修正 → 再三輪驗證 → HTML Matrix closeout。</p>
      </div>
    </div>
  </section>

  <section id="tools" class="panel">
    <h2>def Used Tools Staging Matrix</h2>
    $(def_TableHtml -Rows $ToolRows -TableId "tblTools" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="files" class="panel">
    <h2>def BASE File Matrix</h2>
    $(def_TableHtml -Rows $FileRows -TableId "tblFiles" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="flows" class="panel">
    <h2>def Subsystem Five Independent Flows</h2>
    $(def_TableHtml -Rows $SubsystemFlowRows -TableId "tblFlows" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="plan" class="panel">
    <h2>def Integration Action Plan</h2>
    $(def_TableHtml -Rows $IntegrationPlanRows -TableId "tblPlan" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="libs" class="panel">
    <h2>def Top 10 Local Free Libs · Function × Language</h2>
    $(def_TableHtml -Rows $Top10Rows -TableId "tblLibs" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="ps15" class="panel">
    <h2>def 15 PowerShell Accelerators</h2>
    $(def_TableHtml -Rows $PS15Rows -TableId "tblPS15" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="prev" class="panel">
    <h2>def Previous v0102 State</h2>
    $(def_TableHtml -Rows $PreviousRows -TableId "tblPrev" -Limit $def_PARAM_HTML_TABLE_LIMIT)
  </section>

  <section id="outputs" class="panel">
    <h2>def Output Paths</h2>
    <div class="card path">Run Dir       : $def_PARAM_RUN_DIR
Used Tools    : $def_PARAM_USED_TOOLS_DIR
File Matrix   : $def_PARAM_FILE_MATRIX_CSV
Tool Matrix   : $def_PARAM_TOOL_STAGING_CSV
Flow Matrix   : $def_PARAM_SUBSYSTEM_FLOW_CSV
Action Plan   : $def_PARAM_INTEGRATION_PLAN_CSV
Top10 Libs    : $def_PARAM_TOP10_LIBS_CSV
PS15 Matrix   : $def_PARAM_PS15_CSV
Summary JSON  : $def_PARAM_SUMMARY_JSON
Report HTML   : $def_PARAM_REPORT_HTML
Pointer JSON  : $def_PARAM_ACTIVE_POINTER</div>
  </section>
</div>

<script>
document.querySelectorAll('button.tab').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('button.tab').forEach(x=>x.classList.remove('on'));
    document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
    btn.classList.add('on');
    document.getElementById(btn.dataset.tab).classList.add('on');
  });
});
function filterTable(id,q){
  q=(q||'').toLowerCase();
  const t=document.getElementById(id);
  if(!t)return;
  t.querySelectorAll('tbody tr').forEach(tr=>{
    tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none';
  });
}
</script>
</body>
</html>
"@

    Set-Content -LiteralPath $def_PARAM_REPORT_HTML -Value $html -Encoding UTF8
}

# =============================================================================
# def MAIN
# =============================================================================

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA · INTEGRATION FIRSTSTEP PANORAMA · v0104" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    def_ShowProgress -Step 1 -Total 9 -Status "Prepare run directories"
    def_PrepareDirectories

    def_ShowProgress -Step 2 -Total 9 -Status "Stage used tools into run folder"
    $toolRows = def_StageUsedTools
    def_ExportCsvSafe -Rows $toolRows -Path $def_PARAM_TOOL_STAGING_CSV
    def_WriteLine "OK" "Used tools staged: $(@($toolRows | Where-Object { $_.def_exists }).Count) / $($toolRows.Count)"

    def_ShowProgress -Step 3 -Total 9 -Status "Read previous v0102 one-interface state"
    $previousRows = def_FindPreviousState
    def_ExportCsvSafe -Rows $previousRows -Path $def_PARAM_PREVIOUS_STATE_CSV

    def_ShowProgress -Step 4 -Total 9 -Status "Scan BASE files panoramic static matrix"
    $fileRows = def_ScanBaseFiles
    def_ExportCsvSafe -Rows $fileRows -Path $def_PARAM_FILE_MATRIX_CSV
    def_WriteLine "OK" "Base files scanned: $($fileRows.Count)"

    def_ShowProgress -Step 5 -Total 9 -Status "Build subsystem five-flow matrix"
    $flowRows = def_BuildSubsystemFiveFlowMatrix -FileRows $fileRows
    def_ExportCsvSafe -Rows $flowRows -Path $def_PARAM_SUBSYSTEM_FLOW_CSV

    def_ShowProgress -Step 6 -Total 9 -Status "Build integration action plan"
    $planRows = def_BuildIntegrationPlan -FileRows $fileRows -ToolRows $toolRows -PreviousRows $previousRows
    def_ExportCsvSafe -Rows $planRows -Path $def_PARAM_INTEGRATION_PLAN_CSV

    def_ShowProgress -Step 7 -Total 9 -Status "Build top10 local libs and PS15 matrices"
    $top10Rows = def_BuildTop10Libs
    $ps15Rows = def_BuildPS15Accelerators
    def_ExportCsvSafe -Rows $top10Rows -Path $def_PARAM_TOP10_LIBS_CSV
    def_ExportCsvSafe -Rows $ps15Rows -Path $def_PARAM_PS15_CSV

    def_ShowProgress -Step 8 -Total 9 -Status "Write summary and HTML dense UI report"

    $summary = [ordered]@{
        schema_version = "VIA_IntegrationFirstStep_Panorama_Summary_v0104"
        generated_at = (Get-Date).ToString("s")
        run_id = $def_PARAM_RUN_ID
        status = "VIA_INTEGRATION_FIRSTSTEP_PANORAMA_READY"
        risk = $(if (@($fileRows | Where-Object { $_.def_risk_triage -eq "REVIEW_REAL" }).Count -gt 0) { "MEDIUM_REVIEW_REQUIRED" } else { "LOW" })
        policy = [ordered]@{
            base_scan = "READ_ONLY"
            child_execution = $def_PARAM_ENABLE_CHILD_EXECUTION
            repair = $def_PARAM_ENABLE_REPAIR
            hydra_guard = $true
            max_rounds_recommended = 3
            used_tools_staged = $true
        }
        counts = [ordered]@{
            base_file_count = $fileRows.Count
            tool_count = $toolRows.Count
            tool_ok_count = @($toolRows | Where-Object { $_.def_exists }).Count
            tool_missing_count = @($toolRows | Where-Object { -not $_.def_exists }).Count
            high_risk_file_count = @($fileRows | Where-Object { $_.def_risk -eq "HIGH" }).Count
            real_high_file_count = @($fileRows | Where-Object { $_.def_risk_triage -eq "REVIEW_REAL" }).Count
            noise_reference_file_count = @($fileRows | Where-Object { $_.def_is_noise -eq $true }).Count
            medium_risk_file_count = @($fileRows | Where-Object { $_.def_risk -eq "MEDIUM" }).Count
            subsystem_flow_rows = $flowRows.Count
            integration_plan_rows = $planRows.Count
            top10_lib_rows = $top10Rows.Count
            ps15_rows = $ps15Rows.Count
        }
        outputs = [ordered]@{
            run_dir = $def_PARAM_RUN_DIR
            used_tools_dir = $def_PARAM_USED_TOOLS_DIR
            file_matrix_csv = $def_PARAM_FILE_MATRIX_CSV
            tool_staging_csv = $def_PARAM_TOOL_STAGING_CSV
            subsystem_flow_csv = $def_PARAM_SUBSYSTEM_FLOW_CSV
            integration_plan_csv = $def_PARAM_INTEGRATION_PLAN_CSV
            top10_libs_csv = $def_PARAM_TOP10_LIBS_CSV
            ps15_csv = $def_PARAM_PS15_CSV
            previous_state_csv = $def_PARAM_PREVIOUS_STATE_CSV
            summary_json = $def_PARAM_SUMMARY_JSON
            report_html = $def_PARAM_REPORT_HTML
            active_pointer = $def_PARAM_ACTIVE_POINTER
        }
    }

    $summary.base_file_count = $fileRows.Count

    def_WriteJson -Object $summary -Path $def_PARAM_SUMMARY_JSON -Depth 80

    def_WriteHtmlReport `
        -Summary $summary `
        -FileRows $fileRows `
        -ToolRows $toolRows `
        -SubsystemFlowRows $flowRows `
        -IntegrationPlanRows $planRows `
        -Top10Rows $top10Rows `
        -PS15Rows $ps15Rows `
        -PreviousRows $previousRows

    $pointer = [ordered]@{
        schema_version = "VIA_IntegrationFirstStep_ActivePointer_v0104"
        generated_at = (Get-Date).ToString("s")
        run_id = $def_PARAM_RUN_ID
        status = "ACTIVE_POINTER_READY"
        report_html = $def_PARAM_REPORT_HTML
        summary_json = $def_PARAM_SUMMARY_JSON
        used_tools_dir = $def_PARAM_USED_TOOLS_DIR
        file_matrix_csv = $def_PARAM_FILE_MATRIX_CSV
        subsystem_flow_csv = $def_PARAM_SUBSYSTEM_FLOW_CSV
        integration_plan_csv = $def_PARAM_INTEGRATION_PLAN_CSV
    }

    def_WriteJson -Object $pointer -Path $def_PARAM_ACTIVE_POINTER -Depth 60

    def_ShowProgress -Step 9 -Total 9 -Status "Complete"
    Write-Progress -Id 1 -Activity "VIA Integration FirstStep Panorama" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA INTEGRATION FIRSTSTEP PANORAMA COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status       : $($summary.status)"
    Write-Host "Risk         : $($summary.risk)"
    Write-Host "Base Files   : $($fileRows.Count)"
    Write-Host "Tools OK     : $(@($toolRows | Where-Object { $_.def_exists }).Count) / $($toolRows.Count)"
    Write-Host "High Risk    : $(@($fileRows | Where-Object { $_.def_risk -eq 'HIGH' }).Count) (raw danger-token)"
    Write-Host "Real High    : $(@($fileRows | Where-Object { $_.def_risk_triage -eq 'REVIEW_REAL' }).Count) (triaged, executable roles)"
    Write-Host "Noise (ref)  : $(@($fileRows | Where-Object { $_.def_is_noise -eq $true }).Count) (content/output reference only)"
    Write-Host "Medium Risk  : $(@($fileRows | Where-Object { $_.def_risk -eq 'MEDIUM' }).Count)"
    Write-Host "Flow Rows    : $($flowRows.Count)"
    Write-Host "Action Rows  : $($planRows.Count)"
    Write-Host ""
    Write-Host "Used Tools   : $def_PARAM_USED_TOOLS_DIR"
    Write-Host "Report HTML  : $def_PARAM_REPORT_HTML"
    Write-Host "Summary JSON : $def_PARAM_SUMMARY_JSON"
    Write-Host "Pointer JSON : $def_PARAM_ACTIVE_POINTER"
    Write-Host ""

    if ($def_PARAM_ENABLE_OPEN_REPORT -and (Test-Path -LiteralPath $def_PARAM_REPORT_HTML)) {
        Start-Process $def_PARAM_REPORT_HTML
    }

    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}

try {
    def_Main
} catch {
    def_WriteLine "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
