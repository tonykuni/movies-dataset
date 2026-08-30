#requires -Version 7.0
param(
    [string]$SupportiveModulesRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$ReadmePath = "",
    [string]$NexusCorePath = "",
    [string]$PolyglotPath = "",
    [string]$OutputRoot = "",
    [int]$MaxRounds = 3,
    [switch]$OpenReport,
    [switch]$RunSandboxSelfTest,
    [switch]$RegisterLauncher,
    [switch]$SelfTest,
    [switch]$NoBrowser
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
# def VIA Safe Polyglot Optimizer AIO v0102
# def Mission
# def - Auto deploy and register safe local optimizer around NexusCore and Polyglot check/test/repair.
# def - Sandbox first. No destructive cleanup. No deletion. No stop-process. No global path mutation.
# def - Three rounds maximum to avoid Hydra risk.
# def - Generate HTML UI matrix, JSON registry, CSV matrices, and a one-command launcher.
# =============================================================================

$ErrorActionPreference = "Continue"
$ProgressPreference = "Continue"
$script:def_NOW = Get-Date
$script:def_VERSION = "v0102"
$script:def_STATUS = "BOOT"
$script:def_RISK = "MEDIUM"

# =============================================================================
# def PARAMS RESOLUTION
# =============================================================================

function def_ResolveDefaultPaths {
    if ([string]::IsNullOrWhiteSpace($ReadmePath)) {
        $script:ReadmePath = Join-Path $SupportiveModulesRoot "Read_Me_VeritasNexusCore.md"
    }
    if ([string]::IsNullOrWhiteSpace($NexusCorePath)) {
        $script:NexusCorePath = Join-Path $SupportiveModulesRoot "Invoke-VeritasNexusCore.ps1"
    }
    if ([string]::IsNullOrWhiteSpace($PolyglotPath)) {
        $script:PolyglotPath = Join-Path $SupportiveModulesRoot "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
    }
    if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
        $script:OutputRoot = Join-Path $SupportiveModulesRoot "_via_safe_polyglot_optimizer"
    }
}

function def_WriteLine {
    param(
        [string]$Level,
        [string]$Message
    )
    $ts = Get-Date -Format "HH:mm:ss.fff"
    Write-Host "[$ts] [$Level] $Message"
}

function def_EnsureDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    return $Path
}

function def_GetSha256 {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash
        }
    }
    catch {
        return "HASH_ERROR"
    }
    return "MISSING"
}

function def_ReadTextSafe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
        }
    }
    catch {
        try { return Get-Content -LiteralPath $Path -Raw -ErrorAction Stop } catch { return "" }
    }
    return ""
}

function def_WriteTextSafe {
    param(
        [string]$Path,
        [string]$Text
    )
    $dir = Split-Path -Parent $Path
    def_EnsureDirectory -Path $dir | Out-Null
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.Encoding]::UTF8)
}

function def_ToJsonFile {
    param(
        [string]$Path,
        [object]$Object,
        [int]$Depth = 12
    )
    $json = $Object | ConvertTo-Json -Depth $Depth
    def_WriteTextSafe -Path $Path -Text $json
}

function def_NewRunDirectory {
    def_EnsureDirectory -Path $OutputRoot | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $runDir = Join-Path $OutputRoot "RUN_${stamp}_VIA_SAFE_POLYGLOT_OPTIMIZER_$script:def_VERSION"
    def_EnsureDirectory -Path $runDir | Out-Null
    def_EnsureDirectory -Path (Join-Path $runDir "sandbox") | Out-Null
    def_EnsureDirectory -Path (Join-Path $runDir "reports") | Out-Null
    def_EnsureDirectory -Path (Join-Path $runDir "registry") | Out-Null
    def_EnsureDirectory -Path (Join-Path $runDir "logs") | Out-Null
    return $runDir
}

# =============================================================================
# def SAFETY POLICY
# =============================================================================

function def_GetSafetyPolicyRows {
    $rows = New-Object System.Collections.Generic.List[object]
    $rows.Add([pscustomobject]@{ Policy = "Sandbox First"; Status = "ENFORCED"; Detail = "Copy scripts into run sandbox before checks or optional self-test." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "No Delete"; Status = "ENFORCED"; Detail = "This AIO contains no Remove`-Item, no Clear`-RecycleBin, no permanent deletion." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "No Stop Process"; Status = "ENFORCED"; Detail = "No Stop`-Process and no process kill workflow." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "No Global Mutation"; Status = "ENFORCED"; Detail = "No PATH/profile/environment mutation. Writes only under output root and registry files." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "Coding Settings Protected"; Status = "ENFORCED"; Detail = ".git/.vscode/venv/node_modules/site-packages are treated as protected anchors." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "Three Rounds Max"; Status = "ENFORCED"; Detail = "MaxRounds is capped at 3 to avoid Hydra repair risk." }) | Out-Null
    $rows.Add([pscustomobject]@{ Policy = "Report Before Action"; Status = "ENFORCED"; Detail = "HTML/CSV/JSON report generated before optional child self-test." }) | Out-Null
    return $rows
}

function def_GetForbiddenPatternRows {
    $rows = New-Object System.Collections.Generic.List[object]
    $patterns = @(
        @{ Pattern = "Remove`-Item"; Risk = "HIGH"; Detail = "Destructive file delete command" },
        @{ Pattern = "Clear`-RecycleBin"; Risk = "HIGH"; Detail = "Irreversible recycle-bin cleanup risk" },
        @{ Pattern = "Stop`-Process"; Risk = "HIGH"; Detail = "Can interrupt active coding or system tasks" },
        @{ Pattern = "taskkill"; Risk = "HIGH"; Detail = "Can kill active tasks" },
        @{ Pattern = "docker system prune `--volumes"; Risk = "HIGH"; Detail = "Can delete Docker volumes/databases" },
        @{ Pattern = "Format-Volume"; Risk = "CRITICAL"; Detail = "Disk format risk" },
        @{ Pattern = "Set-ExecutionPolicy"; Risk = "MEDIUM"; Detail = "Global policy mutation" },
        @{ Pattern = "[Environment]::SetEnvironmentVariable"; Risk = "MEDIUM"; Detail = "Global environment mutation" },
        @{ Pattern = "attrib +U -P"; Risk = "MEDIUM"; Detail = "OneDrive local-only / cloud state mutation; should be explicit manual helper only" }
    )
    foreach ($p in $patterns) {
        $rows.Add([pscustomobject]@{ Pattern = $p.Pattern; Risk = $p.Risk; Detail = $p.Detail }) | Out-Null
    }
    return $rows
}

function def_ScanForbiddenPatterns {
    param(
        [string]$FilePath,
        [string]$Text
    )
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($p in def_GetForbiddenPatternRows) {
        $hit = $false
        if (-not [string]::IsNullOrWhiteSpace($Text)) {
            $hit = $Text.IndexOf($p.Pattern, [StringComparison]::OrdinalIgnoreCase) -ge 0
        }
        if ($hit) {
            $rows.Add([pscustomobject]@{
                File = $FilePath
                Pattern = $p.Pattern
                Risk = $p.Risk
                Class = "SEQUENCE_DEPENDENT_REVIEW"
                Message = $p.Detail
            }) | Out-Null
        }
    }
    return $rows
}

function def_TestProtectedAnchorPath {
    param([string]$Path)
    $protected = @(
        "\.git\",
        "\.vscode\",
        "\node_modules\",
        "\venv\",
        "\.venv\",
        "\envs\",
        "\site-packages\",
        "\AppData\Roaming\Code\User\",
        "\Google\Chrome\User Data\",
        "\Microsoft\Edge\User Data\",
        "\Windows\",
        "\Program Files\",
        "\Program Files (x86)\"
    )
    foreach ($item in $protected) {
        if ($Path -like "*$item*") { return $true }
    }
    return $false
}

# =============================================================================
# def INPUT / SANDBOX
# =============================================================================

function def_GetInputManifest {
    $files = @(
        @{ Role = "Readme"; Path = $ReadmePath },
        @{ Role = "NexusCore"; Path = $NexusCorePath },
        @{ Role = "PolyglotCheckTestRepair"; Path = $PolyglotPath }
    )
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($f in $files) {
        $exists = Test-Path -LiteralPath $f.Path
        $len = 0
        $sha = "MISSING"
        if ($exists) {
            try { $len = (Get-Item -LiteralPath $f.Path).Length } catch { $len = 0 }
            $sha = def_GetSha256 -Path $f.Path
        }
        $rows.Add([pscustomobject]@{
            Role = $f.Role
            SourcePath = $f.Path
            Exists = $exists
            LengthBytes = $len
            Sha256 = $sha
        }) | Out-Null
    }
    return $rows
}

function def_CopyInputsToSandbox {
    param([string]$RunDir)
    $sandboxDir = Join-Path $RunDir "sandbox"
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($item in def_GetInputManifest) {
        $target = Join-Path $sandboxDir (Split-Path -Leaf $item.SourcePath)
        if ($item.Exists) {
            try {
                Copy-Item -LiteralPath $item.SourcePath -Destination $target -Force
                $rows.Add([pscustomobject]@{
                    Role = $item.Role
                    SourcePath = $item.SourcePath
                    SandboxPath = $target
                    Copied = $true
                    Risk = "LOW"
                    Message = "Copied into sandbox. Original not modified."
                }) | Out-Null
            }
            catch {
                $rows.Add([pscustomobject]@{
                    Role = $item.Role
                    SourcePath = $item.SourcePath
                    SandboxPath = $target
                    Copied = $false
                    Risk = "MEDIUM"
                    Message = $_.Exception.Message
                }) | Out-Null
            }
        }
        else {
            $rows.Add([pscustomobject]@{
                Role = $item.Role
                SourcePath = $item.SourcePath
                SandboxPath = $target
                Copied = $false
                Risk = "HIGH"
                Message = "Input file missing."
            }) | Out-Null
        }
    }
    return $rows
}

function def_FindOperationOptimizerHtml {
    $candidates = New-Object System.Collections.Generic.List[string]
    $candidates.Add((Join-Path $SupportiveModulesRoot "VeritasOperationOptimizer_v1.0.html")) | Out-Null
    $candidates.Add((Join-Path $SupportiveModulesRoot "VeritasOperationOptimizer_v1.0(2).html")) | Out-Null
    $parent = Split-Path -Parent $SupportiveModulesRoot
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        $candidates.Add((Join-Path $parent "VeritasOperationOptimizer_v1.0.html")) | Out-Null
        $candidates.Add((Join-Path $parent "VeritasOperationOptimizer_v1.0(2).html")) | Out-Null
    }
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return ""
}

# =============================================================================
# def STATIC ANALYSIS
# =============================================================================

function def_ParsePowerShellAstSafe {
    param([string]$Path)
    $result = [ordered]@{
        Path = $Path
        Parsed = $false
        ErrorCount = 0
        Errors = @()
        FunctionCount = 0
        ParamAtTop = $false
    }
    if (-not (Test-Path -LiteralPath $Path)) { return [pscustomobject]$result }
    try {
        $tokens = $null
        $parseErrors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
        $result.Parsed = $true
        $result.ErrorCount = @($parseErrors).Count
        $result.Errors = @($parseErrors | ForEach-Object { $_.Message })
        $funcs = $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)
        $result.FunctionCount = @($funcs).Count
        $text = def_ReadTextSafe -Path $Path
        $trim = $text.TrimStart()
        $result.ParamAtTop = ($trim.StartsWith("param(") -or $trim.StartsWith("#requires") -or $trim.StartsWith("using "))
    }
    catch {
        $result.Parsed = $false
        $result.ErrorCount = 1
        $result.Errors = @($_.Exception.Message)
    }
    return [pscustomobject]$result
}

function def_ScanCodeAnchors {
    param(
        [string]$Path,
        [string]$Text
    )
    $rows = New-Object System.Collections.Generic.List[object]
    $anchors = @(
        @{ Name = "Functions"; Pattern = "function "; Category = "STRUCTURE" },
        @{ Name = "def_Functions"; Pattern = "function def_"; Category = "STRUCTURE" },
        @{ Name = "ParamBlock"; Pattern = "param("; Category = "ENTRY" },
        @{ Name = "HtmlReport"; Pattern = ".html"; Category = "REPORT" },
        @{ Name = "JsonOutput"; Pattern = "ConvertTo-Json"; Category = "REPORT" },
        @{ Name = "CsvOutput"; Pattern = "Export-Csv"; Category = "REPORT" },
        @{ Name = "Sandbox"; Pattern = "sandbox"; Category = "SAFETY" },
        @{ Name = "SelfTest"; Pattern = "SelfTest"; Category = "VALIDATION" },
        @{ Name = "OpenReport"; Pattern = "OpenReport"; Category = "UI" }
    )
    foreach ($a in $anchors) {
        $count = 0
        if (-not [string]::IsNullOrWhiteSpace($Text)) {
            $count = ([regex]::Matches($Text, [regex]::Escape($a.Pattern), [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)).Count
        }
        $rows.Add([pscustomobject]@{
            File = $Path
            Anchor = $a.Name
            Category = $a.Category
            Count = $count
            Status = if ($count -gt 0) { "FOUND" } else { "MISSING_OR_NOT_APPLICABLE" }
        }) | Out-Null
    }
    return $rows
}

function def_FindSubProjectsSafe {
    param([string]$BaseRoot)
    $rows = New-Object System.Collections.Generic.List[object]
    $root = Split-Path -Parent $BaseRoot
    if ([string]::IsNullOrWhiteSpace($root) -or -not (Test-Path -LiteralPath $root)) { return $rows }
    $dirCount = 0
    Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue | Select-Object -First 80 | ForEach-Object {
        $dirCount++
        $hasPy = @(Get-ChildItem -LiteralPath $_.FullName -Filter "*.py" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).Count -gt 0
        $hasPs = @(Get-ChildItem -LiteralPath $_.FullName -Filter "*.ps1" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).Count -gt 0
        $hasJs = @(Get-ChildItem -LiteralPath $_.FullName -Include "*.js","*.ts" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).Count -gt 0
        $rows.Add([pscustomobject]@{
            Project = $_.Name
            Path = $_.FullName
            HasPython = $hasPy
            HasPowerShell = $hasPs
            HasJavaScript = $hasJs
            Protected = def_TestProtectedAnchorPath -Path $_.FullName
        }) | Out-Null
    }
    return $rows
}

function def_ClassifyIssue {
    param(
        [string]$Category,
        [string]$Risk,
        [string]$Message
    )
    $cls = "PARALLEL_FIXABLE"
    if ($Risk -in @("HIGH", "CRITICAL")) { $cls = "SEQUENCE_DEPENDENT" }
    if ($Message -match "delete|Stop|global|PATH|volume|missing") { $cls = "SEQUENCE_DEPENDENT" }
    return $cls
}

# =============================================================================
# def TOOL MATRIX · 10 FUNCTIONS × 3 LANGUAGES × 15 LOCAL FREE TOOLS
# =============================================================================

function def_NewToolRow {
    param(
        [string]$FunctionArea,
        [string]$Language,
        [string[]]$Tools,
        [string]$UseCase
    )
    return [pscustomobject]@{
        FunctionArea = $FunctionArea
        Language = $Language
        Top15LocalFreeTools = ($Tools -join "; ")
        UseCase = $UseCase
    }
}

function def_GetToolMatrixRows {
    $rows = New-Object System.Collections.Generic.List[object]

    $rows.Add((def_NewToolRow "Accelerating" "Python" @("polars","duckdb","pyarrow","numpy","numba","joblib","dask","ray","orjson","uvloop","aiohttp","httpx","ruff","uv","maturin") "Data speed, parallelism, async IO, packaging acceleration")) | Out-Null
    $rows.Add((def_NewToolRow "Accelerating" "PowerShell" @("ThreadJob","ForEach-Object -Parallel","PSScriptAnalyzer","Pester","ImportExcel","PSWriteHTML","Pode","PSFramework","PSReadLine","CompletionPredictor","BurntToast","Microsoft.PowerShell.Archive","Microsoft.PowerShell.SecretManagement","PSWindowsUpdate","PowerShellGet") "Parallel jobs, HTML reports, test automation, shell productivity")) | Out-Null
    $rows.Add((def_NewToolRow "Accelerating" "JavaScript" @("esbuild","vite","swc","tsx","turbo","nx","pnpm","bun","fastify","hono","piscina","worker_threads","node-cache","msgpackr","rollup") "Build speed, monorepo speed, worker threading, API speed")) | Out-Null

    $rows.Add((def_NewToolRow "Panoramic Analysis" "Python" @("rich","textual","pandas","polars","duckdb","networkx","pyvis","plotly","pydantic","typer","watchdog","psutil","loguru","great_expectations","jsonschema") "Console/UI, graph view, data quality, file watching")) | Out-Null
    $rows.Add((def_NewToolRow "Panoramic Analysis" "PowerShell" @("PSWriteHTML","ImportExcel","PSScriptAnalyzer","Pester","ThreadJob","Pode","Polaris","PSFramework","PSReadLine","Get-ChildItem","Measure-Object","ConvertTo-Json","Export-Csv","CimCmdlets","EventLog") "Matrix reports, inventory, system status, validation")) | Out-Null
    $rows.Add((def_NewToolRow "Panoramic Analysis" "JavaScript" @("react","next","vite","echarts","plotly.js","d3","ag-grid-community","tanstack-table","zod","pino","chokidar","commander","fast-glob","dependency-cruiser","madge") "UI matrix, dependency graph, typed schema, file scanning")) | Out-Null

    $rows.Add((def_NewToolRow "Full Error Identification" "Python" @("ruff","pyright","mypy","pytest","coverage","hypothesis","bandit","pip-audit","vulture","interrogate","radon","xenon","pylint","flake8","pydocstyle") "Lint, type, security, coverage, complexity, dead code")) | Out-Null
    $rows.Add((def_NewToolRow "Full Error Identification" "PowerShell" @("PSScriptAnalyzer","Pester","PowerShell Parser AST","StrictMode","PSFramework","ImportExcel","PSWriteHTML","Test-Path","Get-Command","Get-Module","Get-Error","Trace-Command","Start-Transcript","CimCmdlets","EventLog") "Syntax, cmdlet availability, runtime diagnostics, test reporting")) | Out-Null
    $rows.Add((def_NewToolRow "Full Error Identification" "JavaScript" @("eslint","typescript","tsc","vitest","jest","playwright","c8","dependency-cruiser","madge","depcheck","npm audit","knip","ts-prune","jscpd","prettier") "Lint, test, dependency, duplicate code, audit, formatting")) | Out-Null

    $rows.Add((def_NewToolRow "Optimization Points" "Python" @("scalene","py-spy","cProfile","line_profiler","memory_profiler","snakeviz","pyinstrument","pandas-vet","ruff","polars","duckdb","orjson","cachetools","diskcache","pytest-benchmark") "CPU/memory profiling, benchmark, cache and data IO optimization")) | Out-Null
    $rows.Add((def_NewToolRow "Optimization Points" "PowerShell" @("Measure-Command","Trace-Command","PSScriptAnalyzer","ThreadJob","ForEach-Object -Parallel","Start-Transcript","PSWriteHTML","ImportExcel","Get-Counter","Get-Process","Get-CimInstance","Get-EventLog","Pode","PSFramework","Microsoft.PowerShell.Utility") "Timing, parallel-safe classification, performance counters")) | Out-Null
    $rows.Add((def_NewToolRow "Optimization Points" "JavaScript" @("clinic","0x","node --prof","autocannon","tinybench","benchmark.js","webpack-bundle-analyzer","rollup-plugin-visualizer","lighthouse","source-map-explorer","esbuild","vite","piscina","fast-json-stringify","msgpackr") "Profiling, API load, bundle size, worker acceleration")) | Out-Null

    $rows.Add((def_NewToolRow "Positioning Anchor Points" "Python" @("ast","libcst","bowler","rope","parso","jedi","tree-sitter","ripgrep","pathspec","networkx","pyvis","sqlglot","pydantic","jsonschema","rich") "Precise anchors, refactor targets, dependency maps")) | Out-Null
    $rows.Add((def_NewToolRow "Positioning Anchor Points" "PowerShell" @("PowerShell AST","Select-String","Get-ChildItem","Resolve-Path","Get-Command","PSScriptAnalyzer","Pester","ImportExcel","PSWriteHTML","ConvertFrom-Json","ConvertTo-Json","Trace-Command","Start-Transcript","CimCmdlets","PSFramework") "Function anchors, exact file/line references, matrix output")) | Out-Null
    $rows.Add((def_NewToolRow "Positioning Anchor Points" "JavaScript" @("ts-morph","typescript compiler api","acorn","espree","babel parser","recast","jscodeshift","tree-sitter","madge","dependency-cruiser","fast-glob","ripgrep","source-map","eslint","prettier") "AST anchors, codemods, dependency graph, exact line targeting")) | Out-Null

    $rows.Add((def_NewToolRow "AST Analysis" "Python" @("ast","libcst","parso","redbaron","astroid","bowler","rope","jedi","tree-sitter","sqlglot","pyflakes","ruff","mypy","pyright","bandit") "AST parse, refactor, type/security lint")) | Out-Null
    $rows.Add((def_NewToolRow "AST Analysis" "PowerShell" @("System.Management.Automation.Language.Parser","PSScriptAnalyzer","Pester","Select-String","Trace-Command","Get-Command","Get-Module","PSFramework","ImportExcel","PSWriteHTML","ConvertFrom-Json","ConvertTo-Json","StrictMode","Get-Error","Start-Transcript") "Native PowerShell AST and rule checks")) | Out-Null
    $rows.Add((def_NewToolRow "AST Analysis" "JavaScript" @("typescript","ts-morph","acorn","espree","babel parser","recast","jscodeshift","tree-sitter","eslint","prettier","swc","sucrase","meriyah","oxc-parser","dependency-cruiser") "Syntax tree, codemod, linter integration")) | Out-Null

    $rows.Add((def_NewToolRow "Hydra Risk Detection" "Python" @("networkx","pyvis","pipdeptree","pip-audit","bandit","safety","vulture","radon","xenon","pydeps","snakefood","pytest","hypothesis","jsonschema","pydantic") "Cascading dependency/risk detection and test gates")) | Out-Null
    $rows.Add((def_NewToolRow "Hydra Risk Detection" "PowerShell" @("PSScriptAnalyzer","Pester","Get-Command","Get-Module","ImportExcel","PSWriteHTML","ThreadJob","Start-Transcript","Trace-Command","Get-EventLog","CimCmdlets","ConvertTo-Json","ConvertFrom-Json","Test-Path","PSFramework") "Detect destructive command, missing module, sequential dependency risk")) | Out-Null
    $rows.Add((def_NewToolRow "Hydra Risk Detection" "JavaScript" @("dependency-cruiser","madge","npm audit","pnpm audit","depcheck","knip","ts-prune","jscpd","eslint","typescript","vitest","playwright","c8","lockfile-lint","license-checker-rseidelsohn") "Dependency cycles, unused packages, lock risks, license/security")) | Out-Null

    $rows.Add((def_NewToolRow "Syntax Pycompile" "Python" @("py_compile","compileall","ruff","pyright","mypy","pytest","tox","nox","uv","pip-check","pipdeptree","pydantic","jsonschema","tomli","packaging") "Syntax compile, env validation, schema and package checks")) | Out-Null
    $rows.Add((def_NewToolRow "Syntax Pycompile" "PowerShell" @("PowerShell Parser AST","PSScriptAnalyzer","Pester","pwsh -NoProfile","StrictMode","Get-Command","Get-Module","Test-Path","ConvertFrom-Json","Import-PowerShellDataFile","Trace-Command","Get-Error","Start-Transcript","PSReadLine","PowerShellGet") "Parse and validate PowerShell scripts and modules")) | Out-Null
    $rows.Add((def_NewToolRow "Syntax Pycompile" "JavaScript" @("node --check","tsc --noEmit","eslint","prettier","vitest","jest","tsx","ts-node","babel parser","swc","acorn","espree","zod","jsonschema","ajv") "Syntax check, TS type check, schema validation")) | Out-Null

    $rows.Add((def_NewToolRow "Static Analysis" "Python" @("ruff","pylint","flake8","mypy","pyright","bandit","pip-audit","vulture","radon","xenon","interrogate","pydocstyle","black","isort","pre-commit") "Static quality, style, type, security and docs")) | Out-Null
    $rows.Add((def_NewToolRow "Static Analysis" "PowerShell" @("PSScriptAnalyzer","Pester","PowerShell AST","ScriptAnalyzer custom rules","ImportExcel","PSWriteHTML","ConvertTo-Json","Select-String","Get-Command","Get-Help","StrictMode","Start-Transcript","Trace-Command","PSFramework","PSScriptAnalyzerSettings") "PowerShell lint, custom safety policy and matrix reports")) | Out-Null
    $rows.Add((def_NewToolRow "Static Analysis" "JavaScript" @("eslint","typescript","tsc","prettier","biome","oxlint","depcheck","knip","dependency-cruiser","madge","npm audit","jscpd","ts-prune","lockfile-lint","license-checker-rseidelsohn") "Lint, type, dependencies, duplicate code, license/security")) | Out-Null

    $rows.Add((def_NewToolRow "Top25 Failures Solutions" "Python" @("pytest","hypothesis","coverage","ruff","mypy","pyright","bandit","pip-audit","pipdeptree","compileall","cProfile","scalene","memory_profiler","loguru","rich") "Embeddable failure reproduction, diagnostics and fixes")) | Out-Null
    $rows.Add((def_NewToolRow "Top25 Failures Solutions" "PowerShell" @("Pester","PSScriptAnalyzer","PowerShell AST","Start-Transcript","Get-Error","Trace-Command","Test-Path","Get-Command","Get-Module","ImportExcel","PSWriteHTML","ThreadJob","CimCmdlets","EventLog","ConvertTo-Json") "Top failure matrix, reproducible checks, report export")) | Out-Null
    $rows.Add((def_NewToolRow "Top25 Failures Solutions" "JavaScript" @("vitest","jest","playwright","eslint","typescript","tsc","c8","npm audit","depcheck","knip","madge","dependency-cruiser","jscpd","prettier","node --check") "Failure tests, browser/user tests, dependency risk checks")) | Out-Null

    return $rows
}

function def_GetFailureSolutionRows {
    $rows = New-Object System.Collections.Generic.List[object]
    $items = @(
        @{ Id=1; Failure="Missing input file"; Risk="HIGH"; Solution="Mark missing in registry, skip execution, require path fix before activation." },
        @{ Id=2; Failure="PowerShell parser error"; Risk="HIGH"; Solution="Use AST parse message, fix exact line, rerun sandbox parse only." },
        @{ Id=3; Failure="Remove`-Item in optimizer path"; Risk="HIGH"; Solution="Downgrade to report-only or quarantine plan; never direct delete." },
        @{ Id=4; Failure="Clear`-RecycleBin usage"; Risk="HIGH"; Solution="Disable; use recoverable quarantine and manual review." },
        @{ Id=5; Failure="Stop`-Process usage"; Risk="HIGH"; Solution="Replace with detection/report; user closes process manually." },
        @{ Id=6; Failure="Docker prune volumes"; Risk="HIGH"; Solution="Permit docker system df only; volumes require explicit backup and manual approval." },
        @{ Id=7; Failure="Global PATH mutation"; Risk="MEDIUM"; Solution="Use process-local PATH; write env plan instead of applying globally." },
        @{ Id=8; Failure="OneDrive online-only forced download"; Risk="MEDIUM"; Solution="Skip reparse/cloud placeholders; use explicit Free up space helper only." },
        @{ Id=9; Failure=".git deletion or cleanup"; Risk="HIGH"; Solution="Protect .git; use git gc only when repo is clean and backed up." },
        @{ Id=10; Failure="node_modules active project removal"; Risk="MEDIUM"; Solution="Classify as cache candidate only; require lockfile and rebuild plan." },
        @{ Id=11; Failure="venv/site-packages removal"; Risk="MEDIUM"; Solution="Protect active env; only stale env candidate after manifest verification." },
        @{ Id=12; Failure="Huge duplicated CSV/Parquet"; Risk="LOW"; Solution="Use size+extension candidate then SHA256; report/quarantine only." },
        @{ Id=13; Failure="HTML report huge due base64"; Risk="LOW"; Solution="Move assets external; compress; keep final/latest only." },
        @{ Id=14; Failure="Recursive junction loop"; Risk="HIGH"; Solution="Skip reparse points; cap MaxFiles and MaxDepth." },
        @{ Id=15; Failure="Long path failures"; Risk="MEDIUM"; Solution="Use LiteralPath and extended-path awareness; report failures." },
        @{ Id=16; Failure="Encoding corruption"; Risk="MEDIUM"; Solution="Use UTF8 with BOM only for Excel CSV; UTF8 for JSON/HTML." },
        @{ Id=17; Failure="Invalid JSON from child script"; Risk="MEDIUM"; Solution="Capture stdout/stderr separately; validate with ConvertFrom-Json." },
        @{ Id=18; Failure="Port conflict"; Risk="LOW"; Solution="Probe port; choose next candidate; report selected port." },
        @{ Id=19; Failure="Browser auto-open blocked"; Risk="LOW"; Solution="Print HTML path; skip browser with -NoBrowser." },
        @{ Id=20; Failure="Admin-required command"; Risk="MEDIUM"; Solution="Detect admin status; degrade to read-only report when not elevated." },
        @{ Id=21; Failure="Network dependency"; Risk="MEDIUM"; Solution="Local-only by default; no install unless explicit flag added in future." },
        @{ Id=22; Failure="Package version conflict"; Risk="MEDIUM"; Solution="Generate env plan; avoid global pip/npm install." },
        @{ Id=23; Failure="C drive low space during run"; Risk="HIGH"; Solution="Preflight disk check; write outputs under chosen root; cap logs." },
        @{ Id=24; Failure="Hydra cascade risk"; Risk="HIGH"; Solution="Classify parallel vs sequence; cap fixes at three rounds." },
        @{ Id=25; Failure="False duplicate detection by size only"; Risk="HIGH"; Solution="Size/extension only candidate; SHA256 required for confirmed duplicate." }
    )
    foreach ($i in $items) {
        $rows.Add([pscustomobject]@{
            Id = $i.Id
            Failure = $i.Failure
            Risk = $i.Risk
            Solution = $i.Solution
            Class = def_ClassifyIssue -Category "FAILURE" -Risk $i.Risk -Message $i.Failure
        }) | Out-Null
    }
    return $rows
}

# =============================================================================
# def ROUND ENGINE
# =============================================================================

function def_RunOptionalSandboxSelfTest {
    param(
        [string]$RunDir,
        [object[]]$SandboxRows
    )
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($item in $SandboxRows) {
        if (-not $item.Copied) { continue }
        if ($item.SandboxPath -notlike "*.ps1") { continue }
        $leaf = Split-Path -Leaf $item.SandboxPath
        $logPath = Join-Path (Join-Path $RunDir "logs") ("SELFTEST_" + $leaf + ".txt")
        if (-not $RunSandboxSelfTest) {
            $rows.Add([pscustomobject]@{
                Script = $leaf
                Ran = $false
                ExitCode = "SKIPPED"
                Risk = "LOW"
                Message = "Skipped by default. Use -RunSandboxSelfTest to execute copied child script with -SelfTest."
                Log = $logPath
            }) | Out-Null
            continue
        }
        try {
            $stdoutPath = Join-Path (Join-Path $RunDir "logs") ("SELFTEST_" + $leaf + ".stdout.txt")
            $stderrPath = Join-Path (Join-Path $RunDir "logs") ("SELFTEST_" + $leaf + ".stderr.txt")
            $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $item.SandboxPath, "-SelfTest", "-NoBrowser")
            $p = Start-Process -FilePath "pwsh" -ArgumentList $argList -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -WindowStyle Hidden
            $finished = $p.WaitForExit(180000)
            $combined = "STDOUT: $stdoutPath`nSTDERR: $stderrPath"
            def_WriteTextSafe -Path $logPath -Text $combined
            if (-not $finished) {
                $rows.Add([pscustomobject]@{
                    Script = $leaf
                    Ran = $true
                    ExitCode = "TIMEOUT"
                    Risk = "MEDIUM"
                    Message = "Child self-test timed out after 180 seconds. Process was not killed by this tool."
                    Log = $logPath
                }) | Out-Null
            }
            else {
                $risk = if ($p.ExitCode -eq 0) { "LOW" } else { "MEDIUM" }
                $rows.Add([pscustomobject]@{
                    Script = $leaf
                    Ran = $true
                    ExitCode = $p.ExitCode
                    Risk = $risk
                    Message = "Sandbox child self-test finished."
                    Log = $logPath
                }) | Out-Null
            }
        }
        catch {
            $rows.Add([pscustomobject]@{
                Script = $leaf
                Ran = $true
                ExitCode = "ERROR"
                Risk = "MEDIUM"
                Message = $_.Exception.Message
                Log = $logPath
            }) | Out-Null
        }
    }
    return $rows
}

function def_RunRound {
    param(
        [int]$Round,
        [string]$RunDir,
        [object[]]$SandboxRows
    )
    $rows = New-Object System.Collections.Generic.List[object]
    $anchorRows = New-Object System.Collections.Generic.List[object]
    $forbiddenRows = New-Object System.Collections.Generic.List[object]
    $astRows = New-Object System.Collections.Generic.List[object]

    $phase = if ($Round -eq 1) { "Comprehensive Fix Planning" } elseif ($Round -eq 2) { "Sequential Fix Planning" } else { "Final Polishing Planning" }

    foreach ($s in $SandboxRows) {
        $text = def_ReadTextSafe -Path $s.SandboxPath
        $frows = def_ScanForbiddenPatterns -FilePath $s.SandboxPath -Text $text
        foreach ($f in $frows) { $forbiddenRows.Add($f) | Out-Null }
        $arows = def_ScanCodeAnchors -Path $s.SandboxPath -Text $text
        foreach ($a in $arows) { $anchorRows.Add($a) | Out-Null }
        if ($s.SandboxPath -like "*.ps1") {
            $ast = def_ParsePowerShellAstSafe -Path $s.SandboxPath
            $astRows.Add($ast) | Out-Null
        }
    }

    foreach ($s in $SandboxRows) {
        $risk = $s.Risk
        $msg = $s.Message
        if (-not $s.Copied) { $risk = "HIGH"; $msg = "Required file missing or not copied." }
        $rows.Add([pscustomobject]@{
            Round = $Round
            Phase = $phase
            Layer = "SANDBOX_INPUT"
            Item = $s.Role
            Status = if ($s.Copied) { "OK_COPIED" } else { "FAIL_INPUT" }
            Risk = $risk
            Class = def_ClassifyIssue -Category "INPUT" -Risk $risk -Message $msg
            Message = $msg
            Path = $s.SandboxPath
        }) | Out-Null
    }

    foreach ($ast in $astRows) {
        $risk = if ($ast.ErrorCount -eq 0) { "LOW" } else { "HIGH" }
        $rows.Add([pscustomobject]@{
            Round = $Round
            Phase = $phase
            Layer = "AST"
            Item = Split-Path -Leaf $ast.Path
            Status = if ($ast.ErrorCount -eq 0) { "OK_AST" } else { "FAIL_AST" }
            Risk = $risk
            Class = def_ClassifyIssue -Category "AST" -Risk $risk -Message ((@($ast.Errors) -join " | "))
            Message = "Errors=$($ast.ErrorCount); Functions=$($ast.FunctionCount); ParamAtTop=$($ast.ParamAtTop)"
            Path = $ast.Path
        }) | Out-Null
    }

    foreach ($f in $forbiddenRows) {
        $rows.Add([pscustomobject]@{
            Round = $Round
            Phase = $phase
            Layer = "HYDRA_RISK"
            Item = $f.Pattern
            Status = "WARN_FORBIDDEN_PATTERN"
            Risk = $f.Risk
            Class = $f.Class
            Message = $f.Message
            Path = $f.File
        }) | Out-Null
    }

    foreach ($a in $anchorRows) {
        $risk = if ($a.Status -eq "FOUND") { "LOW" } else { "LOW" }
        $rows.Add([pscustomobject]@{
            Round = $Round
            Phase = $phase
            Layer = "ANCHOR"
            Item = $a.Anchor
            Status = $a.Status
            Risk = $risk
            Class = "PARALLEL_FIXABLE"
            Message = "Category=$($a.Category); Count=$($a.Count)"
            Path = $a.File
        }) | Out-Null
    }

    $subProjects = def_FindSubProjectsSafe -BaseRoot $SupportiveModulesRoot
    foreach ($p in $subProjects) {
        $rows.Add([pscustomobject]@{
            Round = $Round
            Phase = $phase
            Layer = "SUBPROJECT_DISCOVERY"
            Item = $p.Project
            Status = "DISCOVERED"
            Risk = if ($p.Protected) { "LOW" } else { "LOW" }
            Class = "PARALLEL_FIXABLE"
            Message = "Python=$($p.HasPython); PowerShell=$($p.HasPowerShell); JavaScript=$($p.HasJavaScript); Protected=$($p.Protected)"
            Path = $p.Path
        }) | Out-Null
    }

    $fixStage = if ($Round -eq 1) { "Comprehensive report-only improvement plan generated." } elseif ($Round -eq 2) { "Sequence-dependent risks isolated for manual review." } else { "Final activation pointer and launcher prepared." }
    $rows.Add([pscustomobject]@{
        Round = $Round
        Phase = $phase
        Layer = "FIX_STRATEGY"
        Item = "TEST_DEBUG_OPTIMIZE_CONSOLIDATE"
        Status = "PLAN_READY"
        Risk = "LOW"
        Class = "PARALLEL_FIXABLE"
        Message = $fixStage
        Path = $RunDir
    }) | Out-Null

    return $rows
}

# =============================================================================
# def REGISTRY AND LAUNCHER
# =============================================================================

function def_WriteRegistryAndPointer {
    param(
        [string]$RunDir,
        [object[]]$InputRows,
        [object[]]$MatrixRows,
        [string]$HtmlPath
    )
    $registryDir = Join-Path $SupportiveModulesRoot "_nexus_registry"
    def_EnsureDirectory -Path $registryDir | Out-Null
    $registryPath = Join-Path $registryDir "VIA_SAFE_POLYGLOT_OPTIMIZER_REGISTRY.json"
    $pointerPath = Join-Path $registryDir "VIA_SAFE_POLYGLOT_OPTIMIZER_ACTIVE_POINTER.json"
    $registry = [ordered]@{
        name = "VIA Safe Polyglot Optimizer"
        version = $script:def_VERSION
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        status = $script:def_STATUS
        risk = $script:def_RISK
        supportive_modules_root = $SupportiveModulesRoot
        run_dir = $RunDir
        html_report = $HtmlPath
        inputs = $InputRows
        matrix_count = @($MatrixRows).Count
        policy = def_GetSafetyPolicyRows
        launch_command = "pwsh -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`" -OpenReport -RegisterLauncher"
    }
    def_ToJsonFile -Path $registryPath -Object $registry -Depth 16
    def_ToJsonFile -Path $pointerPath -Object ([ordered]@{ active_registry = $registryPath; active_run_dir = $RunDir; html_report = $HtmlPath; updated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") }) -Depth 8
    return [pscustomobject]@{ RegistryPath = $registryPath; PointerPath = $pointerPath }
}

function def_WriteLauncher {
    param([string]$ScriptPath)
    $launcherPath = Join-Path $SupportiveModulesRoot "Invoke-VIA-SafePolyglotOptimizer.ps1"
    $body = @"
#requires -Version 7.0
param(
    [switch]`$OpenReport,
    [switch]`$RunSandboxSelfTest,
    [switch]`$SelfTest
)
`$ErrorActionPreference = "Continue"
`$scriptPath = "$ScriptPath"
if (-not (Test-Path -LiteralPath `$scriptPath)) {
    throw "AIO script not found: `$scriptPath"
}
`$argsList = @("-ExecutionPolicy", "Bypass", "-File", `$scriptPath, "-RegisterLauncher")
if (`$OpenReport) { `$argsList += "-OpenReport" }
if (`$RunSandboxSelfTest) { `$argsList += "-RunSandboxSelfTest" }
if (`$SelfTest) { `$argsList += "-SelfTest" }
& pwsh @argsList
"@
    def_WriteTextSafe -Path $launcherPath -Text $body
    return $launcherPath
}

# =============================================================================
# def HTML UI MATRIX REPORT
# =============================================================================

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_RowsToTableHtml {
    param(
        [object[]]$Rows,
        [int]$MaxRows = 500
    )
    if ($null -eq $Rows -or @($Rows).Count -eq 0) { return "<p class='muted'>No rows.</p>" }
    $first = @($Rows)[0]
    $props = $first.PSObject.Properties.Name
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("<table><thead><tr>")
    foreach ($p in $props) { [void]$sb.AppendLine("<th>$(def_HtmlEncode $p)</th>") }
    [void]$sb.AppendLine("</tr></thead><tbody>")
    $count = 0
    foreach ($r in $Rows) {
        $count++
        if ($count -gt $MaxRows) { break }
        [void]$sb.AppendLine("<tr>")
        foreach ($p in $props) {
            $v = $r.$p
            $cls = ""
            if ($p -eq "Risk") { $cls = " class='risk-$(def_HtmlEncode $v)'" }
            if ($p -eq "Status") { $cls = " class='status'" }
            [void]$sb.AppendLine("<td$cls>$(def_HtmlEncode $v)</td>")
        }
        [void]$sb.AppendLine("</tr>")
    }
    [void]$sb.AppendLine("</tbody></table>")
    if (@($Rows).Count -gt $MaxRows) { [void]$sb.AppendLine("<p class='muted'>Showing first $MaxRows of $(@($Rows).Count) rows.</p>") }
    return $sb.ToString()
}

function def_WriteHtmlReport {
    param(
        [string]$RunDir,
        [object[]]$InputRows,
        [object[]]$SandboxRows,
        [object[]]$RoundRows,
        [object[]]$ToolRows,
        [object[]]$FailureRows,
        [object[]]$SelfTestRows,
        [object[]]$PolicyRows
    )
    $htmlPath = Join-Path (Join-Path $RunDir "reports") "VIA_SafePolyglotOptimizer_Matrix_Report.html"
    $fail = @($RoundRows | Where-Object { $_.Status -like "FAIL*" }).Count
    $warn = @($RoundRows | Where-Object { $_.Status -like "WARN*" }).Count
    $high = @($RoundRows | Where-Object { $_.Risk -in @("HIGH", "CRITICAL") }).Count
    $ok = @($RoundRows | Where-Object { $_.Status -like "OK*" -or $_.Status -eq "FOUND" -or $_.Status -eq "DISCOVERED" -or $_.Status -eq "PLAN_READY" }).Count
    $parallel = @($RoundRows | Where-Object { $_.Class -eq "PARALLEL_FIXABLE" }).Count
    $seq = @($RoundRows | Where-Object { $_.Class -eq "SEQUENCE_DEPENDENT" -or $_.Class -like "SEQUENCE*" }).Count
    $risk = if ($fail -gt 0 -or $high -gt 0) { "HIGH" } elseif ($warn -gt 0) { "MEDIUM" } else { "LOW" }
    $script:def_RISK = $risk
    $script:def_STATUS = if ($risk -eq "LOW") { "SAFE_POLYGLOT_OPTIMIZER_READY" } else { "SAFE_POLYGLOT_OPTIMIZER_READY_WITH_REVIEW" }

    $css = @"
:root{--bg:#0d1117;--panel:#111827;--card:#172033;--line:#2b3a55;--text:#eef2ff;--muted:#9aa6bd;--cyan:#38bdf8;--green:#22c55e;--yellow:#f59e0b;--red:#ef4444;--purple:#a78bfa;}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0%,#13243d 0,#0d1117 36%,#090b10 100%);color:var(--text);font-family:Segoe UI,Microsoft JhengHei,Arial,sans-serif;line-height:1.55}.wrap{max-width:1640px;margin:0 auto;padding:24px}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(56,189,248,.13),rgba(167,139,250,.09));border-radius:22px;padding:28px;margin-bottom:18px}.hero h1{margin:0;font-size:30px}.sub{color:var(--muted);margin-top:8px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}.kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px}.kpi b{display:block;font-size:28px;color:var(--cyan)}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}.tab{border:1px solid var(--line);background:var(--panel);padding:10px 14px;border-radius:999px;color:var(--text);cursor:pointer}.tab.active{background:linear-gradient(135deg,#2563eb,#0891b2)}.section{display:none}.section.active{display:block}.card{background:rgba(17,24,39,.86);border:1px solid var(--line);border-radius:18px;padding:18px;margin:14px 0;overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{color:var(--cyan);background:#111827;position:sticky;top:0}tr:hover{background:rgba(56,189,248,.06)}.risk-LOW{color:var(--green);font-weight:700}.risk-MEDIUM{color:var(--yellow);font-weight:700}.risk-HIGH,.risk-CRITICAL{color:var(--red);font-weight:700}.status{font-family:Consolas,monospace;color:#e0f2fe}.muted{color:var(--muted)}.cmd{background:#050812;border:1px solid var(--line);border-radius:14px;padding:14px;font-family:Consolas,monospace;white-space:pre-wrap}.footer{color:var(--muted);text-align:center;margin:30px 0}a{color:var(--cyan)}
"@

    $cmd = "pwsh -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`" -OpenReport -RegisterLauncher"
    $html = @"
<!doctype html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA Safe Polyglot Optimizer Matrix</title><style>$css</style></head><body><div class="wrap">
<div class="hero"><h1>def VIA Safe Polyglot Optimizer · $script:def_VERSION</h1><div class="sub">Sandbox Test & Repair · NexusCore Registration · Polyglot Matrix · Hydra Risk Gate · Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</div></div>
<div class="kpis"><div class="kpi"><b>$script:def_STATUS</b><span>Status</span></div><div class="kpi"><b>$risk</b><span>Risk</span></div><div class="kpi"><b>$ok</b><span>OK / Found</span></div><div class="kpi"><b>$warn</b><span>WARN</span></div><div class="kpi"><b>$fail</b><span>FAIL</span></div><div class="kpi"><b>$high</b><span>High Risk</span></div><div class="kpi"><b>$parallel</b><span>Parallel</span></div><div class="kpi"><b>$seq</b><span>Sequence</span></div></div>
<div class="tabs"><button class="tab active" onclick="showTab('summary')">Summary</button><button class="tab" onclick="showTab('rounds')">3-Round Matrix</button><button class="tab" onclick="showTab('tools')">Tool Matrix</button><button class="tab" onclick="showTab('failures')">Top 25 Failures</button><button class="tab" onclick="showTab('policy')">Safety Policy</button><button class="tab" onclick="showTab('selftest')">Self-Test</button><button class="tab" onclick="showTab('commands')">Commands</button></div>
<section id="summary" class="section active"><div class="card"><h2>def Input Manifest</h2>$(def_RowsToTableHtml -Rows $InputRows)</div><div class="card"><h2>def Sandbox Copies</h2>$(def_RowsToTableHtml -Rows $SandboxRows)</div></section>
<section id="rounds" class="section"><div class="card"><h2>def Three-Round Panoramic Analysis Matrix</h2>$(def_RowsToTableHtml -Rows $RoundRows -MaxRows 900)</div></section>
<section id="tools" class="section"><div class="card"><h2>def 10 Functions × 3 Languages × Top 15 Local Free Tools</h2>$(def_RowsToTableHtml -Rows $ToolRows -MaxRows 100)</div></section>
<section id="failures" class="section"><div class="card"><h2>def Top 25 Failures & Solutions</h2>$(def_RowsToTableHtml -Rows $FailureRows -MaxRows 50)</div></section>
<section id="policy" class="section"><div class="card"><h2>def Safety Policy</h2>$(def_RowsToTableHtml -Rows $PolicyRows)</div></section>
<section id="selftest" class="section"><div class="card"><h2>def Sandbox Self-Test</h2>$(def_RowsToTableHtml -Rows $SelfTestRows)</div></section>
<section id="commands" class="section"><div class="card"><h2>def Activation Command</h2><div class="cmd">$(def_HtmlEncode $cmd)</div><p class="muted">Default mode is report-only. Add -RunSandboxSelfTest only when you want copied child scripts to run their own -SelfTest in the sandbox.</p></div></section>
<div class="footer">Veritas Intelligence Analytics · Safe local automation · No delete · No stop-process · No global mutation</div>
</div><script>function showTab(id){document.querySelectorAll('.section').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');event.target.classList.add('active');}</script></body></html>
"@
    def_WriteTextSafe -Path $htmlPath -Text $html
    return $htmlPath
}

# =============================================================================
# def SELF TEST
# =============================================================================

function def_RunSelfTest {
    param([string]$ScriptPath)
    $rows = New-Object System.Collections.Generic.List[object]
    $text = def_ReadTextSafe -Path $ScriptPath
    $checks = @(
        @{ Name="ParamAtTop"; Pass=($text -match "(?s)^#requires[\s\S]*?param\(") },
        @{ Name="HasDefMain"; Pass=($text -match "function def_Main") },
        @{ Name="NoDirectDeleteCommand"; Pass=($text -notmatch "(?m)^\s*Remove`-Item\b") },
        @{ Name="NoDirectRecycleClearCommand"; Pass=($text -notmatch "(?m)^\s*Clear`-RecycleBin\b") },
        @{ Name="NoDirectStopProcessCommand"; Pass=($text -notmatch "(?m)^\s*Stop`-Process\b") },
        @{ Name="NoDirectDockerVolumePrune"; Pass=($text -notmatch "(?m)^\s*docker\s+system\s+prune\s+--volumes") },
        @{ Name="HasToolMatrix"; Pass=($text -match "def_GetToolMatrixRows") },
        @{ Name="HasTop25Failures"; Pass=($text -match "def_GetFailureSolutionRows") },
        @{ Name="HasHtmlReport"; Pass=($text -match "def_WriteHtmlReport") },
        @{ Name="HasSandboxCopy"; Pass=($text -match "def_CopyInputsToSandbox") }
    )
    foreach ($c in $checks) {
        $rows.Add([pscustomobject]@{ Check = $c.Name; Pass = [bool]$c.Pass; Status = if ($c.Pass) { "OK" } else { "FAIL" } }) | Out-Null
    }
    return $rows
}

# =============================================================================
# def MAIN
# =============================================================================

function def_Main {
    def_ResolveDefaultPaths
    $effectiveMaxRounds = $MaxRounds
    if ($effectiveMaxRounds -gt 3) { $effectiveMaxRounds = 3 }
    if ($effectiveMaxRounds -lt 1) { $effectiveMaxRounds = 1 }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA SAFE POLYGLOT OPTIMIZER AIO $script:def_VERSION" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    def_WriteLine "BOOT" "SupportiveModulesRoot: $SupportiveModulesRoot"
    def_WriteLine "POLICY" "No delete. No Stop`-Process. Sandbox first. Three rounds maximum."

    $runDir = def_NewRunDirectory
    def_WriteLine "RUN" "RunDir: $runDir"

    $inputRows = def_GetInputManifest
    $sandboxRows = def_CopyInputsToSandbox -RunDir $runDir
    $policyRows = def_GetSafetyPolicyRows
    $toolRows = def_GetToolMatrixRows
    $failureRows = def_GetFailureSolutionRows

    $allRoundRows = New-Object System.Collections.Generic.List[object]
    for ($round = 1; $round -le $effectiveMaxRounds; $round++) {
        $pct = [int](($round / $effectiveMaxRounds) * 100)
        Write-Progress -Activity "VIA Safe Polyglot Optimizer" -Status "Round $round / $effectiveMaxRounds" -PercentComplete $pct
        def_WriteLine "ROUND" "Panoramic analysis round $round / $effectiveMaxRounds"
        $roundRows = def_RunRound -Round $round -RunDir $runDir -SandboxRows $sandboxRows
        foreach ($r in $roundRows) { $allRoundRows.Add($r) | Out-Null }
    }
    Write-Progress -Activity "VIA Safe Polyglot Optimizer" -Completed

    $selfTestRows = def_RunOptionalSandboxSelfTest -RunDir $runDir -SandboxRows $sandboxRows
    if ($SelfTest) {
        $own = def_RunSelfTest -ScriptPath $MyInvocation.MyCommand.Path
        $ownCsv = Join-Path (Join-Path $runDir "reports") "00_AIO_SelfTest.csv"
        $own | Export-Csv -LiteralPath $ownCsv -NoTypeInformation -Encoding UTF8
        foreach ($o in $own) {
            $risk = if ($o.Pass) { "LOW" } else { "HIGH" }
            $allRoundRows.Add([pscustomobject]@{
                Round = 0
                Phase = "AIO_SELFTEST"
                Layer = "SELFTEST"
                Item = $o.Check
                Status = $o.Status
                Risk = $risk
                Class = def_ClassifyIssue -Category "SELFTEST" -Risk $risk -Message $o.Check
                Message = "AIO self-test check result: $($o.Pass)"
                Path = $MyInvocation.MyCommand.Path
            }) | Out-Null
        }
    }

    $reportDir = Join-Path $runDir "reports"
    $inputRows | Export-Csv -LiteralPath (Join-Path $reportDir "01_InputManifest.csv") -NoTypeInformation -Encoding UTF8
    $sandboxRows | Export-Csv -LiteralPath (Join-Path $reportDir "02_SandboxCopies.csv") -NoTypeInformation -Encoding UTF8
    $allRoundRows | Export-Csv -LiteralPath (Join-Path $reportDir "03_ThreeRoundMatrix.csv") -NoTypeInformation -Encoding UTF8
    $toolRows | Export-Csv -LiteralPath (Join-Path $reportDir "04_ToolMatrix_Top15.csv") -NoTypeInformation -Encoding UTF8
    $failureRows | Export-Csv -LiteralPath (Join-Path $reportDir "05_Top25FailuresSolutions.csv") -NoTypeInformation -Encoding UTF8
    $policyRows | Export-Csv -LiteralPath (Join-Path $reportDir "06_SafetyPolicy.csv") -NoTypeInformation -Encoding UTF8
    $selfTestRows | Export-Csv -LiteralPath (Join-Path $reportDir "07_SandboxSelfTest.csv") -NoTypeInformation -Encoding UTF8

    def_ToJsonFile -Path (Join-Path $reportDir "03_ThreeRoundMatrix.json") -Object $allRoundRows -Depth 16
    def_ToJsonFile -Path (Join-Path $reportDir "04_ToolMatrix_Top15.json") -Object $toolRows -Depth 16
    def_ToJsonFile -Path (Join-Path $reportDir "05_Top25FailuresSolutions.json") -Object $failureRows -Depth 16

    $htmlPath = def_WriteHtmlReport -RunDir $runDir -InputRows $inputRows -SandboxRows $sandboxRows -RoundRows $allRoundRows -ToolRows $toolRows -FailureRows $failureRows -SelfTestRows $selfTestRows -PolicyRows $policyRows
    $reg = def_WriteRegistryAndPointer -RunDir $runDir -InputRows $inputRows -MatrixRows $allRoundRows -HtmlPath $htmlPath

    $launcherPath = ""
    if ($RegisterLauncher) {
        $launcherPath = def_WriteLauncher -ScriptPath $MyInvocation.MyCommand.Path
    }

    $optimizerHtml = def_FindOperationOptimizerHtml
    if (-not [string]::IsNullOrWhiteSpace($optimizerHtml)) {
        try {
            $copyHtml = Join-Path (Join-Path $runDir "reports") (Split-Path -Leaf $optimizerHtml)
            Copy-Item -LiteralPath $optimizerHtml -Destination $copyHtml -Force
            def_WriteLine "OK" "Existing OperationOptimizer HTML copied: $copyHtml"
        }
        catch {
            def_WriteLine "WARN" "Could not copy OperationOptimizer HTML: $($_.Exception.Message)"
        }
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "def VIA SAFE POLYGLOT OPTIMIZER COMPLETE" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "Status       : $script:def_STATUS"
    Write-Host "Risk         : $script:def_RISK"
    Write-Host "RunDir       : $runDir"
    Write-Host "HTML         : $htmlPath"
    Write-Host "Registry     : $($reg.RegistryPath)"
    Write-Host "Pointer      : $($reg.PointerPath)"
    if (-not [string]::IsNullOrWhiteSpace($launcherPath)) { Write-Host "Launcher     : $launcherPath" }
    Write-Host "Policy       : Report-only by default. No files deleted. No processes stopped."

    if ($OpenReport -and -not $NoBrowser -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process $htmlPath
    }
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell remains open. No destructive action was requested by this tool." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
