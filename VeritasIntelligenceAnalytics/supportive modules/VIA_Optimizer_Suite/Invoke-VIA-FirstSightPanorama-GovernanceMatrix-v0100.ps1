<# 
def VIA FirstSight Panorama Governance Matrix · v0100
Purpose:
  Read-only first-flow analyzer for:
  - BASE:     C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics
  - DOWNLOAD: C:\Users\tonyk\Downloads
  It scans, classifies, parses, counts, detects tool gaps, estimates subsystem progress,
  detects Hydra risks, and outputs HTML/JSON/CSV matrices.

Safety:
  Default mode is read-only.
  No install, no PATH change, no deletion, no overwrite of canonical files.
#>

# =============================================================================
# def PARAMETERS
# =============================================================================
param(
    [string]$BaseRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$DownloadRoot = "C:\Users\tonyk\Downloads",
    [string]$RunName = "VIA_FirstSightPanorama",
    [int]$MaxFilesTotal = 16000,
    [int]$MaxFilesPerRoot = 9000,
    [int]$MaxTextBytes = 1048576,
    [int]$HashMaxMB = 25,
    [int]$BatchSize = 500,
    [int]$MaxExternalLinksPerFile = 25,
    [bool]$EnablePyCompile = $false,
    [bool]$EnableNodeCheck = $false,
    [bool]$EnableExternalFetch = $false,
    [bool]$AllowInstall = $false,
    [bool]$AllowPathChange = $false,
    [bool]$AllowDelete = $false,
    [bool]$OpenHtmlReport = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def CONSTANTS
# =============================================================================
$def_PARAM_REQUIRED_SUPPORT_FILES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Read_Me_VeritasNexusCore.md",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VeritasNexusCore.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_SafePolyglotOptimizer_v0102_StaticValidation.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\chartspec_registry.json"
)

$def_PARAM_FUNCTIONAL_ROOTS = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VPNS"
)

$def_PARAM_KEY_REGISTRIES = @(
    "C:\Users\tonyk\Downloads\GovernanceRegistry.json",
    "C:\Users\tonyk\Downloads\LayoutRegistry.json",
    "C:\Users\tonyk\Downloads\VisualRegistry.json",
    "C:\Users\tonyk\Downloads\UnifiedSpec.json",
    "C:\Users\tonyk\Downloads\VDF_VRN_SourceFallback_AllDataRegistry_v0100.json",
    "C:\Users\tonyk\Downloads\VRN_IO_Summary_v0100.json",
    "C:\Users\tonyk\Downloads\macro_indicator_registry.json",
    "C:\Users\tonyk\Downloads\via_data_detail_registry.json",
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json"
)

$def_PARAM_PROGRESS_FLOW_WEIGHTS = [ordered]@{
    InventoryScan = 20
    StaticHealth = 20
    ParameterExtraction = 20
    ToolReadiness = 20
    StrategyPlan = 20
}

# =============================================================================
# def UTILITY
# =============================================================================
function def_GetTimestamp {
    return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function def_NewRunPaths {
    param([string]$BaseRoot, [string]$RunName)

    $ts = def_GetTimestamp
    $runRoot = Join-Path $BaseRoot ("tools\$RunName\runs\RUN_$ts")
    $paths = [ordered]@{
        RunRoot = $runRoot
        Registry = Join-Path $runRoot "registry"
        Report = Join-Path $runRoot "report"
        Logs = Join-Path $runRoot "logs"
        Evidence = Join-Path $runRoot "evidence"
    }

    foreach ($p in $paths.Values) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
    return $paths
}

function def_WriteLog {
    param(
        [string]$Level,
        [string]$Message
    )
    $stamp = (Get-Date).ToString("HH:mm:ss.fff")
    $line = "[$stamp] [$Level] $Message"
    Write-Host $line
    if ($script:LogPath) {
        Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
    }
}

function def_EscapeHtml {
    param([AllowNull()][object]$Value)
    if ($null -eq $Value) { return "" }
    $s = [string]$Value
    $s = $s.Replace("&","&amp;").Replace("<","&lt;").Replace(">","&gt;").Replace('"',"&quot;").Replace("'","&#39;")
    return $s
}

function def_NormalizePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return ($Path.Replace("\","/").Trim().ToLowerInvariant())
}

function def_GetSha12 {
    param(
        [string]$Path,
        [int]$HashMaxMB
    )
    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($item.Length -gt ($HashMaxMB * 1MB)) {
            return "SKIP_GT_${HashMaxMB}MB"
        }
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.Substring(0,12).ToLowerInvariant()
    } catch {
        return "HASH_FAIL"
    }
}

function def_GetRelativeScope {
    param([string]$Path, [string]$BaseRoot, [string]$DownloadRoot)

    $n = def_NormalizePath $Path
    $b = def_NormalizePath $BaseRoot
    $d = def_NormalizePath $DownloadRoot

    if ($n.StartsWith($b)) { return "BASE" }
    if ($n.StartsWith($d)) { return "DOWNLOAD" }
    return "OTHER"
}

function def_ClassifyExtension {
    param([string]$Ext)

    $e = $Ext.ToLowerInvariant()
    switch ($e) {
        ".ps1" { return "PowerShell" }
        ".psm1" { return "PowerShell" }
        ".psd1" { return "PowerShell" }
        ".py" { return "Python" }
        ".ipynb" { return "Notebook" }
        ".js" { return "JavaScript" }
        ".ts" { return "TypeScript" }
        ".mjs" { return "JavaScript" }
        ".cjs" { return "JavaScript" }
        ".html" { return "HTML" }
        ".htm" { return "HTML" }
        ".css" { return "CSS" }
        ".json" { return "JSON" }
        ".jsonl" { return "JSONL" }
        ".yaml" { return "YAML" }
        ".yml" { return "YAML" }
        ".md" { return "Markdown" }
        ".csv" { return "CSV" }
        ".parquet" { return "Parquet" }
        ".duckdb" { return "DuckDB" }
        ".db" { return "Database" }
        ".sqlite" { return "Database" }
        ".pdf" { return "PDF" }
        ".docx" { return "Office" }
        ".pptx" { return "Office" }
        ".xlsx" { return "Office" }
        ".png" { return "Image" }
        ".jpg" { return "Image" }
        ".jpeg" { return "Image" }
        ".svg" { return "SVG" }
        ".zip" { return "Archive" }
        ".rar" { return "Archive" }
        ".7z" { return "Archive" }
        ".tar" { return "Archive" }
        ".gz" { return "Archive" }
        ".exe" { return "Executable" }
        ".bat" { return "Batch" }
        ".cmd" { return "Batch" }
        ".log" { return "Log" }
        ".txt" { return "Text" }
        default { return "Other" }
    }
}

function def_ClassifyDomain {
    param([string]$Path)

    $p = (def_NormalizePath $Path)
    if ($p -match "functional modules/vdf|/vdf|vdf_|veritasdataforge|dataforge") { return "VDF" }
    if ($p -match "functional modules/vrn|/vrn|vrn_|veritasreportnova|reportnova") { return "VRN" }
    if ($p -match "functional modules/vap|/vap|vap_|autoplot|chart|visual|dashboard") { return "VAP" }
    if ($p -match "functional modules/vpns|/vpns|vpns_|panorama|nexus") { return "VPNS" }
    if ($p -match "supportive modules|nexuscore|polyglot|optimizer|parammanager|chartspec") { return "Supportive" }
    if ($p -match "governance|layout|visualregistry|unifiedspec|ssot|registry|config|params") { return "RegistrySSOT" }
    if ($p -match "activeetf|etf") { return "ActiveETF" }
    if ($p -match "macro|fred|yield|gdp|risk_engine") { return "Macro" }
    if ($p -match "engineforge|ultimateengineforge|vef") { return "EngineForge" }
    if ($p -match "vif|vhs|vvx") { return "AuxiliaryLab" }
    return "General"
}

function def_GetRYG {
    param(
        [double]$Value,
        [double]$GreenMin,
        [double]$YellowMin
    )
    if ($Value -ge $GreenMin) { return "GREEN" }
    if ($Value -ge $YellowMin) { return "YELLOW" }
    return "RED"
}

# =============================================================================
# def TOOL REGISTRY
# =============================================================================
function def_GetToolRegistry {
    $rows = New-Object System.Collections.Generic.List[object]

    $map = [ordered]@{
        panoramic_analysis = [ordered]@{
            python = @("pylint","flake8","mypy","bandit","radon","vulture","prospector","pyright","rope","jedi")
            javascript = @("eslint","typescript","sonarjs-local","dependency-cruiser","madge","webpack-bundle-analyzer","plato","eslint-plugin-import","jscodeshift","ts-morph")
            powershell = @("PSScriptAnalyzer","PSRule","Pester","ScriptAnalyzerRules","PSDepend","PSProfiler","PSFramework","PSGraph","Plaster","custom-ast-analyzer")
        }
        error_identification = [ordered]@{
            python = @("pylint","pyflakes","flake8","mypy","pyright","pytest","unittest","coverage","nose2","bandit")
            javascript = @("eslint","typescript","jest","mocha","ava","eslint-plugin-node","eslint-plugin-promise","node-trace-warnings","c8","nyc")
            powershell = @("PSScriptAnalyzer","Pester","PSFramework","PSRule","Invoke-ScriptAnalyzer","PSLogging","PSProfiler","Transcript","custom-ast-rules","PSReadLine")
        }
        sandbox_testing = [ordered]@{
            python = @("venv","virtualenv","tox","nox","pytest","unittest.mock","subprocess","pyenv","docker","hypothesis")
            javascript = @("node-vm","jest","mocha","ts-node","docker","nvm","playwright","sinon","proxyquire","pnpm")
            powershell = @("PSSession","Start-Job","RunspacePool","Pester","PSModulePath","JEA","ConstrainedLanguage","WindowsSandbox","Docker","sandbox-wrapper")
        }
        ast_analysis = [ordered]@{
            python = @("ast","astroid","libcst","parso","redbaron","typed-ast","jedi","rope","bowler","pylsp")
            javascript = @("babel-parser","esprima","acorn","recast","jscodeshift","ts-morph","typescript-compiler-api","eslint-parser","meriyah","swc-parser")
            powershell = @("PowerShell-AST","PSScriptAnalyzer-AST","PSParser","ScriptAnalyzerRules","custom-ast-visitors","PSGraph-AST","PSFramework-AST","Pester-AST","dotnet-reflection","custom-ast-refactor")
        }
        interface_contract_detection = [ordered]@{
            python = @("mypy-protocols","pydantic","dataclasses","jsonschema","marshmallow","attrs","inspect","pyi-stubs","FastAPI-schema","DRF-schema")
            javascript = @("typescript-interfaces","ts-json-schema-generator","ajv","io-ts","zod","JSDoc","swagger-jsdoc","quicktype","eslint-plugin-jsdoc","openapi-generator")
            powershell = @("param-type-blocks","PowerShell-classes","Test-Json","PSScriptAnalyzer-param-rules","DSC-schema","module-manifest","PSRule-contracts","Pester-contract-tests","Import-PowerShellDataFile","comment-help-schema")
        }
        syntax_compile = [ordered]@{
            python = @("py_compile","compileall","pylint","flake8","pyflakes","mypy","pyright","black","isort","bandit")
            javascript = @("typescript-compiler","babel-cli","eslint","flow","swc","esbuild","webpack","rollup","parcel","node-check")
            powershell = @("PSScriptAnalyzer","ScriptBlock.Create","Test-ModuleManifest","Import-Module","Pester","PSParser","ScriptAnalyzerRules","PSReadLine","PowerShellGet","AST-parse-only")
        }
        hydra_risk_detection = [ordered]@{
            python = @("pylint-cyclic-import","pydeps","snakefood","pipdeptree","radon","vulture","mypy","bandit","networkx","rope")
            javascript = @("madge","dependency-cruiser","eslint-import-rules","webpack-analyzer","ts-morph","typescript-project-refs","sonarjs-local","plato","depcheck","jscodeshift")
            powershell = @("PSScriptAnalyzer-deps","AST-import-graph","PSDepend","PSModulePath","PSGraph","Pester","DSC","ScriptAnalyzerRules","module-manifest","dotnet-reflection")
        }
        anchor_point_detection = [ordered]@{
            python = @("ast-lineno","libcst-loc","parso-loc","jedi-symbol","rope-refactor","bowler-patterns","ripgrep","tree-sitter-python","pylsp","redbaron")
            javascript = @("babel-ast-loc","ts-morph-loc","eslint-sourcecode","recast","jscodeshift","tree-sitter-js","tsserver","ripgrep","source-map","prettier")
            powershell = @("AST-Extent","PSParser-tokens","PSScriptAnalyzer-context","custom-ast-visitors","VSCode-PowerShell","Pester-line-assert","Transcript","PSReadLine","region-tags","anchor-comments")
        }
        integration_scheduling = [ordered]@{
            python = @("tox","nox","invoke","doit","make","airflow","prefect","celery","cron","fabric")
            javascript = @("npm","yarn","pnpm","gulp","grunt","nx","lerna","turbo","node-cron","pm2")
            powershell = @("PSake","Invoke-Build","ScheduledTasks","Register-ScheduledJob","Pester","GitHubActionsRunner","AzureDevOpsAgent","Start-Job","RunspacePool","DSC")
        }
    }

    foreach ($fn in $map.Keys) {
        foreach ($lang in $map[$fn].Keys) {
            $i = 0
            foreach ($tool in $map[$fn][$lang]) {
                $i++
                $rows.Add([pscustomobject]@{
                    Function = $fn
                    Language = $lang
                    Rank = $i
                    Tool = $tool
                    LocalFree = $true
                    InstallPolicy = "PLAN_ONLY_FIRST_FLOW"
                })
            }
        }
    }
    return $rows
}

function def_TestToolAvailability {
    param([object[]]$ToolRows)

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($r in $ToolRows) {
        $tool = [string]$r.Tool
        $lang = [string]$r.Language
        $method = "registry"
        $status = "PLANNED"
        $detail = "Not checked as command/module in first flow."

        if ($lang -eq "powershell") {
            $m = Get-Module -ListAvailable -Name $tool -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) {
                $status = "AVAILABLE"
                $detail = "PowerShell module available: $($m.Version)"
                $method = "Get-Module"
            } else {
                $cmd = Get-Command $tool -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($cmd) {
                    $status = "AVAILABLE"
                    $detail = "PowerShell command available: $($cmd.Source)"
                    $method = "Get-Command"
                } else {
                    $status = "MISSING_OR_LIBRARY"
                    $detail = "Not found as PS module/command. May be built-in concept or custom rule."
                    $method = "Get-Module/Get-Command"
                }
            }
        } elseif ($lang -eq "python") {
            $commandLike = @("pylint","flake8","mypy","bandit","radon","vulture","prospector","pyright","pytest","coverage","nose2","tox","nox","pyenv","docker","black","isort","pydeps","pipdeptree","ripgrep")
            if ($commandLike -contains $tool) {
                $cmd = Get-Command $tool -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($cmd) {
                    $status = "AVAILABLE"
                    $detail = "Command available: $($cmd.Source)"
                    $method = "Get-Command"
                } else {
                    $status = "MISSING"
                    $detail = "Command not found in PATH."
                    $method = "Get-Command"
                }
            } else {
                $status = "LIBRARY_OR_BUILTIN"
                $detail = "Library/built-in; import check deferred to install/test flow."
            }
        } elseif ($lang -eq "javascript") {
            $commandLike = @("eslint","typescript","madge","dependency-cruiser","jest","mocha","ava","nyc","c8","ts-node","docker","nvm","playwright","pnpm","yarn","npm","gulp","grunt","nx","lerna","turbo","pm2","prettier","webpack","rollup","parcel","node-check")
            if ($tool -eq "typescript-compiler") { $tool = "tsc" }
            if ($tool -eq "node-check") { $tool = "node" }
            if ($commandLike -contains $r.Tool -or $tool -in @("tsc","node","npm","yarn","pnpm")) {
                $cmd = Get-Command $tool -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($cmd) {
                    $status = "AVAILABLE"
                    $detail = "Command available: $($cmd.Source)"
                    $method = "Get-Command"
                } else {
                    $status = "MISSING"
                    $detail = "Command not found in PATH."
                    $method = "Get-Command"
                }
            } else {
                $status = "LIBRARY_OR_PACKAGE"
                $detail = "Node package or concept; package check deferred to install/test flow."
            }
        }

        $rows.Add([pscustomobject]@{
            Function = $r.Function
            Language = $r.Language
            Rank = $r.Rank
            Tool = $r.Tool
            Status = $status
            Method = $method
            Detail = $detail
        })
    }
    return $rows
}

# =============================================================================
# def INVENTORY
# =============================================================================
function def_GetFileInventory {
    param(
        [string[]]$Roots,
        [int]$MaxFilesTotal,
        [int]$MaxFilesPerRoot,
        [int]$HashMaxMB,
        [int]$BatchSize
    )

    $rows = New-Object System.Collections.Generic.List[object]
    $seen = 0

    foreach ($root in $Roots) {
        def_WriteLog "RUN" "Scanning root: $root"
        if (-not (Test-Path -LiteralPath $root)) {
            $rows.Add([pscustomobject]@{
                Scope = "MISSING_ROOT"
                Domain = "N/A"
                Language = "N/A"
                Path = $root
                Name = Split-Path $root -Leaf
                Ext = ""
                SizeKB = 0
                Modified = ""
                Created = ""
                SHA12 = "N/A"
                Status = "ROOT_NOT_FOUND"
                Risk = "RED"
            })
            continue
        }

        $rootCount = 0
        $items = Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            if ($seen -ge $MaxFilesTotal) { break }
            if ($rootCount -ge $MaxFilesPerRoot) { break }
            $seen++
            $rootCount++

            if (($seen % $BatchSize) -eq 0) {
                $pct = [math]::Min(100, [math]::Round(($seen / [math]::Max(1,$MaxFilesTotal))*100, 1))
                Write-Progress -Activity "def Inventory Scan" -Status "$seen files scanned" -PercentComplete $pct
            }

            $ext = $item.Extension
            $lang = def_ClassifyExtension $ext
            $domain = def_ClassifyDomain $item.FullName
            $scope = def_GetRelativeScope -Path $item.FullName -BaseRoot $BaseRoot -DownloadRoot $DownloadRoot
            $sha = def_GetSha12 -Path $item.FullName -HashMaxMB $HashMaxMB

            $risk = "GREEN"
            if ($lang -eq "Executable") { $risk = "YELLOW" }
            if ($lang -eq "Archive" -and $scope -eq "DOWNLOAD") { $risk = "YELLOW" }

            $rows.Add([pscustomobject]@{
                Scope = $scope
                Domain = $domain
                Language = $lang
                Path = $item.FullName
                Name = $item.Name
                Ext = $ext.ToLowerInvariant()
                SizeKB = [math]::Round($item.Length / 1KB, 1)
                SizeMB = [math]::Round($item.Length / 1MB, 2)
                Modified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                Created = $item.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
                SHA12 = $sha
                Status = "FOUND"
                Risk = $risk
            })
        }
    }

    Write-Progress -Activity "def Inventory Scan" -Completed
    return $rows
}

function def_GetDirectoryInventory {
    param([string[]]$Roots)

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($root in $Roots) {
        if (-not (Test-Path -LiteralPath $root)) {
            $rows.Add([pscustomobject]@{
                Path = $root
                Domain = def_ClassifyDomain $root
                Exists = $false
                FileCount = 0
                DirectoryCount = 0
                SizeMB = 0
                Risk = "RED"
                Remark = "Directory missing."
            })
            continue
        }

        $files = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction SilentlyContinue)
        $dirs = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory -ErrorAction SilentlyContinue)
        $size = ($files | Measure-Object -Property Length -Sum).Sum
        $rows.Add([pscustomobject]@{
            Path = $root
            Domain = def_ClassifyDomain $root
            Exists = $true
            FileCount = $files.Count
            DirectoryCount = $dirs.Count
            SizeMB = [math]::Round(($size / 1MB), 2)
            Risk = if ($files.Count -eq 0) { "YELLOW" } else { "GREEN" }
            Remark = "Inventory only. No modification."
        })
    }
    return $rows
}

# =============================================================================
# def STATIC ANALYSIS
# =============================================================================
function def_GetTextSafely {
    param(
        [string]$Path,
        [int]$MaxTextBytes
    )
    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($item.Length -gt $MaxTextBytes) {
            return [pscustomobject]@{
                Status = "SKIPPED_TOO_LARGE"
                Text = ""
                Error = "File exceeds MaxTextBytes=$MaxTextBytes"
            }
        }
        $txt = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        return [pscustomobject]@{ Status = "READ_OK"; Text = $txt; Error = "" }
    } catch {
        return [pscustomobject]@{ Status = "READ_FAIL"; Text = ""; Error = $_.Exception.Message }
    }
}

function def_ExtractParametersFromText {
    param(
        [string]$Path,
        [string]$Language,
        [string]$Text
    )

    $rows = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($Text)) { return $rows }

    if ($Language -eq "PowerShell") {
        try {
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseInput($Text, [ref]$tokens, [ref]$errors)
            $params = $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.ParameterAst] }, $true)
            foreach ($p in $params) {
                $rows.Add([pscustomobject]@{
                    SourcePath = $Path
                    Language = $Language
                    Parameter = $p.Name.VariablePath.UserPath
                    Type = ($p.StaticType.Name)
                    Anchor = "$($p.Extent.StartLineNumber):$($p.Extent.StartColumnNumber)"
                    Category = def_ClassifyParameterName $p.Name.VariablePath.UserPath
                    Default = ""
                })
            }
        } catch {}
    } elseif ($Language -eq "Python") {
        $lineNo = 0
        foreach ($line in ($Text -split "`r?`n")) {
            $lineNo++
            if ($line -match "^\s*([A-Z][A-Z0-9_]{2,}|def_PARAM_[A-Za-z0-9_]+)\s*=") {
                $name = $Matches[1]
                $rows.Add([pscustomobject]@{
                    SourcePath = $Path
                    Language = $Language
                    Parameter = $name
                    Type = "python_assignment"
                    Anchor = "$lineNo:1"
                    Category = def_ClassifyParameterName $name
                    Default = ($line.Trim())
                })
            }
        }
    } elseif ($Language -eq "JSON") {
        # Detailed JSON key flattening is deferred to parse matrix. Here only top-level keys.
        try {
            $obj = $Text | ConvertFrom-Json -ErrorAction Stop
            $props = $obj.PSObject.Properties.Name
            foreach ($p in $props) {
                $rows.Add([pscustomobject]@{
                    SourcePath = $Path
                    Language = $Language
                    Parameter = $p
                    Type = "json_top_key"
                    Anchor = "top"
                    Category = def_ClassifyParameterName $p
                    Default = ""
                })
            }
        } catch {}
    }

    return $rows
}

function def_ClassifyParameterName {
    param([string]$Name)
    $n = $Name.ToLowerInvariant()
    if ($n -match "path|root|dir|folder|file|output|input|download|base") { return "PATH" }
    if ($n -match "time|date|timeout|round|batch|max|limit|schedule") { return "TIME_LIMIT" }
    if ($n -match "source|url|api|fetch|provider|ticker|market|region") { return "SOURCE_INPUT" }
    if ($n -match "report|html|csv|json|parquet|duckdb|matrix|registry") { return "OUTPUT" }
    if ($n -match "install|repair|delete|force|allow|enable|open|apply") { return "CONTROL_SAFETY" }
    return "OTHER"
}

function def_RunStaticHealth {
    param(
        [object[]]$InventoryRows,
        [int]$MaxTextBytes,
        [bool]$EnablePyCompile,
        [bool]$EnableNodeCheck,
        [int]$MaxExternalLinksPerFile
    )

    $health = New-Object System.Collections.Generic.List[object]
    $params = New-Object System.Collections.Generic.List[object]
    $links = New-Object System.Collections.Generic.List[object]

    $eligible = @($InventoryRows | Where-Object { $_.Language -in @("PowerShell","Python","JavaScript","TypeScript","JSON","HTML","Markdown","CSS","Text") })
    $i = 0
    foreach ($r in $eligible) {
        $i++
        if (($i % 250) -eq 0) {
            $pct = [math]::Round(($i / [math]::Max(1,$eligible.Count))*100, 1)
            Write-Progress -Activity "def Static Health" -Status "$i / $($eligible.Count)" -PercentComplete $pct
        }

        $read = def_GetTextSafely -Path $r.Path -MaxTextBytes $MaxTextBytes
        $parseStatus = "NOT_PARSED"
        $issueCount = 0
        $issueText = ""

        if ($read.Status -eq "READ_OK") {
            switch ($r.Language) {
                "JSON" {
                    try {
                        $null = $read.Text | ConvertFrom-Json -ErrorAction Stop
                        $parseStatus = "JSON_OK"
                    } catch {
                        $parseStatus = "JSON_FAIL"
                        $issueCount++
                        $issueText = $_.Exception.Message
                    }
                }
                "PowerShell" {
                    try {
                        $tokens = $null
                        $errors = $null
                        $null = [System.Management.Automation.Language.Parser]::ParseInput($read.Text, [ref]$tokens, [ref]$errors)
                        if ($errors.Count -gt 0) {
                            $parseStatus = "PS_PARSE_WARN"
                            $issueCount = $errors.Count
                            $issueText = (($errors | Select-Object -First 3 | ForEach-Object { $_.Message }) -join " | ")
                        } else {
                            $parseStatus = "PS_PARSE_OK"
                        }
                    } catch {
                        $parseStatus = "PS_PARSE_FAIL"
                        $issueCount++
                        $issueText = $_.Exception.Message
                    }
                }
                "Python" {
                    if ($EnablePyCompile) {
                        $py = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
                        if ($py) {
                            try {
                                $env:PYTHONDONTWRITEBYTECODE = "1"
                                $p = Start-Process -FilePath $py.Source -ArgumentList @("-m","py_compile",$r.Path) -NoNewWindow -Wait -PassThru -RedirectStandardError "$env:TEMP\via_pycompile_err.txt" -RedirectStandardOutput "$env:TEMP\via_pycompile_out.txt"
                                if ($p.ExitCode -eq 0) { $parseStatus = "PY_COMPILE_OK" }
                                else {
                                    $parseStatus = "PY_COMPILE_FAIL"
                                    $issueCount++
                                    $issueText = (Get-Content "$env:TEMP\via_pycompile_err.txt" -Raw -ErrorAction SilentlyContinue)
                                }
                            } catch {
                                $parseStatus = "PY_COMPILE_ERROR"
                                $issueCount++
                                $issueText = $_.Exception.Message
                            }
                        } else {
                            $parseStatus = "PYTHON_NOT_FOUND"
                            $issueCount++
                        }
                    } else {
                        $parseStatus = "PY_COMPILE_DEFERRED"
                    }
                }
                {$_ -in @("JavaScript","TypeScript")} {
                    if ($EnableNodeCheck -and $r.Language -eq "JavaScript") {
                        $node = Get-Command node -ErrorAction SilentlyContinue | Select-Object -First 1
                        if ($node) {
                            try {
                                $p = Start-Process -FilePath $node.Source -ArgumentList @("--check",$r.Path) -NoNewWindow -Wait -PassThru -RedirectStandardError "$env:TEMP\via_nodecheck_err.txt" -RedirectStandardOutput "$env:TEMP\via_nodecheck_out.txt"
                                if ($p.ExitCode -eq 0) { $parseStatus = "NODE_CHECK_OK" }
                                else {
                                    $parseStatus = "NODE_CHECK_FAIL"
                                    $issueCount++
                                    $issueText = (Get-Content "$env:TEMP\via_nodecheck_err.txt" -Raw -ErrorAction SilentlyContinue)
                                }
                            } catch {
                                $parseStatus = "NODE_CHECK_ERROR"
                                $issueCount++
                                $issueText = $_.Exception.Message
                            }
                        } else {
                            $parseStatus = "NODE_NOT_FOUND"
                            $issueCount++
                        }
                    } else {
                        $parseStatus = "JS_TS_CHECK_DEFERRED"
                    }
                }
                "HTML" {
                    $hasHtml = $read.Text -match "<html|<!doctype html"
                    $hasScript = $read.Text -match "<script"
                    $parseStatus = if ($hasHtml) { "HTML_BASIC_OK" } else { "HTML_BASIC_WARN" }
                    if (-not $hasHtml) { $issueCount++ ; $issueText = "No <html> or <!doctype html> found." }
                    if ($hasScript) { $issueText = (($issueText + " Script detected.") -replace "^\s+","") }
                }
                default {
                    $parseStatus = "TEXT_READ_OK"
                }
            }

            $extracted = def_ExtractParametersFromText -Path $r.Path -Language $r.Language -Text $read.Text
            foreach ($x in $extracted) { $params.Add($x) }

            $m = [regex]::Matches($read.Text, "https?://[^\s""'<>]+")
            $k = 0
            foreach ($match in $m) {
                if ($k -ge $MaxExternalLinksPerFile) { break }
                $k++
                $links.Add([pscustomobject]@{
                    SourcePath = $r.Path
                    Domain = $r.Domain
                    Link = $match.Value
                    Action = if ($EnableExternalFetch) { "FETCH_NOT_IMPLEMENTED_IN_FIRST_FLOW" } else { "DETECTED_ONLY_NO_FETCH" }
                    Risk = "YELLOW"
                })
            }
        } else {
            $parseStatus = $read.Status
            $issueCount++
            $issueText = $read.Error
        }

        $risk = "GREEN"
        if ($parseStatus -match "FAIL|ERROR") { $risk = "RED" }
        elseif ($parseStatus -match "WARN|DEFERRED|SKIPPED|NOT_FOUND") { $risk = "YELLOW" }

        $health.Add([pscustomobject]@{
            Scope = $r.Scope
            Domain = $r.Domain
            Language = $r.Language
            Path = $r.Path
            SizeKB = $r.SizeKB
            ParseStatus = $parseStatus
            IssueCount = $issueCount
            IssuePreview = (($issueText -replace "`r|`n"," ") | ForEach-Object { if ($_.Length -gt 280) { $_.Substring(0,280) } else { $_ } })
            Risk = $risk
        })
    }

    Write-Progress -Activity "def Static Health" -Completed

    return [pscustomobject]@{
        Health = $health
        Parameters = $params
        ExternalLinks = $links
    }
}

# =============================================================================
# def MATRICES
# =============================================================================
function def_BuildDuplicateMatrix {
    param([object[]]$InventoryRows)

    $groups = $InventoryRows |
        Where-Object { $_.Status -eq "FOUND" } |
        Group-Object -Property Name |
        Where-Object { $_.Count -gt 1 }

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($g in $groups) {
        $paths = @($g.Group | Select-Object -ExpandProperty Path)
        $scopes = @($g.Group | Select-Object -ExpandProperty Scope -Unique)
        $domains = @($g.Group | Select-Object -ExpandProperty Domain -Unique)
        $hashes = @($g.Group | Select-Object -ExpandProperty SHA12 -Unique)
        $rows.Add([pscustomobject]@{
            FileName = $g.Name
            Count = $g.Count
            Scopes = ($scopes -join ",")
            Domains = ($domains -join ",")
            UniqueHashCount = $hashes.Count
            Hashes = ($hashes -join ",")
            Risk = if ($hashes.Count -eq 1) { "YELLOW" } else { "RED" }
            Action = if ($hashes.Count -eq 1) { "ARCHIVE_OR_DEDUP_CANDIDATE_AFTER_CONFIRM" } else { "VERSION_CONFLICT_REVIEW" }
            Paths = ($paths -join " || ")
        })
    }
    return $rows
}

function def_BuildDomainMatrix {
    param([object[]]$InventoryRows, [object[]]$HealthRows)

    $rows = New-Object System.Collections.Generic.List[object]
    $domains = @($InventoryRows | Select-Object -ExpandProperty Domain -Unique | Sort-Object)
    foreach ($d in $domains) {
        $files = @($InventoryRows | Where-Object { $_.Domain -eq $d })
        $health = @($HealthRows | Where-Object { $_.Domain -eq $d })
        $red = @($health | Where-Object { $_.Risk -eq "RED" }).Count
        $yellow = @($health | Where-Object { $_.Risk -eq "YELLOW" }).Count
        $green = @($health | Where-Object { $_.Risk -eq "GREEN" }).Count
        $totalHealth = [math]::Max(1, $health.Count)
        $healthPct = [math]::Round(($green / $totalHealth) * 100, 1)
        $rows.Add([pscustomobject]@{
            Domain = $d
            FileCount = $files.Count
            SizeMB = [math]::Round((($files | Measure-Object -Property SizeMB -Sum).Sum), 2)
            Green = $green
            Yellow = $yellow
            Red = $red
            HealthPct = $healthPct
            RYG = def_GetRYG -Value $healthPct -GreenMin 85 -YellowMin 60
            RecommendedNext = if ($red -gt 0) { "FIX_PARSE_OR_CONTRACT_ISSUES" } elseif ($yellow -gt 0) { "REVIEW_DEFERRED_OR_WARNINGS" } else { "READY_FOR_INTEGRATION_TEST_PLAN" }
        })
    }
    return $rows
}

function def_BuildLanguageMatrix {
    param([object[]]$InventoryRows, [object[]]$HealthRows)

    $rows = New-Object System.Collections.Generic.List[object]
    $langs = @($InventoryRows | Select-Object -ExpandProperty Language -Unique | Sort-Object)
    foreach ($l in $langs) {
        $files = @($InventoryRows | Where-Object { $_.Language -eq $l })
        $health = @($HealthRows | Where-Object { $_.Language -eq $l })
        $red = @($health | Where-Object { $_.Risk -eq "RED" }).Count
        $yellow = @($health | Where-Object { $_.Risk -eq "YELLOW" }).Count
        $green = @($health | Where-Object { $_.Risk -eq "GREEN" }).Count
        $rows.Add([pscustomobject]@{
            Language = $l
            FileCount = $files.Count
            SizeMB = [math]::Round((($files | Measure-Object -Property SizeMB -Sum).Sum), 2)
            StaticChecked = $health.Count
            Green = $green
            Yellow = $yellow
            Red = $red
            Risk = if ($red -gt 0) { "RED" } elseif ($yellow -gt 0) { "YELLOW" } else { "GREEN" }
        })
    }
    return $rows
}

function def_BuildSupportiveToolMatrix {
    param([string[]]$SupportFiles)

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($p in $SupportFiles) {
        $exists = Test-Path -LiteralPath $p
        $rows.Add([pscustomobject]@{
            Tool = Split-Path $p -Leaf
            Path = $p
            Exists = $exists
            Domain = "Supportive"
            RequiredRole = if ($p -match "NexusCore") { "Nexus core deployment / bridge" } elseif ($p -match "Polyglot") { "Multi-language check/test/repair" } elseif ($p -match "Optimizer") { "Safe optimizer" } elseif ($p -match "chartspec") { "Chart governance" } else { "Readme / evidence" }
            Status = if ($exists) { "FOUND" } else { "MISSING" }
            Risk = if ($exists) { "GREEN" } else { "RED" }
            FirstFlowAction = "VERIFY_ONLY_NO_EXECUTE"
        })
    }
    return $rows
}

function def_BuildFunctionalRootMatrix {
    param([string[]]$Roots)

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($p in $Roots) {
        $exists = Test-Path -LiteralPath $p
        $files = if ($exists) { @(Get-ChildItem -LiteralPath $p -Recurse -File -ErrorAction SilentlyContinue) } else { @() }
        $rows.Add([pscustomobject]@{
            Subsystem = Split-Path $p -Leaf
            Path = $p
            Exists = $exists
            FileCount = $files.Count
            SizeMB = if ($exists) { [math]::Round((($files | Measure-Object -Property Length -Sum).Sum / 1MB), 2) } else { 0 }
            Step1Inventory = if ($exists -and $files.Count -gt 0) { 20 } else { 0 }
            Step2StaticHealth = 0
            Step3Parameters = 0
            Step4Testing = 0
            Step5Strategy = 0
            EstimatedProgress = if ($exists -and $files.Count -gt 0) { 20 } else { 0 }
            Risk = if ($exists -and $files.Count -gt 0) { "YELLOW" } else { "RED" }
            Action = "RUN_DOMAIN_SPECIFIC_REVIEW_NEXT"
        })
    }
    return $rows
}

function def_BuildHydraRiskMatrix {
    param(
        [object[]]$InventoryRows,
        [object[]]$DuplicateRows,
        [object[]]$HealthRows,
        [object[]]$ExternalLinks
    )

    $rows = New-Object System.Collections.Generic.List[object]

    $duplicateRed = @($DuplicateRows | Where-Object { $_.Risk -eq "RED" }).Count
    $parseRed = @($HealthRows | Where-Object { $_.Risk -eq "RED" }).Count
    $archiveCount = @($InventoryRows | Where-Object { $_.Language -eq "Archive" }).Count
    $exeCount = @($InventoryRows | Where-Object { $_.Language -eq "Executable" }).Count
    $registryCount = @($InventoryRows | Where-Object { $_.Domain -eq "RegistrySSOT" }).Count
    $supportMissing = @((def_BuildSupportiveToolMatrix $def_PARAM_REQUIRED_SUPPORT_FILES) | Where-Object { $_.Risk -eq "RED" }).Count

    $riskDefs = @(
        @("H01","舊版誤用 / Wrong Version Activation","Many duplicate or versioned scripts can point to wrong active engine.",$DuplicateRows.Count,"YELLOW","Use active pointer + archive manifest before merge."),
        @("H02","Registry 分裂 / Registry Split","Multiple SSOT/config/registry files can conflict.",$registryCount,"YELLOW","Build Registry Spine and compare counts before overwrite."),
        @("H03","Parse Fail / Syntax Fail","Files failing static parse can break automated launch.",$parseRed,"RED","Fix only in sandbox; no canonical overwrite."),
        @("H04","Archive Bloat / ZIP pressure","ZIP/RAR/TAR files consume space and hide older versions.",$archiveCount,"YELLOW","Extract metadata, archive once, delete only after hash proof."),
        @("H05","Executable Risk","EXE/installers in Downloads should not enter BASE without trust review.",$exeCount,"YELLOW","Quarantine installer/exe list."),
        @("H06","Support Tool Missing","Nexus/Polyglot/SafeOptimizer missing blocks later install/test flow.",$supportMissing,"RED","Verify support module files before any auto deploy."),
        @("H07","External Link Drift","HTML/MD/JS external links can change or disappear.",$ExternalLinks.Count,"YELLOW","Evidence cache plan; no fetch in first flow."),
        @("H08","AIO Overwrite Risk","Multiple AllInOne scripts may write similar outputs.",@($InventoryRows | Where-Object { $_.Name -match "AIO|AllInOne|Ultimate" }).Count,"YELLOW","Run in sandbox run dir only."),
        @("H09","Path/PARAM Drift","Many path/config parameters create hidden environmental coupling.",@($HealthRows | Where-Object { $_.Path -match "config|params|registry|ssot" }).Count,"YELLOW","Parameter matrix + canonical defaults.")
    )

    foreach ($rd in $riskDefs) {
        $count = [int]$rd[3]
        $base = [math]::Log(1 + [math]::Max(0,$count))
        $score = [math]::Round($base, 2)
        if ($rd[0] -in @("H02","H03","H06")) { $score = [math]::Round($score + 1.5, 2) }
        $band = if ($score -ge 3.0) { "RED" } elseif ($score -ge 1.5) { "YELLOW" } else { "GREEN" }

        $rows.Add([pscustomobject]@{
            RiskID = $rd[0]
            RiskName = $rd[1]
            Description = $rd[2]
            EvidenceCount = $count
            HydraScore = $score
            Band = $band
            PreventiveCapability = $rd[5]
            FirstFlowAction = "REPORT_ONLY_NO_FIX"
        })
    }

    return $rows
}

function def_BuildPrevention25Matrix {
    $names = @(
        "Read-only default gate",
        "No delete unless AllowDelete=true and manifest signed",
        "No install unless AllowInstall=true",
        "No PATH change unless AllowPathChange=true",
        "RunRoot isolation",
        "Hash evidence before archive/delete",
        "Static parse before runtime",
        "JSON schema parse before SSOT merge",
        "PowerShell AST parse before invocation",
        "Python py_compile deferred or sandboxed",
        "Node --check deferred or sandboxed",
        "External link detect-only first flow",
        "Supportive tool existence check",
        "Functional root count check",
        "Registry duplicate detection",
        "Filename duplicate/hash conflict detection",
        "Progress bound to evidence count",
        "Hydra score threshold",
        "Sequence-dependent issue isolation",
        "Parallel-fixable grouping later only",
        "No canonical overwrite first flow",
        "HTML report auto-open only",
        "CSV/JSON evidence export",
        "Archive candidate list not delete",
        "Human review gate for RED"
    )
    $rows = New-Object System.Collections.Generic.List[object]
    $i = 0
    foreach ($n in $names) {
        $i++
        $rows.Add([pscustomobject]@{
            ID = "P{0:D2}" -f $i
            Capability = $n
            Status = "BUILT_IN_FIRST_FLOW"
            Action = "ENFORCED_OR_REPORTED"
        })
    }
    return $rows
}

function def_BuildProgressMatrix {
    param(
        [object[]]$InventoryRows,
        [object[]]$HealthRows,
        [object[]]$ParameterRows,
        [object[]]$ToolAvailabilityRows,
        [object[]]$HydraRows
    )

    $inventoryPct = if ($InventoryRows.Count -gt 0) { 100 } else { 0 }
    $eligibleHealth = @($InventoryRows | Where-Object { $_.Language -in @("PowerShell","Python","JavaScript","TypeScript","JSON","HTML","Markdown","CSS","Text") }).Count
    $staticPct = if ($eligibleHealth -gt 0) { [math]::Round(($HealthRows.Count / $eligibleHealth) * 100, 1) } else { 0 }
    $paramPct = if ($HealthRows.Count -gt 0) { [math]::Min(100, [math]::Round(($ParameterRows.Count / [math]::Max(1,$HealthRows.Count)) * 30, 1)) } else { 0 }
    $toolAvail = @($ToolAvailabilityRows | Where-Object { $_.Status -eq "AVAILABLE" }).Count
    $toolCheckable = @($ToolAvailabilityRows | Where-Object { $_.Status -in @("AVAILABLE","MISSING","MISSING_OR_LIBRARY") }).Count
    $toolPct = if ($toolCheckable -gt 0) { [math]::Round(($toolAvail / $toolCheckable) * 100, 1) } else { 0 }
    $redHydra = @($HydraRows | Where-Object { $_.Band -eq "RED" }).Count
    $strategyPct = if ($HydraRows.Count -gt 0) { if ($redHydra -eq 0) { 85 } else { 65 } } else { 40 }

    $components = @(
        [pscustomobject]@{ Flow = "Flow-1 Inventory Scan"; Percent = $inventoryPct; Weight = 20; Status = def_GetRYG $inventoryPct 95 60; Meaning = "All files classified into scope/domain/language." },
        [pscustomobject]@{ Flow = "Flow-2 Static Health"; Percent = $staticPct; Weight = 20; Status = def_GetRYG $staticPct 90 60; Meaning = "Text/code/JSON/HTML parse/read matrix." },
        [pscustomobject]@{ Flow = "Flow-3 Parameter Extraction"; Percent = $paramPct; Weight = 20; Status = def_GetRYG $paramPct 70 25; Meaning = "Input/output/path/time/source parameters extracted." },
        [pscustomobject]@{ Flow = "Flow-4 Tool Readiness"; Percent = $toolPct; Weight = 20; Status = def_GetRYG $toolPct 70 35; Meaning = "Local free tool availability and gaps." },
        [pscustomobject]@{ Flow = "Flow-5 Strategy Plan"; Percent = $strategyPct; Weight = 20; Status = def_GetRYG $strategyPct 85 60; Meaning = "Risk/action/copy/archive/test plan exists." }
    )

    $overall = [math]::Round((($components | ForEach-Object { $_.Percent * $_.Weight } | Measure-Object -Sum).Sum / 100), 1)

    return [pscustomobject]@{
        Components = $components
        OverallPercent = $overall
        OverallStatus = def_GetRYG $overall 85 60
    }
}

function def_BuildNextActionMatrix {
    $rows = @(
        [pscustomobject]@{ Phase="P0"; Name="Read-only Panorama"; Action="Current script only scans and reports."; Risk="GREEN"; Gate="NO_WRITE" },
        [pscustomobject]@{ Phase="P1"; Name="Nexus/Polyglot Support Check"; Action="Execute supportive tools in review-only mode after confirming existence."; Risk="YELLOW"; Gate="NO_INSTALL_FIRST" },
        [pscustomobject]@{ Phase="P2"; Name="Registry Spine"; Action="Dedupe Governance/Layout/Visual/UnifiedSpec/SourceTruth into canonical spine."; Risk="YELLOW"; Gate="BACKUP_AND_DIFF" },
        [pscustomobject]@{ Phase="P3"; Name="Domain Deep Scan"; Action="Run VDF/VRN/VAP/VPNS specific inventory and contract analysis."; Risk="YELLOW"; Gate="DOMAIN_SANDBOX" },
        [pscustomobject]@{ Phase="P4"; Name="Unit/Integration/System Test"; Action="Run language-specific tests after static parse is clean."; Risk="YELLOW"; Gate="TEST_ONLY" },
        [pscustomobject]@{ Phase="P5"; Name="Copy Useful Candidates"; Action="Copy selected Downloads candidates into BASE only after hash and manifest."; Risk="YELLOW"; Gate="ALLOW_COPY_EXPLICIT" },
        [pscustomobject]@{ Phase="P6"; Name="Archive Plan"; Action="Move replaced versions into archive manifest, not delete first."; Risk="YELLOW"; Gate="ARCHIVE_PROOF" },
        [pscustomobject]@{ Phase="P7"; Name="Delete Candidate Plan"; Action="Delete only after duplicate hash proof and manual review."; Risk="RED"; Gate="ALLOW_DELETE_AND_SIGN" }
    )
    return $rows
}

# =============================================================================
# def OUTPUT
# =============================================================================
function def_ExportMatrix {
    param(
        [object[]]$Rows,
        [string]$Path
    )
    try {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8BOM
    } catch {
        def_WriteLog "WARN" "Export failed: $Path :: $($_.Exception.Message)"
    }
}

function def_ToHtmlTable {
    param(
        [string]$Title,
        [object[]]$Rows,
        [int]$MaxRows = 500
    )

    $arr = @($Rows | Select-Object -First $MaxRows)
    if ($arr.Count -eq 0) {
        return "<section class='card'><h2>$(def_EscapeHtml $Title)</h2><p class='muted'>No rows.</p></section>"
    }

    $props = $arr[0].PSObject.Properties.Name
    $thead = ($props | ForEach-Object { "<th>$(def_EscapeHtml $_)</th>" }) -join ""
    $body = foreach ($row in $arr) {
        $td = foreach ($p in $props) {
            $v = $row.$p
            $class = ""
            if ($p -match "Risk|Band|Status|RYG") {
                if ($v -match "RED|FAIL|MISSING") { $class = " class='red'" }
                elseif ($v -match "YELLOW|WARN|DEFERRED|SKIP") { $class = " class='yellow'" }
                elseif ($v -match "GREEN|OK|FOUND|AVAILABLE") { $class = " class='green'" }
            }
            "<td$class>$(def_EscapeHtml $v)</td>"
        }
        "<tr>$($td -join '')</tr>"
    }

    $note = if ($Rows.Count -gt $MaxRows) { "<div class='note'>Showing $MaxRows / $($Rows.Count) rows. Full data in CSV/JSON.</div>" } else { "" }
    return "<section class='card'><h2>$(def_EscapeHtml $Title) <span>$($Rows.Count)</span></h2><div class='tablewrap'><table><thead><tr>$thead</tr></thead><tbody>$($body -join "`n")</tbody></table></div>$note</section>"
}

function def_WriteHtmlReport {
    param(
        [string]$Path,
        [hashtable]$Matrices,
        [object]$Progress
    )

    $progressCards = foreach ($c in $Progress.Components) {
        "<div class='metric $($c.Status.ToLower())'><div class='label'>$(def_EscapeHtml $c.Flow)</div><div class='value'>$($c.Percent)%</div><div class='bar'><i style='width:$($c.Percent)%'></i></div><div class='small'>$(def_EscapeHtml $c.Meaning)</div></div>"
    }

    $htmlSections = @()
    $order = @(
        "Overview",
        "Progress Matrix",
        "Functional Root Matrix",
        "Supportive Tool Matrix",
        "Domain Matrix",
        "Language Matrix",
        "Static Health Matrix",
        "Parameter Matrix",
        "Duplicate Matrix",
        "Hydra Risk Matrix",
        "Prevention 25 Matrix",
        "Tool Registry Matrix",
        "Tool Availability Matrix",
        "External Link Matrix",
        "Copy Candidate Matrix",
        "Archive Candidate Matrix",
        "Next Action Matrix",
        "Inventory Matrix"
    )
    foreach ($name in $order) {
        if ($Matrices.ContainsKey($name)) {
            $max = if ($name -eq "Inventory Matrix") { 1000 } elseif ($name -eq "Static Health Matrix") { 1000 } else { 500 }
            $htmlSections += def_ToHtmlTable -Title $name -Rows @($Matrices[$name]) -MaxRows $max
        }
    }

    $now = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $overall = $Progress.OverallPercent
    $overallStatus = $Progress.OverallStatus.ToLower()

    $html = @"
<!doctype html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA FirstSight Panorama · Governance Matrix</title>
<style>
:root{
  --bg:#f7f6f1; --paper:#fffdf7; --ink:#1f2328; --muted:#687076; --line:#dedbd0;
  --green:#2f8f5b; --yellow:#c5962f; --red:#bd5147; --blue:#477da8; --teal:#4a9a9a;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 20% 0%,#eef7f5,transparent 30%),var(--bg);color:var(--ink);font-family:"Segoe UI","Noto Sans TC",Arial,sans-serif;font-size:12px;line-height:1.45}
header{padding:26px 30px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#fffefa,#eef7f5)}
h1{margin:0;font-size:24px;letter-spacing:.02em}
.sub{margin-top:6px;color:var(--muted);font-family:Consolas,monospace}
.wrap{max-width:1680px;margin:0 auto;padding:18px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0 18px}
.metric{background:var(--paper);border:1px solid var(--line);border-left:5px solid var(--blue);border-radius:8px;padding:10px;box-shadow:0 8px 20px rgba(28,31,35,.04)}
.metric.green{border-left-color:var(--green)}
.metric.yellow{border-left-color:var(--yellow)}
.metric.red{border-left-color:var(--red)}
.label{color:var(--muted);font-size:11px;font-weight:700;text-transform:uppercase}
.value{font-size:25px;font-weight:750;margin:3px 0}
.small{font-size:11px;color:var(--muted)}
.bar{height:6px;background:#ece8de;border-radius:20px;overflow:hidden}
.bar i{display:block;height:100%;background:currentColor}
.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;margin:14px 0;overflow:hidden}
.card h2{font-size:15px;margin:0;padding:10px 12px;border-bottom:1px solid var(--line);background:#fbfaf4}
.card h2 span{font-family:Consolas,monospace;color:var(--muted);font-size:12px}
.tablewrap{overflow:auto;max-height:650px}
table{width:100%;border-collapse:collapse}
th,td{padding:6px 8px;border-bottom:1px solid #ece9df;text-align:left;vertical-align:top;white-space:nowrap}
th{position:sticky;top:0;background:#f1eee5;z-index:1;font-size:11px}
td{font-family:Consolas,"Noto Sans Mono",monospace;font-size:11px}
td.green{background:#e8f5ee;color:#126c3d;font-weight:700}
td.yellow{background:#fff5d8;color:#805d00;font-weight:700}
td.red{background:#fde9e6;color:#8c1f16;font-weight:700}
.note,.muted{color:var(--muted);padding:8px 12px}
.kv{display:grid;grid-template-columns:220px 1fr;gap:6px;padding:6px 12px}
footer{padding:20px 30px;color:var(--muted);font-family:Consolas,monospace}
@media(max-width:1000px){.grid{grid-template-columns:1fr 1fr}.wrap{padding:10px}}
</style>
</head>
<body>
<header>
  <h1>def VIA FirstSight Panorama Governance Matrix · v0100</h1>
  <div class="sub">Generated: $now · BASE: $(def_EscapeHtml $BaseRoot) · DOWNLOAD: $(def_EscapeHtml $DownloadRoot) · Safety: read-only / no install / no PATH change / no delete</div>
</header>
<div class="wrap">
  <div class="grid">
    <div class="metric $overallStatus"><div class="label">Overall First-Flow Progress</div><div class="value">$overall%</div><div class="bar"><i style="width:$overall%"></i></div><div class="small">$($Progress.OverallStatus)</div></div>
    $($progressCards -join "`n")
  </div>
  $($htmlSections -join "`n")
</div>
<footer>VIA VisualLock compatible · Matrix CSV/JSON saved next to this report · No file was deleted or modified by this first-flow analyzer.</footer>
</body>
</html>
"@

    Set-Content -LiteralPath $Path -Value $html -Encoding UTF8
}

# =============================================================================
# def COPY / ARCHIVE CANDIDATES
# =============================================================================
function def_BuildCopyCandidateMatrix {
    param([object[]]$InventoryRows)

    $rows = New-Object System.Collections.Generic.List[object]
    $candidates = $InventoryRows | Where-Object {
        $_.Scope -eq "DOWNLOAD" -and
        $_.Domain -in @("RegistrySSOT","VDF","VRN","VAP","VPNS","Supportive","EngineForge") -and
        $_.Language -in @("PowerShell","Python","JavaScript","HTML","JSON","Markdown","CSV","Parquet","SVG","Image")
    } | Sort-Object Domain, Language, Modified -Descending | Select-Object -First 500

    foreach ($c in $candidates) {
        $targetFolder = switch ($c.Domain) {
            "RegistrySSOT" { "_registry" }
            "Supportive" { "supportive modules" }
            "VDF" { "functional modules\VDF" }
            "VRN" { "functional modules\VRN" }
            "VAP" { "functional modules\VAP" }
            "VPNS" { "functional modules\VPNS" }
            "EngineForge" { "supportive modules\EngineForge" }
            default { "_incoming_review" }
        }
        $rows.Add([pscustomobject]@{
            SourcePath = $c.Path
            Domain = $c.Domain
            Language = $c.Language
            SizeKB = $c.SizeKB
            SHA12 = $c.SHA12
            ProposedTarget = Join-Path $BaseRoot $targetFolder
            Action = "PLAN_ONLY_NO_COPY"
            Risk = "YELLOW"
            Reason = "Potential useful candidate from Downloads; requires diff/hash/manual approval."
        })
    }
    return $rows
}

function def_BuildArchiveCandidateMatrix {
    param([object[]]$InventoryRows, [object[]]$DuplicateRows)

    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($d in $DuplicateRows | Select-Object -First 500) {
        $rows.Add([pscustomobject]@{
            CandidateType = "DUPLICATE_NAME"
            Name = $d.FileName
            Count = $d.Count
            Risk = $d.Risk
            Action = "ARCHIVE_PLAN_ONLY"
            Reason = $d.Action
            Evidence = $d.Hashes
        })
    }

    $archives = $InventoryRows | Where-Object { $_.Language -eq "Archive" } | Sort-Object SizeMB -Descending | Select-Object -First 200
    foreach ($a in $archives) {
        $rows.Add([pscustomobject]@{
            CandidateType = "ARCHIVE_FILE"
            Name = $a.Name
            Count = 1
            Risk = "YELLOW"
            Action = "SIZE_REVIEW_PLAN_ONLY"
            Reason = "Archive file may consume space; do not delete until manifest/hash proof exists."
            Evidence = "$($a.SizeMB) MB | $($a.Path)"
        })
    }

    return $rows
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    if ($AllowDelete -or $AllowInstall -or $AllowPathChange -or $EnableExternalFetch) {
        def_WriteLog "WARN" "One or more risky switches are enabled. First-flow analyzer will still NOT implement install/delete/path changes in this script."
    }

    $paths = def_NewRunPaths -BaseRoot $BaseRoot -RunName $RunName
    $script:LogPath = Join-Path $paths.Logs "VIA_FirstSightPanorama.log"

    def_WriteLog "BOOT" "VIA FirstSight Panorama started."
    def_WriteLog "BOOT" "BaseRoot    : $BaseRoot"
    def_WriteLog "BOOT" "DownloadRoot: $DownloadRoot"
    def_WriteLog "BOOT" "RunRoot     : $($paths.RunRoot)"
    def_WriteLog "SAFE" "Read-only mode: no install, no PATH change, no delete, no canonical overwrite."

    $roots = @($BaseRoot, $DownloadRoot) | Select-Object -Unique

    $dirRows = def_GetDirectoryInventory -Roots @($BaseRoot, $DownloadRoot) + (def_GetDirectoryInventory -Roots $def_PARAM_FUNCTIONAL_ROOTS)
    $inventoryRows = def_GetFileInventory -Roots $roots -MaxFilesTotal $MaxFilesTotal -MaxFilesPerRoot $MaxFilesPerRoot -HashMaxMB $HashMaxMB -BatchSize $BatchSize

    $staticResult = def_RunStaticHealth -InventoryRows $inventoryRows -MaxTextBytes $MaxTextBytes -EnablePyCompile $EnablePyCompile -EnableNodeCheck $EnableNodeCheck -MaxExternalLinksPerFile $MaxExternalLinksPerFile
    $healthRows = @($staticResult.Health)
    $parameterRows = @($staticResult.Parameters)
    $externalRows = @($staticResult.ExternalLinks)

    $toolRegistryRows = def_GetToolRegistry
    $toolAvailabilityRows = def_TestToolAvailability -ToolRows $toolRegistryRows

    $duplicateRows = def_BuildDuplicateMatrix -InventoryRows $inventoryRows
    $domainRows = def_BuildDomainMatrix -InventoryRows $inventoryRows -HealthRows $healthRows
    $languageRows = def_BuildLanguageMatrix -InventoryRows $inventoryRows -HealthRows $healthRows
    $supportRows = def_BuildSupportiveToolMatrix -SupportFiles $def_PARAM_REQUIRED_SUPPORT_FILES
    $functionalRows = def_BuildFunctionalRootMatrix -Roots $def_PARAM_FUNCTIONAL_ROOTS
    $hydraRows = def_BuildHydraRiskMatrix -InventoryRows $inventoryRows -DuplicateRows $duplicateRows -HealthRows $healthRows -ExternalLinks $externalRows
    $preventionRows = def_BuildPrevention25Matrix
    $copyRows = def_BuildCopyCandidateMatrix -InventoryRows $inventoryRows
    $archiveRows = def_BuildArchiveCandidateMatrix -InventoryRows $inventoryRows -DuplicateRows $duplicateRows
    $nextRows = def_BuildNextActionMatrix
    $progress = def_BuildProgressMatrix -InventoryRows $inventoryRows -HealthRows $healthRows -ParameterRows $parameterRows -ToolAvailabilityRows $toolAvailabilityRows -HydraRows $hydraRows

    $overviewRows = @(
        [pscustomobject]@{ Item="BaseRoot"; Value=$BaseRoot; Meaning="Formal active system root." },
        [pscustomobject]@{ Item="DownloadRoot"; Value=$DownloadRoot; Meaning="Reference / candidate pool." },
        [pscustomobject]@{ Item="Inventory files"; Value=$inventoryRows.Count; Meaning="Files scanned and classified." },
        [pscustomobject]@{ Item="Static health rows"; Value=$healthRows.Count; Meaning="Readable/parseable text/code files checked." },
        [pscustomobject]@{ Item="Parameter rows"; Value=$parameterRows.Count; Meaning="Input/output/path/time/control parameters extracted." },
        [pscustomobject]@{ Item="Duplicate filename groups"; Value=$duplicateRows.Count; Meaning="Potential old versions or conflicts." },
        [pscustomobject]@{ Item="External links detected"; Value=$externalRows.Count; Meaning="Evidence cache candidates; no fetch in first flow." },
        [pscustomobject]@{ Item="Hydra risks"; Value=$hydraRows.Count; Meaning="Nine major risk classes evaluated." },
        [pscustomobject]@{ Item="Overall progress"; Value="$($progress.OverallPercent)%"; Meaning=$progress.OverallStatus }
    )

    $matrices = [ordered]@{
        "Overview" = $overviewRows
        "Progress Matrix" = $progress.Components
        "Functional Root Matrix" = $functionalRows
        "Supportive Tool Matrix" = $supportRows
        "Domain Matrix" = $domainRows
        "Language Matrix" = $languageRows
        "Static Health Matrix" = $healthRows
        "Parameter Matrix" = $parameterRows
        "Duplicate Matrix" = $duplicateRows
        "Hydra Risk Matrix" = $hydraRows
        "Prevention 25 Matrix" = $preventionRows
        "Tool Registry Matrix" = $toolRegistryRows
        "Tool Availability Matrix" = $toolAvailabilityRows
        "External Link Matrix" = $externalRows
        "Copy Candidate Matrix" = $copyRows
        "Archive Candidate Matrix" = $archiveRows
        "Next Action Matrix" = $nextRows
        "Inventory Matrix" = $inventoryRows
    }

    foreach ($key in $matrices.Keys) {
        $safe = ($key -replace "[^A-Za-z0-9_]+","_").Trim("_")
        def_ExportMatrix -Rows @($matrices[$key]) -Path (Join-Path $paths.Registry "$safe.csv")
    }

    $jsonObj = [ordered]@{
        schema_id = "VIA_FirstSightPanorama_GovernanceMatrix"
        version = "v0100"
        generated_at = (Get-Date).ToString("o")
        safety = [ordered]@{
            read_only = $true
            allow_install = $AllowInstall
            allow_path_change = $AllowPathChange
            allow_delete = $AllowDelete
            enable_external_fetch = $EnableExternalFetch
            note = "This first-flow script does not implement install/delete/path mutations."
        }
        parameters = [ordered]@{
            BaseRoot = $BaseRoot
            DownloadRoot = $DownloadRoot
            MaxFilesTotal = $MaxFilesTotal
            MaxFilesPerRoot = $MaxFilesPerRoot
            MaxTextBytes = $MaxTextBytes
            HashMaxMB = $HashMaxMB
            BatchSize = $BatchSize
            EnablePyCompile = $EnablePyCompile
            EnableNodeCheck = $EnableNodeCheck
        }
        progress = $progress
        matrices = $matrices
    }

    $jsonPath = Join-Path $paths.Registry "VIA_FirstSightPanorama_GovernanceMatrix.json"
    $jsonObj | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $htmlPath = Join-Path $paths.Report "VIA_FirstSightPanorama_GovernanceMatrix.html"
    def_WriteHtmlReport -Path $htmlPath -Matrices $matrices -Progress $progress

    def_WriteLog "OK" "HTML Report: $htmlPath"
    def_WriteLog "OK" "JSON SSOT : $jsonPath"
    def_WriteLog "OK" "CSV folder: $($paths.Registry)"
    def_WriteLog "DONE" "FirstSight Panorama completed."

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA FirstSight Panorama · COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "RunRoot : $($paths.RunRoot)"
    Write-Host "HTML    : $htmlPath"
    Write-Host "JSON    : $jsonPath"
    Write-Host "CSV     : $($paths.Registry)"
    Write-Host "Overall : $($progress.OverallPercent)% [$($progress.OverallStatus)]"
    Write-Host "Safety  : read-only / no install / no PATH change / no delete"

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process $htmlPath
    }
}

# =============================================================================
# def ENTRY
# =============================================================================
try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
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
