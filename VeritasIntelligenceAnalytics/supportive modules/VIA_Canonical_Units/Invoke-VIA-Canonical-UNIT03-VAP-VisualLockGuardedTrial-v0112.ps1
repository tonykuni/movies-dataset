#requires -Version 7.0
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
<# =====================================================================
 UNIT03 v0112 - VAP Visual-Lock Guarded Trial (multi-line, hash-locked)
 Adjudication basis: v0111R2 run P0_..._v0111_20260804_154502 found SEVEN
 direct 0.4 locks in the Chart Library Builder candidate - a spec-level
 divergence, not a single-line defect. Approved repair: 0.4 -> 0.75 at all
 seven sites, applied ONLY to a run-local copy.
 Guarantees: source copy untouched - canonical untouched - no promotion -
 file-level SHA256 gate - per-replacement exact-count gate (fail-closed).
===================================================================== #>
param(
    [string]$Candidate = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP\engine\VAP_ENG002_AutoplotEngine_v001.py",
    [string]$ExpectedSha = "2AE164B5082B2113E12C4D1BCD8D73E97C66010F602E01F4A81D8E4B53689EEC"
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $env:USERPROFILE "VIA_Reports\UNIT03_v0112_GuardedTrial_$ts"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$MATRIX = [System.Collections.Generic.List[object]]::new()
function Gate($n,$s,$note){ $MATRIX.Add([pscustomobject]@{Gate=$n;Status=$s;Note=$note}) }
try {

# GATE 1 - source authority (file-level SHA256 pin)
$actual = (Get-FileHash -LiteralPath $Candidate -Algorithm SHA256).Hash
if ($actual -ne $ExpectedSha) {
    Gate "G1 SHA pin" "FAIL" "candidate drifted: $actual"
    throw "CANDIDATE_HASH_DRIFT - aborting before any action"
}
Gate "G1 SHA pin" "PASS" $actual.Substring(0,16)

# GATE 2 - run-local copy (source is never written)
$patched = Join-Path $runDir "via_autoplot_engine_v001.PATCHED_RUNLOCAL.py"
Copy-Item -LiteralPath $Candidate -Destination $patched -Force
$text = [IO.File]::ReadAllText($patched, [Text.UTF8Encoding]::new($false))
Gate "G2 run-local copy" "PASS" $patched

# GATE 3 - seven-site hash-locked replacement set, exact-count enforced
$map = @(
    @{ o = "FILL_OPACITY = 0.4 ";                    n = "FILL_OPACITY = 0.75 ";                     expect = 1 },  # L55 constant
    @{ o = "# fillOpacity default 0.4";              n = "# fillOpacity default 0.75";               expect = 1 },  # L55 trailing comment
    @{ o = [char]25240 + [char]32218 + " 0.9 " + [char]183 + " " + [char]22635 + [char]33394 + " 0.4"; n = [char]25240 + [char]32218 + " 0.9 " + [char]183 + " " + [char]22635 + [char]33394 + " 0.75"; expect = 2 },  # L8 docstring + L657 footer (折線 0.9 · 填色 0.4)
    @{ o = "bar fill 0.4 " + [char]183 + " area fill 0.4";  n = "bar fill 0.75 " + [char]183 + " area fill 0.75"; expect = 1 },  # L303
    @{ o = "1 " + [char]183 + " .9/.4";              n = "1 " + [char]183 + " .9/.75";               expect = 1 },  # L573 badge
    @{ o = "FILL OPACITY " + [char]183 + " 0.4";     n = "FILL OPACITY " + [char]183 + " 0.75";      expect = 1 },  # L636 badge
    @{ o = "fillOp:0.4";                             n = "fillOp:0.75";                              expect = 1 }   # L663 JS LOCK
)
$allOk = $true
foreach ($m in $map) {
    $count = [regex]::Matches($text, [regex]::Escape($m.o)).Count
    if ($count -ne $m.expect) {
        $allOk = $false
        Gate "G3 replace" "FAIL" "'$($m.o)' count=$count expected=$($m.expect) - fail-closed, no write"
    } else {
        $text = $text.Replace($m.o, $m.n)
        Gate "G3 replace" "PASS" "'$($m.o)' x$count -> 0.75"
    }
}
if (-not $allOk) { throw "REPLACEMENT_COUNT_MISMATCH - patched candidate NOT written" }
[IO.File]::WriteAllText($patched, $text, [Text.UTF8Encoding]::new($false))
Gate "G3 write" "PASS" "eight-site patch applied to run-local copy only"

# GATE 4 - trial 1: interpreter syntax proof (py_compile)
$py = @("C:\Users\tonyk\envs\via_core_312\Scripts\python.exe","py") |
      Where-Object { ($_ -eq "py") -or (Test-Path $_) } | Select-Object -First 1
& $py -m py_compile $patched 2>&1 | Out-Host
Gate "G4 trial1 py_compile" $(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" }) "exit=$LASTEXITCODE"

# GATE 5 - trial 2: static lock rescan (zero remaining direct 0.4 locks)
$lines = [IO.File]::ReadAllLines($patched, [Text.UTF8Encoding]::new($false))
$bad = @(); $good = 0
for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i]
    if ($l -match 'FILL_OPACITY = 0\.4|fillOp:0\.4|OPACITY [^0-9]* 0\.4|\.9/\.4') { $bad += "L$($i+1): $l" }
    if ($l -match 'FILL_OPACITY = 0\.75|fillOp:0\.75|0\.75') { $good++ }
}
if ($bad.Count) { $bad | ForEach-Object { Write-Host "[RESIDUAL] $_" -ForegroundColor Red } }
Gate "G5 trial2 rescan" $(if ($bad.Count -eq 0) { "PASS" } else { "FAIL" }) "residual direct 0.4 locks=$($bad.Count), 0.75 sites=$good"

# GATE 6 - sequence gate: no promotion, write_workbench still pending
Gate "G6 sequence" "HOLD" "NO promotion - source untouched - write_workbench targeted test remains next stage"

}
catch {
    Write-Host "[ABORT] $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Write-Host "`n============ UNIT03 v0112 GUARDED TRIAL MATRIX ============" -ForegroundColor Cyan
    $MATRIX | Format-Table -AutoSize
    $MATRIX | ConvertTo-Json -Depth 4 | Out-File (Join-Path $runDir "v0112_matrix.json") -Encoding utf8
    Write-Host "[RUNDIR] $runDir" -ForegroundColor Cyan
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
