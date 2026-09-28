# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = "Stop"

$P0GroupCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv"
$P1AliasCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv"
$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_SecretGateFinal.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_Load $P0GroupCsv
$p1 = def_Load $P1AliasCsv
$sec = def_Load $SecretCsv

$secPending = @($sec | Where-Object { ([string]$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
$p0Pending = @($p0 | Where-Object { ([string]$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending = @($p1 | Where-Object { ([string]$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113H Precheck after v0113G" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending  : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 group pending: $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 alias pending: $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_GROUP_ACCEPT_REQUIRED. Edit compressed group boards and set accepted groups to YES."
}

Write-Host "[OK] READY_FOR_v0113H_ROW_LEVEL_ACCEPT_EXPANSION_PREVIEW" -ForegroundColor Green

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
