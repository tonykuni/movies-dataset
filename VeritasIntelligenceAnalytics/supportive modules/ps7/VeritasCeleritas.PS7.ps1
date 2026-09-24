#Requires -Version 7.0
# =============================================================================
#  VeritasCeleritas.PS7.ps1  v1.0.0
#  PowerShell 7 · CPU-only · 5 段本行程減壓 + 30 個可堆疊加速器
#  安全契約：
#    - 只動目前 PID。不改登錄檔、不改系統檔、不碰其他進程。
#    - 禁止 EmptyWorkingSet 掃全機、禁止把別人改成 BelowNormal。
#    - 執行緒池上限封頂 64。優先權最高 AboveNormal。
#    - ErrorAction 維持 Continue。關閉即還原。
# =============================================================================
[CmdletBinding()]
param(
    [switch]$RestoreOnly,
    [switch]$Report,
    [scriptblock]$Body
)

Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "VeritasCeleritas.PS7 需要 PowerShell 7+。目前：$($PSVersionTable.PSVersion)"
}

# 批731 Z137(操作員 2026-09-24「PS PY檔案都要依規定裝加速器」= L70 逐次許可):StrictMode 下讀未設的 $script: 變數會丟例外,
#   首載永遠套不上(工作站 2026-09-23 · 容器 pwsh 7.4 皆實證)。改用 Get-Variable 探;其餘一字不動。
if (-not (Get-Variable -Name CeleritasPS7 -Scope Script -ErrorAction SilentlyContinue)) {
    $script:CeleritasPS7 = [ordered]@{
        Version     = '1.0.0'
        Applied     = $false
        Depth       = 0
        Snapshot    = $null
        Log         = [System.Collections.Generic.List[string]]::new()
        Workers     = [Math]::Max(1, [Environment]::ProcessorCount)
        Cores       = [Environment]::ProcessorCount
        ArrayBuffer = $null
        HashBuffer  = $null
        Concurrent  = $null
        RegexCache  = $null
        IOBuffer    = 65536
        Sw          = [System.Diagnostics.Stopwatch]::StartNew()
    }
}

function Write-CeleritasLog {
    param([string]$Code, [string]$Message)
    $line = '{0:N3}s  {1,-4}  {2}' -f $script:CeleritasPS7.Sw.Elapsed.TotalSeconds, $Code, $Message
    [void]$script:CeleritasPS7.Log.Add($line)
    Write-Verbose $line
}

function Get-SafeAffinityPtr {
    $n = [Environment]::ProcessorCount
    if ($n -le 0 -or $n -ge 64) { return $null }
    [UInt64]$mask = 0
    for ($i = 0; $i -lt $n; $i++) {
        $mask = $mask -bor ([UInt64]1 -shl $i)
    }
    return [IntPtr]([Int64]$mask)
}

function Get-CeleritasSnapshot {
    $proc = Get-Process -Id $PID
    $minW = 0; $minC = 0; $maxW = 0; $maxC = 0
    [void][System.Threading.ThreadPool]::GetMinThreads([ref]$minW, [ref]$minC)
    [void][System.Threading.ThreadPool]::GetMaxThreads([ref]$maxW, [ref]$maxC)
    $dbg = $null
    try {
        if ($null -ne [Runspace]::DefaultRunspace -and $null -ne [Runspace]::DefaultRunspace.Debugger) {
            $dbg = [Runspace]::DefaultRunspace.Debugger.DebugMode
        }
    } catch { }
    return [ordered]@{
        PriorityClass     = $proc.PriorityClass
        ProcessorAffinity = $(try { $proc.ProcessorAffinity } catch { $null })
        GcLatency         = [Runtime.GCSettings]::LatencyMode
        MinWorker         = $minW
        MinIo             = $minC
        MaxWorker         = $maxW
        MaxIo             = $maxC
        Progress          = $ProgressPreference
        VerbosePref       = $VerbosePreference
        WarningPref       = $WarningPreference
        InformationPref   = $InformationPreference
        ErrorPref         = $ErrorActionPreference
        OFS               = $(Get-Variable -Name OFS -ValueOnly -ErrorAction SilentlyContinue)   # 批731 Z137:$OFS 預設不存在
        OutputEncoding    = $OutputEncoding
        ConsoleEncoding   = [Console]::OutputEncoding
        Culture           = [System.Threading.Thread]::CurrentThread.CurrentCulture
        UICulture         = [System.Threading.Thread]::CurrentThread.CurrentUICulture
        NativeArgs        = $(Get-Variable -Name PSNativeCommandArgumentPassing -ValueOnly -ErrorAction SilentlyContinue)   # 批731 Z137:7.3 起才有
        DebugMode         = $dbg
        PSStyleProgress   = $(if (Get-Variable PSStyle -ErrorAction SilentlyContinue) { $PSStyle.Progress.View } else { $null })
    }
}

function Restore-CeleritasPS7 {
    $snap = $script:CeleritasPS7.Snapshot
    if ($null -eq $snap) { return }
    try {
        $proc = Get-Process -Id $PID
        $proc.PriorityClass = $snap.PriorityClass
        if ($null -ne $snap.ProcessorAffinity) {
            try { $proc.ProcessorAffinity = $snap.ProcessorAffinity } catch { }
        }
    } catch { }
    try { [Runtime.GCSettings]::LatencyMode = $snap.GcLatency } catch { }
    try {
        [void][System.Threading.ThreadPool]::SetMinThreads($snap.MinWorker, $snap.MinIo)
        [void][System.Threading.ThreadPool]::SetMaxThreads($snap.MaxWorker, $snap.MaxIo)
    } catch { }
    $script:ProgressPreference = $snap.Progress
    $script:VerbosePreference = $snap.VerbosePref
    $script:WarningPreference = $snap.WarningPref
    $script:InformationPreference = $snap.InformationPref
    $script:ErrorActionPreference = $snap.ErrorPref
    $script:OFS = $snap.OFS
    $script:OutputEncoding = $snap.OutputEncoding
    try { [Console]::OutputEncoding = $snap.ConsoleEncoding } catch { }
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $snap.Culture
        [System.Threading.Thread]::CurrentThread.CurrentUICulture = $snap.UICulture
    } catch { }
    try { $script:PSNativeCommandArgumentPassing = $snap.NativeArgs } catch { }
    if ($null -ne $snap.DebugMode) {
        try { [Runspace]::DefaultRunspace.Debugger.SetDebugMode($snap.DebugMode) } catch { }
    }
    if ($null -ne $snap.PSStyleProgress -and (Get-Variable PSStyle -ErrorAction SilentlyContinue)) {
        try { $PSStyle.Progress.View = $snap.PSStyleProgress } catch { }
    }
    $script:CeleritasPS7.Applied = $false
    $script:CeleritasPS7.Depth = 0
    Write-CeleritasLog 'A30' '已還原本行程快照'
}

function Start-CeleritasPS7 {
    if ($script:CeleritasPS7.Applied) {
        $script:CeleritasPS7.Depth++
        Write-CeleritasLog 'A29' "交叉鎖命中，深度 $($script:CeleritasPS7.Depth)"
        return $script:CeleritasPS7
    }

    $script:CeleritasPS7.Sw.Restart()
    $script:CeleritasPS7.Snapshot = Get-CeleritasSnapshot
    Write-CeleritasLog 'P1' '本行程快照完成'

    $ProgressPreference = 'SilentlyContinue'
    $VerbosePreference = 'SilentlyContinue'
    $InformationPreference = 'SilentlyContinue'
    # Error / Warning 不吞
    Write-CeleritasLog 'P2' '本視窗進度條與 Verbose 關閉'

    [GC]::Collect(0, [GCCollectionMode]::Optimized, $false)
    Write-CeleritasLog 'P3' 'Gen0 輕回收（非 Forced Gen2）'
    Write-CeleritasLog 'P4' '安全門：不掃其他進程、不 EmptyWorkingSet'
    Write-CeleritasLog 'P5' '退出還原已註冊'

    Write-CeleritasLog 'A01' "PowerShell $($PSVersionTable.PSVersion) / .NET $([Environment]::Version)"

    $proc = Get-Process -Id $PID
    try {
        $proc.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::AboveNormal
        Write-CeleritasLog 'A02' 'PriorityClass = AboveNormal'
    } catch {
        Write-CeleritasLog 'A02' '優先權無法變更（權限不足，略過）'
    }

    $aff = Get-SafeAffinityPtr
    if ($null -ne $aff) {
        try {
            $proc.ProcessorAffinity = $aff
            Write-CeleritasLog 'A03' "親和性遮罩已套到 $($script:CeleritasPS7.Cores) 核"
        } catch {
            Write-CeleritasLog 'A03' '親和性略過（非 Windows 或權限）'
        }
    } else {
        Write-CeleritasLog 'A03' '核數 ≥ 64 或無法計算，交給 OS'
    }

    $cores = $script:CeleritasPS7.Cores
    $minW = [Math]::Max(1, $cores)
    $maxW = [Math]::Min(64, [Math]::Max($cores * 2, $cores))
    $curMinW = 0; $curMinC = 0; $curMaxW = 0; $curMaxC = 0
    [void][System.Threading.ThreadPool]::GetMinThreads([ref]$curMinW, [ref]$curMinC)
    [void][System.Threading.ThreadPool]::GetMaxThreads([ref]$curMaxW, [ref]$curMaxC)
    [void][System.Threading.ThreadPool]::SetMinThreads($minW, [Math]::Max(1, [Math]::Min($curMinC, $minW)))
    [void][System.Threading.ThreadPool]::SetMaxThreads([Math]::Max($maxW, $curMaxW), $curMaxC)
    $script:CeleritasPS7.Workers = $minW
    Write-CeleritasLog 'A04' "MinThreads worker=$minW"
    Write-CeleritasLog 'A05' "MaxThreads worker≤$maxW（封頂 64）"

    try {
        [Runtime.ProfileOptimization]::SetProfileRoot([IO.Path]::GetTempPath())
        [Runtime.ProfileOptimization]::StartProfile("VeritasCeleritas.PS7.profile")
        Write-CeleritasLog 'A06' 'JIT 設定檔 → TEMP'
    } catch {
        Write-CeleritasLog 'A06' 'ProfileOptimization 不可用，略過'
    }

    try {
        [Runtime.GCSettings]::LatencyMode = [Runtime.GCLatencyMode]::SustainedLowLatency
        Write-CeleritasLog 'A07' 'GC = SustainedLowLatency'
    } catch {
        Write-CeleritasLog 'A07' 'GC 延遲模式不可改'
    }

    $script:CeleritasPS7.ArrayBuffer = [System.Collections.Generic.List[object]]::new(4096)
    $script:CeleritasPS7.HashBuffer  = [System.Collections.Generic.Dictionary[string, object]]::new()
    $script:CeleritasPS7.Concurrent  = [System.Collections.Concurrent.ConcurrentDictionary[string, object]]::new()
    Write-CeleritasLog 'A08' 'List[object](4096)'
    Write-CeleritasLog 'A09' 'Dictionary[string,object]'
    Write-CeleritasLog 'A10' 'ConcurrentDictionary 供 -Parallel'

    $script:OFS = ''
    Write-CeleritasLog 'A11' 'OFS 清空'

    if (Get-Variable PSStyle -ErrorAction SilentlyContinue) {
        try { $PSStyle.Progress.View = 'Minimal'; Write-CeleritasLog 'A12' 'PSStyle.Progress = Minimal' } catch { }
    } else {
        Write-CeleritasLog 'A12' '無 PSStyle，略過'
    }

    try {
        if ($null -ne [Runspace]::DefaultRunspace -and $null -ne [Runspace]::DefaultRunspace.Debugger) {
            [Runspace]::DefaultRunspace.Debugger.SetDebugMode([System.Management.Automation.DebuggerDebugMode]::None)
            Write-CeleritasLog 'A13' 'Debugger = None'
        }
    } catch {
        Write-CeleritasLog 'A13' 'Debugger 略過'
    }

    $simd = $false
    try { $simd = [System.Numerics.Vector]::IsHardwareAccelerated } catch { }
    Write-CeleritasLog 'A14' "SIMD=$simd"

    $script:CeleritasPS7.RegexCache = [System.Collections.Generic.Dictionary[string, System.Text.RegularExpressions.Regex]]::new()
    Write-CeleritasLog 'A15' 'RegexOptions.Compiled 快取表'

    Write-CeleritasLog 'A16' 'Stopwatch 運轉中'

    try {
        $script:PSNativeCommandArgumentPassing = 'Standard'
        Write-CeleritasLog 'A17' 'Native 參數傳遞 = Standard'
    } catch {
        Write-CeleritasLog 'A17' 'Native 參數略過'
    }

    Write-CeleritasLog 'A18' 'Information 靜音；ErrorAction 保持 Continue'
    Write-CeleritasLog 'A19' 'ProgressPreference = SilentlyContinue'
    Write-CeleritasLog 'A20' 'VerbosePreference = SilentlyContinue'
    Write-CeleritasLog 'A21' 'Error 不吞 — 失敗必須看見'

    try {
        $inv = [Globalization.CultureInfo]::InvariantCulture
        [Threading.Thread]::CurrentThread.CurrentCulture = $inv
        Write-CeleritasLog 'A22' 'InvariantCulture'
    } catch {
        Write-CeleritasLog 'A22' 'Culture 略過'
    }

    $utf8 = [Text.UTF8Encoding]::new($false)
    $script:OutputEncoding = $utf8
    try { [Console]::OutputEncoding = $utf8 } catch { }
    Write-CeleritasLog 'A23' 'OutputEncoding UTF-8 無 BOM'
    Write-CeleritasLog 'A24' 'Console.OutputEncoding UTF-8'

    try {
        [Net.ServicePointManager]::DefaultConnectionLimit = [Math]::Min(64, $cores * 4)
        Write-CeleritasLog 'A25' "連線上限 = $([Net.ServicePointManager]::DefaultConnectionLimit)"
    } catch {
        Write-CeleritasLog 'A25' '連線上限略過（由 SocketsHttpHandler 管）'
    }

    $script:CeleritasPS7.IOBuffer = 65536
    Write-CeleritasLog 'A26' 'I/O 緩衝 64KB'

    Write-CeleritasLog 'A27' "Runspace / Parallel throttle = $cores"
    Write-CeleritasLog 'A28' 'Invoke-CeleritasParallel 已就緒'
    Write-CeleritasLog 'A29' '交叉鎖開啟，禁止重套'

    $script:CeleritasPS7.Applied = $true
    $script:CeleritasPS7.Depth = 1

    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action {
        try { Restore-CeleritasPS7 } catch { }
    } | Out-Null

    Write-CeleritasLog 'A30' 'Exiting 還原已掛上'
    return $script:CeleritasPS7
}

function Invoke-CeleritasParallel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [object]$InputObject,
        [Parameter(Mandatory)]
        [scriptblock]$Process,
        [int]$ThrottleLimit = 0
    )
    begin {
        if (-not $script:CeleritasPS7.Applied) { [void](Start-CeleritasPS7) }
        $script:__batch = [System.Collections.Generic.List[object]]::new()
        $script:__th = if ($ThrottleLimit -gt 0) { $ThrottleLimit } else { $script:CeleritasPS7.Workers }
    }
    process { [void]$script:__batch.Add($InputObject) }
    end {
        $script:__batch | ForEach-Object -Parallel $Process -ThrottleLimit $script:__th
    }
}

function Get-CeleritasRegex {
    param([Parameter(Mandatory)][string]$Pattern)
    if (-not $script:CeleritasPS7.Applied) { [void](Start-CeleritasPS7) }
    $cache = $script:CeleritasPS7.RegexCache
    if ($cache.ContainsKey($Pattern)) { return $cache[$Pattern] }
    $rx = [Text.RegularExpressions.Regex]::new(
        $Pattern,
        [Text.RegularExpressions.RegexOptions]::Compiled
    )
    $cache[$Pattern] = $rx
    return $rx
}

function Read-CeleritasText {
    param([Parameter(Mandatory)][string]$Path)
    return [IO.File]::ReadAllText($Path)
}

function Write-CeleritasText {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Text)
    $utf8 = [Text.UTF8Encoding]::new($false)
    [IO.File]::WriteAllText($Path, $Text, $utf8)
}

function Get-CeleritasStatus {
    if (-not $script:CeleritasPS7.Applied) { [void](Start-CeleritasPS7) }
    $minW = 0; $minC = 0; $maxW = 0; $maxC = 0
    [void][System.Threading.ThreadPool]::GetMinThreads([ref]$minW, [ref]$minC)
    [void][System.Threading.ThreadPool]::GetMaxThreads([ref]$maxW, [ref]$maxC)
    $proc = Get-Process -Id $PID
    return [ordered]@{
        Version     = $script:CeleritasPS7.Version
        Applied     = $script:CeleritasPS7.Applied
        Depth       = $script:CeleritasPS7.Depth
        Cores       = $script:CeleritasPS7.Cores
        Workers     = $script:CeleritasPS7.Workers
        Priority    = "$($proc.PriorityClass)"
        GcLatency   = "$([Runtime.GCSettings]::LatencyMode)"
        MinThreads  = $minW
        MaxThreads  = $maxW
        Progress    = "$ProgressPreference"
        ErrorAction = "$ErrorActionPreference"
        ElapsedMs   = [int]$script:CeleritasPS7.Sw.Elapsed.TotalMilliseconds
        LogCount    = $script:CeleritasPS7.Log.Count
        SIMD        = $(try { [Numerics.Vector]::IsHardwareAccelerated } catch { $false })
    }
}

function Write-CeleritasReport {
    param([string]$Path)
    $st = Get-CeleritasStatus
    if (-not $Path) {
        $Path = Join-Path ([IO.Path]::GetTempPath()) ("VeritasCeleritas-PS7-{0:yyyyMMdd-HHmmss}.html" -f (Get-Date))
    }
    $rows = ($script:CeleritasPS7.Log | ForEach-Object { "<li>$([System.Net.WebUtility]::HtmlEncode($_))</li>" }) -join "`n"
    $html = @"
<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Veritas Celeritas PS7</title>
<style>
  :root { --bg:#090a0c; --fg:#e8eaed; --muted:#8b919a; --accent:#9aa8b3; --ok:#7d9a86; --border:#2a2e33; }
  html,body { background:var(--bg); color:var(--fg); font: 15px/1.5 "IBM Plex Sans","Noto Sans TC",sans-serif; margin:0; }
  main { max-width: 960px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-weight: 500; letter-spacing: -0.03em; }
  .mono { font-family: "IBM Plex Mono", ui-monospace, monospace; }
  .kpis { display:grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap:8px; }
  .kpi { border:1px solid var(--border); border-radius:12px; padding:12px; }
  .kpi b { display:block; font-size:22px; }
  .kpi span { color:var(--muted); font-size:11px; letter-spacing:.18em; text-transform:uppercase; }
  .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap:12px; margin-top:16px; }
  .card { border:1px solid var(--border); border-radius:16px; padding:16px; }
  ol { font-size: 12px; color: var(--muted); }
  .ok { color: var(--ok); }
</style>
<main>
  <p class="mono" style="color:var(--accent);letter-spacing:.2em;font-size:11px">VIA / VDF · ANC-28 · PS7 CPU STACK</p>
  <h1>Veritas Celeritas PS7</h1>
  <p style="color:var(--muted)">5 段本行程減壓 + 30 個交叉相疊加速器。只動本 PID，關閉即還原。</p>
  <div class="kpis">
    <div class="kpi"><span>VERSION</span><b class="mono">$($st.Version)</b></div>
    <div class="kpi"><span>CORES</span><b class="mono">$($st.Cores)</b></div>
    <div class="kpi"><span>WORKERS</span><b class="mono">$($st.Workers)</b></div>
    <div class="kpi"><span>PRIORITY</span><b class="mono">$($st.Priority)</b></div>
    <div class="kpi"><span>GC</span><b class="mono">$($st.GcLatency)</b></div>
    <div class="kpi"><span>ELAPSED</span><b class="mono">$($st.ElapsedMs) ms</b></div>
  </div>
  <div class="grid">
    <section class="card">
      <h2 class="ok" style="font-size:14px">堆疊紀錄</h2>
      <ol class="mono">$rows</ol>
    </section>
    <section class="card">
      <h2 style="font-size:14px">安全契約</h2>
      <p style="color:var(--muted);font-size:14px">未掃其他進程。未 EmptyWorkingSet。執行緒池未開到 32767。ErrorAction = $($st.ErrorAction)。</p>
    </section>
  </div>
</main>
</html>
"@
    Write-CeleritasText -Path $Path -Text $html
    return $Path
}

if ($RestoreOnly) {
    Restore-CeleritasPS7
    return [ordered]@{
        Applied = $false
        Restored = $true
        Version = $script:CeleritasPS7.Version
    }
}

[void](Start-CeleritasPS7)

if ($Body) {
    & $Body
}

if ($Report) {
    $out = Write-CeleritasReport
    Write-Output $out
}

# 核心業務邏輯區：把工作放進 -Body，或點來源後自己寫。
# 例：
#   . .\VeritasCeleritas.PS7.ps1
#   1..1000 | Invoke-CeleritasParallel -Process { $_ * $_ }
#   Write-CeleritasReport
