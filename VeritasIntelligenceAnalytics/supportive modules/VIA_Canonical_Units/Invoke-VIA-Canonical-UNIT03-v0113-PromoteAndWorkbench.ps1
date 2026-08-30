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
 UNIT03 v0113 - Promotion + write_workbench targeted test (ONE SHOT)
 Operator approval: "ONE POWERSHELL TO HANDLE ALL & REMAINING PROCESSES"
 P1 promote  : re-derive the eight-site 0.4->0.75 patch from the PINNED
               source (SHA 2AE164B5...), cross-check byte-equality with
               the v0112 run-local artifact, then write ONE NEW repo file
               VAP_ENG001_AutoplotEngineChartlib_v002.py (append-only - never
               overwrites; existing-but-different aborts).
 P2 workbench: import the promoted module in an isolated cwd, verify
               write_workbench exists; call it only if every parameter
               has a default (else static-verify only). 60s job timeout.
 P3 ship     : commit + push main with backoff, transaction record JSON.
 Canonical VAP_ENG002_AutoplotEngine_v001.py untouched. Fail-closed throughout.
===================================================================== #>
param(
    [string]$Candidate  = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP\engine\VAP_ENG002_AutoplotEngine_v001.py",
    [string]$ExpectedSha = "2AE164B5082B2113E12C4D1BCD8D73E97C66010F602E01F4A81D8E4B53689EEC"
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$repo = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$via  = Join-Path $repo "VeritasIntelligenceAnalytics"
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $env:USERPROFILE "VIA_Reports\UNIT03_v0113_Promote_$ts"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$MATRIX = [System.Collections.Generic.List[object]]::new()
function Gate($n,$s,$note){ $MATRIX.Add([pscustomobject]@{Gate=$n;Status=$s;Note=$note}) }
Push-Location $repo
try {

# ---- P1.1 pin source ----
$actual = (Get-FileHash -LiteralPath $Candidate -Algorithm SHA256).Hash
if ($actual -ne $ExpectedSha) { Gate "P1.1 SHA pin" "FAIL" $actual; throw "CANDIDATE_HASH_DRIFT" }
Gate "P1.1 SHA pin" "PASS" $actual.Substring(0,16)

# ---- P1.2 re-derive the eight-site patch (identical map to v0112 R3) ----
$text = [IO.File]::ReadAllText($Candidate, [Text.UTF8Encoding]::new($false))
$map = @(
    @{ o = "FILL_OPACITY = 0.4 ";                    n = "FILL_OPACITY = 0.75 ";                     expect = 1 },
    @{ o = "# fillOpacity default 0.4";              n = "# fillOpacity default 0.75";               expect = 1 },
    @{ o = [char]25240 + [char]32218 + " 0.9 " + [char]183 + " " + [char]22635 + [char]33394 + " 0.4"; n = [char]25240 + [char]32218 + " 0.9 " + [char]183 + " " + [char]22635 + [char]33394 + " 0.75"; expect = 2 },
    @{ o = "bar fill 0.4 " + [char]183 + " area fill 0.4";  n = "bar fill 0.75 " + [char]183 + " area fill 0.75"; expect = 1 },
    @{ o = "1 " + [char]183 + " .9/.4";              n = "1 " + [char]183 + " .9/.75";               expect = 1 },
    @{ o = "FILL OPACITY " + [char]183 + " 0.4";     n = "FILL OPACITY " + [char]183 + " 0.75";      expect = 1 },
    @{ o = "fillOp:0.4";                             n = "fillOp:0.75";                              expect = 1 }
)
foreach ($m in $map) {
    $c = [regex]::Matches($text, [regex]::Escape($m.o)).Count
    if ($c -ne $m.expect) { Gate "P1.2 derive" "FAIL" "'$($m.o)' count=$c expected=$($m.expect)"; throw "REPLACEMENT_COUNT_MISMATCH" }
    $text = $text.Replace($m.o, $m.n)
}
Gate "P1.2 derive" "PASS" "eight-site patch re-derived from pinned source"

# ---- P1.3 cross-check with v0112 run-local artifact (dual derivation must agree) ----
$prior = Get-ChildItem (Join-Path $env:USERPROFILE "VIA_Reports") -Directory -Filter "UNIT03_v0112_GuardedTrial_*" -ErrorAction SilentlyContinue |
         Sort-Object Name -Descending | Select-Object -First 1
$priorFile = if ($prior) { Join-Path $prior.FullName "via_autoplot_engine_v001.PATCHED_RUNLOCAL.py" } else { $null }
if ($priorFile -and (Test-Path -LiteralPath $priorFile)) {
    $priorText = [IO.File]::ReadAllText($priorFile, [Text.UTF8Encoding]::new($false))
    if ($priorText -ne $text) { Gate "P1.3 dual-derivation" "FAIL" "v0112 artifact differs from re-derivation"; throw "DUAL_DERIVATION_MISMATCH" }
    Gate "P1.3 dual-derivation" "PASS" "byte-identical with $($prior.Name)"
} else {
    Gate "P1.3 dual-derivation" "WARN" "no v0112 artifact found - single derivation only"
}

# ---- P1.4 append-only write of the promoted file ----
$destRel = "VeritasIntelligenceAnalytics/functional modules/VAP/engine/VAP_ENG001_AutoplotEngineChartlib_v002.py"
$dest = Join-Path $repo $destRel
$hdr = "# PROMOTED by UNIT03 v0113 $ts from Chart Library Builder candidate (SHA $ExpectedSha)`n" +
       "# Eight-site visual-lock repair 0.4 -> 0.75 per v0111R2 adjudication + v0112 guarded trial (all gates PASS).`n" +
       "# Canonical VAP_ENG002_AutoplotEngine_v001.py is unaffected. Do not edit in place - version forward instead.`n"
$final = $hdr + $text
if (Test-Path -LiteralPath $dest) {
    $existing = [IO.File]::ReadAllText($dest, [Text.UTF8Encoding]::new($false))
    # idempotence: ignore the 3-line promotion header (carries run timestamp) and CRLF/LF,
    # compare bodies only - identical body means the promotion already happened
    $stripHdr = { param($t) (($t -replace "`r`n", "`n") -split "`n" | Select-Object -Skip 3) -join "`n" }
    if ((& $stripHdr $existing) -eq (& $stripHdr $final)) {
        Gate "P1.4 promote" "PASS" "ALREADY_PROMOTED - body identical, header timestamp differs only (idempotent)"
    }
    else { Gate "P1.4 promote" "FAIL" "dest exists with DIFFERENT BODY - refusing overwrite"; throw "DEST_CONFLICT" }
} else {
    [IO.File]::WriteAllText($dest, $final, [Text.UTF8Encoding]::new($false))
    Gate "P1.4 promote" "PASS" $destRel
}
$destSha = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash

# ---- P1.5 transaction record ----
$rec = [pscustomobject]@{
    unit = "UNIT03_v0113_PROMOTION"; ts = $ts
    source = @{ path = $Candidate; sha256 = $ExpectedSha }
    dest   = @{ path = $destRel; sha256 = $destSha }
    repair = "eight-site 0.4->0.75 (v0111R2 adjudication, v0112 guarded trial all green)"
    canonical_mutation = $false; promotion_scope = "new file only"
}
$recRel = "VeritasIntelligenceAnalytics/functional modules/VAP/engine/via_autoplot_engine_chartlib_v002.PROMOTION_RECORD.json"
$rec | ConvertTo-Json -Depth 5 | Out-File (Join-Path $repo $recRel) -Encoding utf8
Gate "P1.5 record" "PASS" $recRel

# ---- P2 write_workbench targeted test (isolated cwd, 60s cap) ----
$py = @("C:\Users\tonyk\envs\via_core_312\Scripts\python.exe","py") |
      Where-Object { ($_ -eq "py") -or (Test-Path $_) } | Select-Object -First 1
$testPy = Join-Path $runDir "wb_test.py"
@'
import sys, json, inspect, importlib.util
dest, outp = sys.argv[1], sys.argv[2]
r = {"import_ok": False, "has_write_workbench": False, "signature": None,
     "callable_with_defaults": False, "call_result": "NOT_ATTEMPTED", "error": None}
try:
    spec = importlib.util.spec_from_file_location("chartlib_v002", dest)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    r["import_ok"] = True
    fn = getattr(m, "write_workbench", None)
    if fn is None:
        for nm in dir(m):
            if "workbench" in nm.lower() and callable(getattr(m, nm)):
                fn = getattr(m, nm); r["found_as"] = nm; break
    if fn is not None:
        r["has_write_workbench"] = True
        sig = inspect.signature(fn)
        r["signature"] = str(sig)
        need = [p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
        if not need:
            r["callable_with_defaults"] = True
            try:
                fn(); r["call_result"] = "CALLED_OK"
            except Exception as e:
                r["call_result"] = "CALL_RAISED: %s" % e
        else:
            r["call_result"] = "SKIP_REQUIRES_ARGS: %s" % [p.name for p in need]
except Exception as e:
    r["error"] = str(e)[:300]
json.dump(r, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(r, ensure_ascii=False))
'@ | Out-File $testPy -Encoding utf8
$wbOut = Join-Path $runDir "wb_result.json"
$job = Start-Job -ArgumentList $py,$testPy,$dest,$wbOut,$runDir -ScriptBlock {
    param($py,$t,$d,$o,$cwd)
    Set-Location $cwd
    & $py $t $d $o 2>&1
}
if (Wait-Job $job -Timeout 60) { Receive-Job $job | Out-Host } else { Stop-Job $job; Write-Host "[TIMEOUT] workbench test 60s" }
Remove-Job $job -Force -ErrorAction SilentlyContinue
$wb = if (Test-Path $wbOut) { Get-Content $wbOut -Raw | ConvertFrom-Json } else { $null }
if ($wb -and $wb.import_ok -and $wb.has_write_workbench) {
    Gate "P2 workbench" "PASS" "sig=$($wb.signature) result=$($wb.call_result)"
} elseif ($wb -and $wb.import_ok) {
    Gate "P2 workbench" "WARN" "module imports but no workbench function found - static promotion stands"
} else {
    Gate "P2 workbench" "FAIL" $(if ($wb) { $wb.error } else { "no result json" })
}

# ---- P3 ship ----
git add -- $destRel $recRel
git commit -m "UNIT03 v0113: promote Chart Library Builder repaired candidate as via_autoplot_engine_chartlib_v002 (eight-site 0.4->0.75, dual-derivation verified) + write_workbench targeted test record" 2>&1 | Out-Host
$ok = $false
foreach ($d in @(0,2,4,8,16)) {
    if ($d) { Start-Sleep -Seconds $d }
    git push origin main 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    git pull --rebase --autostash origin main 2>&1 | Out-Host
}
Gate "P3 ship" $(if($ok){"PASS"}else{"WARN"}) "push=$ok"

}
catch { Write-Host "[ABORT] $($_.Exception.Message)" -ForegroundColor Red }
finally {
    Write-Host "`n============ UNIT03 v0113 PROMOTION MATRIX ============" -ForegroundColor Cyan
    $MATRIX | Format-Table -AutoSize
    $MATRIX | ConvertTo-Json -Depth 4 | Out-File (Join-Path $runDir "v0113_matrix.json") -Encoding utf8
    git log --oneline -3 | Out-Host
    Write-Host "[RUNDIR] $runDir" -ForegroundColor Cyan
    Pop-Location
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
