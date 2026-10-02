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
    UI      = ''
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

# [CELERITAS-UI v0100] 主控台呈現件:YFinance 啟動器(VDF_MDL002)的 Rich 版型,純 PS 重做。
# 操作員 2026-10-02「他 PS U/I 呈現很美 可採用加入標準 PS 模板」(VCGC-REQ124)。只增;缺檔不擋。
# 用法:Write-CeleritasRichMatrix -Title … -Rows …(計數判決同 Write-CeleritasMatrixSummary)· Write-CeleritasTable · Write-CeleritasPanel · Test-CeleritasUI
$celeritasUIPath = Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.UI.ps1'
if ($script:CeleritasTemplate.Joined -and (Test-Path -LiteralPath $celeritasUIPath)) {
    . $celeritasUIPath
    $script:CeleritasTemplate.UI = [string]$script:CeleritasUI.Version
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
        UI      = $script:CeleritasTemplate.UI
        PidOnly = $true
    }
}
