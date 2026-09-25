#requires -Version 7.0
<#
====================================================================================================
def VIA · VRN VISUAL-LOCK WORKBENCH · v0159
====================================================================================================
One-file Windows launcher for the active-generation VRN v0156 workflow.

Seven HTML parameters
---------------------
1. Base
2. Input
3. Manifest
4. Python
5. Timeout
6. Recursive
7. Open HTML

All other authority, schema, adapter, ledger, engine and template paths are derived
from Base and verified before use.

Governance
----------
- Windows HTA HTML UI; no external web server and no network installation.
- Windows file/folder dialogs plus drag/drop report queue.
- Exact v0156 runtime assets copied/registered under the mother system.
- Approved PowerShell modules are imported and registered.
- Required Python modules are imported; installed packages are inventoried.
- Supportive code/config files are SHA-registered, never blindly dot-sourced.
- Added reports are staged collision-safely and registered as enabled=false drafts.
- v0156 performs run-local preflight only; no canonical/pointer/promotion mutation.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$Base = "",
    [switch]$Worker,
    [string]$WorkerConfig = ""
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Script:Version = "v0159"
$Script:ExpectedV0156LauncherSha = "298e557bb8f507f210c5a2dc2af0fd2e08c32ef81a4a10852bd311b805fa66a7"
$Script:ExpectedV0156EngineSha = "5aa2440f2ff3e777524a660cb72006e95594f894521ff16d16ce95f1faaa6079"
$Script:ExpectedV0156TemplateSha = "2a73de943fd45e5e1d12a811fe353c22cfa4d0acff03baed637f124f37b22a71"
$Script:ExpectedV0156Approval = "I_APPROVE_VIA_v0156_ACTIVE_GENERATION_INCREMENTAL_INTAKE_PREFLIGHT"

$Script:AllowedReportExtensions = @(
    ".pdf", ".docx", ".doc", ".txt", ".md", ".html", ".htm",
    ".json", ".csv", ".xlsx", ".xls", ".pptx", ".ppt", ".rtf"
)

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
    "argparse", "csv", "datetime", "hashlib", "html", "json", "os",
    "pathlib", "subprocess", "sys", "tempfile", "time", "traceback",
    "concurrent.futures"
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
        "$env:USERPROFILE\OneDrive\文件\VeritasIntelligenceAnalytics"
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

                $vrn = (Join-Path -Path $current -ChildPath "functional modules\VRN")
                $supportive = (Join-Path -Path $current -ChildPath "supportive modules")

                if (
                    (Test-Path -LiteralPath $vrn -PathType Container) -and
                    (Test-Path -LiteralPath $supportive -PathType Container)
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

function Resolve-PythonRuntime {
    param(
        [AllowEmptyString()][string]$Requested,
        [AllowEmptyString()][string]$BaseRoot
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
        (Join-Path $BaseRoot ".venv\Scripts\python.exe")
    )) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $candidates.Add($candidate)
        }
    }

    $command = (Get-Command python -ErrorAction SilentlyContinue)

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

function Find-LatestVrnViewPage {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)]
        [ValidateSet("BasicInfo", "FinancialData")]
        [string]$View
    )

    $roots = @(
        (Join-Path -Path $BaseRoot -ChildPath "functional modules\VRN"),
        (Join-Path -Path $BaseRoot -ChildPath "outputs"),
        (Join-Path -Path $BaseRoot -ChildPath "output"),
        (Join-Path -Path $BaseRoot -ChildPath "_via_vrn_active_generation_incremental_intake_runs"),
        (Join-Path -Path $BaseRoot -ChildPath "_via_vrn_html_ui_runs")
    )

    $pattern = if ($View -eq "BasicInfo") {
        "(?i)(basic[\s_\-]*info|basicinfo)"
    }
    else {
        "(?i)(financial[\s_\-]*data|financialdata)"
    }

    $candidates = @()

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) {
            continue
        }

        $found = @(
            Get-ChildItem `
                -LiteralPath $root `
                -Recurse `
                -File `
                -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Extension.ToLowerInvariant() -in @(".html", ".htm") -and
                $_.Name -match $pattern -and
                $_.Name -notmatch "(?i)(visual[\s_\-]*lock|one[\s_\-]*click|workbench)"
            } |
            Sort-Object LastWriteTime -Descending
        )

        $candidates += $found
    }

    $selected = @(
        $candidates |
        Sort-Object -Property LastWriteTime, FullName -Descending -Unique |
        Select-Object -First 1
    )

    if ($selected.Count -eq 0) {
        return ""
    }

    return [string]$selected[0].FullName
}

function Get-SevenDefaults {
    param([Parameter(Mandatory)][string]$BaseRoot)

    $intakeRoot = (
        Join-Path `
            -Path $BaseRoot `
            -ChildPath "_vrn_research_report_incremental_intake_v0156"
    )

    return [ordered]@{
        base = $BaseRoot
        input = (
            Join-Path `
                -Path $intakeRoot `
                -ChildPath "incoming"
        )
        manifest = (
            Join-Path `
                -Path $intakeRoot `
                -ChildPath "VRN_ResearchReport_Incremental_Manifest.v0156.jsonl"
        )
        python = (
            Resolve-PythonRuntime `
                -Requested "" `
                -BaseRoot $BaseRoot
        )
        timeout = 2400
        recursive = $true
        openHtml = $true
        basicInfoPage = (
            Find-LatestVrnViewPage `
                -BaseRoot $BaseRoot `
                -View "BasicInfo"
        )
        financialDataPage = (
            Find-LatestVrnViewPage `
                -BaseRoot $BaseRoot `
                -View "FinancialData"
        )
    }
}

function Get-RuntimeSourceCandidate {
    param(
        [Parameter(Mandatory)][string]$FileName,
        [Parameter(Mandatory)][string]$ExpectedSha,
        [Parameter(Mandatory)][string]$BaseRoot
    )

    $canonicalBin = (Join-Path -Path $BaseRoot -ChildPath "supportive modules\VIA_Governance_Runtime\v0156\bin")

    $candidates = @(
        (Join-Path $canonicalBin $FileName),
        (Join-Path $PSScriptRoot $FileName),
        (Join-Path "$env:USERPROFILE\Downloads" $FileName)
    )

    foreach ($candidate in $candidates) {
        if (
            (Test-Path -LiteralPath $candidate -PathType Leaf) -and
            (Get-Sha256 -Path $candidate) -eq $ExpectedSha
        ) {
            return $candidate
        }
    }

    throw (
        "Required exact runtime artifact not found: $FileName; " +
        "expected SHA256=$ExpectedSha"
    )
}

function Install-ExactRuntimeAsset {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$ExpectedSha
    )

    if ((Get-Sha256 -Path $Source) -ne $ExpectedSha) {
        throw "Runtime source SHA mismatch: $Source"
    }

    Ensure-Directory -Path (Split-Path -Parent $Destination)

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        if ((Get-Sha256 -Path $Destination) -eq $ExpectedSha) {
            return "EXACT_EXISTS_SKIP"
        }

        throw (
            "Runtime destination exists with an unexpected SHA: " +
            $Destination
        )
    }

    Copy-Item `
        -LiteralPath $Source `
        -Destination $Destination `
        -Force

    if ((Get-Sha256 -Path $Destination) -ne $ExpectedSha) {
        throw "Runtime asset post-copy SHA mismatch: $Destination"
    }

    return "COPIED_EXACT"
}

function Register-V0156Runtime {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$RunDir
    )

    $bin = (Join-Path -Path $BaseRoot -ChildPath "supportive modules\VIA_Governance_Runtime\v0156\bin")

    Ensure-Directory -Path $bin

    $specs = @(
        [ordered]@{
            name = "Invoke-VIA-VRN-ActiveGenerationIncrementalIntake-8Track-v0156.ps1"
            sha = $Script:ExpectedV0156LauncherSha
        },
        [ordered]@{
            name = "via_vrn_active_generation_incremental_intake_8track_v0156.py"
            sha = $Script:ExpectedV0156EngineSha
        },
        [ordered]@{
            name = "VRN_ResearchReport_Incremental_Manifest.template.v0156.jsonl"
            sha = $Script:ExpectedV0156TemplateSha
        }
    )

    $rows = @()

    foreach ($spec in $specs) {
        $source = Get-RuntimeSourceCandidate `
            -FileName $spec.name `
            -ExpectedSha $spec.sha `
            -BaseRoot $BaseRoot

        $destination = (Join-Path -Path $bin -ChildPath $spec.name)

        $state = Install-ExactRuntimeAsset `
            -Source $source `
            -Destination $destination `
            -ExpectedSha $spec.sha

        $rows += [ordered]@{
            component = $spec.name
            expected_sha256 = $spec.sha
            source = $source
            destination = $destination
            state = $state
            registered = $true
        }
    }

    $registryPath = (Join-Path -Path $RunDir -ChildPath "registry\v0156_runtime_assets.json")

    Write-JsonAtomic `
        -Path $registryPath `
        -Value $rows

    return [ordered]@{
        launcher = (Join-Path -Path $bin -ChildPath $specs[0].name)
        engine = (Join-Path -Path $bin -ChildPath $specs[1].name)
        template = (Join-Path -Path $bin -ChildPath $specs[2].name)
        rows = $rows
        registry = $registryPath
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
                error = "MODULE_NOT_INSTALLED"
            }

            continue
        }

        $selected = $available[0]

        try {
            Import-Module `
                -Name $selected.Path `
                -Force `
                -ErrorAction Stop

            $imported = (
                Get-Module -Name $name -ErrorAction SilentlyContinue |
                Sort-Object Version -Descending |
                Select-Object -First 1
            )

            $rows += [ordered]@{
                module = $name
                available = $true
                imported = ($null -ne $imported)
                version = [string]$selected.Version
                path = [string]$selected.Path
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

    $registryDir = (Join-Path -Path $RunDir -ChildPath "registry")
    Ensure-Directory -Path $registryDir

    Write-JsonAtomic `
        -Path (Join-Path -Path $registryDir -ChildPath "powershell_approved_imports.json") `
        -Value $rows

    Write-JsonAtomic `
        -Path (Join-Path -Path $registryDir -ChildPath "powershell_module_inventory.json") `
        -Value $inventory

    $failed = @(
        $rows |
        Where-Object {
            $_.available -and
            -not $_.imported
        }
    )

    if ($failed.Count -gt 0) {
        throw (
            "Approved PowerShell module import failure: " +
            (
                $failed |
                ConvertTo-Json -Depth 20 -Compress
            )
        )
    }

    return $rows
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

rows = []
for name in sys.argv[1:]:
    try:
        module = importlib.import_module(name)
        rows.append({
            "module": name,
            "imported": True,
            "file": str(getattr(module, "__file__", "")),
        })
    except Exception as exc:
        rows.append({
            "module": name,
            "imported": False,
            "error": f"{type(exc).__name__}: {exc}",
        })

print(json.dumps({
    "python_executable": sys.executable,
    "python_version": platform.python_version(),
    "implementation": platform.python_implementation(),
    "modules": rows,
    "all_imported": all(row["imported"] for row in rows),
}, ensure_ascii=False))
'@

    $pythonImportArguments = @("-c", $testCode) + @($Script:RequiredPythonModules)
    $testOutput = @(
        & $PythonPath @pythonImportArguments 2>&1
    )

    if ($LASTEXITCODE -ne 0) {
        throw (
            "Python runtime import test failed: " +
            ($testOutput | Out-String)
        )
    }

    $runtime = (
        ($testOutput | Out-String).Trim() |
        ConvertFrom-Json
    )

    if (-not $runtime.all_imported) {
        throw (
            "Required Python module import failure: " +
            (
                $runtime.modules |
                Where-Object { -not $_.imported } |
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

    $registryDir = (Join-Path -Path $RunDir -ChildPath "registry")
    Ensure-Directory -Path $registryDir

    Write-JsonAtomic `
        -Path (Join-Path -Path $registryDir -ChildPath "python_runtime_imports.json") `
        -Value $runtime

    Write-JsonAtomic `
        -Path (Join-Path -Path $registryDir -ChildPath "python_package_inventory.json") `
        -Value ([ordered]@{
            packages = $pipPackages
            pip_error = $pipError
        })

    return [ordered]@{
        runtime = $runtime
        pip_package_count = @($pipPackages).Count
        pip_error = $pipError
    }
}

function Register-SupportiveToolsAndLibraries {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$RunDir
    )

    $supportiveRoot = (Join-Path -Path $BaseRoot -ChildPath "supportive modules")

    if (
        -not (
            Test-Path `
                -LiteralPath $supportiveRoot `
                -PathType Container
        )
    ) {
        throw "Supportive modules root missing: $supportiveRoot"
    }

    $extensions = @(
        ".ps1", ".psm1", ".psd1", ".py", ".pyi",
        ".json", ".jsonl", ".sql", ".md", ".html",
        ".htm", ".css", ".js", ".jsx", ".ts", ".tsx",
        ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv"
    )

    $files = @(
        Get-ChildItem `
            -LiteralPath $supportiveRoot `
            -Recurse `
            -File `
            -ErrorAction Stop |
        Where-Object {
            $extension = $_.Extension.ToLowerInvariant()

            if ($extensions -notcontains $extension) {
                return $false
            }

            $full = $_.FullName.ToLowerInvariant()

            foreach ($part in @(
                "\__pycache__\",
                "\.git\",
                "\node_modules\",
                "\cache\",
                "\caches\",
                "\_runs\",
                "\registry\",
                "\ledger\",
                "\snapshots\"
            )) {
                if ($full.Contains($part)) {
                    return $false
                }
            }

            return $true
        } |
        Sort-Object FullName
    )

    $inventory = @()
    $sequence = 0

    foreach ($file in $files) {
        $sequence++

        $inventory += [ordered]@{
            sequence = $sequence
            relative_path = [System.IO.Path]::GetRelativePath($BaseRoot, $file.FullName)
            extension = $file.Extension.ToLowerInvariant()
            bytes = $file.Length
            last_write_utc = $file.LastWriteTimeUtc.ToString("o")
            sha256 = (Get-Sha256 -Path $file.FullName)
            registration_state = "REGISTERED_HASH_ONLY_NOT_EXECUTED"
        }
    }

    $snapshotText = (
        $inventory |
        ForEach-Object {
            "{0}|{1}|{2}" -f
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
                (
                    [System.IO.Path]::GetFileNameWithoutExtension(
                        $_.relative_path
                    )
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

    $registryDir = (Join-Path -Path $BaseRoot -ChildPath "supportive modules\VIA_Governance_Runtime\v0159\registry")

    $snapshotDir = (Join-Path -Path $registryDir -ChildPath "snapshots")

    Ensure-Directory -Path $snapshotDir

    $snapshotName = ("VRN_Supportive_Runtime_Snapshot.{0}.json" -f $snapshotHash)
    $snapshotPath = (Join-Path -Path $snapshotDir -ChildPath $snapshotName)

    if (
        -not (
            Test-Path `
                -LiteralPath $snapshotPath `
                -PathType Leaf
        )
    ) {
        Write-JsonAtomic `
            -Path $snapshotPath `
            -Value ([ordered]@{
                version = $Script:Version
                generated_at = (Get-NowIso)
                base = $BaseRoot
                snapshot_sha256 = $snapshotHash
                file_count = $inventory.Count
                inventory = $inventory
                core_supportive_tools = $coreRows
            })
    }

    $ledgerPath = (Join-Path -Path $registryDir -ChildPath "VRN_Supportive_Runtime_Registry.v0159.jsonl")

    $alreadyRecorded = $false

    if (Test-Path -LiteralPath $ledgerPath -PathType Leaf) {
        foreach (
            $line in
                Get-Content `
                    -LiteralPath $ledgerPath `
                    -Encoding UTF8
        ) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            try {
                $entry = $line | ConvertFrom-Json

                if (
                    [string]$entry.snapshot_sha256 -eq
                    $snapshotHash
                ) {
                    $alreadyRecorded = $true
                    break
                }
            }
            catch {
                throw (
                    "Supportive runtime registry contains " +
                    "malformed JSONL."
                )
            }
        }
    }

    if (-not $alreadyRecorded) {
        Append-Utf8NoBomLine `
            -Path $ledgerPath `
            -Line (
                ConvertTo-CanonicalJson ([ordered]@{
                    event = "SUPPORTIVE_RUNTIME_REGISTERED"
                    version = $Script:Version
                    recorded_at = (Get-NowIso)
                    base = $BaseRoot
                    snapshot_sha256 = $snapshotHash
                    file_count = $inventory.Count
                    snapshot_path = $snapshotPath
                    automatic_code_execution = $false
                })
            )
    }

    $runRegistry = (Join-Path -Path $RunDir -ChildPath "registry")
    $ledgerState = "LEDGER_EVENT_APPENDED"
    if ($alreadyRecorded) {
        $ledgerState = "EXACT_SNAPSHOT_ALREADY_REGISTERED"
    }

    Write-JsonAtomic `
        -Path (Join-Path -Path $runRegistry -ChildPath "supportive_runtime_registry.json") `
        -Value ([ordered]@{
            snapshot_sha256 = $snapshotHash
            file_count = $inventory.Count
            registry_ledger = $ledgerPath
            snapshot = $snapshotPath
            ledger_state = $ledgerState
            core_supportive_tools = $coreRows
        })

    return [ordered]@{
        snapshot_sha256 = $snapshotHash
        file_count = $inventory.Count
        registry_ledger = $ledgerPath
        snapshot = $snapshotPath
        ledger_state = $ledgerState
        core_supportive_tools = $coreRows
    }
}

function Get-SafeFileName {
    param([Parameter(Mandatory)][string]$Name)

    $safe = [System.IO.Path]::GetFileName($Name)

    foreach (
        $character in
            [System.IO.Path]::GetInvalidFileNameChars()
    ) {
        $safe = $safe.Replace(
            [string]$character,
            "_"
        )
    }

    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "Report filename is empty after sanitization."
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

    $destination = (Join-Path -Path $DestinationFolder -ChildPath $name)
    $sourceSha = Get-Sha256 -Path $Source

    if (
        -not (
            Test-Path `
                -LiteralPath $destination `
                -PathType Leaf
        )
    ) {
        return [ordered]@{
            path = $destination
            state = "NEW_DESTINATION"
            sha256 = $sourceSha
        }
    }

    $destinationSha = Get-Sha256 -Path $destination

    if ($destinationSha -eq $sourceSha) {
        return [ordered]@{
            path = $destination
            state = "EXACT_EXISTS_SKIP"
            sha256 = $sourceSha
        }
    }

    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($name)
    $extension = [System.IO.Path]::GetExtension($name)

    $renamed = "{0}.{1}{2}" -f
        $baseName,
        $sourceSha.Substring(0, 12),
        $extension

    return [ordered]@{
        path = (Join-Path -Path $DestinationFolder -ChildPath $renamed)
        state = "HASH_SUFFIX_RENAME"
        sha256 = $sourceSha
    }
}

function Get-ReportSourceFiles {
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
            $extension = [System.IO.Path]::GetExtension($path).ToLowerInvariant()

            if (
                $Script:AllowedReportExtensions -contains
                $extension
            ) {
                $full = [System.IO.Path]::GetFullPath($path)

                $key = $full.ToLowerInvariant()

                if (-not $seen.ContainsKey($key)) {
                    $seen[$key] = $true
                    $files.Add($full)
                }
            }

            continue
        }

        if (
            Test-Path `
                -LiteralPath $path `
                -PathType Container
        ) {
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

                if (
                    $Script:AllowedReportExtensions -notcontains
                    $extension
                ) {
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

function Stage-AdditionalReports {
    param(
        [Parameter(Mandatory)]$Sources,
        [Parameter(Mandatory)][string]$InputFolder,
        [Parameter(Mandatory)][bool]$Recursive,
        [Parameter(Mandatory)][string]$RunDir
    )

    Ensure-Directory -Path $InputFolder

    $sourceFiles = Get-ReportSourceFiles `
        -Sources $Sources `
        -Recursive $Recursive

    $rows = @()

    foreach ($source in $sourceFiles) {
        $destinationInfo = (Resolve-CollisionSafeDestination -Source $source -DestinationFolder $InputFolder)

        if (
            $destinationInfo.state -ne
            "EXACT_EXISTS_SKIP"
        ) {
            if (
                Test-Path `
                    -LiteralPath $destinationInfo.path `
                    -PathType Leaf
            ) {
                if (
                    (Get-Sha256 -Path $destinationInfo.path) -ne
                    $destinationInfo.sha256
                ) {
                    throw (
                        "Collision-safe destination differs: " +
                        $destinationInfo.path
                    )
                }
            }
            else {
                Copy-Item `
                    -LiteralPath $source `
                    -Destination $destinationInfo.path `
                    -Force
            }
        }

        $postSha = (Get-Sha256 -Path $destinationInfo.path)

        if ($postSha -ne $destinationInfo.sha256) {
            throw (
                "Staged report SHA verification failed: " +
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
        -Path (Join-Path -Path $RunDir -ChildPath "evidence\staged_reports.json") `
        -Value $rows

    return $rows
}

function Get-DateCandidateFromFilename {
    param([Parameter(Mandatory)][string]$FileName)

    $match = [regex]::Match(
        $FileName,
        "(?<!\d)(20\d{2})(0[1-9]|1[0-2])([0-2]\d|3[01])(?!\d)"
    )

    if (-not $match.Success) {
        return $null
    }

    $candidate = "{0}-{1}-{2}" -f
        $match.Groups[1].Value,
        $match.Groups[2].Value,
        $match.Groups[3].Value

    try {
        [void][datetime]::ParseExact(
            $candidate,
            "yyyy-MM-dd",
            [System.Globalization.CultureInfo]::InvariantCulture
        )

        return $candidate
    }
    catch {
        return $null
    }
}

function Ensure-ManifestAndAppendDisabledDrafts {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$TemplatePath,
        [Parameter(Mandatory)][string]$InputFolder,
        [Parameter(Mandatory)]$StagedRows,
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][string]$RunDir
    )

    Ensure-Directory -Path (
        Split-Path -Parent $ManifestPath
    )

    if (
        -not (
            Test-Path `
                -LiteralPath $ManifestPath `
                -PathType Leaf
        )
    ) {
        Copy-Item `
            -LiteralPath $TemplatePath `
            -Destination $ManifestPath `
            -Force
    }

    if (@($StagedRows).Count -eq 0) {
        return [ordered]@{
            manifest_path = $ManifestPath
            manifest_before_sha256 = (Get-Sha256 -Path $ManifestPath)
            manifest_after_sha256 = (Get-Sha256 -Path $ManifestPath)
            backup_path = ""
            ledger_path = ""
            transaction_id = ""
            results = @()
        }
    }

    $beforeBytes = [System.IO.File]::ReadAllBytes($ManifestPath)
    $beforeSha = (Get-Sha256 -Path $ManifestPath)

    $backupPath = (Join-Path -Path $RunDir -ChildPath "backup\VRN_ResearchReport_Incremental_Manifest.before_v0159.bytes")

    Ensure-Directory -Path (
        Split-Path -Parent $backupPath
    )

    [System.IO.File]::WriteAllBytes(
        $backupPath,
        $beforeBytes
    )

    $existingShas = @{}
    $lineNumber = 0

    foreach (
        $line in
            Get-Content `
                -LiteralPath $ManifestPath `
                -Encoding UTF8
    ) {
        $lineNumber++

        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $row = $line | ConvertFrom-Json
        }
        catch {
            throw (
                "Manifest JSONL is malformed at line " +
                $lineNumber
            )
        }

        foreach ($sha in @(
            [string]$row.source_sha256,
            [string]$row.record.source_sha256
        )) {
            if ($sha -match "^[0-9a-fA-F]{64}$") {
                $existingShas[
                    $sha.ToLowerInvariant()
                ] = $true
            }
        }
    }

    $draftRows = @()

    foreach ($staged in @($StagedRows)) {
        $sha = (
            [string]$staged.destination_sha256
        ).ToLowerInvariant()

        $fileName = [System.IO.Path]::GetFileName([string]$staged.destination)

        if ($existingShas.ContainsKey($sha)) {
            $draftRows += [ordered]@{
                source_sha256 = $sha
                source_document = $fileName
                state = "SHA_ALREADY_PRESENT_SKIP"
                manifest_mutation = $false
            }

            continue
        }

        $dateCandidate = (Get-DateCandidateFromFilename -FileName $fileName)

        $candidates = if ($null -eq $dateCandidate) {
            @()
        }
        else {
            @($dateCandidate)
        }

        $relative = [System.IO.Path]::GetRelativePath($InputFolder, [string]$staged.destination)

        $recordId = ("VRN-{0}" -f $sha.Substring(0, 12).ToUpperInvariant())
        $dateEvidenceReference = ""
        $dateEvidenceType = "ABSENT"
        $dateEvidenceState = "ABSENT"
        if ($null -ne $dateCandidate) {
            $dateEvidenceReference = "FILENAME_CANDIDATE:$dateCandidate"
            $dateEvidenceType = "DIRECT_FILENAME_DATE_CANDIDATE_UNAPPROVED"
            $dateEvidenceState = "FILENAME_CANDIDATE_UNAPPROVED"
        }

        $row = [ordered]@{
            action = "APPEND_RECORD"
            enabled = $false
            evidence = [ordered]@{
                date_evidence_reference = $dateEvidenceReference
                date_evidence_type = $dateEvidenceType
                notes = (
                    "Created by v0159 HTML Workbench as a " +
                    "disabled operational-manifest draft. " +
                    "Review all fields and set enabled=true " +
                    "only after operator approval."
                )
                operator_approved = $false
                operator_approved_record_id = $false
            }
            record = [ordered]@{
                record_id = $recordId
                report_date_candidates = $candidates
                report_date_evidence_state = $dateEvidenceState
                report_date_guess = $null
                report_date_resolution_provenance = [ordered]@{
                    source = "v0159_HTML_WORKBENCH"
                    automatic_approval = $false
                    filename_candidate = $dateCandidate
                }
                report_date_resolution_state = "UNRESOLVED_EVIDENCE_INSUFFICIENT"
                schema_version = "2.0"
                source_document = $fileName
                source_sha256 = $sha
            }
            source_relative_path = $relative
            source_sha256 = $sha
        }

        Append-Utf8NoBomLine `
            -Path $ManifestPath `
            -Line (
                ConvertTo-CanonicalJson $row
            )

        $existingShas[$sha] = $true

        $draftRows += [ordered]@{
            source_sha256 = $sha
            source_document = $fileName
            record_id = $recordId
            date_candidate = $dateCandidate
            state = "DISABLED_DRAFT_APPENDED"
            manifest_mutation = $true
        }
    }

    $afterSha = (Get-Sha256 -Path $ManifestPath)

    $ledgerDir = (Join-Path -Path $BaseRoot -ChildPath "supportive modules\VIA_Governance_Runtime\v0159\ledger")

    Ensure-Directory -Path $ledgerDir

    $ledgerPath = (Join-Path -Path $ledgerDir -ChildPath "VRN_HTMLUI_Manifest_Draft_Ledger.v0159.jsonl")

    $transactionMaterial = "$beforeSha|$afterSha|$($draftRows.Count)"
    $shaObject = [Security.Cryptography.SHA256]::Create()

    try {
        $transactionHash = ([BitConverter]::ToString($shaObject.ComputeHash([Text.Encoding]::UTF8.GetBytes($transactionMaterial)))).Replace("-", "").Substring(0, 20)
        $transactionId = "VRN-UI-DRAFT-$transactionHash"
    }
    finally {
        $shaObject.Dispose()
    }

    $eventExists = $false

    if (Test-Path -LiteralPath $ledgerPath -PathType Leaf) {
        foreach (
            $line in
                Get-Content `
                    -LiteralPath $ledgerPath `
                    -Encoding UTF8
        ) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            try {
                $event = $line | ConvertFrom-Json

                if (
                    [string]$event.transaction_id -eq
                    $transactionId
                ) {
                    $eventExists = $true
                    break
                }
            }
            catch {
                throw (
                    "v0159 manifest draft ledger contains " +
                    "malformed JSONL."
                )
            }
        }
    }

    if (-not $eventExists) {
        Append-Utf8NoBomLine `
            -Path $ledgerPath `
            -Line (
                ConvertTo-CanonicalJson ([ordered]@{
                    event = "DISABLED_MANIFEST_DRAFTS_REGISTERED"
                    version = $Script:Version
                    transaction_id = $transactionId
                    recorded_at = (Get-NowIso)
                    manifest_path = $ManifestPath
                    manifest_before_sha256 = $beforeSha
                    manifest_after_sha256 = $afterSha
                    backup_path = $backupPath
                    staged_report_count = @($StagedRows).Count
                    draft_result_count = $draftRows.Count
                    enabled_record_count_created = 0
                    authority_mutation_executed = $false
                })
            )
    }

    $result = [ordered]@{
        manifest_path = $ManifestPath
        manifest_before_sha256 = $beforeSha
        manifest_after_sha256 = $afterSha
        backup_path = $backupPath
        ledger_path = $ledgerPath
        transaction_id = $transactionId
        results = $draftRows
    }

    Write-JsonAtomic `
        -Path (Join-Path -Path $RunDir -ChildPath "evidence\manifest_draft_results.json") `
        -Value $result

    return $result
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
        updated_at = (Get-NowIso)
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
        foreach (
            $property in
                $Extra.PSObject.Properties
        ) {
            $payload[$property.Name] = $property.Value
        }
    }

    Write-JsonAtomic `
        -Path $StatusPath `
        -Value $payload
}

function Find-LatestV0156Summary {
    param(
        [Parameter(Mandatory)][string]$BaseRoot,
        [Parameter(Mandatory)][datetime]$NotBefore
    )

    $root = (Join-Path -Path $BaseRoot -ChildPath "_via_vrn_active_generation_incremental_intake_runs")

    if (
        -not (
            Test-Path `
                -LiteralPath $root `
                -PathType Container
        )
    ) {
        return $null
    }

    foreach ($file in @(
        Get-ChildItem `
            -LiteralPath $root `
            -Filter "summary.v0156.json" `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $_.LastWriteTime -ge
                $NotBefore.AddSeconds(-3)
        } |
        Sort-Object LastWriteTime -Descending
    )) {
        try {
            $summary = (Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json)

            return [pscustomobject]@{
                path = $file.FullName
                summary = $summary
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Invoke-WorkerMode {
    param(
        [Parameter(Mandatory)][string]$ConfigPath
    )

    $config = (Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json)

    $statusPath = [string]$config.statusPath
    $runDir = [string]$config.runDir

    try {
        foreach ($folder in @(
            $runDir,
            (Join-Path -Path $runDir -ChildPath "registry"),
            (Join-Path -Path $runDir -ChildPath "evidence"),
            (Join-Path -Path $runDir -ChildPath "backup"),
            (Join-Path -Path $runDir -ChildPath "logs")
        )) {
            Ensure-Directory -Path $folder
        }

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 3 `
            -Message (
                "Resolving Base and the seven UI parameters."
            )

        $baseRoot = Resolve-BaseRoot `
            -Requested (
                [string]$config.parameters.base
            )

        $inputFolder = [System.IO.Path]::GetFullPath([string]$config.parameters.input)
        $manifestPath = [System.IO.Path]::GetFullPath([string]$config.parameters.manifest)

        $pythonPath = (Resolve-PythonRuntime -Requested ([string]$config.parameters.python) -BaseRoot $baseRoot)

        $timeout = [int]$config.parameters.timeout
        $recursive = [bool]$config.parameters.recursive
        $openHtml = [bool]$config.parameters.openHtml

        if ([string]::IsNullOrWhiteSpace($pythonPath)) {
            throw "No usable Python runtime was resolved."
        }

        if ($timeout -lt 60 -or $timeout -gt 86400) {
            throw (
                "Timeout must be between 60 and " +
                "86400 seconds."
            )
        }

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 10 `
            -Message (
                "Registering exact v0156 runtime assets."
            )

        $runtime = (Register-V0156Runtime -BaseRoot $baseRoot -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 20 `
            -Message (
                "Importing available approved modules; missing modules are optional warnings."
            )

        $psModules = (Import-AndRegisterPowerShellModules -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 30 `
            -Message (
                "Verifying Python imports and packages."
            )

        $pythonRegistry = (Test-AndRegisterPythonRuntime -PythonPath $pythonPath -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 42 `
            -Message (
                "Hashing and registering supportive tools."
            )

        $supportRegistry = (Register-SupportiveToolsAndLibraries -BaseRoot $baseRoot -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 55 `
            -Message (
                "Staging additional reports."
            )

        $staged = (Stage-AdditionalReports -Sources $config.sources -InputFolder $inputFolder -Recursive $recursive -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 65 `
            -Message (
                "Appending disabled operational-manifest drafts."
            )

        $manifestDrafts = (Ensure-ManifestAndAppendDisabledDrafts -ManifestPath $manifestPath -TemplatePath $runtime.template -InputFolder $inputFolder -StagedRows $staged -BaseRoot $baseRoot -RunDir $runDir)

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 75 `
            -Message (
                "Launching the v0156 eight-track intake."
            )

        $started = Get-Date
        $intakeRoot = (Split-Path -Parent $manifestPath)

        $launcherOutputPath = (Join-Path -Path $runDir -ChildPath "logs\v0156_launcher.console.log")

        $launcherOutput = @(
            & $runtime.launcher `
                -BaseDir $baseRoot `
                -IntakeRoot $intakeRoot `
                -IntakeDir $inputFolder `
                -ManifestPath $manifestPath `
                -ManifestTemplatePath $runtime.template `
                -EnginePath $runtime.engine `
                -ExpectedEngineSha256 (
                    $Script:ExpectedV0156EngineSha
                ) `
                -ExpectedManifestTemplateSha256 (
                    $Script:ExpectedV0156TemplateSha
                ) `
                -PythonPath $pythonPath `
                -OverallTimeoutSeconds $timeout `
                -OpenHtmlReport $false `
                -KeepParentPowerShellOpen $false `
                -ApprovalPhrase (
                    $Script:ExpectedV0156Approval
                ) 2>&1
        )

        $launcherOutput |
            Set-Content `
                -LiteralPath $launcherOutputPath `
                -Encoding UTF8

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "RUNNING" `
            -Percent 92 `
            -Message (
                "Collecting the newest v0156 Gate."
            )

        $latest = (
            Find-LatestV0156Summary `
                -BaseRoot $baseRoot `
                -NotBefore $started
        )

        $successGates = @(
            "RESEARCH_REPORT_SSOT_V2_ACTIVE_GENERATION_INCREMENTAL_INTAKE_NO_ENABLED_RECORDS_TEMPLATE_READY_NO_MUTATION",
            "RESEARCH_REPORT_SSOT_V2_ACTIVE_GENERATION_INCREMENTAL_INTAKE_PACKAGE_READY_FOR_SEQUENTIAL_APPEND_NO_MUTATION"
        )

        $gate = ""
        $reportPath = ""
        $summaryPath = ""
        $v0156RunDir = ""
        $evidenceMode = "SUMMARY_JSON"
        $evidenceFiles = @()

        if ($null -ne $latest) {
            $gate = [string]$latest.summary.gate
            $reportPath = [string]$latest.summary.html
            $summaryPath = [string]$latest.path
            $v0156RunDir = [string]$latest.summary.run_dir

            if ($successGates -notcontains $gate) {
                throw (
                    "v0156 returned a non-green Gate: " +
                    $gate
                )
            }
        }
        else {
            $consoleText = (
                @($launcherOutput) |
                ForEach-Object { [string]$_ }
            ) -join [Environment]::NewLine

            foreach ($candidateGate in $successGates) {
                if ($consoleText.Contains($candidateGate)) {
                    $gate = $candidateGate
                    $evidenceMode = "EXACT_CONSOLE_GATE"
                    break
                }
            }

            $evidenceRoot = Join-Path `
                -Path $baseRoot `
                -ChildPath "_via_vrn_active_generation_incremental_intake_runs"

            if (
                Test-Path `
                    -LiteralPath $evidenceRoot `
                    -PathType Container
            ) {
                $evidenceFiles = @(
                    Get-ChildItem `
                        -LiteralPath $evidenceRoot `
                        -File `
                        -Recurse `
                        -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.LastWriteTime -ge
                            $started.AddSeconds(-3) -and
                        $_.Extension.ToLowerInvariant() -in @(
                            ".json",
                            ".jsonl",
                            ".html",
                            ".csv",
                            ".parquet"
                        )
                    } |
                    Sort-Object LastWriteTime -Descending |
                    Select-Object -First 30
                )
            }

            $fatalPatterns = @(
                "POWERSHELL AST : FAIL",
                "SAFE CATCH",
                "[FATAL]",
                "Traceback (most recent call last)",
                "Unhandled exception"
            )

            $fatalEvidence = @(
                $fatalPatterns |
                Where-Object {
                    $consoleText.IndexOf(
                        $_,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -ge 0
                }
            )

            if ([string]::IsNullOrWhiteSpace($gate)) {
                if (
                    @($evidenceFiles).Count -gt 0 -and
                    @($fatalEvidence).Count -eq 0
                ) {
                    $gate =
                        "VRN_V0156_DEGRADED_WITH_OUTPUT_EVIDENCE_SUMMARY_MISSING_REVIEW_REQUIRED"

                    $evidenceMode =
                        "OUTPUT_EVIDENCE_NO_SUMMARY"

                    $reportCandidate = @(
                        $evidenceFiles |
                        Where-Object {
                            $_.Extension -ieq ".html"
                        }
                    ) |
                    Select-Object -First 1

                    if ($null -ne $reportCandidate) {
                        $reportPath =
                            [string]$reportCandidate.FullName
                    }

                    $v0156RunDir =
                        [string]$evidenceFiles[0].DirectoryName
                }
                else {
                    throw (
                        "v0156 produced neither a readable summary, " +
                        "an exact green console Gate, nor safe output " +
                        "evidence. Inspect $launcherOutputPath"
                    )
                }
            }
            else {
                $reportCandidate = @(
                    $evidenceFiles |
                    Where-Object {
                        $_.Extension -ieq ".html"
                    }
                ) |
                Select-Object -First 1

                if ($null -ne $reportCandidate) {
                    $reportPath =
                        [string]$reportCandidate.FullName
                }

                if (@($evidenceFiles).Count -gt 0) {
                    $v0156RunDir =
                        [string]$evidenceFiles[0].DirectoryName
                }
            }
        }

        $basicInfoPage = (
            Find-LatestVrnViewPage `
                -BaseRoot $baseRoot `
                -View "BasicInfo"
        )

        $financialDataPage = (
            Find-LatestVrnViewPage `
                -BaseRoot $baseRoot `
                -View "FinancialData"
        )

        $final = [ordered]@{
            base = $baseRoot
            input = $inputFolder
            manifest = $manifestPath
            python = $pythonPath
            timeout = $timeout
            recursive = $recursive
            openHtml = $openHtml
            v0156_gate = $gate
            v0156_summary = $summaryPath
            v0156_report = $reportPath
            v0156_run_dir = $v0156RunDir
            v0156_evidence_mode = $evidenceMode
            v0156_evidence_files = @(
                $evidenceFiles |
                ForEach-Object {
                    [string]$_.FullName
                }
            )
            basic_info_page = $basicInfoPage
            financial_data_page = $financialDataPage
            staged_report_count = @($staged).Count
            manifest_draft_count = @($manifestDrafts.results | Where-Object { $_.state -eq "DISABLED_DRAFT_APPENDED" }).Count
            support_registry = $supportRegistry
            python_package_count = $pythonRegistry.pip_package_count
            powerShell_import_count = @(
                $psModules |
                Where-Object { $_.imported }
            ).Count
            powerShell_optional_missing_count = @(
                $psModules |
                Where-Object { -not $_.available }
            ).Count
            runtime_registry = $runtime.registry
            launcher_console = $launcherOutputPath
            workbench_run_dir = $runDir
        }

        Write-JsonAtomic `
            -Path (Join-Path -Path $runDir -ChildPath "final_summary.v0159.json") `
            -Value $final

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "COMPLETED" `
            -Percent 100 `
            -Message (
                (
                    if (
                        $gate -eq
                        "VRN_V0156_DEGRADED_WITH_OUTPUT_EVIDENCE_SUMMARY_MISSING_REVIEW_REQUIRED"
                    ) {
                        "VRN completed with output evidence; summary is missing and requires review."
                    }
                    else {
                        "VRN v0156 completed with an exact green Gate."
                    }
                )
            ) `
            -Extra ([pscustomobject]$final)
    }
    catch {
        $errorPayload = [ordered]@{
            error_type = $_.Exception.GetType().FullName
            error_message = $_.Exception.Message
            stack_trace = $_.ScriptStackTrace
            workbench_run_dir = $runDir
        }

        Write-JsonAtomic `
            -Path (Join-Path -Path $runDir -ChildPath "failure.v0159.json") `
            -Value $errorPayload

        Update-WorkerStatus `
            -StatusPath $statusPath `
            -State "FAILED" `
            -Percent 100 `
            -Message $_.Exception.Message `
            -Extra ([pscustomobject]$errorPayload)

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
        $dialog =
            [System.Windows.Forms.FolderBrowserDialog]::new()

        $dialog.Description = "VIA VRN — Select folder"
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
        $dialog =
            [System.Windows.Forms.OpenFileDialog]::new()

        $dialog.Multiselect = $true
        $dialog.Filter =
            "Research reports|*.pdf;*.docx;*.doc;*.txt;*.md;*.html;*.htm;*.json;*.csv;*.xlsx;*.xls;*.pptx;*.ppt;*.rtf|All files (*.*)|*.*"

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

    "Python" {
        $dialog =
            [System.Windows.Forms.OpenFileDialog]::new()

        $dialog.Multiselect = $false
        $dialog.Filter =
            "Python executable (python.exe)|python.exe|Executable files (*.exe)|*.exe|All files (*.*)|*.*"

        if (
            -not [string]::IsNullOrWhiteSpace($Current)
        ) {
            $parent =
                Split-Path -Parent $Current

            if (
                -not [string]::IsNullOrWhiteSpace($parent) -and
                (
                    Test-Path `
                        -LiteralPath $parent `
                        -PathType Container
                )
            ) {
                $dialog.InitialDirectory = $parent
            }
        }

        if (
            $dialog.ShowDialog() -eq
            [System.Windows.Forms.DialogResult]::OK
        ) {
            $result = @($dialog.FileName)
        }

        $dialog.Dispose()
    }

    "Manifest" {
        $dialog =
            [System.Windows.Forms.SaveFileDialog]::new()

        $dialog.Filter =
            "JSON Lines (*.jsonl)|*.jsonl|All files (*.*)|*.*"

        if (
            -not [string]::IsNullOrWhiteSpace($Current)
        ) {
            $dialog.FileName =
                Split-Path -Leaf $Current

            $parent =
                Split-Path -Parent $Current

            if (
                -not [string]::IsNullOrWhiteSpace($parent) -and
                (
                    Test-Path `
                        -LiteralPath $parent `
                        -PathType Container
                )
            ) {
                $dialog.InitialDirectory = $parent
            }
        }

        if (
            $dialog.ShowDialog() -eq
            [System.Windows.Forms.DialogResult]::OK
        ) {
            $result = @($dialog.FileName)
        }

        $dialog.Dispose()
    }

    default {
        throw "Unsupported dialog Mode: $Mode"
    }
}

$result |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -LiteralPath $Output `
        -Encoding Unicode
'@

    Write-Utf8NoBomAtomic `
        -Path $Path `
        -Text $helper
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

    $defaultsJson = ($Defaults | ConvertTo-Json -Depth 20 -Compress)
    $configJson = ($ConfigPath | ConvertTo-Json -Compress)
    $statusJson = ($StatusPath | ConvertTo-Json -Compress)
    $dialogJson = ($DialogHelperPath | ConvertTo-Json -Compress)
    $mainJson = ($MainScriptPath | ConvertTo-Json -Compress)
    $pwshJson = ($PowerShellPath | ConvertTo-Json -Compress)

    $html = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA · VRN Sidebar Workbench</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<HTA:APPLICATION
    ID="VIA_VRN"
    APPLICATIONNAME="VIA VRN Sidebar Workbench"
    BORDER="thin"
    CAPTION="yes"
    MAXIMIZEBUTTON="yes"
    MINIMIZEBUTTON="yes"
    SCROLL="yes"
    SINGLEINSTANCE="yes"
    SYSMENU="yes"
    WINDOWSTATE="normal"
/>
<style>
:root{
    --bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;
    --mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;
    --up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;
    --am:#c4943a;--vi:#7a6daa;
    --sidebar:#f8f7f3;
    --reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
    background:var(--bg);color:var(--ink2);
    font:11px/1.5 "DM Sans","Noto Sans TC","Microsoft JhengHei",sans-serif;
    -webkit-font-smoothing:antialiased
}
.bar{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:100}
.appShell{min-height:100vh}
.sidebar{
    position:fixed;top:4px;left:0;bottom:0;width:232px;
    background:var(--sidebar);border-right:1px solid var(--line);
    padding:18px 14px 16px;overflow:auto;z-index:60
}
.sideBrand{padding:2px 5px 15px;border-bottom:2px solid var(--ink)}
.sideKicker{
    font:700 8px "DM Mono",Consolas,monospace;
    letter-spacing:1.5px;color:var(--mut);text-transform:uppercase
}
.sideTitle{
    margin-top:7px;font:800 17px/1.2 "Syne","Microsoft JhengHei",sans-serif;
    color:var(--ink)
}
.sideTitle span{color:var(--up)}
.sideSub{margin-top:6px;color:var(--mut);font-size:9.5px}
.sideGroup{margin-top:18px}
.sideGroupTitle{
    margin:0 6px 6px;font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut2);letter-spacing:1.2px;text-transform:uppercase
}
.sideNav button{
    display:block;width:100%;text-align:left;margin-bottom:4px;
    border:1px solid transparent;border-radius:4px;background:transparent;
    color:var(--ink2);padding:8px 9px;
    font:700 8.5px "DM Mono",Consolas,monospace;cursor:pointer
}
.sideNav button:hover{background:var(--paper);border-color:var(--line)}
.sideNav button.active{
    background:var(--ink);color:#fff;border-color:var(--ink)
}
.sideNav button .n{
    display:inline-block;min-width:21px;color:var(--mut2)
}
.sideNav button.active .n{color:#fff}
.sideMetrics{
    margin-top:16px;border-top:1px solid var(--line);padding-top:12px
}
.sideMetric{
    display:flex;justify-content:space-between;gap:8px;
    padding:5px 3px;border-bottom:1px solid var(--soft)
}
.sideMetric .k{
    font:700 7.5px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.sideMetric .v{
    max-width:112px;text-align:right;overflow-wrap:anywhere;
    font:700 8px "DM Mono",Consolas,monospace;color:var(--ink)
}
.sideFooter{margin-top:14px}
.sideFooter button{width:100%}
.workspace{margin-left:232px;min-height:100vh}
.workspaceInner{max-width:1240px;margin:0 auto;padding:0 22px 54px}
header{padding:22px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink)}
.kicker{
    font:700 10px "DM Mono",Consolas,monospace;
    letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px
}
h1{
    font:800 20px/1.2 "Syne","Microsoft JhengHei",sans-serif;color:var(--ink)
}
h1 span{color:var(--up)}
.sub{margin-top:6px;font-size:10.5px;color:var(--mut);max-width:1030px}
.sub b{color:var(--ink2)}
.page{display:none}.page.active{display:block}
.hero{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px}
.hc{
    background:var(--paper);border:1px solid var(--line);
    border-radius:5px;padding:10px 16px;min-width:130px
}
.hc .v{
    font:800 18px "Syne","Microsoft JhengHei",sans-serif;
    line-height:1;overflow-wrap:anywhere
}
.hc .l{
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
.panel.input{border-left:3px solid var(--up)}
.panel.summary{border-left:3px solid var(--teal)}
.panel.basic{border-left:3px solid var(--blue)}
.panel.financial{border-left:3px solid var(--vi)}
.panel.queuePanel{border-left:3px solid var(--am)}
.panel.registryPanel{border-left:3px solid var(--down)}
.panel.logPanel{border-left:3px solid var(--ink)}
.homeColumns{display:flex;gap:12px;align-items:flex-start}
.homeMain{flex:1;min-width:0}
.homeAside{width:355px;min-width:320px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.full{grid-column:1/3}
.field{border-bottom:1px solid var(--soft);padding:8px 0}
.field:last-child{border-bottom:none}
label{
    display:block;font:700 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase;margin-bottom:5px
}
.row{display:flex;align-items:center;gap:6px}
input[type=text],input[type=number]{
    width:100%;border:1px solid var(--line);border-radius:4px;padding:7px 9px;
    background:#fafaf8;color:var(--ink2);
    font:500 10px "DM Mono",Consolas,monospace
}
input:focus{outline:1px solid var(--teal);border-color:var(--teal)}
.check{display:flex;align-items:center;gap:7px;min-height:30px}
button{
    border:1px solid var(--line);border-radius:4px;padding:7px 10px;
    background:var(--paper);color:var(--ink2);
    font:700 8px "DM Mono",Consolas,monospace;cursor:pointer
}
button:hover{background:#fafaf8}
button.primary{color:#fff;background:var(--teal);border-color:var(--teal)}
button.danger{color:#fff;background:var(--up);border-color:var(--up)}
button:disabled{opacity:.45;cursor:default}
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
.queue{
    margin-top:10px;border:1px solid var(--line);border-radius:4px;
    max-height:430px;overflow:auto
}
.queueItem{
    display:flex;justify-content:space-between;gap:10px;
    padding:7px 9px;border-bottom:1px solid var(--soft);
    font:500 9px "DM Mono",Consolas,monospace
}
.queueItem:last-child{border-bottom:none}
.progressOuter{
    height:9px;background:var(--soft);border-radius:3px;
    overflow:hidden;margin-top:12px
}
.progressInner{height:100%;width:0%;background:var(--reson)}
.status{
    display:grid;grid-template-columns:118px 1fr;
    gap:5px 10px;margin-top:11px
}
.k{
    font:700 8px "DM Mono",Consolas,monospace;
    color:var(--mut);text-transform:uppercase
}
.code{
    font-family:"DM Mono",Consolas,monospace;
    overflow-wrap:anywhere
}
.log{
    background:#f8f8f5;color:var(--ink2);
    border:1px solid var(--line);border-radius:4px;padding:10px;
    min-height:470px;max-height:650px;overflow:auto;white-space:pre-wrap;
    font:500 9px/1.55 "DM Mono",Consolas,monospace
}
.pill{
    display:inline-block;font:700 7.5px "DM Mono",Consolas,monospace;
    color:#fff;border-radius:3px;padding:2px 7px;letter-spacing:.3px
}
.ok{background:var(--down)}.warn{background:var(--am)}
.blind{background:var(--mut2)}.prov{background:var(--vi)}
.viewerTop{
    display:flex;align-items:center;justify-content:space-between;
    gap:10px;flex-wrap:wrap
}
.viewerPath{
    color:var(--mut);font:500 9px "DM Mono",Consolas,monospace;
    overflow-wrap:anywhere;margin-top:6px
}
.frameWrap{
    margin-top:10px;border:1px solid var(--line);
    background:#fafaf8;min-height:620px
}
iframe{
    display:block;width:100%;height:620px;border:0;background:#fff
}
.emptyView{padding:80px 20px;text-align:center;color:var(--mut)}
.emptyView b{
    display:block;color:var(--ink);
    font:800 14px "Syne","Microsoft JhengHei",sans-serif;margin-bottom:6px
}
.registryGrid{
    display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:10px
}
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
.quickLinks{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}
.quickLink{
    border:1px solid var(--line);border-radius:5px;padding:10px;
    cursor:pointer;background:#fafaf8
}
.quickLink:hover{background:var(--paper)}
.quickLink b{
    display:block;color:var(--ink);
    font:800 11px "Syne","Microsoft JhengHei",sans-serif
}
.quickLink span{display:block;color:var(--mut);font-size:9px;margin-top:4px}
.footer{
    margin-top:14px;color:var(--mut2);
    font:500 8px "DM Mono",Consolas,monospace
}
@media(max-width:980px){
    .sidebar{width:194px}
    .workspace{margin-left:194px}
    .homeColumns{display:block}
    .homeAside{width:auto;min-width:0}
    .grid{grid-template-columns:1fr}
    .full{grid-column:auto}
    .registryGrid{grid-template-columns:1fr}
}
</style>
<script language="javascript">
var defaults=__DEFAULTS__;
var configPath=__CONFIG__;
var statusPath=__STATUS__;
var dialogHelper=__DIALOG__;
var mainScript=__MAIN__;
var pwshPath=__PWSH__;
var shell=new ActiveXObject("WScript.Shell");
var fso=new ActiveXObject("Scripting.FileSystemObject");
var sources=[];
var workerStarted=false;
var timerId=0;
var basicInfoPath=defaults.basicInfoPage||"";
var financialDataPath=defaults.financialDataPage||"";

function byId(id){return document.getElementById(id);}
function quote(value){return '"' + String(value).replace(/"/g,'""') + '"';}
function setText(id,value){var node=byId(id);if(node){node.innerText=value;}}
function setHtml(id,value){var node=byId(id);if(node){node.innerHTML=value;}}
function log(text){
    var box=byId("log");
    if(!box){return;}
    box.innerText += "\r\n" + new Date().toLocaleTimeString() + "  " + text;
    box.scrollTop=box.scrollHeight;
}
function jsonRead(path){
    if(!fso.FileExists(path)){return null;}
    var stream=new ActiveXObject("ADODB.Stream");
    stream.Type=2;stream.Charset="utf-8";stream.Open();stream.LoadFromFile(path);
    var text=stream.ReadText();stream.Close();
    text=String(text).replace(/^\uFEFF/,"");
    return JSON.parse(text);
}
function jsonWrite(path,obj){
    var stream=new ActiveXObject("ADODB.Stream");
    stream.Type=2;stream.Charset="utf-8";stream.Open();stream.WriteText(JSON.stringify(obj));
    stream.Position=0;stream.Type=1;
    if(stream.Size>=3){
        var prefix=new VBArray(stream.Read(3)).toArray();
        if(prefix[0]===239&&prefix[1]===187&&prefix[2]===191){
            var body=stream.Read();stream.Position=0;stream.SetEOS();stream.Write(body);
        }
    }
    stream.SaveToFile(path,2);stream.Close();
}
function setDefaults(d){
    byId("base").value=d.base||"";
    byId("input").value=d.input||"";
    byId("manifest").value=d.manifest||"";
    byId("python").value=d.python||"";
    byId("timeout").value=d.timeout||2400;
    byId("recursive").checked=!!d.recursive;
    byId("openHtml").checked=!!d.openHtml;
}
function switchPage(name){
    var pages=["home","basic","financial","queue","registry","logs"];
    var labels={
        home:["首頁 · 輸入與摘要","Home · Input + Summary"],
        basic:["Basic Info","Independent primary page"],
        financial:["Financial Data","Independent primary page"],
        queue:["報告佇列","Investment report intake queue"],
        registry:["Runtime Registry","Tools, modules and library registration"],
        logs:["Execution Logs","Worker events and Gate evidence"]
    };
    for(var i=0;i<pages.length;i++){
        var page=pages[i];
        byId("page-"+page).className="page"+(page===name?" active":"");
        byId("nav-"+page).className=page===name?"active":"";
    }
    setText("pageTitle",labels[name][0]);
    setText("pageSubtitle",labels[name][1]);
    if(name==="basic"){loadView("basic");}
    if(name==="financial"){loadView("financial");}
}
function toFileUrl(path){
    if(!path){return "";}
    return "file:///"+encodeURI(String(path).replace(/\\/g,"/").replace(/^\/+/,""));
}
function setViewPath(view,path){
    if(view==="basic"){
        basicInfoPath=path||"";
        setText("basicPath",basicInfoPath||"尚未找到 Basic Info HTML");
    }else{
        financialDataPath=path||"";
        setText("financialPath",financialDataPath||"尚未找到 Financial Data HTML");
    }
}
function loadView(view){
    var path=view==="basic"?basicInfoPath:financialDataPath;
    var frame=byId(view+"Frame");
    var empty=byId(view+"Empty");
    if(path&&fso.FileExists(path)){
        frame.style.display="block";empty.style.display="none";frame.src=toFileUrl(path);
    }else{
        frame.style.display="none";frame.src="about:blank";empty.style.display="block";
    }
}
function openView(view){
    var path=view==="basic"?basicInfoPath:financialDataPath;
    if(path&&fso.FileExists(path)){shell.Run(quote(path),1,false);}
    else{log(view==="basic"?"尚未找到 Basic Info HTML。":"尚未找到 Financial Data HTML。");}
}
function runDialog(mode,current){
    var resultPath=configPath+"."+mode+".dialog.json";
    if(fso.FileExists(resultPath)){try{fso.DeleteFile(resultPath,true);}catch(e){}}
    var command=quote(pwshPath)+" -NoLogo -NoProfile -Sta -ExecutionPolicy Bypass -File "+
        quote(dialogHelper)+" -Mode "+quote(mode)+" -Output "+quote(resultPath)+" -Current "+quote(current||"");
    shell.Run(command,0,true);
    var result=jsonRead(resultPath);
    if(!result){return [];}
    if(result instanceof Array){return result;}
    return [result];
}
function browseField(mode,id){
    var values=runDialog(mode,byId(id).value);
    if(values.length>0){byId(id).value=values[0];}
}
function addFiles(){
    var values=runDialog("Files",byId("input").value);
    for(var i=0;i<values.length;i++){sources.push({kind:"path",path:values[i]});}
    renderQueue();
}
function addFolder(){
    var values=runDialog("Folder",byId("input").value);
    if(values.length>0){sources.push({kind:"folder",path:values[0]});renderQueue();}
}
function renderQueue(){
    var box=byId("queue");
    if(box){box.innerHTML="";}
    setText("queueCount",sources.length);
    setText("sideQueue",sources.length);
    setText("homeQueue",sources.length);
    if(sources.length===0){
        if(box){box.innerHTML='<div class="queueItem">尚未增加額外投資報告。</div>';}
        return;
    }
    for(var i=0;i<sources.length;i++){
        var row=document.createElement("div");row.className="queueItem";
        var text=document.createElement("span");text.innerText=sources[i].path;
        var remove=document.createElement("button");remove.innerText="移除";remove.setAttribute("data-index",i);
        remove.onclick=function(){var index=parseInt(this.getAttribute("data-index"),10);sources.splice(index,1);renderQueue();};
        row.appendChild(text);row.appendChild(remove);box.appendChild(row);
    }
}
function onDrop(event){
    event.returnValue=false;
    try{
        var files=event.dataTransfer.files;
        for(var i=0;i<files.length;i++){
            var path=files[i].path||files[i].value||files[i].name;
            if(path&&fso.FileExists(path)){sources.push({kind:"drag",path:path});}
            else{log("拖曳項目未提供 Windows 完整路徑；請改用 Windows 選檔。");}
        }
        renderQueue();
    }catch(e){log("Drag/drop: "+e.message);}
    var drops=[byId("dropHome"),byId("dropQueue")];
    for(var d=0;d<drops.length;d++){if(drops[d]){drops[d].className="drop";}}
}
function bindDrop(id){
    var node=byId(id);
    if(!node){return;}
    node.ondragenter=function(){this.className="drop active";return false;};
    node.ondragover=function(){return false;};
    node.ondragleave=function(){this.className="drop";return false;};
    node.ondrop=onDrop;
}
function submitRun(){
    if(workerStarted){return;}
    var parameters={
        base:byId("base").value,input:byId("input").value,manifest:byId("manifest").value,
        python:byId("python").value,timeout:parseInt(byId("timeout").value,10),
        recursive:byId("recursive").checked,openHtml:byId("openHtml").checked
    };
    var runDir=parameters.base+"\\_via_vrn_html_ui_runs\\RUN_"+new Date().getTime()+"_VRN_SIDEBAR_v0159";
    var config={version:"v0159",statusPath:statusPath,runDir:runDir,parameters:parameters,sources:sources};
    jsonWrite(configPath,config);
    if(fso.FileExists(statusPath)){try{fso.DeleteFile(statusPath,true);}catch(e){}}
    var command=quote(pwshPath)+" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "+
        quote(mainScript)+" -Worker -WorkerConfig "+quote(configPath);
    workerStarted=true;byId("run").disabled=true;
    setHtml("state",'<span class="pill warn">STARTING</span>');
    setText("sideState","STARTING");
    shell.Run(command,0,false);log("Worker started.");timerId=window.setInterval(pollStatus,650);
}
function pollStatus(){
    var status=null;try{status=jsonRead(statusPath);}catch(e){return;}if(!status){return;}
    var percent=parseInt(status.percent||0,10);byId("bar").style.width=percent+"%";
    var cls="pill blind";if(status.state==="COMPLETED"){cls="pill ok";}else if(status.state==="FAILED"){cls="pill warn";}
    setHtml("state",'<span class="'+cls+'">'+status.state+'</span>');
    setText("message",status.message||"");
    setText("summaryState",status.state||"RUNNING");
    setText("summaryProgress",percent+"%");
    setText("sideState",status.state||"RUNNING");
    setText("sideProgress",percent+"%");
    if(status.v0156_gate){
        setText("gate",status.v0156_gate);
        setText("summaryGate",status.v0156_gate);
        setText("sideGate",status.v0156_gate);
    }
    if(status.staged_report_count!==undefined){setText("summaryReports",status.staged_report_count);}
    if(status.manifest_draft_count!==undefined){setText("summaryDrafts",status.manifest_draft_count);}
    if(status.support_registry){
        setText("registry",status.support_registry.file_count+" files · "+status.support_registry.snapshot_sha256);
        setText("summaryRegistry",status.support_registry.file_count);
        setText("registryFiles",status.support_registry.file_count);
        setText("registrySnapshot",status.support_registry.snapshot_sha256);
        setText("registryLedger",status.support_registry.registry_ledger||"");
    }
    if(status.powerShell_import_count!==undefined){setText("psModuleCount",status.powerShell_import_count);}
    if(status.python_package_count!==undefined){setText("pythonPackageCount",status.python_package_count);}
    if(status.runtime_registry){setText("runtimeRegistryPath",status.runtime_registry);}
    if(status.basic_info_page){setViewPath("basic",status.basic_info_page);}
    if(status.financial_data_page){setViewPath("financial",status.financial_data_page);}
    if(status.terminal){
        window.clearInterval(timerId);workerStarted=false;byId("run").disabled=false;
        if(status.v0156_report){byId("result").disabled=false;byId("result").setAttribute("data-path",status.v0156_report);}
        if(status.workbench_run_dir){byId("runDir").disabled=false;byId("runDir").setAttribute("data-path",status.workbench_run_dir);}
        log(status.state+": "+status.message);
        if(status.v0156_gate){log("Gate: "+status.v0156_gate);}
        if(status.error_message){log("Error: "+status.error_message);}
        if(status.state==="COMPLETED"&&byId("openHtml").checked&&status.v0156_report){
            shell.Run(quote(status.v0156_report),1,false);
        }
    }
}
function openDataPath(button){var path=button.getAttribute("data-path");if(path){shell.Run(quote(path),1,false);}}
function openManual(path){
    if(!path){return;}
    if(fso.FileExists(path)||fso.FolderExists(path)){shell.Run(quote(path),1,false);return;}
    try{var parent=fso.GetParentFolderName(path);if(fso.FolderExists(parent)){shell.Run(quote(parent),1,false);}}
    catch(e){log("Open path: "+e.message);}
}
window.onload=function(){
    window.resizeTo(1420,940);setDefaults(defaults);
    setViewPath("basic",defaults.basicInfoPage||"");
    setViewPath("financial",defaults.financialDataPage||"");
    renderQueue();switchPage("home");bindDrop("dropHome");bindDrop("dropQueue");
};
</script>
</head>
<body>
<div class="bar"></div>
<div class="appShell">
<aside class="sidebar">
<div class="sideBrand">
<div class="sideKicker">VERITAS INTELLIGENCE ANALYTICS</div>
<div class="sideTitle">VRN <span>Workbench</span></div>
<div class="sideSub">Visual Lock · Sidebar Edition · v0159</div>
</div>

<div class="sideGroup">
<div class="sideGroupTitle">Workspace</div>
<div class="sideNav">
<button id="nav-home" onclick="switchPage('home')"><span class="n">01</span>HOME · INPUT + SUMMARY</button>
<button id="nav-basic" onclick="switchPage('basic')"><span class="n">02</span>BASIC INFO</button>
<button id="nav-financial" onclick="switchPage('financial')"><span class="n">03</span>FINANCIAL DATA</button>
</div>
</div>

<div class="sideGroup">
<div class="sideGroupTitle">Operations</div>
<div class="sideNav">
<button id="nav-queue" onclick="switchPage('queue')"><span class="n">04</span>REPORT QUEUE</button>
<button id="nav-registry" onclick="switchPage('registry')"><span class="n">05</span>RUNTIME REGISTRY</button>
<button id="nav-logs" onclick="switchPage('logs')"><span class="n">06</span>EXECUTION LOGS</button>
</div>
</div>

<div class="sideMetrics">
<div class="sideMetric"><div class="k">STATE</div><div id="sideState" class="v">READY</div></div>
<div class="sideMetric"><div class="k">PROGRESS</div><div id="sideProgress" class="v">0%</div></div>
<div class="sideMetric"><div class="k">QUEUE</div><div id="sideQueue" class="v">0</div></div>
<div class="sideMetric"><div class="k">GATE</div><div id="sideGate" class="v">—</div></div>
</div>

<div class="sideFooter">
<button class="danger" onclick="window.close()">CLOSE WORKBENCH</button>
</div>
</aside>

<div class="workspace">
<div class="workspaceInner">
<header>
<div class="kicker">VRN RESEARCH REPORT SSOT · ACTIVE GENERATION · VISUAL LOCK</div>
<h1 id="pageTitle">首頁 · 輸入與摘要</h1>
<p id="pageSubtitle" class="sub">Home · Input + Summary</p>
</header>

<section id="page-home" class="page active">
<div class="hero">
<div class="hc"><div id="summaryState" class="v" style="color:var(--teal)">READY</div><div class="l">WORKBENCH STATE</div></div>
<div class="hc"><div id="summaryProgress" class="v">0%</div><div class="l">PROGRESS</div></div>
<div class="hc"><div id="homeQueue" class="v">0</div><div class="l">INPUT QUEUE</div></div>
<div class="hc"><div id="summaryReports" class="v">0</div><div class="l">STAGED REPORTS</div></div>
<div class="hc"><div id="summaryDrafts" class="v">0</div><div class="l">DISABLED DRAFTS</div></div>
<div class="hc"><div id="summaryRegistry" class="v">—</div><div class="l">REGISTERED FILES</div></div>
<div class="hc" style="min-width:270px"><div id="summaryGate" class="v" style="font:700 9px/1.35 &quot;DM Mono&quot;,Consolas,monospace">—</div><div class="l">LATEST GATE</div></div>
</div>

<div class="homeColumns">
<div class="homeMain">
<h2>① 輸入參數 <span class="en">seven runtime parameters</span></h2>
<div class="panel input">
<div class="grid">
<div class="field full">
<label>1. Base · 母系統根目錄</label>
<div class="row"><input id="base" type="text"><button onclick="browseField('Folder','base')">WINDOWS SEARCH</button></div>
<div class="hint">其餘 authority、schema、adapter、ledger 與 runtime 路徑全部由 Base 相對推導。</div>
</div>
<div class="field full">
<label>2. Input · 投資報告輸入目錄</label>
<div class="row"><input id="input" type="text"><button onclick="browseField('Folder','input')">WINDOWS SEARCH</button><button onclick="openManual(byId('input').value)">OPEN</button></div>
</div>
<div class="field full">
<label>3. Manifest · Operational JSONL</label>
<div class="row"><input id="manifest" type="text"><button onclick="browseField('Manifest','manifest')">WINDOWS SEARCH</button><button onclick="openManual(byId('manifest').value)">OPEN</button></div>
</div>
<div class="field"><label>4. Python Runtime</label><div class="row"><input id="python" type="text"><button onclick="browseField('Python','python')">SEARCH</button></div></div>
<div class="field"><label>5. Timeout Seconds</label><input id="timeout" type="number" min="60" max="86400" step="60"></div>
<div class="field"><label>6. Recursive Scan</label><div class="check"><input id="recursive" type="checkbox"><span>資料夾輸入採遞迴搜尋</span></div></div>
<div class="field"><label>7. Open Result HTML</label><div class="check"><input id="openHtml" type="checkbox"><span>成功後自動開啟 v0156 結果</span></div></div>
</div>
</div>
</div>

<div class="homeAside">
<h2>② 啟動與摘要 <span class="en">one-click execution</span></h2>
<div class="panel summary">
<div class="actions">
<button id="run" class="primary" onclick="submitRun()">ONE-CLICK START VRN</button>
<button id="result" disabled onclick="openDataPath(this)">RESULT</button>
<button id="runDir" disabled onclick="openDataPath(this)">RUNDIR</button>
</div>
<div class="progressOuter"><div id="bar" class="progressInner"></div></div>
<div class="status">
<div class="k">STATE</div><div id="state"><span class="pill blind">READY</span></div>
<div class="k">MESSAGE</div><div id="message">等待執行。</div>
<div class="k">GATE</div><div id="gate" class="code">—</div>
<div class="k">REGISTRY</div><div id="registry" class="code">執行時驗證、匯入與註冊。</div>
</div>
</div>

<h2>③ 快速拖曳 <span class="en">external report intake</span></h2>
<div id="dropHome" class="drop">
<b>從 Windows 檔案總管拖曳投資報告</b>
<span>詳細佇列請使用左側 REPORT QUEUE</span>
</div>
<div class="actions">
<button onclick="addFiles()">SELECT FILES</button>
<button onclick="addFolder()">SELECT FOLDER</button>
<button onclick="switchPage('queue')">OPEN QUEUE</button>
</div>

<div class="quickLinks">
<div class="quickLink" onclick="switchPage('basic')"><b>Basic Info</b><span>查看最新基本資料頁</span></div>
<div class="quickLink" onclick="switchPage('financial')"><b>Financial Data</b><span>查看最新財務資料頁</span></div>
</div>
</div>
</div>
</section>

<section id="page-basic" class="page">
<h2>Basic Info <span class="en">independent primary page</span></h2>
<div class="panel basic">
<div class="viewerTop">
<div><span class="pill" style="background:var(--blue)">BASIC INFO</span><div id="basicPath" class="viewerPath"></div></div>
<div class="actions"><button onclick="loadView('basic')">RELOAD</button><button onclick="openView('basic')">OPEN EXTERNAL</button></div>
</div>
<div class="frameWrap">
<div id="basicEmpty" class="emptyView"><b>Basic Info HTML 尚未找到</b>Workbench 會從 Base 的 VRN functional modules、output 與最新 run folders 自動尋找。</div>
<iframe id="basicFrame" style="display:none"></iframe>
</div>
</div>
</section>

<section id="page-financial" class="page">
<h2>Financial Data <span class="en">independent primary page</span></h2>
<div class="panel financial">
<div class="viewerTop">
<div><span class="pill prov">FINANCIAL DATA</span><div id="financialPath" class="viewerPath"></div></div>
<div class="actions"><button onclick="loadView('financial')">RELOAD</button><button onclick="openView('financial')">OPEN EXTERNAL</button></div>
</div>
<div class="frameWrap">
<div id="financialEmpty" class="emptyView"><b>Financial Data HTML 尚未找到</b>Workbench 會從 Base 的 VRN functional modules、output 與最新 run folders 自動尋找。</div>
<iframe id="financialFrame" style="display:none"></iframe>
</div>
</div>
</section>

<section id="page-queue" class="page">
<h2>報告佇列 <span class="en">windows I/O + drag and drop</span></h2>
<div class="panel queuePanel">
<div id="dropQueue" class="drop">
<b>拖曳投資報告至佇列</b>
<span>PDF、DOCX、TXT、HTML、JSON、CSV、Excel、PowerPoint</span>
</div>
<div class="actions">
<button onclick="addFiles()">WINDOWS SELECT FILES</button>
<button onclick="addFolder()">WINDOWS SELECT FOLDER</button>
<button onclick="sources=[];renderQueue()">CLEAR QUEUE</button>
<button onclick="switchPage('home')">BACK TO HOME</button>
</div>
<div class="status">
<div class="k">QUEUE COUNT</div><div id="queueCount">0</div>
<div class="k">INPUT TARGET</div><div class="code">使用首頁 Input 參數指定的位置</div>
<div class="k">MANIFEST MODE</div><div>只建立 enabled=false 草稿，不自動核准日期。</div>
</div>
<div id="queue" class="queue"></div>
</div>
</section>

<section id="page-registry" class="page">
<h2>Runtime Registry <span class="en">support tools + modules + libraries</span></h2>
<div class="panel registryPanel">
<div class="registryGrid">
<div class="registryCard"><div class="l">SUPPORT FILES</div><div id="registryFiles" class="v">—</div></div>
<div class="registryCard"><div class="l">POWERSHELL IMPORTS</div><div id="psModuleCount" class="v">—</div></div>
<div class="registryCard"><div class="l">PYTHON PACKAGES</div><div id="pythonPackageCount" class="v">—</div></div>
<div class="registryCard"><div class="l">SNAPSHOT SHA256</div><div id="registrySnapshot" class="v">—</div></div>
<div class="registryCard"><div class="l">SUPPORT LEDGER</div><div id="registryLedger" class="v">—</div></div>
<div class="registryCard"><div class="l">V0156 RUNTIME REGISTRY</div><div id="runtimeRegistryPath" class="v">—</div></div>
</div>
<div class="hint" style="margin-top:12px">
支援性工具採 SHA registry；只 Import 核准 PowerShell modules，不會盲目 dot-source 全部 supportive scripts。
</div>
</div>
</section>

<section id="page-logs" class="page">
<h2>Execution Logs <span class="en">worker events + gate evidence</span></h2>
<div class="panel logPanel">
<div class="actions">
<button onclick="byId('log').innerText='VIA VRN Sidebar Workbench ready.'">CLEAR DISPLAY</button>
<button onclick="switchPage('home')">BACK TO HOME</button>
</div>
<div id="log" class="log">VIA VRN Sidebar Workbench ready.</div>
</div>
</section>

<div class="footer">VIA VRN Visual Lock · fixed left navigation · multiple independent pages · no canonical mutation · disabled drafts only · 理</div>
</div>
</div>
</div>
</body>
</html>
'@

    $rendered = $html
    $rendered = $rendered.Replace("__DEFAULTS__", $defaultsJson)
    $rendered = $rendered.Replace("__CONFIG__", $configJson)
    $rendered = $rendered.Replace("__STATUS__", $statusJson)
    $rendered = $rendered.Replace("__DIALOG__", $dialogJson)
    $rendered = $rendered.Replace("__MAIN__", $mainJson)
    $rendered = $rendered.Replace("__PWSH__", $pwshJson)
    return $rendered
}

function Start-HtmlWorkbench {
    param([AllowEmptyString()][string]$RequestedBase)

    $baseRoot = (Resolve-BaseRoot -Requested $RequestedBase)
    $defaults = (Get-SevenDefaults -BaseRoot $baseRoot)

    $sessionId = "VRNUI_{0}_{1}" -f
        (Get-Date -Format "yyyyMMdd_HHmmss"),
        ([guid]::NewGuid().ToString("N").Substring(0, 8))

    $sessionRoot = (Join-Path -Path $env:TEMP -ChildPath "VIA_VRN_HTML_UI\$sessionId")

    Ensure-Directory -Path $sessionRoot

    $configPath = (Join-Path -Path $sessionRoot -ChildPath "worker_config.json")
    $statusPath = (Join-Path -Path $sessionRoot -ChildPath "worker_status.json")
    $dialogHelperPath = (Join-Path -Path $sessionRoot -ChildPath "VIA_VRN_WindowsDialog.ps1")
    $htaPath = (Join-Path -Path $sessionRoot -ChildPath "VIA_VRN_VisualLock_Workbench_v0159.hta")

    Write-DialogHelper -Path $dialogHelperPath

    $pwshPath = (Get-Process -Id $PID).Path

    $html = (Get-HtaHtml -Defaults $defaults -ConfigPath $configPath -StatusPath $statusPath -DialogHelperPath $dialogHelperPath -MainScriptPath $PSCommandPath -PowerShellPath $pwshPath)

    Write-Utf8NoBomAtomic `
        -Path $htaPath `
        -Text $html

    $mshta = (Join-Path -Path $env:WINDIR -ChildPath "System32\mshta.exe")

    if (-not (Test-Path -LiteralPath $mshta -PathType Leaf)) {
        throw "Windows mshta.exe is unavailable or disabled."
    }

    Write-Host ""
    Write-Host ("=" * 116) -ForegroundColor DarkCyan
    Write-Host (
        "def VIA · VRN VISUAL-LOCK WORKBENCH · v0159"
    ) -ForegroundColor Cyan
    Write-Host (
        "def Base       : {0}" -f $baseRoot
    ) -ForegroundColor White
    Write-Host (
        "def UI         : {0}" -f $htaPath
    ) -ForegroundColor Cyan
    Write-Host (
        "def Parameters : 7"
    ) -ForegroundColor Green
    Write-Host (
        "def Windows I/O: enabled"
    ) -ForegroundColor Green
    Write-Host (
        "def Drag/Drop  : enabled when Explorer supplies full path"
    ) -ForegroundColor Green
    Write-Host ("=" * 116) -ForegroundColor DarkCyan

    Start-Process `
        -FilePath $mshta `
        -ArgumentList ('"{0}"' -f $htaPath) `
        -Wait
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
    Write-Host (
        "def VIA · VRN VISUAL-LOCK WORKBENCH SAFE CATCH"
    ) -ForegroundColor Red
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
    Write-Host (
        "def Parent PowerShell remains open."
    ) -ForegroundColor Cyan
}

