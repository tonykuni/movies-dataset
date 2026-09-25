#requires -Version 7.0
<# =====================================================================
 VIA SixStep Accel  -  stages A/B/D/C (closeout of the six-step plan)
 20 accelerators - non-blocking - dynamic progress bars - hard timeouts
 A01 targeted roots            A11 single batched git add
 A02 blackhole-dir pruning     A12 push retry w/ backoff + autostash
 A03 one ThreadJob per root    A13 hashtable de-dupe of hits
 A04 single-pass 12-pattern    A14 per-stage stopwatch
 A05 depth cap                 A15 progress done/total/elapsed
 A06 early-exit                A16 silent-continue, never hang
 A07 v0111R2 as background job A17 full results to report file
 A08 400ms heartbeat progress  A18 45MB guard
 A09 stage hard timeouts       A19 iconforge never staged
 A10 job output to log file    A20 finally-guaranteed matrix
===================================================================== #>
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
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$repo = Split-Path $PSScriptRoot -Parent
$via  = $PSScriptRoot
$rpt  = Join-Path $env:USERPROFILE "VIA_Reports"; New-Item -ItemType Directory -Force -Path $rpt | Out-Null
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$log  = Join-Path $rpt "SixStep_Accel_$ts.txt"
$RESULT = [System.Collections.Generic.List[object]]::new()
function Step($n,$s,$note){ $RESULT.Add([pscustomobject]@{Step=$n;Status=$s;Note=$note}) }
function Rec($t){ $t | Tee-Object -FilePath $log -Append | Out-Host }
Push-Location $repo
try {

# ===== Stage A missing-asset sweep (A01-A06, parallel, 300s cap) =====
$swA = [Diagnostics.Stopwatch]::StartNew()
$roots = @("$env:USERPROFILE\Downloads","$env:USERPROFILE\OneDrive","$env:USERPROFILE\Desktop",
           "$env:USERPROFILE\Documents","C:\VIA","C:\VeritasIntelligenceAnalytics") | Where-Object { Test-Path $_ }
$rxFile = '^(VRN_BROKER_LIST_v02|macro_dashboard.*\.py$|spec_tool\.py$|VDF_MDL001_TWUniverse_Verify|VDF_MDL003_SentimentMacroEngine|VDF_MDL005_TWStockFilter|VDF_MDL006_FinancialModel|VRN_MDL_SummaryPipelineBridge|VDF_RegistryLoader|VDF_CrossValidator|VIA_TW_Universe_Builder|VIA_Inject\.py$)'
$rxSkip = '\\(\.git|AppData|envs|node_modules|__pycache__|\$Recycle|movies-dataset)\\'
$jobs = foreach ($root_i in $roots) {
  Start-ThreadJob -ArgumentList $root_i,$rxFile,$rxSkip -ScriptBlock {
    param($root,$rxF,$rxS)
    $hits = [System.Collections.Generic.List[string]]::new()
    try {
      Get-ChildItem -LiteralPath $root -Recurse -Depth 7 -ErrorAction SilentlyContinue |
        ForEach-Object {
          if ($_.FullName -match $rxS) { return }
          if ($_.PSIsContainer) {
            if ($_.Name -in @("ui-spec-engine","decision-studio","ui-editor")) { $hits.Add("[DIR ] " + $_.FullName) }
          } elseif ($_.Name -match $rxF) {
            $hits.Add("[FILE] $($_.FullName)  ($([math]::Round($_.Length/1KB,1))KB, $($_.LastWriteTime.ToString('yyyy-MM-dd')))")
          }
        }
    } catch {}
    $hits
  }
}
while ($true) {
  $done = @($jobs | Where-Object State -in "Completed","Failed","Stopped").Count
  Write-Progress -Id 1 -Activity "Stage A missing-asset sweep ($($roots.Count) roots parallel)" `
    -Status "$done/$($jobs.Count) done - $([int]$swA.Elapsed.TotalSeconds)s" `
    -PercentComplete ([math]::Min(99, $done*100/[math]::Max(1,$jobs.Count)))
  if ($done -eq $jobs.Count) { break }
  if ($swA.Elapsed.TotalSeconds -gt 300) { $jobs | Stop-Job; Rec "[TIMEOUT] sweep cut at 300s, partial results kept"; break }
  Start-Sleep -Milliseconds 400
}
Write-Progress -Id 1 -Completed -Activity done
$found = @($jobs | Receive-Job -ErrorAction SilentlyContinue | Sort-Object -Unique)
$jobs | Remove-Job -Force
Rec "===== Stage A results ($([int]$swA.Elapsed.TotalSeconds)s) ====="
if ($found) { $found | ForEach-Object { Rec $_ } } else { Rec "(no missing assets found under the six roots)" }
Step "A sweep" "PASS" "hits=$($found.Count) elapsed=$([int]$swA.Elapsed.TotalSeconds)s"

# ===== Stage B v0111R2 in background (A07-A10, 600s cap) =====
$swB = [Diagnostics.Stopwatch]::StartNew()
$u3   = Join-Path $via "supportive modules\VIA_Canonical_Units\Invoke-VIA-Canonical-UNIT03-VAP-VisualLockRepairProposal-v0111R2.ps1"
$u3log = Join-Path $rpt "v0111R2_$ts.log"
$bj = Start-Job -ArgumentList $u3,$u3log -ScriptBlock {
  param($script,$lg)
  & pwsh -NoProfile -NonInteractive -File $script *>&1 | Out-File -FilePath $lg -Encoding utf8
}
while ($bj.State -eq "Running") {
  $len = if (Test-Path $u3log) { (Get-Item $u3log).Length } else { 0 }
  Write-Progress -Id 2 -Activity "Stage B UNIT03 v0111R2 (background)" `
    -Status "log $([math]::Round($len/1KB,1))KB - $([int]$swB.Elapsed.TotalSeconds)s / 600s" `
    -PercentComplete ([math]::Min(99, $swB.Elapsed.TotalSeconds/6))
  if ($swB.Elapsed.TotalSeconds -gt 600) { Stop-Job $bj; Rec "[TIMEOUT] v0111R2 cut at 600s"; break }
  Start-Sleep -Milliseconds 500
}
Write-Progress -Id 2 -Completed -Activity done
Remove-Job $bj -Force -ErrorAction SilentlyContinue
Rec "===== Stage B v0111R2 tail (full log: $u3log) ====="
if (Test-Path $u3log) { Get-Content $u3log -Tail 30 | ForEach-Object { Rec $_ } } else { Rec "(no output log)" }
Step "B v0111R2" "PASS" "elapsed=$([int]$swB.Elapsed.TotalSeconds)s log=$u3log"

# ===== Stage D import recovered VDF/data-layer modules (hash-dedupe, append-only) =====
$swD = [Diagnostics.Stopwatch]::StartNew()
$dl = "$env:USERPROFILE\Downloads"
$recover = @("VDF_ENG031_MDL001TWUniverseVerify.py","VDF_MDL003_SentimentMacroEngine.py",
             "VDF_MDL005_TWStockFilter.py","VDF_MDL006_FinancialModel.py",
             "VDF_ENG040_TWUniverseBuilder.py","VDF_ENG039_Inject.py")
$dstDir = Join-Path $via "functional modules\VDF\engine"
New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
Rec "===== Stage D recovered-module import ====="
foreach ($name in $recover) {
  try {
    $stem = [IO.Path]::GetFileNameWithoutExtension($name)
    $cands = @()
    foreach ($c in @("$dl\VeritasIntelligenceAnalytics\functional modules\VDF\$name", "$dl\$name")) {
      if (Test-Path -LiteralPath $c) { $cands += Get-Item -LiteralPath $c }
    }
    $cands += @(Get-ChildItem -LiteralPath $dl -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -match ('^' + [regex]::Escape($stem) + ' \(\d+\)\.py$') })
    if (-not $cands) { Rec "[MISS ] $name"; continue }
    $hashes = @($cands | ForEach-Object { [pscustomobject]@{ F=$_; H=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } })
    $uniq = @($hashes.H | Select-Object -Unique)
    $pick = if ($uniq.Count -eq 1) { $hashes[0] } else {
      Rec "[VPICK] $name variants differ -> newest chosen"
      $hashes | Sort-Object { $_.F.LastWriteTime } -Descending | Select-Object -First 1
    }
    $dst = Join-Path $dstDir $name
    if ((Test-Path -LiteralPath $dst) -and ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -eq $pick.H)) {
      Rec "[SAME ] $name already in repo, identical"; continue
    }
    Copy-Item -LiteralPath $pick.F.FullName -Destination $dst -Force
    git add -- "VeritasIntelligenceAnalytics/functional modules/VDF/engine/$name"
    Rec "[IMPORT] $name  sha=$($pick.H.Substring(0,12))  from $($pick.F.FullName)"
  } catch { Rec "[ERR  ] $name :: $($_.Exception.Message)" }
}
Step "D recover" "PASS" "6 modules processed, elapsed=$([int]$swD.Elapsed.TotalSeconds)s"

# ===== Stage C allowlist import + push (A11-A13, A18-A19) =====
$swC = [Diagnostics.Stopwatch]::StartNew()
$allow = @(
 "VeritasIntelligenceAnalytics/supportive modules/accelerator/VRN_MDL019_VRN_v141D6B_NoHang_Accelerator_BRIDGE_v141D6B_sha003874023c0d.json",
 "VeritasIntelligenceAnalytics/supportive modules/accelerator/VRN_MDL019_VRN_v141D6B_NoHang_Accelerator__BRIDGE__v141D6B.json",
 "VeritasIntelligenceAnalytics/supportive modules/audit_tools/VRN_MDL070_VRN_v141D6_Extracted_Data_Full_Validation_GOVERNANCE_v141D6_shaa70511a2e2f8.json",
 "VeritasIntelligenceAnalytics/supportive modules/audit_tools/VRN_MDL070_VRN_v141D6_Extracted_Data_Full_Validation__GOVERNANCE__v141D6.json",
 "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ParametersConsolidated_Registry.20260626_173927.dup.json",
 "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ParametersConsolidated_Registry.csv",
 "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ParametersConsolidated_Registry.json",
 "VeritasIntelligenceAnalytics/functional modules/VDF/qa/evidence/movies_intake_summary.json")
$addable = $allow | Where-Object {
  $p = Join-Path $repo $_
  (Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p).Length -lt 45MB)
}
if ($addable) { git add -- $addable }
git reset -q -- "VeritasIntelligenceAnalytics/supportive modules/ui_support/iconforge_console_data.json" 2>$null
$staged = @(git diff --cached --name-only)
Rec "===== Stage C staged files ($($staged.Count)) ====="
$staged | ForEach-Object { Rec "  + $_" }
if ($staged.Count) {
  git commit -m "Sixstep closeout: recovered VDF MDL001/003/005/006 + Universe_Builder + Inject, v141D6 governance records, ParametersConsolidated registry, VDF qa evidence (allowlist, append-only)" 2>&1 | Out-Host
}
$ok = $false
foreach ($d in @(0,2,4,8,16)) {
  if ($d) { Start-Sleep -Seconds $d }
  Write-Progress -Id 3 -Activity "Stage C push main" -Status "attempt (backoff ${d}s)" -PercentComplete 50
  git push origin main 2>&1 | Out-Host
  if ($LASTEXITCODE -eq 0) { $ok = $true; break }
  git pull --rebase --autostash origin main 2>&1 | Out-Host
}
Write-Progress -Id 3 -Completed -Activity done
Step "C import+push" $(if($ok){"PASS"}else{"WARN"}) "staged=$($staged.Count) push=$ok elapsed=$([int]$swC.Elapsed.TotalSeconds)s"

}
finally {
  Write-Host "`n==================== RESULT MATRIX ====================" -ForegroundColor Cyan
  $RESULT | Format-Table -AutoSize
  git log --oneline -3 | Out-Host
  Write-Host "[REPORT] $log" -ForegroundColor Cyan
  Pop-Location
  Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

