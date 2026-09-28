#requires -Version 7.0
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
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
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

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
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
