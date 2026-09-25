<#
.SYNOPSIS
    VRN auto-test loop launcher: tests VIA_VRN_FirstPageEngine + VRN_Integrated_ReportDatabase_Engine
    against C:\測試樣本報告 (or a synthetic corpus), applies runtime repairs, repeats until green.
.DESCRIPTION
    LIVE off, no network, no consent variable is ever set. Output goes to -Out (default %LOCALAPPDATA%\VRN_AutoTest).
    -InstallDeps is the operator's hand: it runs pip for the optional stack (pandas pyarrow pdfplumber pymupdf python-docx).
.EXAMPLE
    pwsh -NoProfile -ExecutionPolicy Bypass -File ".\Invoke-VRN-AutoTest.ps1"
    pwsh -NoProfile -ExecutionPolicy Bypass -File ".\Invoke-VRN-AutoTest.ps1" -Samples "C:\測試樣本報告" -Rounds 3 -InstallDeps
    pwsh -NoProfile -ExecutionPolicy Bypass -File ".\Invoke-VRN-AutoTest.ps1" -Synthetic
#>
[CmdletBinding()]
param(
    [string]$Samples = 'C:\測試樣本報告',
    [string]$Out = '',
    [int]$Rounds = 3,
    [switch]$Synthetic,
    [switch]$InstallDeps,
    [switch]$NoAudit
)
# ===== VIA-ENTER-ENV v0101 · 進入環境 · 每支 VIA PowerShell 最上方固定區塊（勿手改；全庫同文，改 scripts/VIA-Enter-Root.ps1 後同步） =====
# 進入 VIA-VDF-VRN 根、鎖 UTF-8、預設禁網／LIVE 關、掛 via_core／via_vdf 受管 Python；不刪、不卸載、不殺行程、不 exit、不連網。
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { Write-Verbose "console encoding unchanged: $($_.Exception.Message)" }
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:VIA_NET) { $env:VIA_NET = '0' }
if (-not $env:VIA_LIVE) { $env:VIA_LIVE = '0' }
if (-not $env:VIA_OPEN_ATTACH) { $env:VIA_OPEN_ATTACH = '0' }
if (-not $env:VIA_LKGC) { $env:VIA_LKGC = '2026-09-06' }
foreach ($ViaEnterUvHome in @($env:USERPROFILE, $HOME)) {
    if ($ViaEnterUvHome) {
        $ViaEnterUvBin = Join-Path (Join-Path $ViaEnterUvHome '.local') 'bin'
        if ((Test-Path -LiteralPath (Join-Path $ViaEnterUvBin 'uv.exe') -PathType Leaf) -or (Test-Path -LiteralPath (Join-Path $ViaEnterUvBin 'uv') -PathType Leaf)) {
            if (($env:PATH -split [System.IO.Path]::PathSeparator) -notcontains $ViaEnterUvBin) {
                $env:PATH = $ViaEnterUvBin + [System.IO.Path]::PathSeparator + $env:PATH
            }
        }
    }
}
$ViaEnterCandidates = New-Object System.Collections.Generic.List[string]
if ($env:VIA_ROOT) { $ViaEnterCandidates.Add($env:VIA_ROOT) }
if ($env:USERPROFILE) { $ViaEnterCandidates.Add((Join-Path $env:USERPROFILE 'VIA-VDF-VRN')) }
foreach ($ViaEnterProbe in @($PSScriptRoot, (Get-Location).Path)) {
    for ($ViaEnterDepth = 0; $ViaEnterDepth -lt 6 -and $ViaEnterProbe; $ViaEnterDepth++) {
        $ViaEnterCandidates.Add($ViaEnterProbe)
        $ViaEnterProbe = Split-Path -Parent $ViaEnterProbe
    }
}
if ($env:USERPROFILE) { $ViaEnterCandidates.Add((Join-Path $env:USERPROFILE 'Github/VIA-VDF-VRN')) }
$ViaEnterRoot = $null
foreach ($ViaEnterCandidate in $ViaEnterCandidates) {
    if ($ViaEnterCandidate -and (Test-Path -LiteralPath (Join-Path $ViaEnterCandidate 'VIA_CentralGovernance.py') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $ViaEnterCandidate 'config/ssot/VIA_SystemMaster.via') -PathType Leaf)) {
        $ViaEnterRoot = (Resolve-Path -LiteralPath $ViaEnterCandidate).Path
        break
    }
}
if ($ViaEnterRoot) {
    $env:VIA_ROOT = $ViaEnterRoot
    Set-Location -LiteralPath $ViaEnterRoot
    foreach ($ViaEnterVar in @('VIA_PYTHON', 'VIA_VDF_PY')) {
        $ViaEnterPreset = [System.Environment]::GetEnvironmentVariable($ViaEnterVar)
        if ($ViaEnterPreset -and ($ViaEnterPreset -match '(?i)WindowsApps|[\\/]py\.exe$' -or -not (Test-Path -LiteralPath $ViaEnterPreset -PathType Leaf))) {
            Write-Host ('YELLOW  ENTER        {0}={1} 不是受管直譯器（Store 別名／py.exe／不存在）；本行程改用 via_core／via_vdf' -f $ViaEnterVar, $ViaEnterPreset) -ForegroundColor Yellow
            [System.Environment]::SetEnvironmentVariable($ViaEnterVar, $null)
        }
    }
    $ViaEnterHomes = New-Object System.Collections.Generic.List[string]
    if ($env:USERPROFILE) { $ViaEnterHomes.Add((Join-Path $env:USERPROFILE 'envs')) }
    $ViaEnterHomes.Add($ViaEnterRoot)
    foreach ($ViaEnterHome in $ViaEnterHomes) {
        foreach ($ViaEnterPair in @(@('via_core', 'VIA_PYTHON'), @('via_vdf', 'VIA_VDF_PY'))) {
            $ViaEnterExe = @('Scripts/python.exe', 'bin/python') |
                ForEach-Object { Join-Path (Join-Path $ViaEnterHome $ViaEnterPair[0]) $_ } |
                Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
            if ($ViaEnterExe -and -not [System.Environment]::GetEnvironmentVariable($ViaEnterPair[1])) {
                [System.Environment]::SetEnvironmentVariable($ViaEnterPair[1], $ViaEnterExe)
                if ($ViaEnterPair[0] -eq 'via_core') {
                    $ViaEnterBin = Split-Path -Parent $ViaEnterExe
                    if (($env:PATH -split [System.IO.Path]::PathSeparator) -notcontains $ViaEnterBin) {
                        $env:PATH = $ViaEnterBin + [System.IO.Path]::PathSeparator + $env:PATH
                    }
                }
            }
        }
    }
    if ($env:VIA_ENTER_ENV -ne $ViaEnterRoot) {
        $env:VIA_ENTER_ENV = $ViaEnterRoot
        Write-Host ('GREEN   ENTER        {0} · NET={1} · LIVE={2} · VIA_PYTHON={3}' -f $ViaEnterRoot, $env:VIA_NET, $env:VIA_LIVE,
            $(if ($env:VIA_PYTHON) { $env:VIA_PYTHON } else { 'bootstrap' })) -ForegroundColor Green
    }
}
else {
    Write-Host 'YELLOW  ENTER        找不到 VIA-VDF-VRN 根（需含 VIA_CentralGovernance.py 與 config/ssot/VIA_SystemMaster.via）；沿用目前目錄' -ForegroundColor Yellow
}
# ===== /VIA-ENTER-ENV =====

# ===== [VIA:PS-ACCEL20:v0100] PS20 accelerator lanes x20 (all-ps directive; graceful, zero behaviour change; never sets VIA_NET_CONSENT) =====
try {
    $VIAPS20 = [ordered]@{
        'PS-01' = 'AsyncPool'; 'PS-02' = 'HttpReuse'; 'PS-03' = 'TimeoutBudget'; 'PS-04' = 'RetryOnce'; 'PS-05' = 'ConsentGate'
        'PS-06' = 'SeriesCache'; 'PS-07' = 'ParquetYearPart'; 'PS-08' = 'SortDateId'; 'PS-09' = 'DictEncode'; 'PS-10' = 'ChunkAlign'
        'PS-11' = 'MinMaxIndex'; 'PS-12' = 'BloomProbe'; 'PS-13' = 'Batch64k'; 'PS-14' = 'HotColumns'; 'PS-15' = 'TypedCols'
        'PS-16' = 'PolarsLazy'; 'PS-17' = 'SIMDScan'; 'PS-18' = 'DuckDBScan'; 'PS-19' = 'PredPush'; 'PS-20' = 'PipeParallel'
    }
    $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    while ($VIAPSAccelProbe) {
        $VIAPSAccelMod = Join-Path -Path (Join-Path -Path $VIAPSAccelProbe -ChildPath 'supportive modules') -ChildPath 'VIA_PS_Accel_Module.ps1'
        if (Test-Path -LiteralPath $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelParent = Split-Path -Path $VIAPSAccelProbe -Parent
        if (-not $VIAPSAccelParent -or $VIAPSAccelParent -eq $VIAPSAccelProbe) { break }
        $VIAPSAccelProbe = $VIAPSAccelParent
    }
    if ($VIAPS20.Count -ne 20) { $VIAPS20 = $null }
} catch { $VIAPS20 = $null }
# ===== [VIA:PS-ACCEL20:END] =====

# ===== VRN auto-test launcher body (after the fixed VIA-ENTER-ENV block) =====
$ErrorActionPreference = 'Stop'
$VrnPython = if ($env:VIA_PYTHON) { $env:VIA_PYTHON } else { 'python' }
$VrnLoop = Join-Path (Join-Path $PSScriptRoot 'engine') 'VRN_AutoTestLoop.py'
if (-not (Test-Path -LiteralPath $VrnLoop -PathType Leaf)) {
    Write-Host ('RED     VRN-AUTOTEST  loop not found: {0}' -f $VrnLoop) -ForegroundColor Red
    exit 2
}
if (-not $Out) {
    $VrnOutBase = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } elseif ($HOME) { $HOME } else { $PSScriptRoot }
    $Out = Join-Path $VrnOutBase 'VRN_AutoTest'
}
if ($InstallDeps) {
    Write-Host 'BLUE    VRN-AUTOTEST  installing the optional stack (operator request)' -ForegroundColor Cyan
    & $VrnPython -m pip install --disable-pip-version-check pandas pyarrow pdfplumber pymupdf python-docx
    if ($LASTEXITCODE -ne 0) { Write-Host 'YELLOW  VRN-AUTOTEST  pip install failed; continuing with what is installed' -ForegroundColor Yellow }
}
$VrnLoopArgs = @('--rounds', "$Rounds", '--out', $Out)
if ($Synthetic) {
    $VrnLoopArgs += '--synthetic'
} elseif (Test-Path -LiteralPath $Samples -PathType Container) {
    $VrnLoopArgs += @('--samples', $Samples)
} else {
    Write-Host ('YELLOW  VRN-AUTOTEST  samples folder not found: {0}; using the synthetic corpus' -f $Samples) -ForegroundColor Yellow
    $VrnLoopArgs += '--synthetic'
}
if ($NoAudit) { $VrnLoopArgs += '--no-audit' }
Write-Host ('BLUE    VRN-AUTOTEST  {0} {1}' -f $VrnPython, ($VrnLoopArgs -join ' ')) -ForegroundColor Cyan
& $VrnPython $VrnLoop @VrnLoopArgs
$VrnExit = $LASTEXITCODE
$VrnReport = Join-Path $Out 'VRN_AutoTest_Report.html'
if ($VrnExit -eq 0) {
    Write-Host ('GREEN   VRN-AUTOTEST  all gates passed; report: {0}' -f $VrnReport) -ForegroundColor Green
} elseif ($VrnExit -eq 2) {
    Write-Host ('YELLOW  VRN-AUTOTEST  no corpus could be built (install pymupdf or provide samples); report: {0}' -f $VrnReport) -ForegroundColor Yellow
} else {
    Write-Host ('RED     VRN-AUTOTEST  exit {0}; open the report to see which gate and which file: {1}' -f $VrnExit, $VrnReport) -ForegroundColor Red
}
exit $VrnExit
