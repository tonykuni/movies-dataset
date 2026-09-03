#requires -Version 7.0
# Deploy-Batch347.ps1 — 批347 一鍵部署(只 Copy 新版;零覆寫舊版;零 push)
param([string]$Src = (Split-Path -Parent $MyInvocation.MyCommand.Path),
      [string]$Root = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics')
$ErrorActionPreference = 'Stop'
$reg = Join-Path $Root 'supportive modules\registry'; $ui = Join-Path $Root 'supportive modules\ui_support'
Copy-Item (Join-Path $Src 'registry\*')   $reg -Force
Copy-Item (Join-Path $Src 'ui_support\*') $ui  -Force
Copy-Item (Join-Path $Src 'root\*.cmd')   $Root -Force
Copy-Item (Join-Path $Src 'root\*.py')    (Join-Path $env:USERPROFILE 'Downloads') -Force
Copy-Item (Join-Path $Src 'root\*.ps1')   (Join-Path $env:USERPROFILE 'Downloads') -Force
Write-Host '--- selftests (latest of each) ---' -ForegroundColor Cyan
foreach ($stem in 'CGC_MDL095_DeckServer','CGC_MDL116_UnifiedShell','CGC_MDL122_IntakeRoster','CGC_MDL123_SixStreams','CGC_MDL124_SystemCharter','CGC_MDL125_LifecycleRACI','CGC_MDL126_UIBridge') {
  $f = Get-ChildItem $reg -Filter "${stem}_v0*.py" | Sort-Object Name | Select-Object -Last 1
  $t = & 'C:\Python313\python.exe' $f.FullName --selftest 2>&1 | Select-String '\[計\]' | Select-Object -Last 1
  Write-Host ("{0,-42} {1}" -f $f.Name, $t)
}
Write-Host "`nnext: via-loop  (貼 digest)" -ForegroundColor Yellow
