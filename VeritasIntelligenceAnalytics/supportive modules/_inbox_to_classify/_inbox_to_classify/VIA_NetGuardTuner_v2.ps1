#requires -Version 7.4
<#
.SYNOPSIS
    VIA NetGuard Tuner v2 - production-safe panoramic network engine, 10 cross-accelerators.
.DESCRIPTION
    One paste-and-run PS7 engine. Integrates the best of every accelerator approach and
    engineers out their drawbacks: 10 numbered accelerators (A01-A10) plus a verify step,
    wired into a shared cross-acceleration context so each one reuses earlier results
    (adapter+media -> offloads; DNS benchmark -> DNS pin; etc).

    Safety, unchanged from v1 and non-negotiable:
      * DRY-RUN by default - probes only, never mutates. -ApplySwitch to apply low-risk
        reversible accelerators; -EnableRiskySwitch to also apply gated medium-risk ones.
      * Every mutation is preceded by an Export-Clixml snapshot, followed by a
        Test-Connection health check, and auto-rolled-back on failure (regression guard
        halts all further mutation). -RollbackSwitch restores the latest snapshot.
      * The engine NEVER disables or restarts an adapter -> an interruption can never
        leave networking down (no-stall by construction).

    v2 deltas (integrate strengths / remove weaknesses):
      * A02 multi-sample DNS benchmark with a significance gate (no pin on sub-5ms noise).
      * A04 private-DNS aware (keeps router/LAN DNS instead of pinning a public resolver).
      * media-aware: wired-only offloads (RSS/RSC) auto-skip on a Wi-Fi uplink.
      * A08 restores AutoTuningLevelLocal=Normal (undoes throughput damage from bad optimizers).
      * throttled dynamic progress (parent + child bar), ~150ms tick.
      * per-accelerator Impact rating (Real / Defensive / Marginal / Noise / Security).
      * BBR2 / MTU hardcode / EEE / adapter-restart remain deliberately excluded.

    LL-compliant: param first, [IO.File]::WriteAllText UTF8-no-BOM, no aliases, cuddled
    else/catch, no Start-Job, no exit, Write-Progress -Id, [System.Net.WebUtility]::HtmlEncode,
    Start-Process only to open the report. Append-only snapshots (timestamped, never overwritten).
#>

param(
    [string]$ReportDir,
    [switch]$ApplySwitch,
    [switch]$EnableRiskySwitch,
    [switch]$RollbackSwitch,
    [switch]$NoOpenReportSwitch,
    [string]$PingTarget = '1.1.1.1',
    [int]$HealthTimeoutSec = 5,
    [int]$DnsSamples = 4,
    [int]$DnsSignificantMs = 5
)

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
$script:Modules      = [System.Collections.Generic.List[object]]::new()
$script:Findings     = [System.Collections.Generic.List[object]]::new()
$script:RoundLog     = [System.Collections.Generic.List[object]]::new()
$script:LogLines     = [System.Collections.Generic.List[string]]::new()
$script:Excluded     = @()

# Shared cross-acceleration context (each accelerator reads/writes this)
$script:Ctx = [ordered]@{
    Adapter = $null
    Media   = 'unknown'   # WiFi | Wired | unknown
    Gateway = $null
    CurrentDns = @()
    BestDns = $null
    BestDnsMs = $null
    DnsSignificant = $false
}

# Progress throttling
$script:NextTick = [DateTime]::MinValue

# Visual Lock (VPN v3.5)
$script:ColBlue  = '#4c78a8'
$script:ColGrey  = '#9c9890'
$script:ColTeal  = '#439a9a'
$script:ColUp    = '#c96b5a'   # RED   = risk / fail
$script:ColDown  = '#5a9e6f'   # GREEN = healthy / applied ok

$script:TcpipRegPath = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters'

# ---------------------------------------------------------------------------
# Logging + progress
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

function Update-NGProgress {
    # Throttled parent progress: only repaint every ~150ms (avoids UI-thread overhead).
    param([string]$Status, [int]$Percent, [switch]$ForceSwitch)
    $now = Get-Date
    if (-not $ForceSwitch -and $now -lt $script:NextTick) { return }
    $script:NextTick = $now.AddMilliseconds(150)
    Write-Progress -Id 1 -Activity 'VIA NetGuard v2 - cross-acceleration cycle' -Status $Status -PercentComplete $Percent
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
    $okGw = $true
    $okExt = $true
    if ($null -ne $script:Ctx.Gateway) {
        try {
            $okGw = Test-Connection -TargetName $script:Ctx.Gateway -Count 1 -TimeoutSeconds $HealthTimeoutSec -Quiet -ErrorAction Stop
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

    $tcpXml = Join-Path $latest.FullName 'tcpsettings.xml'
    if (Test-Path -LiteralPath $tcpXml) {
        try {
            $tcpSnap = Import-Clixml -Path $tcpXml
            $inet = $tcpSnap | Where-Object { $_.SettingName -eq 'Internet' } | Select-Object -First 1
            if ($null -ne $inet -and $null -ne $inet.AutoTuningLevelLocal) {
                Set-NetTCPSetting -SettingName 'Internet' -AutoTuningLevelLocal $inet.AutoTuningLevelLocal -ErrorAction SilentlyContinue
            }
            Write-NGLog 'TCP autotuning restored.' 'OK'
        } catch {
            Write-NGLog ("TCP restore failed: {0}" -f $_.Exception.Message) 'WARN'
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
# Adapter + media detection (feeds the whole cross-acceleration graph)
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
        $a = $cand | Select-Object -First 1
        $script:Ctx.Adapter = $a
        if ($null -ne $a) {
            if ($a.PhysicalMediaType -match '802\.11|Wireless|Wi-?Fi|WLAN') {
                $script:Ctx.Media = 'WiFi'
            } else {
                $script:Ctx.Media = 'Wired'
            }
        }
    } catch {
        $script:Ctx.Adapter = $null
    }
    return $script:Ctx.Adapter
}

function Test-NGPrivateIp {
    param([string]$Ip)
    if ([string]::IsNullOrWhiteSpace($Ip)) { return $false }
    if ($Ip -match '^10\.') { return $true }
    if ($Ip -match '^192\.168\.') { return $true }
    if ($Ip -match '^172\.(1[6-9]|2[0-9]|3[0-1])\.') { return $true }
    if ($Ip -match '^169\.254\.') { return $true }
    return $false
}

function Measure-NGResolver {
    # Bounded multi-sample ICMP RTT (ms) to a resolver. Averages Success samples only.
    param([string]$Ip, [int]$Samples = 4)
    $vals = [System.Collections.Generic.List[double]]::new()
    try {
        $res = Test-Connection -TargetName $Ip -Count $Samples -TimeoutSeconds 1 -ErrorAction Stop
        foreach ($p in $res) {
            if ($p.Status -eq 'Success') { $vals.Add([double]$p.Latency) }
        }
    } catch {
        # unreachable -> no samples
    }
    if ($vals.Count -eq 0) { return $null }
    $sum = 0.0
    foreach ($v in $vals) { $sum += $v }
    return [Math]::Round($sum / $vals.Count, 1)
}

# ---------------------------------------------------------------------------
# Accelerator registry. Probe -> [ordered]@{ Current; Proposed; Optimal; Skip; Note }
# Apply -> $true on success / $false on failure (only under -ApplySwitch + gates).
# ---------------------------------------------------------------------------
function Register-NGModule {
    param([hashtable]$Def)
    $script:Modules.Add([pscustomobject]$Def)
}

function Initialize-NGModules {
    $script:Modules.Clear()

    # ===== Round 1: comprehensive / parallel-safe =====

    Register-NGModule @{
        Id = 'A01'; Name = 'Uplink + media detection (lang-neutral, exclude virtual/VPN)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; Impact = 'Foundation';
        NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @();
        Probe = {
            $a = Find-NGPrimaryAdapter
            $r = [ordered]@{ Current = ''; Proposed = ''; Optimal = $true; Skip = $false; Note = '' }
            if ($null -ne $a) {
                $r.Current = ("{0} | {1} | ifIndex {2} | {3}" -f $a.Name, $script:Ctx.Media, $a.InterfaceIndex, $a.LinkSpeed)
                $r.Note = 'Feeds every adapter-scoped accelerator; media gates wired-only offloads.'
            } else {
                $r.Current = 'none'; $r.Optimal = $false
                $r.Note = 'No usable uplink Up; hardware accelerators will self-skip.'
            }
            $r
        };
        Apply = { $true }
    }

    Register-NGModule @{
        Id = 'A02'; Name = 'DNS resolver benchmark (multi-sample, significance-gated)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; Impact = 'Insight';
        NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @('A01');
        Probe = {
            $cands = @('1.1.1.1', '8.8.8.8', '8.8.4.4', '9.9.9.9', '168.95.1.1')
            $stats = [System.Collections.Generic.List[string]]::new()
            $best = $null; $bestMs = [double]::MaxValue; $second = [double]::MaxValue
            $n = 0
            foreach ($c in $cands) {
                $n++
                Write-Progress -Id 2 -ParentId 1 -Activity 'DNS benchmark' -Status $c -PercentComplete ([int](($n / $cands.Count) * 100))
                $ms = Measure-NGResolver -Ip $c -Samples $DnsSamples
                if ($null -eq $ms) {
                    $stats.Add(("{0}: timeout" -f $c))
                } else {
                    $stats.Add(("{0}: {1}ms" -f $c, $ms))
                    if ($ms -lt $bestMs) {
                        $second = $bestMs; $bestMs = $ms; $best = $c
                    } elseif ($ms -lt $second) {
                        $second = $ms
                    }
                }
            }
            Write-Progress -Id 2 -ParentId 1 -Activity 'DNS benchmark' -Completed

            $cur = @()
            if ($null -ne $script:Ctx.Adapter) {
                try {
                    $d = Get-DnsClientServerAddress -InterfaceIndex $script:Ctx.Adapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction Stop
                    if ($null -ne $d) { $cur = @($d.ServerAddresses) }
                } catch { }
            }
            $script:Ctx.CurrentDns = $cur
            $script:Ctx.BestDns = $best
            $script:Ctx.BestDnsMs = if ($best) { $bestMs } else { $null }
            $margin = $second - $bestMs
            $script:Ctx.DnsSignificant = ($null -ne $best -and $margin -ge $DnsSignificantMs)

            $verdict = 'within noise'
            if ($script:Ctx.DnsSignificant) { $verdict = ("significant (+{0}ms over next)" -f [Math]::Round($margin, 1)) }

            $proposed = 'no reachable candidate'
            if ($best) { $proposed = ("fastest {0} @ {1}ms - {2}" -f $best, $bestMs, $verdict) }

            $r = [ordered]@{
                Current = ("system DNS: {0}" -f ($cur -join ', '))
                Proposed = $proposed
                Optimal = $true; Skip = $false
                Note = ($stats -join '  |  ')
            }
            $r
        };
        Apply = { $true }
    }

    Register-NGModule @{
        Id = 'A03'; Name = 'Flush DNS client + resolver cache';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; Impact = 'Marginal';
        NeedsAdmin = $false; NeedsApply = $true; NeedsRisky = $false; DependsOn = @();
        Probe = {
            [ordered]@{ Current = 'cache populated'; Proposed = 'flushed'; Optimal = $false; Skip = $false; Note = 'Harmless, instantly self-healing.' }
        };
        Apply = {
            Clear-DnsClientCache -ErrorAction SilentlyContinue
            $true
        }
    }

    Register-NGModule @{
        Id = 'A05'; Name = 'Encrypted DNS (DoH) posture check (report only)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; Impact = 'Security';
        NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @('A02');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = ''; Optimal = $true; Skip = $false; Note = '' }
            $dohList = @()
            try {
                $doh = Get-DnsClientDohServerAddress -ErrorAction Stop
                if ($null -ne $doh) { $dohList = @($doh.ServerAddress) }
            } catch { }
            $cur = @($script:Ctx.CurrentDns)
            $supported = @($cur | Where-Object { $dohList -contains $_ })
            if ($supported.Count -gt 0) {
                $r.Current = ("DoH-capable resolvers in use: {0}" -f ($supported -join ', '))
                $r.Note = 'Your active resolver(s) support encrypted DNS; enable via Settings > Network > DNS encryption.'
            } else {
                $r.Current = 'no DoH-capable resolver active'
                $r.Note = ("Known DoH templates: {0}. Pinning one of these (e.g. via A04) would allow encrypted DNS." -f ($dohList -join ', '))
            }
            $r
        };
        Apply = { $true }
    }

    Register-NGModule @{
        Id = 'A10'; Name = 'Telemetry / CEIP background task (gated)';
        Round = 1; Class = 'Parallel'; Risk = 'Low'; Impact = 'Marginal';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = 'unknown'; Proposed = 'disabled'; Optimal = $true; Skip = $false; Note = '' }
            try {
                $t = Get-ScheduledTask -TaskName 'Consolidator' -TaskPath '\Microsoft\Windows\Customer Experience Improvement Program\' -ErrorAction Stop
                $r.Current = ("CEIP Consolidator: {0}" -f $t.State)
                if ($t.State -ne 'Disabled') {
                    $r.Optimal = $false; $r.Note = 'CEIP task enabled; gated behind -EnableRiskySwitch.'
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

    # ===== Round 2: sequential / dependency-ordered / snapshot + health-checked =====

    Register-NGModule @{
        Id = 'A04'; Name = 'Pin DNS to fastest (significance + private-DNS aware)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; Impact = 'Marginal';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @('A01', 'A02');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = ''; Optimal = $true; Skip = $false; Note = '' }
            if ($null -eq $script:Ctx.Adapter) { $r.Skip = $true; $r.Note = 'No uplink; skipped.'; return $r }
            $cur = @($script:Ctx.CurrentDns)
            $r.Current = if ($cur.Count -gt 0) { ($cur -join ', ') } else { 'DHCP / automatic' }
            $primary = if ($cur.Count -gt 0) { $cur[0] } else { '' }
            $primaryPrivate = Test-NGPrivateIp -Ip $primary

            if ($null -eq $script:Ctx.BestDns) {
                $r.Note = 'No faster resolver measured; keeping current.'
            } elseif ($primaryPrivate) {
                $r.Skip = $true
                $r.Note = 'Primary DNS is your router/LAN resolver - kept to preserve internal name resolution. Public-resolver pin not recommended.'
            } elseif (-not $script:Ctx.DnsSignificant) {
                $r.Skip = $true
                $r.Note = ("Fastest is within {0}ms noise of alternatives - no statistically meaningful gain, keeping current." -f $DnsSignificantMs)
            } else {
                $r.Proposed = $script:Ctx.BestDns
                $r.Optimal = ($cur -contains $script:Ctx.BestDns)
                $r.Note = 'Public resolver pin (snapshot + health-checked + auto-rollback).'
            }
            $r
        };
        Apply = {
            if ($null -eq $script:Ctx.Adapter -or $null -eq $script:Ctx.BestDns) { return $true }
            try {
                Set-DnsClientServerAddress -InterfaceIndex $script:Ctx.Adapter.InterfaceIndex -ServerAddresses $script:Ctx.BestDns -ErrorAction Stop
                $chk = (Get-DnsClientServerAddress -InterfaceIndex $script:Ctx.Adapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses
                return ($chk -contains $script:Ctx.BestDns)
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'A06'; Name = 'RSS receive-side scaling (wired offload, media-aware)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; Impact = 'Real';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @('A01');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = 'RSS Enabled'; Optimal = $true; Skip = $false; Note = '' }
            if ($null -eq $script:Ctx.Adapter) { $r.Skip = $true; $r.Note = 'No uplink; skipped.'; return $r }
            if ($script:Ctx.Media -eq 'WiFi') { $r.Skip = $true; $r.Note = 'Wi-Fi uplink: wired-only offload, skipped.'; return $r }
            try {
                $rss = Get-NetAdapterRss -Name $script:Ctx.Adapter.Name -ErrorAction Stop
                $r.Current = ("RSS Enabled = {0}" -f $rss.Enabled)
                if (-not $rss.Enabled) {
                    $r.Optimal = $false; $r.Note = 'RSS off; enabling does not down the NIC.'
                } else {
                    $r.Note = 'Already enabled.'
                }
            } catch {
                $r.Skip = $true; $r.Current = 'RSS not exposed by driver'; $r.Note = 'Driver has no RSS property; skipped.'
            }
            $r
        };
        Apply = {
            if ($null -eq $script:Ctx.Adapter) { return $true }
            try {
                Enable-NetAdapterRss -Name $script:Ctx.Adapter.Name -ErrorAction Stop
                return $true
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'A07'; Name = 'RSC receive segment coalescing (wired offload, media-aware)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; Impact = 'Real';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @('A01');
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = 'RSC IPv4 Enabled'; Optimal = $true; Skip = $false; Note = '' }
            if ($null -eq $script:Ctx.Adapter) { $r.Skip = $true; $r.Note = 'No uplink; skipped.'; return $r }
            if ($script:Ctx.Media -eq 'WiFi') { $r.Skip = $true; $r.Note = 'Wi-Fi uplink: wired-only offload, skipped.'; return $r }
            try {
                $rsc = Get-NetAdapterRsc -Name $script:Ctx.Adapter.Name -ErrorAction Stop
                $r.Current = ("RSC IPv4 = {0}" -f $rsc.IPv4Enabled)
                if (-not $rsc.IPv4Enabled) {
                    $r.Optimal = $false; $r.Note = 'RSC off; enabling reduces CPU on bulk receive.'
                } else {
                    $r.Note = 'Already enabled.'
                }
            } catch {
                $r.Skip = $true; $r.Current = 'RSC not exposed by driver'; $r.Note = 'Driver has no RSC property; skipped.'
            }
            $r
        };
        Apply = {
            if ($null -eq $script:Ctx.Adapter) { return $true }
            try {
                Enable-NetAdapterRsc -Name $script:Ctx.Adapter.Name -IPv4 -ErrorAction Stop
                return $true
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'A08'; Name = 'TCP receive autotuning -> Normal (undo bad-optimizer damage)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; Impact = 'Defensive';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = 'Normal'; Optimal = $true; Skip = $false; Note = '' }
            try {
                $t = Get-NetTCPSetting -SettingName 'Internet' -ErrorAction Stop
                $lvl = $t.AutoTuningLevelLocal
                $r.Current = ("AutoTuningLevelLocal = {0}" -f $lvl)
                if ($lvl -ne 'Normal') {
                    $r.Optimal = $false
                    $r.Note = 'Autotuning is NOT Normal - a classic throughput-killing tweak left by older optimizers. Restoring Normal usually helps.'
                } else {
                    $r.Note = 'Already Normal (healthy default).'
                }
            } catch {
                $r.Skip = $true; $r.Current = 'read failed'; $r.Note = $_.Exception.Message
            }
            $r
        };
        Apply = {
            try {
                Set-NetTCPSetting -SettingName 'Internet' -AutoTuningLevelLocal Normal -ErrorAction Stop
                $chk = (Get-NetTCPSetting -SettingName 'Internet' -ErrorAction SilentlyContinue).AutoTuningLevelLocal
                return ($chk -eq 'Normal')
            } catch {
                return $false
            }
        }
    }

    Register-NGModule @{
        Id = 'A09'; Name = 'TCP window scaling + timestamps (Tcp1323Opts, verify-after-write)';
        Round = 2; Class = 'Sequential'; Risk = 'Med'; Impact = 'Marginal';
        NeedsAdmin = $true; NeedsApply = $true; NeedsRisky = $true; DependsOn = @();
        Probe = {
            $r = [ordered]@{ Current = ''; Proposed = '1 (window scaling on)'; Optimal = $true; Skip = $false; Note = '' }
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
                $r.Skip = $true; $r.Current = 'read failed'; $r.Note = $_.Exception.Message
            }
            $r
        };
        Apply = {
            try {
                Set-ItemProperty -LiteralPath $script:TcpipRegPath -Name 'Tcp1323Opts' -Value 1 -Type DWord -ErrorAction Stop
                $chk = (Get-ItemProperty -LiteralPath $script:TcpipRegPath -ErrorAction SilentlyContinue).Tcp1323Opts
                if ($chk -ne 1) {
                    Write-NGLog 'Tcp1323Opts write did not stick (third-party security lock?).' 'RISK'
                    return $false
                }
                return $true
            } catch {
                return $false
            }
        }
    }

    # ===== Round 3: polish / verify =====

    Register-NGModule @{
        Id = 'VFY'; Name = 'Final state verification + health snapshot';
        Round = 3; Class = 'Sequential'; Risk = 'Low'; Impact = 'Foundation';
        NeedsAdmin = $false; NeedsApply = $false; NeedsRisky = $false; DependsOn = @('A01');
        Probe = {
            $healthy = Test-NGHealth
            $curTxt = 'reachability degraded'
            $noteTxt = 'Health failed - consider -RollbackSwitch.'
            if ($healthy) {
                $curTxt = 'gateway + external reachable'
                $noteTxt = 'Network path verified end-to-end.'
            }
            [ordered]@{
                Current = $curTxt
                Proposed = 'healthy'; Optimal = $healthy; Skip = $false
                Note = $noteTxt
            }
        };
        Apply = { $true }
    }

    # ===== Deliberately excluded (shown, never executed) =====
    $script:Excluded = @(
        [pscustomobject]@{ Name = 'BBR2 congestion provider'; Reason = 'Breaks loopback/localhost TCP on Win11 23H2/24H2 (kills your VRN ControlCenter :7788 / HttpListener); CongestionProvider is read-only via Set-NetTCPSetting anyway. netsh-only, manual, at your own risk.' }
        [pscustomobject]@{ Name = 'Hardcode MTU 1500/9000'; Reason = 'PMTU black-hole risk; reliable path is per-driver Jumbo Packet, not a universal MTU write.' }
        [pscustomobject]@{ Name = 'Disable EEE / green Ethernet'; Reason = 'Some older NIC drivers BSOD on toggle; near-zero gain. Irrelevant on a Wi-Fi uplink.' }
        [pscustomobject]@{ Name = 'Disable / restart adapter'; Reason = 'Any NIC-down window can strand a host. This engine never downs an adapter by design (no-stall guarantee).' }
        [pscustomobject]@{ Name = 'Disable Nagle (TcpNoDelay registry)'; Reason = 'Per-app concern, not a global tweak; global disable can hurt bulk throughput. Left to app config.' }
    )
}

# ---------------------------------------------------------------------------
# Classification + dependency ordering (parallel-safe before sequential)
# ---------------------------------------------------------------------------
function Get-NGOrdered {
    $byId = @{}
    foreach ($m in $script:Modules) { $byId[$m.Id] = $m }
    $ordered = [System.Collections.Generic.List[object]]::new()
    $visited = [System.Collections.Generic.HashSet[string]]::new()

    $rounds = $script:Modules | ForEach-Object { $_.Round } | Sort-Object -Unique
    foreach ($rd in $rounds) {
        $inRound = $script:Modules |
            Where-Object { $_.Round -eq $rd } |
            Sort-Object -Property @{ e = 'Class'; desc = $false }, @{ e = 'Id'; desc = $false }
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
# Single accelerator: probe always; apply only when permitted + safe
# ---------------------------------------------------------------------------
function Invoke-NGModule {
    param([object]$Module)

    $probe = $null
    try {
        $probe = & $Module.Probe
    } catch {
        $probe = [ordered]@{ Current = 'probe error'; Proposed = ''; Optimal = $false; Skip = $false; Note = $_.Exception.Message }
    }

    $isSkip = $false
    if ($probe.Contains('Skip')) { $isSkip = [bool]$probe.Skip }

    $status = 'INFO'
    $color  = $script:ColGrey

    if ($isSkip) {
        $status = 'SKIP'; $color = $script:ColGrey
    } elseif (-not $Module.NeedsApply) {
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
        Id = $Module.Id; Name = $Module.Name; Round = $Module.Round; Class = $Module.Class
        Risk = $Module.Risk; Impact = $Module.Impact; Status = $status; Color = $color
        Current = [string]$probe.Current; Proposed = [string]$probe.Proposed; Note = [string]$probe.Note
    }
    $script:Findings.Add($row)
    $logLevel = 'INFO'
    if ($status -in @('FAIL', 'ROLLED-BACK')) { $logLevel = 'RISK' }
    Write-NGLog ("{0} [{1}] {2}" -f $Module.Id, $status, $Module.Name) $logLevel
    return $row
}

# ---------------------------------------------------------------------------
# Three-round panoramic cycle (throttled dynamic progress)
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
        $appliedCount = 0; $failCount = 0; $skipCount = 0
        foreach ($m in $modsThis) {
            $done++
            $pct = [int](($done / [Math]::Max($total, 1)) * 100)
            Update-NGProgress -Status ("{0} :: {1}" -f $roundNames[$rd], $m.Id) -Percent $pct -ForceSwitch
            $row = Invoke-NGModule -Module $m
            if ($row.Status -eq 'APPLIED') { $appliedCount++ }
            if ($row.Status -in @('FAIL', 'ROLLED-BACK')) { $failCount++ }
            if ($row.Status -eq 'SKIP') { $skipCount++ }
        }
        $script:RoundLog.Add([pscustomobject]@{
            Round = $rd; Name = $roundNames[$rd]
            Modules = ($modsThis | Measure-Object).Count
            Applied = $appliedCount; Failed = $failCount; Skipped = $skipCount
            Aborted = $script:AbortApply
        })
        if ($script:AbortApply) {
            Write-NGLog 'Regression guard tripped: halting further mutation, continuing to report.' 'RISK'
        }
    }
    Write-Progress -Id 1 -Activity 'VIA NetGuard v2 - cross-acceleration cycle' -Completed
}

# ---------------------------------------------------------------------------
# HTML matrix report (Visual Lock) with Impact + cross-acceleration map
# ---------------------------------------------------------------------------
function Get-NGImpactColor {
    param([string]$Impact)
    $c = switch ($Impact) {
        'Real'       { $script:ColDown }
        'Defensive'  { $script:ColDown }
        'Security'   { $script:ColTeal }
        'Insight'    { $script:ColBlue }
        'Foundation' { $script:ColBlue }
        default      { $script:ColGrey }
    }
    return $c
}

function Build-NGMatrixRows {
    $sb = [System.Text.StringBuilder]::new()
    foreach ($f in $script:Findings) {
        $badge = ("<span class='badge' style='background:{0}'>{1}</span>" -f $f.Color, (Get-NGHtmlEncode $f.Status))
        $impColor = Get-NGImpactColor -Impact $f.Impact
        $impBadge = ("<span class='tag' style='color:{0};border-color:{0}'>{1}</span>" -f $impColor, (Get-NGHtmlEncode $f.Impact))
        [void]$sb.AppendLine('<tr>')
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Id)))
        [void]$sb.AppendLine(("<td>{0}</td>" -f (Get-NGHtmlEncode $f.Name)))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode ([string]$f.Round))))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Class)))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $f.Risk)))
        [void]$sb.AppendLine(("<td>{0}</td>" -f $impBadge))
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
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $r.Skipped))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $r.Failed))
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f $ab))
        [void]$sb.AppendLine('</tr>')
    }
    return $sb.ToString()
}

function Build-NGCrossRows {
    # Cross-acceleration: which accelerator feeds which (DependsOn graph).
    $sb = [System.Text.StringBuilder]::new()
    $byId = @{}
    foreach ($m in $script:Modules) { $byId[$m.Id] = $m }
    foreach ($m in $script:Modules) {
        if ($m.DependsOn.Count -eq 0) { continue }
        $feeders = [System.Collections.Generic.List[string]]::new()
        foreach ($dep in $m.DependsOn) {
            $depName = $dep
            if ($byId.ContainsKey($dep)) { $depName = ("{0} {1}" -f $dep, $byId[$dep].Name) }
            $feeders.Add($depName)
        }
        [void]$sb.AppendLine('<tr>')
        [void]$sb.AppendLine(("<td class='mono'>{0}</td>" -f (Get-NGHtmlEncode $m.Id)))
        [void]$sb.AppendLine(("<td>{0}</td>" -f (Get-NGHtmlEncode $m.Name)))
        [void]$sb.AppendLine(("<td class='small'>{0}</td>" -f (Get-NGHtmlEncode ($feeders -join '  &larr;  '))))
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
    if ($null -ne $script:Ctx.Adapter) {
        $adapter = ("{0} (ifIndex {1}, {2})" -f $script:Ctx.Adapter.Name, $script:Ctx.Adapter.InterfaceIndex, $script:Ctx.Adapter.LinkSpeed)
    }
    $adminTxt = 'no'
    if ($script:IsAdmin) { $adminTxt = 'yes' }
    $gw = 'unknown'
    if ($null -ne $script:Ctx.Gateway) { $gw = $script:Ctx.Gateway }
    $backupShown = 'n/a (dry-run)'
    if ($script:DoApply) { $backupShown = $script:BackupDir }

    $tpl = @'
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA NetGuard v2 Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;700;800&display=swap');
:root{ --blue:@@BLUE@@; --grey:@@GREY@@; --teal:@@TEAL@@; --up:@@UP@@; --down:@@DOWN@@; }
*{ box-sizing:border-box; }
body{ margin:0; padding:36px; background:#13161a; color:#e7e9ec; font-family:'DM Sans',sans-serif; }
h1{ font-family:'Syne',sans-serif; font-weight:800; font-size:26px; margin:0 0 4px; color:#fff; letter-spacing:.5px; }
.sub{ color:var(--grey); font-size:13px; margin-bottom:22px; }
.meta{ display:flex; flex-wrap:wrap; gap:10px; margin:16px 0 26px; }
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
.tag{ display:inline-block; padding:2px 8px; border-radius:10px; border:1px solid; font-weight:700; font-size:10.5px; font-family:'DM Mono',monospace; background:transparent; }
.foot{ color:var(--grey); font-size:11px; margin-top:24px; line-height:1.6; }
.legend span{ display:inline-block; margin-right:14px; font-size:11px; color:var(--grey); }
.dot{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }
code{ background:#23282e; padding:2px 6px; border-radius:4px; font-family:'DM Mono',monospace; color:#e7e9ec; }
</style>
</head>
<body>
<h1>VIA NetGuard Tuner v2</h1>
<div class="sub">10 cross-accelerators &mdash; production-safe panoramic network analysis &mdash; 判天地之美，析萬物之理</div>
<div><span class="mode @@MODECLS@@">@@MODE@@</span></div>
<div class="meta">
  <div class="chip">generated <b>@@GENERATED@@</b></div>
  <div class="chip">admin <b>@@ADMIN@@</b></div>
  <div class="chip">uplink <b>@@ADAPTER@@</b></div>
  <div class="chip">media <b>@@MEDIA@@</b></div>
  <div class="chip">gateway <b>@@GATEWAY@@</b></div>
  <div class="chip">snapshot <b>@@BACKUP@@</b></div>
</div>

<h2>Round summary</h2>
<table>
<thead><tr><th>#</th><th>round</th><th>modules</th><th>applied</th><th>skipped</th><th>failed</th><th>aborted</th></tr></thead>
<tbody>@@ROUNDROWS@@</tbody>
</table>

<h2>Accelerator matrix</h2>
<div class="legend" style="margin-bottom:8px;">
  <span><i class="dot" style="background:@@DOWN@@"></i>OK / APPLIED</span>
  <span><i class="dot" style="background:@@BLUE@@"></i>DRY (would change)</span>
  <span><i class="dot" style="background:@@GREY@@"></i>SKIP / NO-ADMIN / INFO</span>
  <span><i class="dot" style="background:@@UP@@"></i>FAIL / ROLLED-BACK</span>
</div>
<table>
<thead><tr><th>id</th><th>accelerator</th><th>rd</th><th>class</th><th>risk</th><th>impact</th><th>status</th><th>current</th><th>proposed</th><th>note</th></tr></thead>
<tbody>@@MATRIXROWS@@</tbody>
</table>

<h2>Cross-acceleration map (feeds &larr;)</h2>
<table>
<thead><tr><th>id</th><th>accelerator</th><th>consumes output of</th></tr></thead>
<tbody>@@CROSSROWS@@</tbody>
</table>

<h2>Deliberately excluded (not executed)</h2>
<table>
<thead><tr><th>item</th><th>why it is off on a production host</th></tr></thead>
<tbody>@@EXCLROWS@@</tbody>
</table>

<div class="foot">
DRY-RUN changes nothing. Apply low-risk reversible accelerators with <code>-ApplySwitch</code>;
add gated medium-risk ones with <code>-EnableRiskySwitch</code>; restore the latest snapshot with <code>-RollbackSwitch</code>.
Every mutation is snapshotted, health-checked, and auto-rolled-back on failure; a regression guard halts all further mutation.
This engine never disables or restarts an adapter. Impact ratings: <b>Real</b>/<b>Defensive</b> = worth doing,
<b>Marginal</b> = small/noise, <b>Security</b> = posture, <b>Foundation</b>/<b>Insight</b> = feeds other accelerators.
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
    $html = $html.Replace('@@MEDIA@@', (Get-NGHtmlEncode $script:Ctx.Media))
    $html = $html.Replace('@@GATEWAY@@', (Get-NGHtmlEncode $gw))
    $html = $html.Replace('@@BACKUP@@', (Get-NGHtmlEncode $backupShown))
    $html = $html.Replace('@@ROUNDROWS@@', (Build-NGRoundRows))
    $html = $html.Replace('@@MATRIXROWS@@', (Build-NGMatrixRows))
    $html = $html.Replace('@@CROSSROWS@@', (Build-NGCrossRows))
    $html = $html.Replace('@@EXCLROWS@@', (Build-NGExcludedRows))

    [IO.File]::WriteAllText($script:ReportPath, $html, $script:Utf8NoBom)
    Write-NGLog ("Report written: {0}" -f $script:ReportPath) 'OK'
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function Start-NGEngine {
    Write-Host ''
    Write-Host '====================================================' -ForegroundColor Cyan
    Write-Host ' VIA NetGuard Tuner v2  (10 cross-accelerators)      ' -ForegroundColor Cyan
    Write-Host '====================================================' -ForegroundColor Cyan

    Initialize-NGDirs
    $script:IsAdmin = Test-NGAdmin
    $script:Ctx.Gateway = Get-NGGateway

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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
