#Requires -Version 5.1
# 批600: vrn_unified Spec verb=--selftest + EngineBus v0128 (NEED_INPUT→ABSENT)
param(
  [string]$ViaRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
  [string]$PatchDir = ''
)
$ErrorActionPreference = 'Stop'
if (-not $PatchDir) { $PatchDir = $PSScriptRoot }
$reg = Join-Path $ViaRoot 'supportive modules\registry'
$specPath = Join-Path $reg 'VIA_InputConsole_Spec_v0100.json'
if (-not (Test-Path -LiteralPath $specPath)) { throw "Spec missing: $specPath" }

$raw = [IO.File]::ReadAllText($specPath)
$bak = $specPath + '.bak_b600_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
[IO.File]::Copy($specPath, $bak, $true)
$rx = [regex]'(?s)("id"\s*:\s*"vrn_unified".{0,600}?"verb"\s*:\s*)\[\s*\]'
if ($rx.IsMatch($raw)) {
  [IO.File]::WriteAllText($specPath, $rx.Replace($raw, '$1["--selftest"]', 1))
  Write-Host "Spec: verb [] -> [--selftest] (bak=$bak)"
} elseif ($raw -match '(?s)"id"\s*:\s*"vrn_unified".{0,600}?"verb"\s*:\s*\[\s*"--selftest"\s*\]') {
  Write-Host 'Spec: verb already [--selftest] — skip'
} else {
  Write-Warning 'Spec: could not locate empty verb for vrn_unified — inspect manually'
}

$v127 = Join-Path $reg 'CGC_MDL148_EngineBus_v0127.py'
$v128 = Join-Path $reg 'CGC_MDL148_EngineBus_v0128.py'
$diff = Join-Path $PatchDir 'CGC_MDL148_EngineBus_v0127_to_v0128.diff'
$busSrc = Join-Path $PatchDir 'CGC_MDL148_EngineBus_v0128.py'
$pyApp = Join-Path $PatchDir '_apply_bus_diff.py'
if (Test-Path -LiteralPath $busSrc) {
  Copy-Item -LiteralPath $busSrc -Destination $v128 -Force
  Write-Host "Bus: copied v0128 -> $v128"
} elseif ((Test-Path -LiteralPath $v127) -and (Test-Path -LiteralPath $diff) -and (Test-Path -LiteralPath $pyApp)) {
  python $pyApp $v127 $diff $v128
  if ($LASTEXITCODE -ne 0) { throw "diff apply failed" }
  Write-Host "Bus: applied diff -> $v128"
} else {
  Write-Warning "Bus: need v0127+diff+_apply_bus_diff.py or full v0128.py in PatchDir=$PatchDir"
}

Write-Host @"

Next (VIA sole entry):
  Set-Location '$ViaRoot'
  . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
  via-bus matrix --ids vrn_unified --apply
  Get-ChildItem -LiteralPath 'C:\測試樣本報告' | Format-Table Name, Length, LastWriteTime
  via-vrnlogic --selftest
  via-vrnlogic status
  via-vrnval --dir 'C:\測試樣本報告'
  via-vrnuni -SelfTest
"@
