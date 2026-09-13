#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$PathContract = Join-Path $PSScriptRoot 'VIA-VDF-Path-Contract.ps1'
if (-not (Test-Path -LiteralPath $PathContract -PathType Leaf)) {
    throw "找不到 VDF path contract：$PathContract"
}
. $PathContract

function Invoke-VDF-Fetch {
    param(
        [ValidateSet('status', 'open-database', 'show-plan', 'show-manifest', 'show-result', 'open-report')]
        [string]$Action = 'status',
        [string]$DataRoot = ''
    )

    $Root = Resolve-VDFDataRoot -RequestedRoot $DataRoot
    $ControllerRoot = Join-Path $Root 'dict\VDF\_active\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337'
    $DatabaseRoot = Join-Path $Root 'dict\VDF\DATABASE'
    $FetchPlan = Join-Path $ControllerRoot 'registry\VDF_ProductionFetchPlan_v016.json'
    $FetchManifest = Join-Path $ControllerRoot 'registry\VDF_ProductionFetchManifest_v016.json'
    $FetchResult = Join-Path $ControllerRoot 'runtime\vdf_production_fetch_result_v016.json'
    $PythonController = Join-Path $ControllerRoot 'runtime\vdf_production_fetch_controller_v016.py'
    $HtmlReport = Join-Path $ControllerRoot 'report\VDF_ProductionFetchController_Report_v016.html'
    $Required = @($DatabaseRoot, $FetchPlan, $FetchManifest, $FetchResult, $PythonController, $HtmlReport)
    $Missing = @($Required | Where-Object { -not (Test-Path -LiteralPath $_) })
    $Status = if ($Missing.Count -eq 0 -and (Test-VDFDataContract -Root $Root)) { 'VDF_PRODUCTION_FETCH_CONTROLLER_READY' } else { 'VDF_PRODUCTION_FETCH_CONTROLLER_BLOCKED' }

    if ($Action -eq 'status') {
        [pscustomobject]@{
            status = $Status
            database_root = $DatabaseRoot
            fetch_plan = $FetchPlan
            fetch_manifest = $FetchManifest
            fetch_result = $FetchResult
            python_controller = $PythonController
            html_report = $HtmlReport
            missing = $Missing
            policy = 'Network disabled unless caller explicitly enables it. VIA_DATA_ROOT only. No delete. No Stop-Process. No exit.'
        } | Format-List
        return
    }

    $Target = switch ($Action) {
        'open-database' { $DatabaseRoot }
        'show-plan' { $FetchPlan }
        'show-manifest' { $FetchManifest }
        'show-result' { $FetchResult }
        'open-report' { $HtmlReport }
    }
    Assert-VDFPath -Path $Target
    if ($Action -like 'open-*') {
        Open-VDFShellPath -Path $Target
    }
    else {
        Get-Content -LiteralPath $Target -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
    }
}

Invoke-VDF-Fetch @args
