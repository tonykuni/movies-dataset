#requires -Version 7.0
<# =====================================================================
 VRN Batch AllInOne v0100 - run the whole incoming corpus, unattended
 20 accelerators - non-blocking - resumable - canonical untouched
 A01 pdf-only enumeration        A11 append-only results CSV
 A02 parallel pool (Throttle 3)  A12 per-broker tally
 A03 patch candidate ONCE        A13 per-file fail-closed, batch continues
 A04 per-file hard timeout 240s  A14 per-file + total stopwatch
 A05 overall progress + ETA      A15 pool cap = memory guard
 A06 per-file log (no flood)     A16 silent-continue everywhere
 A07 verdict from log markers    A17 report dir under VIA_Reports
 A08 [ALIAS] broker extraction   A18 docx listed as SKIP_UNSUPPORTED
 A09 filename ticker (v0100)     A19 final matrix + counts
 A10 resume: skip prior SUCCESS  A20 finally-guaranteed summary
===================================================================== #>
param(
    [int]$Throttle = 3,
    [int]$TimeoutSec = 240,
    [switch]$Fresh
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$via   = $PSScriptRoot | Split-Path -Parent | Split-Path -Parent
$inbox = Join-Path $PSScriptRoot "input\incoming"
$cand  = Join-Path $via "supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
$rules = Join-Path $via "supportive modules\70_VRN_Rules"
$ts    = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $env:USERPROFILE "VIA_Reports\VRN_Batch_$ts"
$resultCsv = Join-Path $env:USERPROFILE "VIA_Reports\VRN_Batch_Results.csv"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$sw = [Diagnostics.Stopwatch]::StartNew()
try {

# A03 - patch the candidate ONCE into a run-local copy (canonical untouched)
$code = Get-Content -LiteralPath $cand -Raw -Encoding UTF8
$code = $code -replace '\$BrokerHelper\s*=\s*".*?"',
    ('$BrokerHelper = "' + (Join-Path $rules "VIS_VRN_BrokerAlias_Compatibility_v0222.py") + '"')
$code = $code -replace '\$FallbackHelper\s*=\s*".*?"',
    ('$FallbackHelper = "' + (Join-Path $rules "VIS_VRN_PDFTextLayerFallbackPlan_v0222.py") + '"')
$patched = Join-Path $runDir "candidate_patched.RUNLOCAL.ps1"
[IO.File]::WriteAllText($patched, $code, [Text.UTF8Encoding]::new($true))
Write-Host "[BATCH] run-local candidate: $patched" -ForegroundColor Cyan

# A01/A18 - enumerate corpus
$pdfs = @(Get-ChildItem -LiteralPath $inbox -Filter *.pdf -File | Sort-Object Name)
$docx = @(Get-ChildItem -LiteralPath $inbox -Filter *.docx -File)
Write-Host "[BATCH] corpus: $($pdfs.Count) pdf | $($docx.Count) docx (SKIP_UNSUPPORTED)" -ForegroundColor Cyan

# A10 - resume set
$done = @{}
if ((-not $Fresh) -and (Test-Path $resultCsv)) {
    foreach ($r in (Import-Csv $resultCsv)) {
        if ($r.Verdict -eq "PLAN_READY") { $done[$r.File] = $true }
    }
}
$todo = @($pdfs | Where-Object { -not $done.ContainsKey($_.Name) })
Write-Host "[BATCH] resume: $($done.Count) already PLAN_READY, $($todo.Count) to run" -ForegroundColor Cyan

# A09 - filename tickers in one python pass (v0100 tokenizer)
$tickMap = @{}
try {
    $py = @("$env:USERPROFILE\envs\via_core_312\Scripts\python.exe","py") |
          Where-Object { ($_ -eq "py") -or (Test-Path $_) } | Select-Object -First 1
    $names = Join-Path $runDir "names.txt"
    $pdfs.Name | Out-File $names -Encoding utf8
    $tk = Join-Path $rules "VIS_VRN_TickerFilenameSSOT_v0100.py"
    $pyc = "import sys,importlib.util;spec=importlib.util.spec_from_file_location('t',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);" +
           "[print(l.rstrip()+'`t'+','.join(m.extract_filename_ticker_candidates(l.rstrip())[0])) for l in open(sys.argv[2],encoding='utf-8') if l.strip()]"
    foreach ($line in (& $py -c $pyc $tk $names 2>$null)) {
        $parts = $line -split "`t"
        if ($parts.Count -eq 2) { $tickMap[$parts[0]] = $parts[1] }
    }
} catch {}

# A02 - parallel pool
$jobs = @{}
$queue = [System.Collections.Generic.Queue[object]]::new()
$todo | ForEach-Object { $queue.Enqueue($_) }
$results = [System.Collections.Generic.List[object]]::new()
$total = $todo.Count
$launched = 0

function Start-One($pdf, $patched, $runDir, $timeout) {
    $log = Join-Path $runDir ($pdf.BaseName + ".log")
    Start-ThreadJob -ArgumentList $patched, $pdf.FullName, $log, $timeout -ScriptBlock {
        param($p, $f, $lg, $to)
        $sw2 = [Diagnostics.Stopwatch]::StartNew()
        $proc = Start-Process pwsh -ArgumentList @("-NoProfile","-NonInteractive","-File","`"$p`"","-TargetFile","`"$f`"") `
                -RedirectStandardOutput $lg -RedirectStandardError ($lg + ".err") -PassThru -WindowStyle Hidden
        if (-not $proc.WaitForExit($to * 1000)) { try { $proc.Kill($true) } catch {}; $timedOut = $true } else { $timedOut = $false }
        $tail = if (Test-Path $lg) { (Get-Content $lg -Tail 60) -join "`n" } else { "" }
        if (Test-Path ($lg + ".err")) { $tail += "`n" + ((Get-Content ($lg + ".err") -Tail 20) -join "`n") }
        $alias = if ($tail -match '\[ALIAS\]\s*(.+)') { $Matches[1].Trim() } else { "" }
        $verdict = if ($timedOut) { "TIMEOUT" }
                   elseif ($tail -match 'NOOCR_STAGING_PLAN_READY') { "PLAN_READY" }
                   elseif ($tail -match 'ERROR|FATAL|Exception') { "FAIL" }
                   else { "UNKNOWN" }
        [pscustomobject]@{ Verdict = $verdict; Alias = $alias; Sec = [int]$sw2.Elapsed.TotalSeconds; Log = $lg }
    }
}

while ($queue.Count -or $jobs.Count) {
    while ($queue.Count -and $jobs.Count -lt $Throttle) {
        $pdf = $queue.Dequeue(); $launched++
        $jobs[(Start-One $pdf $patched $runDir $TimeoutSec).Id] = $pdf
    }
    $doneIds = @($jobs.Keys | Where-Object { (Get-Job -Id $_).State -in @("Completed","Failed","Stopped") })
    foreach ($id in $doneIds) {
        $pdf = $jobs[$id]; $jobs.Remove($id)
        $r = Receive-Job -Id $id -ErrorAction SilentlyContinue | Select-Object -First 1
        Remove-Job -Id $id -Force -ErrorAction SilentlyContinue
        if (-not $r) { $r = [pscustomobject]@{ Verdict="JOBFAIL"; Alias=""; Sec=0; Log="" } }
        $row = [pscustomobject]@{
            Time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss"); File = $pdf.Name
            Ticker = $tickMap[$pdf.Name]; Alias = $r.Alias; Verdict = $r.Verdict; Sec = $r.Sec; Run = $ts
        }
        $results.Add($row)
        $row | Export-Csv $resultCsv -Append -NoTypeInformation -Encoding UTF8
        $color = switch ($r.Verdict) { "PLAN_READY" { "Green" } "TIMEOUT" { "Yellow" } default { "Red" } }
        Write-Host ("[{0}/{1}] {2,-11} {3}  {4}" -f $results.Count, $total, $r.Verdict, $pdf.Name, $r.Alias) -ForegroundColor $color
    }
    $eta = if ($results.Count) { [int](($total - $results.Count) * ($sw.Elapsed.TotalSeconds / [math]::Max(1,$results.Count))) } else { 0 }
    Write-Progress -Id 1 -Activity "VRN Batch ($Throttle-wide pool)" `
        -Status "$($results.Count)/$total done - $([int]$sw.Elapsed.TotalSeconds)s elapsed - ETA ${eta}s" `
        -PercentComplete $(if ($total) { [math]::Min(99, $results.Count * 100 / $total) } else { 100 })
    Start-Sleep -Milliseconds 300
}
Write-Progress -Id 1 -Completed -Activity done

}
catch { Write-Host "[ABORT] $($_.Exception.Message)" -ForegroundColor Red }
finally {
    Write-Host "`n==================== VRN BATCH SUMMARY ====================" -ForegroundColor Cyan
    $g = $results | Group-Object Verdict | Sort-Object Count -Descending
    $g | ForEach-Object { Write-Host ("  {0,-11} {1}" -f $_.Name, $_.Count) }
    Write-Host "`n---- broker tally (this run) ----" -ForegroundColor Cyan
    $results | Where-Object Alias | Group-Object Alias | Sort-Object Count -Descending |
        ForEach-Object { Write-Host ("  {0,-24} {1}" -f $_.Name, $_.Count) }
    Write-Host "`n[RESULTS] $resultCsv (append-only, resumable - rerun skips PLAN_READY)" -ForegroundColor Cyan
    Write-Host "[LOGS]    $runDir" -ForegroundColor Cyan
    Write-Host "[TOTAL]   $([int]$sw.Elapsed.TotalSeconds)s" -ForegroundColor Cyan
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}
