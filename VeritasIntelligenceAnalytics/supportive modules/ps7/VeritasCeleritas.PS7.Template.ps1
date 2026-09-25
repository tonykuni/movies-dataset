# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =============================================================================
#  Veritas Celeritas · PS 生成模板
#  凡 AI 被要求產出 .ps1，必須接入本檔，不得裸奔。
#  契約：只動 $PID · 關閉即還原 · 不改系統檔 · ErrorAction Continue
# =============================================================================
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "Celeritas 模板需要 PowerShell 7+。"
}

$script:CeleritasTemplate = [ordered]@{
    Version = 'v1141'
    Marker  = 'CELERITAS-TEMPLATE-JOIN v1'
    Joined  = $false
}

$join = Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.ps1'
if (-not (Test-Path -LiteralPath $join)) {
    $alt = Join-Path (Split-Path -Parent $PSScriptRoot) 'ps7\VeritasCeleritas.PS7.ps1'
    if (Test-Path -LiteralPath $alt) { $join = $alt }
}

if (Test-Path -LiteralPath $join) {
    . $join
    if (-not $script:CeleritasPS7.Applied) { [void](Start-CeleritasPS7) }
    $script:CeleritasTemplate.Version = [string]$script:CeleritasPS7.Version
    $script:CeleritasTemplate.Joined = $true
}

function Invoke-CeleritasGenerated {
    param([Parameter(Mandatory)][scriptblock]$Body)
    try {
        & $Body
    }
    finally {
        if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
            Restore-CeleritasPS7
        }
    }
}

function Test-CeleritasJoin {
    return [pscustomobject]@{
        Marker  = $script:CeleritasTemplate.Marker
        Joined  = [bool]$script:CeleritasTemplate.Joined
        Version = $script:CeleritasTemplate.Version
        PidOnly = $true
    }
}
