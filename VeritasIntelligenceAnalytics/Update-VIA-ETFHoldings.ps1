# Update the active Taiwan ETF master list, then today's holdings.
# via-etfuniv and via-etfhist already choose the newest engine.
# This file does not set consent. Those commands fill an unset gate only.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$reg = Get-ChildItem -LiteralPath $root -Filter 'Register-VIA-Commands-v*.ps1' |
    Sort-Object Name | Select-Object -Last 1
if (-not $reg) { throw "Register-VIA-Commands not found under $root" }
. $reg.FullName
via-etfuniv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
via-etfhist
exit $LASTEXITCODE
