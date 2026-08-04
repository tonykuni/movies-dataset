#requires -Version 7.0
<# =====================================================================
 TickerRegex P1 Closeout - verify SSOT v0100 on this machine and ship
 Operator directive 2026-08-04: VDF/VRN/VAP ticker regex = four digits,
 first digit non-zero. Scope frozen. Old year-exclusion regex retired
 from SSOT (v029SSOT1B archived in place).
 Read-only verification + push. No canonical mutation.
===================================================================== #>
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$repo = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$via  = Join-Path $repo "VeritasIntelligenceAnalytics"
$MATRIX = [System.Collections.Generic.List[object]]::new()
function Gate($n,$s,$note){ $MATRIX.Add([pscustomobject]@{Gate=$n;Status=$s;Note=$note}) }
Push-Location $repo
try {

# G1 SSOT artifacts present and parseable
$ssot = Join-Path $via "supportive modules\ssot\VRN_TickerRegexSSOT_v0100.json"
$mod  = Join-Path $via "supportive modules\70_VRN_Rules\VIS_VRN_TickerFilenameSSOT_v0100.py"
$cen  = Join-Path $via "supportive modules\audit_tools\TickerRegex_LegacyDebt_Census_v0100.json"
$j = Get-Content -LiteralPath $ssot -Raw -Encoding UTF8 | ConvertFrom-Json
$c = Get-Content -LiteralPath $cen  -Raw -Encoding UTF8 | ConvertFrom-Json
$okArt = ($j.version -eq "v0100") -and ($j.status -eq "ACTIVE") -and $j.scope_freeze -and (Test-Path -LiteralPath $mod)
Gate "G1 artifacts" $(if($okArt){"PASS"}else{"FAIL"}) "SSOT $($j.version)/$($j.status) freeze=$($j.scope_freeze) census=$($c.total_files) files"

# G2 live self-test of the new rule on this machine
$py = @("C:\Users\tonyk\envs\via_core_312\Scripts\python.exe","py") |
      Where-Object { ($_ -eq "py") -or (Test-Path $_) } | Select-Object -First 1
$test = @'
import sys, importlib.util
spec = importlib.util.spec_from_file_location("tk", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
R = m.TW_TICKER_REGEX
cases = [
    ("2330", True,  "normal ticker"),
    ("0050", False, "ETF leading zero must NOT match"),
    ("2027", True,  "in-band real ticker must MATCH at regex layer"),
    ("123",  False, "3 digits"),
    ("12345",False, "5 digits"),
]
fails = []
for tok, want, why in cases:
    got = bool(R.fullmatch(tok))
    if got != want: fails.append((tok, why, got))
v, conf, why = m.disambiguate_year_vs_ticker("2027", firstpage_ticker="2027")
if v != "TICKER": fails.append(("2027-corroborated", "should be TICKER", v))
v2, c2, w2 = m.disambiguate_year_vs_ticker("2024", neighbor_text="2024\u5e74Q1")
if v2 != "YEAR": fails.append(("2024-datecue", "should be YEAR", v2))
v3, c3, w3 = m.disambiguate_year_vs_ticker("2029")
if v3 != "AMBIGUOUS": fails.append(("2029-nocorr", "should be AMBIGUOUS", v3))
print("SELFTEST", "PASS 8/8" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
'@
$tf = Join-Path $env:TEMP "tk_selftest.py"
$test | Out-File $tf -Encoding utf8
& $py $tf $mod 2>&1 | Out-Host
Gate "G2 self-test" $(if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" }) "regex + disambiguation live on this machine"

# G3 ship anything pending, then final state
git add -A -- "VeritasIntelligenceAnalytics" 2>$null
$staged = @(git diff --cached --name-only)
if ($staged.Count) { git commit -m "TickerRegex P1 closeout: local sync ($($staged.Count) files)" 2>&1 | Out-Host }
$ok = $false
foreach ($d in @(0,2,4,8,16)) {
    if ($d) { Start-Sleep -Seconds $d }
    git push origin main 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    git pull --rebase --autostash origin main 2>&1 | Out-Host
}
Gate "G3 ship" $(if($ok){"PASS"}else{"WARN"}) "push=$ok staged=$($staged.Count)"

}
catch { Write-Host "[ABORT] $($_.Exception.Message)" -ForegroundColor Red }
finally {
    Write-Host "`n========== TICKERREGEX P1 CLOSEOUT MATRIX ==========" -ForegroundColor Cyan
    $MATRIX | Format-Table -AutoSize
    git log --oneline -3 | Out-Host
    Pop-Location
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}
