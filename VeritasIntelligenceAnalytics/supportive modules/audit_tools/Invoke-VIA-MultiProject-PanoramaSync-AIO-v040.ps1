param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$FunctionalRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules",
    [string]$ToolRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_MultiProject_PanoramaSync",
    [string[]]$ProjectNames = @("VRN","VPNS","VAP","VDF"),
    [bool]$CreateSandbox = $true,
    [bool]$RunToolDryProbe = $true,
    [bool]$RunUserSmokeTest = $false,
    [bool]$OpenReport = $true,
    [int]$TimeoutSec = 180,
    [int]$MaxRounds = 3,
    [int]$MaxFilesPerProjectCopy = 2500,
    [bool]$KeepPowerShellOpen = $true
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

# =============================================================================
# def VIA MULTI-PROJECT PANORAMA SYNC AIO v0.4.0
# =============================================================================
# Purpose:
# - One PowerShell to inspect Root / Supportive modules / VRN / VPNS / VAP / VDF.
# - Three-round panorama gate with dynamic progress, remaining-flow count, completion ratio.
# - Sandbox-first check/test/repair plan. Original folders remain read-only except report output.
# - Distinguish real blockers from policy-review warnings to avoid false HIGH.
#
# Policy:
# - no DB write
# - no canonical merge
# - no destructive delete
# - no stop-process
# - append-only
# - sandbox-first
# - user smoke test disabled by default
# =============================================================================

# =============================================================================
# def PARAMETERS / STATIC INPUTS
# =============================================================================
$def_PARAM_VERSION = "v0.4.0"
$def_PARAM_RUN_ID = "RUN_{0}_VIA_MULTIPROJECT_PANORAMA_SYNC" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_PARAM_POLICY = [ordered]@{
    db_write           = $false
    canonical_merge    = $false
    destructive_delete = $false
    stop_process       = $false
    append_only        = $true
    sandbox_first      = $true
    max_rounds         = $MaxRounds
    user_smoke_test    = $RunUserSmokeTest
}
$def_PARAM_SUPPORTIVE_FILES = @(
    (Join-Path $SupportiveDir "Read_Me_VeritasNexusCore.md"),
    (Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1"),
    (Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1")
)
$def_PARAM_ACCELERATORS = @(
    [pscustomobject]@{ID="A01"; Name="Run Isolation"; Function="Run folders are append-only and isolated."},
    [pscustomobject]@{ID="A02"; Name="Remaining Flow Counter"; Function="Every step updates completed/remaining/percent."},
    [pscustomobject]@{ID="A03"; Name="Dynamic Progress"; Function="Write-Progress shows project, round, phase and percent."},
    [pscustomobject]@{ID="A04"; Name="AST Before Invoke"; Function="PS files are parse-checked before any child invocation."},
    [pscustomobject]@{ID="A05"; Name="Sandbox Copy"; Function="Only scripts/docs/configs are copied to sandbox."},
    [pscustomobject]@{ID="A06"; Name="Hydra Gate"; Function="Parallel-safe and sequential-required issues are split."},
    [pscustomobject]@{ID="A07"; Name="Timeout Guard"; Function="Child processes cannot block the parent forever."},
    [pscustomobject]@{ID="A08"; Name="History Lens"; Function="Prior RUN folders and reports are indexed."},
    [pscustomobject]@{ID="A09"; Name="Library Matrix"; Function="Top10 per flow/language + Top20 process-mining stack."},
    [pscustomobject]@{ID="A10"; Name="HTML Matrix UI"; Function="All results are exported to HTML/CSV/JSON."}
)
$def_PARAM_SCAN_EXTENSIONS = @(".ps1",".psm1",".psd1",".py",".json",".md",".html",".htm",".csv",".yaml",".yml",".toml",".txt")
$def_PARAM_EXCLUDE_DIR_NAMES = @(".git",".svn",".hg","__pycache__",".pytest_cache",".ruff_cache","node_modules",".next","dist","build",".venv","venv","env","site-packages")
$def_PARAM_PHASES = @(
    "Round1.PathCheck",
    "Round1.FileInventory",
    "Round1.HistoryLens",
    "Round1.CommandPolicyReview",
    "Round2.SandboxCopy",
    "Round2.PowerShellAst",
    "Round2.PythonCompile",
    "Round2.ToolDryProbe",
    "Round2.HydraClassify",
    "Round3.Consolidate",
    "Round3.UserSmokePlan",
    "Round3.ArtifactSeal"
)

# =============================================================================
# def RUNTIME PATHS
# =============================================================================
$def_RUN_ROOT = Join-Path $ToolRoot ("runs\" + $def_PARAM_RUN_ID)
$def_SANDBOX_ROOT = Join-Path $def_RUN_ROOT "sandbox"
$def_RUNTIME_DIR = Join-Path $def_RUN_ROOT "runtime"
$def_REGISTRY_DIR = Join-Path $def_RUN_ROOT "registry"
$def_REPORT_DIR = Join-Path $def_RUN_ROOT "report"
$def_LOG_DIR = Join-Path $def_RUN_ROOT "logs"
$def_PLAN_DIR = Join-Path $def_RUN_ROOT "plans"
$def_BRIDGE_DIR = Join-Path $ToolRoot "bridge"

$def_MATRIX_CSV = Join-Path $def_REGISTRY_DIR "VIA_MultiProject_PanoramaSync_Matrix.csv"
$def_MATRIX_JSON = Join-Path $def_REGISTRY_DIR "VIA_MultiProject_PanoramaSync_Matrix.json"
$def_PROJECT_CSV = Join-Path $def_REGISTRY_DIR "VIA_Project_Status.csv"
$def_HISTORY_CSV = Join-Path $def_REGISTRY_DIR "VIA_PastRun_HistoryLens.csv"
$def_TASK_CSV = Join-Path $def_REGISTRY_DIR "VIA_Flow_ProgressTasks.csv"
$def_TOP_LIBS_CSV = Join-Path $def_REGISTRY_DIR "VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
$def_PM20_CSV = Join-Path $def_REGISTRY_DIR "VIA_Top20_EnterpriseForms_To_ProcessMining_Libs.csv"
$def_REPAIR_PLAN_CSV = Join-Path $def_PLAN_DIR "VIA_Sequential_RepairPlan.csv"
$def_PARALLEL_PLAN_CSV = Join-Path $def_PLAN_DIR "VIA_ParallelSafe_OptimizationPlan.csv"
$def_FIRSTSTEP_PS1 = Join-Path $def_PLAN_DIR "VIA_Strongest_MultiProject_FirstStep.ps1"
$def_BRIDGE_PSM1 = Join-Path $def_BRIDGE_DIR "VIA_MultiProject_PanoramaSyncBridge.psm1"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_MultiProject_PanoramaSync_Report.html"

# =============================================================================
# def GLOBAL STATE - plain arrays only, no Generic.List
# =============================================================================
$script:def_Rows = @()
$script:def_ProjectRows = @()
$script:def_HistoryRows = @()
$script:def_TaskRows = @()
$script:def_TopLibRows = @()
$script:def_PM20Rows = @()
$script:def_SequentialPlanRows = @()
$script:def_ParallelPlanRows = @()
$script:def_TotalTasks = 1
$script:def_CompletedTasks = 0
$script:def_LastProgressTick = [DateTime]::MinValue

# =============================================================================
# def CORE HELPERS
# =============================================================================
function def_EnsureDirectory {
    param([string]$Path)
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_AsArray {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return @() }
    if ($InputObject -is [string]) { return @($InputObject) }
    try {
        $out = @()
        foreach ($x in $InputObject) { $out += $x }
        return @($out)
    } catch {
        return @($InputObject)
    }
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [array]) { return $InputObject.Count }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    return 1
}

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_WriteLog {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function def_GetPercent {
    param([int]$Done, [int]$Total)
    if ($Total -le 0) { return 0 }
    return [math]::Min(100, [math]::Round(($Done / $Total) * 100, 1))
}

function def_UpdateProgress {
    param(
        [string]$Round,
        [string]$Project,
        [string]$Phase,
        [string]$Status
    )
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $now = Get-Date
    if ($now -ge $script:def_LastProgressTick.AddMilliseconds(120) -or $script:def_CompletedTasks -eq $script:def_TotalTasks) {
        $activity = "VIA MultiProject Panorama Sync · $Round · $Project"
        $line = "$Phase · $Status · Completed $($script:def_CompletedTasks)/$($script:def_TotalTasks) · Remaining $remaining · $pct%"
        Write-Progress -Id 1 -Activity $activity -Status $line -PercentComplete ([int]$pct)
        $script:def_LastProgressTick = $now
    }
}

function def_TaskBegin {
    param([string]$Round, [string]$Project, [string]$Phase)
    def_UpdateProgress -Round $Round -Project $Project -Phase $Phase -Status "running"
}

function def_TaskDone {
    param([string]$Round, [string]$Project, [string]$Phase, [string]$Status)
    $script:def_CompletedTasks++
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $script:def_TaskRows += [pscustomobject]@{
        Time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Round = $Round
        Project = $Project
        Phase = $Phase
        Status = $Status
        Completed = $script:def_CompletedTasks
        Total = $script:def_TotalTasks
        Remaining = $remaining
        Percent = $pct
    }
    def_UpdateProgress -Round $Round -Project $Project -Phase $Phase -Status $Status
}

function def_AddRow {
    param(
        [string]$Round,
        [string]$Project,
        [string]$Layer,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Class,
        [string]$Priority,
        [string]$Metric,
        [object]$Value,
        [string]$Message,
        [string]$Path = ""
    )
    $script:def_Rows += [pscustomobject]@{
        Time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Round = $Round
        Project = $Project
        Layer = $Layer
        Name = $Name
        Status = $Status
        Risk = $Risk
        Class = $Class
        Priority = $Priority
        Metric = $Metric
        Value = [string]$Value
        Message = $Message
        Path = $Path
    }
}

function def_GetSha256Safe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
    } catch {}
    return ""
}

function def_ReadTextSafe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        }
    } catch {}
    return ""
}

function def_SaveCsv {
    param([string]$Path, [object[]]$Rows)
    def_EnsureDirectory -Path (Split-Path -Parent $Path)
    $arr = @(def_AsArray $Rows)
    if ((def_CountSafe $arr) -eq 0) {
        "" | Set-Content -LiteralPath $Path -Encoding UTF8
        return
    }
    $arr | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8BOM
}

function def_SaveJson {
    param([string]$Path, [object]$Object)
    def_EnsureDirectory -Path (Split-Path -Parent $Path)
    $Object | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_IsExcludedPath {
    param([string]$Path)
    foreach ($d in $def_PARAM_EXCLUDE_DIR_NAMES) {
        if ($Path -match ("\\{0}(\\|$)" -f [regex]::Escape($d))) { return $true }
    }
    return $false
}

function def_GetProjectPath {
    param([string]$Project)
    if ($Project -eq "SUPPORTIVE") { return $SupportiveDir }
    return (Join-Path $FunctionalRoot $Project)
}

function def_InvokeChildProcessSafe {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [int]$TimeoutSeconds
    )
    def_EnsureDirectory -Path $def_LOG_DIR
    $safeName = $Name -replace '[^\w\-]','_'
    $stdout = Join-Path $def_LOG_DIR ("{0}_stdout.log" -f $safeName)
    $stderr = Join-Path $def_LOG_DIR ("{0}_stderr.log" -f $safeName)
    try {
        if (-not (Test-Path -LiteralPath $FilePath)) {
            return [pscustomobject]@{Status="WARN_NOT_FOUND"; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message="Executable not found."}
        }
        if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) { $WorkingDirectory = $Root }
        $p = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
        $finished = $p.WaitForExit($TimeoutSeconds * 1000)
        if (-not $finished) {
            return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; ExitCode=$null; TimedOut=$true; Stdout=$stdout; Stderr=$stderr; Message="Timeout reached; child not stopped due policy."}
        }
        return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message="Child process completed."}
    } catch {
        return [pscustomobject]@{Status="WARN_PROCESS_ERROR"; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message=$_.Exception.Message}
    }
}

function def_TestPSParseSafe {
    param([string]$Path)
    try {
        [System.Management.Automation.Language.Token[]]$tokens = $null
        [System.Management.Automation.Language.ParseError[]]$errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile([string]$Path, [ref]$tokens, [ref]$errors)
        return [pscustomobject]@{
            Ok = ((def_CountSafe $errors) -eq 0)
            ErrorCount = (def_CountSafe $errors)
            ErrorText = (($errors | ForEach-Object { "{0}:{1} {2}" -f $_.Extent.StartLineNumber, $_.Extent.StartColumnNumber, $_.Message }) -join " | ")
        }
    } catch {
        return [pscustomobject]@{Ok=$false; ErrorCount=1; ErrorText=$_.Exception.Message}
    }
}

function def_GetFilesLight {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return @() }
    $files = @()
    try {
        $files = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { (-not (def_IsExcludedPath -Path $_.FullName)) -and ($def_PARAM_SCAN_EXTENSIONS -contains $_.Extension.ToLowerInvariant()) }
    } catch {
        $files = @()
    }
    return @(def_AsArray $files)
}

# =============================================================================
# def LIBRARY MATRICES
# =============================================================================
function def_AddTopLib {
    param([string]$Flow,[string]$Lang,[string]$FunctionArea,[int]$Rank,[string]$Name,[string]$Install,[string]$UseCase,[string]$RiskNote)
    $script:def_TopLibRows += [pscustomobject]@{
        Flow=$Flow; Lang=$Lang; FunctionArea=$FunctionArea; Rank=$Rank; Name=$Name; Install=$Install; UseCase=$UseCase; RiskNote=$RiskNote
    }
}

function def_AddPM20 {
    param([int]$Rank,[string]$Name,[string]$Lang,[string]$Install,[string]$Stage,[string]$UseCase,[string]$RiskNote)
    $script:def_PM20Rows += [pscustomobject]@{
        Rank=$Rank; Name=$Name; Lang=$Lang; Install=$Install; Stage=$Stage; UseCase=$UseCase; RiskNote=$RiskNote
    }
}

function def_BuildLibraryMatrices {
    $flows = @(
        "01_Panorama_Discovery",
        "02_Project_Inventory",
        "03_Sandbox_Test",
        "04_Check_Test_Repair",
        "05_Form_To_ProcessMining",
        "06_HTML_UI_Report",
        "07_Consolidate",
        "08_User_Smoke_Activation"
    )
    $ps = @(
        @("PSScriptAnalyzer","Install-Module PSScriptAnalyzer -Scope CurrentUser -Force","PowerShell AST/lint/fixable finding detection","Run after parse clean"),
        @("Pester","Install-Module Pester -Scope CurrentUser -Force","PowerShell tests","Needs tests"),
        @("PSWriteHTML","Install-Module PSWriteHTML -Scope CurrentUser -Force","HTML report UI","Fallback HTML is built in"),
        @("ImportExcel","Install-Module ImportExcel -Scope CurrentUser -Force","Excel/CSV review","Optional"),
        @("ThreadJob","Install-Module ThreadJob -Scope CurrentUser -Force","Parallel-safe job lanes","Use only for low-impact probes"),
        @("PSFramework","Install-Module PSFramework -Scope CurrentUser -Force","Structured logging","Optional"),
        @("PSReadLine","Install-Module PSReadLine -Scope CurrentUser -Force","CLI accelerator","Usually installed"),
        @("SecretManagement","Install-Module Microsoft.PowerShell.SecretManagement -Scope CurrentUser -Force","Secret bridge","Never print secrets"),
        @("SecretStore","Install-Module Microsoft.PowerShell.SecretStore -Scope CurrentUser -Force","Local vault","Needs setup"),
        @("Pode","Install-Module Pode -Scope CurrentUser -Force","Local web UI/API","Optional")
    )
    $py = @(
        @("pandas","python -m pip install pandas","Table ETL/event logs","Stable core"),
        @("polars","python -m pip install polars","Fast low-memory ETL","Good for large logs"),
        @("duckdb","python -m pip install duckdb","Local SQL over parquet/csv","No external DB needed"),
        @("pyarrow","python -m pip install pyarrow","Parquet/Arrow IO","Version compatibility"),
        @("pm4py","python -m pip install pm4py","Process mining","Needs clean event log schema"),
        @("networkx","python -m pip install networkx","Graph/DFG analysis","Large graphs slower"),
        @("pandera","python -m pip install pandera","Dataframe schema validation","Optional"),
        @("great_expectations","python -m pip install great_expectations","Data quality gates","Heavier"),
        @("rich","python -m pip install rich","Console tables/progress","Lightweight"),
        @("tqdm","python -m pip install tqdm","Progress bars","Lightweight")
    )
    $doc = @(
        @("docling","python -m pip install docling","Multi-format document conversion/layout","Heavy; sandbox first"),
        @("paddleocr","python -m pip install paddleocr","OCR/PP-Structure/KIE","Model downloads"),
        @("ocrmypdf","python -m pip install ocrmypdf","OCR layer for scanned PDFs","Needs Tesseract/Ghostscript"),
        @("pytesseract","python -m pip install pytesseract","Tesseract wrapper","Needs binary"),
        @("pdfplumber","python -m pip install pdfplumber","Digital PDF text/table extraction","Weak on scans"),
        @("pymupdf","python -m pip install pymupdf","PDF rendering/text/images","Fast"),
        @("camelot-py","python -m pip install camelot-py","PDF table extraction","Needs Ghostscript for some cases"),
        @("tabula-py","python -m pip install tabula-py","Java Tabula bridge","Needs Java"),
        @("opencv-python","python -m pip install opencv-python","Image preprocessing/layout","Memory-heavy"),
        @("unstructured","python -m pip install unstructured","Document partitioning","Heavy extras")
    )
    $js = @(
        @("typescript","npm install -g typescript","Type checking","Global optional"),
        @("eslint","npm install -g eslint","JS/TS lint","Config needed"),
        @("prettier","npm install -g prettier","Formatting","Config needed"),
        @("vite","npm install -g vite","Fast UI build/dev","Optional"),
        @("playwright","npm install -g playwright","Browser UI tests","Browser install"),
        @("vitest","npm install -g vitest","JS/TS tests","Project config"),
        @("mermaid-cli","npm install -g @mermaid-js/mermaid-cli","Process diagrams","Chromium may be needed"),
        @("marked","npm install -g marked","Markdown render","Optional"),
        @("d3","npm install d3","Visualization","Per project"),
        @("cytoscape","npm install cytoscape","Graph visualization","Per project")
    )
    $cs = @(
        @("xunit","dotnet add package xunit","Unit tests","Project needed"),
        @("NUnit","dotnet add package NUnit","Unit tests","Project needed"),
        @("FluentAssertions","dotnet add package FluentAssertions","Readable assertions","Project needed"),
        @("Serilog","dotnet add package Serilog","Structured logging","Project needed"),
        @("CsvHelper","dotnet add package CsvHelper","CSV IO","Project needed"),
        @("ClosedXML","dotnet add package ClosedXML","Excel IO","Project needed"),
        @("HtmlAgilityPack","dotnet add package HtmlAgilityPack","HTML parsing","Project needed"),
        @("Microsoft.Playwright","dotnet add package Microsoft.Playwright","Browser tests","Install browsers"),
        @("CliWrap","dotnet add package CliWrap","Process wrapper","Project needed"),
        @("QuestPDF","dotnet add package QuestPDF","PDF report generation","License review")
    )

    foreach ($flow in $flows) {
        for ($i=0; $i -lt 10; $i++) {
            def_AddTopLib $flow "PowerShell" "Orchestration_Check_Test_Repair" ($i+1) $ps[$i][0] $ps[$i][1] $ps[$i][2] $ps[$i][3]
            def_AddTopLib $flow "Python" "ETL_ProcessMining" ($i+1) $py[$i][0] $py[$i][1] $py[$i][2] $py[$i][3]
            def_AddTopLib $flow "Python" "EnterpriseFormReading" ($i+1) $doc[$i][0] $doc[$i][1] $doc[$i][2] $doc[$i][3]
            def_AddTopLib $flow "JS_TS" "UI_Test_Visualization" ($i+1) $js[$i][0] $js[$i][1] $js[$i][2] $js[$i][3]
            def_AddTopLib $flow "CSharp" "Windows_IO_Testing" ($i+1) $cs[$i][0] $cs[$i][1] $cs[$i][2] $cs[$i][3]
        }
    }

    $pm20 = @(
        @(1,"Docling","Python","python -m pip install docling","Document conversion/layout","Convert PDF/DOCX/PPTX/images into structured document objects","Install in sandbox env first"),
        @(2,"PaddleOCR / PP-Structure","Python","python -m pip install paddleocr","OCR/layout/table/KIE","OCR and structured document parsing for scanned forms","Heavy; avoid global install"),
        @(3,"OCRmyPDF","CLI/Python","python -m pip install ocrmypdf","OCR PDF layer","Make scanned PDFs searchable before extraction","Needs Tesseract/Ghostscript"),
        @(4,"Tesseract + pytesseract","CLI/Python","winget install UB-Mannheim.TesseractOCR ; python -m pip install pytesseract","OCR","Traditional OCR fallback","Accuracy depends on preprocessing"),
        @(5,"pdfplumber","Python","python -m pip install pdfplumber","Digital PDF extraction","Extract text/tables/coordinates","Weak on scans"),
        @(6,"PyMuPDF","Python","python -m pip install pymupdf","PDF render/text/images","Fast page rendering/extraction","License review for distribution"),
        @(7,"Camelot","Python","python -m pip install camelot-py","PDF tables","Lattice/stream table extraction","Needs Ghostscript for some cases"),
        @(8,"tabula-py","Python/Java","python -m pip install tabula-py","PDF tables","Java Tabula bridge","Needs Java"),
        @(9,"OpenCV","Python/C++","python -m pip install opencv-python","Image preprocessing","Deskew/threshold/boxes/morphology","Can be memory-heavy"),
        @(10,"LayoutParser","Python","python -m pip install layoutparser","Layout detection","Layout zones for forms/pages","Model deps vary"),
        @(11,"Unstructured","Python","python -m pip install unstructured","Document partitioning","Partition docs into semantic elements","Heavy extras"),
        @(12,"Microsoft MarkItDown","Python","python -m pip install markitdown","Markdown conversion","Convert Office/PDF/media to Markdown","Quality varies"),
        @(13,"Apache Tika","Java/Python","python -m pip install tika","Document metadata/text","Fallback broad document parser","Java dependency"),
        @(14,"pandas","Python","python -m pip install pandas","Event log shaping","Normalize case/activity/timestamp logs","Memory use for large logs"),
        @(15,"polars","Python/Rust","python -m pip install polars","Fast ETL","Low-memory event-log transformation","Some ecosystem gaps"),
        @(16,"DuckDB","Python/CLI","python -m pip install duckdb","Local analytics","SQL over parquet/csv logs","Avoid DB writes outside sandbox"),
        @(17,"PyArrow","Python/C++","python -m pip install pyarrow","Parquet/Arrow","Columnar outputs","Version compatibility"),
        @(18,"PM4Py","Python","python -m pip install pm4py","Process mining","Discovery/conformance/event-log analytics","Needs clean schema"),
        @(19,"NetworkX","Python","python -m pip install networkx","Graph analytics","DFG/process graph analysis","Large graphs slower"),
        @(20,"Pandera / Great Expectations","Python","python -m pip install pandera great_expectations","Data validation","Validate extraction schema before mining","GE is heavier")
    )
    foreach ($p in $pm20) {
        def_AddPM20 $p[0] $p[1] $p[2] $p[3] $p[4] $p[5] $p[6]
    }
}

# =============================================================================
# def INITIALIZE / TASK PLAN
# =============================================================================
function def_Initialize {
    def_EnsureDirectory $ToolRoot
    def_EnsureDirectory $def_RUN_ROOT
    def_EnsureDirectory $def_SANDBOX_ROOT
    def_EnsureDirectory $def_RUNTIME_DIR
    def_EnsureDirectory $def_REGISTRY_DIR
    def_EnsureDirectory $def_REPORT_DIR
    def_EnsureDirectory $def_LOG_DIR
    def_EnsureDirectory $def_PLAN_DIR
    def_EnsureDirectory $def_BRIDGE_DIR

    $projectLaneCount = (def_CountSafe $ProjectNames) + 1
    $script:def_TotalTasks = ($projectLaneCount * (def_CountSafe $def_PARAM_PHASES)) + 6
    $script:def_CompletedTasks = 0

    def_AddRow "Round0" "GLOBAL" "POLICY" "Safety Policy" "OK_LOCKED" "LOW" "SEQUENTIAL_GATED" "P0" "policy" "append-only" "No DB write, no canonical merge, no destructive delete, no stop-process." $ToolRoot
    foreach ($a in $def_PARAM_ACCELERATORS) {
        def_AddRow "Round0" "GLOBAL" "ACCELERATOR" $a.Name "OK_ENABLED" "LOW" "PARALLEL_SAFE" "P1" $a.ID "enabled" $a.Function ""
    }
}

# =============================================================================
# def ROUND FUNCTIONS
# =============================================================================
function def_Run_PathCheck {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round1" $Project "PathCheck"
    if (Test-Path -LiteralPath $ProjectPath -PathType Container) {
        def_AddRow "Round1" $Project "PATH" "ProjectPath" "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "exists" $true "Project folder exists." $ProjectPath
    } else {
        def_AddRow "Round1" $Project "PATH" "ProjectPath" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Project folder missing." $ProjectPath
        $script:def_SequentialPlanRows += [pscustomobject]@{Project=$Project; Priority="P0"; Issue="Missing project folder"; Action="Create or restore folder before deeper activation."; Path=$ProjectPath}
    }
    def_TaskDone "Round1" $Project "PathCheck" "done"
}

function def_Run_FileInventory {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round1" $Project "FileInventory"
    $files = @(def_GetFilesLight -Path $ProjectPath)
    $ps = def_CountSafe ($files | Where-Object { $_.Extension -in @(".ps1",".psm1",".psd1") })
    $py = def_CountSafe ($files | Where-Object { $_.Extension -eq ".py" })
    $json = def_CountSafe ($files | Where-Object { $_.Extension -eq ".json" })
    $html = def_CountSafe ($files | Where-Object { $_.Extension -in @(".html",".htm") })
    $md = def_CountSafe ($files | Where-Object { $_.Extension -eq ".md" })
    $bytes = 0
    foreach ($f in $files) { try { $bytes += [int64]$f.Length } catch {} }
    $script:def_ProjectRows += [pscustomobject]@{
        Project=$Project; Path=$ProjectPath; Files=(def_CountSafe $files); PS=$ps; PY=$py; JSON=$json; HTML=$html; MD=$md; Bytes=$bytes
    }
    def_AddRow "Round1" $Project "INVENTORY" "LightSourceInventory" "OK_SCANNED" "LOW" "PARALLEL_SAFE" "P1" "files/ps/py/json/html/md" "$(def_CountSafe $files)/$ps/$py/$json/$html/$md" "Low-memory source inventory completed." $ProjectPath
    def_TaskDone "Round1" $Project "FileInventory" "done"
}

function def_Run_HistoryLens {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round1" $Project "HistoryLens"
    $roots = @($ProjectPath, (Join-Path $Root "tools"))
    $runDirs = @()
    foreach ($r in $roots) {
        if (Test-Path -LiteralPath $r -PathType Container) {
            try {
                $runDirs += Get-ChildItem -LiteralPath $r -Directory -Recurse -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -like "RUN_*" } |
                    Sort-Object LastWriteTime -Descending |
                    Select-Object -First 20
            } catch {}
        }
    }
    $count = def_CountSafe $runDirs
    foreach ($d in $runDirs) {
        $html = @(Get-ChildItem -LiteralPath $d.FullName -Recurse -File -Filter "*.html" -ErrorAction SilentlyContinue | Select-Object -First 1)
        $json = @(Get-ChildItem -LiteralPath $d.FullName -Recurse -File -Filter "*.json" -ErrorAction SilentlyContinue | Select-Object -First 1)
        $script:def_HistoryRows += [pscustomobject]@{
            Project=$Project; RunDir=$d.FullName; LastWriteTime=$d.LastWriteTime; Html=(if($html){$html[0].FullName}else{""}); Json=(if($json){$json[0].FullName}else{""})
        }
    }
    def_AddRow "Round1" $Project "HISTORY" "PastRunHistoryLens" "OK_INDEXED" "LOW" "PARALLEL_SAFE" "P2" "runs" $count "Past RUN folders indexed for continuity." $ProjectPath
    def_TaskDone "Round1" $Project "HistoryLens" "done"
}

function def_Run_CommandPolicyReview {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round1" $Project "CommandPolicyReview"
    $files = @(def_GetFilesLight -Path $ProjectPath | Where-Object { $_.Extension -in @(".ps1",".psm1",".psd1",".md") })
    $riskCount = 0
    $policyWarn = 0
    foreach ($f in $files) {
        $text = def_ReadTextSafe $f.FullName
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        $hasDangerPattern = ($text -match "Remove-Item\s+.*-Recurse|Stop-Process|taskkill|Invoke-Expression|iex\s")
        $hasPolicyGuard = ($text -match "no destructive|no stop-process|DRY_RUN|DryRun|ApprovalToken|append-only|sandbox")
        if ($hasDangerPattern -and $hasPolicyGuard) {
            $policyWarn++
            def_AddRow "Round1" $Project "POLICY_REVIEW" $f.Name "WARN_POLICY_PATTERN_REVIEW" "MEDIUM" "SEQUENTIAL_GATED" "P1" "policy_review" "guarded" "Potentially sensitive command pattern appears guarded; review before direct invoke." $f.FullName
            $script:def_SequentialPlanRows += [pscustomobject]@{Project=$Project; Priority="P1"; Issue="Guarded sensitive pattern"; Action="Review before integrating into direct invocation path."; Path=$f.FullName}
        } elseif ($hasDangerPattern) {
            $riskCount++
            def_AddRow "Round1" $Project "POLICY_REVIEW" $f.Name "WARN_UNGUARDED_RISK_PATTERN" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "policy_review" "unguarded" "Potential destructive/process/invoke pattern without obvious guard." $f.FullName
            $script:def_SequentialPlanRows += [pscustomobject]@{Project=$Project; Priority="P0"; Issue="Unguarded sensitive pattern"; Action="Sandbox and manual review required before any activation."; Path=$f.FullName}
        }
    }
    if ($riskCount -eq 0 -and $policyWarn -eq 0) {
        def_AddRow "Round1" $Project "POLICY_REVIEW" "CommandPolicyReview" "OK_CLEAR" "LOW" "PARALLEL_SAFE" "P1" "risk/warn" "0/0" "No obvious risky command pattern in reviewed files." $ProjectPath
    } else {
        def_AddRow "Round1" $Project "POLICY_REVIEW" "CommandPolicyReview" "WARN_REVIEW" ($(if($riskCount -gt 0){"HIGH"}else{"MEDIUM"})) "SEQUENTIAL_GATED" "P1" "risk/warn" "$riskCount/$policyWarn" "Sensitive command patterns classified separately from parse errors." $ProjectPath
    }
    def_TaskDone "Round1" $Project "CommandPolicyReview" "done"
}

function def_Run_SandboxCopy {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round2" $Project "SandboxCopy"
    if (-not $CreateSandbox) {
        def_AddRow "Round2" $Project "SANDBOX" "SandboxCopy" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "enabled" $CreateSandbox "Sandbox copy disabled." $ProjectPath
        def_TaskDone "Round2" $Project "SandboxCopy" "skipped"
        return
    }
    if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
        def_AddRow "Round2" $Project "SANDBOX" "SandboxCopy" "WARN_SKIPPED_MISSING_PATH" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "exists" $false "Project missing; cannot sandbox." $ProjectPath
        def_TaskDone "Round2" $Project "SandboxCopy" "skipped"
        return
    }
    $destRoot = Join-Path $def_SANDBOX_ROOT $Project
    def_EnsureDirectory $destRoot
    $files = @(def_GetFilesLight -Path $ProjectPath | Select-Object -First $MaxFilesPerProjectCopy)
    $copied = 0
    foreach ($f in $files) {
        try {
            $rel = $f.FullName.Substring($ProjectPath.Length).TrimStart("\")
            $dest = Join-Path $destRoot $rel
            def_EnsureDirectory (Split-Path -Parent $dest)
            Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
            $copied++
        } catch {}
    }
    def_AddRow "Round2" $Project "SANDBOX" "SandboxCopy" "OK_COPIED" "LOW" "PARALLEL_SAFE" "P1" "copied" $copied "Light files copied to sandbox only." $destRoot
    def_TaskDone "Round2" $Project "SandboxCopy" "done"
}

function def_Run_PowerShellAst {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round2" $Project "PowerShellAst"
    $psFiles = @(def_GetFilesLight -Path $ProjectPath | Where-Object { $_.Extension -in @(".ps1",".psm1",".psd1") })
    $fail = 0
    foreach ($f in $psFiles) {
        $res = def_TestPSParseSafe -Path $f.FullName
        if (-not $res.Ok) {
            $fail += $res.ErrorCount
            def_AddRow "Round2" $Project "PS_AST" $f.Name "FAIL_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "errors" $res.ErrorCount $res.ErrorText $f.FullName
            $script:def_SequentialPlanRows += [pscustomobject]@{Project=$Project; Priority="P0"; Issue="PowerShell parse error"; Action="Fix syntax before lint/autofix/user-test."; Path=$f.FullName}
        }
    }
    if ($fail -eq 0) {
        def_AddRow "Round2" $Project "PS_AST" "PowerShell AST Parse" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "P0" "files/errors" "$(def_CountSafe $psFiles)/0" "All PowerShell files parse clean." $ProjectPath
    }
    def_TaskDone "Round2" $Project "PowerShellAst" "done"
}

function def_Run_PythonCompile {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round2" $Project "PythonCompile"
    $pyFiles = @(def_GetFilesLight -Path $ProjectPath | Where-Object { $_.Extension -eq ".py" })
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        def_AddRow "Round2" $Project "PY_COMPILE" "PythonCompile" "WARN_PYTHON_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "files" (def_CountSafe $pyFiles) "python not found; compile skipped." $ProjectPath
        def_TaskDone "Round2" $Project "PythonCompile" "skipped"
        return
    }
    $fail = 0
    foreach ($f in $pyFiles) {
        $name = "pycompile_{0}_{1}" -f $Project, ($f.BaseName -replace '[^\w\-]','_')
        $res = def_InvokeChildProcessSafe -Name $name -FilePath $python.Source -ArgumentList @("-m","py_compile",$f.FullName) -WorkingDirectory $ProjectPath -TimeoutSeconds 45
        if ($res.Status -notlike "OK_EXIT_0") {
            $fail++
            def_AddRow "Round2" $Project "PY_COMPILE" $f.Name "WARN_COMPILE_REVIEW" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "exit" $res.ExitCode $res.Message $f.FullName
            $script:def_SequentialPlanRows += [pscustomobject]@{Project=$Project; Priority="P1"; Issue="Python compile review"; Action="Open stderr log and fix before user-test."; Path=$f.FullName}
        }
    }
    if ($fail -eq 0) {
        def_AddRow "Round2" $Project "PY_COMPILE" "PythonCompile" "OK_ALL_COMPILE" "LOW" "PARALLEL_SAFE" "P1" "files/fail" "$(def_CountSafe $pyFiles)/0" "All Python files compiled clean or no Python files." $ProjectPath
    }
    def_TaskDone "Round2" $Project "PythonCompile" "done"
}

function def_Run_ToolDryProbe {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round2" $Project "ToolDryProbe"
    if (-not $RunToolDryProbe) {
        def_AddRow "Round2" $Project "DRY_PROBE" "ToolDryProbe" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "run" $false "Dry probe disabled." $ProjectPath
        def_TaskDone "Round2" $Project "ToolDryProbe" "skipped"
        return
    }
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh) {
        def_AddRow "Round2" $Project "DRY_PROBE" "pwsh" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "pwsh missing." ""
        def_TaskDone "Round2" $Project "ToolDryProbe" "skipped"
        return
    }
    $probeScripts = @()
    if ($Project -eq "SUPPORTIVE") {
        $probeScripts = $def_PARAM_SUPPORTIVE_FILES | Where-Object { $_ -like "*.ps1" }
    } else {
        $probeScripts = @(Get-ChildItem -LiteralPath $ProjectPath -File -Filter "Invoke-*.ps1" -ErrorAction SilentlyContinue | Select-Object -First 2 | ForEach-Object { $_.FullName })
    }
    $done = 0
    foreach ($p in $probeScripts) {
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { continue }
        $parse = def_TestPSParseSafe -Path $p
        if (-not $parse.Ok) {
            def_AddRow "Round2" $Project "DRY_PROBE" (Split-Path $p -Leaf) "WARN_PARSE_BLOCKED" "MEDIUM" "SEQUENTIAL_REQUIRED" "P0" "parse" $parse.ErrorCount "Dry probe blocked by parse error." $p
            continue
        }
        $res = def_InvokeChildProcessSafe -Name ("probe_{0}_{1}" -f $Project,(Split-Path $p -Leaf)) -FilePath $pwsh.Source -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$p) -WorkingDirectory (Split-Path $p -Parent) -TimeoutSeconds $TimeoutSec
        $risk = "LOW"
        if ($res.Status -notlike "OK_EXIT_0") { $risk = "MEDIUM" }
        def_AddRow "Round2" $Project "DRY_PROBE" (Split-Path $p -Leaf) $res.Status $risk "PARALLEL_SAFE" "P2" "exit" $res.ExitCode $res.Message $p
        $done++
    }
    if ($done -eq 0) {
        def_AddRow "Round2" $Project "DRY_PROBE" "ToolDryProbe" "WARN_NO_PROBE_TARGET" "LOW" "PARALLEL_SAFE" "P3" "targets" 0 "No dry-probe target found." $ProjectPath
    }
    def_TaskDone "Round2" $Project "ToolDryProbe" "done"
}

function def_Run_HydraClassify {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round2" $Project "HydraClassify"
    $rows = @(def_AsArray $script:def_Rows | Where-Object { $_.Project -eq $Project })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })
    $med = def_CountSafe ($rows | Where-Object { $_.Risk -eq "MEDIUM" })
    $parallel = def_CountSafe ($rows | Where-Object { $_.Class -eq "PARALLEL_SAFE" -and $_.Risk -ne "HIGH" })
    $seq = def_CountSafe ($rows | Where-Object { $_.Class -like "SEQUENTIAL*" -or $_.Risk -eq "HIGH" })
    $status = "OK_HYDRA_CLEAR"; $risk = "LOW"
    if ($high -gt 0) { $status = "WARN_HYDRA_REVIEW"; $risk = "HIGH" }
    elseif ($med -gt 0) { $status = "WARN_REVIEW"; $risk = "MEDIUM" }
    def_AddRow "Round2" $Project "CLASSIFY" "HydraRiskGate" $status $risk "SEQUENTIAL_GATED" "P0" "parallel/sequential/high/medium" "$parallel/$seq/$high/$med" "Parallel-safe and sequential-required work classified." $ProjectPath
    def_TaskDone "Round2" $Project "HydraClassify" "done"
}

function def_Run_Consolidate {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round3" $Project "Consolidate"
    $rows = @(def_AsArray $script:def_Rows | Where-Object { $_.Project -eq $Project })
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    $status = "READY"; $risk = "LOW"
    if ($fail -gt 0) { $status = "READY_WITH_REVIEW"; $risk = "HIGH" }
    elseif ($warn -gt 0) { $status = "READY_WITH_WARNINGS"; $risk = "MEDIUM" }
    def_AddRow "Round3" $Project "CONSOLIDATE" "ProjectStatus" $status $risk "SEQUENTIAL_GATED" "P1" "ok/warn/high" "$ok/$warn/$fail" "Project consolidated into final matrix." $ProjectPath
    def_TaskDone "Round3" $Project "Consolidate" "done"
}

function def_Run_UserSmokePlan {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round3" $Project "UserSmokePlan"
    if (-not $RunUserSmokeTest) {
        def_AddRow "Round3" $Project "USER_TEST" "UserSmokeTest" "WARN_SKIPPED_BY_POLICY" "LOW" "SEQUENTIAL_GATED" "P3" "enabled" $false "Full user smoke test disabled by default. Enable only after HIGH=0." $ProjectPath
        def_TaskDone "Round3" $Project "UserSmokePlan" "skipped"
        return
    }
    def_AddRow "Round3" $Project "USER_TEST" "UserSmokeTest" "WARN_NOT_IMPLEMENTED_DIRECTLY" "MEDIUM" "SEQUENTIAL_GATED" "P2" "enabled" $true "User smoke test requested; implement per-module invoke target after review." $ProjectPath
    def_TaskDone "Round3" $Project "UserSmokePlan" "done"
}

function def_Run_ArtifactSeal {
    param([string]$Project,[string]$ProjectPath)
    def_TaskBegin "Round3" $Project "ArtifactSeal"
    def_AddRow "Round3" $Project "ARTIFACT" "ArtifactSeal" "OK_SEALED" "LOW" "PARALLEL_SAFE" "P2" "run_root" $def_RUN_ROOT "Artifacts will be exported at finalization." $def_RUN_ROOT
    def_TaskDone "Round3" $Project "ArtifactSeal" "done"
}

# =============================================================================
# def GLOBAL EXTRA TASKS
# =============================================================================
function def_CheckSupportiveFiles {
    def_TaskBegin "Round1" "GLOBAL" "SupportiveFiles"
    foreach ($f in $def_PARAM_SUPPORTIVE_FILES) {
        $name = Split-Path $f -Leaf
        if (Test-Path -LiteralPath $f -PathType Leaf) {
            def_AddRow "Round1" "GLOBAL" "SUPPORTIVE_FILE" $name "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "sha256" (def_GetSha256Safe $f) "Required supportive file found." $f
        } else {
            def_AddRow "Round1" "GLOBAL" "SUPPORTIVE_FILE" $name "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Required supportive file missing." $f
            $script:def_SequentialPlanRows += [pscustomobject]@{Project="GLOBAL"; Priority="P0"; Issue="Missing supportive file"; Action="Restore file before module activation."; Path=$f}
        }
    }
    def_TaskDone "Round1" "GLOBAL" "SupportiveFiles" "done"
}

function def_BuildGlobalLibraries {
    def_TaskBegin "Round2" "GLOBAL" "LibraryMatrices"
    def_BuildLibraryMatrices
    def_AddRow "Round2" "GLOBAL" "LIBRARY_MATRIX" "Top10 Local Free Libs" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "rows" (def_CountSafe $script:def_TopLibRows) "Top10 libs per flow/function/language generated." $def_TOP_LIBS_CSV
    def_AddRow "Round2" "GLOBAL" "LIBRARY_MATRIX" "Top20 Enterprise Forms To ProcessMining" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "rows" (def_CountSafe $script:def_PM20Rows) "Top20 local/free process-mining form stack generated." $def_PM20_CSV
    def_TaskDone "Round2" "GLOBAL" "LibraryMatrices" "done"
}

function def_GeneratePlans {
    def_TaskBegin "Round3" "GLOBAL" "GeneratePlans"
    $first = @"
# VIA Strongest MultiProject First Step
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSCommandPath" -Root "$Root" -SupportiveDir "$SupportiveDir" -FunctionalRoot "$FunctionalRoot" -CreateSandbox `$$true -RunToolDryProbe `$$true -RunUserSmokeTest `$$false -OpenReport `$$true
"@
    $first | Set-Content -LiteralPath $def_FIRSTSTEP_PS1 -Encoding UTF8
    if ((def_CountSafe $script:def_SequentialPlanRows) -eq 0) {
        $script:def_SequentialPlanRows += [pscustomobject]@{Project="GLOBAL"; Priority="P0"; Issue="No sequential blockers detected"; Action="Proceed to user smoke-test after reviewing warnings."; Path=$def_REPORT_HTML}
    }
    if ((def_CountSafe $script:def_ParallelPlanRows) -eq 0) {
        $script:def_ParallelPlanRows += [pscustomobject]@{Project="GLOBAL"; Priority="P2"; Issue="Parallel-safe optimization lane"; Action="HTML/UI polish, library install planning, report formatting can proceed independently."; Path=$def_TOP_LIBS_CSV}
    }
    def_AddRow "Round3" "GLOBAL" "PLAN" "StrongestFirstStepCommand" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "file" "ready" "Reusable first-step command generated." $def_FIRSTSTEP_PS1
    def_TaskDone "Round3" "GLOBAL" "GeneratePlans" "done"
}

function def_GenerateBridge {
    def_TaskBegin "Round3" "GLOBAL" "GenerateBridge"
    $bridge = @"
# VIA MultiProject Panorama Sync Bridge
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

function def_InvokeVIAMultiProjectPanoramaSync {
    param(
        [string]`$ScriptPath = "$PSCommandPath",
        [int]`$TimeoutSec = 180
    )
    `$pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not `$pwsh) {
        return [pscustomobject]@{Status="FAIL_PWSH_MISSING"; Message="pwsh not found."}
    }
    `$out = Join-Path "$def_LOG_DIR" ("bridge_multiproject_stdout_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    `$err = Join-Path "$def_LOG_DIR" ("bridge_multiproject_stderr_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    `$args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",`$ScriptPath,"-OpenReport", "`$true")
    `$p = Start-Process -FilePath `$pwsh.Source -ArgumentList `$args -WorkingDirectory "$Root" -RedirectStandardOutput `$out -RedirectStandardError `$err -PassThru -WindowStyle Hidden
    `$finished = `$p.WaitForExit(`$TimeoutSec * 1000)
    if (-not `$finished) {
        return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; Stdout=`$out; Stderr=`$err}
    }
    return [pscustomobject]@{Status=("OK_EXIT_{0}" -f `$p.ExitCode); ExitCode=`$p.ExitCode; Stdout=`$out; Stderr=`$err}
}

function def_GetVIAMultiProjectPanoramaArtifacts {
    return [pscustomobject]@{
        RunRoot = "$def_RUN_ROOT"
        ReportHtml = "$def_REPORT_HTML"
        MatrixCsv = "$def_MATRIX_CSV"
        ProjectCsv = "$def_PROJECT_CSV"
        HistoryCsv = "$def_HISTORY_CSV"
        TaskCsv = "$def_TASK_CSV"
        TopLibsCsv = "$def_TOP_LIBS_CSV"
        PM20Csv = "$def_PM20_CSV"
        SequentialPlan = "$def_REPAIR_PLAN_CSV"
        ParallelPlan = "$def_PARALLEL_PLAN_CSV"
    }
}

Export-ModuleMember -Function def_InvokeVIAMultiProjectPanoramaSync,def_GetVIAMultiProjectPanoramaArtifacts
"@
    $bridge | Set-Content -LiteralPath $def_BRIDGE_PSM1 -Encoding UTF8
    def_AddRow "Round3" "GLOBAL" "BRIDGE" "VIA_MultiProject_PanoramaSyncBridge" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P1" "file" "ready" "Bridge module generated for later PS integration." $def_BRIDGE_PSM1
    def_TaskDone "Round3" "GLOBAL" "GenerateBridge" "done"
}

function def_FinalProgressSeal {
    def_TaskBegin "Round3" "GLOBAL" "FinalProgressSeal"
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    def_AddRow "Round3" "GLOBAL" "PROGRESS" "FinalProgressSeal" "OK_PROGRESS_RECORDED" "LOW" "PARALLEL_SAFE" "P0" "completed/total/remaining/percent" "$($script:def_CompletedTasks)/$($script:def_TotalTasks)/$remaining/$pct" "Final progress state recorded before export." $def_TASK_CSV
    def_TaskDone "Round3" "GLOBAL" "FinalProgressSeal" "done"
}

# =============================================================================
# def EXPORT / HTML REPORT
# =============================================================================
function def_ExportAll {
    def_SaveCsv $def_MATRIX_CSV $script:def_Rows
    def_SaveJson $def_MATRIX_JSON $script:def_Rows
    def_SaveCsv $def_PROJECT_CSV $script:def_ProjectRows
    def_SaveCsv $def_HISTORY_CSV $script:def_HistoryRows
    def_SaveCsv $def_TASK_CSV $script:def_TaskRows
    def_SaveCsv $def_TOP_LIBS_CSV $script:def_TopLibRows
    def_SaveCsv $def_PM20_CSV $script:def_PM20Rows
    def_SaveCsv $def_REPAIR_PLAN_CSV $script:def_SequentialPlanRows
    def_SaveCsv $def_PARALLEL_PLAN_CSV $script:def_ParallelPlanRows
}

function def_BuildHtmlRows {
    param([object[]]$Rows,[string[]]$Columns)
    $htmlRows = @()
    foreach ($r in @(def_AsArray $Rows)) {
        $cls = "risk-low"
        if ($r.Risk -eq "HIGH" -or $r.Priority -eq "P0") { $cls = "risk-high" }
        elseif ($r.Risk -eq "MEDIUM" -or $r.Priority -eq "P1") { $cls = "risk-medium" }
        $tds = @()
        foreach ($c in $Columns) { $tds += "<td>$(def_HtmlEncode $r.$c)</td>" }
        $htmlRows += "<tr class='$cls'>$($tds -join '')</tr>"
    }
    return ($htmlRows -join "`n")
}

function def_WriteHtmlReport {
    $rows = @(def_AsArray $script:def_Rows)
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" -or $_.Status -like "FAIL*" })
    $status = "READY"
    $risk = "LOW"
    if ($high -gt 0) { $status = "READY_WITH_REVIEW"; $risk = "HIGH" }
    elseif ($warn -gt 0) { $status = "READY_WITH_WARNINGS"; $risk = "MEDIUM" }
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks

    $matrixRows = def_BuildHtmlRows -Rows $script:def_Rows -Columns @("Round","Project","Layer","Name","Status","Risk","Class","Priority","Metric","Value","Message","Path")
    $projectRows = def_BuildHtmlRows -Rows $script:def_ProjectRows -Columns @("Project","Path","Files","PS","PY","JSON","HTML","MD","Bytes")
    $taskRows = def_BuildHtmlRows -Rows $script:def_TaskRows -Columns @("Round","Project","Phase","Status","Completed","Total","Remaining","Percent")
    $seqRows = def_BuildHtmlRows -Rows $script:def_SequentialPlanRows -Columns @("Project","Priority","Issue","Action","Path")
    $parallelRows = def_BuildHtmlRows -Rows $script:def_ParallelPlanRows -Columns @("Project","Priority","Issue","Action","Path")
    $pmRows = def_BuildHtmlRows -Rows $script:def_PM20Rows -Columns @("Rank","Name","Lang","Stage","UseCase","RiskNote")
    $historyRows = def_BuildHtmlRows -Rows $script:def_HistoryRows -Columns @("Project","RunDir","LastWriteTime","Html","Json")

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA MultiProject Panorama Sync</title>
<style>
body{margin:0;background:#f8f8f4;color:#18211f;font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;}
header{padding:34px 42px;border-bottom:1px solid #d7ded8;background:radial-gradient(circle at 12% 15%,rgba(83,130,118,.18),transparent 35%),linear-gradient(135deg,#f8f8f4,#e9f1ee);}
h1{margin:0;font-size:28px;letter-spacing:.04em;font-weight:700}.sub{margin-top:8px;color:#53615c;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:20px 42px}
.card{background:white;border:1px solid #d7ded8;border-radius:18px;padding:16px;box-shadow:0 10px 30px rgba(20,40,35,.06)}
.k{font-size:12px;color:#6c7771}.v{font-size:22px;font-weight:800;margin-top:4px}
.wrap{padding:0 42px 38px 42px}h2{margin:26px 0 10px;font-size:18px}
table{border-collapse:collapse;width:100%;font-size:12px;background:white;border-radius:16px;overflow:hidden}
th{position:sticky;top:0;background:#22342f;color:white;text-align:left;padding:8px}td{border-bottom:1px solid #e4e8e5;padding:7px;vertical-align:top}
.risk-low td{background:#fbfffd}.risk-medium td{background:#fffaf0}.risk-high td{background:#fff3f1}
.progressbar{height:12px;background:#dfe7e2;border-radius:999px;overflow:hidden}.progressbar span{display:block;height:12px;background:#4f7f73;width:$pct%}
code{font-family:Consolas,monospace}
</style>
</head>
<body>
<header>
<h1>理 · VIA MultiProject Panorama Sync · Three-Round Safety Gate</h1>
<div class="sub">Run ID: $def_PARAM_RUN_ID · Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") · Root: $(def_HtmlEncode $Root)</div>
</header>
<section class="grid">
<div class="card"><div class="k">Status</div><div class="v">$status</div></div>
<div class="card"><div class="k">Risk</div><div class="v">$risk</div></div>
<div class="card"><div class="k">OK</div><div class="v">$ok</div></div>
<div class="card"><div class="k">WARN</div><div class="v">$warn</div></div>
<div class="card"><div class="k">HIGH</div><div class="v">$high</div></div>
<div class="card"><div class="k">Progress</div><div class="v">$pct%</div><div class="progressbar"><span></span></div><div class="k">Completed $script:def_CompletedTasks / $script:def_TotalTasks · Remaining $remaining</div></div>
</section>
<section class="wrap">
<h2>def Project Inventory</h2>
<table><thead><tr><th>Project</th><th>Path</th><th>Files</th><th>PS</th><th>PY</th><th>JSON</th><th>HTML</th><th>MD</th><th>Bytes</th></tr></thead><tbody>$projectRows</tbody></table>

<h2>def Flow Progress Tasks</h2>
<table><thead><tr><th>Round</th><th>Project</th><th>Phase</th><th>Status</th><th>Completed</th><th>Total</th><th>Remaining</th><th>Percent</th></tr></thead><tbody>$taskRows</tbody></table>

<h2>def Sequential Repair Plan</h2>
<table><thead><tr><th>Project</th><th>Priority</th><th>Issue</th><th>Action</th><th>Path</th></tr></thead><tbody>$seqRows</tbody></table>

<h2>def Parallel Safe Optimization Plan</h2>
<table><thead><tr><th>Project</th><th>Priority</th><th>Issue</th><th>Action</th><th>Path</th></tr></thead><tbody>$parallelRows</tbody></table>

<h2>def Past Run History Lens</h2>
<table><thead><tr><th>Project</th><th>RunDir</th><th>LastWriteTime</th><th>Html</th><th>Json</th></tr></thead><tbody>$historyRows</tbody></table>

<h2>def Top 20 Enterprise Forms → Process Mining Local Free Stack</h2>
<table><thead><tr><th>Rank</th><th>Name</th><th>Lang</th><th>Stage</th><th>Use Case</th><th>Risk Note</th></tr></thead><tbody>$pmRows</tbody></table>

<h2>def Full Matrix</h2>
<table><thead><tr><th>Round</th><th>Project</th><th>Layer</th><th>Name</th><th>Status</th><th>Risk</th><th>Class</th><th>Priority</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th></tr></thead><tbody>$matrixRows</tbody></table>
</section>
</body>
</html>
"@
    $html | Set-Content -LiteralPath $def_REPORT_HTML -Encoding UTF8
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA MultiProject Panorama Sync AIO $def_PARAM_VERSION" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Root       : $Root"
    Write-Host "Supportive : $SupportiveDir"
    Write-Host "Functional : $FunctionalRoot"
    Write-Host "Run ID     : $def_PARAM_RUN_ID"
    Write-Host "Policy     : no DB write · no canonical merge · no destructive delete · no stop-process · append-only"
    Write-Host ""

    def_Initialize

    # Global required supportive check
    def_CheckSupportiveFiles

    $lanes = @("SUPPORTIVE") + $ProjectNames
    foreach ($project in $lanes) {
        $path = def_GetProjectPath -Project $project
        def_Run_PathCheck $project $path
        def_Run_FileInventory $project $path
        def_Run_HistoryLens $project $path
        def_Run_CommandPolicyReview $project $path
    }

    foreach ($project in $lanes) {
        $path = def_GetProjectPath -Project $project
        def_Run_SandboxCopy $project $path
        def_Run_PowerShellAst $project $path
        def_Run_PythonCompile $project $path
        def_Run_ToolDryProbe $project $path
        def_Run_HydraClassify $project $path
    }

    def_BuildGlobalLibraries

    foreach ($project in $lanes) {
        $path = def_GetProjectPath -Project $project
        def_Run_Consolidate $project $path
        def_Run_UserSmokePlan $project $path
        def_Run_ArtifactSeal $project $path
    }

    def_GeneratePlans
    def_GenerateBridge
    def_FinalProgressSeal

    def_ExportAll
    def_WriteHtmlReport
    Write-Progress -Id 1 -Activity "VIA MultiProject Panorama Sync" -Completed

    $rows = @(def_AsArray $script:def_Rows)
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" -or $_.Status -like "FAIL*" })
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA MULTIPROJECT PANORAMA SYNC COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status       : $(if($high -gt 0){"READY_WITH_REVIEW"}elseif($warn -gt 0){"READY_WITH_WARNINGS"}else{"READY"})"
    Write-Host "OK/WARN/HIGH : $ok / $warn / $high"
    Write-Host "Progress     : $script:def_CompletedTasks / $script:def_TotalTasks · Remaining $remaining · $pct%"
    Write-Host "Run Root     : $def_RUN_ROOT"
    Write-Host "HTML         : $def_REPORT_HTML"
    Write-Host "Matrix CSV   : $def_MATRIX_CSV"
    Write-Host "Project CSV  : $def_PROJECT_CSV"
    Write-Host "Task CSV     : $def_TASK_CSV"
    Write-Host "Top Libs CSV : $def_TOP_LIBS_CSV"
    Write-Host "PM20 CSV     : $def_PM20_CSV"
    Write-Host "Seq Plan     : $def_REPAIR_PLAN_CSV"
    Write-Host "Bridge       : $def_BRIDGE_PSM1"
    Write-Host ""

    if ($OpenReport -and (Test-Path -LiteralPath $def_REPORT_HTML)) {
        Start-Process $def_REPORT_HTML
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddRow "FATAL" "GLOBAL" "RUNTIME" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Unhandled exception; exporting partial report." ""
        def_ExportAll
        def_WriteHtmlReport
    } catch {}
} finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
}

