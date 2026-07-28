#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$PackageRoot,
    [Parameter(Mandatory)][string]$OutputJson
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$binDir = Join-Path $PackageRoot 'supportive modules/VIA_Governance_Runtime/v0162B/bin'
$allInOne = Join-Path $binDir 'Invoke-VIA-SystemManager-AllInOne-v0162B.ps1'
$engineFile = Join-Path $PackageRoot 'supportive modules/VIA_Governance_Runtime/v0162B/engine/via_system_manager_engine_v0162B.py'
$workbenchFile = Join-Path $PackageRoot 'supportive modules/VIA_Governance_Runtime/v0162B/ui/VIA_SystemManager_v0162B_Preview.html'

$results = [ordered]@{}

function Get-AstReport {
    param([string]$Path)
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
    $errorRows = @(
        @($parseErrors) | ForEach-Object {
            [ordered]@{
                line    = $_.Extent.StartLineNumber
                column  = $_.Extent.StartColumnNumber
                message = $_.Message
            }
        }
    )
    return @{ ast = $ast; tokens = $tokens; errors = $errorRows }
}

# 1. AST validation of every shipped .ps1
$scripts = @(
    @{ Key = 'allinone_ast';       Path = $allInOne },
    @{ Key = 'start_manager_ast';  Path = (Join-Path $PackageRoot 'StartVIASystemManager.ps1') },
    @{ Key = 'start_unified_ast';  Path = (Join-Path $PackageRoot 'StartVIAUnified.ps1') }
)
$allInOneReport = $null
foreach ($script in $scripts) {
    $report = Get-AstReport -Path $script.Path
    if ($script.Key -eq 'allinone_ast') { $allInOneReport = $report }
    $results[$script.Key] = [ordered]@{
        path   = $script.Path
        status = if (@($report.errors).Count -eq 0) { 'PASS' } else { 'FAIL' }
        errors = $report.errors
    }
}

# 2. Expandable here-string token scan (v0162A root cause must stay absent)
$expandable = @(
    @($allInOneReport.tokens) | Where-Object {
        $_.Kind -eq [System.Management.Automation.Language.TokenKind]::HereStringExpandable
    }
)
$results['expandable_here_string_scan'] = [ordered]@{
    status = if (@($expandable).Count -eq 0) { 'PASS' } else { 'FAIL' }
    expandable_here_string_count = @($expandable).Count
}

# 3. Embedded asset roundtrip: evaluate the three here-string assignments from
#    the AST and confirm materialized bytes match the canonical artifacts.
function Get-EmbeddedValue {
    param($Ast, [string]$VariableName)
    $assignments = $Ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
        $node.Left.Extent.Text -eq ('$Script:' + $VariableName)
    }, $true)
    if (@($assignments).Count -ne 1) {
        throw ('Expected exactly one assignment for ' + $VariableName)
    }
    $expr = @($assignments)[0].Right.Expression
    if ($expr -isnot [System.Management.Automation.Language.StringConstantExpressionAst]) {
        throw ($VariableName + ' is not a constant single-quoted string')
    }
    return [string]$expr.Value
}

function Get-TextSha256 {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') })
    }
    finally { $sha.Dispose() }
}

$engineEmbedded = Get-EmbeddedValue -Ast $allInOneReport.ast -VariableName 'EngineSource'
$workbenchEmbedded = Get-EmbeddedValue -Ast $allInOneReport.ast -VariableName 'WorkbenchSource'
$templateEmbedded = Get-EmbeddedValue -Ast $allInOneReport.ast -VariableName 'EntrypointTemplate'

$engineExpected = (Get-FileHash -LiteralPath $engineFile -Algorithm SHA256).Hash.ToLowerInvariant()
$workbenchExpected = (Get-FileHash -LiteralPath $workbenchFile -Algorithm SHA256).Hash.ToLowerInvariant()
$engineActual = Get-TextSha256 -Text ($engineEmbedded + "`n")
$workbenchActual = Get-TextSha256 -Text ($workbenchEmbedded + "`n")

$results['embedded_engine_roundtrip'] = [ordered]@{
    status = if ($engineActual -eq $engineExpected) { 'PASS' } else { 'FAIL' }
    expected_sha256 = $engineExpected
    materialized_sha256 = $engineActual
}
$results['embedded_workbench_roundtrip'] = [ordered]@{
    status = if ($workbenchActual -eq $workbenchExpected) { 'PASS' } else { 'FAIL' }
    expected_sha256 = $workbenchExpected
    materialized_sha256 = $workbenchActual
}

# 4. Entrypoint generation gate: template + real AllInOne SHA must reproduce
#    the shipped Start launchers byte-for-byte, and the generated text must
#    itself pass AST validation.
$allInOneSHA = (Get-FileHash -LiteralPath $allInOne -Algorithm SHA256).Hash.ToLowerInvariant()
$canonicalLauncher = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0162B\bin\Invoke-VIA-SystemManager-AllInOne-v0162B.ps1'
$canonicalBase = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
$generated = $templateEmbedded
$generated = $generated.Replace('{{VIA_LAUNCHER_PATH}}', $canonicalLauncher)
$generated = $generated.Replace('{{VIA_EXPECTED_SHA}}', $allInOneSHA)
$generated = $generated.Replace('{{VIA_BASE}}', $canonicalBase)

$startShipped = [System.IO.File]::ReadAllText((Join-Path $PackageRoot 'StartVIASystemManager.ps1'))
$unifiedShipped = [System.IO.File]::ReadAllText((Join-Path $PackageRoot 'StartVIAUnified.ps1'))
$results['entrypoint_template_roundtrip'] = [ordered]@{
    status = if ($generated -eq $startShipped -and $generated -eq $unifiedShipped) { 'PASS' } else { 'FAIL' }
    allinone_sha256 = $allInOneSHA
}

$generatedTokens = $null
$generatedErrors = $null
[System.Management.Automation.Language.Parser]::ParseInput($generated, [ref]$generatedTokens, [ref]$generatedErrors) | Out-Null
$results['generated_daily_launcher_ast'] = [ordered]@{
    status = if (@($generatedErrors).Count -eq 0) { 'PASS' } else { 'FAIL' }
    errors = @(@($generatedErrors) | ForEach-Object { $_.Message })
}

$results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputJson -Encoding UTF8
$failed = @($results.Values | Where-Object { $_ -is [System.Collections.IDictionary] -and $_['status'] -eq 'FAIL' })
if (@($failed).Count -gt 0) {
    Write-Host 'QA FAIL' -ForegroundColor Red
    exit 2
}
Write-Host 'QA PASS'
