#requires -Version 7.0
Set-StrictMode -Version Latest

function Resolve-VDFDataRoot {
    param([AllowEmptyString()][string]$RequestedRoot = '')

    $Candidate = if ($RequestedRoot) {
        $RequestedRoot
    }
    elseif ($env:VIA_DATA_ROOT) {
        $env:VIA_DATA_ROOT
    }
    else {
        (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
    }
    if (-not [IO.Path]::IsPathRooted($Candidate)) {
        throw "VIA_DATA_ROOT 必須是絕對路徑：$Candidate"
    }
    return [IO.Path]::GetFullPath($Candidate).TrimEnd('\')
}

function Test-VDFDataContract {
    param([Parameter(Mandatory)][string]$Root)

    $Required = @(
        'dict\VDF\DATABASE',
        'dict\VDF\_ssot',
        'dict\VDF\_active'
    )
    return @($Required | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $Root $_))
    }).Count -eq 0
}

function Assert-VDFPath {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "VDF 路徑不存在：$Path"
    }
}

function Open-VDFShellPath {
    param([Parameter(Mandatory)][string]$Path)

    Assert-VDFPath -Path $Path
    $Info = [System.Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Path
    $Info.UseShellExecute = $true
    $null = [System.Diagnostics.Process]::Start($Info)
}
