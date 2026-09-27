# Register-VIA-Commands-v0258.ps1 — via-vcgc 是唯一入口。指令結束後跳出子系統矩陣。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0257.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vcgc {
    $env:VIA_FROM_VCGC = "YES"
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    if (-not $eng) { Write-Host "  [via-vcgc] FAIL:console tail missing" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } elseif ($_ -eq "-Publish") { "--publish" } elseif ($_ -eq "-Apply") { "--apply" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
    $code = $LASTEXITCODE
    $pop = Join-Path $PSScriptRoot "Invoke-VIA-VCGC-Probe.ps1"
    if (Test-Path -LiteralPath $pop) { & $pop }
    $global:LASTEXITCODE = $code
}
Set-Alias -Name 中央控管 -Value via-vcgc -Scope Global -Force
