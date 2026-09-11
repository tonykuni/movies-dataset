#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$PathContract = Join-Path $PSScriptRoot 'VIA-VDF-Path-Contract.ps1'
if (-not (Test-Path -LiteralPath $PathContract -PathType Leaf)) {
    throw "找不到 VDF path contract：$PathContract"
}
. $PathContract

function Invoke-VDF {
    param(
        [ValidateSet('status', 'open-database', 'open-header-registry', 'show-active-pointer', 'show-ssot', 'show-output-manifest')]
        [string]$Action = 'status',
        [string]$DataRoot = ''
    )

    $Root = Resolve-VDFDataRoot -RequestedRoot $DataRoot
    $VdfDict = Join-Path $Root 'dict\VDF'
    $SsotDir = Join-Path $VdfDict '_ssot'
    $DbDir = Join-Path $VdfDict 'DATABASE'
    $ParamsJson = Join-Path $SsotDir 'VDF_Extraction_Params_SSOT.json'
    $HeaderRegistryJson = Join-Path $SsotDir 'VDF_DataScope_HeaderRegistry_SSOT.json'
    $ActivePointer = Join-Path $VdfDict '_active\VDF_ACTIVE_POINTER.json'
    $OutputManifest = Join-Path $VdfDict '_active\VDF_ACTIVE_READER_USERTEST_v014_20260609_215513\registry\VDF_DatabaseSkeleton_OutputManifest_v014.json'
    $Required = @($ParamsJson, $HeaderRegistryJson, $DbDir, $ActivePointer, $OutputManifest)
    $Missing = @($Required | Where-Object { -not (Test-Path -LiteralPath $_) })
    $Status = if ($Missing.Count -eq 0 -and (Test-VDFDataContract -Root $Root)) { 'VDF_ACTIVE_READER_READY' } else { 'VDF_ACTIVE_READER_BLOCKED' }

    if ($Action -eq 'status') {
        [pscustomobject]@{
            status = $Status
            root = $Root
            params_ssot = $ParamsJson
            header_registry = $HeaderRegistryJson
            database = $DbDir
            active_pointer = $ActivePointer
            output_manifest = $OutputManifest
            missing = $Missing
            policy = 'Read SSOT. VIA_DATA_ROOT only. No delete. No Stop-Process. No exit.'
        } | Format-List
        return
    }

    $Target = switch ($Action) {
        'open-database' { $DbDir }
        'open-header-registry' { $HeaderRegistryJson }
        'show-active-pointer' { $ActivePointer }
        'show-ssot' { $ParamsJson }
        'show-output-manifest' { $OutputManifest }
    }
    Assert-VDFPath -Path $Target
    if ($Action -like 'open-*') {
        Open-VDFShellPath -Path $Target
    }
    else {
        Get-Content -LiteralPath $Target -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
    }
}

Invoke-VDF @args
