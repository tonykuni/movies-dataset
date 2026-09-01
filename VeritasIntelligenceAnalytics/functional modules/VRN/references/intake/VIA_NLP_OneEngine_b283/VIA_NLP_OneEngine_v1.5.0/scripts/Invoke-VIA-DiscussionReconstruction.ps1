[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$InputPath,

    [string]$OutputDirectory = ".\VIA_Reconstruction_Output",

    [string]$ConfigPath = ".\config\default.json",

    [ValidateSet("knowledge", "govern")]
    [string]$Task = "knowledge",

    [ValidateSet("fast", "balanced")]
    [string]$Quality = "balanced",

    [int]$MaxFiles = 1000,

    [long]$MaxTotalBytes = 536870912,

    [long]$MaxFileBytes = 52428800,

    [switch]$NoRecursive,

    [switch]$MarkItDown,

    [string]$PreviousPackage = "",

    [string]$PythonExecutable = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"


function Resolve-VIAProjectRoot {
    [CmdletBinding()]
    param()

    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}


function Resolve-VIAPythonCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot,

        [string]$RequestedExecutable
    )

    if ($RequestedExecutable) {
        $Resolved = Get-Command -Name $RequestedExecutable -ErrorAction Stop
        return [pscustomobject]@{
            Executable = $Resolved.Source
            PrefixArguments = @()
        }
    }

    $VirtualEnvironmentPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $VirtualEnvironmentPython -PathType Leaf) {
        return [pscustomobject]@{
            Executable = $VirtualEnvironmentPython
            PrefixArguments = @()
        }
    }

    $Python = Get-Command -Name "python" -ErrorAction SilentlyContinue
    if ($Python) {
        return [pscustomobject]@{
            Executable = $Python.Source
            PrefixArguments = @()
        }
    }

    $PyLauncher = Get-Command -Name "py" -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        return [pscustomobject]@{
            Executable = $PyLauncher.Source
            PrefixArguments = @("-3.12")
        }
    }

    throw "找不到 Python。請先執行 Install-VIA-NLPOneEngine.ps1，或傳入 -PythonExecutable。"
}


function Resolve-VIAInputPaths {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Paths
    )

    $Resolved = foreach ($Path in $Paths) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "找不到輸入路徑：$Path"
        }
        (Resolve-Path -LiteralPath $Path).Path
    }
    return @($Resolved | Sort-Object -Unique)
}


function Invoke-VIADiscussionReconstruction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$ResolvedInputPath,

        [Parameter(Mandatory = $true)]
        [string]$ResolvedOutputDirectory,

        [Parameter(Mandatory = $true)]
        [string]$ResolvedConfigPath,

        [Parameter(Mandatory = $true)]
        [pscustomobject]$PythonCommand,

        [Parameter(Mandatory = $true)]
        [string]$SelectedTask,

        [Parameter(Mandatory = $true)]
        [string]$SelectedQuality,

        [Parameter(Mandatory = $true)]
        [int]$SelectedMaxFiles,

        [Parameter(Mandatory = $true)]
        [long]$SelectedMaxTotalBytes,

        [Parameter(Mandatory = $true)]
        [long]$SelectedMaxFileBytes,

        [Parameter(Mandatory = $true)]
        [bool]$Recursive,

        [bool]$UseMarkItDown,

        [string]$ResolvedPreviousPackage
    )

    $Arguments = @($PythonCommand.PrefixArguments)
    $Arguments += @(
        "-m", "via_nlp_engine",
        "--config", $ResolvedConfigPath,
        "reconstruct-bundle",
        "--input"
    )
    $Arguments += $ResolvedInputPath
    $Arguments += @(
        "--output-dir", $ResolvedOutputDirectory,
        "--task", $SelectedTask,
        "--quality", $SelectedQuality,
        "--max-files", $SelectedMaxFiles.ToString(),
        "--max-total-bytes", $SelectedMaxTotalBytes.ToString(),
        "--max-file-bytes", $SelectedMaxFileBytes.ToString()
    )
    $Arguments += $(if ($Recursive) { "--recursive" } else { "--no-recursive" })
    if ($UseMarkItDown) {
        $Arguments += "--markitdown"
    }
    if ($ResolvedPreviousPackage) {
        $Arguments += @("--previous-package", $ResolvedPreviousPackage)
    }

    & $PythonCommand.Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "VIA discussion reconstruction failed with exit code $LASTEXITCODE"
    }
}


function Start-VIADiscussionReconstruction {
    [CmdletBinding()]
    param()

    $ProjectRoot = Resolve-VIAProjectRoot
    $ResolvedInputs = Resolve-VIAInputPaths -Paths $InputPath
    $ConfigCandidate = $(if ([IO.Path]::IsPathRooted($ConfigPath)) { $ConfigPath } else { Join-Path $ProjectRoot $ConfigPath })
    $OutputCandidate = $(if ([IO.Path]::IsPathRooted($OutputDirectory)) { $OutputDirectory } else { Join-Path $ProjectRoot $OutputDirectory })
    $ResolvedConfig = (Resolve-Path -LiteralPath $ConfigCandidate).Path
    $ResolvedOutput = [IO.Path]::GetFullPath($OutputCandidate)
    $PythonCommand = Resolve-VIAPythonCommand -ProjectRoot $ProjectRoot -RequestedExecutable $PythonExecutable
    $ResolvedPrevious = ""
    if ($PreviousPackage) {
        $ResolvedPrevious = (Resolve-Path -LiteralPath $PreviousPackage).Path
    }

    Push-Location $ProjectRoot
    try {
        $InvokeParameters = @{
            ResolvedInputPath = $ResolvedInputs
            ResolvedOutputDirectory = $ResolvedOutput
            ResolvedConfigPath = $ResolvedConfig
            PythonCommand = $PythonCommand
            SelectedTask = $Task
            SelectedQuality = $Quality
            SelectedMaxFiles = $MaxFiles
            SelectedMaxTotalBytes = $MaxTotalBytes
            SelectedMaxFileBytes = $MaxFileBytes
            ResolvedPreviousPackage = $ResolvedPrevious
            Recursive = (-not $NoRecursive.IsPresent)
            UseMarkItDown = $MarkItDown.IsPresent
        }
        Invoke-VIADiscussionReconstruction @InvokeParameters
    }
    finally {
        Pop-Location
    }
}


Start-VIADiscussionReconstruction
