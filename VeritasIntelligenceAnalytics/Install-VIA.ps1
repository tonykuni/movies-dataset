#requires -Version 7.0
<# =====================================================================
 Install-VIA - one-shot, idempotent provisioning (布建到底,整合為一)
 Sets everything up so any new terminal can just type:
   via         -> sync + VDF + VAP + open UIs
   via-tower   -> Control Tower HTML console
   via-all     -> full stack (VDF+VAP+VRN+Tower+audits)
   via-shim    -> TickerRegex v0100 shimmed entry
   via-sync    -> repo sync (fetch/merge/push)
 What it provisions (User scope, no admin needed, re-run safe):
   1. env vars VIA_REPO / VIA_HOME / VIA_REPORTS
   2. adds VeritasIntelligenceAnalytics\bin to User PATH
   3. desktop shortcut "VIA Control Tower"
   4. prerequisite matrix (git / python / via_core_312 / java) with
      best-effort winget install for missing ones (never blocks)
   5. verification matrix at the end
 Optional: -AutoStart registers a logon task for the Tower (default off).
===================================================================== #>
param([switch]$AutoStart, [switch]$NoWinget)
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
$viaHome = $PSScriptRoot
$repo    = Split-Path $viaHome -Parent
$binDir  = Join-Path $viaHome "bin"
$reports = Join-Path $env:USERPROFILE "VIA_Reports"
$M = [System.Collections.Generic.List[object]]::new()
function Step($n,$s,$note){ $M.Add([pscustomobject]@{Item=$n;Status=$s;Note=$note}) }

Write-Host "===== VIA PROVISIONING (idempotent) =====" -ForegroundColor Cyan
Write-Host "repo: $repo"

# ---- 1) env vars (User scope + current session) ----
try {
    foreach ($kv in @(@("VIA_REPO",$repo), @("VIA_HOME",$viaHome), @("VIA_REPORTS",$reports))) {
        [Environment]::SetEnvironmentVariable($kv[0], $kv[1], "User")
        Set-Item -Path "Env:$($kv[0])" -Value $kv[1]
    }
    New-Item -ItemType Directory -Force -Path $reports | Out-Null
    Step "env vars" "PASS" "VIA_REPO / VIA_HOME / VIA_REPORTS"
} catch { Step "env vars" "FAIL" $_.Exception.Message }

# ---- 2) PATH += bin (idempotent) ----
try {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("Path", ($userPath.TrimEnd(";") + ";" + $binDir), "User")
        Step "PATH" "PASS" "added $binDir"
    } else { Step "PATH" "PASS" "already present" }
    if ($env:Path -notlike "*$binDir*") { $env:Path += ";$binDir" }
} catch { Step "PATH" "FAIL" $_.Exception.Message }

# ---- 3) desktop shortcut: VIA Control Tower ----
try {
    $lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "VIA Control Tower.lnk"
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = (Get-Command pwsh).Source
    $sc.Arguments = "-NoProfile -File `"$viaHome\Start-VIA-OneClick.ps1`" -Tower"
    $sc.WorkingDirectory = $repo
    $sc.Description = "Veritas Intelligence Analytics - Control Tower"
    $sc.Save()
    Step "desktop shortcut" "PASS" $lnk
} catch { Step "desktop shortcut" "WARN" $_.Exception.Message }

# ---- 4) prerequisites (check, then best-effort winget) ----
$pre = @(
    @{ n = "git";    test = { Get-Command git -ErrorAction SilentlyContinue };    winget = "Git.Git" },
    @{ n = "python"; test = { (Get-Command py -ErrorAction SilentlyContinue) -or
                              (Test-Path "$env:USERPROFILE\envs\via_core_312\Scripts\python.exe") }; winget = "Python.Python.3.12" },
    @{ n = "java(tabula)"; test = { Get-Command java -ErrorAction SilentlyContinue }; winget = "EclipseAdoptium.Temurin.8.JRE" }
)
foreach ($p in $pre) {
    $ok = & $p.test
    if ($ok) { Step "prereq $($p.n)" "PASS" ""; continue }
    if ($NoWinget -or -not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Step "prereq $($p.n)" "WARN" "missing (winget unavailable/skipped)"; continue
    }
    Write-Host "[WINGET] installing $($p.n)..." -ForegroundColor Yellow
    winget install --id $p.winget --accept-source-agreements --accept-package-agreements -h 2>&1 |
        Select-Object -Last 2 | Out-Host
    Step "prereq $($p.n)" $(if (& $p.test) { "PASS" } else { "WARN" }) "winget attempted"
}
$envp = "$env:USERPROFILE\envs\via_core_312\Scripts\python.exe"
Step "via_core_312 (OCR env)" $(if (Test-Path $envp) { "PASS" } else { "WARN" }) `
    $(if (Test-Path $envp) { "12-dep OCR environment present" } else { "optional - only needed for VRN OCR lanes" })

# ---- 5) optional logon autostart ----
if ($AutoStart) {
    try {
        schtasks /Create /F /SC ONLOGON /TN "VIA_Control_Tower" /TR "`"$((Get-Command pwsh).Source)`" -NoProfile -File `"$viaHome\Start-VIA-OneClick.ps1`" -Tower" | Out-Null
        Step "autostart" "PASS" "logon task VIA_Control_Tower"
    } catch { Step "autostart" "WARN" $_.Exception.Message }
} else { Step "autostart" "SKIP" "off by default (rerun with -AutoStart to enable)" }

# ---- 6) verification ----
foreach ($cmd in "via.cmd","via-tower.cmd","via-all.cmd","via-shim.cmd","via-sync.cmd") {
    Step "command $($cmd -replace '\.cmd$','')" $(if (Test-Path (Join-Path $binDir $cmd)) { "PASS" } else { "FAIL" }) ""
}

Write-Host "`n==================== PROVISION MATRIX ====================" -ForegroundColor Cyan
$M | Format-Table -AutoSize
Write-Host "開新終端機後直接輸入:  via   |   via-tower   |   via-all   |   via-shim   |   via-sync" -ForegroundColor Green
Write-Host "注意:若本安裝器是以 pwsh -File 從另一個視窗啟動,母視窗需開新終端機才會生效;" -ForegroundColor Yellow
Write-Host ('      或在母視窗貼:  $env:Path += ";' + $binDir + '"') -ForegroundColor Yellow
Write-Host "PowerShell session remains open." -ForegroundColor Cyan

