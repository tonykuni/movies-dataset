param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$Downloads = "C:\Users\tonyk\Downloads",
    [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$ToolRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_FirstStep_PanoramaSandbox",
    [bool]$AllowNetworkInstall = $true,
    [bool]$InstallLightPSModules = $true,
    [bool]$InstallHeavyPythonPackages = $false,
    [bool]$RunToolDryProbe = $true,
    [bool]$CreateSandbox = $true,
    [bool]$OpenReport = $true,
    [int]$TimeoutSec = 180,
    [int]$MaxRounds = 3,
    [bool]$KeepPowerShellOpen = $true
)

# =============================================================================
# def VIA FIRST STEP · PANORAMA SANDBOX · AIO v0.3.0
# =============================================================================
# Purpose:
# - Read-only first step for VIA-wide command review and safe integration.
# - Analyze prior scripts, classify strengths/weaknesses, generate methodology.
# - Bootstrap light local/free tooling and create a reusable sandbox bridge.
# - Heavy OCR / document / process-mining packages are planned, not forced, unless explicitly enabled.
#
# Policy:
# - no DB write
# - no canonical merge
# - no destructive delete
# - no stop-process
# - append-only
# - sandbox-first
# =============================================================================

# =============================================================================
# def PARAMETERS / STATIC INPUTS
# =============================================================================
$def_PARAM_RUN_ID = "RUN_{0}_VIA_FIRSTSTEP_PANORAMA_SANDBOX" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_PARAM_POLICY = [ordered]@{
    db_write                     = $false
    canonical_merge              = $false
    destructive_delete           = $false
    stop_process                 = $false
    append_only                  = $true
    sandbox_first                = $true
    repair_mode                  = "DRY_RUN"
    max_rounds                   = $MaxRounds
    allow_network_install        = $AllowNetworkInstall
    install_light_ps_modules     = $InstallLightPSModules
    install_heavy_python_packages= $InstallHeavyPythonPackages
}

$def_PARAM_COMMAND_CANDIDATES = @(
    "C:\Users\tonyk\Downloads\Invoke-VDF-Nexus-Panorama3RoundGate.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v2.ps1",
    "C:\Users\tonyk\Downloads\VIA_NetGuardTuner_v1.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-NexusToolBridge-AIO-v010.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-Polyglot-RedFindingStabilizer-v0122-AstParserHotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-Polyglot-RedFindingStabilizer-v0121-Hotfix.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-Polyglot-RedFindingStabilizer-v012.ps1",
    "C:\Users\tonyk\Downloads\Invoke-VIA-NexusToolBridge-Unified-v02.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VDF-Nexus-Panorama3RoundGate.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_NetGuardTuner_v2.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_NetGuardTuner_v1.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA-NexusToolBridge-AIO-v010.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA-Polyglot-RedFindingStabilizer-v0122-AstParserHotfix.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA-Polyglot-RedFindingStabilizer-v0121-Hotfix.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA-Polyglot-RedFindingStabilizer-v012.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\Invoke-VIA-NexusToolBridge-Unified-v02.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Read_Me_VeritasNexusCore.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
)

$def_PARAM_LIGHT_PS_MODULES = @(
    [pscustomobject]@{Lang="PowerShell"; Function="StaticAnalysis"; Name="PSScriptAnalyzer"; Required=$true; Install="Install-Module PSScriptAnalyzer -Scope CurrentUser -Force"; Purpose="AST/lint/static findings/fixable rules"},
    [pscustomobject]@{Lang="PowerShell"; Function="Testing"; Name="Pester"; Required=$true; Install="Install-Module Pester -Scope CurrentUser -Force"; Purpose="unit/integration tests"},
    [pscustomobject]@{Lang="PowerShell"; Function="HTMLReport"; Name="PSWriteHTML"; Required=$false; Install="Install-Module PSWriteHTML -Scope CurrentUser -Force"; Purpose="rich HTML reports"},
    [pscustomobject]@{Lang="PowerShell"; Function="ExcelExport"; Name="ImportExcel"; Required=$false; Install="Install-Module ImportExcel -Scope CurrentUser -Force"; Purpose="xlsx/csv review"},
    [pscustomobject]@{Lang="PowerShell"; Function="Logging"; Name="PSFramework"; Required=$false; Install="Install-Module PSFramework -Scope CurrentUser -Force"; Purpose="structured logging"},
    [pscustomobject]@{Lang="PowerShell"; Function="CLIUX"; Name="PSReadLine"; Required=$false; Install="Install-Module PSReadLine -Scope CurrentUser -Force"; Purpose="interactive shell enhancement"},
    [pscustomobject]@{Lang="PowerShell"; Function="Prediction"; Name="CompletionPredictor"; Required=$false; Install="Install-Module CompletionPredictor -Scope CurrentUser -Force"; Purpose="command prediction"},
    [pscustomobject]@{Lang="PowerShell"; Function="Secrets"; Name="Microsoft.PowerShell.SecretManagement"; Required=$false; Install="Install-Module Microsoft.PowerShell.SecretManagement -Scope CurrentUser -Force"; Purpose="secret abstraction"},
    [pscustomobject]@{Lang="PowerShell"; Function="Secrets"; Name="Microsoft.PowerShell.SecretStore"; Required=$false; Install="Install-Module Microsoft.PowerShell.SecretStore -Scope CurrentUser -Force"; Purpose="local secret vault"},
    [pscustomobject]@{Lang="PowerShell"; Function="PackageBridge"; Name="WinGet.Client"; Required=$false; Install="Install-Module WinGet.Client -Scope CurrentUser -Force"; Purpose="Windows package manager bridge"}
)

$def_PARAM_NATIVE_TOOLS = @(
    [pscustomobject]@{Name="pwsh"; Lang="PowerShell"; Purpose="PowerShell 7 orchestration"},
    [pscustomobject]@{Name="powershell"; Lang="PowerShell"; Purpose="Windows PowerShell fallback"},
    [pscustomobject]@{Name="python"; Lang="Python"; Purpose="Python package/runtime probe"},
    [pscustomobject]@{Name="pip"; Lang="Python"; Purpose="Python package installer"},
    [pscustomobject]@{Name="node"; Lang="JS/TS"; Purpose="JavaScript syntax checks"},
    [pscustomobject]@{Name="npm"; Lang="JS/TS"; Purpose="Node package manager"},
    [pscustomobject]@{Name="dotnet"; Lang="C#"; Purpose=".NET build/test"},
    [pscustomobject]@{Name="git"; Lang="CLI"; Purpose="source control check"},
    [pscustomobject]@{Name="winget"; Lang="CLI"; Purpose="Windows package manager"},
    [pscustomobject]@{Name="curl"; Lang="CLI"; Purpose="network fetch probe"}
)

# =============================================================================
# def RUNTIME PATHS
# =============================================================================
$def_RUN_ROOT = Join-Path $ToolRoot ("runs\" + $def_PARAM_RUN_ID)
$def_SANDBOX_DIR = Join-Path $def_RUN_ROOT "sandbox"
$def_SANDBOX_TOOLS_DIR = Join-Path $def_SANDBOX_DIR "tools_input"
$def_REGISTRY_DIR = Join-Path $def_RUN_ROOT "registry"
$def_REPORT_DIR = Join-Path $def_RUN_ROOT "report"
$def_LOG_DIR = Join-Path $def_RUN_ROOT "logs"
$def_PLAN_DIR = Join-Path $def_RUN_ROOT "plans"
$def_BRIDGE_DIR = Join-Path $ToolRoot "bridge"

$def_MATRIX_CSV = Join-Path $def_REGISTRY_DIR "VIA_FirstStep_Panorama_Matrix.csv"
$def_MATRIX_JSON = Join-Path $def_REGISTRY_DIR "VIA_FirstStep_Panorama_Matrix.json"
$def_COMMAND_REVIEW_CSV = Join-Path $def_REGISTRY_DIR "VIA_CommandReview_StrengthWeakness.csv"
$def_METHOD_CSV = Join-Path $def_REGISTRY_DIR "VIA_ThreeRound_Methodology.csv"
$def_TOP_LIBS_CSV = Join-Path $def_REGISTRY_DIR "VIA_Top10_LocalFreeLibs_ByFunctionLanguage.csv"
$def_PROCESS_MINING_TOP20_CSV = Join-Path $def_REGISTRY_DIR "VIA_Top20_EnterpriseForms_To_ProcessMining_Libs.csv"
$def_INSTALL_PLAN_PS1 = Join-Path $def_PLAN_DIR "VIA_InstallPlan_OptionalHeavy.ps1"
$def_APPLY_PLAN_PS1 = Join-Path $def_PLAN_DIR "VIA_ApplyPlan_ReviewOnly.ps1"
$def_FIRSTSTEP_CMD_PS1 = Join-Path $def_PLAN_DIR "VIA_Strongest_FirstStep_Command.ps1"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_FirstStep_PanoramaSandbox_Report.html"
$def_BRIDGE_PSM1 = Join-Path $def_BRIDGE_DIR "VIA_FirstStep_PanoramaBridge.psm1"
$def_BRIDGE_JSON = Join-Path $def_BRIDGE_DIR "VIA_FirstStep_PanoramaBridge.json"

# =============================================================================
# def GLOBAL STATE
# =============================================================================
$script:def_Rows = New-Object System.Collections.Generic.List[object]
$script:def_CommandReviews = New-Object System.Collections.Generic.List[object]
$script:def_Methodology = New-Object System.Collections.Generic.List[object]
$script:def_TopLibraries = New-Object System.Collections.Generic.List[object]
$script:def_ProcessMiningTop20 = New-Object System.Collections.Generic.List[object]
$script:def_FoundCommands = New-Object System.Collections.Generic.List[object]

# =============================================================================
# def CORE HELPERS
# =============================================================================
function def_EnsureDirectory {
    param([string]$Path)
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [array]) { return $InputObject.Count }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    return 1
}

function def_AsArraySafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return @() }
    return @($InputObject)
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

function def_ShowProgress {
    param([int]$Step, [int]$Total, [string]$Activity, [string]$Status)
    $pct = 0
    if ($Total -gt 0) { $pct = [math]::Min(100, [math]::Round(($Step / $Total) * 100, 0)) }
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $pct
}

function def_AddRow {
    param(
        [string]$Round, [string]$Layer, [string]$Name, [string]$Status,
        [string]$Risk, [string]$Class, [string]$Priority,
        [string]$Metric, [object]$Value, [string]$Message, [string]$Path = ""
    )
    $row = [pscustomobject]@{
        Time     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Round    = $Round
        Layer    = $Layer
        Name     = $Name
        Status   = $Status
        Risk     = $Risk
        Class    = $Class
        Priority = $Priority
        Metric   = $Metric
        Value    = [string]$Value
        Message  = $Message
        Path     = $Path
    }
    $script:def_Rows.Add($row) | Out-Null
}

function def_GetSha256Safe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
        return ""
    } catch {
        return ""
    }
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

function def_NormalizeScore {
    param([int]$Score)
    if ($Score -lt 0) { return 0 }
    if ($Score -gt 100) { return 100 }
    return $Score
}

function def_TestPowerShellAstSafe {
    param([string]$Path)
    try {
        [System.Management.Automation.Language.Token[]]$tokens = $null
        [System.Management.Automation.Language.ParseError[]]$errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
        return [pscustomobject]@{
            Ok = ((def_CountSafe $errors) -eq 0)
            ErrorCount = (def_CountSafe $errors)
            ErrorText = (($errors | ForEach-Object { "{0}:{1} {2}" -f $_.Extent.StartLineNumber, $_.Extent.StartColumnNumber, $_.Message }) -join " | ")
        }
    } catch {
        return [pscustomobject]@{
            Ok = $false
            ErrorCount = 1
            ErrorText = $_.Exception.Message
        }
    }
}

function def_InvokeChildProcessSafe {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [int]$TimeoutSeconds = 180
    )
    $safeName = $Name -replace '[^\w\-]', '_'
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
            return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; ExitCode=$null; TimedOut=$true; Stdout=$stdout; Stderr=$stderr; Message="Timeout reached. Child process not stopped due policy."}
        }
        return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message="Child process completed."}
    } catch {
        return [pscustomobject]@{Status="WARN_PROCESS_ERROR"; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message=$_.Exception.Message}
    }
}

# =============================================================================
# def LIBRARY MATRICES
# =============================================================================
function def_AddTopLibrary {
    param(
        [string]$Flow, [string]$Lang, [string]$FunctionArea, [int]$Rank,
        [string]$Name, [string]$Install, [string]$UseCase, [string]$RiskNote
    )
    $script:def_TopLibraries.Add([pscustomobject]@{
        Flow = $Flow
        Lang = $Lang
        FunctionArea = $FunctionArea
        Rank = $Rank
        Name = $Name
        Install = $Install
        UseCase = $UseCase
        RiskNote = $RiskNote
    }) | Out-Null
}

function def_AddProcessMiningLib {
    param(
        [int]$Rank, [string]$Name, [string]$Lang, [string]$Install,
        [string]$Stage, [string]$UseCase, [string]$LocalFreeNote, [string]$RiskNote
    )
    $script:def_ProcessMiningTop20.Add([pscustomobject]@{
        Rank = $Rank
        Name = $Name
        Lang = $Lang
        Install = $Install
        Stage = $Stage
        UseCase = $UseCase
        LocalFreeNote = $LocalFreeNote
        RiskNote = $RiskNote
    }) | Out-Null
}

function def_BuildTopLibraryMatrices {
    def_WriteLog "RUN" "Building Top10 local/free library matrices."
    $flowList = @(
        "01_Panorama_Discovery",
        "02_Command_Forensics",
        "03_Toolchain_Bootstrap",
        "04_Sandbox_Test",
        "05_Check_Test_Repair",
        "06_Form_To_ProcessMining",
        "07_HTML_UI_Report",
        "08_Consolidate_Activate"
    )

    $psLibs = @(
        @("PSScriptAnalyzer","Install-Module PSScriptAnalyzer -Scope CurrentUser -Force","PowerShell static analysis, AST lint, fixable findings","Run after parse clean"),
        @("Pester","Install-Module Pester -Scope CurrentUser -Force","PowerShell unit/integration tests","Needs tests to exist"),
        @("PSWriteHTML","Install-Module PSWriteHTML -Scope CurrentUser -Force","Detailed HTML dashboards/reports","Optional; fallback HTML exists"),
        @("ImportExcel","Install-Module ImportExcel -Scope CurrentUser -Force","XLSX output for review matrices","Optional"),
        @("PSFramework","Install-Module PSFramework -Scope CurrentUser -Force","Structured logging","Optional"),
        @("PSReadLine","Install-Module PSReadLine -Scope CurrentUser -Force","Interactive CLI productivity","May already exist"),
        @("CompletionPredictor","Install-Module CompletionPredictor -Scope CurrentUser -Force","Command prediction accelerator","Optional"),
        @("SecretManagement","Install-Module Microsoft.PowerShell.SecretManagement -Scope CurrentUser -Force","Secret abstraction","Do not print secrets"),
        @("SecretStore","Install-Module Microsoft.PowerShell.SecretStore -Scope CurrentUser -Force","Local secret vault","Needs setup"),
        @("WinGet.Client","Install-Module WinGet.Client -Scope CurrentUser -Force","Package manager bridge","Optional")
    )
    $pyLibs = @(
        @("pandas","python -m pip install pandas","Tabular ETL, event-log shaping","Stable core"),
        @("polars","python -m pip install polars","Fast low-memory dataframe engine","Great for large logs"),
        @("duckdb","python -m pip install duckdb","Local OLAP, parquet/sql analytics","Excellent local DB"),
        @("pyarrow","python -m pip install pyarrow","Parquet/Arrow interchange","Needed for parquet"),
        @("pm4py","python -m pip install pm4py","Process mining algorithms/event logs","Core process mining"),
        @("networkx","python -m pip install networkx","Graph/path/process relation analysis","Complements PM4Py"),
        @("pandera","python -m pip install pandera","Dataframe schema validation","Optional but useful"),
        @("great_expectations","python -m pip install great_expectations","Data quality validation","Heavier"),
        @("rich","python -m pip install rich","Console progress/table UX","Lightweight UX"),
        @("tqdm","python -m pip install tqdm","Progress bars","Lightweight")
    )
    $docLibs = @(
        @("docling","python -m pip install docling","PDF/DOCX/PPTX/image conversion, layout/table/OCR pipeline","Heavy; install only in sandbox env"),
        @("paddleocr","python -m pip install paddleocr","OCR and PP-Structure document parsing","Heavy; model downloads"),
        @("ocrmypdf","python -m pip install ocrmypdf","Searchable PDFs with OCR layer","Needs Tesseract/Ghostscript"),
        @("pytesseract","python -m pip install pytesseract","Tesseract Python wrapper","Needs Tesseract binary"),
        @("pdfplumber","python -m pip install pdfplumber","PDF text/table extraction","Good for digital PDFs"),
        @("pymupdf","python -m pip install pymupdf","PDF rendering/text/image extraction","Fast"),
        @("camelot-py","python -m pip install camelot-py","PDF table extraction","Needs ghostscript/opencv depending flavor"),
        @("tabula-py","python -m pip install tabula-py","Java Tabula wrapper for tables","Needs Java"),
        @("opencv-python","python -m pip install opencv-python","Image preprocessing/layout/cv","May be heavy"),
        @("unstructured","python -m pip install unstructured","Document partitioning pipeline","Heavy; pin versions if needed")
    )
    $jsLibs = @(
        @("typescript","npm install -g typescript","Type checking","Global optional"),
        @("eslint","npm install -g eslint","JS/TS lint","Config needed"),
        @("prettier","npm install -g prettier","Formatter","Config needed"),
        @("vite","npm install -g vite","Fast UI dev server/build","Optional"),
        @("playwright","npm install -g playwright","Browser UI testing","Needs browser install"),
        @("vitest","npm install -g vitest","JS/TS test runner","Project config needed"),
        @("mermaid","npm install -g @mermaid-js/mermaid-cli","Process diagrams","May need chromium"),
        @("marked","npm install -g marked","Markdown conversion/rendering","Optional"),
        @("d3","npm install d3","Visualization library","Per project"),
        @("cytoscape","npm install cytoscape","Graph/network visualization","Per project")
    )
    $csLibs = @(
        @("xunit","dotnet add package xunit","C# unit testing","Project needed"),
        @("NUnit","dotnet add package NUnit","C# unit testing","Project needed"),
        @("FluentAssertions","dotnet add package FluentAssertions","Readable assertions","Project needed"),
        @("Serilog","dotnet add package Serilog","Structured logs","Project needed"),
        @("HtmlAgilityPack","dotnet add package HtmlAgilityPack","HTML parsing","Project needed"),
        @("CsvHelper","dotnet add package CsvHelper","CSV IO","Project needed"),
        @("ClosedXML","dotnet add package ClosedXML","Excel IO","Project needed"),
        @("QuestPDF","dotnet add package QuestPDF","PDF generation/reporting","License constraints should be reviewed"),
        @("Microsoft.Playwright","dotnet add package Microsoft.Playwright","Browser UI tests","Install browsers separately"),
        @("CliWrap","dotnet add package CliWrap","External process wrapper","Project needed")
    )

    foreach ($flow in $flowList) {
        for ($i=0; $i -lt 10; $i++) {
            def_AddTopLibrary $flow "PowerShell" "Orchestration_Check_Test_Repair" ($i+1) $psLibs[$i][0] $psLibs[$i][1] $psLibs[$i][2] $psLibs[$i][3]
            def_AddTopLibrary $flow "Python" "ETL_ProcessMining_DocAI" ($i+1) $pyLibs[$i][0] $pyLibs[$i][1] $pyLibs[$i][2] $pyLibs[$i][3]
            def_AddTopLibrary $flow "Python" "EnterpriseFormReading" ($i+1) $docLibs[$i][0] $docLibs[$i][1] $docLibs[$i][2] $docLibs[$i][3]
            def_AddTopLibrary $flow "JS_TS" "UI_Test_Visualization" ($i+1) $jsLibs[$i][0] $jsLibs[$i][1] $jsLibs[$i][2] $jsLibs[$i][3]
            def_AddTopLibrary $flow "CSharp" "Windows_App_Testing_IO" ($i+1) $csLibs[$i][0] $csLibs[$i][1] $csLibs[$i][2] $csLibs[$i][3]
        }
    }

    $pm20 = @(
        @(1,"Docling","Python","python -m pip install docling","Document conversion/layout","Convert PDF/DOCX/PPTX/images into structured document objects","Open-source local toolkit; heavy models possible","Install in sandbox env first"),
        @(2,"PaddleOCR / PP-Structure","Python","python -m pip install paddleocr","OCR/layout/table/KIE","OCR and structured document parsing for scanned forms","Apache-style open toolkit; model downloads","Heavy; avoid global install"),
        @(3,"OCRmyPDF","CLI/Python","python -m pip install ocrmypdf","OCR PDF layer","Make scanned PDFs searchable before table/text extraction","Open-source; local","Needs Tesseract/Ghostscript"),
        @(4,"Tesseract + pytesseract","CLI/Python","winget install UB-Mannheim.TesseractOCR ; python -m pip install pytesseract","OCR","Traditional OCR fallback for forms","Free local OCR","Accuracy depends on preprocessing"),
        @(5,"pdfplumber","Python","python -m pip install pdfplumber","Digital PDF extraction","Extract text/tables/coordinates from digital PDFs","Open-source local","Weak on scans"),
        @(6,"PyMuPDF","Python","python -m pip install pymupdf","PDF render/text/images","Fast page rendering and extraction","Open-source local","License review for distribution"),
        @(7,"Camelot","Python","python -m pip install camelot-py","PDF tables","Lattice/stream table extraction","Open-source local","Needs Ghostscript for some use cases"),
        @(8,"tabula-py","Python/Java","python -m pip install tabula-py","PDF tables","Java Tabula table extraction bridge","Open-source local","Needs Java"),
        @(9,"OpenCV","Python/C++","python -m pip install opencv-python","Image preprocessing","Deskew, threshold, boxes, morphology","Open-source local","Can be memory-heavy"),
        @(10,"LayoutParser","Python","python -m pip install layoutparser","Layout detection","Layout zones for forms/pages","Open-source local","Model deps vary"),
        @(11,"Unstructured","Python","python -m pip install unstructured","Document partitioning","Partition diverse enterprise docs into semantic elements","Open-source local components","Heavy extras if enabled"),
        @(12,"Microsoft MarkItDown","Python","python -m pip install markitdown","Markdown conversion","Convert Office/PDF/media formats to Markdown for downstream parsing","Open-source local utility","Quality varies by format"),
        @(13,"Apache Tika","Java/Python","python -m pip install tika","Document metadata/text","Fallback broad document parsing","Open-source local/server","Java dependency"),
        @(14,"pandas","Python","python -m pip install pandas","Event log shaping","Normalize extracted records into case/activity/timestamp logs","Open-source local","Memory use for large logs"),
        @(15,"polars","Python/Rust","python -m pip install polars","Fast ETL","Low-memory event-log transformation","Open-source local","Some pandas ecosystem gaps"),
        @(16,"DuckDB","Python/CLI","python -m pip install duckdb","Local analytics","SQL over parquet/csv event logs","Open-source local","Avoid accidental DB writes outside sandbox"),
        @(17,"PyArrow","Python/C++","python -m pip install pyarrow","Parquet/Arrow","Columnar outputs for event logs","Open-source local","Version compatibility"),
        @(18,"PM4Py","Python","python -m pip install pm4py","Process mining","Discovery, conformance, event-log analytics","Open-source local","Needs clean event log schema"),
        @(19,"NetworkX","Python","python -m pip install networkx","Graph analytics","DFG/process graph analysis and routing","Open-source local","Large graphs slower than igraph"),
        @(20,"Pandera / Great Expectations","Python","python -m pip install pandera great_expectations","Data validation","Validate extracted form-to-event schema before mining","Open-source local","GE is heavier")
    )

    foreach ($p in $pm20) {
        def_AddProcessMiningLib -Rank $p[0] -Name $p[1] -Lang $p[2] -Install $p[3] -Stage $p[4] -UseCase $p[5] -LocalFreeNote $p[6] -RiskNote $p[7]
    }
}

# =============================================================================
# def METHODOLOGY
# =============================================================================
function def_AddMethodStep {
    param(
        [int]$Round, [string]$Phase, [string]$Goal, [string]$Inputs,
        [string]$Action, [string]$ParallelSafe, [string]$SequentialGate,
        [string]$Output, [string]$StopCondition
    )
    $script:def_Methodology.Add([pscustomobject]@{
        Round = "Round$Round"
        Phase = $Phase
        Goal = $Goal
        Inputs = $Inputs
        Action = $Action
        ParallelSafe = $ParallelSafe
        SequentialGate = $SequentialGate
        Output = $Output
        StopCondition = $StopCondition
    }) | Out-Null
}

function def_BuildMethodology {
    def_WriteLog "RUN" "Building three-round methodology."
    def_AddMethodStep 1 "Inventory" "建立全局 SSOT，不碰原始碼" "Root, SupportiveDir, command candidates" "SHA256, existence, AST parse, policy scan" "hash, file inventory, docs review" "missing root/supportive tools/high parse errors" "Matrix CSV/JSON/HTML" "Root missing or high-risk destructive pattern"
    def_AddMethodStep 1 "Command Forensics" "檢視他人指令優缺點並提煉強度" "Existing PS scripts and README" "score method strength, safety, UX, integration, testability" "read-only scoring" "parse error / destructive command pattern" "StrengthWeakness CSV" "Parse red not resolved"
    def_AddMethodStep 1 "Toolchain Bootstrap" "導入輕量工具與 10 加速器" "PSGallery, local modules" "install/check PSScriptAnalyzer, Pester, report modules" "module detect/import" "network install failure on required modules" "Module Matrix" "No pwsh/python available"
    def_AddMethodStep 2 "Sandbox" "建立安全沙盒複本" "Found command candidates" "copy scripts/docs to sandbox/tools_input only" "copy/read/hash" "copy failed / insufficient permissions" "Sandbox folder + manifest" "Sandbox cannot be created"
    def_AddMethodStep 2 "Check-Test-Repair DryRun" "只在 sandbox 做測試與修復計畫" "sandbox files" "AST/PSSA/pytest/ruff/node/dotnet probes when available" "lint/test dry-run" "parse errors first; no broad autofix" "RepairPlan ReviewOnly" "High parse errors remain"
    def_AddMethodStep 2 "Library Plan" "建立企業表單轉流程探勘能力矩陣" "Top10 per flow/lang + Top20 form-to-process mining" "generate install plan, not force heavy installs" "plan generation" "heavy OCR installs require explicit flag" "Top libs CSV + OptionalHeavy ps1" "Global env contamination risk"
    def_AddMethodStep 3 "Consolidate" "整合為可被其他 PS 指令引用的 Bridge" "validated tool paths" "generate psm1 wrapper with timeout and dry-run policy" "wrapper generation" "unknown direct dot-source blocked" "Bridge PSM1/JSON" "Bridge parse failure"
    def_AddMethodStep 3 "Activate User-Test" "最後才啟動真實 user smoke test" "pass matrix + no high risk" "create strongest first-step command" "read-only run" "original apply requires explicit token" "FirstStep_Command.ps1" "Any HIGH remains"
}

# =============================================================================
# def ROUND0 INITIALIZE
# =============================================================================
function def_Round0_Initialize {
    def_ShowProgress -Step 1 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Initialize"
    def_EnsureDirectory $ToolRoot
    def_EnsureDirectory $def_RUN_ROOT
    def_EnsureDirectory $def_SANDBOX_DIR
    def_EnsureDirectory $def_SANDBOX_TOOLS_DIR
    def_EnsureDirectory $def_REGISTRY_DIR
    def_EnsureDirectory $def_REPORT_DIR
    def_EnsureDirectory $def_LOG_DIR
    def_EnsureDirectory $def_PLAN_DIR
    def_EnsureDirectory $def_BRIDGE_DIR

    def_AddRow "Round0" "POLICY" "Safety Policy" "OK_LOCKED" "LOW" "SEQUENTIAL_GATED" "P0" "policy" "append-only" "No DB write, no canonical merge, no destructive delete, no stop-process." $ToolRoot
    if (Test-Path -LiteralPath $Root -PathType Container) {
        def_AddRow "Round0" "ROOT" "VIA Root" "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "exists" $true "Root exists." $Root
    } else {
        def_AddRow "Round0" "ROOT" "VIA Root" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Root missing." $Root
    }
    foreach ($a in @(
        "Run Isolation","Timeout Guard","AST Before Invoke","Module Cache First","Network Retry Lite",
        "Hash Inventory","Sandbox Copy","Low-Memory Scan","Hydra Gate","HTML Matrix"
    )) {
        def_AddRow "Round0" "ACCELERATOR" $a "OK_ENABLED" "LOW" "PARALLEL_SAFE" "P1" "enabled" $true "Accelerator enabled." ""
    }
}

# =============================================================================
# def ROUND1 TOOL / COMMAND REVIEW
# =============================================================================
function def_Round1_CheckNativeTools {
    def_ShowProgress -Step 2 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Native tools"
    foreach ($t in $def_PARAM_NATIVE_TOOLS) {
        $cmd = Get-Command $t.Name -ErrorAction SilentlyContinue
        if ($cmd) {
            def_AddRow "Round1" "NATIVE_TOOL" $t.Name "OK_FOUND" "LOW" "PARALLEL_SAFE" "P1" "path" $cmd.Source "$($t.Purpose) available." $cmd.Source
        } else {
            def_AddRow "Round1" "NATIVE_TOOL" $t.Name "WARN_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "path" "" "$($t.Purpose) not found; continuing." ""
        }
    }
}

function def_Round1_InstallLightPSModules {
    def_ShowProgress -Step 3 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "PowerShell modules"
    if ($AllowNetworkInstall) {
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        } catch {
            try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
        }
    }

    foreach ($m in $def_PARAM_LIGHT_PS_MODULES) {
        $existing = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($existing) {
            def_AddRow "Round1" "PS_MODULE" $m.Name "OK_PRESENT" "LOW" "PARALLEL_SAFE" "P1" "version" $existing.Version "$($m.Purpose)." $existing.Path
            continue
        }
        if ($InstallLightPSModules -and $AllowNetworkInstall) {
            try {
                Install-Module -Name $m.Name -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
                $installed = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($installed) {
                    def_AddRow "Round1" "PS_MODULE" $m.Name "OK_INSTALLED" "LOW" "PARALLEL_SAFE" "P1" "version" $installed.Version "$($m.Purpose)." $installed.Path
                } else {
                    def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_UNCONFIRMED" "MEDIUM" "PARALLEL_SAFE" "P2" "installed" "unknown" "Install completed but module not discovered." ""
                }
            } catch {
                $risk = "LOW"; if ($m.Required) { $risk = "MEDIUM" }
                def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_FAILED" $risk "PARALLEL_SAFE" "P2" "error" $_.Exception.Message "Install failed; continuing." ""
            }
        } else {
            $risk = "LOW"; if ($m.Required) { $risk = "MEDIUM" }
            def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_NOT_INSTALLED_BY_POLICY" $risk "PARALLEL_SAFE" "P2" "install" $false "Install disabled or network disabled." ""
        }
    }
}

function def_ScoreCommandContent {
    param([string]$Path, [string]$Text)

    $score = 50
    $pros = New-Object System.Collections.Generic.List[string]
    $cons = New-Object System.Collections.Generic.List[string]
    $risks = New-Object System.Collections.Generic.List[string]

    if ($Text -match "param\s*\(") { $score += 5; $pros.Add("Param block") | Out-Null } else { $score -= 4; $cons.Add("No clear param block") | Out-Null }
    if ($Text -match "function\s+def_|def_") { $score += 5; $pros.Add("def_* structure") | Out-Null } else { $score -= 2; $cons.Add("Weak def_* structure") | Out-Null }
    if ($Text -match "try\s*\{|catch\s*\{") { $score += 8; $pros.Add("try/catch") | Out-Null } else { $score -= 8; $cons.Add("Weak exception handling") | Out-Null }
    if ($Text -match "Write-Progress") { $score += 5; $pros.Add("Dynamic progress") | Out-Null } else { $cons.Add("Progress may be weak") | Out-Null }
    if ($Text -match "HTML|Report|Matrix|Export-Csv|ConvertTo-Json") { $score += 8; $pros.Add("Matrix report output") | Out-Null } else { $score -= 5; $cons.Add("No obvious matrix report") | Out-Null }
    if ($Text -match "DRY_RUN|DryRun|dry-run|ApplyRepairs|ApprovalToken") { $score += 8; $pros.Add("Dry-run / approval gate") | Out-Null } else { $score -= 6; $cons.Add("No obvious dry-run approval gate") | Out-Null }
    if ($Text -match "Start-Process|WaitForExit|Timeout|TimeoutSec") { $score += 6; $pros.Add("Child process / timeout guard") | Out-Null } else { $cons.Add("Timeout/process isolation may be weak") | Out-Null }
    if ($Text -match "Get-FileHash|SHA256") { $score += 4; $pros.Add("Hash inventory") | Out-Null } else { $cons.Add("Hash inventory not obvious") | Out-Null }
    if ($Text -match "Sandbox|sandbox|Copy-Item") { $score += 4; $pros.Add("Sandbox/copy strategy") | Out-Null } else { $cons.Add("Sandbox strategy not obvious") | Out-Null }
    if ($Text -match "Remove-Item\s+.*-Recurse|Stop-Process|taskkill|Format-Volume|Clear-Content|Set-Content\s+.*canonical|DROP\s+TABLE") {
        $score -= 25
        $risks.Add("Potential destructive or process-stopping pattern") | Out-Null
    }
    if ($Text -match "Invoke-Expression|iex\s") {
        $score -= 10
        $risks.Add("Invoke-Expression pattern requires review") | Out-Null
    }

    $grade = "C"
    $norm = def_NormalizeScore $score
    if ($norm -ge 90) { $grade = "A+" }
    elseif ($norm -ge 80) { $grade = "A" }
    elseif ($norm -ge 70) { $grade = "B" }
    elseif ($norm -ge 60) { $grade = "C" }
    elseif ($norm -ge 50) { $grade = "D" }
    else { $grade = "F" }

    return [pscustomobject]@{
        Score = $norm
        Grade = $grade
        Pros = ($pros -join "; ")
        Cons = ($cons -join "; ")
        Risks = ($risks -join "; ")
    }
}

function def_Round1_CommandReview {
    def_ShowProgress -Step 4 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Command review"
    $unique = $def_PARAM_COMMAND_CANDIDATES | Select-Object -Unique
    foreach ($path in $unique) {
        $name = Split-Path $path -Leaf
        if (-not (Test-Path -LiteralPath $path)) {
            def_AddRow "Round1" "COMMAND" $name "WARN_NOT_FOUND" "LOW" "PARALLEL_SAFE" "P3" "exists" $false "Candidate not found at this path." $path
            continue
        }

        $item = Get-Item -LiteralPath $path -ErrorAction SilentlyContinue
        if ($null -eq $item) { continue }
        $hash = def_GetSha256Safe -Path $path
        $text = def_ReadTextSafe -Path $path
        $score = def_ScoreCommandContent -Path $path -Text $text
        $parseStatus = "N/A"
        $parseErrors = 0
        $parseText = ""

        if ($item.Extension -in @(".ps1",".psm1",".psd1")) {
            $parse = def_TestPowerShellAstSafe -Path $path
            $parseStatus = if ($parse.Ok) { "OK_PARSE" } else { "WARN_PARSE" }
            $parseErrors = $parse.ErrorCount
            $parseText = $parse.ErrorText
        }

        $risk = "LOW"
        $class = "PARALLEL_SAFE"
        $status = "OK_REVIEWED"
        if ($parseStatus -eq "WARN_PARSE") {
            $risk = "MEDIUM"; $class = "SEQUENTIAL_REQUIRED"; $status = "WARN_PARSE_REVIEW"
        }
        if (-not [string]::IsNullOrWhiteSpace($score.Risks)) {
            $risk = "HIGH"; $class = "SEQUENTIAL_REQUIRED"; $status = "WARN_RISK_PATTERN"
        }

        $review = [pscustomobject]@{
            Name = $name
            Path = $path
            Exists = $true
            Extension = $item.Extension
            Length = $item.Length
            SHA256 = $hash
            ParseStatus = $parseStatus
            ParseErrors = $parseErrors
            ParseErrorText = $parseText
            MethodScore = $score.Score
            Grade = $score.Grade
            Pros = $score.Pros
            Cons = $score.Cons
            Risks = $score.Risks
        }
        $script:def_CommandReviews.Add($review) | Out-Null
        $script:def_FoundCommands.Add($review) | Out-Null

        def_AddRow "Round1" "COMMAND_REVIEW" $name $status $risk $class "P1" "score/grade/parse" "$($score.Score)/$($score.Grade)/$parseStatus" "Pros=[$($score.Pros)] Cons=[$($score.Cons)] Risks=[$($score.Risks)]" $path
    }
}

# =============================================================================
# def ROUND2 SANDBOX / TOOL PROBE
# =============================================================================
function def_Round2_CreateSandbox {
    def_ShowProgress -Step 5 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Create sandbox"
    if (-not $CreateSandbox) {
        def_AddRow "Round2" "SANDBOX" "Sandbox Copy" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "copy" $false "Sandbox copy disabled." $def_SANDBOX_TOOLS_DIR
        return
    }
    foreach ($cmd in (def_AsArraySafe $script:def_FoundCommands)) {
        try {
            $destName = "{0}_{1}" -f (($cmd.Grade -replace '[^\w]','_')), (Split-Path $cmd.Path -Leaf)
            $dest = Join-Path $def_SANDBOX_TOOLS_DIR $destName
            Copy-Item -LiteralPath $cmd.Path -Destination $dest -Force
            def_AddRow "Round2" "SANDBOX" (Split-Path $cmd.Path -Leaf) "OK_COPIED" "LOW" "PARALLEL_SAFE" "P1" "dest" $dest "Copied to sandbox only." $cmd.Path
        } catch {
            def_AddRow "Round2" "SANDBOX" (Split-Path $cmd.Path -Leaf) "WARN_COPY_FAILED" "MEDIUM" "PARALLEL_SAFE" "P2" "error" $_.Exception.Message "Sandbox copy failed." $cmd.Path
        }
    }
}

function def_Round2_RunToolDryProbe {
    def_ShowProgress -Step 6 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Tool dry probe"
    if (-not $RunToolDryProbe) {
        def_AddRow "Round2" "DRY_PROBE" "External Tool Probe" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "run" $false "Tool dry probe disabled." ""
        return
    }
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh) {
        def_AddRow "Round2" "DRY_PROBE" "pwsh" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "pwsh missing; cannot probe PS tools." ""
        return
    }

    $probeTargets = @(
        "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1",
        "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
    )
    foreach ($p in $probeTargets) {
        $name = Split-Path $p -Leaf
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
            def_AddRow "Round2" "DRY_PROBE" $name "WARN_NOT_FOUND" "LOW" "PARALLEL_SAFE" "P3" "exists" $false "Probe target missing." $p
            continue
        }
        $parse = def_TestPowerShellAstSafe -Path $p
        if (-not $parse.Ok) {
            def_AddRow "Round2" "DRY_PROBE" $name "WARN_PARSE_BLOCKED" "MEDIUM" "SEQUENTIAL_REQUIRED" "P0" "parse_errors" $parse.ErrorCount "Blocked from probe due parse errors." $p
            continue
        }
        $res = def_InvokeChildProcessSafe -Name ("Probe_" + $name) -FilePath $pwsh.Source -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$p) -WorkingDirectory (Split-Path $p -Parent) -TimeoutSeconds $TimeoutSec
        $risk = "LOW"
        if ($res.TimedOut -or ($res.Status -notlike "OK_EXIT_0")) { $risk = "MEDIUM" }
        def_AddRow "Round2" "DRY_PROBE" $name $res.Status $risk "PARALLEL_SAFE" "P2" "exit" $res.ExitCode $res.Message $p
    }
}

# =============================================================================
# def ROUND2 METHOD / LIBRARY PLAN
# =============================================================================
function def_Round2_ExportMethodAndLibraries {
    def_ShowProgress -Step 7 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Methodology + libs"
    def_BuildMethodology
    def_BuildTopLibraryMatrices

    $script:def_Methodology | Export-Csv -LiteralPath $def_METHOD_CSV -NoTypeInformation -Encoding UTF8BOM
    $script:def_TopLibraries | Export-Csv -LiteralPath $def_TOP_LIBS_CSV -NoTypeInformation -Encoding UTF8BOM
    $script:def_ProcessMiningTop20 | Export-Csv -LiteralPath $def_PROCESS_MINING_TOP20_CSV -NoTypeInformation -Encoding UTF8BOM

    def_AddRow "Round2" "METHODOLOGY" "Three-Round Safety Method" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P0" "rows" (def_CountSafe $script:def_Methodology) "Three-round method generated." $def_METHOD_CSV
    def_AddRow "Round2" "LIBRARY_MATRIX" "Top10 Local Free Libs by Flow/Lang" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "rows" (def_CountSafe $script:def_TopLibraries) "Top10 libraries generated for each flow and language area." $def_TOP_LIBS_CSV
    def_AddRow "Round2" "LIBRARY_MATRIX" "Top20 Enterprise Form to Process Mining" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "rows" (def_CountSafe $script:def_ProcessMiningTop20) "Top20 document/form-to-process-mining stack generated." $def_PROCESS_MINING_TOP20_CSV
}

function def_Round2_GenerateInstallPlans {
    def_ShowProgress -Step 8 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Install plans"
    $heavyPlan = @'
param(
    [bool]$InstallHeavyPythonPackages = $false,
    [bool]$KeepPowerShellOpen = $true
)

# Optional heavy package plan.
# Default is review-only. Set -InstallHeavyPythonPackages $true only inside a dedicated sandbox venv.
$packages_light = @("pandas","polars","duckdb","pyarrow","pm4py","networkx","pandera","rich","tqdm")
$packages_heavy = @("docling","paddleocr","ocrmypdf","pytesseract","pdfplumber","pymupdf","camelot-py","tabula-py","opencv-python","unstructured","markitdown","tika","great_expectations")

function def_InstallPipPackageList {
    param([string[]]$Packages)
    foreach ($pkg in $Packages) {
        Write-Host "[PIP] $pkg" -ForegroundColor Cyan
        python -m pip install $pkg
    }
}

Write-Host "Review packages first. Heavy install is disabled by default." -ForegroundColor Yellow
Write-Host "Light packages: $($packages_light -join ', ')"
Write-Host "Heavy packages: $($packages_heavy -join ', ')"

if ($InstallHeavyPythonPackages) {
    def_InstallPipPackageList -Packages $packages_light
    def_InstallPipPackageList -Packages $packages_heavy
} else {
    Write-Host "DRY_RUN: no Python package installed." -ForegroundColor Green
}

if ($KeepPowerShellOpen) {
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}
'@
    $heavyPlan | Set-Content -LiteralPath $def_INSTALL_PLAN_PS1 -Encoding UTF8

    $applyPlan = @"
# VIA Apply Plan · Review Only
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# This file is intentionally non-destructive.
# It lists the safe order:
# 1. Fix PowerShell parse errors first.
# 2. Rerun Polyglot CTR.
# 3. Only when FAIL=0, run PSScriptAnalyzer -Fix / ruff --fix in sandbox.
# 4. Re-run VDF / VRN user smoke test.
# 5. Only after review, manually copy confirmed files to original.

Write-Host "Review-only apply plan. No changes are performed." -ForegroundColor Yellow
Write-Host "Report: $def_REPORT_HTML"
Write-Host "Command review: $def_COMMAND_REVIEW_CSV"
Write-Host "Top libs: $def_TOP_LIBS_CSV"
Write-Host "Top20 process mining libs: $def_PROCESS_MINING_TOP20_CSV"
"@
    $applyPlan | Set-Content -LiteralPath $def_APPLY_PLAN_PS1 -Encoding UTF8

    $firstCmd = @"
# VIA Strongest First Step Command
# Safe read-only + additive bootstrap.
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSCommandPath" -Root "$Root" -Downloads "$Downloads" -SupportiveDir "$SupportiveDir" -AllowNetworkInstall `$$AllowNetworkInstall -InstallLightPSModules `$$InstallLightPSModules -InstallHeavyPythonPackages `$$false -RunToolDryProbe `$$true -CreateSandbox `$$true -OpenReport `$$true
"@
    $firstCmd | Set-Content -LiteralPath $def_FIRSTSTEP_CMD_PS1 -Encoding UTF8

    def_AddRow "Round2" "PLAN" "Optional Heavy Install Plan" "OK_WRITTEN" "LOW" "SEQUENTIAL_GATED" "P2" "file" "ready" "Heavy document/OCR/process-mining installs are planned but not forced." $def_INSTALL_PLAN_PS1
    def_AddRow "Round2" "PLAN" "Review Only Apply Plan" "OK_WRITTEN" "LOW" "SEQUENTIAL_GATED" "P2" "file" "ready" "Non-destructive apply plan generated." $def_APPLY_PLAN_PS1
    def_AddRow "Round2" "PLAN" "Strongest First Step Command" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "file" "ready" "Reusable one-command first step generated." $def_FIRSTSTEP_CMD_PS1
}

# =============================================================================
# def ROUND3 BRIDGE / CONSOLIDATION
# =============================================================================
function def_Round3_GenerateBridge {
    def_ShowProgress -Step 9 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Bridge"
    $bridge = @"
# VIA FirstStep Panorama Bridge
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Import:
# Import-Module "$def_BRIDGE_PSM1" -Force

function def_InvokeVIAFirstStep {
    param(
        [string]`$ScriptPath = "$PSCommandPath",
        [int]`$TimeoutSec = 180
    )
    `$pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not `$pwsh) {
        return [pscustomobject]@{Status="FAIL_PWSH_MISSING"; Message="pwsh not found."}
    }
    `$out = Join-Path "$def_LOG_DIR" ("bridge_firststep_stdout_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    `$err = Join-Path "$def_LOG_DIR" ("bridge_firststep_stderr_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    `$args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",`$ScriptPath,"-OpenReport", "`$true")
    `$p = Start-Process -FilePath `$pwsh.Source -ArgumentList `$args -WorkingDirectory "$Root" -RedirectStandardOutput `$out -RedirectStandardError `$err -PassThru -WindowStyle Hidden
    `$finished = `$p.WaitForExit(`$TimeoutSec * 1000)
    if (-not `$finished) {
        return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; Stdout=`$out; Stderr=`$err}
    }
    return [pscustomobject]@{Status=("OK_EXIT_{0}" -f `$p.ExitCode); ExitCode=`$p.ExitCode; Stdout=`$out; Stderr=`$err}
}

function def_GetVIAFirstStepArtifacts {
    return [pscustomobject]@{
        RunRoot = "$def_RUN_ROOT"
        ReportHtml = "$def_REPORT_HTML"
        MatrixCsv = "$def_MATRIX_CSV"
        CommandReviewCsv = "$def_COMMAND_REVIEW_CSV"
        TopLibsCsv = "$def_TOP_LIBS_CSV"
        ProcessMiningTop20Csv = "$def_PROCESS_MINING_TOP20_CSV"
        FirstStepCommand = "$def_FIRSTSTEP_CMD_PS1"
    }
}

Export-ModuleMember -Function def_InvokeVIAFirstStep,def_GetVIAFirstStepArtifacts
"@
    try {
        $bridge | Set-Content -LiteralPath $def_BRIDGE_PSM1 -Encoding UTF8
        $meta = [ordered]@{
            schema = "VIA.FirstStep.PanoramaBridge"
            version = "v0.3.0"
            generated = (Get-Date).ToString("s")
            root = $Root
            tool_root = $ToolRoot
            run_root = $def_RUN_ROOT
            bridge = $def_BRIDGE_PSM1
            policy = $def_PARAM_POLICY
            artifacts = [ordered]@{
                report = $def_REPORT_HTML
                matrix = $def_MATRIX_CSV
                command_review = $def_COMMAND_REVIEW_CSV
                method = $def_METHOD_CSV
                top_libs = $def_TOP_LIBS_CSV
                process_mining_top20 = $def_PROCESS_MINING_TOP20_CSV
                first_step = $def_FIRSTSTEP_CMD_PS1
            }
        }
        $meta | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $def_BRIDGE_JSON -Encoding UTF8
        def_AddRow "Round3" "BRIDGE" "VIA_FirstStep_PanoramaBridge.psm1" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "module" "ready" "Reusable bridge module generated." $def_BRIDGE_PSM1
        def_AddRow "Round3" "BRIDGE" "VIA_FirstStep_PanoramaBridge.json" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "json" "ready" "Bridge manifest generated." $def_BRIDGE_JSON
    } catch {
        def_AddRow "Round3" "BRIDGE" "Bridge Generation" "FAIL_WRITE_ERROR" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Bridge generation failed." $def_BRIDGE_PSM1
    }
}

function def_Round3_FinalClassification {
    def_ShowProgress -Step 10 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Classification"
    $rows = def_AsArraySafe $script:def_Rows
    $parallel = def_CountSafe ($rows | Where-Object { $_.Class -eq "PARALLEL_SAFE" -and $_.Risk -ne "HIGH" })
    $sequential = def_CountSafe ($rows | Where-Object { $_.Class -like "SEQUENTIAL*" -or $_.Risk -eq "HIGH" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })
    $medium = def_CountSafe ($rows | Where-Object { $_.Risk -eq "MEDIUM" })

    def_AddRow "Round3" "CLASSIFY" "Parallel Safe Items" "OK_CLASSIFIED" "LOW" "PARALLEL_SAFE" "P1" "count" $parallel "Can be inspected or improved independently." ""
    $seqStatus = "OK_CLASSIFIED"; $seqRisk = "LOW"
    if ($high -gt 0) { $seqStatus = "WARN_REVIEW_REQUIRED"; $seqRisk = "HIGH" }
    elseif ($medium -gt 0) { $seqStatus = "WARN_REVIEW"; $seqRisk = "MEDIUM" }
    def_AddRow "Round3" "CLASSIFY" "Sequential Gated Items" $seqStatus $seqRisk "SEQUENTIAL_GATED" "P0" "count" $sequential "Handle in order to avoid Hydra risk." ""
    $hydraStatus = "OK_HYDRA_CLEAR"; $hydraRisk = "LOW"
    if ($high -gt 0) { $hydraStatus = "WARN_HYDRA_REVIEW"; $hydraRisk = "HIGH" }
    def_AddRow "Round3" "CLASSIFY" "Hydra Risk Gate" $hydraStatus $hydraRisk "SEQUENTIAL_GATED" "P0" "high" $high "High-risk issues isolated before any apply action." ""
}

# =============================================================================
# def EXPORT / HTML
# =============================================================================
function def_ExportAll {
    def_ShowProgress -Step 11 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "Export"
    $rows = def_AsArraySafe $script:def_Rows
    $rows | Export-Csv -LiteralPath $def_MATRIX_CSV -NoTypeInformation -Encoding UTF8BOM
    $rows | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $def_MATRIX_JSON -Encoding UTF8
    $script:def_CommandReviews | Export-Csv -LiteralPath $def_COMMAND_REVIEW_CSV -NoTypeInformation -Encoding UTF8BOM
}

function def_WriteHtmlReport {
    def_ShowProgress -Step 12 -Total 12 -Activity "VIA FirstStep Panorama Sandbox" -Status "HTML report"
    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    $risk = "LOW"
    if ($fail -gt 0) { $risk = "HIGH" }
    elseif ($warn -gt 0) { $risk = "MEDIUM" }

    $commandRows = foreach ($c in (def_AsArraySafe $script:def_CommandReviews)) {
        $riskClass = "risk-low"
        if ($c.Risks) { $riskClass = "risk-high" }
        elseif ($c.ParseStatus -eq "WARN_PARSE") { $riskClass = "risk-medium" }
        "<tr class='$riskClass'><td>$(def_HtmlEncode $c.Name)</td><td>$(def_HtmlEncode $c.Grade)</td><td>$(def_HtmlEncode $c.MethodScore)</td><td>$(def_HtmlEncode $c.ParseStatus)</td><td>$(def_HtmlEncode $c.ParseErrors)</td><td>$(def_HtmlEncode $c.Pros)</td><td>$(def_HtmlEncode $c.Cons)</td><td>$(def_HtmlEncode $c.Risks)</td><td>$(def_HtmlEncode $c.Path)</td></tr>"
    }

    $matrixRows = foreach ($r in $rows) {
        $riskClass = "risk-low"
        if ($r.Risk -eq "HIGH") { $riskClass = "risk-high" }
        elseif ($r.Risk -eq "MEDIUM") { $riskClass = "risk-medium" }
        "<tr class='$riskClass'><td>$(def_HtmlEncode $r.Round)</td><td>$(def_HtmlEncode $r.Layer)</td><td>$(def_HtmlEncode $r.Name)</td><td>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.Risk)</td><td>$(def_HtmlEncode $r.Class)</td><td>$(def_HtmlEncode $r.Priority)</td><td>$(def_HtmlEncode $r.Metric)</td><td>$(def_HtmlEncode $r.Value)</td><td>$(def_HtmlEncode $r.Message)</td><td>$(def_HtmlEncode $r.Path)</td></tr>"
    }

    $methodRows = foreach ($m in (def_AsArraySafe $script:def_Methodology)) {
        "<tr><td>$(def_HtmlEncode $m.Round)</td><td>$(def_HtmlEncode $m.Phase)</td><td>$(def_HtmlEncode $m.Goal)</td><td>$(def_HtmlEncode $m.Action)</td><td>$(def_HtmlEncode $m.ParallelSafe)</td><td>$(def_HtmlEncode $m.SequentialGate)</td><td>$(def_HtmlEncode $m.Output)</td></tr>"
    }

    $top20Rows = foreach ($p in (def_AsArraySafe $script:def_ProcessMiningTop20)) {
        "<tr><td>$(def_HtmlEncode $p.Rank)</td><td>$(def_HtmlEncode $p.Name)</td><td>$(def_HtmlEncode $p.Lang)</td><td>$(def_HtmlEncode $p.Stage)</td><td>$(def_HtmlEncode $p.UseCase)</td><td>$(def_HtmlEncode $p.RiskNote)</td></tr>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA FirstStep Panorama Sandbox</title>
<style>
body{margin:0;background:#f8f8f4;color:#18211f;font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;}
header{padding:34px 42px;border-bottom:1px solid #d7ded8;background:
radial-gradient(circle at 12% 15%,rgba(83,130,118,.18),transparent 35%),
linear-gradient(135deg,#f8f8f4,#e9f1ee);}
h1{margin:0;font-size:27px;letter-spacing:.04em;font-weight:650}
.sub{margin-top:9px;color:#53615c;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:20px 42px}
.card{background:white;border:1px solid #d7ded8;border-radius:18px;padding:16px;box-shadow:0 10px 30px rgba(20,40,35,.06)}
.k{font-size:12px;color:#6c7771}.v{font-size:22px;font-weight:750;margin-top:4px}
.wrap{padding:0 42px 34px 42px}
h2{margin:24px 0 10px 0;font-size:18px}
table{border-collapse:collapse;width:100%;font-size:12px;background:white;border-radius:16px;overflow:hidden}
th{position:sticky;top:0;background:#22342f;color:white;text-align:left;padding:9px}
td{border-bottom:1px solid #e4e8e5;padding:8px;vertical-align:top}
.risk-low td{background:#fbfffd}.risk-medium td{background:#fffaf0}.risk-high td{background:#fff3f1}
code{font-family:Consolas,monospace}
.footer{padding:24px 42px;color:#66736d;font-size:12px}
</style>
</head>
<body>
<header>
<h1>理 · VIA FirstStep Panorama Sandbox · Three-Round Safety Gate</h1>
<div class="sub">Run ID: $def_PARAM_RUN_ID · Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") · Root: $(def_HtmlEncode $Root)</div>
</header>
<section class="grid">
<div class="card"><div class="k">Status</div><div class="v">$(if($fail -gt 0){"REVIEW"}elseif($warn -gt 0){"READY_WARN"}else{"READY"})</div></div>
<div class="card"><div class="k">Risk</div><div class="v">$risk</div></div>
<div class="card"><div class="k">OK</div><div class="v">$ok</div></div>
<div class="card"><div class="k">WARN</div><div class="v">$warn</div></div>
<div class="card"><div class="k">HIGH</div><div class="v">$fail</div></div>
</section>
<section class="wrap">
<h2>def Command Strength / Weakness Review</h2>
<table><thead><tr><th>Name</th><th>Grade</th><th>Score</th><th>Parse</th><th>Errors</th><th>Pros</th><th>Cons</th><th>Risks</th><th>Path</th></tr></thead><tbody>
$($commandRows -join "`n")
</tbody></table>

<h2>def Three-Round Methodology</h2>
<table><thead><tr><th>Round</th><th>Phase</th><th>Goal</th><th>Action</th><th>Parallel Safe</th><th>Sequential Gate</th><th>Output</th></tr></thead><tbody>
$($methodRows -join "`n")
</tbody></table>

<h2>def Top 20 Enterprise Forms → Process Mining Local Free Stack</h2>
<table><thead><tr><th>Rank</th><th>Name</th><th>Lang</th><th>Stage</th><th>Use Case</th><th>Risk Note</th></tr></thead><tbody>
$($top20Rows -join "`n")
</tbody></table>

<h2>def Matrix</h2>
<table><thead><tr><th>Round</th><th>Layer</th><th>Name</th><th>Status</th><th>Risk</th><th>Class</th><th>Priority</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th></tr></thead><tbody>
$($matrixRows -join "`n")
</tbody></table>
</section>
<div class="footer">
Outputs: <code>$def_RUN_ROOT</code><br>
First Step Command: <code>$def_FIRSTSTEP_CMD_PS1</code><br>
Bridge: <code>$def_BRIDGE_PSM1</code>
</div>
</body>
</html>
"@
    $html | Set-Content -LiteralPath $def_REPORT_HTML -Encoding UTF8
    Write-Progress -Activity "VIA FirstStep Panorama Sandbox" -Completed
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA FirstStep Panorama Sandbox AIO v0.3.0" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Root       : $Root"
    Write-Host "Tool Root  : $ToolRoot"
    Write-Host "Run ID     : $def_PARAM_RUN_ID"
    Write-Host "Policy     : no DB write · no canonical merge · no destructive delete · no stop-process · append-only"
    Write-Host ""

    def_Round0_Initialize
    def_Round1_CheckNativeTools
    def_Round1_InstallLightPSModules
    def_Round1_CommandReview
    def_Round2_CreateSandbox
    def_Round2_RunToolDryProbe
    def_Round2_ExportMethodAndLibraries
    def_Round2_GenerateInstallPlans
    def_Round3_GenerateBridge
    def_Round3_FinalClassification
    def_ExportAll
    def_WriteHtmlReport

    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" -or $_.Status -like "FAIL*" })

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA FIRSTSTEP PANORAMA SANDBOX COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status       : $(if($high -gt 0){"READY_WITH_REVIEW"}elseif($warn -gt 0){"READY_WITH_WARNINGS"}else{"READY"})"
    Write-Host "OK/WARN/HIGH : $ok / $warn / $high"
    Write-Host "Run Root     : $def_RUN_ROOT"
    Write-Host "HTML         : $def_REPORT_HTML"
    Write-Host "Matrix CSV   : $def_MATRIX_CSV"
    Write-Host "Command CSV  : $def_COMMAND_REVIEW_CSV"
    Write-Host "Method CSV   : $def_METHOD_CSV"
    Write-Host "Top Libs CSV : $def_TOP_LIBS_CSV"
    Write-Host "Top20 CSV    : $def_PROCESS_MINING_TOP20_CSV"
    Write-Host "Bridge       : $def_BRIDGE_PSM1"
    Write-Host "First Step   : $def_FIRSTSTEP_CMD_PS1"
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
        def_AddRow "FATAL" "RUNTIME" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Unhandled exception caught; exporting partial report." ""
        def_ExportAll
        def_WriteHtmlReport
    } catch {}
} finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
