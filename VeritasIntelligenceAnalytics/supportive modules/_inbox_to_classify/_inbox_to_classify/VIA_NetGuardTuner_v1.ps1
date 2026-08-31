#requires -Version 7.4
<#
.SYNOPSIS
    VIA NetGuard Tuner v1 - production-safe network analysis and tuning harness.
.DESCRIPTION
    One paste-and-run PS7 engine. Three-round panoramic flow (comprehensive ->
    sequential -> polish) over a registry of network modules. Each module has a
    read-only Probe and (optionally) a reversible Apply. Default run is DRY-RUN:
    it only probes, classifies parallel-safe vs sequential, and prints what WOULD
    change - it never mutates the system. Mutation requires -ApplySwitch, every
    mutation is preceded by an Export-Clixml snapshot, followed by a Test-Connection
    health check, and auto-rolled-back on failure. The engine never disables or
    restarts an adapter, so an interruption can never leave networking down; a
    separate -RollbackSwitch restores the latest snapshot. High-risk tuning is gated
    behind -EnableRiskySwitch and OFF by default. BBR2 congestion tuning is
    deliberately excluded (breaks loopback/Steam on Win11 23H2/24H2).
    LL-compliant: param first, [IO.File]::WriteAllText UTF8-no-BOM, no aliases,
    cuddled else/catch, no Start-Job, no exit, Write-Progress -Id 1,
    [System.Net.WebUtility]::HtmlEncode, Start-Process only to open the report.
.NOTES
    Append-only governance: snapshots are timestamped and never overwritten.
#>

param(
    [string]$ReportDir,
    [switch]$ApplySwitch,
    [switch]$EnableRiskySwitch,
    [switch]$RollbackSwitch,
    [switch]$NoOpenReportSwitch,
    [string]$PingTarget = '1.1.1.1',
    [int]$HealthTimeoutSec = 5
)
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

# ---------------------------------------------------------------------------
# Script-scoped state
# ---------------------------------------------------------------------------
$script:Stamp        = (Get-Date).ToString('yyyyMMdd_HHmmss')
$script:Root         = if ([string]::IsNullOrWhiteSpace($ReportDir)) { Join-Path $env:USERPROFILE 'VIA_NetGuard' } else { $ReportDir }
$script:WorkDir      = $script:Root
$script:ReportPath   = Join-Path $script:WorkDir ("VIA_NetGuard_Report_{0}.html" -f $script:Stamp)
$script:BackupRoot   = Join-Path $script:WorkDir '_snapshots'
$script:BackupDir    = Join-Path $script:BackupRoot $script:Stamp
$script:Utf8NoBom    = [System.Text.UTF8Encoding]::new($false)

$script:DoApply      = [bool]$ApplySwitch
$script:DoRisky      = [bool]$EnableRiskySwitch
$script:DoRollback   = [bool]$RollbackSwitch
$script:AbortApply   = $false
$script:IsAdmin      = $false
$script:PrimaryAdapter = $null
$script:Gateway      = $null
$script:Modules      = [System.Collections.Generic.List[object]]::new()
$script:Findings     = [System.Collections.Generic.List[object]]::new()
$script:RoundLog     = [System.Collections.Generic.List[object]]::new()
$script:LogLines     = [System.Collections.Generic.List[string]]::new()

# Visual Lock (VPN v3.5)
$script:ColBlue  = '#4c78a8'
$script:ColGrey  = '#9c9890'
$script:ColTeal  = '#439a9a'
$script:ColUp    = '#c96b5a'   # RED  = risk / fail (TW convention: up)
$script:ColDown  = '#5a9e6f'   # GREEN = healthy / applied ok (TW convention: down)

# Registry target for window-scaling tuning (snapshot/verify/restore)
$script:TcpipRegPath = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters'

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
function Write-NGLog {
    param([string]$Message, [string]$Level = 'INFO')
    $line = "[{0}] {1,-5} {2}" -f (Get-Date).ToString('HH:mm:ss'), $Level, $Message
    $script:LogLines.Add($line)
    $color = switch ($Level) {
        'OK'   { 'Green' }
        'WARN' { 'Yellow' }
        'RISK' { 'Red' }
        'STEP' { 'Cyan' }
        default { 'Gray' }
    }
    Write-Host $line -ForegroundColor $color
}

function Get-NGHtmlEncode {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return [System.Net.WebUtility]::HtmlEncode($Text)
}

# ---------------------------------------------------------------------------
# Environment + safety primitives
# ---------------------------------------------------------------------------
function Test-NGAdmin {
    try {
        $id = [Security.Principal.WindowsIdentity]::GetCurrent()
        $pr = [Security.Principal.WindowsPrincipal]::new($id)
        return $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Initialize-NGDirs {
    foreach ($d in @($script:WorkDir, $script:BackupRoot)) {
        if (-not (Test-Path -LiteralPath $d)) {
            New-Item -ItemType Directory -Path $d -Force | Out-Null
        }
    }
    if ($script:DoApply -and -not (Test-Path -LiteralPath $script:BackupDir)) {
        New-Item -ItemType Directory -Path $script:BackupDir -Force | Out-Null
    }
}

function Get-NGGateway {
    try {
        $routes = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop |
            Sort-Object -Property @{ e = 'RouteMetric'; desc = $false }
        $r = $routes | Select-Object -First 1
        if ($null -ne $r) { return $r.NextHop }
    } catch {
        Write-NGLog ("Gateway lookup failed: {0}" -f $_.Exception.Message) 'WARN'
    }
    return $null
}

function Test-NGHealth {
    # Non-destructive reachability probe. Returns $true only if BOTH the default
    # gateway (when known) and the external target answer within the timeout.
    $okGw = $true
    $okExt = $true
    if ($null -ne $script:Gateway) {
        try {
            $okGw = Test-Connection -TargetName $script:Gateway -Count 1 -TimeoutSeconds $HealthTimeoutSec -Quiet -ErrorAction Stop
        } catch {
            $okGw = $false
        }
    }
    try {
        $okExt = Test-Connection -TargetName $PingTarget -Count 1 -TimeoutSeconds $HealthTimeoutSec -Quiet -ErrorAction Stop
    } catch {
        $okExt = $false
    }
    return ($okGw -and $okExt)
}

function Save-NGSnapshot {
    # Capture everything a mutator could touch, once per run, before any Apply.
    if (-not $script:DoApply) { return }
    if (Test-Path -LiteralPath (Join-Path $script:BackupDir 'adapters.xml')) { return }
    Write-NGLog ("Writing snapshot -> {0}" -f $script:BackupDir) 'STEP'
    try { Get-NetAdapter -ErrorAction SilentlyContinue | Export-Clixml -Path (Join-Path $script:BackupDir 'adapters.xml') } catch { }
    try { Get-DnsClientServerAddress -ErrorAction SilentlyContinue | Export-Clixml -Path (Join-Path $script:BackupDir 'dns.xml') } catch { }
    try { Get-NetTCPSetting -ErrorAction SilentlyContinue | Export-Clixml -Path (Join-Path $script:BackupDir 'tcpsettings.xml') } catch { }
    try { Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Export-Clixml -Path (Join-Path $script:BackupDir 'routes.xml') } catch { }
    try {
        $regSnap = [ordered]@{}
        if (Test-Path -LiteralPath $script:TcpipRegPath) {
            $p = Get-ItemProperty -LiteralPath $script:TcpipRegPath -ErrorAction SilentlyContinue
            if ($null -ne $p -and $p.PSObject.Properties.Name -contains 'Tcp1323Opts') {
                $regSnap['Tcp1323Opts'] = $p.Tcp1323Opts
            } else {
                $regSnap['Tcp1323Opts'] = '__ABSENT__'
            }
        }
        $regSnap | Export-Clixml -Path (Join-Path $script:BackupDir 'registry.xml')
    } catch { }
    Write-NGLog 'Snapshot complete (append-only, never overwritten).' 'OK'
}

function Restore-NGFromSnapshot {
    # -RollbackSwitch entry point: restore DNS + registry from the most recent snapshot.
    $latest = $null
    if (Test-Path -LiteralPath $script:BackupRoot) {
        $dirs = Get-ChildItem -LiteralPath $script:BackupRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object -Property @{ e = 'Name'; desc = $true }
        $latest = $dirs | Select-Object -First 1
    }
    if ($null -eq $latest) {
        Write-NGLog 'No snapshot found to restore.' 'WARN'
        return
    }
    Write-NGLog ("Restoring from snapshot: {0}" -f $latest.FullName) 'STEP'

    $dnsXml = Join-Path $latest.FullName 'dns.xml'
    if (Test-Path -LiteralPath $dnsXml) {
        try {
            $dnsSnap = Import-Clixml -Path $dnsXml
            $byIdx = $dnsSnap | Group-Object -Property InterfaceIndex
            foreach ($g in $byIdx) {
                $idx = [int]$g.Name
                $v4 = $g.Group | Where-Object { $_.AddressFamily -eq 2 } | Select-Object -First 1
                if ($null -ne $v4) {
                    if ($null -ne $v4.ServerAddresses -and $v4.ServerAddresses.Count -gt 0) {
                        Set-DnsClientServerAddress -InterfaceIndex $idx -ServerAddresses $v4.ServerAddresses -ErrorAction SilentlyContinue
                    } else {
                        Set-DnsClientServerAddress -InterfaceIndex $idx -ResetServerAddresses -ErrorAction SilentlyContinue
                    }
                }
            }
            Write-NGLog 'DNS restored.' 'OK'
        } catch {
            Write-NGLog ("DNS restore failed: {0}" -f $_.Exception.Message) 'WARN'
        }
    }

    $regXml = Join-Path $latest.FullName 'registry.xml'
    if (Test-Path -LiteralPath $regXml) {
        try {
            $regSnap = Import-Clixml -Path $regXml
            if ($regSnap.Contains('Tcp1323Opts')) {
                $val = $regSnap['Tcp1323Opts']
                if ($val -eq '__ABSENT__') {
                    Remove-ItemProperty -LiteralPath $script:TcpipRegPath -Name 'Tcp1323Opts' -ErrorAction SilentlyContinue
                } else {
                    Set-ItemProperty -LiteralPath $script:TcpipRegPath -Name 'Tcp1323Opts' -Value $val -ErrorAction SilentlyContinue
                }
            }
            Write-NGLog 'Registry restored.' 'OK'
        } catch {
            Write-NGLog ("Registry restore failed: {0}" -f $_.Exception.Message) 'WARN'
        }
    }

    $healthy = Test-NGHealth
    if ($healthy) {
        Write-NGLog 'Post-restore health check PASSED.' 'OK'
    } else {
        Write-NGLog 'Post-restore health check FAILED - verify network manually.' 'RISK'
    }
}

# ---------------------------------------------------------------------------
# Adapter discovery (language-neutral: by InterfaceIndex, never by name string)
# ---------------------------------------------------------------------------
function Find-NGPrimaryAdapter {
    try {
        $cand = Get-NetAdapter -ErrorAction Stop |
            Where-Object {
                $_.Status -eq 'Up' -and
                $_.InterfaceDescription -notmatch 'Virtual|VMware|vEthernet|Hyper-V|TAP|VPN|Loopback|WAN Miniport' -and
                $_.Name -notmatch 'Virtual|vEthernet|VPN|Loopback'
            } |
            Sort-Object -Property @{ e = 'LinkSpeed'; desc = $true }
        $script:PrimaryAdapter = $cand | Select-Object -First 1
    } catch {
        $script:PrimaryAdapter = $null
    }
    return $script:PrimaryAdapter
}

# ---------------------------------------------------------------------------
# Module registry. Each module:
#   Id Name Round Class Risk NeedsAdmin NeedsApply NeedsRisky DependsOn
#   Probe  -> [ordered]@{ Current; Proposed; Optimal(bool); Note }
#   Apply  -> $true on success, $false on failure (only called under -ApplySwitch)
# ---------------------------------------------------------------------------
function Register-NGModule {
    param([hashtable]$Def)
    $script:Modules.Add([pscustomobject]$Def)
}

function Initialize-NGModules {
    $script:Modules.Clear()

    # ---- Round 1: comprehensive / parallel-safe / read-only or fully reversible ----

    Register-NGModule @{
        Id = 'M01'; Name = 'Locate primary physical adapter (lang-neutral, exclude virtual/VPN)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @();
        Probe = {
            $a = Find-NGPrimaryAdapter
            $r = [ordered]@{ Current = ''; Proposed = ''; Optimal = $true; Note = '' }
            if ($null -ne $a) {
                $r.Current = ("{0} (ifIndex {1}, {2})" -f $a.Name, $a.InterfaceIndex, $a.LinkSpeed)
                $r.Note = 'Primary uplink identified by InterfaceIndex.'
            } else {
                $r.Current = 'none'; $r.Optimal = $false
                $r.Note = 'No wired physical adapter Up; hardware-specific modules will self-skip.'
            }
            $r
        };
        Apply = { $true }
    }

    Register-NGModule @{
        Id = 'M02'; Name = 'Flush DNS client + resolver cache';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; NeedsAdmin = $false; NeedsApply = $true; NeedsRisky = $false; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = 'cache populated'; Proposed = 'flushed'; Optimal = $false; Note = 'Harmless, instantly self-healing.' }
            $r
        };
        Apply = {
            Clear-DnsClientCache -ErrorAction SilentlyContinue
            $true
        }
    }

    Register-NGModule @{
        Id = 'M03'; Name = 'Benchmark candidate DNS resolvers (read-only, recommend only)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @();
        Probe = {
            $cands = @('1.1.1.1', '8.8.8.8', '9.9.9.9', '168.95.1.1', '8.8.4.4')
            $rows = [System.Collections.Generic.List[string]]::new()
            $best = $null; $bestMs = [double]::MaxValue
            foreach ($c in $cands) {
                $ms = $null
                try {
                    $p = Test-Connection -TargetName $c -Count 1 -TimeoutSeconds 2 -ErrorAction Stop | Select-Object -First 1
                    if ($null -ne $p -and $p.Status -eq 'Success') { $ms = [double]$p.Latency }
                } catch {
                    $ms = $null
                }
                if ($null -eq $ms) {
                    $rows.Add(("{0}: timeout" -f $c))
                } else {
                    $rows.Add(("{0}: {1} ms" -f $c, $ms))
                    if ($ms -lt $bestMs) { $bestMs = $ms; $best = $c }
                }
            }
            $cur = ''
            if ($null -ne $script:PrimaryAdapter) {
                try {
                    $d = Get-DnsClientServerAddress -InterfaceIndex $script:PrimaryAdapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction Stop
                    if ($null -ne $d) { $cur = ($d.ServerAddresses -join ', ') }
                } catch { }
            }
            $r = [ordered]@{
                Current = ("system DNS: {0}" -f $cur)
                Proposed = if ($null -ne $best) { ("fastest: {0} ({1} ms)" -f $best, $bestMs) } else { 'no reachable candidate' }
                Optimal = $true
                Note = ($rows -join '  |  ')
            }
            $script:BestDns = $best
            $r
        };
        Apply = { $true }
    }

    Register-NGModule @{
        Id = 'M04'; Name = 'Check telemetry / CEIP scheduled task (report only by default)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = 'unknown'; Proposed = 'disabled'; Optimal = $true; Note = '' }
            try {
                $t = Get-ScheduledTask -TaskName 'Consolidator' -TaskPath '\Microsoft\Windows\Customer Experience Improvement Program\' -ErrorAction Stop
                $r.Current = ("CEIP Consolidator: {0}" -f $t.State)
                if ($t.State -ne 'Disabled') {
                    $r.Optimal = $false; $r.Note = 'Background CEIP task enabled; gated behind -EnableRiskySwitch.'
                } else {
                    $r.Note = 'Already disabled.'
                }
            } catch {
                $r.Current = 'task not present'; $r.Note = 'No CEIP Consolidator task on this build.'
            }
            $r
        };
        Apply = {
            try {
                Disable-ScheduledTask -TaskName 'Consolidator' -TaskPath '\Microsoft\Windows\Customer Experience Improvement Program\' -ErrorAction Stop | Out-Null
                return $true
            } catch {
                return $false
            }
        }
    }

    # ---- Round 2: sequential / depends on M01 / snapshot + health-checked ----

    Register-NGModule @{
        Id = 'M05'; Name = 'Set adapter DNS to fastest measured (reversible, health-checked)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @('M01', 'M03');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = ''; Optimal = $true; Note = '' }
            if ($null -eq $script:PrimaryAdapter) { $r.Note = 'No primary adapter; skipped.'; return $r }
            $cur = ''
            try {
                $d = Get-DnsClientServerAddress -InterfaceIndex $script:PrimaryAdapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction Stop
                if ($null -ne $d) { $cur = ($d.ServerAddresses -join ', ') }
            } catch { }
            $r.Current = if ([string]::IsNullOrWhiteSpace($cur)) { 'DHCP / automatic' } else { $cur }
            if ($null -ne $script:BestDns) {
                $r.Proposed = $script:BestDns
                $r.Optimal = ($cur -eq $script:BestDns)
                $r.Note = 'Static DNS pin to fastest measured resolver. Snapshot taken; auto-rollback on health fail.'
            } else {
                $r.Note = 'No faster resolver measured; keeping current.'
            }
            $r
        };
        Apply = {
            if ($null -eq $script:PrimaryAdapter -or $null -eq $script:BestDns) { return $true }
            try {
                Set-DnsClientServerAddress -InterfaceIndex $script:PrimaryAdapter.InterfaceIndex -ServerAddresses $script:BestDns -ErrorAction Stop
                return $true
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'M06'; Name = 'Enable RSS (receive-side scaling) if supported';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @('M01');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = 'RSS Enabled'; Optimal = $true; Note = '' }
            if ($null -eq $script:PrimaryAdapter) { $r.Note = 'No primary adapter; skipped.'; return $r }
            try {
                $rss = Get-NetAdapterRss -Name $script:PrimaryAdapter.Name -ErrorAction Stop
                $r.Current = ("RSS Enabled = {0}" -f $rss.Enabled)
                if (-not $rss.Enabled) {
                    $r.Optimal = $false; $r.Note = 'RSS off; enabling does not down the NIC.'
                } else {
                    $r.Note = 'Already enabled.'
                }
            } catch {
                $r.Current = 'RSS not exposed by driver'; $r.Note = 'Adapter/driver has no RSS property; will self-skip.'
            }
            $r
        };
        Apply = {
            if ($null -eq $script:PrimaryAdapter) { return $true }
            try {
                Enable-NetAdapterRss -Name $script:PrimaryAdapter.Name -ErrorAction Stop
                return $true
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'M07'; Name = 'TCP window scaling + timestamps (Tcp1323Opts, verify-after-write)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = '1 (window scaling on)'; Optimal = $true; Note = '' }
            try {
                $cur = $null
                if (Test-Path -LiteralPath $script:TcpipRegPath) {
                    $p = Get-ItemProperty -LiteralPath $script:TcpipRegPath -ErrorAction SilentlyContinue
                    if ($null -ne $p -and $p.PSObject.Properties.Name -contains 'Tcp1323Opts') { $cur = $p.Tcp1323Opts }
                }
                if ($null -eq $cur) {
                    $r.Current = 'unset (OS default applies)'; $r.Optimal = $false; $r.Note = 'Usually already optimal at OS level; low marginal value.'
                } else {
                    $r.Current = ("Tcp1323Opts = {0}" -f $cur); $r.Optimal = ($cur -eq 1)
                }
            } catch {
                $r.Current = 'read failed'; $r.Note = $_.Exception.Message
            }
            $r
        };
        Apply = {
            try {
                Set-ItemProperty -LiteralPath $script:TcpipRegPath -Name 'Tcp1323Opts' -Value 1 -Type DWord -ErrorAction Stop
                $chk = (Get-ItemProperty -LiteralPath $script:TcpipRegPath -ErrorAction SilentlyContinue).Tcp1323Opts
                if ($chk -ne 1) {
                    Write-NGLog 'Tcp1323Opts write did not stick (third-party security software lock?).' 'RISK'
                    return $false
                }
                return $true
            } catch {
                return $false
            }
        }
    }

    # ---- Round 3: polish / verification ----

    Register-NGModule @{
        Id = 'M08'; Name = 'Final state verification + health snapshot';
        Round = 3; Class = 'Sequential'; Risk = 'Low'; NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @('M01');
        Probe = {
            $healthy = Test-NGHealth
            $r = [ordered]@{
                Current = if ($healthy) { 'gateway + external reachable' } else { 'reachability degraded' }
                Proposed = 'healthy'
                Optimal = $healthy
                Note = if ($healthy) { 'Network path verified end-to-end.' } else { 'Health check failed - consider -RollbackSwitch.' }
            }
            $r
        };
        Apply = { $true }
    }

    # ---- Deliberately excluded (shown in report, never executed) ----
    $script:Excluded = @(
        [pscustomobject]@{ Name = 'BBR2 congestion provider'; Reason = 'Breaks loopback/localhost TCP on Win11 23H2/24H2 (kills your VRN ControlCenter :7788 / HttpListener); also read-only via Set-NetTCPSetting. Use netsh manually only if you accept the risk.' }
        [pscustomobject]@{ Name = 'Hardcode MTU 1500/9000'; Reason = 'PMTU black-hole risk; reliable set path is per-driver Jumbo Packet, not a universal MTU write. Left to manual tuning.' }
        [pscustomobject]@{ Name = 'Disable EEE / green Ethernet'; Reason = 'Some older NIC drivers BSOD on toggle; near-zero real-world gain. Excluded on a production host.' }
        [pscustomobject]@{ Name = 'Disable/restart adapter'; Reason = 'Any NIC-down window can strand a remote/production host. This engine never downs an adapter by design.' }
    )
}

# ---------------------------------------------------------------------------
# Classification + ordering (parallel-safe vs sequential / dependency aware)
# ---------------------------------------------------------------------------
function Get-NGOrdered {
    # Stable order: Round asc, then Sequential after Parallel within a round,
    # then dependencies before dependents (simple Kahn over DependsOn).
    $byId = @{}
    foreach ($m in $script:Modules) { $byId[$m.Id] = $m }
    $ordered = [System.Collections.Generic.List[object]]::new()
    $visited = [System.Collections.Generic.HashSet[string]]::new()

    $rounds = $script:Modules | ForEach-Object { $_.Round } | Sort-Object -Unique
    foreach ($rd in $rounds) {
        $inRound = $script:Modules |
            Where-Object { $_.Round -eq $rd } |
            Sort-Object -Property @{ e = 'Class'; desc = $false }, @{ e = 'Id'; desc = $false }
        # ascending Class puts 'Parallel' before 'Sequential' -> parallel-safe first within a round
        foreach ($m in $inRound) {
            $stack = [System.Collections.Generic.Stack[object]]::new()
            $stack.Push($m)
            while ($stack.Count -gt 0) {
                $top = $stack.Peek()
                $pending = @()
                foreach ($dep in $top.DependsOn) {
                    if ($byId.ContainsKey($dep) -and -not $visited.Contains($dep)) { $pending += $dep }
                }
                if ($pending.Count -eq 0) {
                    [void]$stack.Pop()
                    if (-not $visited.Contains($top.Id)) {
                        [void]$visited.Add($top.Id)
                        $ordered.Add($top)
                    }
                } else {
                    foreach ($dep in $pending) { $stack.Push($byId[$dep]) }
                }
            }
        }
    }
    return $ordered
}

# ---------------------------------------------------------------------------
# Single-module execution: probe always; apply only when permitted + safe
# ---------------------------------------------------------------------------
function Invoke-NGModule {
    param([object]$Module, [int]$RoundTag)

    $probe = $null
    try {
        $probe = & $Module.Probe
    } catch {
        $probe = [ordered]@{ Current = 'probe error'; Proposed = ''; Optimal = $false; Note = $_.Exception.Message }
    }

    $status = 'INFO'
    $color  = $script:ColGrey

    if (-not $Module.NeedsApply) {
        if ($probe.Optimal) {
            $status = 'OK'; $color = $script:ColDown
        } else {
            $status = 'INFO'; $color = $script:ColGrey
        }
    } elseif ($probe.Optimal) {
        $status = 'OK'; $color = $script:ColDown
    } elseif (-not $script:DoApply) {
        $status = 'DRY'; $color = $script:ColBlue
    } elseif ($Module.NeedsRisky -and -not $script:DoRisky) {
        $status = 'SKIP'; $color = $script:ColGrey
    } elseif ($Module.NeedsAdmin -and -not $script:IsAdmin) {
        $status = 'NO-ADMIN'; $color = $script:ColGrey
    } elseif ($script:AbortApply) {
        $status = 'HALTED'; $color = $script:ColGrey
    } else {
        Save-NGSnapshot
        $ok = $false
        try {
            $ok = [bool](& $Module.Apply)
        } catch {
            $ok = $false
            $probe.Note = ("{0} | apply error: {1}" -f $probe.Note, $_.Exception.Message)
        }
        if (-not $ok) {
            $status = 'FAIL'; $color = $script:ColUp
        } else {
            $healthy = Test-NGHealth
            if ($healthy) {
                $status = 'APPLIED'; $color = $script:ColDown
            } else {
                Write-NGLog ("Health FAILED after {0}; rolling back and halting further applies." -f $Module.Id) 'RISK'
                Restore-NGFromSnapshot
                $script:AbortApply = $true
                $status = 'ROLLED-BACK'; $color = $script:ColUp
            }
        }
    }

    $row = [pscustomobject]@{
        Id = $Module.Id; Name = $Module.Name; Round = $Module.Round; Class = $Module.Class; Risk = $Module.Risk
        Status = $status; Color = $color
        Current = [string]$probe.Current; Proposed = [string]$probe.Proposed; Note = [string]$probe.Note
    }
    $script:Findings.Add($row)
    $logLevel = 'INFO'
    if ($status -in @('FAIL', 'ROLLED-BACK')) { $logLevel = 'RISK' }
    Write-NGLog ("{0} [{1}] {2}" -f $Module.Id, $status, $Module.Name) $logLevel
    return $row
}

# ---------------------------------------------------------------------------
# Three-round panoramic cycle
# ---------------------------------------------------------------------------
function Invoke-NGThreeRoundCycle {
    $ordered = Get-NGOrdered
    $total = $ordered.Count
    $done = 0
    $roundNames = @{ 1 = 'R1 comprehensive (parallel-safe)'; 2 = 'R2 sequential (dependency-ordered)'; 3 = 'R3 polish (verify)' }

    foreach ($rd in @(1, 2, 3)) {
        $modsThis = $ordered | Where-Object { $_.Round -eq $rd }
        if (($modsThis | Measure-Object).Count -eq 0) { continue }
        Write-NGLog ("=== {0} ===" -f $roundNames[$rd]) 'STEP'
        $appliedCount = 0; $failCount = 0
        foreach ($m in $modsThis) {
            $done++
            $pct = [int](($done / [Math]::Max($total, 1)) * 100)
            Write-Progress -Id 1 -Activity 'VIA NetGuard - panoramic cycle' -Status ("{0} :: {1}" -f $roundNames[$rd], $m.Id) -PercentComplete $pct
            $row = Invoke-NGModule -Module $m -RoundTag $rd
            if ($row.Status -eq 'APPLIED') { $appliedCount++ }
            if ($row.Status -in @('FAIL', 'ROLLED-BACK')) { $failCount++ }
        }
        $script:RoundLog.Add([pscustomobject]@{
            Round = $rd; Name = $roundNames[$rd]
            Modules = ($modsThis | Measure-Object).Count
            Applied = $appliedCount; Failed = $failCount
            Aborted = $script:AbortApply
        })
        if ($script:AbortApply) {
            Write-NGLog 'Regression guard tripped: halting further mutation, continuing to report.' 'RISK'
        }
    }
    Write-Progress -Id 1 -Activity 'VIA NetGuard - panoramic cycle' -Completed
}

# ---------------------------------------------------------------------------
# HTML matrix report (Visual Lock)
# ---------------------------------------------------------------------------
function Build-NGMatrixRows {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($f in $script:Findings) {
        $badge = ("<span class='badge' style='background:{0}'>{1}</span>" -f $f.Color, (Get-NGHtmlEncode $f.Status))
        [void]$sb.AppendLine('<tr>')
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Id)))
        [void]$sb.AppendLine(("<td>{0}</td>" -f (Get-NGHtmlEncode $f.Name)))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode ([string]$f.Round))))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Class)))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Risk)))
        [void]$sb.AppendLine(("<td>{0}</td>" -f $badge))
        [void]$sb.AppendLine(("<td class='mono small'>{0}</td>" -f (Get-NGHtmlEncode $f.Current)))
        [void]$sb.AppendLine(("<td class='mono small'>{0}</td>" -f (Get-NGHtmlEncode $f.Proposed)))
        [void]$sb.AppendLine(("<td class='small'>{0}</td>" -f (Get-NGHtmlEncode $f.Note)))
        [void]$sb.AppendLine('</tr>')
    }
    return $sb.ToString()
}

function Build-NGRoundRows {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($r in $script:RoundLog) {
        $ab = 'no'
        if ($r.Aborted) { $ab = 'YES' }
        [void]$sb.AppendLine('<tr>')
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode ([string]$r.Round))))
        [void]$sb.AppendLine(("<td>{0}</td>" -f (Get-NGHtmlEncode $r.Name)))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $r.Modules))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $r.Applied))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $r.Failed))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $ab))
        [void]$sb.AppendLine('</tr>')
    }
    return $sb.ToString()
}

function Build-NGExcludedRows {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($e in $script:Excluded) {
        [void]$sb.AppendLine('<tr>')
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $e.Name)))
        [void]$sb.AppendLine(("<td class='small'>{0}</td>" -f (Get-NGHtmlEncode $e.Reason)))
        [void]$sb.AppendLine('</tr>')
    }
    return $sb.ToString()
}

function New-NGReport {
    $mode = 'DRY-RUN (no system changes)'
    if ($script:DoApply) {
        $mode = 'APPLY'
        if ($script:DoRisky) { $mode = 'APPLY + RISKY' }
    }
    $adapter = 'none'
    if ($null -ne $script:PrimaryAdapter) {
        $adapter = ("{0} (ifIndex {1}, {2})" -f $script:PrimaryAdapter.Name, $script:PrimaryAdapter.InterfaceIndex, $script:PrimaryAdapter.LinkSpeed)
    }
    $adminTxt = 'no'
    if ($script:IsAdmin) { $adminTxt = 'yes' }
    $gw = 'unknown'
    if ($null -ne $script:Gateway) { $gw = $script:Gateway }

    $tpl = @'
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA NetGuard Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;700;800&display=swap');
:root{ --blue:@@BLUE@@; --grey:@@GREY@@; --teal:@@TEAL@@; --up:@@UP@@; --down:@@DOWN@@; }
*{ box-sizing:border-box; }
body{ margin:0; padding:36px; background:#13161a; color:#e7e9ec; font-family:'DM Sans',sans-serif; }
h1{ font-family:'Syne',sans-serif; font-weight:800; font-size:26px; margin:0 0 4px; color:#fff; letter-spacing:.5px; }
.sub{ color:var(--grey); font-size:13px; margin-bottom:22px; }
.meta{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:26px; }
.chip{ background:#1b1f24; border:1px solid #2a2f36; border-radius:8px; padding:8px 14px; font-size:12px; }
.chip b{ color:var(--teal); font-family:'DM Mono',monospace; }
.mode{ display:inline-block; padding:6px 16px; border-radius:20px; font-weight:700; font-size:13px; color:#13161a; background:var(--teal); }
.mode.apply{ background:var(--up); color:#fff; }
h2{ font-family:'Syne',sans-serif; font-weight:700; font-size:17px; color:var(--blue); border-bottom:1px solid #2a2f36; padding-bottom:8px; margin:30px 0 12px; }
table{ border-collapse:collapse; width:100%; background:#171b20; border:1px solid #2a2f36; border-radius:10px; overflow:hidden; margin-bottom:10px; }
th{ background:#1d2228; color:var(--teal); text-align:left; padding:11px 12px; font-size:12px; font-family:'DM Mono',monospace; border-bottom:1px solid #2a2f36; }
td{ padding:10px 12px; font-size:13px; border-bottom:1px solid #23282e; vertical-align:top; }
tr:last-child td{ border-bottom:none; }
tr:hover td{ background:#1b2026; }
.mono{ font-family:'DM Mono',monospace; }
.small{ font-size:11.5px; color:#b9bdc3; }
.badge{ display:inline-block; padding:3px 10px; border-radius:12px; color:#13161a; font-weight:700; font-size:11px; font-family:'DM Mono',monospace; }
.foot{ color:var(--grey); font-size:11px; margin-top:24px; }
.legend span{ display:inline-block; margin-right:14px; font-size:11px; color:var(--grey); }
.dot{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }
</style>
</head>
<body>
<h1>VIA NetGuard Tuner</h1>
<div class="sub">production-safe panoramic network analysis &mdash; 判天地之美，析萬物之理</div>
<div><span class="mode @@MODECLS@@">@@MODE@@</span></div>
<div class="meta" style="margin-top:16px;">
  <div class="chip">generated <b>@@GENERATED@@</b></div>
  <div class="chip">admin <b>@@ADMIN@@</b></div>
  <div class="chip">primary uplink <b>@@ADAPTER@@</b></div>
  <div class="chip">gateway <b>@@GATEWAY@@</b></div>
  <div class="chip">snapshot <b>@@BACKUP@@</b></div>
</div>

<h2>Round summary</h2>
<table>
<thead><tr><th>#</th><th>round</th><th>modules</th><th>applied</th><th>failed</th><th>aborted</th></tr></thead>
<tbody>@@ROUNDROWS@@</tbody>
</table>

<h2>Module matrix</h2>
<div class="legend" style="margin-bottom:8px;">
  <span><i class="dot" style="background:@@DOWN@@"></i>OK / APPLIED</span>
  <span><i class="dot" style="background:@@BLUE@@"></i>DRY (would change)</span>
  <span><i class="dot" style="background:@@GREY@@"></i>SKIP / NO-ADMIN / INFO</span>
  <span><i class="dot" style="background:@@UP@@"></i>FAIL / ROLLED-BACK</span>
</div>
<table>
<thead><tr><th>id</th><th>module</th><th>rd</th><th>class</th><th>risk</th><th>status</th><th>current</th><th>proposed</th><th>note</th></tr></thead>
<tbody>@@MATRIXROWS@@</tbody>
</table>

<h2>Deliberately excluded (not executed)</h2>
<table>
<thead><tr><th>item</th><th>why it is off on a production host</th></tr></thead>
<tbody>@@EXCLROWS@@</tbody>
</table>

<div class="foot">
DRY-RUN changes nothing. To apply low-risk reversible modules: re-run with <code>-ApplySwitch</code>.
To also apply gated medium-risk tuning: add <code>-EnableRiskySwitch</code>. To restore the latest snapshot: <code>-RollbackSwitch</code>.
Every mutation is snapshotted, health-checked, and auto-rolled-back on failure. This engine never disables or restarts an adapter.
</div>
</body>
</html>
'@

    $html = $tpl
    $modeCls = ''
    if ($script:DoApply) { $modeCls = 'apply' }
    $html = $html.Replace('@@BLUE@@', $script:ColBlue)
    $html = $html.Replace('@@GREY@@', $script:ColGrey)
    $html = $html.Replace('@@TEAL@@', $script:ColTeal)
    $html = $html.Replace('@@UP@@', $script:ColUp)
    $html = $html.Replace('@@DOWN@@', $script:ColDown)
    $html = $html.Replace('@@MODECLS@@', $modeCls)
    $html = $html.Replace('@@MODE@@', (Get-NGHtmlEncode $mode))
    $html = $html.Replace('@@GENERATED@@', (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))
    $html = $html.Replace('@@ADMIN@@', (Get-NGHtmlEncode $adminTxt))
    $html = $html.Replace('@@ADAPTER@@', (Get-NGHtmlEncode $adapter))
    $html = $html.Replace('@@GATEWAY@@', (Get-NGHtmlEncode $gw))
    $backupShown = 'n/a (dry-run)'
    if ($script:DoApply) { $backupShown = $script:BackupDir }
    $html = $html.Replace('@@BACKUP@@', (Get-NGHtmlEncode $backupShown))
    $html = $html.Replace('@@ROUNDROWS@@', (Build-NGRoundRows))
    $html = $html.Replace('@@MATRIXROWS@@', (Build-NGMatrixRows))
    $html = $html.Replace('@@EXCLROWS@@', (Build-NGExcludedRows))

    [IO.File]::WriteAllText($script:ReportPath, $html, $script:Utf8NoBom)
    Write-NGLog ("Report written: {0}" -f $script:ReportPath) 'OK'
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function Start-NGEngine {
    Write-Host ''
    Write-Host '==================================================' -ForegroundColor Cyan
    Write-Host ' VIA NetGuard Tuner v1  (production-safe edition)  ' -ForegroundColor Cyan
    Write-Host '==================================================' -ForegroundColor Cyan

    Initialize-NGDirs
    $script:IsAdmin = Test-NGAdmin
    $script:Gateway = Get-NGGateway

    if (-not $script:IsAdmin) {
        Write-NGLog 'Not elevated: read-only probes run; admin-only mutations will self-skip (no elevation forced).' 'WARN'
    }

    if ($script:DoRollback) {
        Write-NGLog 'Rollback mode: restoring latest snapshot, no analysis.' 'STEP'
        Restore-NGFromSnapshot
        return
    }

    if ($script:DoApply) {
        Write-NGLog 'APPLY mode: mutations are snapshotted + health-checked + auto-rolled-back on failure.' 'STEP'
    } else {
        Write-NGLog 'DRY-RUN mode: probing only, nothing on the system will be changed.' 'STEP'
    }

    Initialize-NGModules
    $null = Find-NGPrimaryAdapter
    Invoke-NGThreeRoundCycle
    New-NGReport

    if (-not $NoOpenReportSwitch) {
        try {
            Start-Process $script:ReportPath | Out-Null
        } catch {
            Write-NGLog ("Could not auto-open report: {0}" -f $_.Exception.Message) 'WARN'
        }
    }
    Write-Host ''
    Write-NGLog 'Done.' 'OK'
}

Start-NGEngine

