#requires -Version 7.0
<# =====================================================================
 Invoke-VIA-ImportStaging - manifest-driven Downloads import (reusable)
 Reads the newest (or named) manifest in import_manifests/, then for each
 canonical name: collects "(n)" duplicate downloads, SHA256-dedupes,
 picks newest when variants differ, compares against the repo tree -
 identical -> skip, different -> _conflicts_with_repo, absent -> staging.
 45MB guard. Commits and pushes main. Claude does stage-2 placement.
===================================================================== #>
param([string]$Manifest = "")
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
$via  = $PSScriptRoot
$repo = Split-Path $via -Parent
$dl   = Join-Path $env:USERPROFILE "Downloads"
$mdir = Join-Path $via "import_manifests"
$mfile = if ($Manifest) { Join-Path $mdir $Manifest }
         else { (Get-ChildItem $mdir -Filter "IMPORT_*.json" | Sort-Object Name -Descending | Select-Object -First 1).FullName }
if (-not (Test-Path -LiteralPath $mfile)) { Write-Host "[FATAL] no manifest found" -ForegroundColor Red; return }
$m = Get-Content -LiteralPath $mfile -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "[IMPORT] manifest: $(Split-Path $mfile -Leaf) ($($m.files.Count) entries)" -ForegroundColor Cyan

Push-Location $repo
try {
    git fetch origin 2>&1 | Out-Null
    git checkout main 2>&1 | Out-Host
    git merge origin/claude/via-system-followup-tz7k9t 2>&1 | Out-Host

    $stage = Join-Path $via $m.staging_dir
    $conf  = Join-Path $stage "_conflicts_with_repo"
    New-Item -ItemType Directory -Force -Path $stage, $conf | Out-Null

    $groups = [ordered]@{}
    foreach ($n in $m.files) {
        $k = ($n -replace '%20',' ') -replace ' \(\d+\)(\.[^.]+)$','$1'
        $groups[$k] = $true
    }

    $idx = @{}
    Get-ChildItem $via -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch [regex]::Escape($m.staging_dir) } |
        ForEach-Object { if (-not $idx.ContainsKey($_.Name.ToLower())) { $idx[$_.Name.ToLower()] = $_.FullName } }

    $new=0; $same=0; $cfl=0; $miss=0; $big=0
    foreach ($k in $groups.Keys) {
        try {
            $stem = [IO.Path]::GetFileNameWithoutExtension($k); $ext = [IO.Path]::GetExtension($k)
            $vars = @()
            $exact = Join-Path $dl $k
            if (Test-Path -LiteralPath $exact) { $vars += Get-Item -LiteralPath $exact }
            $vars += @(Get-ChildItem -LiteralPath $dl -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match ('^' + [regex]::Escape($stem) + ' \(\d+\)' + [regex]::Escape($ext) + '$') })
            if (-not $vars -or $vars.Count -eq 0) { Write-Host "[MISS ] $k" -ForegroundColor DarkYellow; $miss++; continue }
            $hashes = @($vars | ForEach-Object { [pscustomobject]@{ F=$_; H=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } })
            $uniq = @($hashes.H | Select-Object -Unique)
            $pick = if ($uniq.Count -eq 1) { $hashes[0] } else {
                Write-Host "[VPICK] $k -> newest of $($uniq.Count) variants" -ForegroundColor Magenta
                $hashes | Sort-Object { $_.F.LastWriteTime } -Descending | Select-Object -First 1
            }
            if ($pick.F.Length -gt 45MB) { Write-Host "[LARGE] $k skipped" -ForegroundColor Red; $big++; continue }
            $inRepo = $idx[$k.ToLower()]
            if ($inRepo) {
                if ((Get-FileHash -LiteralPath $inRepo -Algorithm SHA256).Hash -eq $pick.H) {
                    $same++; Write-Host "[SAME ] $k" -ForegroundColor DarkGray; continue
                }
                Copy-Item -LiteralPath $pick.F.FullName -Destination (Join-Path $conf $k) -Force
                $cfl++; Write-Host "[CONFL] $k" -ForegroundColor Yellow
            } else {
                Copy-Item -LiteralPath $pick.F.FullName -Destination (Join-Path $stage $k) -Force
                $new++; Write-Host "[NEW  ] $k" -ForegroundColor Green
            }
        } catch { Write-Host "[ERR  ] $k :: $($_.Exception.Message)" -ForegroundColor Red }
    }
    Write-Host "==== NEW=$new SAME=$same CONFL=$cfl MISS=$miss LARGE=$big ====" -ForegroundColor Cyan

    git add -- ("VeritasIntelligenceAnalytics/" + $m.staging_dir) 2>&1 | Out-Host
    $staged = @(git diff --cached --name-only)
    if ($staged.Count) {
        git commit -m "Import staging $($m.staging_dir): $new new, $cfl conflicts ($same identical skipped)" 2>&1 | Out-Host
    } else { Write-Host "nothing staged" }
    $ok = $false
    foreach ($d in @(0,2,4,8,16)) {
        if ($d) { Start-Sleep -Seconds $d }
        git push origin main 2>&1 | Out-Host
        if ($LASTEXITCODE -eq 0) { $ok = $true; break }
        git pull --rebase --autostash origin main 2>&1 | Out-Host
    }
    Write-Host $(if ($ok) { "[PUSH] OK" } else { "[PUSH] FAILED" }) -ForegroundColor $(if ($ok) { "Green" } else { "Red" })
}
catch { Write-Host "[ABORT] $($_.Exception.Message)" -ForegroundColor Red }
finally { Pop-Location; Write-Host "PowerShell session remains open." -ForegroundColor Cyan }

