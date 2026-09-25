[CmdletBinding()]
param(
    [ValidateSet("Core", "All")]
    [string]$Profile = "Core",

    [string]$PythonCommand = "python",

    [string]$IndexUrl = "https://pypi.org/simple",

    [switch]$Force,

    [switch]$FailOnOptionalError
)

# =============================================================================
# 01. PARAMETERS AND PATHS
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$CoreRequirements = Join-Path $ScriptRoot "requirements-core.txt"
$OptionalRequirements = Join-Path $ScriptRoot "requirements-all-optional.txt"
$StateDirectory = Join-Path $ScriptRoot "_install_state"
$StatePath = Join-Path $StateDirectory "GenericLayoutEngine.InstallState.json"
$AuditPath = Join-Path $StateDirectory "GenericLayoutEngine.InstallAudit.json"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"


# =============================================================================
# 02. SUPPORT FUNCTIONS
# =============================================================================

function Get-RequirementsHash {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Paths
    )

    $HashInput = foreach ($Path in $Paths) {
        if (Test-Path -LiteralPath $Path) {
            Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        }
    }
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes(($HashInput -join "`n"))
    $Stream = [System.IO.MemoryStream]::new($Bytes)
    try {
        return (Get-FileHash -InputStream $Stream -Algorithm SHA256).Hash
    }
    finally {
        $Stream.Dispose()
    }
}


function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$AllowFailure
    )

    & $PythonCommand @Arguments | Out-Host
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0 -and -not $AllowFailure) {
        throw "Python command failed with exit code ${ExitCode}: $($Arguments -join ' ')"
    }
    return $ExitCode
}


function Get-RequirementLines {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return @(
        Get-Content -LiteralPath $Path -Encoding UTF8 |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and -not $_.StartsWith("#") }
    )
}


function Install-RequirementList {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Requirements,

        [Parameter(Mandatory = $true)]
        [bool]$Optional
    )

    $Results = @()
    foreach ($Requirement in $Requirements) {
        Write-Host "Installing $Requirement" -ForegroundColor Cyan
        $ExitCode = Invoke-Python -Arguments @(
            "-m", "pip", "install", "--index-url", $IndexUrl, $Requirement
        ) -AllowFailure:$Optional
        $Results += [ordered]@{
            requirement = $Requirement
            optional = $Optional
            exit_code = $ExitCode
            status = if ($ExitCode -eq 0) { "PASS" } else { "FAIL" }
        }
        if ($ExitCode -ne 0 -and $Optional -and $FailOnOptionalError) {
            throw "Optional dependency failed under FailOnOptionalError: $Requirement"
        }
    }
    return $Results
}


# =============================================================================
# 03. HASH-STATE-MACHINE IDEMPOTENCY
# =============================================================================

if (-not (Test-Path -LiteralPath $CoreRequirements)) {
    throw "Missing requirements file: $CoreRequirements"
}

$RequirementPaths = @($CoreRequirements)
if ($Profile -eq "All") {
    $RequirementPaths += $OptionalRequirements
}
$RequirementsHash = Get-RequirementsHash -Paths $RequirementPaths

if (Test-Path -LiteralPath $StatePath) {
    $ExistingState = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (
        -not $Force -and
        $ExistingState.profile -eq $Profile -and
        $ExistingState.requirements_sha256 -eq $RequirementsHash -and
        $ExistingState.status -eq "PASS"
    ) {
        Write-Host "SKIP: identical requirements/profile already installed." -ForegroundColor Green
        return
    }

    $BackupPath = "$StatePath.$Timestamp.bak"
    Copy-Item -LiteralPath $StatePath -Destination $BackupPath
}

New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null


# =============================================================================
# 04. INSTALLATION
# =============================================================================

$PythonVersion = & $PythonCommand --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Python command is unavailable: $PythonCommand"
}

Invoke-Python -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") | Out-Null

$InstallResults = @()
$InstallResults += Install-RequirementList -Requirements (Get-RequirementLines -Path $CoreRequirements) -Optional:$false

if ($Profile -eq "All") {
    if (-not (Test-Path -LiteralPath $OptionalRequirements)) {
        throw "Missing optional requirements file: $OptionalRequirements"
    }
    $InstallResults += Install-RequirementList -Requirements (Get-RequirementLines -Path $OptionalRequirements) -Optional:$true
}

$PipCheckExitCode = Invoke-Python -Arguments @("-m", "pip", "check") -AllowFailure
$FailedCount = @($InstallResults | Where-Object { $_.status -eq "FAIL" }).Count
$FinalStatus = if ($FailedCount -eq 0 -and $PipCheckExitCode -eq 0) { "PASS" } else { "WARN" }


# =============================================================================
# 05. AUDIT AND STATE COMMIT
# =============================================================================

$Audit = [ordered]@{
    engine = "GenericLayoutExtractionOS"
    version = "2.1.0"
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    profile = $Profile
    python = [string]$PythonVersion
    index_url = $IndexUrl
    requirements_sha256 = $RequirementsHash
    pip_check_exit_code = $PipCheckExitCode
    failed_optional_count = $FailedCount
    status = $FinalStatus
    results = $InstallResults
}

$Audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $AuditPath -Encoding UTF8
$Audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatePath -Encoding UTF8

Write-Host "Installation status: $FinalStatus" -ForegroundColor $(if ($FinalStatus -eq "PASS") { "Green" } else { "Yellow" })
Write-Host "Audit: $AuditPath"
Write-Host "The current PowerShell window will remain open."
