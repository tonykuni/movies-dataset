[CmdletBinding()]
param(
    [ValidateSet('Validate', 'Status', 'InstructionAst', 'AstIndex', 'ContextPack', 'ValidateHandoff', 'Lease', 'Allocate')]
    [string]$Action = 'Validate',
    [string]$PythonExe = $env:VIA_PYTHON,
    [string]$RepoRoot = '',
    [string]$ScanRoot = '',
    [string]$TaskPath = '',
    [string]$HandoffPath = '',
    [ValidateSet('PREFLIGHT', 'DATA', 'CORE', 'UI', 'QA', 'OPS')]
    [string]$Layer = 'CORE',
    [string]$Slug = '',
    [string]$Title = '',
    [string]$Owner = 'ChatGPT',
    [string]$LeaseId = '',
    [ValidateRange(1, 1000)]
    [int]$LeaseSize = 20,
    [string]$Branch = 'ChatGPT',
    [string]$BaseSha = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================================
# 01. PARAMETERS AND PATHS
# ============================================================================

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnginePath = Join-Path $ScriptRoot 'src\via_ai_workflow.py'
$DefaultRepoCandidates = @(
    $env:VIA_REPO_ROOT,
    'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics'
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

# ============================================================================
# 02. RESOLUTION
# ============================================================================

function Resolve-VIAPython {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (-not (Test-Path -LiteralPath $Requested -PathType Leaf)) {
            throw "Python executable not found: $Requested"
        }
        return @{ File = $Requested; Prefix = @() }
    }

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $PythonCommand) {
        return @{ File = $PythonCommand.Source; Prefix = @() }
    }

    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        return @{ File = $PyLauncher.Source; Prefix = @('-3.12') }
    }

    throw 'Python 3.10 or newer was not found. Set VIA_PYTHON or pass -PythonExe.'
}

function Resolve-VIARepoRoot {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (-not (Test-Path -LiteralPath $Requested -PathType Container)) {
            throw "Repository root not found: $Requested"
        }
        return (Resolve-Path -LiteralPath $Requested).Path
    }

    foreach ($Candidate in $DefaultRepoCandidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Container) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }

    throw 'VIA repository root was not found. Set VIA_REPO_ROOT or pass -RepoRoot.'
}

function Invoke-VIAPython {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )

    & $Python.File @($Python.Prefix) $EnginePath @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "VIA AI Workflow failed with exit code $ExitCode"
    }
}

# ============================================================================
# 03. DISPATCH
# ============================================================================

function Invoke-VIAAction {
    param([string]$SelectedAction)

    $Python = Resolve-VIAPython -Requested $PythonExe
    switch ($SelectedAction) {
        'Validate' {
            $Arguments = @('validate')
            if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
                $Arguments += @('--repo-root', (Resolve-VIARepoRoot -Requested $RepoRoot))
            }
            Invoke-VIAPython -Python $Python -Arguments $Arguments
        }
        'Status' {
            Invoke-VIAPython -Python $Python -Arguments @('status')
        }
        'InstructionAst' {
            Invoke-VIAPython -Python $Python -Arguments @('instruction-ast')
        }
        'AstIndex' {
            $ResolvedScanRoot = if ([string]::IsNullOrWhiteSpace($ScanRoot)) {
                Resolve-VIARepoRoot -Requested $RepoRoot
            } else {
                Resolve-VIARepoRoot -Requested $ScanRoot
            }
            Invoke-VIAPython -Python $Python -Arguments @('ast-index', '--root', $ResolvedScanRoot)
        }
        'ContextPack' {
            if ([string]::IsNullOrWhiteSpace($TaskPath)) {
                throw '-TaskPath is required for ContextPack.'
            }
            Invoke-VIAPython -Python $Python -Arguments @('context-pack', '--task', $TaskPath)
        }
        'ValidateHandoff' {
            if ([string]::IsNullOrWhiteSpace($HandoffPath)) {
                throw '-HandoffPath is required for ValidateHandoff.'
            }
            Invoke-VIAPython -Python $Python -Arguments @('validate-handoff', '--path', $HandoffPath)
        }
        'Lease' {
            if ([string]::IsNullOrWhiteSpace($BaseSha)) {
                throw '-BaseSha is required for Lease.'
            }
            Invoke-VIAPython -Python $Python -Arguments @(
                'lease', '--agent', $Owner, '--size', [string]$LeaseSize,
                '--branch', $Branch, '--base-sha', $BaseSha
            )
        }
        'Allocate' {
            if ([string]::IsNullOrWhiteSpace($Slug) -or [string]::IsNullOrWhiteSpace($Title)) {
                throw '-Slug and -Title are required for Allocate.'
            }
            $Arguments = @('allocate', '--layer', $Layer, '--slug', $Slug, '--title', $Title, '--owner', $Owner)
            if (-not [string]::IsNullOrWhiteSpace($LeaseId)) {
                $Arguments += @('--lease-id', $LeaseId)
            }
            Invoke-VIAPython -Python $Python -Arguments $Arguments
        }
        default {
            throw "Unsupported action: $SelectedAction"
        }
    }
}

Invoke-VIAAction -SelectedAction $Action

