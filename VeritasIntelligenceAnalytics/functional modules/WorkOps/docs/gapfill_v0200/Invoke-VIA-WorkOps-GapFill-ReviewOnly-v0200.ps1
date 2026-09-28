#requires -Version 7.0
[CmdletBinding()]
param(
  [string]$WorkOpsRoot = "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\functional modules\WorkOps",
  [switch]$StageToOut
)
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

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Candidate=Join-Path $Here "engines"
$TargetEng=Join-Path $WorkOpsRoot "engines"
$Files=@(
"workops_gapfill_common.py",
"workops_milestone_manager.py",
"workops_closure_intelligence.py",
"workops_lesson_learned.py",
"workops_unified_search.py",
"workops_retention_manager.py",
"workops_onboarding.py",
"workops_timeline_dependency.py"
)
Write-Host "================================================================================================" -ForegroundColor DarkCyan
Write-Host "def VERITAS WORKOPS · PANORAMIC GAPFILL · REVIEW ONLY · v0200" -ForegroundColor Cyan
Write-Host "================================================================================================" -ForegroundColor DarkCyan
$rows=@()
foreach($f in $Files){
  $src=Join-Path $Candidate $f
  $dst=Join-Path $TargetEng $f
  $state=if(Test-Path $dst){"EXISTS"}else{"MISSING"}
  $sha=(Get-FileHash $src -Algorithm SHA256).Hash
  $rows += [pscustomobject]@{File=$f;TargetState=$state;CandidateSHA256=$sha}
}
$rows | Format-Table -AutoSize
if($StageToOut){
  $stage=Join-Path $WorkOpsRoot ("out\_gapfill_staging\RUN_"+(Get-Date -Format "yyyyMMdd_HHmmss"))
  New-Item -ItemType Directory -Force -Path $stage | Out-Null
  foreach($f in $Files){Copy-Item (Join-Path $Candidate $f) (Join-Path $stage $f)}
  Copy-Item (Join-Path $Here "config\*.json") $stage
  Write-Host "def STAGED ONLY : $stage" -ForegroundColor Yellow
  Write-Host "def Canonical mutation : 0" -ForegroundColor Green
}
Write-Host "def Gate : REVIEW_REQUIRED" -ForegroundColor Yellow
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
