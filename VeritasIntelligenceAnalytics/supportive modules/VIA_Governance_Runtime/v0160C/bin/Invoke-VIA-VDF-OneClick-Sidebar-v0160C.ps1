#requires -Version 7.0
<#
====================================================================================================
def VIA · VDF ONE-CLICK SIDEBAR WORKBENCH · v0160C
(version-forward of v0160B: same Veritas design-lock UI served as a plain browser HTML page over a
localhost HTTP bridge — mshta/ActiveX removed, every workbench action mapped to /api endpoints)
====================================================================================================
One PowerShell entrypoint for Veritas Data Forge.

Seven UI parameters
-------------------
1. Base
2. Input / Data Source
3. Start Date
4. End Date
5. Universe / Tickers
6. Update Mode
7. Open HTML

The launcher:
- resolves the VIA mother system and the VDF root;
- discovers the canonical VDF PowerShell or Python entrypoint;
- imports approved PowerShell modules and registers all available modules;
- verifies required Python data libraries and inventories installed packages;
- SHA-registers supportive tools and VDF code without blindly dot-sourcing them;
- stages optional CSV/Excel/JSON/Parquet data sources collision-safely;
- invokes only parameters that the discovered VDF PowerShell entrypoint declares;
- discovers and embeds the latest Basic Info, Financial Data, Market Data and
  Data Quality HTML outputs;
- opens a fixed-left-sidebar Windows HTML U/I.

Governance
----------
- no network installation;
- no broad delete and no Stop-Process;
- no blind dot-source of supportive tools;
- no canonical merge or pointer mutation by this wrapper;
- timeout is fail-closed, but the child process is not forcibly terminated;
- run-local evidence and append-only registries.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$Base = "",
    [switch]$Worker,
    [string]$WorkerConfig = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Script:Version = "v0160C"

$Script:ApprovedPowerShellModules = @(
    "PSScriptAnalyzer",
    "Pester",
    "PSWriteHTML",
    "ThreadJob",
    "ImportExcel",
    "Microsoft.PowerShell.SecretManagement",
    "PSReadLine"
)

$Script:RequiredPythonModules = @(
    "pandas",
    "pyarrow",
    "duckdb"
)

$Script:OptionalPythonModules = @(
    "polars",
    "numpy",
    "requests",
    "yfinance",
    "akshare",
    "openpyxl"
)

$Script:AllowedInputExtensions = @(
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".jsonl",
    ".parquet",
    ".duckdb",
    ".db",
    ".sqlite",
    ".txt",
    ".yaml",
    ".yml"
)

$Script:CoreSupportiveToolPatterns = @(
    "VIA_RegistryCore_v1",
    "VIA_SSOT_Unified",
    "VIA_EnvManager",
    "VeritasCeleritas",
    "VeritasAegisNexus",
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "Invoke-VeritasNexusCore",
    "Invoke-VeritasCodexNexus",
    "Invoke-VIA-CentralGovernanceManager"
)

$Script:PowerShellEntrypointNames = @(
    "Invoke-VDF.ps1",
    "run_vdf.ps1",
    "VDF_Launch_Master.ps1",
    "VDF_DataHub_Launch.ps1",
    "Start-VDF.ps1"
)

function Get-NowIso {
    return (Get-Date).ToString("o")
}

function Ensure-Directory {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }

    return (
        Get-FileHash -LiteralPath $Path -Algorithm SHA256
    ).Hash.ToLowerInvariant()
}

function Write-Utf8NoBomAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Text
    )

    $parent = Split-Path -Parent $Path

    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        Ensure-Directory -Path $parent
    }

    $temporary = "{0}.tmp.{1}.{2}" -f
        $Path,
        $PID,
        ([DateTime]::UtcNow.Ticks)

    $encoding = [System.Text.UTF8Encoding]::new($false)

    [System.IO.File]::WriteAllText(
        $temporary,
        $Text,
        $encoding
    )

    [System.IO.File]::Move(
        $temporary,
        $Path,
        $true
    )
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )

    $text = (
        $Value |
        ConvertTo-Json -Depth 100
    ) + [Environment]::NewLine

    Write-Utf8NoBomAtomic -Path $Path -Text $text
}

function Append-Utf8NoBomLine {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Line
    )

    Ensure-Directory -Path (Split-Path -Parent $Path)

    $encoding = [System.Text.UTF8Encoding]::new($false)
    $prefix = ""

    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $bytes = [System.IO.File]::ReadAllBytes($Path)

        if (
            $bytes.Length -gt 0 -and
            $bytes[$bytes.Length - 1] -ne 10
        ) {
            $prefix = [Environment]::NewLine
        }
    }

    [System.IO.File]::AppendAllText(
        $Path,
        $prefix + $Line + [Environment]::NewLine,
        $encoding
    )
}

function ConvertTo-CanonicalJson {
    param([Parameter(Mandatory)]$Value)

    return (
        $Value |
        ConvertTo-Json -Depth 100 -Compress
    )
}

function Resolve-BaseRoot {
    param([AllowEmptyString()][string]$Requested)

    $candidates = [System.Collections.Generic.List[string]]::new()

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        $candidates.Add($Requested)
    }

    foreach ($candidate in @(
        $PSScriptRoot,
        (Get-Location).Path,
        "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics",
        "$env:USERPROFILE\OneDrive\VeritasIntelligenceAnalytics",
        "$env:USERPROFILE\OneDrive\文件\VeritasIntelligenceAnalytics",
        "C:\VeritasIntelligenceAnalytics"
    )) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $candidates.Add($candidate)
        }
    }

    $seen = @{}

    foreach ($candidate in $candidates) {
        try {
            $current = [System.IO.Path]::GetFullPath($candidate)
        }
        catch {
            continue
        }

        for ($depth = 0; $depth -le 7; $depth++) {
            $key = $current.ToLowerInvariant()

            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true

                $hasSupport = Test-Path `
                    -LiteralPath (
                        Join-Path `
                            -Path $current `
                            -ChildPath "supportive modules"
                    ) `
                    -PathType Container

                $hasFunctional = Test-Path `
                    -LiteralPath (
                        Join-Path `
                            -Path $current `
                            -ChildPath "functional modules"
                    ) `
                    -PathType Container

                $hasModule = Test-Path `
                    -LiteralPath (
                        Join-Path `
                            -Path $current `
                            -ChildPath "module"
                    ) `
                    -PathType Container

                if (
                    $hasSupport -and
                    ($hasFunctional -or $hasModule)
                ) {
                    return $current
                }
            }

            $parent = Split-Path -Parent $current

            if (
                [string]::IsNullOrWhiteSpace($parent) -or
                $parent -eq $current
            ) {
                break
            }

            $current = $parent
        }
    }

    throw (
        "Could not locate the VeritasIntelligenceAnalytics mother system. " +
        "Use the Base Windows folder picker."
    )
}

function Resolve-VdfRoot {
    param([Parameter(Mandatory)][string]$BaseRoot)

    $relativeCandidates = @(
        "functional modules\VDF",
        "functional modules\VeritasDataForge",
        "module\VeritasDataForge",
        "VeritasDataForge",
        "VDF_DataHub_FINAL\VDF_FINAL"
    )

    foreach ($relative in $relativeCandidates) {
        $candidate = Join-Path `
            -Path $BaseRoot `
            -ChildPath $relative

        if (Test-Path -LiteralPath $candidate -PathType Container) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    $entrypointNames = $Script:PowerShellEntrypointNames

    $found = @(
        Get-ChildItem `
            -LiteralPath $BaseRoot `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $entrypointNames -contains $_.Name
        } |
        Where-Object {
            $full = $_.FullName.ToLowerInvariant()

            -not (
                $full.Contains("\_runs\") -or
                $full.Contains("\archive\") -or
                $full.Contains("\backup\") -or
                $full.Contains("\staging\") -or
                $full.Contains("\__pycache__\")
            )
        } |
        Sort-Object `
            @{Expression = {
                $priority = [Array]::IndexOf(
                    $entrypointNames,
                    $_.Name
                )

                if ($priority -lt 0) {
                    999
                }
                else {
                    $priority
                }
            }},
            FullName
    )

    if ($found.Count -gt 0) {
        return $found[0].Directory.FullName
    }

    throw (
        "VDF root could not be resolved under Base: " +
        $BaseRoot
    )
}

function Resolve-PythonRuntime {
    param(
        [AllowEmptyString()][string]$Requested,
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot
    )

    $candidates = [System.Collections.Generic.List[string]]::new()

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        $candidates.Add($Requested)
    }

    foreach ($candidate in @(
        "$env:USERPROFILE\envs\via_core_312\Scripts\python.exe",
        "$env:USERPROFILE\envs\via_core\Scripts\python.exe",
        "$env:USERPROFILE\envs\via_compute\Scripts\python.exe",
        "C:\Python313\python.exe",
        (Join-Path -Path $VdfRoot -ChildPath ".venv\Scripts\python.exe"),
        (Join-Path -Path $BaseRoot -ChildPath ".venv\Scripts\python.exe")
    )) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $candidates.Add($candidate)
        }
    }

    $command = Get-Command python -ErrorAction SilentlyContinue

    if (
        $null -ne $command -and
        -not [string]::IsNullOrWhiteSpace($command.Source)
    ) {
        $candidates.Add([string]$command.Source)
    }

    $seen = @{}

    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        $key = $candidate.ToLowerInvariant()

        if ($seen.ContainsKey($key)) {
            continue
        }

        $seen[$key] = $true

        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    return ""
}

function Find-VdfPowerShellEntrypoint {
    param([Parameter(Mandatory)][string]$VdfRoot)

    foreach ($name in $Script:PowerShellEntrypointNames) {
        $candidate = Join-Path `
            -Path $VdfRoot `
            -ChildPath $name

        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [ordered]@{
                type = "POWERSHELL"
                path = [System.IO.Path]::GetFullPath($candidate)
                name = $name
            }
        }
    }

    $entrypointNames = $Script:PowerShellEntrypointNames

    $found = @(
        Get-ChildItem `
            -LiteralPath $VdfRoot `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $entrypointNames -contains $_.Name
        } |
        Where-Object {
            $full = $_.FullName.ToLowerInvariant()

            -not (
                $full.Contains("\_runs\") -or
                $full.Contains("\archive\") -or
                $full.Contains("\backup\") -or
                $full.Contains("\staging\")
            )
        } |
        Sort-Object `
            @{Expression = {
                $priority = [Array]::IndexOf(
                    $entrypointNames,
                    $_.Name
                )

                if ($priority -lt 0) {
                    999
                }
                else {
                    $priority
                }
            }},
            FullName
    )

    if ($found.Count -gt 0) {
        return [ordered]@{
            type = "POWERSHELL"
            path = $found[0].FullName
            name = $found[0].Name
        }
    }

    return $null
}

function Find-VdfPythonEntrypoint {
    param(
        [Parameter(Mandatory)][string]$VdfRoot,
        [Parameter(Mandatory)][string]$PythonPath
    )

    $mainPath = Join-Path `
        -Path $VdfRoot `
        -ChildPath "__main__.py"

    if (Test-Path -LiteralPath $mainPath -PathType Leaf) {
        return [ordered]@{
            type = "PYTHON_MODULE"
            path = $mainPath
            package = Split-Path -Leaf $VdfRoot
            working_directory = Split-Path -Parent $VdfRoot
        }
    }

    $orchestratorNames = @(
        "VDF_ENG001_DataHubOrchestrator.py",
        "vdf_orchestrator.py",
        "main.py"
    )

    foreach ($name in $orchestratorNames) {
        $candidate = Join-Path `
            -Path $VdfRoot `
            -ChildPath $name

        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [ordered]@{
                type = "PYTHON_SCRIPT"
                path = $candidate
                package = ""
                working_directory = $VdfRoot
            }
        }
    }

    $found = @(
        Get-ChildItem `
            -LiteralPath $VdfRoot `
            -Recurse `
            -File `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $orchestratorNames -contains $_.Name
        } |
        Sort-Object FullName
    )

    if ($found.Count -gt 0) {
        return [ordered]@{
            type = "PYTHON_SCRIPT"
            path = $found[0].FullName
            package = ""
            working_directory = $found[0].Directory.FullName
        }
    }

    throw (
        "No VDF PowerShell or Python entrypoint was found under: " +
        $VdfRoot
    )
}

function Resolve-VdfEntrypoint {
    param(
        [Parameter(Mandatory)][string]$VdfRoot,
        [Parameter(Mandatory)][string]$PythonPath
    )

    $powerShell = Find-VdfPowerShellEntrypoint -VdfRoot $VdfRoot

    if ($null -ne $powerShell) {
        return $powerShell
    }

    return Find-VdfPythonEntrypoint `
        -VdfRoot $VdfRoot `
        -PythonPath $PythonPath
}

function Resolve-DefaultInput {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot
    )

    $candidates = @(
        (Join-Path -Path $VdfRoot -ChildPath "input"),
        (Join-Path -Path $VdfRoot -ChildPath "data\input"),
        (Join-Path -Path $VdfRoot -ChildPath "data"),
        (Join-Path -Path $BaseRoot -ChildPath "_vdf_input")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            return $candidate
        }
    }

    return $candidates[0]
}

function Find-LatestHtmlByPatterns {
    param(
        [Parameter(Mandatory)][string[]]$SearchRoots,
        [Parameter(Mandatory)][string[]]$Patterns
    )

    $files = [System.Collections.Generic.List[System.IO.FileInfo]]::new()

    foreach ($root in $SearchRoots) {
        if (
            [string]::IsNullOrWhiteSpace($root) -or
            -not (
                Test-Path `
                    -LiteralPath $root `
                    -PathType Container
            )
        ) {
            continue
        }

        foreach ($file in @(
            Get-ChildItem `
                -LiteralPath $root `
                -Filter "*.html" `
                -File `
                -Recurse `
                -ErrorAction SilentlyContinue
        )) {
            $full = $file.FullName.ToLowerInvariant()

            if (
                $full.Contains("\archive\") -or
                $full.Contains("\backup\") -or
                $full.Contains("\staging\")
            ) {
                continue
            }

            foreach ($pattern in $Patterns) {
                if ($file.Name -match $pattern) {
                    $files.Add($file)
                    break
                }
            }
        }
    }

    if ($files.Count -eq 0) {
        return ""
    }

    return (
        $files |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    ).FullName
}

function Resolve-VdfViewPages {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot
    )

    $searchRoots = @(
        $VdfRoot,
        (Join-Path -Path $VdfRoot -ChildPath "output"),
        (Join-Path -Path $VdfRoot -ChildPath "outputs"),
        (Join-Path -Path $BaseRoot -ChildPath "output"),
        (Join-Path -Path $BaseRoot -ChildPath "outputs"),
        (Join-Path -Path $BaseRoot -ChildPath "_vdf_launcher_runs"),
        (Join-Path -Path $BaseRoot -ChildPath "_via_vdf_runs")
    )

    return [ordered]@{
        basic_info_page = Find-LatestHtmlByPatterns `
            -SearchRoots $searchRoots `
            -Patterns @(
                "(?i)basic[_\- ]?info",
                "(?i)company[_\- ]?profile"
            )
        financial_data_page = Find-LatestHtmlByPatterns `
            -SearchRoots $searchRoots `
            -Patterns @(
                "(?i)financial[_\- ]?data",
                "(?i)financial[_\- ]?statement",
                "(?i)fundamental"
            )
        market_data_page = Find-LatestHtmlByPatterns `
            -SearchRoots $searchRoots `
            -Patterns @(
                "(?i)market[_\- ]?data",
                "(?i)price",
                "(?i)ohlcv",
                "(?i)marketflow"
            )
        data_quality_page = Find-LatestHtmlByPatterns `
            -SearchRoots $searchRoots `
            -Patterns @(
                "(?i)data[_\- ]?quality",
                "(?i)validation",
                "(?i)validator",
                "(?i)audit",
                "(?i)dashboard"
            )
        main_ui_page = Find-LatestHtmlByPatterns `
            -SearchRoots $searchRoots `
            -Patterns @(
                "(?i)vdf.*ui",
                "(?i)datahub.*ui",
                "(?i)dashboard"
            )
    }
}

function Get-SevenDefaults {
    param([Parameter(Mandatory)][string]$BaseRoot)

    $vdfRoot = Resolve-VdfRoot -BaseRoot $BaseRoot

    $python = Resolve-PythonRuntime `
        -Requested "" `
        -BaseRoot $BaseRoot `
        -VdfRoot $vdfRoot

    $views = Resolve-VdfViewPages `
        -BaseRoot $BaseRoot `
        -VdfRoot $vdfRoot

    return [ordered]@{
        base = $BaseRoot
        input = Resolve-DefaultInput `
            -BaseRoot $BaseRoot `
            -VdfRoot $vdfRoot
        startDate = (Get-Date -Format "yyyy-MM-dd")
        endDate = ""
        universe = "DEFAULT"
        updateMode = "Incremental"
        openHtml = $true
        vdfRoot = $vdfRoot
        python = $python
        basicInfoPage = $views.basic_info_page
        financialDataPage = $views.financial_data_page
        marketDataPage = $views.market_data_page
        dataQualityPage = $views.data_quality_page
        mainUiPage = $views.main_ui_page
    }
}

function Import-AndRegisterPowerShellModules {
    param([Parameter(Mandatory)][string]$RunDir)

    $rows = @()

    foreach ($name in $Script:ApprovedPowerShellModules) {
        $available = @(
            Get-Module `
                -ListAvailable `
                -Name $name `
                -ErrorAction SilentlyContinue |
            Sort-Object Version -Descending
        )

        if ($available.Count -eq 0) {
            $rows += [ordered]@{
                module = $name
                available = $false
                imported = $false
                version = ""
                path = ""
                state = "NOT_INSTALLED_OPTIONAL"
                error = ""
            }

            continue
        }

        $selected = $available[0]

        try {
            Import-Module `
                -Name $selected.Path `
                -Force `
                -ErrorAction Stop

            $rows += [ordered]@{
                module = $name
                available = $true
                imported = $true
                version = [string]$selected.Version
                path = [string]$selected.Path
                state = "IMPORTED"
                error = ""
            }
        }
        catch {
            $rows += [ordered]@{
                module = $name
                available = $true
                imported = $false
                version = [string]$selected.Version
                path = [string]$selected.Path
                state = "IMPORT_FAILED"
                error = $_.Exception.Message
            }
        }
    }

    $inventory = @(
        Get-Module -ListAvailable |
        Sort-Object Name, Version -Unique |
        ForEach-Object {
            [ordered]@{
                name = $_.Name
                version = [string]$_.Version
                path = [string]$_.Path
                module_type = [string]$_.ModuleType
            }
        }
    )

    $registryDir = Join-Path -Path $RunDir -ChildPath "registry"

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $registryDir `
                -ChildPath "powershell_approved_imports.json"
        ) `
        -Value $rows

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $registryDir `
                -ChildPath "powershell_module_inventory.json"
        ) `
        -Value $inventory

    $failedImports = @(
        $rows |
        Where-Object {
            $_.state -eq "IMPORT_FAILED"
        }
    )

    if ($failedImports.Count -gt 0) {
        throw (
            "Installed approved PowerShell modules failed to import: " +
            (
                $failedImports |
                ConvertTo-Json -Depth 20 -Compress
            )
        )
    }

    return [ordered]@{
        approved = $rows
        inventory_count = $inventory.Count
        imported_count = @(
            $rows |
            Where-Object {
                $_.imported
            }
        ).Count
        missing_optional_count = @(
            $rows |
            Where-Object {
                -not $_.available
            }
        ).Count
    }
}

function Test-AndRegisterPythonRuntime {
    param(
        [Parameter(Mandatory)][string]$PythonPath,
        [Parameter(Mandatory)][string]$RunDir
    )

    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        throw "Python runtime does not exist: $PythonPath"
    }

    $testCode = @'
import importlib
import json
import platform
import sys

required_count = int(sys.argv[1])
names = sys.argv[2:]
rows = []

for index, name in enumerate(names):
    required = index < required_count
    try:
        module = importlib.import_module(name)
        rows.append({
            "module": name,
            "required": required,
            "imported": True,
            "file": str(getattr(module, "__file__", "")),
            "version": str(getattr(module, "__version__", "")),
        })
    except Exception as exc:
        rows.append({
            "module": name,
            "required": required,
            "imported": False,
            "error": f"{type(exc).__name__}: {exc}",
        })

print(json.dumps({
    "python_executable": sys.executable,
    "python_version": platform.python_version(),
    "implementation": platform.python_implementation(),
    "modules": rows,
    "required_all_imported": all(
        row["imported"] for row in rows if row["required"]
    ),
}, ensure_ascii=False))
'@

    $allModules = @(
        $Script:RequiredPythonModules +
        $Script:OptionalPythonModules
    )

    $testOutput = @(
        & $PythonPath `
            -c $testCode `
            $Script:RequiredPythonModules.Count `
            @allModules 2>&1
    )

    if ($LASTEXITCODE -ne 0) {
        throw (
            "Python import test process failed: " +
            ($testOutput | Out-String)
        )
    }

    $runtime = (
        ($testOutput | Out-String).Trim() |
        ConvertFrom-Json
    )

    if (-not $runtime.required_all_imported) {
        $missing = @(
            $runtime.modules |
            Where-Object {
                $_.required -and
                -not $_.imported
            }
        )

        throw (
            "Required VDF Python libraries are missing: " +
            (
                $missing |
                ConvertTo-Json -Depth 20 -Compress
            )
        )
    }

    $pipOutput = @(
        & $PythonPath `
            -m pip list --format=json 2>&1
    )

    $pipPackages = @()
    $pipError = ""

    if ($LASTEXITCODE -eq 0) {
        try {
            $pipPackages = (
                ($pipOutput | Out-String).Trim() |
                ConvertFrom-Json
            )
        }
        catch {
            $pipError = $_.Exception.Message
        }
    }
    else {
        $pipError = ($pipOutput | Out-String).Trim()
    }

    $registryDir = Join-Path -Path $RunDir -ChildPath "registry"

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $registryDir `
                -ChildPath "python_runtime_imports.json"
        ) `
        -Value $runtime

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $registryDir `
                -ChildPath "python_package_inventory.json"
        ) `
        -Value ([ordered]@{
            packages = $pipPackages
            pip_error = $pipError
        })

    return [ordered]@{
        runtime = $runtime
        pip_package_count = @($pipPackages).Count
        required_import_count = @(
            $runtime.modules |
            Where-Object {
                $_.required -and
                $_.imported
            }
        ).Count
        optional_import_count = @(
            $runtime.modules |
            Where-Object {
                -not $_.required -and
                $_.imported
            }
        ).Count
        optional_missing_count = @(
            $runtime.modules |
            Where-Object {
                -not $_.required -and
                -not $_.imported
            }
        ).Count
        pip_error = $pipError
    }
}

function Register-CodeInventory {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot,
        [Parameter(Mandatory)][string]$RunDir
    )

    $roots = @(
        [ordered]@{
            label = "SUPPORTIVE"
            path = Join-Path `
                -Path $BaseRoot `
                -ChildPath "supportive modules"
        },
        [ordered]@{
            label = "VDF"
            path = $VdfRoot
        }
    )

    $extensions = @(
        ".ps1",
        ".psm1",
        ".psd1",
        ".py",
        ".pyi",
        ".json",
        ".jsonl",
        ".sql",
        ".md",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".csv"
    )

    $inventory = @()
    $sequence = 0

    foreach ($root in $roots) {
        if (
            -not (
                Test-Path `
                    -LiteralPath $root.path `
                    -PathType Container
            )
        ) {
            continue
        }

        foreach ($file in @(
            Get-ChildItem `
                -LiteralPath $root.path `
                -Recurse `
                -File `
                -ErrorAction SilentlyContinue |
            Sort-Object FullName
        )) {
            $extension = $file.Extension.ToLowerInvariant()

            if ($extensions -notcontains $extension) {
                continue
            }

            $full = $file.FullName.ToLowerInvariant()

            $excluded = $false

            foreach ($part in @(
                "\__pycache__\",
                "\.git\",
                "\node_modules\",
                "\cache\",
                "\caches\",
                "\archive\",
                "\backup\",
                "\staging\",
                "\registry\",
                "\ledger\",
                "\snapshots\",
                "\_runs\"
            )) {
                if ($full.Contains($part)) {
                    $excluded = $true
                    break
                }
            }

            if ($excluded) {
                continue
            }

            $sequence++

            $inventory += [ordered]@{
                sequence = $sequence
                scope = $root.label
                relative_path = [System.IO.Path]::GetRelativePath(
                    $BaseRoot,
                    $file.FullName
                )
                extension = $extension
                bytes = $file.Length
                last_write_utc = $file.LastWriteTimeUtc.ToString("o")
                sha256 = Get-Sha256 -Path $file.FullName
                registration_state = "REGISTERED_HASH_ONLY_NOT_EXECUTED"
            }
        }
    }

    $snapshotText = (
        $inventory |
        ForEach-Object {
            "{0}|{1}|{2}|{3}" -f
                $_.scope,
                $_.relative_path,
                $_.sha256,
                $_.bytes
        }
    ) -join "`n"

    $shaObject = [System.Security.Cryptography.SHA256]::Create()

    try {
        $snapshotHash = (
            [BitConverter]::ToString(
                $shaObject.ComputeHash(
                    [Text.Encoding]::UTF8.GetBytes(
                        $snapshotText
                    )
                )
            )
        ).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $shaObject.Dispose()
    }

    $coreRows = @()

    foreach ($pattern in $Script:CoreSupportiveToolPatterns) {
        $matches = @(
            $inventory |
            Where-Object {
                [System.IO.Path]::GetFileNameWithoutExtension(
                    $_.relative_path
                ) -like "*$pattern*"
            }
        )

        $coreRows += [ordered]@{
            tool_pattern = $pattern
            found = ($matches.Count -gt 0)
            match_count = $matches.Count
            matches = @(
                $matches |
                ForEach-Object {
                    $_.relative_path
                }
            )
        }
    }

    $registryDir = Join-Path `
        -Path $BaseRoot `
        -ChildPath "supportive modules\VIA_Governance_Runtime\v0160A\registry"

    $snapshotDir = Join-Path `
        -Path $registryDir `
        -ChildPath "snapshots"

    Ensure-Directory -Path $snapshotDir

    $snapshotPath = Join-Path `
        -Path $snapshotDir `
        -ChildPath (
            "VDF_Runtime_Snapshot.{0}.json" -f
            $snapshotHash
        )

    if (-not (Test-Path -LiteralPath $snapshotPath -PathType Leaf)) {
        Write-JsonAtomic `
            -Path $snapshotPath `
            -Value ([ordered]@{
                version = $Script:Version
                generated_at = Get-NowIso
                base = $BaseRoot
                vdf_root = $VdfRoot
                snapshot_sha256 = $snapshotHash
                file_count = $inventory.Count
                inventory = $inventory
                core_supportive_tools = $coreRows
            })
    }

    $ledgerPath = Join-Path `
        -Path $registryDir `
        -ChildPath "VDF_Runtime_Registry.v0160A.jsonl"

    $alreadyRecorded = $false

    if (Test-Path -LiteralPath $ledgerPath -PathType Leaf) {
        foreach ($line in Get-Content -LiteralPath $ledgerPath -Encoding UTF8) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            try {
                $event = $line | ConvertFrom-Json

                if ([string]$event.snapshot_sha256 -eq $snapshotHash) {
                    $alreadyRecorded = $true
                    break
                }
            }
            catch {
                throw "VDF runtime registry contains malformed JSONL."
            }
        }
    }

    if (-not $alreadyRecorded) {
        Append-Utf8NoBomLine `
            -Path $ledgerPath `
            -Line (
                ConvertTo-CanonicalJson ([ordered]@{
                    event = "VDF_RUNTIME_REGISTERED"
                    version = $Script:Version
                    recorded_at = Get-NowIso
                    base = $BaseRoot
                    vdf_root = $VdfRoot
                    snapshot_sha256 = $snapshotHash
                    file_count = $inventory.Count
                    snapshot_path = $snapshotPath
                    automatic_code_execution = $false
                })
            )
    }

    $runRegistry = Join-Path -Path $RunDir -ChildPath "registry"

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $runRegistry `
                -ChildPath "vdf_code_registry.json"
        ) `
        -Value ([ordered]@{
            snapshot_sha256 = $snapshotHash
            file_count = $inventory.Count
            registry_ledger = $ledgerPath
            snapshot = $snapshotPath
            ledger_state = if ($alreadyRecorded) {
                "EXACT_SNAPSHOT_ALREADY_REGISTERED"
            }
            else {
                "LEDGER_EVENT_APPENDED"
            }
            core_supportive_tools = $coreRows
        })

    return [ordered]@{
        snapshot_sha256 = $snapshotHash
        file_count = $inventory.Count
        registry_ledger = $ledgerPath
        snapshot = $snapshotPath
        ledger_state = if ($alreadyRecorded) {
            "EXACT_SNAPSHOT_ALREADY_REGISTERED"
        }
        else {
            "LEDGER_EVENT_APPENDED"
        }
        core_supportive_tools = $coreRows
    }
}

function Get-SafeFileName {
    param([Parameter(Mandatory)][string]$Name)

    $safe = [System.IO.Path]::GetFileName($Name)

    foreach ($character in [System.IO.Path]::GetInvalidFileNameChars()) {
        $safe = $safe.Replace([string]$character, "_")
    }

    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "Input filename is empty after sanitization."
    }

    return $safe
}

function Resolve-CollisionSafeDestination {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$DestinationFolder
    )

    $name = Get-SafeFileName -Name (
        [System.IO.Path]::GetFileName($Source)
    )

    $destination = Join-Path `
        -Path $DestinationFolder `
        -ChildPath $name

    $sourceSha = Get-Sha256 -Path $Source

    if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
        return [ordered]@{
            path = $destination
            state = "NEW_DESTINATION"
            sha256 = $sourceSha
        }
    }

    if ((Get-Sha256 -Path $destination) -eq $sourceSha) {
        return [ordered]@{
            path = $destination
            state = "EXACT_EXISTS_SKIP"
            sha256 = $sourceSha
        }
    }

    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($name)
    $extension = [System.IO.Path]::GetExtension($name)

    return [ordered]@{
        path = Join-Path `
            -Path $DestinationFolder `
            -ChildPath (
                "{0}.{1}{2}" -f
                $baseName,
                $sourceSha.Substring(0, 12),
                $extension
            )
        state = "HASH_SUFFIX_RENAME"
        sha256 = $sourceSha
    }
}

function Get-InputSourceFiles {
    param(
        [Parameter(Mandatory)]$Sources,
        [Parameter(Mandatory)][bool]$Recursive
    )

    $files = [System.Collections.Generic.List[string]]::new()
    $seen = @{}

    foreach ($source in @($Sources)) {
        $path = [string]$source.path

        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }

        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $extension = [System.IO.Path]::GetExtension(
                $path
            ).ToLowerInvariant()

            if ($Script:AllowedInputExtensions -contains $extension) {
                $full = [System.IO.Path]::GetFullPath($path)
                $key = $full.ToLowerInvariant()

                if (-not $seen.ContainsKey($key)) {
                    $seen[$key] = $true
                    $files.Add($full)
                }
            }

            continue
        }

        if (Test-Path -LiteralPath $path -PathType Container) {
            $arguments = @{
                LiteralPath = $path
                File = $true
                ErrorAction = "Stop"
            }

            if ($Recursive) {
                $arguments.Recurse = $true
            }

            foreach ($file in Get-ChildItem @arguments) {
                $extension = $file.Extension.ToLowerInvariant()

                if ($Script:AllowedInputExtensions -notcontains $extension) {
                    continue
                }

                $key = $file.FullName.ToLowerInvariant()

                if (-not $seen.ContainsKey($key)) {
                    $seen[$key] = $true
                    $files.Add($file.FullName)
                }
            }
        }
    }

    return @($files)
}

function Stage-AdditionalInputs {
    param(
        [Parameter(Mandatory)]$Sources,
        [Parameter(Mandatory)][string]$InputPath,
        [Parameter(Mandatory)][bool]$Recursive,
        [Parameter(Mandatory)][string]$RunDir
    )

    $inputFolder = $InputPath

    if (
        Test-Path `
            -LiteralPath $InputPath `
            -PathType Leaf
    ) {
        $inputFolder = Split-Path -Parent $InputPath
    }

    Ensure-Directory -Path $inputFolder

    $files = Get-InputSourceFiles `
        -Sources $Sources `
        -Recursive $Recursive

    $rows = @()

    foreach ($source in $files) {
        $destinationInfo = Resolve-CollisionSafeDestination `
            -Source $source `
            -DestinationFolder $inputFolder

        if ($destinationInfo.state -ne "EXACT_EXISTS_SKIP") {
            if (-not (Test-Path -LiteralPath $destinationInfo.path -PathType Leaf)) {
                Copy-Item `
                    -LiteralPath $source `
                    -Destination $destinationInfo.path `
                    -Force
            }
        }

        $postSha = Get-Sha256 -Path $destinationInfo.path

        if ($postSha -ne $destinationInfo.sha256) {
            throw (
                "Staged VDF input SHA verification failed: " +
                $destinationInfo.path
            )
        }

        $rows += [ordered]@{
            source = $source
            destination = $destinationInfo.path
            source_sha256 = $destinationInfo.sha256
            destination_sha256 = $postSha
            state = $destinationInfo.state
            bytes = (
                Get-Item -LiteralPath $destinationInfo.path
            ).Length
        }
    }

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $RunDir `
                -ChildPath "evidence\staged_inputs.json"
        ) `
        -Value $rows

    return $rows
}

function Get-PowerShellParameterNames {
    param([Parameter(Mandatory)][string]$Path)

    $tokens = $null
    $errors = $null

    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$errors
    )

    if (@($errors).Count -gt 0) {
        throw (
            "VDF entrypoint PowerShell AST failed: " +
            (
                @($errors) |
                ForEach-Object {
                    "L{0}:C{1} {2}" -f
                        $_.Extent.StartLineNumber,
                        $_.Extent.StartColumnNumber,
                        $_.Message
                } |
                Out-String
            )
        )
    }

    if ($null -eq $ast.ParamBlock) {
        return @()
    }

    return @(
        $ast.ParamBlock.Parameters |
        ForEach-Object {
            $_.Name.VariablePath.UserPath
        }
    )
}

function Add-FirstSupportedParameter {
    param(
        [Parameter(Mandatory)][hashtable]$Arguments,
        [Parameter(Mandatory)][string[]]$Supported,
        [Parameter(Mandatory)][string[]]$Names,
        [AllowNull()]$Value
    )

    foreach ($name in $Names) {
        if ($Supported -contains $name) {
            $Arguments[$name] = $Value
            return $name
        }
    }

    return ""
}

function Build-VdfPowerShellArguments {
    param(
        [Parameter(Mandatory)][string]$EntrypointPath,
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot,
        [Parameter(Mandatory)][string]$PythonPath,
        [Parameter(Mandatory)]$Parameters
    )

    $supported = Get-PowerShellParameterNames -Path $EntrypointPath
    $arguments = @{}
    $mapping = @()

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "Base",
            "BaseDir",
            "BaseRoot",
            "VIA_ROOT",
            "Root"
        ) `
        -Value $BaseRoot

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "Base->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "VDFRoot",
            "VdfRoot",
            "ProjectRoot"
        ) `
        -Value $VdfRoot

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "VDFRoot->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "Input",
            "InputPath",
            "InputDir",
            "DataSource",
            "Source",
            "SourcePath"
        ) `
        -Value ([string]$Parameters.input)

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "Input->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "StartDate",
            "SinceDate",
            "DateFrom",
            "FromDate"
        ) `
        -Value ([string]$Parameters.startDate)

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "StartDate->$selected"
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$Parameters.endDate)) {
        $selected = Add-FirstSupportedParameter `
            -Arguments $arguments `
            -Supported $supported `
            -Names @(
                "EndDate",
                "UntilDate",
                "DateTo",
                "ToDate"
            ) `
            -Value ([string]$Parameters.endDate)

        if (-not [string]::IsNullOrWhiteSpace($selected)) {
            $mapping += "EndDate->$selected"
        }
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "Universe",
            "Tickers",
            "Symbols",
            "TickerList"
        ) `
        -Value ([string]$Parameters.universe)

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "Universe->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "UpdateMode",
            "RunMode",
            "Mode"
        ) `
        -Value ([string]$Parameters.updateMode)

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "UpdateMode->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "PythonPath",
            "Python",
            "PythonExe"
        ) `
        -Value $PythonPath

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "Python->$selected"
    }

    $selected = Add-FirstSupportedParameter `
        -Arguments $arguments `
        -Supported $supported `
        -Names @(
            "OpenHtml",
            "OpenHtmlReport",
            "OpenUI",
            "OpenReport"
        ) `
        -Value $false

    if (-not [string]::IsNullOrWhiteSpace($selected)) {
        $mapping += "OpenHtml->$selected"
    }

    return [ordered]@{
        supported_parameters = $supported
        invocation_arguments = $arguments
        mapping = $mapping
    }
}

function Convert-HashtableToPowerShellArguments {
    param([Parameter(Mandatory)][hashtable]$Arguments)

    $result = [System.Collections.Generic.List[string]]::new()

    foreach ($key in @($Arguments.Keys | Sort-Object)) {
        $value = $Arguments[$key]
        $result.Add("-$key")

        if ($value -is [bool]) {
            if ($value) {
                [void]$result.Add('$true')
            }
            else {
                [void]$result.Add('$false')
            }
        }
        else {
            $escaped = ([string]$value).Replace('"', '\"')
            [void]$result.Add('"{0}"' -f $escaped)
        }
    }

    return @($result)
}

function Update-WorkerStatus {
    param(
        [Parameter(Mandatory)][string]$StatusPath,
        [Parameter(Mandatory)][string]$State,
        [Parameter(Mandatory)][int]$Percent,
        [Parameter(Mandatory)][string]$Message,
        [AllowNull()]$Extra = $null
    )

    $payload = [ordered]@{
        version = $Script:Version
        updated_at = Get-NowIso
        state = $State
        percent = $Percent
        message = $Message
        terminal = (
            $State -in @(
                "COMPLETED",
                "FAILED"
            )
        )
    }

    if ($null -ne $Extra) {
        foreach ($property in $Extra.PSObject.Properties) {
            $payload[$property.Name] = $property.Value
        }
    }

    Write-JsonAtomic -Path $StatusPath -Value $payload
}

function Invoke-VdfEntrypoint {
    param(
        [Parameter(Mandatory)]$Entrypoint,
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot,
        [Parameter(Mandatory)][string]$PythonPath,
        [Parameter(Mandatory)]$Parameters,
        [Parameter(Mandatory)][string]$RunDir,
        [Parameter(Mandatory)][int]$TimeoutSeconds
    )

    $stdoutPath = Join-Path `
        -Path $RunDir `
        -ChildPath "logs\vdf.stdout.log"

    $stderrPath = Join-Path `
        -Path $RunDir `
        -ChildPath "logs\vdf.stderr.log"

    $process = $null
    $contract = [ordered]@{
        entrypoint_type = $Entrypoint.type
        entrypoint_path = $Entrypoint.path
        arguments = @()
        supported_parameters = @()
        parameter_mapping = @()
        working_directory = $VdfRoot
    }

    if ($Entrypoint.type -eq "POWERSHELL") {
        $binding = Build-VdfPowerShellArguments `
            -EntrypointPath $Entrypoint.path `
            -BaseRoot $BaseRoot `
            -VdfRoot $VdfRoot `
            -PythonPath $PythonPath `
            -Parameters $Parameters

        $entryArguments = Convert-HashtableToPowerShellArguments `
            -Arguments $binding.invocation_arguments

        $contract.arguments = $entryArguments
        $contract.supported_parameters = $binding.supported_parameters
        $contract.parameter_mapping = $binding.mapping
        $contract.working_directory = Split-Path -Parent $Entrypoint.path

        $pwshPath = (Get-Process -Id $PID).Path

        $argumentList = @(
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ('"{0}"' -f $Entrypoint.path)
        ) + $entryArguments

        $process = Start-Process `
            -FilePath $pwshPath `
            -ArgumentList $argumentList `
            -WorkingDirectory $contract.working_directory `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru
    }
    elseif ($Entrypoint.type -eq "PYTHON_MODULE") {
        $contract.arguments = @(
            "-m",
            $Entrypoint.package,
            "--once"
        )

        $contract.working_directory = $Entrypoint.working_directory

        $process = Start-Process `
            -FilePath $PythonPath `
            -ArgumentList $contract.arguments `
            -WorkingDirectory $contract.working_directory `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru
    }
    elseif ($Entrypoint.type -eq "PYTHON_SCRIPT") {
        $contract.arguments = @(
            ('"{0}"' -f $Entrypoint.path),
            "--once"
        )

        $contract.working_directory = $Entrypoint.working_directory

        $process = Start-Process `
            -FilePath $PythonPath `
            -ArgumentList $contract.arguments `
            -WorkingDirectory $contract.working_directory `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru
    }
    else {
        throw "Unsupported VDF entrypoint type: $($Entrypoint.type)"
    }

    Write-JsonAtomic `
        -Path (
            Join-Path `
                -Path $RunDir `
                -ChildPath "evidence\vdf_invocation_contract.json"
        ) `
        -Value $contract

    $started = Get-Date

    while (-not $process.HasExited) {
        $elapsed = (Get-Date) - $started

        if ($elapsed.TotalSeconds -ge $TimeoutSeconds) {
            return [ordered]@{
                state = "TIMEOUT_CHILD_LEFT_RUNNING"
                exit_code = $null
                process_id = $process.Id
                elapsed_seconds = [math]::Round(
                    $elapsed.TotalSeconds,
                    2
                )
                stdout = $stdoutPath
                stderr = $stderrPath
                contract = $contract
            }
        }

        Start-Sleep -Milliseconds 500
        $process.Refresh()
    }

    $process.Refresh()

    return [ordered]@{
        state = if ($process.ExitCode -eq 0) {
            "COMPLETED"
        }
        else {
            "FAILED_EXIT_CODE"
        }
        exit_code = $process.ExitCode
        process_id = $process.Id
        elapsed_seconds = [math]::Round(
            ((Get-Date) - $started).TotalSeconds,
            2
        )
        stdout = $stdoutPath
        stderr = $stderrPath
        contract = $contract
    }
}

function Get-VdfOutputInventory {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$VdfRoot
    )

    $roots = @(
        (Join-Path -Path $VdfRoot -ChildPath "output"),
        (Join-Path -Path $VdfRoot -ChildPath "outputs"),
        (Join-Path -Path $VdfRoot -ChildPath "data"),
        (Join-Path -Path $BaseRoot -ChildPath "output"),
        (Join-Path -Path $BaseRoot -ChildPath "outputs")
    )

    $files = @()

    foreach ($root in $roots) {
        if (Test-Path -LiteralPath $root -PathType Container) {
            $files += @(
                Get-ChildItem `
                    -LiteralPath $root `
                    -Recurse `
                    -File `
                    -ErrorAction SilentlyContinue
            )
        }
    }

    $unique = @(
        $files |
        Sort-Object FullName -Unique
    )

    $extensionRows = @(
        $unique |
        Group-Object {
            $_.Extension.ToLowerInvariant()
        } |
        Sort-Object Count -Descending |
        ForEach-Object {
            [ordered]@{
                extension = if ([string]::IsNullOrWhiteSpace($_.Name)) {
                    "(none)"
                }
                else {
                    $_.Name
                }
                count = $_.Count
                bytes = (
                    $_.Group |
                    Measure-Object -Property Length -Sum
                ).Sum
            }
        }
    )

    return [ordered]@{
        total_files = $unique.Count
        total_bytes = (
            $unique |
            Measure-Object -Property Length -Sum
        ).Sum
        parquet_count = @(
            $unique |
            Where-Object {
                $_.Extension -eq ".parquet"
            }
        ).Count
        duckdb_count = @(
            $unique |
            Where-Object {
                $_.Extension -eq ".duckdb"
            }
        ).Count
        csv_count = @(
            $unique |
            Where-Object {
                $_.Extension -eq ".csv"
            }
        ).Count
        json_count = @(
            $unique |
            Where-Object {
                $_.Extension -in @(
                    ".json",
                    ".jsonl"
                )
            }
        ).Count
        html_count = @(
            $unique |
            Where-Object {
                $_.Extension -in @(
                    ".html",
                    ".htm"
                )
            }
        ).Count
        extensions = $extensionRows
        latest_files = @(
            $unique |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 30 |
            ForEach-Object {
                [ordered]@{
                    path = $_.FullName
                    extension = $_.Extension
                    bytes = $_.Length
                    last_write = $_.LastWriteTime.ToString("o")
                }
            }
        )
    }
}

function Invoke-WorkerMode {
    param([Parameter(Mandatory)][string]$ConfigPath)

    $config = Get-Content `
        -LiteralPath $ConfigPath `
        -Raw `
        -Encoding UTF8 |
        ConvertFrom-Json

    $statusPath = [string]$config.statusPath
    $runDir = [string]$config.runDir

    try {
        foreach ($folder in @(
            $runDir,
            (Join-Path -Path $runDir -ChildPath "registry"),
            (Join-Path -Path $runDir -ChildPath "evidence"),
            (Join-Path -Path $runDir -ChildPath "logs")
        )) {
            Ensure-Directory -Path $folder
        }

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 3 `
            -Message "Resolving Base, VDF root and seven parameters."

        $baseRoot = Resolve-BaseRoot `
            -Requested ([string]$config.parameters.base)

        $vdfRoot = Resolve-VdfRoot -BaseRoot $baseRoot

        $pythonPath = Resolve-PythonRuntime `
            -Requested "" `
            -BaseRoot $baseRoot `
            -VdfRoot $vdfRoot

        if ([string]::IsNullOrWhiteSpace($pythonPath)) {
            throw "No usable Python runtime was resolved."
        }

        $timeout = [int]$config.parameters.timeoutSeconds

        if ($timeout -lt 60 -or $timeout -gt 86400) {
            throw "Timeout must be between 60 and 86400 seconds."
        }

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 10 `
            -Message "Discovering the canonical VDF entrypoint."

        $entrypoint = Resolve-VdfEntrypoint `
            -VdfRoot $vdfRoot `
            -PythonPath $pythonPath

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 20 `
            -Message "Importing approved PowerShell modules."

        $powerShellRegistry = Import-AndRegisterPowerShellModules `
            -RunDir $runDir

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 32 `
            -Message "Verifying VDF Python data libraries."

        $pythonRegistry = Test-AndRegisterPythonRuntime `
            -PythonPath $pythonPath `
            -RunDir $runDir

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 44 `
            -Message "SHA-registering supportive tools and VDF code."

        $codeRegistry = Register-CodeInventory `
            -BaseRoot $baseRoot `
            -VdfRoot $vdfRoot `
            -RunDir $runDir

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 55 `
            -Message "Staging optional local data sources."

        $stagedInputs = Stage-AdditionalInputs `
            -Sources $config.sources `
            -InputPath ([string]$config.parameters.input) `
            -Recursive ([bool]$config.parameters.recursive) `
            -RunDir $runDir

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 67 `
            -Message "Launching the discovered VDF entrypoint."

        $invocation = Invoke-VdfEntrypoint `
            -Entrypoint $entrypoint `
            -BaseRoot $baseRoot `
            -VdfRoot $vdfRoot `
            -PythonPath $pythonPath `
            -Parameters $config.parameters `
            -RunDir $runDir `
            -TimeoutSeconds $timeout

        if ($invocation.state -eq "TIMEOUT_CHILD_LEFT_RUNNING") {
            throw (
                "VDF exceeded the timeout. The child process was not " +
                "forcibly terminated. PID=$($invocation.process_id)"
            )
        }

        if ($invocation.state -ne "COMPLETED") {
            $stderrTail = ""

            if (Test-Path -LiteralPath $invocation.stderr -PathType Leaf) {
                $stderrTail = (
                    Get-Content `
                        -LiteralPath $invocation.stderr `
                        -Tail 120 `
                        -Encoding UTF8
                ) -join [Environment]::NewLine
            }

            throw (
                "VDF entrypoint failed with exit code " +
                "$($invocation.exit_code). STDERR=$stderrTail"
            )
        }

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 88 `
            -Message "Discovering output pages and data-quality evidence."

        $views = Resolve-VdfViewPages `
            -BaseRoot $baseRoot `
            -VdfRoot $vdfRoot

        $outputInventory = Get-VdfOutputInventory `
            -BaseRoot $baseRoot `
            -VdfRoot $vdfRoot

        $gate = if ($outputInventory.total_files -gt 0) {
            "VDF_ONECLICK_RUNTIME_COMPLETED_OUTPUTS_DISCOVERED"
        }
        else {
            "VDF_ONECLICK_RUNTIME_COMPLETED_NO_OUTPUT_FILES_DISCOVERED"
        }

        $final = [ordered]@{
            gate = $gate
            base = $baseRoot
            vdf_root = $vdfRoot
            input = [string]$config.parameters.input
            start_date = [string]$config.parameters.startDate
            end_date = [string]$config.parameters.endDate
            universe = [string]$config.parameters.universe
            update_mode = [string]$config.parameters.updateMode
            open_html = [bool]$config.parameters.openHtml
            python = $pythonPath
            entrypoint_type = $entrypoint.type
            entrypoint_path = $entrypoint.path
            entrypoint_sha256 = Get-Sha256 -Path $entrypoint.path
            invocation = $invocation
            staged_input_count = @($stagedInputs).Count
            powerShell_import_count = $powerShellRegistry.imported_count
            powerShell_inventory_count = $powerShellRegistry.inventory_count
            python_package_count = $pythonRegistry.pip_package_count
            python_required_import_count = $pythonRegistry.required_import_count
            python_optional_import_count = $pythonRegistry.optional_import_count
            code_registry = $codeRegistry
            output_inventory = $outputInventory
            basic_info_page = $views.basic_info_page
            financial_data_page = $views.financial_data_page
            market_data_page = $views.market_data_page
            data_quality_page = $views.data_quality_page
            main_ui_page = $views.main_ui_page
            workbench_run_dir = $runDir
            authority_mutation_by_wrapper = $false
            network_install_executed = $false
        }

        Write-JsonAtomic `
            -Path (
                Join-Path `
                    -Path $runDir `
                    -ChildPath "final_summary.v0160A.json"
            ) `
            -Value $final

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "COMPLETED" `
            -Percent 100 `
            -Message "VDF completed and the latest output pages were discovered." `
            -Extra ([pscustomobject]$final)
    }
    catch {
        $failure = [ordered]@{
            error_type = $_.Exception.GetType().FullName
            error_message = $_.Exception.Message
            stack_trace = $_.ScriptStackTrace
            workbench_run_dir = $runDir
        }

        Write-JsonAtomic `
            -Path (
                Join-Path `
                    -Path $runDir `
                    -ChildPath "failure.v0160A.json"
            ) `
            -Value $failure

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "FAILED" `
            -Percent 100 `
            -Message $_.Exception.Message `
            -Extra ([pscustomobject]$failure)

        exit 3
    }
}

function Write-DialogHelper {
    param([Parameter(Mandatory)][string]$Path)

    $helper = @'
#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$Mode,
    [Parameter(Mandatory)][string]$Output,
    [string]$Current = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

$result = @()

switch ($Mode) {
    "Folder" {
        $dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
        $dialog.Description = "VIA VDF — Select folder"
        $dialog.UseDescriptionForTitle = $true

        if (
            -not [string]::IsNullOrWhiteSpace($Current) -and
            (
                Test-Path `
                    -LiteralPath $Current `
                    -PathType Container
            )
        ) {
            $dialog.SelectedPath = $Current
        }

        if (
            $dialog.ShowDialog() -eq
            [System.Windows.Forms.DialogResult]::OK
        ) {
            $result = @($dialog.SelectedPath)
        }

        $dialog.Dispose()
    }

    "Files" {
        $dialog = [System.Windows.Forms.OpenFileDialog]::new()
        $dialog.Multiselect = $true
        $dialog.Filter =
            "VDF data sources|*.csv;*.xlsx;*.xls;*.json;*.jsonl;*.parquet;*.duckdb;*.db;*.sqlite;*.txt;*.yaml;*.yml|All files (*.*)|*.*"

        if (
            -not [string]::IsNullOrWhiteSpace($Current) -and
            (
                Test-Path `
                    -LiteralPath $Current `
                    -PathType Container
            )
        ) {
            $dialog.InitialDirectory = $Current
        }

        if (
            $dialog.ShowDialog() -eq
            [System.Windows.Forms.DialogResult]::OK
        ) {
            $result = @($dialog.FileNames)
        }

        $dialog.Dispose()
    }

    default {
        throw "Unsupported dialog mode: $Mode"
    }
}

$result |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -LiteralPath $Output `
        -Encoding UTF8
'@

    Write-Utf8NoBomAtomic -Path $Path -Text $helper
}

function Get-HtaHtml {
    param(
        [Parameter(Mandatory)]$Defaults,
        [Parameter(Mandatory)][string]$ConfigPath,
        [Parameter(Mandatory)][string]$StatusPath,
        [Parameter(Mandatory)][string]$DialogHelperPath,
        [Parameter(Mandatory)][string]$MainScriptPath,
        [Parameter(Mandatory)][string]$PowerShellPath
    )

    $defaultsJson = $Defaults | ConvertTo-Json -Depth 30 -Compress
    $configJson = $ConfigPath | ConvertTo-Json -Compress
    $statusJson = $StatusPath | ConvertTo-Json -Compress
    $dialogJson = $DialogHelperPath | ConvertTo-Json -Compress
    $mainJson = $MainScriptPath | ConvertTo-Json -Compress
    $pwshJson = $PowerShellPath | ConvertTo-Json -Compress

    $html = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA · VDF Sidebar Workbench</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@600&family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
    --bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;
    --mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;
    --up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;
    --am:#c4943a;--vi:#7a6daa;--sidebar:#f8f7f3;
    --reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%),
    --serif:"Cormorant Garamond",Georgia,serif;
    --cjkserif:"Noto Serif TC","Noto Serif CJK TC","PMingLiU",serif
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
    background:var(--bg);color:var(--ink2);
    font:11px/1.5 "DM Sans","Noto Sans TC","Microsoft JhengHei",sans-serif
}
.bar{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:100}
.sidebar{
    position:fixed;top:4px;left:0;bottom:0;width:236px;
    background:var(--sidebar);border-right:1px solid var(--line);
    padding:18px 14px;overflow:auto;z-index:60
}
.brand{padding:2px 5px 13px;border-bottom:2px solid var(--ink)}
.brand .eyebrow{display:flex;align-items:center;gap:7px;margin-bottom:8px}
.brand .chip{padding:2px 7px;background:var(--ink);color:#fff;font:700 7.5px "DM Mono",Consolas,monospace;letter-spacing:.14em}
.brand .ey{font:700 7px "DM Mono",Consolas,monospace;letter-spacing:.13em;color:var(--mut);text-transform:uppercase}
.brand .mastrow{display:flex;align-items:center;gap:9px}
.brand .seal{width:34px;height:34px;background:var(--ink);color:#f2f1ec;display:flex;align-items:center;justify-content:center;font-family:var(--cjkserif);font-size:19px;border-radius:4px;flex:none}
.brand .wm{font:600 14.5px/1.15 var(--serif);letter-spacing:.09em;color:var(--ink);white-space:nowrap}
.brand .wmcjk{margin-top:2px;font:600 9px var(--cjkserif);letter-spacing:.2em;color:var(--mut)}
.brand p{margin-top:7px;color:var(--mut);font-size:9.5px}
.group{margin-top:18px}
.groupTitle{
    margin:0 6px 6px;font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut2);letter-spacing:1.2px;text-transform:uppercase
}
.nav button{
    display:block;width:100%;text-align:left;margin-bottom:4px;
    border:1px solid transparent;border-radius:4px;background:transparent;
    color:var(--ink2);padding:8px 9px;
    font:700 8.3px "DM Mono",Consolas,monospace;cursor:pointer
}
.nav button:hover{background:var(--paper);border-color:var(--line)}
.nav button.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.nav .n{display:inline-block;min-width:22px;color:var(--mut2)}
.nav button.active .n{color:#fff}
.sideMetrics{margin-top:16px;border-top:1px solid var(--line);padding-top:12px}
.sm{display:flex;justify-content:space-between;gap:8px;padding:5px 3px;border-bottom:1px solid var(--soft)}
.sm .k{font:700 7.5px "DM Mono",Consolas,monospace;color:var(--mut)}
.sm .v{
    max-width:115px;text-align:right;overflow-wrap:anywhere;
    font:700 8px "DM Mono",Consolas,monospace;color:var(--ink)
}
.workspace{margin-left:236px;min-height:100vh}
.inner{max-width:1240px;margin:0 auto;padding:0 22px 54px}
header{padding:22px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink)}
.kicker{
    font:700 10px "DM Mono",Consolas,monospace;
    letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px
}
h1{font:600 21px/1.25 var(--serif),var(--cjkserif);letter-spacing:.04em;color:var(--ink)}
h1{font-family:"Cormorant Garamond","Noto Serif TC","Noto Serif CJK TC",Georgia,"PMingLiU",serif}
h1 span{color:var(--teal)}
.sub{margin-top:6px;color:var(--mut);font-size:10.5px}
.page{display:none}.page.active{display:block}
.hero{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px}
.card{
    background:var(--paper);border:1px solid var(--line);
    border-radius:5px;padding:10px 15px;min-width:125px
}
.card .v{
    font:800 18px "Syne","Microsoft JhengHei",sans-serif;
    line-height:1;overflow-wrap:anywhere
}
.card .l{
    font:600 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase;margin-top:4px
}
h2{
    font:800 13px "Syne","Microsoft JhengHei",sans-serif;
    color:var(--ink);margin:24px 0 8px;padding-bottom:5px;
    border-bottom:1px solid var(--line)
}
h2 .en{
    font:600 8px "DM Mono",Consolas,monospace;
    color:var(--mut2);letter-spacing:1px;margin-left:8px;text-transform:uppercase
}
.panel{
    background:var(--paper);border:1px solid var(--line);
    border-radius:6px;padding:14px 16px;margin-top:10px
}
.inputPanel{border-left:3px solid var(--up)}
.summaryPanel{border-left:3px solid var(--teal)}
.sourcePanel{border-left:3px solid var(--am)}
.basicPanel{border-left:3px solid var(--blue)}
.financialPanel{border-left:3px solid var(--vi)}
.marketPanel{border-left:3px solid var(--teal)}
.qualityPanel{border-left:3px solid var(--down)}
.registryPanel{border-left:3px solid var(--ink)}
.logPanel{border-left:3px solid var(--mut)}
.columns{display:flex;gap:12px;align-items:flex-start}
.mainColumn{flex:1;min-width:0}
.asideColumn{width:355px;min-width:320px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.full{grid-column:1/3}
.field{border-bottom:1px solid var(--soft);padding:8px 0}
label{
    display:block;font:700 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase;margin-bottom:5px
}
.row{display:flex;align-items:center;gap:6px}
input[type=text],input[type=number],select{
    width:100%;border:1px solid var(--line);border-radius:4px;padding:7px 9px;
    background:#fafaf8;color:var(--ink2);
    font:500 10px "DM Mono",Consolas,monospace
}
input:focus,select:focus{outline:1px solid var(--teal);border-color:var(--teal)}
.check{display:flex;align-items:center;gap:7px;min-height:30px}
button{
    border:1px solid var(--line);border-radius:4px;padding:7px 10px;
    background:var(--paper);color:var(--ink2);
    font:700 8px "DM Mono",Consolas,monospace;cursor:pointer
}
button:hover{background:#fafaf8}
button.primary{color:#fff;background:var(--teal);border-color:var(--teal)}
button.danger{color:#fff;background:var(--up);border-color:var(--up)}
button:disabled{opacity:.45}
.hint{color:var(--mut);font-size:9px;margin-top:4px}
.drop{
    border:1px dashed var(--mut2);border-radius:5px;background:#fafaf8;
    padding:18px;text-align:center;color:var(--mut)
}
.drop.active{border-color:var(--teal);background:#eef7f5}
.drop b{
    display:block;color:var(--ink);
    font:800 11px "Syne","Microsoft JhengHei",sans-serif
}
.drop span{display:block;margin-top:4px;font-size:9px}
.actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
.progressOuter{height:9px;background:var(--soft);border-radius:3px;overflow:hidden;margin-top:12px}
.progressInner{height:100%;width:0%;background:var(--reson)}
.status{display:grid;grid-template-columns:120px 1fr;gap:5px 10px;margin-top:11px}
.k{font:700 8px "DM Mono",Consolas,monospace;color:var(--mut);text-transform:uppercase}
.code{font-family:"DM Mono",Consolas,monospace;overflow-wrap:anywhere}
.pill{
    display:inline-block;font:700 7.5px "DM Mono",Consolas,monospace;
    color:#fff;border-radius:3px;padding:2px 7px
}
.ok{background:var(--down)}.warn{background:var(--am)}
.blind{background:var(--mut2)}.prov{background:var(--vi)}
.queue{
    margin-top:10px;border:1px solid var(--line);
    border-radius:4px;max-height:430px;overflow:auto
}
.queueItem{
    display:flex;justify-content:space-between;gap:10px;
    padding:7px 9px;border-bottom:1px solid var(--soft);
    font:500 9px "DM Mono",Consolas,monospace
}
.viewerTop{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.viewerPath{
    color:var(--mut);font:500 9px "DM Mono",Consolas,monospace;
    overflow-wrap:anywhere;margin-top:6px
}
.frameWrap{margin-top:10px;border:1px solid var(--line);background:#fafaf8;min-height:620px}
iframe{display:block;width:100%;height:620px;border:0;background:#fff}
.empty{padding:80px 20px;text-align:center;color:var(--mut)}
.empty b{
    display:block;color:var(--ink);
    font:800 14px "Syne","Microsoft JhengHei",sans-serif;margin-bottom:6px
}
.registryGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.registryCard{
    border:1px solid var(--line);border-radius:5px;background:#fafaf8;
    padding:11px;min-height:88px
}
.registryCard .l{
    font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.registryCard .v{
    margin-top:7px;color:var(--ink);
    font:700 10px/1.45 "DM Mono",Consolas,monospace;
    overflow-wrap:anywhere
}
.log{
    background:#f8f8f5;color:var(--ink2);
    border:1px solid var(--line);border-radius:4px;padding:10px;
    min-height:500px;max-height:680px;overflow:auto;white-space:pre-wrap;
    font:500 9px/1.55 "DM Mono",Consolas,monospace
}
table{width:100%;border-collapse:collapse;font:500 10px "DM Mono",Consolas,monospace}
th{
    font:700 8px "DM Mono",Consolas,monospace;text-transform:uppercase;
    color:var(--mut);text-align:left;padding:6px 9px;
    border-bottom:2px solid var(--ink);background:#fafaf8
}
td{padding:5px 9px;border-bottom:1px solid var(--soft);vertical-align:top}
.footer{margin-top:14px;color:var(--mut2);font:500 8px "DM Mono",Consolas,monospace}
@media(max-width:980px){
    .sidebar{width:196px}.workspace{margin-left:196px}
    .columns{display:block}.asideColumn{width:auto;min-width:0}
    .grid{grid-template-columns:1fr}.full{grid-column:auto}
    .registryGrid{grid-template-columns:1fr}
}
</style>
<script>
var defaults=__DEFAULTS__;
var configPath=__CONFIG__;
var statusPath=__STATUS__;
var dialogHelper=__DIALOG__;
var mainScript=__MAIN__;
var pwshPath=__PWSH__;
var sources=[];
var workerStarted=false;
var timerId=0;
var pages={
    basic:defaults.basicInfoPage||"",
    financial:defaults.financialDataPage||"",
    market:defaults.marketDataPage||"",
    quality:defaults.dataQualityPage||""
};

function byId(id){return document.getElementById(id);}
function quote(value){return '"' + String(value).replace(/"/g,'""') + '"';}
function setText(id,value){var node=byId(id);if(node){node.innerText=value;}}
function setHtml(id,value){var node=byId(id);if(node){node.innerHTML=value;}}
function log(text){
    var box=byId("log");
    box.innerText+="\r\n"+new Date().toLocaleTimeString()+"  "+text;
    box.scrollTop=box.scrollHeight;
}
function apiGet(path,cb){
    fetch(path).then(function(r){return r.json();}).then(cb).catch(function(e){log("API: "+e.message);});
}
function apiPost(path,obj,cb){
    fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(obj)})
        .then(function(r){return r.json();}).then(cb||function(){}).catch(function(e){log("API: "+e.message);});
}
function openPath(p){if(!p){return;}apiPost("/api/open",{path:p});}
function switchPage(name){
    var names=["home","sources","basic","financial","market","quality","registry","logs"];
    var labels={
        home:["首頁 · 輸入與摘要","Home · Input + Summary"],
        sources:["Data Sources","Local files, folders and staged inputs"],
        basic:["Basic Info","Company and security master data"],
        financial:["Financial Data","Statements, ratios and estimates"],
        market:["Market Data","Prices, volume, flows and indices"],
        quality:["Data Quality","Validation, freshness and evidence"],
        registry:["Output Registry","Runtime, libraries and generated files"],
        logs:["Execution Logs","Worker events and invocation evidence"]
    };
    for(var i=0;i<names.length;i++){
        var page=names[i];
        byId("page-"+page).className="page"+(page===name?" active":"");
        byId("nav-"+page).className=page===name?"active":"";
    }
    setText("pageTitle",labels[name][0]);
    setText("pageSubtitle",labels[name][1]);
    if(name==="basic"||name==="financial"||name==="market"||name==="quality"){loadView(name);}
}
function setDefaults(d){
    byId("base").value=d.base||"";
    byId("input").value=d.input||"";
    byId("startDate").value=d.startDate||"";
    byId("endDate").value=d.endDate||"";
    byId("universe").value=d.universe||"DEFAULT";
    byId("updateMode").value=d.updateMode||"Incremental";
    byId("openHtml").checked=!!d.openHtml;
    setText("vdfRoot",d.vdfRoot||"");
}
function toFileUrl(path){
    if(!path){return "";}
    return "file:///"+encodeURI(String(path).replace(/\\/g,"/").replace(/^\/+/,""));
}
function setViewPath(name,path){
    pages[name]=path||"";
    setText(name+"Path",pages[name]||"尚未找到對應 HTML");
}
function loadView(name){
    var path=pages[name];
    var frame=byId(name+"Frame");
    var empty=byId(name+"Empty");
    if(!path){frame.style.display="none";frame.src="about:blank";empty.style.display="block";return;}
    apiGet("/api/exists?path="+encodeURIComponent(path),function(r){
        if(r&&r.exists){frame.style.display="block";empty.style.display="none";frame.src="/view?path="+encodeURIComponent(path);}
        else{frame.style.display="none";frame.src="about:blank";empty.style.display="block";}
    });
}
function openView(name){
    var path=pages[name];
    if(path){openPath(path);}
    else{log("尚未找到 "+name+" HTML。");}
}
function runDialog(mode,current,cb){
    apiGet("/api/dialog?mode="+encodeURIComponent(mode)+"&current="+encodeURIComponent(current||""),function(r){
        if(!r){cb([]);return;}
        if(r instanceof Array){cb(r);}else{cb([r]);}
    });
}
function browseFolder(id){
    runDialog("Folder",byId(id).value,function(values){
        if(values.length>0){byId(id).value=values[0];}
    });
}
function addFiles(){
    runDialog("Files",byId("input").value,function(values){
        for(var i=0;i<values.length;i++){sources.push({kind:"file",path:values[i]});}
        renderSources();
    });
}
function addFolder(){
    runDialog("Folder",byId("input").value,function(values){
        if(values.length>0){sources.push({kind:"folder",path:values[0]});renderSources();}
    });
}
function renderSources(){
    var box=byId("sourceQueue");box.innerHTML="";
    setText("sourceCount",sources.length);setText("sideSources",sources.length);
    if(sources.length===0){box.innerHTML='<div class="queueItem">尚未增加額外資料來源。</div>';return;}
    for(var i=0;i<sources.length;i++){
        var row=document.createElement("div");row.className="queueItem";
        var text=document.createElement("span");text.innerText=sources[i].path;
        var remove=document.createElement("button");remove.innerText="移除";remove.setAttribute("data-index",i);
        remove.onclick=function(){var index=parseInt(this.getAttribute("data-index"),10);sources.splice(index,1);renderSources();};
        row.appendChild(text);row.appendChild(remove);box.appendChild(row);
    }
}
function onDrop(event){
    event.returnValue=false;
    try{
        var files=event.dataTransfer.files;
        for(var i=0;i<files.length;i++){
            var path=files[i].path||files[i].value||"";
            if(path){sources.push({kind:"drag",path:path});}
            else{log("瀏覽器拖曳不提供完整路徑；請使用「Windows 選檔」按鈕。");}
        }
        renderSources();
    }catch(e){log("Drag/drop: "+e.message);}
    byId("dropHome").className="drop";byId("dropSources").className="drop";
}
function bindDrop(id){
    var node=byId(id);
    node.ondragenter=function(){this.className="drop active";return false;};
    node.ondragover=function(){return false;};
    node.ondragleave=function(){this.className="drop";return false;};
    node.ondrop=onDrop;
}
function submitRun(){
    if(workerStarted){return;}
    var parameters={
        base:byId("base").value,
        input:byId("input").value,
        startDate:byId("startDate").value,
        endDate:byId("endDate").value,
        universe:byId("universe").value,
        updateMode:byId("updateMode").value,
        openHtml:byId("openHtml").checked,
        recursive:true,
        timeoutSeconds:2400
    };
    var runDir=parameters.base+"\\_via_vdf_runs\\RUN_"+new Date().getTime()+"_VDF_ONECLICK_v0160C";
    var config={version:"v0160C",statusPath:statusPath,runDir:runDir,parameters:parameters,sources:sources};
    workerStarted=true;byId("run").disabled=true;
    setHtml("state",'<span class="pill warn">STARTING</span>');
    apiPost("/api/run",config,function(){
        log("VDF worker started.");timerId=window.setInterval(pollStatus,650);
    });
}
function pollStatus(){
    apiGet("/api/status",function(status){
    if(!status||!status.state){return;}
    var percent=parseInt(status.percent||0,10);byId("bar").style.width=percent+"%";
    var cls="pill blind";if(status.state==="COMPLETED"){cls="pill ok";}else if(status.state==="FAILED"){cls="pill warn";}
    setHtml("state",'<span class="'+cls+'">'+status.state+'</span>');
    setText("message",status.message||"");setText("sideState",status.state||"");
    setText("sideProgress",percent+"%");setText("summaryState",status.state||"");
    setText("summaryProgress",percent+"%");
    if(status.gate){setText("gate",status.gate);setText("summaryGate",status.gate);setText("sideGate",status.gate);}
    if(status.entrypoint_path){setText("entrypoint",status.entrypoint_path);setText("summaryEntrypoint",status.entrypoint_type);}
    if(status.staged_input_count!==undefined){setText("stagedInputs",status.staged_input_count);}
    if(status.code_registry){
        setText("registryFiles",status.code_registry.file_count);
        setText("registrySnapshot",status.code_registry.snapshot_sha256);
        setText("registryLedger",status.code_registry.registry_ledger);
    }
    if(status.powerShell_import_count!==undefined){setText("psImports",status.powerShell_import_count);}
    if(status.powerShell_inventory_count!==undefined){setText("psInventory",status.powerShell_inventory_count);}
    if(status.python_package_count!==undefined){setText("pythonPackages",status.python_package_count);}
    if(status.python_required_import_count!==undefined){setText("pythonRequired",status.python_required_import_count);}
    if(status.output_inventory){
        setText("outputFiles",status.output_inventory.total_files);
        setText("parquetCount",status.output_inventory.parquet_count);
        setText("duckdbCount",status.output_inventory.duckdb_count);
        setText("csvCount",status.output_inventory.csv_count);
        setText("htmlCount",status.output_inventory.html_count);
        renderOutputTable(status.output_inventory.latest_files||[]);
    }
    if(status.basic_info_page){setViewPath("basic",status.basic_info_page);}
    if(status.financial_data_page){setViewPath("financial",status.financial_data_page);}
    if(status.market_data_page){setViewPath("market",status.market_data_page);}
    if(status.data_quality_page){setViewPath("quality",status.data_quality_page);}
    if(status.terminal){
        window.clearInterval(timerId);workerStarted=false;byId("run").disabled=false;
        if(status.workbench_run_dir){byId("runDir").disabled=false;byId("runDir").setAttribute("data-path",status.workbench_run_dir);}
        log(status.state+": "+status.message);
        if(status.gate){log("Gate: "+status.gate);}
        if(status.error_message){log("Error: "+status.error_message);}
        if(status.state==="COMPLETED"&&byId("openHtml").checked){
            var target=status.main_ui_page||status.data_quality_page||status.basic_info_page||status.financial_data_page;
            if(target){openPath(target);}
        }
    }
    });
}
function renderOutputTable(rows){
    var body=byId("outputBody");body.innerHTML="";
    for(var i=0;i<rows.length;i++){
        var tr=document.createElement("tr");
        var values=[rows[i].extension,rows[i].bytes,rows[i].last_write,rows[i].path];
        for(var j=0;j<values.length;j++){var td=document.createElement("td");td.innerText=values[j];tr.appendChild(td);}
        body.appendChild(tr);
    }
}
function openDataPath(button){
    var path=button.getAttribute("data-path");
    if(path){openPath(path);}
}
function openManual(path){
    if(!path){return;}
    openPath(path);
}
window.onload=function(){
    setDefaults(defaults);
    setViewPath("basic",defaults.basicInfoPage||"");
    setViewPath("financial",defaults.financialDataPage||"");
    setViewPath("market",defaults.marketDataPage||"");
    setViewPath("quality",defaults.dataQualityPage||"");
    renderSources();switchPage("home");bindDrop("dropHome");bindDrop("dropSources");
};
</script>
</head>
<body>
<div class="bar"></div>
<aside class="sidebar">
<div class="brand"><div class="eyebrow"><span class="chip">v0160C</span><span class="ey">Veritas Intelligence Analytics</span></div><div class="mastrow"><div class="seal">鍛</div><div><div class="wm">VERITAS DATA FORGE</div><div class="wmcjk">維里塔斯 · 資料鍛造 · 工作台</div></div></div><p>Data Forge · Sidebar Edition · v0160C · Browser HTML</p></div>
<div class="group"><div class="groupTitle">Workspace</div><div class="nav">
<button id="nav-home" onclick="switchPage('home')"><span class="n">01</span>HOME · INPUT + SUMMARY</button>
<button id="nav-sources" onclick="switchPage('sources')"><span class="n">02</span>DATA SOURCES</button>
<button id="nav-basic" onclick="switchPage('basic')"><span class="n">03</span>BASIC INFO</button>
<button id="nav-financial" onclick="switchPage('financial')"><span class="n">04</span>FINANCIAL DATA</button>
<button id="nav-market" onclick="switchPage('market')"><span class="n">05</span>MARKET DATA</button>
<button id="nav-quality" onclick="switchPage('quality')"><span class="n">06</span>DATA QUALITY</button>
<button id="nav-registry" onclick="switchPage('registry')"><span class="n">07</span>OUTPUT REGISTRY</button>
<button id="nav-logs" onclick="switchPage('logs')"><span class="n">08</span>EXECUTION LOGS</button>
</div></div>
<div class="sideMetrics">
<div class="sm"><div class="k">STATE</div><div id="sideState" class="v">READY</div></div>
<div class="sm"><div class="k">PROGRESS</div><div id="sideProgress" class="v">0%</div></div>
<div class="sm"><div class="k">SOURCES</div><div id="sideSources" class="v">0</div></div>
<div class="sm"><div class="k">GATE</div><div id="sideGate" class="v">—</div></div>
</div>
<div style="margin-top:14px"><button class="danger" style="width:100%" onclick="window.close()">CLOSE WORKBENCH</button></div>
</aside>

<div class="workspace"><div class="inner">
<header><div class="kicker">VERITAS DATA FORGE · MARKET FACTS · DATA QUALITY · VISUAL LOCK</div><h1 id="pageTitle">首頁 · 輸入與摘要</h1><p id="pageSubtitle" class="sub">Home · Input + Summary</p></header>

<section id="page-home" class="page active">
<div class="hero">
<div class="card"><div id="summaryState" class="v" style="color:var(--teal)">READY</div><div class="l">STATE</div></div>
<div class="card"><div id="summaryProgress" class="v">0%</div><div class="l">PROGRESS</div></div>
<div class="card"><div id="summaryEntrypoint" class="v">AUTO</div><div class="l">ENTRYPOINT</div></div>
<div class="card"><div id="stagedInputs" class="v">0</div><div class="l">STAGED INPUTS</div></div>
<div class="card"><div id="outputFiles" class="v">—</div><div class="l">OUTPUT FILES</div></div>
<div class="card"><div id="parquetCount" class="v">—</div><div class="l">PARQUET</div></div>
<div class="card"><div id="duckdbCount" class="v">—</div><div class="l">DUCKDB</div></div>
<div class="card" style="min-width:270px"><div id="summaryGate" class="v" style="font:700 9px/1.35 &quot;DM Mono&quot;,Consolas,monospace">—</div><div class="l">LATEST GATE</div></div>
</div>

<div class="columns">
<div class="mainColumn">
<h2>① 七個執行參數 <span class="en">seven runtime parameters</span></h2>
<div class="panel inputPanel"><div class="grid">
<div class="field full"><label>1. Base · 母系統根目錄</label><div class="row"><input id="base" type="text"><button onclick="browseFolder('base')">WINDOWS SEARCH</button></div></div>
<div class="field full"><label>2. Input / Data Source</label><div class="row"><input id="input" type="text"><button onclick="browseFolder('input')">WINDOWS SEARCH</button><button onclick="openManual(byId('input').value)">OPEN</button></div></div>
<div class="field"><label>3. Start Date</label><input id="startDate" type="text" placeholder="yyyy-mm-dd"></div>
<div class="field"><label>4. End Date</label><input id="endDate" type="text" placeholder="blank = no end date"></div>
<div class="field full"><label>5. Universe / Tickers</label><input id="universe" type="text" placeholder="DEFAULT or comma-separated symbols"></div>
<div class="field"><label>6. Update Mode</label><select id="updateMode"><option>Incremental</option><option>Refresh</option><option>ValidateOnly</option><option>DryRun</option></select></div>
<div class="field"><label>7. Open Result HTML</label><div class="check"><input id="openHtml" type="checkbox"><span>完成後開啟最新 VDF HTML</span></div></div>
</div></div>
</div>

<div class="asideColumn">
<h2>② 啟動與摘要 <span class="en">one-click execution</span></h2>
<div class="panel summaryPanel">
<div class="actions"><button id="run" class="primary" onclick="submitRun()">ONE-CLICK START VDF</button><button id="runDir" disabled onclick="openDataPath(this)">RUNDIR</button></div>
<div class="progressOuter"><div id="bar" class="progressInner"></div></div>
<div class="status">
<div class="k">STATE</div><div id="state"><span class="pill blind">READY</span></div>
<div class="k">MESSAGE</div><div id="message">等待執行。</div>
<div class="k">VDF ROOT</div><div id="vdfRoot" class="code"></div>
<div class="k">ENTRYPOINT</div><div id="entrypoint" class="code">自動辨識</div>
<div class="k">GATE</div><div id="gate" class="code">—</div>
</div>
</div>

<h2>③ 快速資料輸入 <span class="en">local only</span></h2>
<div id="dropHome" class="drop"><b>拖曳 CSV／Excel／JSON／Parquet</b><span>詳細佇列請使用左側 DATA SOURCES</span></div>
<div class="actions"><button onclick="addFiles()">SELECT FILES</button><button onclick="addFolder()">SELECT FOLDER</button><button onclick="switchPage('sources')">OPEN SOURCES</button></div>
</div>
</div>
</section>

<section id="page-sources" class="page">
<h2>Data Sources <span class="en">windows I/O + drag and drop</span></h2>
<div class="panel sourcePanel">
<div id="dropSources" class="drop"><b>拖曳本機資料來源</b><span>支援 CSV、Excel、JSON、JSONL、Parquet、DuckDB、SQLite、YAML</span></div>
<div class="actions"><button onclick="addFiles()">WINDOWS SELECT FILES</button><button onclick="addFolder()">WINDOWS SELECT FOLDER</button><button onclick="sources=[];renderSources()">CLEAR</button></div>
<div class="status"><div class="k">SOURCE COUNT</div><div id="sourceCount">0</div><div class="k">TARGET</div><div>使用首頁 Input 路徑；同名不同 SHA 自動加上 hash suffix。</div></div>
<div id="sourceQueue" class="queue"></div>
</div>
</section>

<section id="page-basic" class="page"><h2>Basic Info <span class="en">security master + company profile</span></h2><div class="panel basicPanel"><div class="viewerTop"><div><span class="pill" style="background:var(--blue)">BASIC INFO</span><div id="basicPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('basic')">RELOAD</button><button onclick="openView('basic')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="basicEmpty" class="empty"><b>Basic Info HTML 尚未找到</b>執行 VDF 後會重新搜尋最新 Basic Info 頁面。</div><iframe id="basicFrame" style="display:none"></iframe></div></div></section>

<section id="page-financial" class="page"><h2>Financial Data <span class="en">statements + ratios + estimates</span></h2><div class="panel financialPanel"><div class="viewerTop"><div><span class="pill prov">FINANCIAL DATA</span><div id="financialPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('financial')">RELOAD</button><button onclick="openView('financial')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="financialEmpty" class="empty"><b>Financial Data HTML 尚未找到</b>執行 VDF 後會重新搜尋最新財務資料頁面。</div><iframe id="financialFrame" style="display:none"></iframe></div></div></section>

<section id="page-market" class="page"><h2>Market Data <span class="en">prices + volume + flows + indices</span></h2><div class="panel marketPanel"><div class="viewerTop"><div><span class="pill" style="background:var(--teal)">MARKET DATA</span><div id="marketPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('market')">RELOAD</button><button onclick="openView('market')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="marketEmpty" class="empty"><b>Market Data HTML 尚未找到</b>執行 VDF 後會重新搜尋價格、成交量與市場資料頁。</div><iframe id="marketFrame" style="display:none"></iframe></div></div></section>

<section id="page-quality" class="page"><h2>Data Quality <span class="en">validation + freshness + evidence</span></h2><div class="panel qualityPanel"><div class="viewerTop"><div><span class="pill ok">DATA QUALITY</span><div id="qualityPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('quality')">RELOAD</button><button onclick="openView('quality')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="qualityEmpty" class="empty"><b>Data Quality HTML 尚未找到</b>執行 VDF 後會搜尋 validation、audit 或 dashboard HTML。</div><iframe id="qualityFrame" style="display:none"></iframe></div></div></section>

<section id="page-registry" class="page">
<h2>Output Registry <span class="en">runtime + libraries + generated files</span></h2>
<div class="panel registryPanel">
<div class="registryGrid">
<div class="registryCard"><div class="l">CODE FILES REGISTERED</div><div id="registryFiles" class="v">—</div></div>
<div class="registryCard"><div class="l">POWERSHELL IMPORTS</div><div id="psImports" class="v">—</div></div>
<div class="registryCard"><div class="l">POWERSHELL INVENTORY</div><div id="psInventory" class="v">—</div></div>
<div class="registryCard"><div class="l">PYTHON PACKAGES</div><div id="pythonPackages" class="v">—</div></div>
<div class="registryCard"><div class="l">REQUIRED PYTHON IMPORTS</div><div id="pythonRequired" class="v">—</div></div>
<div class="registryCard"><div class="l">SNAPSHOT SHA256</div><div id="registrySnapshot" class="v">—</div></div>
<div class="registryCard"><div class="l">REGISTRY LEDGER</div><div id="registryLedger" class="v">—</div></div>
<div class="registryCard"><div class="l">CSV FILES</div><div id="csvCount" class="v">—</div></div>
<div class="registryCard"><div class="l">HTML FILES</div><div id="htmlCount" class="v">—</div></div>
</div>
<h2>Latest Output Files <span class="en">newest 30</span></h2>
<table><thead><tr><th>Ext</th><th>Bytes</th><th>Last Write</th><th>Path</th></tr></thead><tbody id="outputBody"></tbody></table>
</div>
</section>

<section id="page-logs" class="page"><h2>Execution Logs <span class="en">worker + invocation evidence</span></h2><div class="panel logPanel"><div class="actions"><button onclick="byId('log').innerText='VIA VDF Sidebar Workbench ready.'">CLEAR DISPLAY</button></div><div id="log" class="log">VIA VDF Sidebar Workbench ready.</div></div></section>

<div class="footer">VIA VDF Visual Lock · fixed left navigation · Base-relative discovery · no network install · no wrapper canonical mutation · 理</div>
</div></div>
</body>
</html>
'@

    $rendered = $html.Replace(
        "__DEFAULTS__",
        $defaultsJson
    ).Replace(
        "__CONFIG__",
        $configJson
    ).Replace(
        "__STATUS__",
        $statusJson
    ).Replace(
        "__DIALOG__",
        $dialogJson
    ).Replace(
        "__MAIN__",
        $mainJson
    ).Replace(
        "__PWSH__",
        $pwshJson
    )

    return $rendered
}

function Start-HtmlWorkbench {
    param([AllowEmptyString()][string]$RequestedBase)

    $baseRoot = Resolve-BaseRoot -Requested $RequestedBase
    $defaults = Get-SevenDefaults -BaseRoot $baseRoot

    $sessionId = "VDFUI_{0}_{1}" -f
        (Get-Date -Format "yyyyMMdd_HHmmss"),
        ([guid]::NewGuid().ToString("N").Substring(0, 8))

    $sessionRoot = Join-Path `
        -Path $env:TEMP `
        -ChildPath "VIA_VDF_HTML_UI\$sessionId"

    Ensure-Directory -Path $sessionRoot

    $configPath = Join-Path `
        -Path $sessionRoot `
        -ChildPath "worker_config.json"

    $statusPath = Join-Path `
        -Path $sessionRoot `
        -ChildPath "worker_status.json"

    $dialogHelperPath = Join-Path `
        -Path $sessionRoot `
        -ChildPath "VIA_VDF_WindowsDialog.ps1"

    $htaPath = Join-Path `
        -Path $sessionRoot `
        -ChildPath "VIA_VDF_Sidebar_Workbench_v0160C.html"

    Write-DialogHelper -Path $dialogHelperPath

    $pwshPath = (Get-Process -Id $PID).Path

    $html = Get-HtaHtml `
        -Defaults $defaults `
        -ConfigPath $configPath `
        -StatusPath $statusPath `
        -DialogHelperPath $dialogHelperPath `
        -MainScriptPath $PSCommandPath `
        -PowerShellPath $pwshPath

    Write-Utf8NoBomAtomic -Path $htaPath -Text $html

    $listener = $null
    $prefix = ""
    foreach ($port in @(8766, 8768, 8776, 0)) {
        if ($port -eq 0) { throw "No free localhost port among 8766/8768/8776 for the VDF UI bridge." }
        try {
            $candidate = "http://127.0.0.1:$port/"
            $listener = [System.Net.HttpListener]::new()
            $listener.Prefixes.Add($candidate)
            $listener.Start()
            $prefix = $candidate
            break
        }
        catch {
            if ($listener) { $listener.Close(); $listener = $null }
        }
    }

    Write-Host ""
    Write-Host ("=" * 118) -ForegroundColor DarkCyan
    Write-Host "def VIA · VDF ONE-CLICK SIDEBAR WORKBENCH · v0160C
(version-forward of v0160B: same Veritas design-lock UI served as a plain browser HTML page over a
localhost HTTP bridge — mshta/ActiveX removed, every workbench action mapped to /api endpoints)" -ForegroundColor Cyan
    Write-Host ("def Base       : {0}" -f $baseRoot) -ForegroundColor White
    Write-Host ("def VDF Root   : {0}" -f $defaults.vdfRoot) -ForegroundColor White
    Write-Host ("def UI         : {0}  (一般瀏覽器 HTML U/I)" -f $prefix) -ForegroundColor Cyan
    Write-Host ("def Page File  : {0}" -f $htaPath) -ForegroundColor White
    Write-Host "def Parameters : 7" -ForegroundColor Green
    Write-Host "def Windows I/O: enabled via localhost HTTP bridge (/api/run /api/dialog /api/open /api/status /view)" -ForegroundColor Green
    Write-Host "def 結束       : Ctrl+C 停止本機伺服器" -ForegroundColor Yellow
    Write-Host ("=" * 118) -ForegroundColor DarkCyan

    Start-Process $prefix | Out-Null

    $utf8 = [System.Text.UTF8Encoding]::new($false)
    try {
        while ($listener.IsListening) {
            $ctx = $listener.GetContext()
            $req = $ctx.Request
            $res = $ctx.Response
            $out = ""
            $code = 200
            $ctype = "application/json; charset=utf-8"
            try {
                $route = $req.Url.AbsolutePath
                if ($route -eq "/") {
                    $out = $html
                    $ctype = "text/html; charset=utf-8"
                }
                elseif ($route -eq "/api/status") {
                    if (Test-Path -LiteralPath $statusPath) {
                        $out = [System.IO.File]::ReadAllText($statusPath, $utf8)
                    }
                    else { $out = "{}" }
                }
                elseif ($route -eq "/api/run" -and $req.HttpMethod -eq "POST") {
                    $reader = [System.IO.StreamReader]::new($req.InputStream, $utf8)
                    $body = $reader.ReadToEnd()
                    $reader.Dispose()
                    [System.IO.File]::WriteAllText($configPath, $body, $utf8)
                    if (Test-Path -LiteralPath $statusPath) { Remove-Item -LiteralPath $statusPath -Force }
                    Start-Process `
                        -FilePath $pwshPath `
                        -WindowStyle Hidden `
                        -ArgumentList @(
                            "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", ('"{0}"' -f $PSCommandPath),
                            "-Worker", "-WorkerConfig", ('"{0}"' -f $configPath)
                        ) | Out-Null
                    $out = '{"ok":true}'
                }
                elseif ($route -eq "/api/dialog") {
                    $mode = [string]$req.QueryString["mode"]
                    $current = [string]$req.QueryString["current"]
                    if ($mode -notin @("Files", "Folder")) { throw "Unsupported dialog mode." }
                    $resultPath = "{0}.{1}.dialog.json" -f $configPath, $mode
                    if (Test-Path -LiteralPath $resultPath) { Remove-Item -LiteralPath $resultPath -Force }
                    Start-Process `
                        -FilePath $pwshPath `
                        -Wait `
                        -WindowStyle Hidden `
                        -ArgumentList @(
                            "-NoLogo", "-NoProfile", "-Sta", "-ExecutionPolicy", "Bypass",
                            "-File", ('"{0}"' -f $dialogHelperPath),
                            "-Mode", $mode,
                            "-Output", ('"{0}"' -f $resultPath),
                            "-Current", ('"{0}"' -f $current)
                        )
                    if (Test-Path -LiteralPath $resultPath) {
                        $out = [System.IO.File]::ReadAllText($resultPath, $utf8)
                    }
                    else { $out = "[]" }
                }
                elseif ($route -eq "/api/exists") {
                    $probe = [string]$req.QueryString["path"]
                    $out = (@{ exists = [bool]($probe -and (Test-Path -LiteralPath $probe)) } | ConvertTo-Json -Compress)
                }
                elseif ($route -eq "/api/open" -and $req.HttpMethod -eq "POST") {
                    $reader = [System.IO.StreamReader]::new($req.InputStream, $utf8)
                    $payload = $reader.ReadToEnd() | ConvertFrom-Json
                    $reader.Dispose()
                    $target = [string]$payload.path
                    if ($target -and (Test-Path -LiteralPath $target)) {
                        Start-Process -FilePath $target | Out-Null
                        $out = '{"ok":true}'
                    }
                    else {
                        $parentDir = if ($target) { Split-Path -Path $target -Parent } else { "" }
                        if ($parentDir -and (Test-Path -LiteralPath $parentDir)) {
                            Start-Process -FilePath $parentDir | Out-Null
                            $out = '{"ok":true,"opened":"parent"}'
                        }
                        else { $out = '{"ok":false}' }
                    }
                }
                elseif ($route -eq "/view") {
                    $doc = [string]$req.QueryString["path"]
                    if ($doc -and (Test-Path -LiteralPath $doc -PathType Leaf)) {
                        $out = [System.IO.File]::ReadAllText($doc, $utf8)
                        $ctype = "text/html; charset=utf-8"
                    }
                    else {
                        $code = 404
                        $out = "not found"
                        $ctype = "text/plain; charset=utf-8"
                    }
                }
                else {
                    $code = 404
                    $out = '{"error":"not found"}'
                }
            }
            catch {
                $code = 500
                $out = (@{ error = $_.Exception.Message } | ConvertTo-Json -Compress)
            }
            $bytes = $utf8.GetBytes([string]$out)
            $res.StatusCode = $code
            $res.ContentType = $ctype
            $res.ContentLength64 = $bytes.Length
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
            $res.OutputStream.Close()
        }
    }
    finally {
        if ($listener) { $listener.Stop(); $listener.Close() }
    }
}

if ($Worker) {
    if ([string]::IsNullOrWhiteSpace($WorkerConfig)) {
        throw "-WorkerConfig is required in Worker mode."
    }

    Invoke-WorkerMode -ConfigPath $WorkerConfig
    exit $LASTEXITCODE
}

try {
    Start-HtmlWorkbench -RequestedBase $Base
}
catch {
    Write-Host ""
    Write-Host "def VIA · VDF ONE-CLICK SAFE CATCH" -ForegroundColor Red
    Write-Host (
        "def ErrorType    : {0}" -f
        $_.Exception.GetType().FullName
    ) -ForegroundColor Red
    Write-Host (
        "def ErrorMessage : {0}" -f
        $_.Exception.Message
    ) -ForegroundColor Red
    Write-Host (
        "def StackTrace   : {0}" -f
        $_.ScriptStackTrace
    ) -ForegroundColor DarkRed
}
finally {
    Write-Host ""
    Write-Host "def Parent PowerShell remains open." -ForegroundColor Cyan
}
