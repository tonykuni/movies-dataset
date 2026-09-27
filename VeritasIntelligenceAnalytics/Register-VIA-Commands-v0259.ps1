# Register-VIA-Commands-v0259.ps1 — 先對齊子系統，通過才執行。座位有變才推 GitHub。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0258.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vcgc {
    $env:VIA_FROM_VCGC = "YES"
    if (-not $env:VIA_VCGC_PUSH) { $env:VIA_VCGC_PUSH = "YES" }
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
    if (-not $eng) { Write-Host "  [via-vcgc] FAIL:console tail missing" -ForegroundColor Red; return }
    $a = @($args | ForEach-Object { if ($_ -eq "-SelfTest") { "--selftest" } elseif ($_ -eq "-Publish") { "--publish" } elseif ($_ -eq "-Apply") { "--apply" } else { $_ } })
    if (-not $a) { $a = @("status") }
    Invoke-VIAPython -Family "vrn" $eng @a
    $code = $LASTEXITCODE
    $page = Join-Path $PSScriptRoot "VIA_Reports/vcgc/VIA_Flow_Matrix_v0100.html"
    if (Test-Path -LiteralPath $page) {
        Write-Host ("  [矩陣] " + $page) -ForegroundColor DarkCyan
        if ($env:OS -eq "Windows_NT") { Start-Process -FilePath $page }
    }
    $global:LASTEXITCODE = $code
}
Set-Alias -Name 中央控管 -Value via-vcgc -Scope Global -Force
