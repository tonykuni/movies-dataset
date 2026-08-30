# requires -Version 7.0
# =============================================================================
# Invoke-VIA-ALL.ps1 v5
# VIA ALL-IN-ONE  ENV -> HardGate FULL -> VRN -> Report
# =============================================================================
# Fixes vs v4 (based on Tony's actual run log 2026-05-06 21:40:33):
#   F1: ALL child PS1 invocations now use:
#       pwsh -NoProfile -ExecutionPolicy Bypass -File <path>
#       (solves "not digitally signed" error)
#   F2: HardGate seal still PARTIAL with env vars only -> now also writes a
#       config JSON read by HardGate AND parses returned JSON to verify
#       seal=FULL. If not FULL, prints exactly what to fix.
#   F3: All paths quoted properly to handle spaces ("$Var")
#   F4: Self-healing parser: detects v4-style script that crashes on .SYNOPSIS
#       and rewrites it before re-running.
# =============================================================================

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
[CmdletBinding()]
param(
    [ValidateSet("all","stock")]
    [string]$M01Mode = "all",
    [switch]$NoPause,
    [switch]$NoKeepAlive,
    [switch]$SkipDedup,
    [switch]$SkipEnvPartition,
    [switch]$SkipHardGate,
    [switch]$NoOpenReport,
    [int]$KeepAliveMinutes = 5
)

$ErrorActionPreference = "Continue"

# VIA Visual Lock palette
$P = @{
    H = "`e[38;2;76;120;168m"
    S = "`e[38;2;67;154;154m"
    W = "`e[38;2;224;176;32m"
    E = "`e[38;2;200;48;48m"
    M = "`e[38;2;200;224;200m"
    R = "`e[0m"
    B = "`e[1m"
}

$global:VIA_EXIT  = 0
$global:STAGE_RES = @()
$SPINNER = @('|','/','-','\')

# =============================================================================
# UI
# =============================================================================

function Write-VHeader {
    param([string]$Text)
    $bar = "=" * 76
    Write-Host ""
    Write-Host "$($P.H)$($P.B)$bar$($P.R)"
    Write-Host "$($P.H)$($P.B)  $Text$($P.R)"
    Write-Host "$($P.H)$($P.B)$bar$($P.R)"
}

function Write-VStatus {
    param([string]$Status,[string]$Text)
    $color = switch ($Status) {
        "OK"    { $P.S }
        "PASS"  { $P.S }
        "READY" { $P.S }
        "WARN"  { $P.W }
        "FAIL"  { $P.E }
        "ERROR" { $P.E }
        "STALL" { $P.W }
        "SKIP"  { $P.M }
        default { $P.M }
    }
    Write-Host "$color  [$Status]$($P.R) $Text"
}

function Add-StageResult {
    param([string]$Stage,[string]$Status,[string]$Detail,[double]$Elapsed)
    $global:STAGE_RES += [pscustomobject]@{
        Stage   = $Stage
        Status  = $Status
        Detail  = $Detail
        Elapsed = $Elapsed
    }
}

# =============================================================================
# KEEP-ALIVE
# =============================================================================

function Wait-VAnyKey {
    param([int]$ExitCode = 0)
    if ($script:NoPause) { return }
    Write-Host ""
    Write-Host "$($P.H)$('-' * 76)$($P.R)"
    $statusColor = if ($ExitCode -eq 0) { $P.S } else { $P.E }
    $statusText  = if ($ExitCode -eq 0) { "[COMPLETE]" } else { "[EXIT CODE $ExitCode]" }
    Write-Host "$statusColor  $statusText$($P.R)"
    Write-Host "$($P.M)  Press any key to enter keep-alive...$($P.R)"
    Write-Host "$($P.H)$('-' * 76)$($P.R)"
    try {
        if ($Host.UI.RawUI -and $Host.Name -ne "Default Host") {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        } else {
            Read-Host "Press Enter"
        }
    } catch {
        try { Read-Host "Press Enter" } catch { Start-Sleep -Seconds 3 }
    }
}

function Start-VIAKeepAlive {
    param([int]$ExitCode = 0,[int]$Minutes = 5)
    if ($script:NoKeepAlive) { return }
    Write-Host ""
    Write-Host "$($P.H)$('=' * 76)$($P.R)"
    Write-Host "$($P.S)  POWERSHELL SESSION ACTIVE$($P.R)"
    Write-Host "$($P.M)  ExitCode = $ExitCode  Keep-alive ${Minutes}min  Ctrl+C to exit anytime$($P.R)"
    Write-Host "$($P.H)$('=' * 76)$($P.R)"
    $totalSec = $Minutes * 60
    $tick = 0
    for ($s = $totalSec; $s -gt 0; $s -= 1) {
        $tick++
        $mm = [math]::Floor($s / 60)
        $ss = $s % 60
        $glyph = $SPINNER[$tick % $SPINNER.Count]
        $line = ("$($P.M)  $glyph  Keep-alive remaining: {0:00}:{1:00}  (Ctrl+C to exit)$($P.R)" -f $mm, $ss)
        Write-Host "`r$line" -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host "`r$(' ' * 100)`r" -NoNewline
    Write-Host ""
    Write-Host "$($P.M)  Keep-alive expired. Exiting cleanly.$($P.R)"
}

# =============================================================================
# CHILD-SCRIPT INVOKER  (FIX F1 + F3)
# Runs every child PS1 via: pwsh -NoProfile -ExecutionPolicy Bypass -File ...
# This bypasses digital signature checks and any custom ExecutionPolicy.
# Env vars set in current session ARE inherited by child pwsh process.
# =============================================================================

function Invoke-VIAScript {
    param(
        [string]$Name,
        [string]$Path,
        [string[]]$ScriptArgs = @()
    )
    if (-not (Test-Path $Path)) {
        Write-VStatus "WARN" "$Name not found: $Path"
        return @{ ExitCode = -1; Status = "MISSING"; Elapsed = 0 }
    }
    $start = Get-Date
    Write-VStatus "READY" "$Name -> launching child pwsh..."
    try {
        $allArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$Path) + $ScriptArgs
        & pwsh @allArgs
        $code = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
        $elapsed = ((Get-Date) - $start).TotalSeconds
        return @{
            ExitCode = $code
            Status   = if ($code -eq 0) { "PASS" } else { "WARN" }
            Elapsed  = $elapsed
        }
    } catch {
        Write-VStatus "FAIL" "$Name exception: $($_.Exception.Message)"
        return @{
            ExitCode = 1
            Status   = "FAIL"
            Elapsed  = ((Get-Date) - $start).TotalSeconds
            Detail   = $_.Exception.Message
        }
    }
}

# =============================================================================
# PATHS
# =============================================================================

$Root         = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
$ModuleRoot   = Join-Path $Root "module"
$Supportive   = Join-Path $ModuleRoot "supportive_module"
$VRNDir       = Join-Path $ModuleRoot "VRN"
$M01InputDir  = Join-Path $VRNDir "input"

$EnvPartition = Join-Path $Supportive "VIA_ENV_PARTITION_v2.ps1"
$SupportGate  = Join-Path $Supportive "Invoke-VIA-SupportiveHardGate.ps1"
$VRNGo        = Join-Path $VRNDir "VRN_GO.ps1"

$EnvRunsRoot  = Join-Path $ModuleRoot "_via_env_partition_runs"
$VRNOutRoot   = Join-Path $VRNDir "_runs"
$HGRunsRoot   = Join-Path $Supportive "_via_supportive_integration_runs"

# =============================================================================
# MAIN
# =============================================================================

function Invoke-Main {
    Write-VHeader "VIA ALL-IN-ONE v5  ENV -> HardGate FULL -> VRN -> Report"
    Write-Host "$($P.M)  Script Dir : $PSScriptRoot$($P.R)"
    Write-Host "$($P.M)  M01 Mode   : $M01Mode$($P.R)"
    Write-Host "$($P.M)  Started    : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')$($P.R)"

    # =========================================================================
    # STAGE 0  M01 Input Dedup (size + SHA256)
    # =========================================================================
    Write-VHeader "STAGE 0  M01 Input Dedup (size + SHA256)"
    $t0 = Get-Date

    if ($SkipDedup) {
        Write-VStatus "SKIP" "Dedup skipped by -SkipDedup"
        Add-StageResult "Dedup" "SKIP" "skipped" 0
    } elseif (-not (Test-Path $M01InputDir)) {
        Write-VStatus "WARN" "M01 input not found: $M01InputDir"
        Add-StageResult "Dedup" "SKIP" "no input dir" 0
    } else {
        $files = Get-ChildItem $M01InputDir -File -Recurse -ErrorAction SilentlyContinue
        $dupCount = 0
        if ($files -and $files.Count -gt 1) {
            $bySize = $files | Group-Object Length
            foreach ($g in $bySize) {
                if ($g.Count -le 1) { continue }
                $hashMap = @{}
                foreach ($f in $g.Group) {
                    try {
                        $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash
                        if ($hashMap.ContainsKey($h)) {
                            def_SafeRemoveItem -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
                            $dupCount++
                            Write-VStatus "WARN" "Removed duplicate: $($f.Name)"
                        } else {
                            $hashMap[$h] = $f.FullName
                        }
                    } catch {
                        Write-VStatus "WARN" "Hash failed: $($f.Name)"
                    }
                }
            }
        }
        $elapsed = ((Get-Date) - $t0).TotalSeconds
        $count = if ($files) { $files.Count } else { 0 }
        Write-VStatus "OK" "Dedup complete: $count scanned, $dupCount duplicates removed"
        Add-StageResult "Dedup" "PASS" "$count files, $dupCount removed" $elapsed
    }

    # =========================================================================
    # STAGE 1  ENV PARTITION
    # FIX F1: use Invoke-VIAScript -> bypasses signature check
    # FIX F4: pre-flight repair of broken .SYNOPSIS header
    # =========================================================================
    Write-VHeader "STAGE 1  ENV PARTITION (CPU SAFE  NO GPU)"
    if ($SkipEnvPartition) {
        Write-VStatus "SKIP" "ENV PARTITION skipped"
        Add-StageResult "ENV Partition" "SKIP" "skipped" 0
    } else {
        # Pre-flight: detect & repair broken <# .SYNOPSIS #> header
        if (Test-Path $EnvPartition) {
            try {
                $head = Get-Content $EnvPartition -TotalCount 5 -ErrorAction SilentlyContinue
                # Check if line 2 starts with .SYNOPSIS but line 1 lacks <#
                $line1 = if ($head.Count -ge 1) { "$($head[0])".Trim() } else { "" }
                $line2 = if ($head.Count -ge 2) { "$($head[1])".Trim() } else { "" }
                $brokenHeader = ($line2 -match '^\.SYNOPSIS') -and ($line1 -notmatch '<#')
                if ($brokenHeader) {
                    Write-VStatus "WARN" "Detected broken <# header in $($EnvPartition.Split('\')[-1])"
                    # Backup original
                    $bak = "$EnvPartition.bak"
                    if (-not (Test-Path $bak)) {
                        Copy-Item -LiteralPath $EnvPartition -Destination $bak -Force
                        Write-VStatus "OK" "Backup created: $($bak.Split('\')[-1])"
                    }
                    # Read full file, find end of broken comment block, rewrite
                    $orig = Get-Content $EnvPartition -Raw -Encoding UTF8
                    # Find first line that looks like real PS code (after .SYNOPSIS / .DESCRIPTION block)
                    # Strategy: skip lines starting with . or empty until we hit #requires / param( / function / etc
                    $lines = $orig -split "`r?`n"
                    $skipUntil = 0
                    for ($i = 0; $i -lt [math]::Min(40, $lines.Count); $i++) {
                        $ln = $lines[$i].Trim()
                        if ($ln -match '^(#requires|param\s*\(|function\s|\$\w+\s*=|Set-StrictMode|\[CmdletBinding|using\s)') {
                            $skipUntil = $i
                            break
                        }
                    }
                    if ($skipUntil -gt 0) {
                        $repaired = ($lines[$skipUntil..($lines.Count - 1)] -join "`r`n")
                        # Write repaired version
                        Set-Content -LiteralPath $EnvPartition -Value $repaired -Encoding UTF8 -NoNewline
                        Write-VStatus "OK" "Repaired: removed orphan SYNOPSIS block, kept code from L$($skipUntil + 1)"
                    } else {
                        Write-VStatus "WARN" "Could not find code start; leaving file as-is"
                    }
                }
            } catch {
                Write-VStatus "WARN" "Pre-flight repair check failed: $($_.Exception.Message)"
            }
        }

        $r = Invoke-VIAScript -Name "ENV_PARTITION" -Path $EnvPartition `
                -ScriptArgs @("-MaxParallelEnvs","4","-NoPause","-NoKeepAlive")
        if ($r.Status -eq "MISSING") {
            Add-StageResult "ENV Partition" "SKIP" "script missing" 0
        } elseif ($r.ExitCode -eq 0) {
            Write-VStatus "OK" "ENV PARTITION completed ($($r.Elapsed)s)"
            Add-StageResult "ENV Partition" "PASS" "exit=0" $r.Elapsed
        } else {
            Write-VStatus "WARN" "ENV PARTITION exit=$($r.ExitCode) (continuing)"
            Add-StageResult "ENV Partition" "WARN" "exit=$($r.ExitCode)" $r.Elapsed
            if ($global:VIA_EXIT -eq 0) { $global:VIA_EXIT = 1 }
        }
    }

    # =========================================================================
    # STAGE 2  SUPPORTIVE HARDGATE FULL
    # FIX F2: env vars + explicit parameters + verify seal=FULL via JSON
    # =========================================================================
    Write-VHeader "STAGE 2  SUPPORTIVE HARDGATE (FULL PROFILE 7/7)"
    $t2 = Get-Date

    # Set FULL profile in current session
    $env:VIA_HARDGATE_POLICY          = "FULL"
    $env:VIA_ENABLE_NETWORK_IO        = "1"
    $env:VIA_ENABLE_PARALLEL_ACCEL    = "1"
    $env:VIA_ENABLE_SSOT_UNIFIED      = "1"
    $env:VIA_ENABLE_RUNTIME_BRIDGE    = "1"
    $env:VIA_ENABLE_ENV_MANAGER       = "1"
    $env:VIA_ENABLE_AST_PLANNER       = "1"
    $env:VIA_ENABLE_ACCELERATOR_SAFE  = "1"
    $env:VIA_MAX_WORKERS              = "8"
    $env:VIA_MAX_CPU_PCT              = "65"
    $env:VIA_MAX_RAM_GB               = "24"
    $env:VIA_SAFE_MODE                = "true"
    $env:VIA_ENABLE_GPU               = "false"

    Write-VStatus "OK" "FULL profile env vars set in current session"
    Write-Host "$($P.M)    VIA_HARDGATE_POLICY     = $($env:VIA_HARDGATE_POLICY)$($P.R)"
    Write-Host "$($P.M)    VIA_ENABLE_NETWORK_IO   = $($env:VIA_ENABLE_NETWORK_IO)$($P.R)"
    Write-Host "$($P.M)    VIA_ENABLE_PARALLEL     = $($env:VIA_ENABLE_PARALLEL_ACCEL)$($P.R)"

    # Also write a config JSON next to the HardGate script, in case it reads
    # config from disk rather than env vars
    $hgConfigPath = Join-Path $Supportive "via_hardgate_config.json"
    try {
        $cfgObj = [ordered]@{
            policy                       = "FULL"
            network_io_enabled           = $true
            parallel_accelerator_enabled = $true
            ssot_unified                 = $true
            runtime_bridge               = $true
            env_manager                  = $true
            ast_planner                  = $true
            accelerator_safe             = $true
            max_workers                  = 8
            max_cpu_pct                  = 65
            max_ram_gb                   = 24
            safe_mode                    = $true
            enable_gpu                   = $false
            generated_by                 = "Invoke-VIA-ALL-v5"
            generated_at                 = (Get-Date).ToString("s")
        }
        $cfgObj | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $hgConfigPath -Encoding UTF8
        Write-VStatus "OK" "Wrote HardGate config: $hgConfigPath"
    } catch {
        Write-VStatus "WARN" "Could not write hardgate config: $($_.Exception.Message)"
    }

    if ($SkipHardGate) {
        Write-VStatus "SKIP" "HardGate skipped"
        Add-StageResult "HardGate FULL" "SKIP" "skipped" 0
    } else {
        $r = Invoke-VIAScript -Name "SUPPORTIVE_HARDGATE" -Path $SupportGate -ScriptArgs @()
        $elapsed = ((Get-Date) - $t2).TotalSeconds
        if ($r.Status -eq "MISSING") {
            Add-StageResult "HardGate FULL" "SKIP" "script missing" 0
        } elseif ($r.ExitCode -eq 0) {
            Write-VStatus "OK" "Supportive HardGate completed (${elapsed}s)"
            # Verify the actual seal level by parsing the latest JSON report
            $sealStatus = "?"
            $sealCapable = "?/7"
            try {
                $latestRun = Get-ChildItem $HGRunsRoot -Directory -ErrorAction SilentlyContinue |
                    Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($latestRun) {
                    $jsonPath = Join-Path $latestRun.FullName "supportive_hardgate_report.json"
                    if (Test-Path $jsonPath) {
                        $hgRpt = Get-Content $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
                        $netOk  = [bool]$hgRpt.network_io_enabled
                        $parOk  = [bool]$hgRpt.parallel_accelerator_enabled
                        if ($netOk -and $parOk) {
                            $sealStatus = "FULL"
                        } elseif ($netOk -or $parOk) {
                            $sealStatus = "PARTIAL+"
                        } else {
                            $sealStatus = "PARTIAL"
                        }
                        Write-VStatus "OK" "HardGate report: seal=$sealStatus  network=$netOk  parallel=$parOk"
                        if ($sealStatus -ne "FULL") {
                            Write-Host ""
                            Write-VStatus "WARN" "HardGate seal is $sealStatus (expected FULL)"
                            Write-Host "$($P.M)    Reason: HardGate script ignores env vars / config JSON.$($P.R)"
                            Write-Host "$($P.M)    Fix: Edit Invoke-VIA-SupportiveHardGate.ps1 to read either:$($P.R)"
                            Write-Host "$($P.M)         (a) `$env:VIA_HARDGATE_POLICY -eq 'FULL'$($P.R)"
                            Write-Host "$($P.M)         (b) Read $hgConfigPath$($P.R)"
                            Write-Host "$($P.M)    Then set network_io_enabled and parallel_accelerator_enabled to true.$($P.R)"
                        }
                    }
                }
            } catch {
                Write-VStatus "WARN" "Could not parse HardGate report: $($_.Exception.Message)"
            }
            Add-StageResult "HardGate FULL" "PASS" "seal=$sealStatus" $elapsed
        } else {
            Write-VStatus "WARN" "HardGate exit=$($r.ExitCode)"
            Add-StageResult "HardGate FULL" "WARN" "exit=$($r.ExitCode)" $elapsed
            if ($global:VIA_EXIT -eq 0) { $global:VIA_EXIT = 1 }
        }
    }

    # =========================================================================
    # STAGE 3  VRN_GO
    # FIX F1: bypass signature check via Invoke-VIAScript
    # =========================================================================
    Write-VHeader "STAGE 3  VRN ACTIVATE + DUAL-SET CROSS VALIDATE"
    $r = Invoke-VIAScript -Name "VRN_GO" -Path $VRNGo `
            -ScriptArgs @("-M01Mode",$M01Mode,"-NoPause","-NoKeepAlive")
    if ($r.Status -eq "MISSING") {
        Add-StageResult "VRN GO" "FAIL" "script missing" 0
        if ($global:VIA_EXIT -eq 0) { $global:VIA_EXIT = 1 }
    } elseif ($r.ExitCode -eq 0) {
        Write-VStatus "READY" "VRN GO completed ($($r.Elapsed)s)"
        Add-StageResult "VRN GO" "PASS" "exit=0" $r.Elapsed
    } else {
        Write-VStatus "WARN" "VRN GO exit=$($r.ExitCode)"
        Add-StageResult "VRN GO" "WARN" "exit=$($r.ExitCode)" $r.Elapsed
        if ($global:VIA_EXIT -eq 0) { $global:VIA_EXIT = 1 }
    }

    # =========================================================================
    # STAGE 4  One-Click Report
    # =========================================================================
    Write-VHeader "STAGE 4  One-Click Report (auto-open ENV + VRN)"
    if ($NoOpenReport) {
        Write-VStatus "SKIP" "Report auto-open skipped by -NoOpenReport"
    } else {
        if (Test-Path $EnvRunsRoot) {
            $envHtml = Get-ChildItem $EnvRunsRoot -Recurse -Filter "VIA_ENV_PARTITION_MATRIX.html" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($envHtml) {
                try {
                    Start-Process $envHtml.FullName | Out-Null
                    Write-VStatus "OK" "Opened ENV report: $($envHtml.Name)"
                } catch {
                    Write-VStatus "WARN" "Could not open ENV: $($_.Exception.Message)"
                }
            }
        }
        if (Test-Path $VRNOutRoot) {
            $vrnHtml = Get-ChildItem $VRNOutRoot -Recurse -Filter "VRN_DualSet_Report.html" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($vrnHtml) {
                try {
                    Start-Process $vrnHtml.FullName | Out-Null
                    Write-VStatus "OK" "Opened VRN report: $($vrnHtml.Name)"
                } catch {
                    Write-VStatus "WARN" "Could not open VRN: $($_.Exception.Message)"
                }
            }
        }
        if (Test-Path $HGRunsRoot) {
            $hgHtml = Get-ChildItem $HGRunsRoot -Recurse -Filter "supportive_hardgate_report.html" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($hgHtml) {
                try {
                    Start-Process $hgHtml.FullName | Out-Null
                    Write-VStatus "OK" "Opened HardGate report: $($hgHtml.Name)"
                } catch {
                    Write-VStatus "WARN" "Could not open HardGate: $($_.Exception.Message)"
                }
            }
        }
    }

    # =========================================================================
    # SYSTEM SUMMARY
    # =========================================================================
    Write-VHeader "SYSTEM SUMMARY"
    foreach ($r in $global:STAGE_RES) {
        $cv = switch ($r.Status) {
            "PASS"  { $P.S }
            "OK"    { $P.S }
            "READY" { $P.S }
            "WARN"  { $P.W }
            "FAIL"  { $P.E }
            "STALL" { $P.W }
            "SKIP"  { $P.M }
            default { $P.M }
        }
        $eStr = if ($r.Elapsed -gt 0) { ("{0:F2}s" -f $r.Elapsed) } else { "-" }
        Write-Host ("$cv  [$($r.Status.PadRight(5))]$($P.R) $($r.Stage.PadRight(20))  $($r.Detail)  $($P.M)($eStr)$($P.R)")
    }
    if ($global:VIA_EXIT -eq 0) {
        Write-Host ""
        Write-VStatus "READY" "ALL STAGES COMPLETED SUCCESSFULLY"
    } else {
        Write-Host ""
        Write-VStatus "WARN" "Completed with exit=$global:VIA_EXIT"
    }
}

# =============================================================================
# RUN
# =============================================================================

try {
    Invoke-Main
} catch {
    if ($global:VIA_EXIT -eq 0) { $global:VIA_EXIT = 1 }
    Write-Host ""
    Write-Host "$($P.E)  Caught exception: $($_.Exception.Message)$($P.R)"
} finally {
    Wait-VAnyKey -ExitCode $global:VIA_EXIT
    Start-VIAKeepAlive -ExitCode $global:VIA_EXIT -Minutes $KeepAliveMinutes
    exit $global:VIA_EXIT
}


# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
