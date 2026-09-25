Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Script:BridgeContract = "veritas.vofie-powershell-tool-bridge/1.2"
$Script:SourcePolicy = "READ_ONLY_NO_DELETE_NO_MOVE_NO_CANONICAL_MUTATION"
$Script:ExpectedModuleCount = 18
$Script:ModuleNames = @(
    "PSScriptAnalyzer", "Pester", "PSRule", "Microsoft.PowerShell.PSResourceGet",
    "PowerShellGet", "platyPS", "InvokeBuild", "psake", "PSDepend", "ThreadJob",
    "PoshRSJob", "ImportExcel", "powershell-yaml", "PSToml", "PsIni", "PSWriteHTML",
    "Pode", "PSFramework"
)


function Test-VOFIEPowerShellFile {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$LiteralPath)

    $resolved = (Resolve-Path -LiteralPath $LiteralPath -ErrorAction Stop).Path
    $before = Get-Item -LiteralPath $resolved
    $tokens = $null
    $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile($resolved, [ref]$tokens, [ref]$errors)
    $functions = @($ast.FindAll({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] }, $true))
    $after = Get-Item -LiteralPath $resolved
    [pscustomobject]@{
        contract       = $Script:BridgeContract
        path           = $resolved
        gate           = $(if ($errors.Count -eq 0 -and $before.Length -eq $after.Length) { "PASS" } else { "FAIL" })
        parse_errors   = @($errors | ForEach-Object { $_.Message })
        function_count = $functions.Count
        functions      = @($functions | ForEach-Object { $_.Name })
        source_mutated = ($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc)
        source_policy  = $Script:SourcePolicy
    }
}


function Get-VOFIEPowerShellToolInventory {
    [CmdletBinding()]
    param()

    $rows = [Collections.Generic.List[object]]::new()
    $rows.Add([pscustomobject]@{
        name = "PowerShell 7"; module = ""; status = "AVAILABLE";
        version = $PSVersionTable.PSVersion.ToString(); source_mutated = $false
    })
    $rows.Add([pscustomobject]@{
        name = "System.Management.Automation AST Parser"; module = "Microsoft.PowerShell.Core";
        status = "BUILTIN"; version = $PSVersionTable.PSVersion.ToString(); source_mutated = $false
    })
    foreach ($name in $Script:ModuleNames) {
        $module = Get-Module -ListAvailable -Name $name | Sort-Object Version -Descending | Select-Object -First 1
        $rows.Add([pscustomobject]@{
            name = $name; module = $name;
            status = $(if ($null -ne $module) { "AVAILABLE" } else { "NOT_INSTALLED" });
            version = $(if ($null -ne $module) { $module.Version.ToString() } else { "" });
            source_mutated = $false
        })
    }
    [pscustomobject]@{
        contract = $Script:BridgeContract
        gate = $(if ($rows.Count -eq 20) { "PASS" } else { "FAIL" })
        total = $rows.Count
        available = @($rows | Where-Object status -in @("AVAILABLE", "BUILTIN")).Count
        not_installed = @($rows | Where-Object status -eq "NOT_INSTALLED").Count
        source_policy = $Script:SourcePolicy
        tools = $rows.ToArray()
    }
}


function Invoke-VOFIEPowerShellBridgeSelfTest {
    [CmdletBinding()]
    param([string]$LauncherPath = (Join-Path $PSScriptRoot "..\Invoke-Veritas-VOFIE.ps1"))

    $syntax = Test-VOFIEPowerShellFile -LiteralPath $LauncherPath
    $inventory = Get-VOFIEPowerShellToolInventory
    $passed = @(
        $syntax.gate -eq "PASS",
        -not $syntax.source_mutated,
        $inventory.gate -eq "PASS",
        $inventory.total -eq 20
    )
    [pscustomobject]@{
        contract = $Script:BridgeContract
        gate = $(if ($passed -notcontains $false) { "PASS" } else { "FAIL" })
        passed = @($passed | Where-Object { $_ }).Count
        failed = @($passed | Where-Object { -not $_ }).Count
        syntax = $syntax
        inventory = $inventory
    }
}


function Export-VOFIEPowerShellToolReport {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$LiteralPath,
        [string]$LauncherPath = (Join-Path $PSScriptRoot "..\Invoke-Veritas-VOFIE.ps1")
    )

    $payload = Invoke-VOFIEPowerShellBridgeSelfTest -LauncherPath $LauncherPath
    $parent = Split-Path -Parent $LiteralPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        $null = New-Item -ItemType Directory -Path $parent -Force
    }
    $payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $LiteralPath -Encoding utf8
    Get-Item -LiteralPath $LiteralPath
}


Export-ModuleMember -Function @(
    "Test-VOFIEPowerShellFile",
    "Get-VOFIEPowerShellToolInventory",
    "Invoke-VOFIEPowerShellBridgeSelfTest",
    "Export-VOFIEPowerShellToolReport"
)

