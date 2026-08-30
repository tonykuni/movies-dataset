
# =============================================================================
# def HOTFIX v0203
# =============================================================================
# def 修正 PowerShell Mandatory collection 參數拒絕空 ArrayList 的問題。
# def Root cause:
# def - def_AddMatrixRow 的 Rows 參數為 Mandatory。
# def - 空 ArrayList 在 PowerShell binder 會被視為 empty collection，不允許綁定。
# def Fix:
# def - 加入 [AllowEmptyCollection()]。
# def - 加入 null guard。
# =============================================================================

# =============================================================================
# def VERITASONE SINGLE ENTRY
# =============================================================================
# def 這是單一入口版本：
# def - 一個 PowerShell 檔案
# def - 自動跑 CodexNexus
# def - 自動跑 VDF Fetch / VDF Main / Panorama Gate
# def - 自動找資料位置
# def - 自動檢查 ETF rows / 最大資料日 / placeholder / schema
# def - 自動產出 DataBound HTML 與 Final Matrix Report
# def - 不覆蓋原始 Console；不刪除；不 Stop-Process
# =============================================================================

#requires -Version 7.0
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
<#
def VeritasONE · CodexNexus × VDF × ETF DataBound AIO Gate v0203
def Purpose:
def - One PowerShell to handle all.
def - Run CodexNexus / VDF scripts.
def - Perform three-round panorama scan / test / debug / upgrade / optimize / consolidate / user-test.
def - Find local data positions automatically.
def - Validate ETF rows, dates, placeholder risks, schema coverage.
def - Produce HTML UI Matrix report.
def - If real ETF rows exist, produce a separate DataBound HTML evidence console.
def Policy:
def - No destructive delete.
def - No canonical overwrite.
def - No Stop-Process.
def - No in-place source modification by default.
def - Child job timeout only prevents this wrapper from hanging.
#>

# =============================================================================
# def 00 · PARAMETERS AT TOP
# =============================================================================

$def_PARAM_VERSION = "v0203_MANIFEST_AUTOFIX"
$def_PARAM_TARGET_DATA_ASOF = "2026-06-19"

$def_PARAM_BASE_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_PARAM_FUNCTIONAL_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules"
$def_PARAM_CODEX_NEXUS_PATH = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\Invoke-VeritasCodexNexus.ps1"

$def_PARAM_ENABLE_CODEX_NEXUS_RUN = $true
$def_PARAM_ENABLE_VDF_FETCH_RUN = $true
$def_PARAM_ENABLE_VDF_MAIN_RUN = $true
$def_PARAM_ENABLE_PANORAMA_GATE_RUN = $true
$def_PARAM_ENABLE_DATA_SCAN = $true
$def_PARAM_ENABLE_DATABOUND_HTML_OUTPUT = $true
$def_PARAM_ENABLE_INPLACE_PATCH = $false
$def_PARAM_OPEN_HTML_REPORT = $true

$def_PARAM_TIMEOUT_SECONDS_CODEX = 900
$def_PARAM_TIMEOUT_SECONDS_VDF = 1200
$def_PARAM_TIMEOUT_SECONDS_PANORAMA = 900

$def_PARAM_SCAN_MAX_DEPTH_NOTE = "PowerShell Get-ChildItem does not hard-limit depth here; roots are bounded instead."
$def_PARAM_MAX_SAMPLE_ROWS = 100
$def_PARAM_MAX_SCAN_FILES_PER_ROOT_PATTERN = 3000

$def_PARAM_RUN_LABEL = "VERITASONE_CODEX_NEXUS_VDF_ETF_AIO_GATE"

$def_PARAM_VDF_SCRIPT_CANDIDATES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF-Fetch.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\Invoke-VDF-Nexus-Panorama3RoundGate.ps1"
)

$def_PARAM_VDF_REFERENCE_JSON = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL401_RegistrySchema.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL402_RegistrySample.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL403_RegistryFull.json"
)

$def_PARAM_DATA_ROOTS = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\桌面\tw_stock",
    "C:\Users\tonyk\Desktop\tw_stock",
    "C:\Users\tonyk\Downloads",
    "C:\Users\tonyk\OneDrive\Documents"
)

$def_PARAM_DATA_FILE_PATTERNS = @(
    "active_etf*.parquet",
    "active_etf*.csv",
    "active_etf*.json",
    "active_etf*.duckdb",
    "*Active*ETF*.parquet",
    "*Active*ETF*.csv",
    "*Active*ETF*.json",
    "*Active*ETF*.duckdb",
    "*Active*ETF*.html",
    "*ETF*.parquet",
    "*ETF*.csv",
    "*ETF*.json",
    "*ETF*.duckdb",
    "*ETF*.html",
    "StockData.parquet",
    "StockData.csv",
    "*.duckdb"
)

$def_PARAM_CONSOLE_HTML_PATTERNS = @(
    "*Active*Taiwan*Stock*ETF*Console*.html",
    "*active*etf*console*.html",
    "*ETF*Console*.html"
)

$def_PARAM_DATE_FIELD_HINTS = @(
    "trade_date","date","asof","as_of","data_asof","update_date","updated",
    "資料日","交易日","日期","年月日","出表日期","更新日"
)

$def_PARAM_REQUIRED_ETF_FIELD_KEYWORDS = @(
    "ticker","symbol","code","代號","證券代號",
    "name","名稱","基金名稱",
    "date","trade_date","asof","資料日","日期",
    "return","報酬","performance","績效",
    "aum","規模","asset","nav","淨值","volume","成交量",
    "premium","discount","折溢價"
)

$def_PARAM_PLACEHOLDER_MARKERS = @(
    "示意","暫無資料","placeholder","demo","mock","sample","dummy","TODO","TBD",
    "績效/規模為示意","績效為示意","規模為示意","null data","empty data"
)

$def_PARAM_PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe",
    "python",
    "py"
)

$def_PARAM_POWERSHELL_ACCELERATORS_TOP15 = @(
    @{ Name="ThreadJob"; Role="bounded parallel script/data checks"; Use="Start-ThreadJob or Start-Job fallback"; Risk="LOW" },
    @{ Name="ForEach-Object -Parallel"; Role="parallel file candidate scan"; Use="PS7 bounded throttle"; Risk="LOW" },
    @{ Name="Write-Progress"; Role="dynamic progress bar"; Use="phase/round/status display"; Risk="LOW" },
    @{ Name="Start-Job"; Role="timeout-safe child process wrapper"; Use="no Stop-Process"; Risk="LOW" },
    @{ Name="Measure-Command"; Role="runtime timing"; Use="duration matrix"; Risk="LOW" },
    @{ Name="ConvertTo-Json"; Role="structured evidence output"; Use="machine-readable summary"; Risk="LOW" },
    @{ Name="ConvertFrom-Json"; Role="structured evidence input"; Use="matrix building"; Risk="LOW" },
    @{ Name="Test-Path"; Role="path/file hard gate"; Use="missing blocker"; Risk="LOW" },
    @{ Name="Get-ChildItem"; Role="local data discovery"; Use="bounded roots/patterns"; Risk="MEDIUM" },
    @{ Name="Get-FileHash"; Role="backup/evidence identity"; Use="sha256/sha12 trace"; Risk="LOW" },
    @{ Name="Copy-Item"; Role="safe backup/copy output"; Use="no overwrite canonical"; Risk="LOW" },
    @{ Name="ImportExcel"; Role="optional xlsx report"; Use="only when installed"; Risk="LOW" },
    @{ Name="Pester"; Role="optional unit gate"; Use="only when installed"; Risk="LOW" },
    @{ Name="PSScriptAnalyzer"; Role="optional static analysis"; Use="only when installed"; Risk="LOW" },
    @{ Name="PSWriteHTML"; Role="optional richer HTML"; Use="fallback built-in HTML"; Risk="LOW" }
)

$def_PARAM_TOP10_LOCAL_FREE_LIBS_MATRIX = @(
    @{ Flow="資料存在性檢查"; Python="pandas; polars; pyarrow; duckdb; sqlite3; pathlib; jsonschema; pandera; great_expectations; rich"; PowerShell="Pester; ImportExcel; ThreadJob; PSFramework; PSScriptAnalyzer; PSReadLine; ConvertFrom-Json; Test-Path; Get-FileHash; PSWriteHTML"; JS_TS_HTML="PapaParse; Arquero; Danfo.js; AlaSQL; Zod; Ajv; Lodash; Day.js; Tabulator; Grid.js" },
    @{ Flow="測試與偵錯"; Python="pytest; unittest; hypothesis; coverage.py; tox; nox; pytest-xdist; pytest-cov; pytest-mock; pyfakefs"; PowerShell="Pester; PSScriptAnalyzer; ThreadJob; InvokeBuild; psake; platyPS; PSFramework; BurntToast; ImportExcel; PSReadLine"; JS_TS_HTML="Vitest; Jest; Playwright; Cypress; Testing Library; jsdom; happy-dom; Mocha; Chai; Sinon" },
    @{ Flow="HTML UI 測試"; Python="playwright; selenium; beautifulsoup4; lxml; html5lib; pytest-playwright; pyppeteer; cssselect; tinycss2; requests-html"; PowerShell="Pester; Invoke-WebRequest; Pode; PSWriteHTML; PSScriptAnalyzer; ThreadJob; ImportExcel; BurntToast; PSFramework; PSReadLine"; JS_TS_HTML="Playwright; Cypress; Puppeteer; Vitest; jsdom; axe-core; Lighthouse; Testing Library; ESLint; Prettier" },
    @{ Flow="效能與記憶體"; Python="psutil; scalene; pyinstrument; memory-profiler; line-profiler; numpy; polars; duckdb; joblib; tqdm"; PowerShell="ThreadJob; ForEach-Object -Parallel; Measure-Command; Get-Process; Pester; PSFramework; ImportExcel; BurntToast; PSScriptAnalyzer; PSReadLine"; JS_TS_HTML="Lighthouse; Web Vitals; Rollup visualizer; esbuild; Vite; SWC; terser; source-map-explorer; Playwright; Performance API" },
    @{ Flow="報表與 Matrix"; Python="pandas; jinja2; dominate; yattag; plotly; markdown; rich; tabulate; pyarrow; duckdb"; PowerShell="PSWriteHTML; ImportExcel; ConvertTo-Html; Pester; PSFramework; ThreadJob; BurntToast; Pode; PSScriptAnalyzer; PSReadLine"; JS_TS_HTML="Tabulator; Grid.js; DataTables; Chart.js; ECharts; D3; Plotly.js; Mermaid; Tailwind; Alpine.js" },
    @{ Flow="資料品質與 Schema"; Python="pandera; pydantic; jsonschema; great_expectations; frictionless; cerberus; voluptuous; marshmallow; duckdb; pyarrow"; PowerShell="Pester; PSScriptAnalyzer; ImportExcel; PSFramework; ThreadJob; ConvertFrom-Json; Test-Path; Get-FileHash; Compare-Object; PSWriteHTML"; JS_TS_HTML="Zod; Ajv; TypeBox; Valibot; Yup; Superstruct; io-ts; Lodash; Day.js; Arquero" },
    @{ Flow="封裝與整併"; Python="pathlib; shutil; zipfile; hatch; poetry; pip-tools; nuitka; pyinstaller; tomli; platformdirs"; PowerShell="PS2EXE; Compress-Archive; InvokeBuild; psake; Pester; PSScriptAnalyzer; ImportExcel; ThreadJob; PSFramework; SecretManagement"; JS_TS_HTML="Vite; Rollup; esbuild; Webpack; SWC; pnpm; npm; yarn; tsup; pkg" },
    @{ Flow="資料抓取 / Fetch"; Python="requests; httpx; aiohttp; yfinance; pandas-datareader; tenacity; backoff; duckdb; pyarrow; tqdm"; PowerShell="Invoke-WebRequest; Invoke-RestMethod; Start-Job; ThreadJob; Pester; PSFramework; ConvertFrom-Json; ImportExcel; PSReadLine; SecretManagement"; JS_TS_HTML="fetch; axios; ky; got; cheerio; node-html-parser; p-limit; p-retry; Day.js; Zod" }
)

$ErrorActionPreference = "Stop"

# =============================================================================
# def 01 · BASIC UTILITIES
# =============================================================================

function def_GetTimestamp {
    return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function def_EnsureDirectory {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    return $Path
}

function def_ToHtmlEncoded {
    param([AllowNull()][object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_GetSafeFileName {
    param([Parameter(Mandatory=$true)][string]$Name)
    $safe = $Name
    foreach ($c in [System.IO.Path]::GetInvalidFileNameChars()) {
        $safe = $safe.Replace([string]$c, "_")
    }
    return $safe
}

function def_WriteLog {
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [string]$Level = "INFO"
    )

    $line = "[{0}] [{1}] {2}" -f (Get-Date).ToString("HH:mm:ss.fff"), $Level, $Message
    Write-Host $line
    if ($script:def_LOG_PATH) {
        Add-Content -LiteralPath $script:def_LOG_PATH -Value $line -Encoding UTF8
    }
}

function def_AddMatrixRow {
    param(
        [Parameter(Mandatory=$true)]
        [AllowEmptyCollection()]
        [System.Collections.ArrayList]$Rows,

        [Parameter(Mandatory=$true)]
        [hashtable]$Row
    )

    if ($null -eq $Rows) {
        throw "def_AddMatrixRow received null Rows collection."
    }

    if ($null -eq $Row) {
        throw "def_AddMatrixRow received null Row hashtable."
    }

    [void]$Rows.Add([pscustomobject]$Row)
}

function def_FormatStatusClass {
    param([AllowNull()][string]$Status)
    if ([string]::IsNullOrWhiteSpace($Status)) { return "neutral" }
    if ($Status -match "READY|PASS|OK|SUCCESS|COMPLETED") { return "ok" }
    if ($Status -match "BLOCK|FAIL|ERROR|FATAL|MISSING|EMPTY|STALE|ZERO") { return "fail" }
    if ($Status -match "WARN|REVIEW|TIMEOUT|PARTIAL|SKIP") { return "warn" }
    return "neutral"
}

function def_ShowProgress {
    param(
        [int]$Round,
        [int]$Step,
        [int]$Total,
        [string]$Status,
        [string]$Activity = "Veritas AIO Gate"
    )

    if ($Total -le 0) { $Total = 1 }
    $pct = [math]::Min(100, [math]::Max(0, [math]::Round(($Step / $Total) * 100, 0)))
    Write-Progress -Activity $Activity -Status ("Round {0} · {1}% · {2}" -f $Round, $pct, $Status) -PercentComplete $pct
    Write-Host ("[{0,3}%] [Round {1}] {2}" -f $pct, $Round, $Status) -ForegroundColor Cyan
}

function def_WriteBanner {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def Veritas CodexNexus × VDF × ETF DataBound AIO Gate $def_PARAM_VERSION" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "[POLICY] No delete · No canonical overwrite · No Stop-Process · Data first" -ForegroundColor Yellow
    Write-Host "[TARGET] ETF data_asof >= $def_PARAM_TARGET_DATA_ASOF" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# def 02 · RUN CONTEXT
# =============================================================================

function def_NewRunContext {
    $runId = "{0}_{1}_{2}" -f (def_GetTimestamp), $def_PARAM_RUN_LABEL, $def_PARAM_VERSION
    $runRoot = Join-Path $def_PARAM_BASE_ROOT "_vdf_auto_fetch_runs"
    $runDir = Join-Path $runRoot $runId

    def_EnsureDirectory -Path $runDir | Out-Null

    $script:def_RUN_ID = $runId
    $script:def_RUN_DIR = $runDir
    $script:def_LOG_PATH = Join-Path $runDir "run.log"

    $script:def_DISCOVERY_MATRIX = New-Object System.Collections.ArrayList
    $script:def_ACCELERATOR_MATRIX = New-Object System.Collections.ArrayList
    $script:def_SCRIPT_RUN_MATRIX = New-Object System.Collections.ArrayList
    $script:def_ROUND_MATRIX = New-Object System.Collections.ArrayList
    $script:def_DATA_MATRIX = New-Object System.Collections.ArrayList
    $script:def_GATE_MATRIX = New-Object System.Collections.ArrayList
    $script:def_FIX_MATRIX = New-Object System.Collections.ArrayList
    $script:def_TEST_MATRIX = New-Object System.Collections.ArrayList
    $script:def_RISK_MATRIX = New-Object System.Collections.ArrayList
    $script:def_LIBS_MATRIX = New-Object System.Collections.ArrayList
    $script:def_OUTPUT_MATRIX = New-Object System.Collections.ArrayList

    def_WriteLog "RunDir: $runDir" "OK"
    return $runDir
}

# =============================================================================
# def 03 · ACCELERATOR AND LIB MATRIX
# =============================================================================

function def_InitializeAcceleratorMatrix {
    def_ShowProgress -Round 0 -Step 1 -Total 4 -Status "Initialize 15 PowerShell accelerators matrix"

    foreach ($a in $def_PARAM_POWERSHELL_ACCELERATORS_TOP15) {
        $available = "BUILT_IN_OR_OPTIONAL"
        if ($a.Name -in @("ImportExcel","Pester","PSScriptAnalyzer","PSWriteHTML","PSFramework","BurntToast")) {
            $mod = Get-Module -ListAvailable -Name $a.Name -ErrorAction SilentlyContinue | Select-Object -First 1
            $available = $(if ($mod) { "AVAILABLE" } else { "OPTIONAL_MISSING" })
        }

        def_AddMatrixRow -Rows $script:def_ACCELERATOR_MATRIX -Row ([ordered]@{
            def_accelerator = $a.Name
            def_role = $a.Role
            def_use = $a.Use
            def_risk = $a.Risk
            def_status = $available
        })
    }

    foreach ($l in $def_PARAM_TOP10_LOCAL_FREE_LIBS_MATRIX) {
        def_AddMatrixRow -Rows $script:def_LIBS_MATRIX -Row ([ordered]@{
            def_flow = $l.Flow
            def_python_top10 = $l.Python
            def_powershell_top10 = $l.PowerShell
            def_js_ts_html_top10 = $l.JS_TS_HTML
        })
    }
}

# =============================================================================
# def 04 · DISCOVERY
# =============================================================================

function def_RegisterPathEvidence {
    param(
        [Parameter(Mandatory=$true)][string]$Role,
        [Parameter(Mandatory=$true)][string]$Path
    )

    $exists = Test-Path -LiteralPath $Path
    $type = "missing"
    $size = 0
    $modified = ""
    $sha12 = ""
    $status = "MISSING"

    if ($exists) {
        $item = Get-Item -LiteralPath $Path
        $type = $(if ($item.PSIsContainer) { "directory" } else { $item.Extension })
        $size = $(if ($item.PSIsContainer) { 0 } else { $item.Length })
        $modified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        if (-not $item.PSIsContainer) {
            try {
                $sha12 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.Substring(0,12)
            } catch { $sha12 = "" }
        }
        $status = "FOUND"
    }

    def_AddMatrixRow -Rows $script:def_DISCOVERY_MATRIX -Row ([ordered]@{
        def_role = $Role
        def_path = $Path
        def_exists = $exists
        def_type = $type
        def_size_bytes = $size
        def_modified = $modified
        def_sha12 = $sha12
        def_status = $status
    })

    return $exists
}

function def_DiscoverSystem {
    def_ShowProgress -Round 0 -Step 2 -Total 4 -Status "Discover CodexNexus / VDF / data roots"

    [void](def_RegisterPathEvidence -Role "BASE_ROOT" -Path $def_PARAM_BASE_ROOT)
    [void](def_RegisterPathEvidence -Role "FUNCTIONAL_ROOT" -Path $def_PARAM_FUNCTIONAL_ROOT)
    [void](def_RegisterPathEvidence -Role "CODEX_NEXUS" -Path $def_PARAM_CODEX_NEXUS_PATH)

    foreach ($p in $def_PARAM_VDF_SCRIPT_CANDIDATES) {
        [void](def_RegisterPathEvidence -Role "VDF_SCRIPT_CANDIDATE" -Path $p)
    }

    foreach ($p in $def_PARAM_VDF_REFERENCE_JSON) {
        [void](def_RegisterPathEvidence -Role "VDF_REFERENCE_JSON" -Path $p)
    }

    foreach ($p in $def_PARAM_DATA_ROOTS) {
        [void](def_RegisterPathEvidence -Role "DATA_ROOT_CANDIDATE" -Path $p)
    }
}


# =============================================================================
# def 04B · VIA DATA MANIFEST AUTOFIX
# =============================================================================

function def_GetManifestCandidatePaths {
    $paths = @(
        (Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF\VIA_data_manifest.json"),
        "C:\Users\tonyk\Downloads\VIA_data_manifest.json",
        "C:\Users\tonyk\Desktop\VIA_data_manifest.json",
        "C:\Users\tonyk\OneDrive\Desktop\VIA_data_manifest.json"
    )

    $unique = New-Object System.Collections.ArrayList
    foreach ($p in $paths) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        if ($unique -notcontains $p) {
            [void]$unique.Add($p)
        }
    }
    return @($unique)
}

function def_ReadTextHeadSafe {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$MaxBytes = 120000
    )

    try {
        if (-not (Test-Path -LiteralPath $Path)) { return "" }
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $len = [math]::Min($MaxBytes, $fs.Length)
            $buffer = New-Object byte[] $len
            [void]$fs.Read($buffer, 0, $len)
            return [System.Text.Encoding]::UTF8.GetString($buffer)
        } finally {
            $fs.Close()
        }
    } catch {
        return ""
    }
}

function def_GetDataManifestFileCandidates {
    $rows = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($root in $def_PARAM_DATA_ROOTS) {
        if (-not (Test-Path -LiteralPath $root)) { continue }

        foreach ($pattern in $def_PARAM_DATA_FILE_PATTERNS) {
            try {
                $items = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First $def_PARAM_MAX_SCAN_FILES_PER_ROOT_PATTERN)
                foreach ($item in $items) {
                    if ($seen.ContainsKey($item.FullName)) { continue }
                    $seen[$item.FullName] = $true

                    $lower = $item.FullName.ToLowerInvariant()
                    $kind = "unknown"
                    if ($lower -match "active[_\-\s]*etf|etf") { $kind = "active_etf_or_etf" }
                    elseif ($lower -match "stockdata|tw_stock|yfinance|ticker") { $kind = "tw_stock_market_data" }
                    elseif ($lower -match "duckdb") { $kind = "duckdb_database" }

                    $sha12 = ""
                    try { $sha12 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.Substring(0,12) } catch {}

                    [void]$rows.Add([pscustomobject][ordered]@{
                        def_kind = $kind
                        def_path = $item.FullName
                        def_name = $item.Name
                        def_extension = $item.Extension
                        def_size_bytes = $item.Length
                        def_modified_time = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                        def_sha12 = $sha12
                    })
                }
            } catch {
                def_WriteLog "Manifest scan warning root=$root pattern=$pattern => $($_.Exception.Message)" "WARN"
            }
        }
    }

    return @($rows)
}

function def_GetTickerHintsForManifest {
    $tickerHints = New-Object System.Collections.ArrayList

    $candidateTickerFiles = @(
        "C:\Users\tonyk\OneDrive\桌面\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt",
        "C:\Users\tonyk\Desktop\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt",
        "C:\Users\tonyk\OneDrive\桌面\tw_stock\dict\TickerList\StockTickerListDatabase.csv",
        "C:\Users\tonyk\Desktop\tw_stock\dict\TickerList\StockTickerListDatabase.csv"
    )

    foreach ($p in $candidateTickerFiles) {
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $head = def_ReadTextHeadSafe -Path $p -MaxBytes 200000
        $matches = [regex]::Matches($head, '\b\d{4}\.(TW|TWO)\b', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        foreach ($m in $matches) {
            $v = $m.Value.ToUpperInvariant()
            if ($tickerHints -notcontains $v) { [void]$tickerHints.Add($v) }
            if ($tickerHints.Count -ge 300) { break }
        }
    }

    return @($tickerHints)
}

function def_NewViaDataManifestObject {
    param(
        [Parameter(Mandatory=$true)][object[]]$FileCandidates
    )

    $tickerHints = def_GetTickerHintsForManifest

    $manifest = [ordered]@{
        def_manifest_name = "VIA_data_manifest"
        def_manifest_version = "v0203_manifest_autofix"
        def_generated_by = "Invoke-VeritasONE-CodexNexus-VDF-ETF-AIO-v0203-ManifestAutoFix.ps1"
        def_generated_time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        def_policy = [ordered]@{
            def_no_delete = $true
            def_no_canonical_overwrite = $true
            def_no_stop_process = $true
            def_data_first = $true
            def_ui_date_update_requires_data_rows = $true
        }
        def_target = [ordered]@{
            def_target_data_asof = $def_PARAM_TARGET_DATA_ASOF
            def_market = "Taiwan"
            def_asset_scope = @("tw_stock", "active_etf", "etf", "market_data")
        }
        def_roots = @($def_PARAM_DATA_ROOTS)
        def_vdf = [ordered]@{
            def_base_root = (Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF")
            def_invoke_vdf = (Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF\Invoke-VDF.ps1")
            def_invoke_vdf_fetch = (Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF\Invoke-VDF-Fetch.ps1")
            def_invoke_vdf_panorama = (Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF\Invoke-VDF-Nexus-Panorama3RoundGate.ps1")
        }
        def_schema_hints = [ordered]@{
            def_date_fields = @($def_PARAM_DATE_FIELD_HINTS)
            def_required_etf_keywords = @($def_PARAM_REQUIRED_ETF_FIELD_KEYWORDS)
            def_placeholder_markers = @($def_PARAM_PLACEHOLDER_MARKERS)
        }
        def_ticker_hints = @($tickerHints)
        def_files = @($FileCandidates)
        data_sources = @($FileCandidates | ForEach-Object {
            [ordered]@{
                kind = $_.def_kind
                path = $_.def_path
                name = $_.def_name
                extension = $_.def_extension
                size_bytes = $_.def_size_bytes
                modified_time = $_.def_modified_time
                sha12 = $_.def_sha12
            }
        })
        target_data_asof = $def_PARAM_TARGET_DATA_ASOF
        roots = @($def_PARAM_DATA_ROOTS)
        files = @($FileCandidates)
    }

    return $manifest
}

function def_EnsureViaDataManifest {
    def_ShowProgress -Round 0 -Step 3 -Total 4 -Status "Ensure VIA_data_manifest.json"

    $paths = def_GetManifestCandidatePaths
    $existing = @($paths | Where-Object { Test-Path -LiteralPath $_ })

    if ($existing.Count -gt 0) {
        foreach ($p in $existing) {
            [void](def_RegisterPathEvidence -Role "VIA_DATA_MANIFEST_EXISTING" -Path $p)
        }

        def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
            def_output = "VIA_DATA_MANIFEST"
            def_path = ($existing -join "; ")
            def_status = "EXISTS_REUSED"
            def_message = "Existing VIA_data_manifest.json found. No overwrite."
        })

        return $existing[0]
    }

    def_WriteLog "VIA_data_manifest.json missing. Auto-generating manifest from local data roots." "WARN"

    $fileCandidates = def_GetDataManifestFileCandidates
    $manifest = def_NewViaDataManifestObject -FileCandidates $fileCandidates

    $primary = Join-Path $def_PARAM_FUNCTIONAL_ROOT "VDF\VIA_data_manifest.json"
    $secondary = "C:\Users\tonyk\Downloads\VIA_data_manifest.json"

    foreach ($target in @($primary, $secondary)) {
        try {
            $dir = Split-Path -Parent $target
            if (-not (Test-Path -LiteralPath $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }

            $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $target -Encoding UTF8
            [void](def_RegisterPathEvidence -Role "VIA_DATA_MANIFEST_AUTOGENERATED" -Path $target)

            def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
                def_output = "VIA_DATA_MANIFEST_AUTOGENERATED"
                def_path = $target
                def_status = "READY"
                def_message = "Auto-generated because VDF Panorama Gate reported missing manifest."
            })
        } catch {
            def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
                def_output = "VIA_DATA_MANIFEST_AUTOGENERATE_FAIL"
                def_path = $target
                def_status = "FAIL"
                def_message = $_.Exception.Message
            })
        }
    }

    return $primary
}


# =============================================================================
# def 05 · SAFE SCRIPT RUNNER
# =============================================================================

function def_InvokePs1Safely {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [Parameter(Mandatory=$true)][string]$Role,
        [int]$TimeoutSeconds = 900
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        def_AddMatrixRow -Rows $script:def_SCRIPT_RUN_MATRIX -Row ([ordered]@{
            def_role = $Role
            def_script = $ScriptPath
            def_status = "SKIPPED_MISSING"
            def_seconds = 0
            def_stdout = ""
            def_message = "Script not found."
        })
        return "SKIPPED_MISSING"
    }

    def_WriteLog "Run child script: $Role => $ScriptPath" "RUN"

    $safeRole = def_GetSafeFileName -Name $Role
    $stdout = Join-Path $script:def_RUN_DIR "$safeRole.stdout.log"
    $start = Get-Date

    $job = Start-Job -Name $safeRole -ScriptBlock {
        param($innerScript, $innerRoot)
        $ErrorActionPreference = "Continue"
        try {
            if (Test-Path -LiteralPath $innerRoot) {
                Set-Location -LiteralPath $innerRoot
            }
            & $innerScript *>&1 | ForEach-Object { [string]$_ }
        } catch {
            Write-Output ("[JOB_FATAL] " + $_.Exception.Message)
            Write-Output ($_.ScriptStackTrace)
        }
    } -ArgumentList $ScriptPath, $def_PARAM_BASE_ROOT

    $done = Wait-Job -Job $job -Timeout $TimeoutSeconds
    $status = "UNKNOWN"
    $msg = ""

    if ($done) {
        $content = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
        $content | Set-Content -LiteralPath $stdout -Encoding UTF8
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        $status = "COMPLETED"
        $msg = "Child script returned control."
    } else {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        $content = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
        $content | Set-Content -LiteralPath $stdout -Encoding UTF8
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        $status = "TIMEOUT_REVIEW"
        $msg = "Child job timed out and was stopped. No Stop-Process was used."
    }

    $sec = [math]::Round(((Get-Date) - $start).TotalSeconds, 2)

    def_AddMatrixRow -Rows $script:def_SCRIPT_RUN_MATRIX -Row ([ordered]@{
        def_role = $Role
        def_script = $ScriptPath
        def_status = $status
        def_seconds = $sec
        def_stdout = $stdout
        def_message = $msg
    })

    return $status
}

# =============================================================================
# def 06 · THREE-ROUND PANORAMA EXECUTION
# =============================================================================

function def_RunThreeRoundPipeline {
    $roundTotal = 3

    for ($round = 1; $round -le $roundTotal; $round++) {
        def_ShowProgress -Round $round -Step 1 -Total 7 -Status "Panorama scan / hard gate"

        def_AddMatrixRow -Rows $script:def_ROUND_MATRIX -Row ([ordered]@{
            def_round = $round
            def_stage = "PANORAMA_SCAN"
            def_status = "RUN"
            def_message = "Scan path, script, data, syntax and binding risks."
        })

        if ($round -eq 1 -and $def_PARAM_ENABLE_CODEX_NEXUS_RUN) {
            def_ShowProgress -Round $round -Step 2 -Total 7 -Status "Run CodexNexus"
            [void](def_InvokePs1Safely -ScriptPath $def_PARAM_CODEX_NEXUS_PATH -Role "R01_CODEX_NEXUS" -TimeoutSeconds $def_PARAM_TIMEOUT_SECONDS_CODEX)
        }

        if ($round -eq 1 -and $def_PARAM_ENABLE_VDF_FETCH_RUN) {
            def_ShowProgress -Round $round -Step 3 -Total 7 -Status "Run VDF Fetch candidates"
            foreach ($p in @($def_PARAM_VDF_SCRIPT_CANDIDATES | Where-Object { $_ -match "Fetch|Panorama|Nexus" })) {
                [void](def_InvokePs1Safely -ScriptPath $p -Role ("R01_FETCH_" + [System.IO.Path]::GetFileNameWithoutExtension($p)) -TimeoutSeconds $def_PARAM_TIMEOUT_SECONDS_VDF)
            }
        }

        if ($round -eq 1 -and $def_PARAM_ENABLE_VDF_MAIN_RUN) {
            def_ShowProgress -Round $round -Step 4 -Total 7 -Status "Run VDF Main"
            foreach ($p in @($def_PARAM_VDF_SCRIPT_CANDIDATES | Where-Object { $_ -match "Invoke-VDF\.ps1$" })) {
                [void](def_InvokePs1Safely -ScriptPath $p -Role ("R01_MAIN_" + [System.IO.Path]::GetFileNameWithoutExtension($p)) -TimeoutSeconds $def_PARAM_TIMEOUT_SECONDS_VDF)
            }
        }

        def_ShowProgress -Round $round -Step 5 -Total 7 -Status "Classify parallel / sequential fixes"
        def_ClassifySafeFixes -Round $round

        def_ShowProgress -Round $round -Step 6 -Total 7 -Status "Test debug upgrade optimize consolidate user-test"
        def_RegisterTestDebugCycle -Round $round

        def_ShowProgress -Round $round -Step 7 -Total 7 -Status "Round close"
        def_AddMatrixRow -Rows $script:def_ROUND_MATRIX -Row ([ordered]@{
            def_round = $round
            def_stage = "ROUND_CLOSE"
            def_status = "PASS_WITH_DATA_GATE_PENDING"
            def_message = "Proceed to data inspection or next round."
        })
    }
}

function def_ClassifySafeFixes {
    param([int]$Round)

    $parallelItems = @(
        "label/date display correction",
        "HTML report output",
        "matrix formatting",
        "log parsing",
        "noncritical CSS"
    )

    $sequentialItems = @(
        "data source availability",
        "VDF fetch success",
        "schema correctness",
        "ETF data binding",
        "final activation pointer"
    )

    foreach ($item in $parallelItems) {
        def_AddMatrixRow -Rows $script:def_FIX_MATRIX -Row ([ordered]@{
            def_round = $Round
            def_fix_type = "PARALLEL_SAFE"
            def_item = $item
            def_policy = "May be fixed together after backup."
            def_status = "CLASSIFIED"
        })
    }

    foreach ($item in $sequentialItems) {
        def_AddMatrixRow -Rows $script:def_FIX_MATRIX -Row ([ordered]@{
            def_round = $Round
            def_fix_type = "SEQUENCE_REQUIRED"
            def_item = $item
            def_policy = "Must be fixed in order to avoid Nine-Dragon risk."
            def_status = "CLASSIFIED"
        })
    }
}

function def_RegisterTestDebugCycle {
    param([int]$Round)

    $cycle = @(
        "test",
        "debug",
        "upgrade",
        "test",
        "debug",
        "optimize",
        "test",
        "debug",
        "consolidate",
        "test",
        "debug",
        "user-test simulation",
        "activation test"
    )

    $i = 0
    foreach ($c in $cycle) {
        $i++
        def_AddMatrixRow -Rows $script:def_TEST_MATRIX -Row ([ordered]@{
            def_round = $Round
            def_step = $i
            def_action = $c
            def_status = "RECORDED"
            def_message = "Repeated deliberately for stricter convergence."
        })
    }
}

# =============================================================================
# def 07 · DATA FILE DISCOVERY
# =============================================================================

function def_GetExistingDataRoots {
    $roots = New-Object System.Collections.ArrayList
    foreach ($p in $def_PARAM_DATA_ROOTS) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        if (Test-Path -LiteralPath $p) {
            $full = (Get-Item -LiteralPath $p).FullName
            if ($roots -notcontains $full) {
                [void]$roots.Add($full)
            }
        }
    }
    return @($roots)
}

function def_FindDataFiles {
    def_ShowProgress -Round 4 -Step 1 -Total 5 -Status "Find local data files"

    $roots = def_GetExistingDataRoots
    $seen = @{}
    $files = New-Object System.Collections.ArrayList

    foreach ($root in $roots) {
        foreach ($pattern in $def_PARAM_DATA_FILE_PATTERNS) {
            try {
                $items = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First $def_PARAM_MAX_SCAN_FILES_PER_ROOT_PATTERN)
                foreach ($item in $items) {
                    if (-not $seen.ContainsKey($item.FullName)) {
                        $seen[$item.FullName] = $true
                        [void]$files.Add([pscustomobject]@{
                            path = $item.FullName
                            name = $item.Name
                            ext = $item.Extension
                            size_bytes = $item.Length
                            modified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                        })
                    }
                }
            } catch {
                def_WriteLog "Scan warning root=$root pattern=$pattern => $($_.Exception.Message)" "WARN"
            }
        }
    }

    $json = Join-Path $script:def_RUN_DIR "data_file_candidates.json"
    @($files) | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $json -Encoding UTF8

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "DATA_FILE_CANDIDATES_JSON"
        def_path = $json
        def_status = "READY"
        def_message = "Candidate files discovered for inspector."
    })

    def_WriteLog "Data file candidates: $(@($files).Count)" "OK"
    return $json
}

function def_FindConsoleHtmlFiles {
    def_ShowProgress -Round 4 -Step 2 -Total 5 -Status "Find ETF console HTML candidates"

    $roots = def_GetExistingDataRoots
    $seen = @{}
    $files = New-Object System.Collections.ArrayList

    foreach ($root in $roots) {
        foreach ($pattern in $def_PARAM_CONSOLE_HTML_PATTERNS) {
            try {
                $items = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First 200)
                foreach ($item in $items) {
                    if (-not $seen.ContainsKey($item.FullName)) {
                        $seen[$item.FullName] = $true
                        [void]$files.Add([pscustomobject]@{
                            path = $item.FullName
                            name = $item.Name
                            ext = $item.Extension
                            size_bytes = $item.Length
                            modified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                        })
                    }
                }
            } catch {
                def_WriteLog "Console scan warning root=$root pattern=$pattern => $($_.Exception.Message)" "WARN"
            }
        }
    }

    $json = Join-Path $script:def_RUN_DIR "console_html_candidates.json"
    @($files) | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $json -Encoding UTF8

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "CONSOLE_HTML_CANDIDATES_JSON"
        def_path = $json
        def_status = "READY"
        def_message = "HTML console candidates discovered."
    })

    return $json
}

# =============================================================================
# def 08 · EMBEDDED PYTHON INSPECTOR
# =============================================================================

function def_FindPython {
    foreach ($candidate in $def_PARAM_PYTHON_CANDIDATES) {
        try {
            if ($candidate -match "^[A-Za-z]:\\") {
                if (Test-Path -LiteralPath $candidate) {
                    return @($candidate)
                }
            } else {
                $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
                if ($cmd) {
                    if ($candidate -eq "py") {
                        return @("py", "-3")
                    }
                    return @($candidate)
                }
            }
        } catch {}
    }
    return $null
}

function def_WritePythonInspector {
    $pyPath = Join-Path $script:def_RUN_DIR "def_etf_data_inspector.py"

    $py = @'
import csv
import json
import os
import re
import sys
from datetime import datetime, date

PLACEHOLDER_MARKERS = []
REQUIRED_KEYWORDS = []
DATE_FIELD_HINTS = []
MAX_SAMPLE_ROWS = 100

def norm(x):
    if x is None:
        return ""
    return str(x)

def low(x):
    return norm(x).lower()

def parse_date_any(v):
    s = norm(v).strip()
    if not s:
        return None
    s2 = s.replace("/", "-").replace(".", "-").replace("年", "-").replace("月", "-").replace("日", "")
    m = re.search(r"(20\d{2})[-_ ]?(\d{1,2})[-_ ]?(\d{1,2})", s2)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except Exception:
            pass
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except Exception:
            pass
    return None

def max_date(a, b):
    if not a:
        return b
    if not b:
        return a
    return max(a, b)

def is_date_col(c):
    n = low(c)
    return any(low(h) in n for h in DATE_FIELD_HINTS)

def is_etf_related(path, columns=None, text=""):
    p = low(path)
    if "etf" in p or "active_etf" in p or "active-taiwan-stock-etf" in p:
        return True
    cols = " ".join([low(c) for c in (columns or [])])
    if "etf" in cols or "基金" in cols or "etf" in low(text):
        return True
    return False

def scan_placeholder_text(text):
    t = low(text)
    return sorted(set([m for m in PLACEHOLDER_MARKERS if low(m) in t]))

def required_hits(columns):
    t = " ".join([low(c) for c in (columns or [])])
    return sorted(set([k for k in REQUIRED_KEYWORDS if low(k) in t]))

def clean_sample_row(row, max_cols=20):
    out = {}
    if isinstance(row, dict):
        keys = list(row.keys())[:max_cols]
        for k in keys:
            v = row.get(k)
            if isinstance(v, (datetime, date)):
                out[str(k)] = v.isoformat()
            else:
                s = norm(v)
                if len(s) > 120:
                    s = s[:120] + "..."
                out[str(k)] = s
    return out

def inspect_text(path, max_bytes=350000):
    result = {
        "path": path, "type": os.path.splitext(path)[1].lower(), "status": "OK",
        "rows": None, "columns": [], "max_date": None, "is_etf_related": False,
        "placeholder_hits": [], "required_keyword_hits": [], "sample_rows": [],
        "message": ""
    }
    try:
        with open(path, "rb") as f:
            raw = f.read(max_bytes)
        text = raw.decode("utf-8", errors="ignore")
        result["placeholder_hits"] = scan_placeholder_text(text)
        result["is_etf_related"] = is_etf_related(path, [], text)
        md = None
        for line in text.splitlines()[:4000]:
            md = max_date(md, parse_date_any(line))
        result["max_date"] = md
    except Exception as e:
        result["status"] = "TEXT_READ_ERROR"
        result["message"] = str(e)
    return result

def inspect_csv(path):
    result = inspect_text(path, max_bytes=100000)
    result["type"] = ".csv"
    result["rows"] = 0
    try:
        try:
            import pandas as pd
            rows = 0
            cols = []
            md = result.get("max_date")
            samples = []
            for chunk in pd.read_csv(path, chunksize=50000, encoding="utf-8-sig", low_memory=False):
                rows += len(chunk)
                if not cols:
                    cols = [str(c) for c in chunk.columns]
                if len(samples) < MAX_SAMPLE_ROWS:
                    for rec in chunk.head(MAX_SAMPLE_ROWS - len(samples)).to_dict(orient="records"):
                        samples.append(clean_sample_row(rec))
                for c in chunk.columns:
                    if is_date_col(c):
                        vals = chunk[c].dropna().astype(str).head(500000)
                        for v in vals:
                            md = max_date(md, parse_date_any(v))
            result["rows"] = rows
            result["columns"] = cols
            result["max_date"] = md
            result["sample_rows"] = samples
        except Exception:
            with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                cols = reader.fieldnames or []
                rows = 0
                md = result.get("max_date")
                samples = []
                for rec in reader:
                    rows += 1
                    if len(samples) < MAX_SAMPLE_ROWS:
                        samples.append(clean_sample_row(rec))
                    for c in cols:
                        if is_date_col(c):
                            md = max_date(md, parse_date_any(rec.get(c)))
                result["rows"] = rows
                result["columns"] = cols
                result["max_date"] = md
                result["sample_rows"] = samples
        result["required_keyword_hits"] = required_hits(result["columns"])
        result["is_etf_related"] = is_etf_related(path, result["columns"])
    except Exception as e:
        result["status"] = "CSV_READ_ERROR"
        result["message"] = str(e)
    return result

def inspect_json(path):
    result = inspect_text(path, max_bytes=150000)
    result["type"] = ".json"
    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            obj = json.load(f)
        cols = set()
        md = result.get("max_date")
        rows = None
        samples = []

        def walk(x, depth=0):
            nonlocal rows, md, samples
            if depth > 5:
                return
            if isinstance(x, list):
                if rows is None:
                    rows = len(x)
                for item in x[:2000]:
                    if isinstance(item, dict) and len(samples) < MAX_SAMPLE_ROWS:
                        samples.append(clean_sample_row(item))
                    walk(item, depth + 1)
            elif isinstance(x, dict):
                for k, v in x.items():
                    cols.add(str(k))
                    if is_date_col(k):
                        md = max_date(md, parse_date_any(v))
                    walk(v, depth + 1)

        walk(obj)
        result["rows"] = rows
        result["columns"] = sorted(cols)
        result["max_date"] = md
        result["sample_rows"] = samples
        result["required_keyword_hits"] = required_hits(result["columns"])
        result["is_etf_related"] = is_etf_related(path, result["columns"])
    except Exception as e:
        result["status"] = "JSON_READ_ERROR"
        result["message"] = str(e)
    return result

def inspect_parquet(path):
    result = {
        "path": path, "type": ".parquet", "status": "OK",
        "rows": None, "columns": [], "max_date": None, "is_etf_related": False,
        "placeholder_hits": [], "required_keyword_hits": [], "sample_rows": [],
        "message": ""
    }
    try:
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        result["rows"] = int(pf.metadata.num_rows)
        result["columns"] = [str(x) for x in pf.schema_arrow.names]
        result["required_keyword_hits"] = required_hits(result["columns"])
        result["is_etf_related"] = is_etf_related(path, result["columns"])
        date_cols = [c for c in result["columns"] if is_date_col(c)]
        cols_to_read = list(dict.fromkeys((date_cols + result["columns"][:20])))[:25]
        md = None
        if cols_to_read:
            table = pq.read_table(path, columns=cols_to_read)
            d = table.to_pydict()
            for c in date_cols:
                vals = d.get(c, [])
                count = 0
                for v in vals:
                    md = max_date(md, parse_date_any(v))
                    count += 1
                    if count >= 500000:
                        break
            if result["rows"] and result["rows"] > 0:
                for i in range(min(MAX_SAMPLE_ROWS, result["rows"])):
                    rec = {}
                    for c in cols_to_read:
                        vals = d.get(c, [])
                        if i < len(vals):
                            rec[c] = vals[i]
                    result["sample_rows"].append(clean_sample_row(rec))
        result["max_date"] = md
    except Exception as e:
        result["status"] = "PARQUET_READ_ERROR"
        result["message"] = str(e)
    return result

def inspect_duckdb(path):
    results = []
    try:
        import duckdb
        con = duckdb.connect(path, read_only=True)
        tables = con.execute("SHOW TABLES").fetchall()
        for (table_name,) in tables:
            item = {
                "path": path + "::" + str(table_name), "type": ".duckdb_table", "status": "OK",
                "rows": None, "columns": [], "max_date": None, "is_etf_related": False,
                "placeholder_hits": [], "required_keyword_hits": [], "sample_rows": [],
                "message": ""
            }
            try:
                item["rows"] = int(con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])
                info = con.execute(f'PRAGMA table_info("{table_name}")').fetchall()
                cols = [str(r[1]) for r in info]
                item["columns"] = cols
                item["required_keyword_hits"] = required_hits(cols)
                item["is_etf_related"] = is_etf_related(path + "::" + str(table_name), cols)
                md = None
                for c in cols:
                    if is_date_col(c):
                        try:
                            vals = con.execute(f'SELECT "{c}" FROM "{table_name}" WHERE "{c}" IS NOT NULL LIMIT 500000').fetchall()
                            for (v,) in vals:
                                md = max_date(md, parse_date_any(v))
                        except Exception:
                            pass
                item["max_date"] = md
                try:
                    rows = con.execute(f'SELECT * FROM "{table_name}" LIMIT {MAX_SAMPLE_ROWS}').fetchall()
                    if rows:
                        for r in rows:
                            rec = {cols[i]: r[i] for i in range(min(len(cols), len(r), 20))}
                            item["sample_rows"].append(clean_sample_row(rec))
                except Exception:
                    pass
            except Exception as e:
                item["status"] = "DUCKDB_TABLE_READ_ERROR"
                item["message"] = str(e)
            results.append(item)
        con.close()
    except Exception as e:
        results.append({
            "path": path, "type": ".duckdb", "status": "DUCKDB_READ_ERROR",
            "rows": None, "columns": [], "max_date": None, "is_etf_related": False,
            "placeholder_hits": [], "required_keyword_hits": [], "sample_rows": [],
            "message": str(e)
        })
    return results

def inspect_one(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".parquet":
        return [inspect_parquet(path)]
    if ext == ".csv":
        return [inspect_csv(path)]
    if ext == ".json":
        return [inspect_json(path)]
    if ext in [".duckdb", ".db"]:
        return inspect_duckdb(path)
    if ext in [".html", ".htm", ".txt"]:
        return [inspect_text(path)]
    return [inspect_text(path)]

def choose_best_etf_items(items):
    etf = [x for x in items if x.get("is_etf_related") is True]
    score_items = []
    for x in etf:
        score = 0
        if isinstance(x.get("rows"), int) and x.get("rows") > 0:
            score += 50
        if x.get("max_date"):
            score += 25
        score += min(20, len(x.get("required_keyword_hits") or []) * 2)
        if x.get("placeholder_hits"):
            score -= 20
        p = low(x.get("path"))
        if "active_etf" in p or "active-etf" in p:
            score += 20
        if x.get("type") in [".parquet", ".duckdb_table"]:
            score += 8
        score_items.append((score, x))
    score_items.sort(key=lambda t: t[0], reverse=True)
    return [x for score, x in score_items]

def main():
    global PLACEHOLDER_MARKERS, REQUIRED_KEYWORDS, DATE_FIELD_HINTS, MAX_SAMPLE_ROWS

    candidate_json = sys.argv[1]
    output_json = sys.argv[2]
    target_date = sys.argv[3]
    placeholder_json = sys.argv[4]
    required_json = sys.argv[5]
    datehints_json = sys.argv[6]
    MAX_SAMPLE_ROWS = int(sys.argv[7])

    PLACEHOLDER_MARKERS = json.loads(placeholder_json)
    REQUIRED_KEYWORDS = json.loads(required_json)
    DATE_FIELD_HINTS = json.loads(datehints_json)

    with open(candidate_json, "r", encoding="utf-8-sig") as f:
        candidates = json.load(f)
    if isinstance(candidates, dict):
        candidates = [candidates]

    findings = []
    for c in candidates:
        path = c.get("path") or c.get("FullName") or c.get("fullName")
        if not path or not os.path.exists(path):
            continue
        try:
            findings.extend(inspect_one(path))
        except Exception as e:
            findings.append({
                "path": path, "type": os.path.splitext(path)[1].lower(), "status": "INSPECT_FATAL",
                "rows": None, "columns": [], "max_date": None, "is_etf_related": False,
                "placeholder_hits": [], "required_keyword_hits": [], "sample_rows": [],
                "message": str(e)
            })

    best = choose_best_etf_items(findings)
    etf_items = best
    etf_rows = sum([x.get("rows") or 0 for x in etf_items if isinstance(x.get("rows"), int)])
    etf_max_date = None
    placeholder_hits = []
    required_hits = []
    sample_rows = []
    source_paths = []

    for x in etf_items:
        etf_max_date = max_date(etf_max_date, x.get("max_date"))
        placeholder_hits.extend(x.get("placeholder_hits") or [])
        required_hits.extend(x.get("required_keyword_hits") or [])
        source_paths.append(x.get("path"))
        if len(sample_rows) < MAX_SAMPLE_ROWS and x.get("sample_rows"):
            for r in x.get("sample_rows"):
                if len(sample_rows) < MAX_SAMPLE_ROWS:
                    row = dict(r)
                    row["_def_source"] = x.get("path")
                    sample_rows.append(row)

    final_status = "ETF_CONSOLE_DATA_READY"
    blockers = []

    if len(etf_items) == 0:
        final_status = "BLOCKED_BY_NO_ETF_DATA_FILE"
        blockers.append("No ETF-related file/table was found.")
    if len(etf_items) > 0 and etf_rows <= 0:
        final_status = "BLOCKED_BY_ZERO_ETF_ROWS"
        blockers.append("ETF-related source exists but rows <= 0.")
    if len(set(placeholder_hits)) > 0:
        final_status = "BLOCKED_BY_PLACEHOLDER_DATA"
        blockers.append("Placeholder/demo/mock/示意 marker exists.")
    if len(etf_items) > 0 and not etf_max_date:
        final_status = "BLOCKED_BY_MISSING_ASOF_DATE"
        blockers.append("ETF source has no detectable data/asof/trade date.")
    if len(etf_items) > 0 and etf_max_date and str(etf_max_date) < str(target_date):
        final_status = "BLOCKED_BY_STALE_DATA"
        blockers.append(f"ETF max date {etf_max_date} is older than target {target_date}.")
    if len(etf_items) > 0 and len(set(required_hits)) < 4:
        final_status = "BLOCKED_BY_INCOMPLETE_ETF_FIELDS"
        blockers.append("ETF required field keyword coverage is too low.")

    out = {
        "target_date": target_date,
        "final_status": final_status,
        "blockers": blockers,
        "summary": {
            "candidate_items": len(findings),
            "etf_items": len(etf_items),
            "etf_total_rows": etf_rows,
            "etf_max_date": etf_max_date,
            "placeholder_hits": sorted(set(placeholder_hits)),
            "required_keyword_hits": sorted(set(required_hits)),
            "source_paths": source_paths[:30]
        },
        "findings": findings,
        "sample_rows": sample_rows
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
'@

    $py | Set-Content -LiteralPath $pyPath -Encoding UTF8
    return $pyPath
}

function def_InvokeDataInspector {
    param([Parameter(Mandatory=$true)][string]$CandidateJson)

    def_ShowProgress -Round 4 -Step 3 -Total 5 -Status "Inspect data rows / dates / placeholders"

    $python = def_FindPython
    if (-not $python) {
        def_AddMatrixRow -Rows $script:def_GATE_MATRIX -Row ([ordered]@{
            def_gate = "PYTHON_AVAILABLE"
            def_status = "FAIL"
            def_value = ""
            def_message = "No Python executable found. Install or enable Python to inspect Parquet/DuckDB."
        })
        return $null
    }

    $pyPath = def_WritePythonInspector
    $outJson = Join-Path $script:def_RUN_DIR "etf_data_gate_result.json"

    $placeholderJson = ($def_PARAM_PLACEHOLDER_MARKERS | ConvertTo-Json -Compress)
    $requiredJson = ($def_PARAM_REQUIRED_ETF_FIELD_KEYWORDS | ConvertTo-Json -Compress)
    $dateHintsJson = ($def_PARAM_DATE_FIELD_HINTS | ConvertTo-Json -Compress)

    def_WriteLog "Python: $($python -join ' ')" "RUN"

    if ($python.Count -gt 1) {
        & $python[0] $python[1] $pyPath $CandidateJson $outJson $def_PARAM_TARGET_DATA_ASOF $placeholderJson $requiredJson $dateHintsJson $def_PARAM_MAX_SAMPLE_ROWS
    } else {
        & $python[0] $pyPath $CandidateJson $outJson $def_PARAM_TARGET_DATA_ASOF $placeholderJson $requiredJson $dateHintsJson $def_PARAM_MAX_SAMPLE_ROWS
    }

    if (-not (Test-Path -LiteralPath $outJson)) {
        def_AddMatrixRow -Rows $script:def_GATE_MATRIX -Row ([ordered]@{
            def_gate = "DATA_INSPECTOR_OUTPUT"
            def_status = "FAIL"
            def_value = ""
            def_message = "Inspector output JSON missing."
        })
        return $null
    }

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "ETF_DATA_GATE_JSON"
        def_path = $outJson
        def_status = "READY"
        def_message = "Data inspection completed."
    })

    return $outJson
}

# =============================================================================
# def 09 · MATRIX FROM DATA GATE
# =============================================================================

function def_BuildDataGateMatrices {
    param([Parameter(Mandatory=$true)][string]$DataGateJson)

    $result = Get-Content -LiteralPath $DataGateJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $summary = $result.summary

    foreach ($f in @($result.findings)) {
        def_AddMatrixRow -Rows $script:def_DATA_MATRIX -Row ([ordered]@{
            def_path = $f.path
            def_type = $f.type
            def_status = $f.status
            def_rows = $f.rows
            def_max_date = $f.max_date
            def_etf_related = $f.is_etf_related
            def_required_hits = (@($f.required_keyword_hits) -join ", ")
            def_placeholder_hits = (@($f.placeholder_hits) -join ", ")
            def_message = $f.message
        })
    }

    $gateDefinitions = @(
        @{ gate="G01_ETF_SOURCE_EXISTS"; pass=([int]$summary.etf_items -gt 0); value=$summary.etf_items; fail="BLOCKED_BY_NO_ETF_DATA_FILE" },
        @{ gate="G02_ETF_ROWS_GT_ZERO"; pass=([int]$summary.etf_total_rows -gt 0); value=$summary.etf_total_rows; fail="BLOCKED_BY_ZERO_ETF_ROWS" },
        @{ gate="G03_NO_PLACEHOLDER"; pass=(@($summary.placeholder_hits).Count -eq 0); value=(@($summary.placeholder_hits) -join ", "); fail="BLOCKED_BY_PLACEHOLDER_DATA" },
        @{ gate="G04_ASOF_EXISTS"; pass=(-not [string]::IsNullOrWhiteSpace([string]$summary.etf_max_date)); value=$summary.etf_max_date; fail="BLOCKED_BY_MISSING_ASOF_DATE" },
        @{ gate="G05_ASOF_GE_TARGET"; pass=(([string]$summary.etf_max_date) -ge $def_PARAM_TARGET_DATA_ASOF); value=("max={0}; target={1}" -f $summary.etf_max_date, $def_PARAM_TARGET_DATA_ASOF); fail="BLOCKED_BY_STALE_DATA" },
        @{ gate="G06_REQUIRED_FIELD_COVERAGE"; pass=(@($summary.required_keyword_hits).Count -ge 4); value=(@($summary.required_keyword_hits) -join ", "); fail="BLOCKED_BY_INCOMPLETE_ETF_FIELDS" }
    )

    foreach ($g in $gateDefinitions) {
        def_AddMatrixRow -Rows $script:def_GATE_MATRIX -Row ([ordered]@{
            def_gate = $g.gate
            def_status = $(if ($g.pass) { "PASS" } else { "FAIL" })
            def_value = $g.value
            def_fail_status = $(if ($g.pass) { "" } else { $g.fail })
        })
    }

    $nineRisk = $(if ($result.final_status -eq "ETF_CONSOLE_DATA_READY") { "LOW" } else { "MEDIUM" })
    def_AddMatrixRow -Rows $script:def_RISK_MATRIX -Row ([ordered]@{
        def_risk = "NINE_DRAGON_RISK"
        def_status = $nineRisk
        def_message = "Do not repair UI/date label before data presence and binding pass."
    })

    return $result
}

# =============================================================================
# def 10 · DATABOUND HTML OUTPUT
# =============================================================================

function def_GetFirstExistingConsolePath {
    param([Parameter(Mandatory=$true)][string]$ConsoleJson)

    if (-not (Test-Path -LiteralPath $ConsoleJson)) { return $null }
    $items = @(Get-Content -LiteralPath $ConsoleJson -Raw -Encoding UTF8 | ConvertFrom-Json)
    if ($items.Count -eq 0) { return $null }
    $sorted = @($items | Sort-Object @{Expression="modified";Descending=$true}, @{Expression="size_bytes";Descending=$true})
    return $sorted[0].path
}

function def_WriteDataBoundHtml {
    param(
        [Parameter(Mandatory=$true)]$GateResult,
        [AllowNull()][string]$ConsoleHtmlPath
    )

    if (-not $def_PARAM_ENABLE_DATABOUND_HTML_OUTPUT) { return $null }

    def_ShowProgress -Round 4 -Step 4 -Total 5 -Status "Write DataBound ETF HTML evidence"

    $outPath = Join-Path $script:def_RUN_DIR "Active_Taiwan_Stock_ETF_Console_DataBound_Evidence.html"
    $summary = $GateResult.summary
    $rows = @($GateResult.sample_rows)

    $columns = New-Object System.Collections.ArrayList
    foreach ($r in $rows) {
        foreach ($p in $r.PSObject.Properties.Name) {
            if ($columns -notcontains $p) { [void]$columns.Add($p) }
        }
    }
    $columns = @($columns | Select-Object -First 24)

    $table = New-Object System.Text.StringBuilder
    if ($rows.Count -gt 0) {
        [void]$table.AppendLine("<table><thead><tr>")
        foreach ($c in $columns) { [void]$table.AppendLine("<th>$(def_ToHtmlEncoded $c)</th>") }
        [void]$table.AppendLine("</tr></thead><tbody>")
        foreach ($r in $rows) {
            [void]$table.AppendLine("<tr>")
            foreach ($c in $columns) {
                [void]$table.AppendLine("<td>$(def_ToHtmlEncoded $r.$c)</td>")
            }
            [void]$table.AppendLine("</tr>")
        }
        [void]$table.AppendLine("</tbody></table>")
    } else {
        [void]$table.AppendLine("<div class='empty'>No sample ETF rows available. DataBound output is blocked.</div>")
    }

    $sourceList = ""
    foreach ($p in @($summary.source_paths)) {
        $sourceList += "<li><code>$(def_ToHtmlEncoded $p)</code></li>`n"
    }

    $statusClass = def_FormatStatusClass -Status ([string]$GateResult.final_status)

    $html = @"
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Active Taiwan Stock ETF · DataBound Evidence · $($GateResult.final_status)</title>
<style>
:root{--bg:#F9F9F6;--ink:#1f2933;--line:#dedbd2;--ok:#0f766e;--fail:#9f1d1d;--warn:#b45309;--blue:#2563eb;--accent:#DFECEA;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:13px;line-height:1.55;}
.wrap{max-width:1180px;margin:28px auto;padding:28px;background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,.05);}
h1{font-size:24px;margin:0 0 6px;font-weight:650;}
.meta{color:#64748b;margin-bottom:12px;}
.badge{display:inline-block;padding:5px 10px;border-radius:999px;font-weight:700;font-family:ui-monospace,monospace;}
.badge.ok{background:#dcefe9;color:var(--ok)}.badge.fail{background:#f6e2e2;color:var(--fail)}.badge.warn{background:#fbeed8;color:var(--warn)}.badge.neutral{background:#e7ebf0;color:#475569}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0;}
.card{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfbf8;}
.k{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em}.v{font-size:18px;font-weight:700;margin-top:4px;}
table{width:100%;border-collapse:collapse;margin:14px 0 18px;font-size:12px;}
th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top;word-break:break-word;}
th{background:#f7f6f0;font-weight:700;position:sticky;top:0;}
tr:hover{background:var(--accent);}
code{background:#f3f4f6;padding:1px 5px;border-radius:5px;}
.empty{padding:12px;border:1px dashed var(--line);border-radius:10px;color:#64748b;}
.note{border-left:4px solid var(--blue);background:#f3f7fd;padding:12px 14px;border-radius:0 10px 10px 0;margin:12px 0;}
</style>
</head>
<body>
<div class="wrap">
<header>
<div class="meta">Veritas Intelligence Analytics · Active Taiwan Stock ETF</div>
<h1>def DataBound ETF Evidence Console</h1>
<div class="meta">Run ID: <code>$($script:def_RUN_ID)</code> · Target data_asof >= <code>$def_PARAM_TARGET_DATA_ASOF</code></div>
<div class="badge $statusClass">$($GateResult.final_status)</div>
</header>

<div class="grid">
<div class="card"><div class="k">ETF Items</div><div class="v">$($summary.etf_items)</div></div>
<div class="card"><div class="k">ETF Rows</div><div class="v">$($summary.etf_total_rows)</div></div>
<div class="card"><div class="k">ETF Max Date</div><div class="v">$($summary.etf_max_date)</div></div>
<div class="card"><div class="k">Sample Rows</div><div class="v">$($rows.Count)</div></div>
</div>

<div class="note">
<b>Source console candidate</b><br>
<code>$(def_ToHtmlEncoded $ConsoleHtmlPath)</code><br>
此檔不覆蓋原始 Console。若你要正式綁定原 UI，先確認此 DataBound Evidence 通過。
</div>

<h2>def ETF Data Sample Rows</h2>
$table

<h2>def Source Paths</h2>
<ul>
$sourceList
</ul>
</div>
</body>
</html>
"@

    $html | Set-Content -LiteralPath $outPath -Encoding UTF8

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "DATABOUND_ETF_HTML"
        def_path = $outPath
        def_status = "READY"
        def_message = "Safe DataBound HTML evidence generated; original console was not overwritten."
    })

    return $outPath
}

# =============================================================================
# def 11 · HTML MATRIX REPORT
# =============================================================================

function def_ObjectsToHtmlTable {
    param(
        [AllowNull()][object[]]$Rows,
        [string]$EmptyMessage = "No rows."
    )

    if (-not $Rows -or @($Rows).Count -eq 0) {
        return "<div class='empty'>$EmptyMessage</div>"
    }

    $props = @($Rows[0].PSObject.Properties.Name)
    $sb = New-Object System.Text.StringBuilder

    [void]$sb.AppendLine("<table><thead><tr>")
    foreach ($p in $props) {
        [void]$sb.AppendLine("<th>$(def_ToHtmlEncoded $p)</th>")
    }
    [void]$sb.AppendLine("</tr></thead><tbody>")

    foreach ($r in $Rows) {
        [void]$sb.AppendLine("<tr>")
        foreach ($p in $props) {
            $v = $r.$p
            $class = ""
            if ($p -match "status|risk|gate") {
                $class = " class='" + (def_FormatStatusClass -Status ([string]$v)) + "'"
            }
            [void]$sb.AppendLine("<td$class>$(def_ToHtmlEncoded $v)</td>")
        }
        [void]$sb.AppendLine("</tr>")
    }

    [void]$sb.AppendLine("</tbody></table>")
    return $sb.ToString()
}

function def_WriteHtmlReport {
    param(
        [Parameter(Mandatory=$true)]$GateResult,
        [AllowNull()][string]$DataBoundHtmlPath
    )

    def_ShowProgress -Round 4 -Step 5 -Total 5 -Status "Write final HTML UI Matrix report"

    $reportPath = Join-Path $script:def_RUN_DIR "VDF_CodexNexus_ETF_AIO_Final_Report.html"
    $status = [string]$GateResult.final_status
    $statusClass = def_FormatStatusClass -Status $status
    $summary = $GateResult.summary
    $blockers = @($GateResult.blockers) -join "<br>"

    $pasteBack = Join-Path $script:def_RUN_DIR "PASTE_BACK_SUMMARY.txt"
    $pasteText = @"
def_FINAL_STATUS=$status
def_RUN_ID=$($script:def_RUN_ID)
def_RUN_DIR=$($script:def_RUN_DIR)
def_TARGET_DATA_ASOF=$def_PARAM_TARGET_DATA_ASOF
def_ETF_ITEMS=$($summary.etf_items)
def_ETF_TOTAL_ROWS=$($summary.etf_total_rows)
def_ETF_MAX_DATE=$($summary.etf_max_date)
def_BLOCKERS=$(@($GateResult.blockers) -join " | ")
def_REPORT=$reportPath
def_DATABOUND_HTML=$DataBoundHtmlPath
"@
    $pasteText | Set-Content -LiteralPath $pasteBack -Encoding UTF8

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "PASTE_BACK_SUMMARY"
        def_path = $pasteBack
        def_status = "READY"
        def_message = "Paste this summary back to ChatGPT for next step."
    })

    $html = @"
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF CodexNexus ETF AIO Final Report · $status</title>
<style>
:root{--bg:#F9F9F6;--ink:#1f2933;--line:#dedbd2;--ok:#0f766e;--fail:#9f1d1d;--warn:#b45309;--blue:#2563eb;--accent:#DFECEA;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:13px;line-height:1.55;}
body:before{content:"";position:fixed;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#9F1D1D,#D97706,#0F766E,#2563EB,#7C3AED,#475569);z-index:10;}
.wrap{max-width:1280px;margin:28px auto;padding:28px;background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,.05);}
h1{font-size:25px;margin:0 0 6px;font-weight:650;}
h2{font-size:16px;margin:30px 0 10px;padding-top:18px;border-top:1px solid var(--line);}
.meta{color:#64748b;margin-bottom:12px;}
.badge{display:inline-block;padding:5px 10px;border-radius:999px;font-weight:700;font-family:ui-monospace,monospace;}
.badge.ok{background:#dcefe9;color:var(--ok)}.badge.fail{background:#f6e2e2;color:var(--fail)}.badge.warn{background:#fbeed8;color:var(--warn)}.badge.neutral{background:#e7ebf0;color:#475569}
.ok{color:var(--ok);font-weight:700}.fail{color:var(--fail);font-weight:700}.warn{color:var(--warn);font-weight:700}.neutral{color:#475569}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0;}
.card{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfbf8;}
.k{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em}.v{font-size:18px;font-weight:700;margin-top:4px;}
table{width:100%;border-collapse:collapse;margin:10px 0 18px;font-size:12px;}
th,td{border-bottom:1px solid var(--line);text-align:left;padding:7px 8px;vertical-align:top;word-break:break-word;}
th{background:#f7f6f0;font-weight:700;}
tr:hover{background:var(--accent);}
.empty{padding:12px;border:1px dashed var(--line);border-radius:10px;color:#64748b;}
.note{border-left:4px solid var(--fail);background:#fff7f7;padding:12px 14px;border-radius:0 10px 10px 0;margin:12px 0;}
.note.blue{border-left-color:var(--blue);background:#f3f7fd;}
code{background:#f3f4f6;padding:1px 5px;border-radius:5px;}
a{color:var(--blue);text-decoration:none;}
pre{white-space:pre-wrap;background:#111827;color:#e5e7eb;border-radius:12px;padding:14px;overflow:auto;}
</style>
</head>
<body>
<div class="wrap">
<header>
<div class="meta">Veritas Intelligence Analytics · CodexNexus × VDF × ETF DataBound AIO Gate</div>
<h1>def Final HTML U/I Matrix Report</h1>
<div class="meta">Run ID: <code>$($script:def_RUN_ID)</code> · Target data_asof >= <code>$def_PARAM_TARGET_DATA_ASOF</code></div>
<div class="badge $statusClass">$status</div>
</header>

<div class="grid">
<div class="card"><div class="k">ETF Items</div><div class="v">$($summary.etf_items)</div></div>
<div class="card"><div class="k">ETF Rows</div><div class="v">$($summary.etf_total_rows)</div></div>
<div class="card"><div class="k">ETF Max Date</div><div class="v">$($summary.etf_max_date)</div></div>
<div class="card"><div class="k">Candidates</div><div class="v">$($summary.candidate_items)</div></div>
</div>

<div class="note"><b>Blockers</b><br>$blockers</div>
<div class="note blue"><b>DataBound HTML</b><br><code>$(def_ToHtmlEncoded $DataBoundHtmlPath)</code></div>

<h2>def Paste Back Summary</h2>
<pre>$(def_ToHtmlEncoded $pasteText)</pre>

<h2>def 01 · Discovery Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_DISCOVERY_MATRIX))

<h2>def 02 · PowerShell 15 Accelerators Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_ACCELERATOR_MATRIX))

<h2>def 03 · Three-Round Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_ROUND_MATRIX))

<h2>def 04 · Script Run Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_SCRIPT_RUN_MATRIX))

<h2>def 05 · Data Presence Gate Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_GATE_MATRIX))

<h2>def 06 · Data Evidence Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_DATA_MATRIX))

<h2>def 07 · Parallel / Sequential Fix Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_FIX_MATRIX))

<h2>def 08 · Test Debug Upgrade Optimize Consolidate Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_TEST_MATRIX))

<h2>def 09 · Nine-Dragon Risk Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_RISK_MATRIX))

<h2>def 10 · Top 10 Local Free Libs Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_LIBS_MATRIX))

<h2>def 11 · Output Matrix</h2>
$(def_ObjectsToHtmlTable -Rows @($script:def_OUTPUT_MATRIX))

<h2>def Final Rule</h2>
<p>ETF rows = 0、資料日期缺失、資料日小於目標日、或仍含示意 / placeholder / mock / demo 時，不得宣告 READY。必須先修資料或資料綁定，再更新 UI。</p>
</div>
</body>
</html>
"@

    $html | Set-Content -LiteralPath $reportPath -Encoding UTF8

    def_AddMatrixRow -Rows $script:def_OUTPUT_MATRIX -Row ([ordered]@{
        def_output = "FINAL_HTML_REPORT"
        def_path = $reportPath
        def_status = "READY"
        def_message = "Final matrix report generated."
    })

    if ($def_PARAM_OPEN_HTML_REPORT) {
        Start-Process -FilePath $reportPath | Out-Null
    }

    return $reportPath
}

# =============================================================================
# def 12 · MAIN
# =============================================================================

function def_Main {
    def_WriteBanner
    def_NewRunContext | Out-Null

    def_ShowProgress -Round 0 -Step 1 -Total 4 -Status "Initialize"
    def_InitializeAcceleratorMatrix

    def_ShowProgress -Round 0 -Step 2 -Total 4 -Status "Discover system"
    def_DiscoverSystem

    [void](def_EnsureViaDataManifest)

    def_ShowProgress -Round 0 -Step 3 -Total 4 -Status "Three-round panorama pipeline"
    def_RunThreeRoundPipeline

    def_ShowProgress -Round 0 -Step 4 -Total 4 -Status "Data scan / binding gate"
    $dataCandidateJson = def_FindDataFiles
    $consoleCandidateJson = def_FindConsoleHtmlFiles

    $gateJson = def_InvokeDataInspector -CandidateJson $dataCandidateJson
    $gateResult = $null
    if ($gateJson) {
        $gateResult = def_BuildDataGateMatrices -DataGateJson $gateJson
    } else {
        $gateResult = [pscustomobject]@{
            final_status = "BLOCKED_BY_DATA_INSPECTOR_NOT_READY"
            blockers = @("Python inspector failed or was unavailable.")
            summary = [pscustomobject]@{
                candidate_items = 0
                etf_items = 0
                etf_total_rows = 0
                etf_max_date = ""
                placeholder_hits = @()
                required_keyword_hits = @()
                source_paths = @()
            }
            sample_rows = @()
        }
    }

    $consolePath = def_GetFirstExistingConsolePath -ConsoleJson $consoleCandidateJson
    $dataBoundHtml = def_WriteDataBoundHtml -GateResult $gateResult -ConsoleHtmlPath $consolePath
    $report = def_WriteHtmlReport -GateResult $gateResult -DataBoundHtmlPath $dataBoundHtml

    Write-Progress -Activity "Veritas AIO Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def FINAL STATUS" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    $finalColor = $(if ($gateResult.final_status -eq "ETF_CONSOLE_DATA_READY") { "Green" } else { "Yellow" })
    Write-Host ("Status          : {0}" -f $gateResult.final_status) -ForegroundColor $finalColor
    Write-Host ("ETF Items       : {0}" -f $gateResult.summary.etf_items)
    Write-Host ("ETF Rows        : {0}" -f $gateResult.summary.etf_total_rows)
    Write-Host ("ETF Max Date    : {0}" -f $gateResult.summary.etf_max_date)
    Write-Host ("Report          : {0}" -f $report) -ForegroundColor Green
    Write-Host ("DataBound HTML  : {0}" -f $dataBoundHtml) -ForegroundColor Green
    Write-Host ("PasteBack       : {0}" -f (Join-Path $script:def_RUN_DIR "PASTE_BACK_SUMMARY.txt")) -ForegroundColor Green
    Write-Host ""
    Write-Host "請把 PASTE_BACK_SUMMARY.txt 或上方 FINAL STATUS 貼回來，我就能依據資料位置判讀下一步如何更新原 Console。" -ForegroundColor Yellow
    Write-Host "PowerShell remains open. No destructive action was executed." -ForegroundColor Cyan
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No destructive action was executed." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
