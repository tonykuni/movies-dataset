#requires -Version 7.0
<#
VIA TriBox Optimizer  三合一系統優化器
BOX 1 DEV    : 開發快取回收 regenerable dev caches reclaim
BOX 2 SYSTEM : 系統垃圾清理 windows junk cleanup
BOX 3 PERF   : 運作效能優化 runtime performance tune

四階安全刪除階梯 Scan to Quarantine to Recycle to Permanent
硬保護守則 venv root and VIA source root and OneDrive never touched
單檔貼上即跑 accelerator parallel sizing  HTML report auto open
LL compliant PS7  no aliases  ProcessStartInfo only  IO.File WriteAllText UTF8 no BOM
#>
[CmdletBinding()]
param(
    [ValidateSet('Scan','Quarantine','Recycle','Permanent')]
    [string]$Mode = 'Scan',
    [string[]]$ScanRoot = @(),
    [string]$QuarantineRoot = '',
    [switch]$IncludeNodeModules,
    [switch]$IncludePackageCache,
    [switch]$RunPerf,
    [switch]$EmptyRecycleBin,
    [switch]$DeepClean,
    [switch]$DockerPrune,
    [switch]$NoOpenReport,
    [int]$ThrottleLimit = 8,
    [switch]$DownloadsManager,
    [int]$DownloadsPort = 8871,
    [string]$DownloadsRoot = '',
    [int]$AccelThrottle = 10,
    [switch]$IncludeBuildOutput,
    [switch]$FastScan,
    [switch]$EnvAudit,
    [switch]$Control
)

# ---------- 0-2. 初始化（貼上主控台安全：所有 $script: 設定收進函式，原子解析、同範圍共享）----------
function Initialize-TriBox {
    $ErrorActionPreference = 'Stop'
    [System.Threading.Thread]::CurrentThread.CurrentCulture = 'en-US'

    $script:Ts        = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $script:StartTime = Get-Date
    $self = ''
    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $self = $PSScriptRoot }
    $script:SelfDir   = $self
    $script:OutDir    = Join-Path $env:USERPROFILE ('VIA_TriBox\' + $script:Ts)
    $null = [System.IO.Directory]::CreateDirectory($script:OutDir)
    $script:ReportPath = Join-Path $script:OutDir ('VIA_TriBox_Report_' + $script:Ts + '.html')

    $qr = $QuarantineRoot
    if ([string]::IsNullOrWhiteSpace($qr)) { $qr = Join-Path $env:USERPROFILE ('VIA_Quarantine\' + $script:Ts) }
    $script:QuarantineRoot = $qr
    $script:ManifestPath   = Join-Path $script:OutDir ('quarantine_manifest_' + $script:Ts + '.jsonl')

    if ($ScanRoot.Count -eq 0) { $script:ScanRoots = @($env:USERPROFILE) } else { $script:ScanRoots = $ScanRoot }

    try { Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction Stop } catch { }

    $script:IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    $script:CssBlue  = '#4c78a8'
    $script:CssGrey  = '#9c9890'
    $script:CssTeal  = '#439a9a'
    $script:CssRed   = '#c96b5a'
    $script:CssGreen = '#5a9e6f'

    $roots = [System.Collections.Generic.List[string]]::new()
    $roots.Add('C:\Users\tonyk\envs')
    $roots.Add('C:\VeritasIntelligenceAnalytics')
    $roots.Add([string]$env:WINDIR)
    $roots.Add([string][System.Environment]::GetEnvironmentVariable('ProgramFiles'))
    $roots.Add([string][System.Environment]::GetEnvironmentVariable('ProgramFiles(x86)'))
    $roots.Add([string][System.Environment]::GetEnvironmentVariable('ProgramW6432'))
    $roots.Add([string]$env:OneDrive)
    $roots.Add([string][System.Environment]::GetEnvironmentVariable('OneDriveConsumer'))
    $roots.Add([string][System.Environment]::GetEnvironmentVariable('OneDriveCommercial'))
    $roots.Add('C:\ProgramData\Anaconda3')
    $roots.Add('C:\ProgramData\miniconda3')
    $roots.Add([string]$script:SelfDir)
    $roots.Add([string]$script:OutDir)
    $roots.Add([string]$script:QuarantineRoot)
    $script:ProtectedRoots = $roots | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    $script:UnambiguousCache = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($n in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.ipynb_checkpoints','.tox','.eggs','.next','.nuxt','.parcel-cache','.turbo','.svelte-kit','.angular','.vite')) { $null = $script:UnambiguousCache.Add($n) }

    $script:BuildDirNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($n in @('build','dist','target','bin','obj','out')) { $null = $script:BuildDirNames.Add($n) }

    $script:ProjectMarkers = @('package.json','pyproject.toml','setup.py','Cargo.toml','*.csproj','*.sln','tsconfig.json','Makefile','pom.xml','build.gradle','go.mod')

    # 套件庫/編輯器/環境片段：其中的 dist/build/bin/out 與 .egg-info 屬已安裝內容，永不視為可回收建置產物
    $script:StoreSegs = @(
        '\site-packages\', '\dist-packages\', '\node_modules\',
        '\resources\app\', '\.vscode\extensions\', '\.cursor\extensions\',
        '\appdata\local\programs\',
        '\.conda\', '\anaconda3\', '\miniconda3\', '\mamba\', '\conda_pkgs\', '\pkgs\',
        '\.cargo\', '\.nuget\', '\.gradle\', '\.m2\',
        '\uv\cache\', '\.cache\', '\veritas_env_root\'
    )
}

# ---------- 3. 工具函式 ----------
function Test-Protected {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $true }
    $full = ''
    try { $full = [System.IO.Path]::GetFullPath($Path) } catch { return $true }
    $norm = $full.TrimEnd('\').ToLowerInvariant()
    foreach ($root in $script:ProtectedRoots) {
        $r = $root.TrimEnd('\').ToLowerInvariant()
        if ($norm -eq $r) { return $true }
        if ($norm.StartsWith($r + '\')) { return $true }
    }
    return $false
}

function Format-Size {
    param([double]$Bytes)
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N2} MB' -f ($Bytes / 1MB)) }
    if ($Bytes -ge 1KB) { return ('{0:N2} KB' -f ($Bytes / 1KB)) }
    return ('{0} B' -f [int64]$Bytes)
}

function Test-ProjectMarker {
    param([string]$Dir)
    foreach ($m in $script:ProjectMarkers) {
        try {
            $hits = [System.IO.Directory]::EnumerateFileSystemEntries($Dir, $m)
            foreach ($h in $hits) { return $true }
        } catch { }
    }
    return $false
}

function Find-CacheDirs {
    param([string[]]$Roots)
    $found = [System.Collections.Generic.List[object]]::new()
    $stack = [System.Collections.Generic.Stack[string]]::new()
    foreach ($r in $Roots) {
        if ((Test-Path -LiteralPath $r) -and -not (Test-Protected -Path $r)) { $stack.Push($r) }
    }
    while ($stack.Count -gt 0) {
        $dir = $stack.Pop()
        $children = $null
        try { $children = [System.IO.Directory]::GetDirectories($dir) } catch { continue }
        foreach ($child in $children) {
            if (Test-Protected -Path $child) { continue }
            $attr = [System.IO.FileAttributes]::Normal
            try { $attr = [System.IO.File]::GetAttributes($child) } catch { continue }
            if (($attr -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
            $name  = [System.IO.Path]::GetFileName($child)
            $lower = $name.ToLowerInvariant()
            $matched  = $false
            $category = ''
            $tier     = ''
            if ($script:UnambiguousCache.Contains($lower)) {
                $matched = $true; $category = 'PyCache/Tooling'; $tier = 'Regen'
            } elseif ($lower -like '*.egg-info') {
                $matched = $true; $category = 'Egg-Info'; $tier = 'Regen'
            } elseif ($lower -eq 'node_modules') {
                if ($IncludeNodeModules) { $matched = $true; $category = 'node_modules'; $tier = 'Heavy' }
            } elseif ($script:BuildDirNames.Contains($lower)) {
                if (Test-ProjectMarker -Dir $dir) { $matched = $true; $category = 'BuildOutput'; $tier = 'Regen' }
            }
            if ($matched) {
                $found.Add([pscustomobject]@{ Path = $child; Category = $category; Tier = $tier; Box = 'DEV'; Kind = 'Dir' })
            } else {
                $stack.Push($child)
            }
        }
    }
    return $found
}

function Add-Target {
    param(
        [System.Collections.Generic.List[object]]$List,
        [string]$Path,
        [string]$Category,
        [string]$Box,
        [string]$Tier,
        [string]$Kind
    )
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if (Test-Protected -Path $Path) { return }
    $List.Add([pscustomobject]@{ Path = $Path; Category = $Category; Tier = $Tier; Box = $Box; Kind = $Kind })
}

function Get-WellKnownTargets {
    $list = [System.Collections.Generic.List[object]]::new()
    $lad  = $env:LOCALAPPDATA
    $rad  = $env:APPDATA
    $up   = $env:USERPROFILE

    # BOX 1 dev tool caches  container clean keep folder
    Add-Target $list (Join-Path $lad 'pip\Cache')      'pip cache'   'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $lad 'npm-cache')      'npm cache'   'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $rad 'npm-cache')      'npm cache'   'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $lad 'Yarn\Cache')     'yarn cache'  'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $lad 'pnpm\store')     'pnpm store'  'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $up  '.pnpm-store')    'pnpm store'  'DEV' 'Regen' 'Container'
    Add-Target $list (Join-Path $lad 'uv\cache')       'uv cache'    'DEV' 'Regen' 'Container'

    # BOX 1 reusable package caches  opt in heavy re download
    if ($IncludePackageCache) {
        Add-Target $list (Join-Path $up '.nuget\packages')                 'NuGet pkg'   'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.cargo\registry\cache')           'cargo cache' 'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.cargo\registry\src')             'cargo src'   'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up 'go\pkg\mod\cache\download')       'go modcache' 'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.gradle\caches')                  'gradle'      'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.m2\repository')                  'maven m2'    'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.conda\pkgs')                     'conda pkgs'  'DEV' 'PkgCache' 'Container'
        Add-Target $list (Join-Path $up '.cache\huggingface')             'HF cache'    'DEV' 'Heavy'    'Container'
        Add-Target $list (Join-Path $up '.cache\torch')                    'torch cache' 'DEV' 'Heavy'    'Container'
    }

    # BOX 2 windows junk  container clean
    Add-Target $list $env:TEMP                                            'User Temp'   'SYS' 'Junk' 'Container'
    Add-Target $list (Join-Path $lad 'CrashDumps')                       'CrashDumps'  'SYS' 'Junk' 'Container'
    Add-Target $list (Join-Path $lad 'Microsoft\Windows\WER\ReportQueue')   'WER queue'   'SYS' 'Junk' 'Container'
    Add-Target $list (Join-Path $lad 'Microsoft\Windows\WER\ReportArchive') 'WER archive' 'SYS' 'Junk' 'Container'
    Add-Target $list (Join-Path $lad 'Microsoft\Windows\INetCache')       'INetCache'   'SYS' 'Junk' 'Container'
    if ($script:IsAdmin) {
        Add-Target $list (Join-Path $env:WINDIR 'Temp')                  'Windows Temp' 'SYS' 'Junk' 'Container'
        Add-Target $list (Join-Path $env:WINDIR 'SoftwareDistribution\Download') 'WinUpdate cache' 'SYS' 'Junk' 'Container'
        Add-Target $list 'C:\ProgramData\Microsoft\Windows\WER\ReportQueue'   'WER queue sys'   'SYS' 'Junk' 'Container'
        Add-Target $list 'C:\ProgramData\Microsoft\Windows\WER\ReportArchive' 'WER archive sys' 'SYS' 'Junk' 'Container'
    }
    return $list
}

function Measure-Targets {
    param([System.Collections.Generic.List[object]]$Targets)
    $sized = $Targets | ForEach-Object -ThrottleLimit $ThrottleLimit -Parallel {
        $item  = $_
        $bytes = 0L
        try {
            $sum = (Get-ChildItem -LiteralPath $item.Path -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($null -ne $sum) { $bytes = [int64]$sum }
        } catch { $bytes = 0L }
        $item | Add-Member -NotePropertyName Bytes -NotePropertyValue $bytes -PassThru
    }
    return $sized
}

# ---------- 3A. 十項加速器 + 動態進度 ----------
# A1 runspace pool 真多執行緒（非 ForEach-Object -Parallel 的高開銷）
# A2 .NET EnumerateDirectories/EnumerateFiles（免 Get-ChildItem 物件開銷）
# A3 EnumerationOptions：IgnoreInaccessible + 跳過 ReparsePoint/System
# A4 手動堆疊走訪、命中即剪枝（不下探 node_modules / 快取內部）
# A5 受保護根短路剪枝（不走 envs / OneDrive / Windows）
# A6 ConcurrentBag 無鎖結果收集
# A7 Synchronized 計數器批次回寫（低競爭）
# A8 依頂層子樹切工作單元，N 執行緒負載平衡
# A9 DirectoryInfo.EnumerateFiles Length 加總測量（FileInfo.Length 免額外 stat）
# A10 主執行緒 120ms 進度泵，與工作緒解耦 → 動態進度條
function Invoke-AccelPool {
    param(
        [object[]]$Items,
        [int]$Throttle,
        [scriptblock]$Worker,
        [object[]]$Shared,
        [string]$Activity,
        [int]$ProgressId,
        [scriptblock]$StatusFormatter
    )
    $bag = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    if ($null -eq $Items -or $Items.Count -eq 0) { return ,@($bag.ToArray()) }
    $sync = [System.Collections.Hashtable]::Synchronized(@{ done = 0; total = $Items.Count; n1 = [int64]0; n2 = [int64]0; cur = '' })
    $max  = [Math]::Max(1, $Throttle)
    $pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, $max)
    $pool.Open()
    $src  = $Worker.ToString()
    $jobs = [System.Collections.Generic.List[object]]::new()
    foreach ($it in $Items) {
        $ps = [System.Management.Automation.PowerShell]::Create()
        $ps.RunspacePool = $pool
        $null = $ps.AddScript($src)
        $null = $ps.AddArgument($it)
        $null = $ps.AddArgument($sync)
        $null = $ps.AddArgument($bag)
        foreach ($s in $Shared) { $null = $ps.AddArgument($s) }
        $jobs.Add([pscustomobject]@{ PS = $ps; H = $ps.BeginInvoke() })
    }
    while ($true) {
        $remaining = 0
        foreach ($j in $jobs) {
            if (-not $j.H.IsCompleted) { $remaining = $remaining + 1 }
        }
        $sync.done = $jobs.Count - $remaining
        $pct = 0
        if ($jobs.Count -gt 0) { $pct = [int](($sync.done / $jobs.Count) * 100) }
        $stat = ''
        try { $stat = (& $StatusFormatter $sync) } catch { $stat = '' }
        Write-Progress -Id $ProgressId -Activity $Activity -Status $stat -PercentComplete $pct
        if ($remaining -eq 0) { break }
        Start-Sleep -Milliseconds 120
    }
    foreach ($j in $jobs) {
        try { $null = $j.PS.EndInvoke($j.H) } catch { }
        $j.PS.Dispose()
    }
    $pool.Close()
    $pool.Dispose()
    Write-Progress -Id $ProgressId -Activity $Activity -Completed
    return ,@($bag.ToArray())
}

# 工作竊取目錄爬蟲：固定 N 常駐執行緒從共享佇列搶工作，發現子目錄丟回佇列，負載自動均衡
function Invoke-Crawl {
    param([string[]]$Seed, [int]$Threads, [hashtable]$Cfg, [string]$Activity, [int]$ProgressId, [scriptblock]$StatusFormatter)
    $bag   = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    $queue = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
    foreach ($s in $Seed) { $queue.Enqueue($s) }
    if ($Seed.Count -eq 0) { return ,@($bag.ToArray()) }
    $sync = [System.Collections.Hashtable]::Synchronized(@{ dirs = [int64]0; found = [int64]0; out = [int64]$Seed.Count; cur = '' })
    $engine = {
        param($Queue, $Bag, $Sync, $Cfg)
        $opt = [System.IO.EnumerationOptions]::new()
        $opt.IgnoreInaccessible = $true
        $opt.AttributesToSkip   = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
        $mode    = [string]$Cfg['mode']
        $IncNM   = [bool]$Cfg['IncludeNM']
        $IncBld  = [bool]$Cfg['IncludeBuild']
        $Fast    = [bool]$Cfg['FastScan']
        $Markers = @($Cfg['Markers'])
        $StoreSegs = @($Cfg['StoreSegs'])
        $ua = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @($Cfg['Unambig'])) { [void]$ua.Add($x) }
        $bd = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @($Cfg['BuildNames'])) { [void]$bd.Add($x) }
        $prot = [System.Collections.Generic.List[string]]::new()
        foreach ($p in @($Cfg['Protected'])) { $prot.Add($p.TrimEnd('\').ToLowerInvariant()) }
        $boundary = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @('site-packages','dist-packages','node_modules')) { [void]$boundary.Add($x) }
        $vboundary = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @('site-packages','dist-packages','node_modules','__pycache__','.git')) { [void]$vboundary.Add($x) }
        function Test-Prot {
            param([string]$Dir)
            $dl = $Dir.TrimEnd('\').ToLowerInvariant()
            foreach ($p in $prot) {
                if ($dl -eq $p -or $dl.StartsWith($p + '\')) { return $true }
            }
            return $false
        }
        function Test-InStore {
            param([string]$Path)
            $pl = $Path.ToLowerInvariant()
            foreach ($seg in $StoreSegs) {
                if ($pl.Contains($seg)) { return $true }
            }
            return $false
        }
        function Test-VenvRoot {
            param([string]$Dir)
            try {
                if ([System.IO.File]::Exists((Join-Path $Dir 'pyvenv.cfg'))) { return @{ ok = $true; kind = 'venv' } }
                if ([System.IO.Directory]::Exists((Join-Path $Dir 'conda-meta'))) { return @{ ok = $true; kind = 'conda' } }
                if ([System.IO.File]::Exists((Join-Path $Dir 'Scripts\python.exe'))) { return @{ ok = $true; kind = 'venv' } }
            } catch { }
            return @{ ok = $false }
        }
        function Get-PyVer {
            param([string]$Dir)
            try {
                $cfg = Join-Path $Dir 'pyvenv.cfg'
                if ([System.IO.File]::Exists($cfg)) {
                    foreach ($line in [System.IO.File]::ReadAllLines($cfg)) {
                        if ($line -match '^\s*version\s*=\s*(.+)$') { return $Matches[1].Trim() }
                    }
                }
            } catch { }
            return ''
        }
        function Test-Match {
            param([string]$Child, [string]$Parent)
            $name  = [System.IO.Path]::GetFileName($Child)
            $lower = $name.ToLowerInvariant()
            if ($ua.Contains($lower)) { return @{ ok = $true; cat = 'PyCache/Tooling'; tier = 'Regen' } }
            $inStore = Test-InStore -Path $Child
            if ($lower -like '*.egg-info') {
                if ($inStore) { return @{ ok = $false } }
                return @{ ok = $true; cat = 'Egg-Info'; tier = 'Regen' }
            }
            if ($lower -eq 'node_modules') {
                if ($IncNM) { return @{ ok = $true; cat = 'node_modules'; tier = 'Heavy' } }
                return @{ ok = $false }
            }
            if ($bd.Contains($lower)) {
                if (-not $IncBld) { return @{ ok = $false } }
                if ($inStore) { return @{ ok = $false } }
                $hasMarker = $false
                foreach ($m in $Markers) {
                    try {
                        foreach ($z in [System.IO.Directory]::EnumerateFileSystemEntries($Parent, $m)) { $hasMarker = $true; break }
                    } catch { }
                    if ($hasMarker) { break }
                }
                if ($hasMarker) { return @{ ok = $true; cat = 'BuildOutput'; tier = 'Regen' } }
            }
            return @{ ok = $false }
        }
        while ($true) {
            $dir = $null
            if ($Queue.TryDequeue([ref]$dir)) {
                $emit = [System.Collections.Generic.List[string]]::new()
                $hit  = 0
                try {
                    $subs = [System.IO.Directory]::EnumerateDirectories($dir, '*', $opt)
                    foreach ($child in $subs) {
                        if (Test-Prot -Dir $child) { continue }
                        if ($mode -eq 'venv') {
                            $cname = [System.IO.Path]::GetFileName($child).ToLowerInvariant()
                            if ($vboundary.Contains($cname)) { continue }
                            $v = Test-VenvRoot -Dir $child
                            if ($v.ok) {
                                $pv = ''
                                if ($v.kind -eq 'venv') { $pv = Get-PyVer -Dir $child }
                                $Bag.Add([pscustomobject]@{ Path = $child; EnvKind = $v.kind; PyVer = $pv })
                                $hit = $hit + 1
                            } else {
                                $emit.Add($child)
                            }
                        } else {
                            $m = Test-Match -Child $child -Parent $dir
                            if ($m.ok) {
                                $Bag.Add([pscustomobject]@{ Path = $child; Category = $m.cat; Tier = $m.tier; Box = 'DEV'; Kind = 'Dir' })
                                $hit = $hit + 1
                            } else {
                                $skip = $false
                                if ($Fast) {
                                    $cname = [System.IO.Path]::GetFileName($child).ToLowerInvariant()
                                    if ($boundary.Contains($cname)) { $skip = $true }
                                    elseif (Test-InStore -Path $child) { $skip = $true }
                                    elseif ((Test-VenvRoot -Dir $child).ok) { $skip = $true }
                                }
                                if (-not $skip) { $emit.Add($child) }
                            }
                        }
                    }
                } catch { }
                $k = $emit.Count
                [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                try { $Sync.out = $Sync.out + $k - 1; $Sync.dirs = $Sync.dirs + 1; $Sync.found = $Sync.found + $hit; $Sync.cur = $dir } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                foreach ($e in $emit) { $Queue.Enqueue($e) }
            } else {
                $done = $false
                [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                try { $done = ($Sync.out -le 0) } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                if ($done) { break }
                Start-Sleep -Milliseconds 4
            }
        }
    }
    $max  = [Math]::Max(1, $Threads)
    $pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, $max)
    $pool.Open()
    $src  = $engine.ToString()
    $jobs = [System.Collections.Generic.List[object]]::new()
    for ($i = 0; $i -lt $max; $i++) {
        $ps = [System.Management.Automation.PowerShell]::Create()
        $ps.RunspacePool = $pool
        $null = $ps.AddScript($src)
        $null = $ps.AddArgument($queue)
        $null = $ps.AddArgument($bag)
        $null = $ps.AddArgument($sync)
        $null = $ps.AddArgument($Cfg)
        $jobs.Add([pscustomobject]@{ PS = $ps; H = $ps.BeginInvoke() })
    }
    $peak = [double]$sync.out
    if ($peak -lt 1) { $peak = 1 }
    while ($true) {
        $rem = 0
        foreach ($j in $jobs) {
            if (-not $j.H.IsCompleted) { $rem = $rem + 1 }
        }
        $outv = [double]$sync.out
        if ($outv -gt $peak) { $peak = $outv }
        $pct = [int]((1.0 - ([Math]::Max(0.0, $outv) / $peak)) * 100)
        if ($pct -lt 0) { $pct = 0 }
        if ($pct -gt 100) { $pct = 100 }
        $stat = ''
        try { $stat = (& $StatusFormatter $sync) } catch { $stat = '' }
        Write-Progress -Id $ProgressId -Activity $Activity -Status $stat -PercentComplete $pct
        if ($rem -eq 0) { break }
        Start-Sleep -Milliseconds 120
    }
    foreach ($j in $jobs) {
        try { $null = $j.PS.EndInvoke($j.H) } catch { }
        $j.PS.Dispose()
    }
    $pool.Close()
    $pool.Dispose()
    Write-Progress -Id $ProgressId -Activity $Activity -Completed
    return ,@($bag.ToArray())
}

# 工作竊取測量佇列：N 常駐執行緒從佇列搶目標測大小，無論目標數多少只建 N 個 runspace
function Invoke-SizeQueue {
    param([object[]]$Targets, [int]$Threads, [string]$Activity, [int]$ProgressId)
    $bag = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    if ($null -eq $Targets -or $Targets.Count -eq 0) { return ,@($bag.ToArray()) }
    $queue = [System.Collections.Concurrent.ConcurrentQueue[object]]::new()
    foreach ($t in $Targets) { $queue.Enqueue($t) }
    $total = $Targets.Count
    $sync  = [System.Collections.Hashtable]::Synchronized(@{ done = [int64]0; bytes = [int64]0; out = [int64]$total })
    $engine = {
        param($Queue, $Bag, $Sync)
        $opt = [System.IO.EnumerationOptions]::new()
        $opt.IgnoreInaccessible    = $true
        $opt.RecurseSubdirectories = $true
        $opt.AttributesToSkip      = [System.IO.FileAttributes]::ReparsePoint
        while ($true) {
            $t = $null
            if ($Queue.TryDequeue([ref]$t)) {
                $bytes = [int64]0
                try {
                    $di = [System.IO.DirectoryInfo]::new($t.Path)
                    foreach ($fi in $di.EnumerateFiles('*', $opt)) { $bytes = $bytes + $fi.Length }
                } catch { $bytes = [int64]0 }
                $Bag.Add([pscustomobject]@{ Path = $t.Path; Category = $t.Category; Tier = $t.Tier; Box = $t.Box; Kind = $t.Kind; Bytes = $bytes })
                [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                try { $Sync.done = $Sync.done + 1; $Sync.bytes = $Sync.bytes + $bytes; $Sync.out = $Sync.out - 1 } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
            } else {
                $fin = $false
                [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                try { $fin = ($Sync.out -le 0) } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                if ($fin) { break }
                Start-Sleep -Milliseconds 4
            }
        }
    }
    $max  = [Math]::Max(1, $Threads)
    $pool = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspacePool(1, $max)
    $pool.Open()
    $src  = $engine.ToString()
    $jobs = [System.Collections.Generic.List[object]]::new()
    for ($i = 0; $i -lt $max; $i++) {
        $ps = [System.Management.Automation.PowerShell]::Create()
        $ps.RunspacePool = $pool
        $null = $ps.AddScript($src)
        $null = $ps.AddArgument($queue)
        $null = $ps.AddArgument($bag)
        $null = $ps.AddArgument($sync)
        $jobs.Add([pscustomobject]@{ PS = $ps; H = $ps.BeginInvoke() })
    }
    while ($true) {
        $rem = 0
        foreach ($j in $jobs) {
            if (-not $j.H.IsCompleted) { $rem = $rem + 1 }
        }
        $d   = [double]$sync.done
        $pct = 0
        if ($total -gt 0) { $pct = [int](($d / $total) * 100) }
        Write-Progress -Id $ProgressId -Activity $Activity -Status (('已測 {0}/{1} · 累計 {2}' -f $sync.done, $total, (Format-Size -Bytes $sync.bytes))) -PercentComplete $pct
        if ($rem -eq 0) { break }
        Start-Sleep -Milliseconds 120
    }
    foreach ($j in $jobs) {
        try { $null = $j.PS.EndInvoke($j.H) } catch { }
        $j.PS.Dispose()
    }
    $pool.Close()
    $pool.Dispose()
    Write-Progress -Id $ProgressId -Activity $Activity -Completed
    return ,@($bag.ToArray())
}

function Find-CacheDirsAccel {
    param([string[]]$Roots, [int]$Throttle)
    $units = [System.Collections.Generic.List[string]]::new()
    $eo = [System.IO.EnumerationOptions]::new()
    $eo.IgnoreInaccessible = $true
    $eo.AttributesToSkip   = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
    foreach ($r in $Roots) {
        if (-not (Test-Path -LiteralPath $r)) { continue }
        if (Test-Protected -Path $r) { continue }
        try {
            foreach ($c in [System.IO.Directory]::EnumerateDirectories($r, '*', $eo)) {
                if (Test-Protected -Path $c) { continue }
                $units.Add($c)
            }
        } catch { }
    }
    $worker = {
        param($Root, $Sync, $Bag, $Protected, $Unambig, $BuildNames, $Markers, $IncludeNM, $IncludeBuild, $FastScan, $StoreSegs)
        $opt = [System.IO.EnumerationOptions]::new()
        $opt.IgnoreInaccessible = $true
        $opt.AttributesToSkip   = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
        $ua = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in $Unambig) { [void]$ua.Add($x) }
        $bd = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in $BuildNames) { [void]$bd.Add($x) }
        $prot = [System.Collections.Generic.List[string]]::new()
        foreach ($p in $Protected) { $prot.Add($p.TrimEnd('\').ToLowerInvariant()) }
        $boundary = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @('site-packages','dist-packages','node_modules')) { [void]$boundary.Add($x) }
        function Test-Prot {
            param([string]$Dir)
            $dl = $Dir.TrimEnd('\').ToLowerInvariant()
            foreach ($p in $prot) {
                if ($dl -eq $p -or $dl.StartsWith($p + '\')) { return $true }
            }
            return $false
        }
        function Test-InStore {
            param([string]$Path)
            $pl = $Path.ToLowerInvariant()
            foreach ($seg in $StoreSegs) {
                if ($pl.Contains($seg)) { return $true }
            }
            return $false
        }
        function Test-VenvRoot {
            param([string]$Dir)
            try {
                if ([System.IO.File]::Exists((Join-Path $Dir 'pyvenv.cfg'))) { return $true }
                if ([System.IO.Directory]::Exists((Join-Path $Dir 'conda-meta'))) { return $true }
                if ([System.IO.File]::Exists((Join-Path $Dir 'Scripts\python.exe'))) { return $true }
            } catch { }
            return $false
        }
        function Test-Match {
            param([string]$Child, [string]$Parent)
            $name  = [System.IO.Path]::GetFileName($Child)
            $lower = $name.ToLowerInvariant()
            # __pycache__ 與工具快取：套件庫內外都安全可重生
            if ($ua.Contains($lower)) { return @{ ok = $true; cat = 'PyCache/Tooling'; tier = 'Regen' } }
            $inStore = Test-InStore -Path $Child
            # .egg-info / .dist-info 在套件庫內是中繼資料，刪了破壞 pip，僅在非套件庫才回收
            if ($lower -like '*.egg-info') {
                if ($inStore) { return @{ ok = $false } }
                return @{ ok = $true; cat = 'Egg-Info'; tier = 'Regen' }
            }
            if ($lower -eq 'node_modules') {
                if ($IncludeNM) { return @{ ok = $true; cat = 'node_modules'; tier = 'Heavy' } }
                return @{ ok = $false }
            }
            # build/dist/bin/obj/out：僅在 -IncludeBuildOutput 且非套件庫且父為真實專案時回收
            if ($bd.Contains($lower)) {
                if (-not $IncludeBuild) { return @{ ok = $false } }
                if ($inStore) { return @{ ok = $false } }
                $hasMarker = $false
                foreach ($m in $Markers) {
                    try {
                        foreach ($z in [System.IO.Directory]::EnumerateFileSystemEntries($Parent, $m)) { $hasMarker = $true; break }
                    } catch { }
                    if ($hasMarker) { break }
                }
                if ($hasMarker) { return @{ ok = $true; cat = 'BuildOutput'; tier = 'Regen' } }
            }
            return @{ ok = $false }
        }
        $stack = [System.Collections.Generic.Stack[string]]::new()
        $rootMatch = Test-Match -Child $Root -Parent ([System.IO.Path]::GetDirectoryName($Root))
        if ($rootMatch.ok) {
            $Bag.Add([pscustomobject]@{ Path = $Root; Category = $rootMatch.cat; Tier = $rootMatch.tier; Box = 'DEV'; Kind = 'Dir' })
            [System.Threading.Monitor]::Enter($Sync.SyncRoot)
            try { $Sync.n2 = $Sync.n2 + 1 } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
        } else {
            $stack.Push($Root)
        }
        $localDirs = 0
        $sinceFlush = 0
        while ($stack.Count -gt 0) {
            $dir = $stack.Pop()
            $subs = $null
            try { $subs = [System.IO.Directory]::EnumerateDirectories($dir, '*', $opt) } catch { continue }
            foreach ($child in $subs) {
                $localDirs = $localDirs + 1
                $sinceFlush = $sinceFlush + 1
                if (Test-Prot -Dir $child) { continue }
                $m = Test-Match -Child $child -Parent $dir
                if ($m.ok) {
                    $Bag.Add([pscustomobject]@{ Path = $child; Category = $m.cat; Tier = $m.tier; Box = 'DEV'; Kind = 'Dir' })
                    [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                    try { $Sync.n2 = $Sync.n2 + 1 } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                } else {
                    $cname = [System.IO.Path]::GetFileName($child).ToLowerInvariant()
                    $skip = $false
                    if ($FastScan) {
                        if ($boundary.Contains($cname)) { $skip = $true }
                        elseif (Test-InStore -Path $child) { $skip = $true }
                        elseif (Test-VenvRoot -Dir $child) { $skip = $true }
                    }
                    if (-not $skip) { $stack.Push($child) }
                }
                if ($sinceFlush -ge 1024) {
                    [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                    try { $Sync.n1 = $Sync.n1 + $sinceFlush; $Sync.cur = $dir } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                    $sinceFlush = 0
                }
            }
        }
        [System.Threading.Monitor]::Enter($Sync.SyncRoot)
        try { $Sync.n1 = $Sync.n1 + $sinceFlush; $Sync.cur = $Root } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
    }
    $cfg = @{
        mode         = 'cache'
        Protected    = @($script:ProtectedRoots)
        Unambig      = @($script:UnambiguousCache)
        BuildNames   = @($script:BuildDirNames)
        Markers      = @($script:ProjectMarkers)
        StoreSegs    = @($script:StoreSegs)
        IncludeNM    = [bool]$IncludeNodeModules
        IncludeBuild = [bool]$IncludeBuildOutput
        FastScan     = [bool]$FastScan
    }
    $fmt = {
        param($s)
        $c = [string]$s.cur
        if ($c.Length -gt 48) { $c = '...' + $c.Substring($c.Length - 45) }
        ('掃描目錄 {0} · 命中 {1} · {2}' -f $s.dirs, $s.found, $c)
    }
    return (Invoke-Crawl -Seed ($units.ToArray()) -Threads $Throttle -Cfg $cfg -Activity 'BOX1 加速掃描開發快取' -ProgressId 1 -StatusFormatter $fmt)
}

function Measure-TargetsAccel {
    param([object[]]$Targets, [int]$Throttle)
    return (Invoke-SizeQueue -Targets $Targets -Threads $Throttle -Activity 'BOX1/2 加速測量大小' -ProgressId 1)
}

function Write-Manifest {
    param([object]$Record)
    $line = ($Record | ConvertTo-Json -Compress -Depth 5)
    [System.IO.File]::AppendAllText($script:ManifestPath, ($line + "`n"), [System.Text.UTF8Encoding]::new($false))
}

function Invoke-SafeRemove {
    param([object]$Target, [string]$ActMode)
    $path = $Target.Path
    if (Test-Protected -Path $path) { return 'SKIP-PROTECTED' }
    if (-not (Test-Path -LiteralPath $path)) { return 'MISSING' }
    try {
        if ($Target.Kind -eq 'Container') {
            $kids = @()
            try { $kids = Get-ChildItem -LiteralPath $path -Force -ErrorAction SilentlyContinue } catch { $kids = @() }
            foreach ($k in $kids) {
                if (Test-Protected -Path $k.FullName) { continue }
                try {
                    if ($ActMode -eq 'Permanent') {
                        Remove-Item -LiteralPath $k.FullName -Recurse -Force -ErrorAction Stop
                    } elseif ($ActMode -eq 'Recycle') {
                        if ($k.PSIsContainer) {
                            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($k.FullName, 'OnlyErrorDialogs', 'SendToRecycleBin')
                        } else {
                            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($k.FullName, 'OnlyErrorDialogs', 'SendToRecycleBin')
                        }
                    } elseif ($ActMode -eq 'Quarantine') {
                        $sub  = Join-Path $script:QuarantineRoot ($Target.Category -replace '[^\w\.-]','_')
                        $null = [System.IO.Directory]::CreateDirectory($sub)
                        $dest = Join-Path $sub $k.Name
                        Move-Item -LiteralPath $k.FullName -Destination $dest -Force -ErrorAction Stop
                        Write-Manifest ([pscustomobject]@{ ts=$script:Ts; src=$k.FullName; dst=$dest; cat=$Target.Category })
                    }
                } catch { }
            }
            return $ActMode
        } else {
            if ($ActMode -eq 'Permanent') {
                Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
            } elseif ($ActMode -eq 'Recycle') {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($path, 'OnlyErrorDialogs', 'SendToRecycleBin')
            } elseif ($ActMode -eq 'Quarantine') {
                $flat = ($path -replace '[:\\/]','_')
                if ($flat.Length -gt 120) { $flat = $flat.Substring($flat.Length - 120) }
                $null = [System.IO.Directory]::CreateDirectory($script:QuarantineRoot)
                $dest = Join-Path $script:QuarantineRoot $flat
                Move-Item -LiteralPath $path -Destination $dest -Force -ErrorAction Stop
                Write-Manifest ([pscustomobject]@{ ts=$script:Ts; src=$path; dst=$dest; cat=$Target.Category })
            }
            return $ActMode
        }
    } catch {
        return ('FAIL ' + $_.Exception.Message)
    }
}

# ---------- 4. BOX 3 效能優化 ----------
function Invoke-Perf {
    $results = [System.Collections.Generic.List[object]]::new()

    try {
        Clear-DnsClientCache
        $results.Add([pscustomobject]@{ Op='Flush DNS cache'; Status='OK' })
    } catch { $results.Add([pscustomobject]@{ Op='Flush DNS cache'; Status=('ERR ' + $_.Exception.Message) }) }

    $src = @'
using System;
using System.Runtime.InteropServices;
public static class VIAPsapi {
    [DllImport("psapi.dll")]
    public static extern int EmptyWorkingSet(IntPtr hProcess);
}
'@
    try {
        Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
        $cnt = 0
        foreach ($p in (Get-Process)) {
            try { $null = [VIAPsapi]::EmptyWorkingSet($p.Handle); $cnt = $cnt + 1 } catch { }
        }
        $results.Add([pscustomobject]@{ Op=('Empty working set x ' + $cnt); Status='OK' })
    } catch { $results.Add([pscustomobject]@{ Op='Empty working set'; Status=('ERR ' + $_.Exception.Message) }) }

    if ($script:IsAdmin) {
        try {
            $media = 'Unspecified'
            $phys  = Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($null -ne $phys) { $media = [string]$phys.MediaType }
            if ($media -eq 'HDD') {
                Optimize-Volume -DriveLetter C -Defrag -ErrorAction Stop
                $results.Add([pscustomobject]@{ Op='Defrag C HDD'; Status='OK' })
            } else {
                Optimize-Volume -DriveLetter C -ReTrim -ErrorAction Stop
                $results.Add([pscustomobject]@{ Op=('ReTrim C ' + $media); Status='OK' })
            }
        } catch { $results.Add([pscustomobject]@{ Op='Optimize-Volume C'; Status=('ERR ' + $_.Exception.Message) }) }
    } else {
        $results.Add([pscustomobject]@{ Op='Optimize-Volume C'; Status='SKIP need admin' })
    }

    try {
        $rel = Get-PhysicalDisk -ErrorAction SilentlyContinue | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $rel) {
            $wear = $rel.Wear
            $rerr = $rel.ReadErrorsTotal
            $results.Add([pscustomobject]@{ Op='SMART health'; Status=('Wear=' + [string]$wear + ' ReadErr=' + [string]$rerr) })
        } else {
            $results.Add([pscustomobject]@{ Op='SMART health'; Status='no data' })
        }
    } catch { $results.Add([pscustomobject]@{ Op='SMART health'; Status=('ERR ' + $_.Exception.Message) }) }

    return $results
}

function Invoke-DeepClean {
    $results = [System.Collections.Generic.List[object]]::new()
    if (-not $script:IsAdmin) {
        $results.Add([pscustomobject]@{ Op='DISM component cleanup'; Status='SKIP need admin' })
        return $results
    }
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName               = 'dism.exe'
        $psi.Arguments              = '/Online /Cleanup-Image /StartComponentCleanup'
        $psi.UseShellExecute        = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.CreateNoWindow         = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        $null = $proc.StandardOutput.ReadToEnd()
        $null = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        $results.Add([pscustomobject]@{ Op='DISM StartComponentCleanup'; Status=('exit ' + [string]$proc.ExitCode) })
    } catch { $results.Add([pscustomobject]@{ Op='DISM StartComponentCleanup'; Status=('ERR ' + $_.Exception.Message) }) }
    return $results
}

function Invoke-DockerPrune {
    $results = [System.Collections.Generic.List[object]]::new()
    $docker  = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $docker) {
        $results.Add([pscustomobject]@{ Op='Docker prune'; Status='docker not found' })
        return $results
    }
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName               = $docker.Source
        $psi.Arguments              = 'system prune -af --volumes'
        $psi.UseShellExecute        = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.CreateNoWindow         = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        $out  = $proc.StandardOutput.ReadToEnd()
        $null = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        $last = ($out -split "`n" | Where-Object { $_ -match 'reclaimed' } | Select-Object -Last 1)
        $results.Add([pscustomobject]@{ Op='Docker system prune'; Status=([string]$last).Trim() })
    } catch { $results.Add([pscustomobject]@{ Op='Docker system prune'; Status=('ERR ' + $_.Exception.Message) }) }
    return $results
}

# ---------- 5. HTML 報告 ----------
function New-HtmlReport {
    param(
        [object[]]$Items,
        [object[]]$Perf,
        [double]$TotalBytes,
        [double]$DevBytes,
        [double]$SysBytes
    )
    $rowsSb = [System.Text.StringBuilder]::new()
    $top = $Items | Sort-Object @{ e = 'Bytes'; desc = $true } | Select-Object -First 250
    foreach ($c in $top) {
        $act = ''
        if ($null -ne $c.Action) { $act = [string]$c.Action }
        $null = $rowsSb.AppendLine('<tr><td class="p">' + [System.Net.WebUtility]::HtmlEncode([string]$c.Path) + '</td><td>' + [System.Net.WebUtility]::HtmlEncode([string]$c.Category) + '</td><td><span class="bx">' + [System.Net.WebUtility]::HtmlEncode([string]$c.Box) + '</span></td><td class="r">' + (Format-Size -Bytes $c.Bytes) + '</td><td>' + [System.Net.WebUtility]::HtmlEncode($act) + '</td></tr>')
    }
    $perfSb = [System.Text.StringBuilder]::new()
    foreach ($p in $Perf) {
        $null = $perfSb.AppendLine('<tr><td>' + [System.Net.WebUtility]::HtmlEncode([string]$p.Op) + '</td><td>' + [System.Net.WebUtility]::HtmlEncode([string]$p.Status) + '</td></tr>')
    }
    # 分類彙總 category rollup
    $rollSb = [System.Text.StringBuilder]::new()
    $groups = $Items | Group-Object -Property Category | ForEach-Object {
        $sum = ($_.Group | Measure-Object -Property Bytes -Sum).Sum
        if ($null -eq $sum) { $sum = 0 }
        [pscustomobject]@{ Category = $_.Name; Count = $_.Count; Bytes = $sum }
    } | Sort-Object @{ e = 'Bytes'; desc = $true }
    foreach ($g in $groups) {
        $null = $rollSb.AppendLine('<tr><td>' + [System.Net.WebUtility]::HtmlEncode([string]$g.Category) + '</td><td class="r">' + [string]$g.Count + '</td><td class="r">' + (Format-Size -Bytes $g.Bytes) + '</td></tr>')
    }
    $adminTxt = 'Standard'
    if ($script:IsAdmin) { $adminTxt = 'Administrator' }
    $elapsed = ((Get-Date) - $script:StartTime).TotalSeconds

    $tpl = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA TriBox Optimizer</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;800&display=swap" rel="stylesheet">
<style>
:root{--blue:@@BLUE@@;--grey:@@GREY@@;--teal:@@TEAL@@;--red:@@RED@@;--green:@@GREEN@@;--bg:#16181d;--card:#1f232b;--line:#2c313b;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:#e8e6e1;font-family:'DM Sans',sans-serif;padding:32px;line-height:1.5}
h1{font-family:'Syne',sans-serif;font-weight:800;font-size:30px;letter-spacing:.5px}
h1 .seal{color:var(--teal)}
.sub{color:var(--grey);font-family:'DM Mono',monospace;font-size:13px;margin-top:6px}
.mode{display:inline-block;margin-top:14px;padding:5px 14px;border:1px solid var(--blue);border-radius:4px;font-family:'DM Mono',monospace;font-size:13px;color:var(--blue)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin:26px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px;opacity:0;transform:translateY(14px);animation:rise .6s forwards}
.card:nth-child(2){animation-delay:.08s}.card:nth-child(3){animation-delay:.16s}.card:nth-child(4){animation-delay:.24s}
.card .k{font-family:'DM Mono',monospace;font-size:12px;color:var(--grey);text-transform:uppercase;letter-spacing:1px}
.card .v{font-family:'Syne',sans-serif;font-weight:800;font-size:28px;margin-top:8px}
.v.total{color:var(--teal)}.v.dev{color:var(--blue)}.v.sys{color:var(--red)}.v.cnt{color:var(--green)}
@keyframes rise{to{opacity:1;transform:none}}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:14px}
th{text-align:left;font-family:'DM Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--grey);padding:11px 14px;border-bottom:1px solid var(--line)}
td{padding:9px 14px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}
td.p{font-family:'DM Mono',monospace;font-size:12px;color:#cfcdc7;word-break:break-all;max-width:520px}
td.r{font-family:'DM Mono',monospace;text-align:right;color:var(--teal);white-space:nowrap}
.bx{font-family:'DM Mono',monospace;font-size:11px;padding:2px 7px;border-radius:3px;background:#272c35;color:var(--blue)}
tr:hover td{background:#222630}
h2{font-family:'Syne',sans-serif;font-weight:600;font-size:18px;margin:30px 0 4px}
.foot{color:var(--grey);font-family:'DM Mono',monospace;font-size:12px;margin-top:24px}
.warn{color:var(--red)}
</style></head><body>
<h1><span class="seal">理</span> VIA TriBox Optimizer</h1>
<div class="sub">三合一系統優化 · BOX1 DEV 開發回收 · BOX2 SYSTEM 系統清理 · BOX3 PERF 效能優化</div>
<div class="mode">MODE = @@MODE@@ &nbsp;·&nbsp; @@ADMIN@@ &nbsp;·&nbsp; @@TS@@</div>
<div class="grid">
<div class="card"><div class="k">Total Reclaimable</div><div class="v total">@@TOTAL@@</div></div>
<div class="card"><div class="k">BOX1 Dev Caches</div><div class="v dev">@@DEV@@</div></div>
<div class="card"><div class="k">BOX2 System Junk</div><div class="v sys">@@SYS@@</div></div>
<div class="card"><div class="k">Targets Found</div><div class="v cnt">@@CNT@@</div></div>
</div>
<h2>分類彙總 Category Rollup</h2>
<table><thead><tr><th>Category</th><th>Dirs</th><th>Size</th></tr></thead>
<tbody>@@ROLL@@</tbody></table>
<h2>清理目標 Cleanup Targets <span class="sub">(top 250 by size)</span></h2>
<table><thead><tr><th>Path</th><th>Category</th><th>Box</th><th>Size</th><th>Action</th></tr></thead>
<tbody>@@ROWS@@</tbody></table>
<h2>效能優化 Performance Ops</h2>
<table><thead><tr><th>Operation</th><th>Status</th></tr></thead>
<tbody>@@PERF@@</tbody></table>
<div class="foot">elapsed @@ELAPSED@@s · protected roots locked: envs / VeritasIntelligenceAnalytics / OneDrive / Windows / ProgramFiles<br>Scan 模式僅統計不刪除 · Quarantine 移入隔離區可還原 · Recycle 送資源回收筒 · Permanent 永久刪除</div>
</body></html>
'@

    $cntTxt = ([string]$Items.Count)
    $html = $tpl.Replace('@@BLUE@@',$script:CssBlue).Replace('@@GREY@@',$script:CssGrey).Replace('@@TEAL@@',$script:CssTeal).Replace('@@RED@@',$script:CssRed).Replace('@@GREEN@@',$script:CssGreen)
    $html = $html.Replace('@@MODE@@',$Mode).Replace('@@ADMIN@@',$adminTxt).Replace('@@TS@@',$script:Ts)
    $html = $html.Replace('@@TOTAL@@',(Format-Size -Bytes $TotalBytes)).Replace('@@DEV@@',(Format-Size -Bytes $DevBytes)).Replace('@@SYS@@',(Format-Size -Bytes $SysBytes))
    $html = $html.Replace('@@CNT@@',$cntTxt).Replace('@@ELAPSED@@',('{0:N1}' -f $elapsed))
    $html = $html.Replace('@@ROWS@@',$rowsSb.ToString()).Replace('@@PERF@@',$perfSb.ToString()).Replace('@@ROLL@@',$rollSb.ToString())
    [System.IO.File]::WriteAllText($script:ReportPath, $html, [System.Text.UTF8Encoding]::new($false))
}

# ---------- 6. Downloads 管理模組 ----------
function Get-DownloadsRoot {
    if (-not [string]::IsNullOrWhiteSpace($DownloadsRoot)) { return $DownloadsRoot }
    $p = ''
    try {
        $rk = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders' -ErrorAction Stop
        $g  = $rk.'{374DE290-123F-4565-9164-39C4925E467B}'
        if (-not [string]::IsNullOrWhiteSpace($g)) { $p = [System.Environment]::ExpandEnvironmentVariables($g) }
    } catch { }
    if ([string]::IsNullOrWhiteSpace($p)) { $p = Join-Path $env:USERPROFILE 'Downloads' }
    return $p
}

function Get-FastHash {
    param([string]$Path, [int64]$Size)
    $sha = $null
    $fs  = $null
    try {
        $sha   = [System.Security.Cryptography.SHA256]::Create()
        $fs    = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $chunk = 65536
        $buf   = [byte[]]::new($chunk)
        $first = [int][Math]::Min([int64]$chunk, $Size)
        $r1    = $fs.Read($buf, 0, $first)
        $null  = $sha.TransformBlock($buf, 0, $r1, $null, 0)
        if ($Size -gt ($chunk * 2)) {
            $null = $fs.Seek(-1 * $chunk, [System.IO.SeekOrigin]::End)
            $r2   = $fs.Read($buf, 0, $chunk)
            $null = $sha.TransformBlock($buf, 0, $r2, $null, 0)
        }
        $lenBytes = [System.BitConverter]::GetBytes($Size)
        $null     = $sha.TransformFinalBlock($lenBytes, 0, $lenBytes.Length)
        return [System.BitConverter]::ToString($sha.Hash).Replace('-', '')
    } catch {
        return ''
    } finally {
        if ($null -ne $fs)  { $fs.Dispose() }
        if ($null -ne $sha) { $sha.Dispose() }
    }
}

function Get-DownloadsInventory {
    param([string]$Root)
    $files = [System.Collections.Generic.List[object]]::new()
    if (-not (Test-Path -LiteralPath $Root)) { return $files }
    $all = @()
    try {
        $di  = [System.IO.DirectoryInfo]::new($Root)
        $opt = [System.IO.EnumerationOptions]::new()
        $opt.IgnoreInaccessible    = $true
        $opt.RecurseSubdirectories = $true
        $opt.AttributesToSkip      = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
        $all = $di.EnumerateFiles('*', $opt)
    } catch { $all = @() }
    $id = 0
    foreach ($f in $all) {
        $ext = $f.Extension.ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($ext)) { $ext = '(none)' }
        $files.Add([pscustomobject]@{
            id    = $id
            path  = $f.FullName
            name  = $f.Name
            ext   = $ext
            size  = [int64]$f.Length
            mtime = $f.LastWriteTime.ToString('yyyy-MM-dd')
            mts   = [int64]([DateTimeOffset]$f.LastWriteTime).ToUnixTimeSeconds()
            dup   = ''
        })
        $id = $id + 1
    }
    return $files
}

function Add-DuplicateKeys {
    param([System.Collections.Generic.List[object]]$Inv)
    $bySig = [System.Collections.Generic.Dictionary[string,object]]::new()
    foreach ($f in $Inv) {
        $sig = $f.ext + '|' + [string]$f.size
        if (-not $bySig.ContainsKey($sig)) { $bySig[$sig] = [System.Collections.Generic.List[object]]::new() }
        $bySig[$sig].Add($f)
    }
    foreach ($sig in $bySig.Keys) {
        $grp = $bySig[$sig]
        if ($grp.Count -ge 2) {
            foreach ($f in $grp) { $f.dup = (Get-FastHash -Path $f.path -Size $f.size) }
        }
    }
}

function Invoke-DownloadRemove {
    param([string]$Path, [string]$RootGuard, [string]$ActMode)
    $full = ''
    try { $full = [System.IO.Path]::GetFullPath($Path) } catch { return 'BAD-PATH' }
    $fn = $full.TrimEnd('\').ToLowerInvariant()
    $rg = $RootGuard.TrimEnd('\').ToLowerInvariant()
    if (-not $fn.StartsWith($rg + '\')) { return 'OUT-OF-SCOPE' }
    foreach ($d in @($env:WINDIR, 'C:\Users\tonyk\envs', 'C:\VeritasIntelligenceAnalytics')) {
        $dl = $d.TrimEnd('\').ToLowerInvariant()
        if ($fn -eq $dl -or $fn.StartsWith($dl + '\')) { return 'PROTECTED' }
    }
    if (-not (Test-Path -LiteralPath $full)) { return 'MISSING' }
    try {
        $at = [System.IO.File]::GetAttributes($full)
        if (($at -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return 'REPARSE' }
    } catch { }
    try {
        if ($ActMode -eq 'Permanent') {
            Remove-Item -LiteralPath $full -Force -ErrorAction Stop
        } elseif ($ActMode -eq 'Recycle') {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($full, 'OnlyErrorDialogs', 'SendToRecycleBin')
        } elseif ($ActMode -eq 'Quarantine') {
            $null = [System.IO.Directory]::CreateDirectory($script:QuarantineRoot)
            $flat = ($full -replace '[:\\/]', '_')
            if ($flat.Length -gt 120) { $flat = $flat.Substring($flat.Length - 120) }
            $dest = Join-Path $script:QuarantineRoot $flat
            Move-Item -LiteralPath $full -Destination $dest -Force -ErrorAction Stop
            Write-Manifest ([pscustomobject]@{ ts = $script:Ts; src = $full; dst = $dest; cat = 'Downloads' })
        } else {
            return 'SCAN'
        }
        return 'OK'
    } catch {
        return ('FAIL ' + $_.Exception.Message)
    }
}

function Send-Http {
    param([System.Net.HttpListenerContext]$Ctx, [int]$Code, [string]$Body, [string]$Ctype = 'text/plain; charset=utf-8')
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $Ctx.Response.StatusCode      = $Code
        $Ctx.Response.ContentType     = $Ctype
        $Ctx.Response.ContentLength64 = $bytes.Length
        $Ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        $Ctx.Response.OutputStream.Close()
    } catch { }
}

function New-DownloadsHtml {
    param([string]$Json, [string]$Csrf, [string]$Root, [int]$Count, [double]$Total)
    $tpl = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Downloads Manager</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;800&display=swap" rel="stylesheet">
<style>
:root{--blue:@@BLUE@@;--grey:@@GREY@@;--teal:@@TEAL@@;--red:@@RED@@;--green:@@GREEN@@;--bg:#14171c;--card:#1d2128;--line:#2b313b;--ink:#e8e6e1;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;padding:24px 28px 110px;line-height:1.45}
h1{font-family:'Syne',sans-serif;font-weight:800;font-size:26px}
h1 .s{color:var(--blue)}
.sub{color:var(--grey);font-family:'DM Mono',monospace;font-size:12px;margin-top:5px;word-break:break-all}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:18px 0}
.row{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center}
label{font-family:'DM Mono',monospace;font-size:12px;color:var(--grey)}
input[type=date],input[type=text],select{background:#11141a;border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:6px 9px;font-family:'DM Mono',monospace;font-size:13px}
input[type=text]{min-width:140px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.seg button{background:#11141a;color:var(--grey);border:0;padding:6px 12px;font-family:'DM Mono',monospace;font-size:12px;cursor:pointer}
.seg button.on{background:var(--blue);color:#fff}
.kwwrap{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.btn{background:var(--blue);color:#fff;border:0;border-radius:6px;padding:7px 14px;font-family:'DM Mono',monospace;font-size:12px;cursor:pointer}
.btn.ghost{background:#11141a;color:var(--ink);border:1px solid var(--line)}
.btn.warn{background:var(--red)}
.chip{font-family:'DM Mono',monospace;font-size:11px;padding:3px 9px;border:1px solid var(--line);border-radius:20px;color:var(--grey);cursor:pointer;background:#11141a}
.chip.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.stat{font-family:'DM Mono',monospace;font-size:12px;color:var(--grey)}
.stat b{color:var(--teal);font-weight:500}
table{width:100%;border-collapse:collapse;table-layout:fixed}
th{position:sticky;top:0;background:#222732;text-align:left;font-family:'DM Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--grey);padding:9px 12px;border-bottom:1px solid var(--line);cursor:pointer}
td{padding:7px 12px;border-bottom:1px solid var(--line);font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
td.nm{font-family:'DM Mono',monospace;font-size:12px;color:#d6d4ce}
td.r{font-family:'DM Mono',monospace;text-align:right;color:var(--teal)}
td.c{text-align:center}
tr.sel td{background:#23304a}
tr:hover td{background:#262b35}
.dupb{font-family:'DM Mono',monospace;font-size:10px;padding:1px 6px;border-radius:3px;background:#3a2a28;color:var(--red)}
.tbox{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:auto;max-height:60vh}
.gcard{border:1px solid var(--line);border-radius:8px;margin:12px 0;overflow:hidden}
.ghead{background:#222732;padding:8px 14px;font-family:'DM Mono',monospace;font-size:12px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.ghead .meta{color:var(--grey)}
.actbar{position:fixed;left:0;right:0;bottom:0;background:#10131a;border-top:1px solid var(--line);padding:12px 28px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.toast{position:fixed;right:24px;bottom:84px;background:var(--card);border:1px solid var(--teal);border-radius:8px;padding:10px 16px;font-family:'DM Mono',monospace;font-size:12px;opacity:0;transition:opacity .3s}
.toast.show{opacity:1}
.muted{color:var(--grey);font-size:12px;font-family:'DM Mono',monospace;padding:10px 12px}
</style></head><body>
<h1><span class="s">理</span> VIA Downloads Manager</h1>
<div class="sub">@@ROOT@@ &nbsp;·&nbsp; @@COUNT@@ files &nbsp;·&nbsp; @@TOTAL@@</div>

<div class="panel">
  <div class="row">
    <label>日期模式</label>
    <div class="seg" id="dateMode">
      <button data-m="all" class="on">全部 All</button>
      <button data-m="range">區間 Range</button>
      <button data-m="before">之前 Before</button>
    </div>
    <label>從</label><input type="date" id="from">
    <label>到 / 之前</label><input type="date" id="to">
  </div>
  <div class="row" style="margin-top:14px">
    <label>關鍵字</label>
    <div class="kwwrap" id="kwwrap"></div>
    <button class="btn ghost" id="addKw">+ 新增關鍵字</button>
    <div class="seg" id="kwMode">
      <button data-k="any" class="on">任一 ANY</button>
      <button data-k="all">全部 ALL</button>
    </div>
  </div>
  <div class="row" style="margin-top:14px">
    <label>類型</label><div class="kwwrap" id="extchips"></div>
  </div>
  <div class="row" style="margin-top:14px">
    <div class="seg" id="viewMode">
      <button data-v="list" class="on">清單 List</button>
      <button data-v="matrix">重複矩陣 Duplicate Matrix</button>
    </div>
    <button class="btn ghost" id="selAll">全選目前篩選</button>
    <button class="btn ghost" id="selNone">清除選取</button>
    <span class="stat" id="filtStat"></span>
  </div>
</div>

<div id="view"></div>

<div class="actbar">
  <span class="stat">已選 <b id="selCnt">0</b> · <b id="selSize">0 B</b></span>
  <label>處理階梯</label>
  <select id="tier">
    <option value="Quarantine">Quarantine 隔離可還原</option>
    <option value="Recycle">Recycle 資源回收筒</option>
    <option value="Permanent">Permanent 永久刪除</option>
  </select>
  <button class="btn warn" id="apply">執行 Apply</button>
  <button class="btn ghost" id="stop">停止伺服器</button>
</div>
<div class="toast" id="toast"></div>

<script>
const DATA = @@DATA@@;
const CSRF = '@@CSRF@@';
let rows = DATA.slice();
let selected = new Set();
const state = { dateMode:'all', from:'', to:'', kws:[], kwMode:'any', exts:new Set(), view:'list' };
const RENDER_CAP = 1500;

function fmt(b){ if(b>=1073741824)return (b/1073741824).toFixed(2)+' GB'; if(b>=1048576)return (b/1048576).toFixed(2)+' MB'; if(b>=1024)return (b/1024).toFixed(2)+' KB'; return b+' B'; }
function esc(s){ return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

function passDate(f){
  if(state.dateMode==='all') return true;
  if(state.dateMode==='before') return state.to ? f.mtime <= state.to : true;
  let ok=true; if(state.from) ok = ok && f.mtime >= state.from; if(state.to) ok = ok && f.mtime <= state.to; return ok;
}
function passKw(f){
  if(state.kws.length===0) return true;
  const n=f.name.toLowerCase();
  const hits=state.kws.map(k=>n.includes(k.toLowerCase()));
  return state.kwMode==='all' ? hits.every(x=>x) : hits.some(x=>x);
}
function passExt(f){ return state.exts.size===0 || state.exts.has(f.ext); }
function filtered(){ return rows.filter(f=>passDate(f)&&passKw(f)&&passExt(f)); }

function buildKw(){
  const w=document.getElementById('kwwrap'); w.innerHTML='';
  const need=Math.max(5, state.kws.length+1);
  for(let i=0;i<need;i++){
    const inp=document.createElement('input'); inp.type='text'; inp.placeholder='關鍵字'+(i+1);
    inp.value=state.kws[i]||''; inp.oninput=collectKw; w.appendChild(inp);
  }
}
function collectKw(){
  const vals=[...document.querySelectorAll('#kwwrap input')].map(x=>x.value.trim()).filter(x=>x);
  state.kws=vals; render();
}
function buildExt(){
  const set=new Set(DATA.map(f=>f.ext)); const w=document.getElementById('extchips'); w.innerHTML='';
  [...set].sort().forEach(e=>{
    const c=document.createElement('span'); c.className='chip'; c.textContent=e;
    c.onclick=()=>{ if(state.exts.has(e)){state.exts.delete(e);c.classList.remove('on');} else {state.exts.add(e);c.classList.add('on');} render(); };
    w.appendChild(c);
  });
}

function autoFit(table){
  const cols=table.querySelectorAll('colgroup col'); if(!cols.length) return;
  const heads=table.querySelectorAll('thead th');
  const sampleRows=[...table.querySelectorAll('tbody tr')].slice(0,200);
  const cv=document.createElement('canvas'); const ctx=cv.getContext('2d'); ctx.font="12px 'DM Mono', monospace";
  for(let i=0;i<cols.length;i++){
    if(cols[i].dataset.fix){ continue; }
    let max=ctx.measureText(heads[i]?heads[i].textContent:'').width;
    sampleRows.forEach(r=>{ const cell=r.children[i]; if(cell){ const w=ctx.measureText(cell.textContent).width; if(w>max)max=w; } });
    const px=Math.min(Math.max(Math.ceil(max)+28,60),520);
    cols[i].style.width=px+'px';
  }
}

function render(){
  const v=document.getElementById('view');
  const f=filtered();
  document.getElementById('filtStat').textContent='符合 '+f.length+' 檔 · '+fmt(f.reduce((a,b)=>a+b.size,0));
  if(state.view==='list'){ renderList(v,f); } else { renderMatrix(v,f); }
  updateBar();
}

function renderList(v,f){
  const show=f.slice(0,RENDER_CAP);
  let h='<div class="tbox"><table><colgroup>'
    +'<col data-fix="1" style="width:38px"><col><col><col data-fix="1" style="width:104px"><col data-fix="1" style="width:118px"><col data-fix="1" style="width:74px"></colgroup>'
    +'<thead><tr><th></th><th data-s="name">Name</th><th data-s="ext">Ext</th><th data-s="size">Size</th><th data-s="mtime">Modified</th><th>Dup</th></tr></thead><tbody>';
  show.forEach(x=>{
    const sel=selected.has(x.path)?' class="sel"':'';
    const db=x.dup?'<span class="dupb">DUP</span>':'';
    h+='<tr'+sel+' data-p="'+esc(x.path)+'"><td class="c"><input type="checkbox" data-p="'+esc(x.path)+'"'+(selected.has(x.path)?' checked':'')+'></td>'
      +'<td class="nm" title="'+esc(x.path)+'">'+esc(x.name)+'</td><td>'+esc(x.ext)+'</td><td class="r">'+fmt(x.size)+'</td><td>'+esc(x.mtime)+'</td><td class="c">'+db+'</td></tr>';
  });
  h+='</tbody></table></div>';
  if(f.length>RENDER_CAP){ h+='<div class="muted">顯示前 '+RENDER_CAP+' 筆（共 '+f.length+'）· 「全選目前篩選」仍作用於全部</div>'; }
  v.innerHTML=h;
  v.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>{ toggle(cb.dataset.p); });
  autoFit(v.querySelector('table'));
}

function renderMatrix(v,f){
  const groups=new Map();
  f.forEach(x=>{ const key=x.dup?('h:'+x.dup):(x.ext+'|'+x.size); if(!groups.has(key))groups.set(key,[]); groups.get(key).push(x); });
  const arr=[...groups.values()].filter(g=>g.length>=2).sort((a,b)=>b.reduce((s,x)=>s+x.size,0)-a.reduce((s,x)=>s+x.size,0));
  if(!arr.length){ v.innerHTML='<div class="muted">目前篩選下無重複（同類型+同大小）群組。</div>'; return; }
  let h='';
  arr.forEach((g,gi)=>{
    const tot=g.reduce((s,x)=>s+x.size,0); const confirmed=g[0].dup?' · 內容雜湊一致':'';
    h+='<div class="gcard"><div class="ghead"><span>'+esc(g[0].ext)+' · '+fmt(g[0].size)+' <span class="meta">x'+g.length+confirmed+'</span></span>'
      +'<span><span class="meta">合計 '+fmt(tot)+'</span> &nbsp; <button class="btn" data-g="'+gi+'">保留最新·其餘全選</button></span></div>'
      +'<div class="tbox" style="max-height:none"><table><colgroup><col data-fix="1" style="width:38px"><col><col data-fix="1" style="width:118px"></colgroup><tbody>';
    g.forEach(x=>{ const sel=selected.has(x.path)?' class="sel"':'';
      h+='<tr'+sel+'><td class="c"><input type="checkbox" data-p="'+esc(x.path)+'"'+(selected.has(x.path)?' checked':'')+'></td><td class="nm" title="'+esc(x.path)+'">'+esc(x.name)+'</td><td>'+esc(x.mtime)+'</td></tr>'; });
    h+='</tbody></table></div></div>';
  });
  v.innerHTML=h;
  v.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>toggle(cb.dataset.p));
  v.querySelectorAll('button[data-g]').forEach(b=>b.onclick=()=>{
    const g=arr[+b.dataset.g]; let newest=g[0]; g.forEach(x=>{ if(x.mts>newest.mts)newest=x; });
    g.forEach(x=>{ if(x.path!==newest.path) selected.add(x.path); }); render();
  });
}

function toggle(p){ if(selected.has(p))selected.delete(p); else selected.add(p); updateBar(); 
  document.querySelectorAll('tr[data-p="'+CSS.escape(p)+'"]').forEach(r=>r.classList.toggle('sel',selected.has(p))); }
function updateBar(){
  const map=new Map(DATA.map(f=>[f.path,f.size]));
  let sz=0; selected.forEach(p=>{ sz+=map.get(p)||0; });
  document.getElementById('selCnt').textContent=selected.size;
  document.getElementById('selSize').textContent=fmt(sz);
}
function toast(msg){ const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2600); }

document.getElementById('dateMode').onclick=e=>{ if(e.target.dataset.m){ [...e.currentTarget.children].forEach(b=>b.classList.remove('on')); e.target.classList.add('on'); state.dateMode=e.target.dataset.m; render(); } };
document.getElementById('kwMode').onclick=e=>{ if(e.target.dataset.k){ [...e.currentTarget.children].forEach(b=>b.classList.remove('on')); e.target.classList.add('on'); state.kwMode=e.target.dataset.k; render(); } };
document.getElementById('viewMode').onclick=e=>{ if(e.target.dataset.v){ [...e.currentTarget.children].forEach(b=>b.classList.remove('on')); e.target.classList.add('on'); state.view=e.target.dataset.v; render(); } };
document.getElementById('from').onchange=e=>{ state.from=e.target.value; render(); };
document.getElementById('to').onchange=e=>{ state.to=e.target.value; render(); };
document.getElementById('addKw').onclick=()=>{ state.kws.push(''); buildKw(); };
document.getElementById('selAll').onclick=()=>{ filtered().forEach(x=>selected.add(x.path)); render(); };
document.getElementById('selNone').onclick=()=>{ selected.clear(); render(); };
document.getElementById('stop').onclick=async()=>{ try{ await fetch('/api/stop'); }catch(e){} toast('伺服器已停止，可關閉此頁'); };
document.getElementById('apply').onclick=async()=>{
  const paths=[...selected]; if(!paths.length){ toast('尚未選取'); return; }
  const mode=document.getElementById('tier').value;
  if(mode==='Permanent' && !confirm('永久刪除 '+paths.length+' 個檔案，無法還原。確定？')) return;
  try{
    const res=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-VIA-CSRF':CSRF},body:JSON.stringify({mode,paths})});
    const j=await res.json();
    const ok=new Set(j.results.filter(r=>r.r==='OK').map(r=>r.p));
    const freed=rows.filter(f=>ok.has(f.path)).reduce((a,b)=>a+b.size,0);
    rows=rows.filter(f=>!ok.has(f.path)); ok.forEach(p=>selected.delete(p));
    render(); toast(mode+' 完成 '+ok.size+' 檔 · 釋出 '+fmt(freed));
  }catch(e){ toast('動作失敗 '+e); }
};

buildKw(); buildExt(); render();
</script>
</body></html>
'@
    $h = $tpl.Replace('@@BLUE@@', $script:CssBlue).Replace('@@GREY@@', $script:CssGrey).Replace('@@TEAL@@', $script:CssTeal).Replace('@@RED@@', $script:CssRed).Replace('@@GREEN@@', $script:CssGreen)
    $h = $h.Replace('@@ROOT@@', [System.Net.WebUtility]::HtmlEncode($Root)).Replace('@@COUNT@@', [string]$Count).Replace('@@TOTAL@@', (Format-Size -Bytes $Total))
    $h = $h.Replace('@@CSRF@@', $Csrf).Replace('@@DATA@@', $Json)
    return $h
}

function Start-DownloadsManager {
    $root = Get-DownloadsRoot
    Write-Host ''
    Write-Host '理  VIA Downloads Manager' -ForegroundColor Cyan
    Write-Host ('   根目錄 ' + $root) -ForegroundColor DarkGray
    if (-not (Test-Path -LiteralPath $root)) { Write-Host '   找不到 Downloads 目錄' -ForegroundColor Yellow; return }

    Write-Progress -Id 2 -Activity 'Downloads Manager' -Status '掃描檔案' -PercentComplete 20
    $inv = Get-DownloadsInventory -Root $root
    Write-Progress -Id 2 -Activity 'Downloads Manager' -Status '重複偵測 type+size+hash' -PercentComplete 55
    Add-DuplicateKeys -Inv $inv
    Write-Progress -Id 2 -Activity 'Downloads Manager' -Completed

    $total = ($inv | Measure-Object -Property size -Sum).Sum
    if ($null -eq $total) { $total = 0 }
    $json = '[]'
    if ($inv.Count -eq 1) {
        $json = '[' + ($inv | ConvertTo-Json -Depth 4 -Compress) + ']'
    } elseif ($inv.Count -gt 1) {
        $json = ($inv | ConvertTo-Json -Depth 4 -Compress)
    }

    $script:DlRoot = $root
    $script:DlCsrf = [guid]::NewGuid().ToString('N')
    $html = New-DownloadsHtml -Json $json -Csrf $script:DlCsrf -Root $root -Count $inv.Count -Total $total

    $allowHosts = @(('127.0.0.1:' + [string]$DownloadsPort), ('localhost:' + [string]$DownloadsPort))
    $prefix     = ('http://127.0.0.1:' + [string]$DownloadsPort + '/')
    $listener   = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add($prefix)
    try {
        $listener.Start()
    } catch {
        Write-Host ('   無法在 port ' + [string]$DownloadsPort + ' 啟動，改用 -DownloadsPort 指定其他埠') -ForegroundColor Yellow
        return
    }

    Write-Host ('   伺服器 ' + $prefix) -ForegroundColor Green
    Write-Host '   瀏覽器已開啟；頁面上「停止伺服器」或 Ctrl+C 可結束' -ForegroundColor DarkGray
    try { Start-Process $prefix } catch { }

    try {
        while ($listener.IsListening) {
            $ctx = $null
            try { $ctx = $listener.GetContext() } catch { break }
            $req = $ctx.Request

            if (-not [System.Net.IPAddress]::IsLoopback($req.RemoteEndPoint.Address)) { Send-Http -Ctx $ctx -Code 403 -Body 'forbidden'; continue }
            $hn = ''
            if ($null -ne $req.UserHostName) { $hn = $req.UserHostName.ToLowerInvariant() }
            if (-not ($allowHosts -contains $hn)) { Send-Http -Ctx $ctx -Code 403 -Body 'bad host'; continue }

            $route = $req.Url.AbsolutePath
            if ($req.HttpMethod -eq 'GET' -and $route -eq '/') {
                Send-Http -Ctx $ctx -Code 200 -Body $html -Ctype 'text/html; charset=utf-8'
            } elseif ($req.HttpMethod -eq 'GET' -and $route -eq '/api/stop') {
                Send-Http -Ctx $ctx -Code 200 -Body 'stopping'
                break
            } elseif ($req.HttpMethod -eq 'POST' -and $route -eq '/api/action') {
                if ($req.Headers['X-VIA-CSRF'] -ne $script:DlCsrf) { Send-Http -Ctx $ctx -Code 403 -Body 'csrf'; continue }
                if ($req.ContentLength64 -gt 2097152) { Send-Http -Ctx $ctx -Code 413 -Body 'too large'; continue }
                $body = ''
                $sr   = [System.IO.StreamReader]::new($req.InputStream, $req.ContentEncoding)
                try { $body = $sr.ReadToEnd() } finally { $sr.Dispose() }
                $payload = $null
                try { $payload = $body | ConvertFrom-Json } catch { Send-Http -Ctx $ctx -Code 400 -Body 'bad json'; continue }
                $actMode = [string]$payload.mode
                $arr = [System.Collections.Generic.List[object]]::new()
                foreach ($pp in @($payload.paths)) {
                    $r = Invoke-DownloadRemove -Path ([string]$pp) -RootGuard $script:DlRoot -ActMode $actMode
                    $arr.Add([pscustomobject]@{ p = [string]$pp; r = $r })
                }
                $resp = (@{ ok = $true; results = $arr } | ConvertTo-Json -Depth 4 -Compress)
                Send-Http -Ctx $ctx -Code 200 -Body $resp -Ctype 'application/json; charset=utf-8'
            } else {
                Send-Http -Ctx $ctx -Code 404 -Body 'not found'
            }
        }
    } finally {
        try { $listener.Stop() } catch { }
        try { $listener.Close() } catch { }
    }
    Write-Host '   Downloads Manager 已結束' -ForegroundColor DarkGray
}

# ---------- 6C. 控制台 Control Center（自動跳出互動 UI，一鍵安全清理）----------
function Get-DiskInfo {
    $list = [System.Collections.Generic.List[object]]::new()
    try {
        foreach ($d in [System.IO.DriveInfo]::GetDrives()) {
            if (-not $d.IsReady) { continue }
            if ($d.DriveType -ne [System.IO.DriveType]::Fixed) { continue }
            $list.Add([pscustomobject]@{ name = $d.Name; total = [int64]$d.TotalSize; free = [int64]$d.AvailableFreeSpace })
        }
    } catch { }
    return $list
}

function Invoke-SingleOpt {
    param([string]$Op)
    try {
        switch ($Op) {
            'dns' {
                Clear-DnsClientCache
                return 'DNS 快取已清除'
            }
            'recycle' {
                Clear-RecycleBin -Force -ErrorAction Stop
                return '資源回收筒已清空'
            }
            'trim' {
                if (-not $script:IsAdmin) { return '需系統管理員權限（請以管理員開 PS7）' }
                $media = 'Unspecified'
                $phys  = Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $phys) { $media = [string]$phys.MediaType }
                if ($media -eq 'HDD') {
                    Optimize-Volume -DriveLetter C -Defrag -ErrorAction Stop
                    return 'Defrag C 完成 (HDD)'
                } else {
                    Optimize-Volume -DriveLetter C -ReTrim -ErrorAction Stop
                    return ('ReTrim C 完成 (' + $media + ')')
                }
            }
            'dism' {
                if (-not $script:IsAdmin) { return '需系統管理員權限（請以管理員開 PS7）' }
                $r   = Invoke-DeepClean
                $txt = ''
                foreach ($x in $r) { $txt = $txt + [string]$x.Op + '=' + [string]$x.Status + '; ' }
                return $txt.Trim()
            }
            'smart' {
                $rel = Get-PhysicalDisk -ErrorAction SilentlyContinue | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $rel) { return ('Wear=' + [string]$rel.Wear + ' · ReadErr=' + [string]$rel.ReadErrorsTotal) }
                return '無 SMART 資料'
            }
            default {
                return '未知操作'
            }
        }
    } catch {
        return ('ERR ' + $_.Exception.Message)
    }
}

function Get-SafetyInfo {
    param([string]$Category)
    switch -Wildcard ($Category) {
        'PyCache/Tooling' { return @{ lvl = 'safe';    txt = 'Python 位元組碼／工具快取，刪後自動重生' } }
        'Egg-Info'        { return @{ lvl = 'safe';    txt = '非套件庫的套件中繼，安全' } }
        'User Temp'       { return @{ lvl = 'safe';    txt = '使用者暫存檔，安全' } }
        'Windows Temp'    { return @{ lvl = 'safe';    txt = '系統暫存，安全' } }
        'CrashDumps'      { return @{ lvl = 'safe';    txt = '當機傾印檔，安全' } }
        'WER*'            { return @{ lvl = 'safe';    txt = 'Windows 錯誤回報，安全' } }
        'INetCache'       { return @{ lvl = 'safe';    txt = '系統網頁快取，安全' } }
        'WinUpdate cache' { return @{ lvl = 'safe';    txt = 'Windows Update 下載快取，安全（需要時重新下載）' } }
        'pip cache'       { return @{ lvl = 'rebuild'; txt = 'pip 下載快取，刪後重裝會重新下載' } }
        'npm cache'       { return @{ lvl = 'rebuild'; txt = 'npm 下載快取，可重新下載' } }
        'yarn cache'      { return @{ lvl = 'rebuild'; txt = 'yarn 快取，可重新下載' } }
        'pnpm store'      { return @{ lvl = 'rebuild'; txt = 'pnpm 全域儲存，可重新下載' } }
        'uv cache'        { return @{ lvl = 'rebuild'; txt = 'uv 下載快取（常很大），可重新下載' } }
        'HF cache'        { return @{ lvl = 'rebuild'; txt = 'HuggingFace 模型快取，刪後需重新下載（可能很大）' } }
        'torch cache'     { return @{ lvl = 'rebuild'; txt = 'torch 快取，可重新下載' } }
        'NuGet pkg'       { return @{ lvl = 'rebuild'; txt = 'NuGet 套件快取，可重新還原' } }
        'cargo*'          { return @{ lvl = 'rebuild'; txt = 'cargo 套件快取，可重新下載' } }
        'go modcache'     { return @{ lvl = 'rebuild'; txt = 'go 模組快取，可重新下載' } }
        'gradle'          { return @{ lvl = 'rebuild'; txt = 'gradle 快取，可重新下載' } }
        'maven m2'        { return @{ lvl = 'rebuild'; txt = 'maven 快取，可重新下載' } }
        'conda pkgs'      { return @{ lvl = 'rebuild'; txt = 'conda 套件 tarball 快取，可重新下載' } }
        'node_modules'    { return @{ lvl = 'rebuild'; txt = '專案相依，刪後需 npm/pnpm install' } }
        'BuildOutput'     { return @{ lvl = 'caution'; txt = '建置輸出，重建需重跑 build' } }
        default           { return @{ lvl = 'rebuild'; txt = '可回收項目' } }
    }
}

function Get-ScanInventory {
    $devFound = Find-CacheDirsAccel -Roots $script:ScanRoots -Throttle $AccelThrottle
    $known = Get-WellKnownTargets
    $all  = [System.Collections.Generic.List[object]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($x in $devFound) { if ($seen.Add($x.Path)) { $all.Add($x) } }
    foreach ($x in $known)    { if ($seen.Add($x.Path)) { $all.Add($x) } }
    $sized = @()
    if ($all.Count -gt 0) { $sized = Measure-TargetsAccel -Targets ($all.ToArray()) -Throttle $AccelThrottle }
    return @($sized | Where-Object { $_.Bytes -gt 0 })
}

function New-ControlHtml {
    param([string]$Json, [string]$Csrf, [int]$Count, [double]$Total, [double]$SafeB, [double]$RebuildB, [double]$SysB, [string]$DiskJson)
    $tpl = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Control Center</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;800&display=swap" rel="stylesheet">
<style>
:root{--blue:@@BLUE@@;--grey:@@GREY@@;--teal:@@TEAL@@;--red:@@RED@@;--green:@@GREEN@@;--bg:#14171c;--card:#1d2128;--line:#2b313b;--ink:#e8e6e1;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;padding:24px 28px 110px;line-height:1.45}
h1{font-family:'Syne',sans-serif;font-weight:800;font-size:26px}
h1 .s{color:var(--teal)}
.sub{color:var(--grey);font-family:'DM Mono',monospace;font-size:12px;margin-top:5px;word-break:break-all}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:20px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.card .k{font-family:'DM Mono',monospace;font-size:11px;color:var(--grey);text-transform:uppercase;letter-spacing:1px}
.card .v{font-family:'Syne',sans-serif;font-weight:800;font-size:24px;margin-top:6px}
.v.total{color:var(--teal)}.v.safe{color:var(--green)}.v.rebuild{color:var(--blue)}.v.sys{color:var(--grey)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0}
.row{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center}
.btn{background:var(--blue);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-family:'DM Mono',monospace;font-size:12px;cursor:pointer}
.btn.ok{background:var(--green)}.btn.ghost{background:#11141a;color:var(--ink);border:1px solid var(--line)}.btn.warn{background:var(--red)}
.chip{font-family:'DM Mono',monospace;font-size:11px;padding:4px 10px;border:1px solid var(--line);border-radius:20px;color:var(--grey);cursor:pointer;background:#11141a}
.chip.on{background:var(--blue);color:#fff;border-color:var(--blue)}
input[type=text],input[type=number],select{background:#11141a;border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:6px 9px;font-family:'DM Mono',monospace;font-size:13px}
.lab{font-family:'DM Mono',monospace;font-size:12px;color:var(--grey)}
.tbox{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:auto;max-height:58vh}
table{width:100%;border-collapse:collapse;table-layout:fixed}
th{position:sticky;top:0;background:#222732;text-align:left;font-family:'DM Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--grey);padding:9px 12px;border-bottom:1px solid var(--line)}
td{padding:7px 12px;border-bottom:1px solid var(--line);font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
td.nm{font-family:'DM Mono',monospace;font-size:12px;color:#d6d4ce}
td.r{font-family:'DM Mono',monospace;text-align:right;color:var(--teal)}
td.c{text-align:center}
tr.sel td{background:#23304a}
tr:hover td{background:#262b35}
.badge{font-family:'DM Mono',monospace;font-size:10px;padding:2px 7px;border-radius:3px}
.b-safe{background:#1f3a2b;color:var(--green)}.b-rebuild{background:#1c3535;color:var(--teal)}.b-caution{background:#3a2a28;color:var(--red)}
.actbar{position:fixed;left:0;right:0;bottom:0;background:#10131a;border-top:1px solid var(--line);padding:12px 28px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.stat{font-family:'DM Mono',monospace;font-size:12px;color:var(--grey)}.stat b{color:var(--teal);font-weight:500}
.toast{position:fixed;right:24px;bottom:84px;background:var(--card);border:1px solid var(--teal);border-radius:8px;padding:10px 16px;font-family:'DM Mono',monospace;font-size:12px;opacity:0;transition:opacity .3s}
.toast.show{opacity:1}
.legend{font-family:'DM Mono',monospace;font-size:11px;color:var(--grey);margin-top:6px}
.dwrap{margin:8px 0}
.dhead{display:flex;justify-content:space-between;font-family:'DM Mono',monospace;font-size:12px;color:var(--ink);margin-bottom:4px}
.dhead .pf{color:var(--green)}
.dtrack{height:14px;background:#11141a;border:1px solid var(--line);border-radius:7px;overflow:hidden;position:relative}
.dused{height:100%;background:var(--grey);position:absolute;left:0;top:0}
.dproj{height:100%;background:var(--green);opacity:.55;position:absolute;top:0}
.muted{color:var(--grey);font-size:12px;font-family:'DM Mono',monospace;padding:10px 12px}
</style></head><body>
<h1><span class="s">理</span> VIA Control Center · 一鍵安全清理</h1>
<div class="sub">掃描已完成。下方依「安全等級」分色：綠=刪了自動重生｜青=可重建需重新下載｜紅=謹慎。預設動作為 Quarantine（移入隔離區可還原）。</div>
<div class="grid">
<div class="card"><div class="k">可回收總量</div><div class="v total">@@TOTAL@@</div></div>
<div class="card"><div class="k">安全·自動重生</div><div class="v safe">@@SAFE@@</div></div>
<div class="card"><div class="k">可重建·需重載</div><div class="v rebuild">@@REBUILD@@</div></div>
<div class="card"><div class="k">系統垃圾</div><div class="v sys">@@SYS@@</div></div>
</div>
<div class="panel">
  <div class="lab" style="margin-bottom:8px">硬碟使用率 Disk Usage（清理選取後預估可用，即時更新）</div>
  <div id="disks"></div>
</div>
<div class="panel">
  <div class="row">
    <span class="lab">最佳化（不刪檔，立即執行）</span>
    <button class="btn ghost" data-op="dns">清 DNS 快取</button>
    <button class="btn ghost" data-op="recycle">清空資源回收筒</button>
    <button class="btn ghost" data-op="trim">SSD TRIM / 重組</button>
    <button class="btn ghost" data-op="dism">DISM 元件清理</button>
    <button class="btn ghost" data-op="smart">SMART 健康檢查</button>
  </div>
  <div id="optlog" class="legend" style="margin-top:8px;white-space:pre-wrap"></div>
</div>
<div class="panel">
  <div class="row">
    <button class="btn ok" id="selSafe">✓ 一鍵選取所有「安全」項目</button>
    <button class="btn ghost" id="selFiltered">選取目前篩選</button>
    <button class="btn ghost" id="selNone">清除選取</button>
    <span class="lab">最小大小(MB)</span><input type="number" id="minmb" value="0" min="0" style="width:88px">
    <span class="lab">搜尋</span><input type="text" id="q" placeholder="路徑關鍵字">
  </div>
  <div class="row" style="margin-top:10px"><span class="lab">分類</span><div id="cats" style="display:flex;flex-wrap:wrap;gap:8px"></div></div>
  <div class="legend">提示：先用「一鍵選取所有安全」清最沒風險的部分；可重建類(uv/pip/npm 快取)空間最大但下次首跑需重新下載。</div>
</div>
<div id="view"></div>
<div class="actbar">
  <span class="stat">已選 <b id="selCnt">0</b> 項 · <b id="selSize">0 B</b></span>
  <span class="lab">處理階梯</span>
  <select id="tier">
    <option value="Quarantine">Quarantine 隔離可還原（建議）</option>
    <option value="Recycle">Recycle 資源回收筒</option>
    <option value="Permanent">Permanent 永久刪除</option>
  </select>
  <button class="btn warn" id="apply">執行清理 Apply</button>
  <button class="btn ghost" id="stop">停止伺服器</button>
</div>
<div class="toast" id="toast"></div>
<script>
const DATA = @@DATA@@;
const CSRF = '@@CSRF@@';
let rows = DATA.slice();
let selected = new Set();
const state = { cats:new Set(), minMB:0, q:'' };
const DISK = @@DISK@@;
const CAP = 1500;
function fmt(b){ if(b>=1073741824)return (b/1073741824).toFixed(2)+' GB'; if(b>=1048576)return (b/1048576).toFixed(2)+' MB'; if(b>=1024)return (b/1024).toFixed(2)+' KB'; return b+' B'; }
function esc(s){ return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function pass(f){
  if(state.cats.size && !state.cats.has(f.cat)) return false;
  if(state.minMB>0 && f.bytes < state.minMB*1048576) return false;
  if(state.q && !f.path.toLowerCase().includes(state.q.toLowerCase())) return false;
  return true;
}
function filtered(){ return rows.filter(pass); }
function buildCats(){
  const m=new Map();
  DATA.forEach(f=>{ m.set(f.cat,(m.get(f.cat)||0)+f.bytes); });
  const w=document.getElementById('cats'); w.innerHTML='';
  [...m.entries()].sort((a,b)=>b[1]-a[1]).forEach(([c,b])=>{
    const el=document.createElement('span'); el.className='chip'; el.textContent=c+' ('+fmt(b)+')';
    el.onclick=()=>{ if(state.cats.has(c)){state.cats.delete(c);el.classList.remove('on');}else{state.cats.add(c);el.classList.add('on');} render(); };
    w.appendChild(el);
  });
}
function badge(lvl){ const m={safe:['b-safe','安全'],rebuild:['b-rebuild','可重建'],caution:['b-caution','謹慎']}; const x=m[lvl]||m.rebuild; return '<span class="badge '+x[0]+'">'+x[1]+'</span>'; }
function render(){
  const f=filtered();
  const v=document.getElementById('view');
  const show=f.slice(0,CAP);
  let h='<div class="tbox"><table><colgroup><col style="width:38px"><col style="width:150px"><col style="width:84px"><col><col style="width:104px"></colgroup>'
    +'<thead><tr><th></th><th>分類</th><th>安全</th><th>路徑 · 說明</th><th>大小</th></tr></thead><tbody>';
  show.forEach(x=>{
    const sel=selected.has(x.path)?' class="sel"':'';
    h+='<tr'+sel+' data-p="'+esc(x.path)+'"><td class="c"><input type="checkbox" data-p="'+esc(x.path)+'"'+(selected.has(x.path)?' checked':'')+'></td>'
      +'<td>'+esc(x.cat)+'</td><td>'+badge(x.lvl)+'</td><td class="nm" title="'+esc(x.path)+' — '+esc(x.txt)+'">'+esc(x.path)+'</td><td class="r">'+fmt(x.bytes)+'</td></tr>';
  });
  h+='</tbody></table></div>';
  if(f.length>CAP){ h+='<div class="muted">顯示前 '+CAP+' 筆（共 '+f.length+'）· 批次選取仍作用於全部</div>'; }
  v.innerHTML=h;
  v.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>toggle(cb.dataset.p));
  bar();
}
function toggle(p){ if(selected.has(p))selected.delete(p);else selected.add(p);
  document.querySelectorAll('tr[data-p="'+CSS.escape(p)+'"]').forEach(r=>r.classList.toggle('sel',selected.has(p))); bar(); }
function bar(){
  const map=new Map(DATA.map(f=>[f.path,f.bytes]));
  let sz=0; selected.forEach(p=>sz+=map.get(p)||0);
  document.getElementById('selCnt').textContent=selected.size;
  document.getElementById('selSize').textContent=fmt(sz);
  renderDisks();
}
function toast(m){ const t=document.getElementById('toast'); t.textContent=m; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2800); }
document.getElementById('selSafe').onclick=()=>{ DATA.forEach(f=>{ if(f.lvl==='safe')selected.add(f.path); }); render(); };
document.getElementById('selFiltered').onclick=()=>{ filtered().forEach(f=>selected.add(f.path)); render(); };
document.getElementById('selNone').onclick=()=>{ selected.clear(); render(); };
document.getElementById('minmb').oninput=e=>{ state.minMB=+e.target.value||0; render(); };
document.getElementById('q').oninput=e=>{ state.q=e.target.value; render(); };
document.getElementById('stop').onclick=async()=>{ try{await fetch('/api/stop');}catch(e){} toast('伺服器已停止，可關閉此頁'); };
document.getElementById('apply').onclick=async()=>{
  const paths=[...selected]; if(!paths.length){ toast('尚未選取'); return; }
  const mode=document.getElementById('tier').value;
  if(mode==='Permanent' && !confirm('永久刪除 '+paths.length+' 個項目，無法還原。確定？')) return;
  try{
    const res=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-VIA-CSRF':CSRF},body:JSON.stringify({mode,paths})});
    const j=await res.json();
    const ok=new Set(j.results.filter(r=>r.ok).map(r=>r.p));
    const freed=rows.filter(f=>ok.has(f.path)).reduce((a,b)=>a+b.bytes,0);
    rows=rows.filter(f=>!ok.has(f.path)); ok.forEach(p=>selected.delete(p));
    render(); toast(mode+' 完成 '+ok.size+' 項 · 釋出 '+fmt(freed));
  }catch(e){ toast('動作失敗 '+e); }
};
function selBytes(){ const map=new Map(DATA.map(f=>[f.path,f.bytes])); let s=0; selected.forEach(p=>s+=map.get(p)||0); return s; }
function renderDisks(){
  const sel=selBytes(); const w=document.getElementById('disks'); if(!w)return; w.innerHTML='';
  DISK.forEach(d=>{
    const used=d.total-d.free; const usedPct=d.total?used/d.total*100:0;
    const isC=d.name.toUpperCase().startsWith('C');
    const projFree=isC?d.free+sel:d.free;
    const projW=(isC&&sel>0&&d.total)?(sel/d.total*100):0;
    const projOverlay=projW>0?'<div class="dproj" style="left:'+(usedPct-projW)+'%;width:'+projW+'%"></div>':'';
    let h='<div class="dwrap"><div class="dhead"><span>'+d.name+'  已用 '+fmt(used)+' / '+fmt(d.total)+'</span><span>可用 '+fmt(d.free);
    if(isC&&sel>0){ h+=' <span class="pf">→ 清理後 ≈ '+fmt(projFree)+'</span>'; }
    h+='</span></div><div class="dtrack"><div class="dused" style="width:'+usedPct+'%"></div>'+projOverlay+'</div></div>';
    w.innerHTML+=h;
  });
}
function optlog(m){ const el=document.getElementById('optlog'); el.textContent=(new Date().toLocaleTimeString()+'  '+m+'\n'+el.textContent).slice(0,1400); }
function wireOpt(){
  document.querySelectorAll('button[data-op]').forEach(b=>b.onclick=async()=>{
    const op=b.dataset.op, lab=b.textContent; b.disabled=true; optlog(lab+' …執行中');
    try{ const r=await fetch('/api/optimize',{method:'POST',headers:{'Content-Type':'application/json','X-VIA-CSRF':CSRF},body:JSON.stringify({op})}); const j=await r.json(); optlog(lab+': '+j.status); }
    catch(e){ optlog(lab+': 失敗 '+e); } finally{ b.disabled=false; }
  });
}
buildCats(); renderDisks(); wireOpt(); render();
</script>
</body></html>
'@
    $h = $tpl.Replace('@@BLUE@@',$script:CssBlue).Replace('@@GREY@@',$script:CssGrey).Replace('@@TEAL@@',$script:CssTeal).Replace('@@RED@@',$script:CssRed).Replace('@@GREEN@@',$script:CssGreen)
    $h = $h.Replace('@@TOTAL@@',(Format-Size -Bytes $Total)).Replace('@@SAFE@@',(Format-Size -Bytes $SafeB)).Replace('@@REBUILD@@',(Format-Size -Bytes $RebuildB)).Replace('@@SYS@@',(Format-Size -Bytes $SysB))
    $h = $h.Replace('@@CSRF@@',$Csrf).Replace('@@DATA@@',$Json).Replace('@@DISK@@',$DiskJson)
    return $h
}

function Start-ControlCenter {
    Write-Host ''
    Write-Host '理  VIA Control Center · 掃描中…' -ForegroundColor Cyan
    Write-Host ('   掃描根 ' + ($script:ScanRoots -join ', ') + '   FastScan=' + [string]([bool]$FastScan)) -ForegroundColor DarkGray
    $sized = Get-ScanInventory
    $sized = @($sized)
    if ($sized.Count -eq 0) {
        Write-Host '   無可回收項目' -ForegroundColor Yellow
        return
    }
    $inv = [System.Collections.Generic.Dictionary[string,object]]::new()
    $jsonItems = [System.Collections.Generic.List[object]]::new()
    $safeB = 0.0
    $rebuildB = 0.0
    $sysB = 0.0
    $totalB = 0.0
    foreach ($s in $sized) {
        $si = Get-SafetyInfo -Category ([string]$s.Category)
        $inv[$s.Path] = $s
        $jsonItems.Add([pscustomobject]@{ path = $s.Path; cat = $s.Category; box = $s.Box; bytes = [int64]$s.Bytes; lvl = $si.lvl; txt = $si.txt })
        $totalB = $totalB + $s.Bytes
        if ($s.Box -eq 'SYS') { $sysB = $sysB + $s.Bytes }
        if ($si.lvl -eq 'safe') { $safeB = $safeB + $s.Bytes } else { $rebuildB = $rebuildB + $s.Bytes }
    }
    $script:CtrlInv = $inv
    $json = '[]'
    if ($jsonItems.Count -eq 1) {
        $json = '[' + ($jsonItems | ConvertTo-Json -Depth 4 -Compress) + ']'
    } elseif ($jsonItems.Count -gt 1) {
        $json = ($jsonItems | ConvertTo-Json -Depth 4 -Compress)
    }
    $script:CtrlCsrf = [guid]::NewGuid().ToString('N')
    $disks = Get-DiskInfo
    $diskJson = '[]'
    if ($disks.Count -eq 1) {
        $diskJson = '[' + ($disks | ConvertTo-Json -Depth 3 -Compress) + ']'
    } elseif ($disks.Count -gt 1) {
        $diskJson = ($disks | ConvertTo-Json -Depth 3 -Compress)
    }
    $html = New-ControlHtml -Json $json -Csrf $script:CtrlCsrf -Count $sized.Count -Total $totalB -SafeB $safeB -RebuildB $rebuildB -SysB $sysB -DiskJson $diskJson

    $allowHosts = @(('127.0.0.1:' + [string]$DownloadsPort), ('localhost:' + [string]$DownloadsPort))
    $prefix     = ('http://127.0.0.1:' + [string]$DownloadsPort + '/')
    $listener   = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add($prefix)
    try {
        $listener.Start()
    } catch {
        Write-Host ('   無法在 port ' + [string]$DownloadsPort + ' 啟動，改用 -DownloadsPort 指定其他埠') -ForegroundColor Yellow
        return
    }
    Write-Host ('   可回收 ' + (Format-Size -Bytes $totalB) + '（安全 ' + (Format-Size -Bytes $safeB) + '）· ' + [string]$sized.Count + ' 項') -ForegroundColor Green
    Write-Host ('   控制台 ' + $prefix + '  瀏覽器已開啟') -ForegroundColor Cyan
    try { Start-Process $prefix } catch { }
    try {
        while ($listener.IsListening) {
            $ctx = $null
            try { $ctx = $listener.GetContext() } catch { break }
            $req = $ctx.Request
            if (-not [System.Net.IPAddress]::IsLoopback($req.RemoteEndPoint.Address)) { Send-Http -Ctx $ctx -Code 403 -Body 'forbidden'; continue }
            $hn = ''
            if ($null -ne $req.UserHostName) { $hn = $req.UserHostName.ToLowerInvariant() }
            if (-not ($allowHosts -contains $hn)) { Send-Http -Ctx $ctx -Code 403 -Body 'bad host'; continue }
            $route = $req.Url.AbsolutePath
            if ($req.HttpMethod -eq 'GET' -and $route -eq '/') {
                Send-Http -Ctx $ctx -Code 200 -Body $html -Ctype 'text/html; charset=utf-8'
            } elseif ($req.HttpMethod -eq 'GET' -and $route -eq '/api/stop') {
                Send-Http -Ctx $ctx -Code 200 -Body 'stopping'
                break
            } elseif ($req.HttpMethod -eq 'POST' -and $route -eq '/api/action') {
                if ($req.Headers['X-VIA-CSRF'] -ne $script:CtrlCsrf) { Send-Http -Ctx $ctx -Code 403 -Body 'csrf'; continue }
                if ($req.ContentLength64 -gt 2097152) { Send-Http -Ctx $ctx -Code 413 -Body 'too large'; continue }
                $body = ''
                $sr   = [System.IO.StreamReader]::new($req.InputStream, $req.ContentEncoding)
                try { $body = $sr.ReadToEnd() } finally { $sr.Dispose() }
                $payload = $null
                try { $payload = $body | ConvertFrom-Json } catch { Send-Http -Ctx $ctx -Code 400 -Body 'bad json'; continue }
                $actMode = [string]$payload.mode
                $arr = [System.Collections.Generic.List[object]]::new()
                foreach ($pp in @($payload.paths)) {
                    $key = [string]$pp
                    $okFlag = $false
                    $rtext  = 'NOT-IN-SCAN'
                    if ($script:CtrlInv.ContainsKey($key)) {
                        $rtext = Invoke-SafeRemove -Target $script:CtrlInv[$key] -ActMode $actMode
                        if ($rtext -eq $actMode) { $okFlag = $true }
                    }
                    $arr.Add([pscustomobject]@{ p = $key; r = $rtext; ok = $okFlag })
                }
                $resp = (@{ ok = $true; results = $arr } | ConvertTo-Json -Depth 4 -Compress)
                Send-Http -Ctx $ctx -Code 200 -Body $resp -Ctype 'application/json; charset=utf-8'
            } elseif ($req.HttpMethod -eq 'POST' -and $route -eq '/api/optimize') {
                if ($req.Headers['X-VIA-CSRF'] -ne $script:CtrlCsrf) { Send-Http -Ctx $ctx -Code 403 -Body 'csrf'; continue }
                if ($req.ContentLength64 -gt 2097152) { Send-Http -Ctx $ctx -Code 413 -Body 'too large'; continue }
                $obody = ''
                $osr   = [System.IO.StreamReader]::new($req.InputStream, $req.ContentEncoding)
                try { $obody = $osr.ReadToEnd() } finally { $osr.Dispose() }
                $op = ''
                try { $op = [string]($obody | ConvertFrom-Json).op } catch { $op = '' }
                $status = Invoke-SingleOpt -Op $op
                $oresp  = (@{ ok = $true; status = $status } | ConvertTo-Json -Depth 3 -Compress)
                Send-Http -Ctx $ctx -Code 200 -Body $oresp -Ctype 'application/json; charset=utf-8'
            } else {
                Send-Http -Ctx $ctx -Code 404 -Body 'not found'
            }
        }
    } finally {
        try { $listener.Stop() } catch { }
        try { $listener.Close() } catch { }
    }
    Write-Host '   Control Center 已結束' -ForegroundColor DarkGray
}

# ---------- 6B. 環境盤點 Env Audit ----------
function Find-VenvRootsAccel {
    param([string[]]$Roots, [int]$Throttle)
    $units = [System.Collections.Generic.List[string]]::new()
    $eo = [System.IO.EnumerationOptions]::new()
    $eo.IgnoreInaccessible = $true
    $eo.AttributesToSkip   = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
    foreach ($r in $Roots) {
        if (-not (Test-Path -LiteralPath $r)) { continue }
        if (Test-Protected -Path $r) { continue }
        try {
            foreach ($c in [System.IO.Directory]::EnumerateDirectories($r, '*', $eo)) {
                if (Test-Protected -Path $c) { continue }
                $units.Add($c)
            }
        } catch { }
    }
    $worker = {
        param($Root, $Sync, $Bag, $Protected, $StoreSegs)
        $opt = [System.IO.EnumerationOptions]::new()
        $opt.IgnoreInaccessible = $true
        $opt.AttributesToSkip   = ([System.IO.FileAttributes]::ReparsePoint -bor [System.IO.FileAttributes]::System)
        $prot = [System.Collections.Generic.List[string]]::new()
        foreach ($p in $Protected) { $prot.Add($p.TrimEnd('\').ToLowerInvariant()) }
        function Test-Prot {
            param([string]$Dir)
            $dl = $Dir.TrimEnd('\').ToLowerInvariant()
            foreach ($p in $prot) {
                if ($dl -eq $p -or $dl.StartsWith($p + '\')) { return $true }
            }
            return $false
        }
        function Get-Venv {
            param([string]$Dir)
            try {
                $cfg = Join-Path $Dir 'pyvenv.cfg'
                if ([System.IO.File]::Exists($cfg)) {
                    $ver = ''
                    foreach ($line in [System.IO.File]::ReadAllLines($cfg)) {
                        if ($line -match '^\s*version\s*=\s*(.+)$') { $ver = $Matches[1].Trim() }
                    }
                    return @{ ok = $true; kind = 'venv'; ver = $ver }
                }
                if ([System.IO.Directory]::Exists((Join-Path $Dir 'conda-meta'))) {
                    return @{ ok = $true; kind = 'conda'; ver = '' }
                }
                if ([System.IO.File]::Exists((Join-Path $Dir 'Scripts\python.exe'))) {
                    return @{ ok = $true; kind = 'venv'; ver = '' }
                }
            } catch { }
            return @{ ok = $false }
        }
        $boundary = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($x in @('site-packages','dist-packages','node_modules','__pycache__','.git')) { [void]$boundary.Add($x) }
        $stack = [System.Collections.Generic.Stack[string]]::new()
        $rv = Get-Venv -Dir $Root
        if ($rv.ok) {
            $Bag.Add([pscustomobject]@{ Path = $Root; EnvKind = $rv.kind; PyVer = $rv.ver })
            [System.Threading.Monitor]::Enter($Sync.SyncRoot)
            try { $Sync.n2 = $Sync.n2 + 1 } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
        } else {
            $stack.Push($Root)
        }
        $sinceFlush = 0
        while ($stack.Count -gt 0) {
            $dir = $stack.Pop()
            $subs = $null
            try { $subs = [System.IO.Directory]::EnumerateDirectories($dir, '*', $opt) } catch { continue }
            foreach ($child in $subs) {
                $sinceFlush = $sinceFlush + 1
                if (Test-Prot -Dir $child) { continue }
                $cname = [System.IO.Path]::GetFileName($child).ToLowerInvariant()
                if ($boundary.Contains($cname)) { continue }
                $v = Get-Venv -Dir $child
                if ($v.ok) {
                    $Bag.Add([pscustomobject]@{ Path = $child; EnvKind = $v.kind; PyVer = $v.ver })
                    [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                    try { $Sync.n2 = $Sync.n2 + 1 } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                } else {
                    $stack.Push($child)
                }
                if ($sinceFlush -ge 1024) {
                    [System.Threading.Monitor]::Enter($Sync.SyncRoot)
                    try { $Sync.n1 = $Sync.n1 + $sinceFlush; $Sync.cur = $dir } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
                    $sinceFlush = 0
                }
            }
        }
        [System.Threading.Monitor]::Enter($Sync.SyncRoot)
        try { $Sync.n1 = $Sync.n1 + $sinceFlush; $Sync.cur = $Root } finally { [System.Threading.Monitor]::Exit($Sync.SyncRoot) }
    }
    $cfg = @{
        mode       = 'venv'
        Protected  = @($script:ProtectedRoots)
        Unambig    = @($script:UnambiguousCache)
        BuildNames = @($script:BuildDirNames)
        Markers    = @($script:ProjectMarkers)
        StoreSegs  = @($script:StoreSegs)
        IncludeNM  = $false
        IncludeBuild = $false
        FastScan   = $false
    }
    $fmt = {
        param($s)
        $c = [string]$s.cur
        if ($c.Length -gt 48) { $c = '...' + $c.Substring($c.Length - 45) }
        ('掃描目錄 {0} · 找到環境 {1} · {2}' -f $s.dirs, $s.found, $c)
    }
    return (Invoke-Crawl -Seed ($units.ToArray()) -Threads $Throttle -Cfg $cfg -Activity 'EnvAudit 加速盤點 venv/conda' -ProgressId 3 -StatusFormatter $fmt)
}

function New-EnvAuditHtml {
    param([object[]]$Envs, [double]$Total)
    $rowsSb = [System.Text.StringBuilder]::new()
    $sorted = $Envs | Sort-Object @{ e = 'Bytes'; desc = $true }
    foreach ($e in $sorted) {
        $mt = ''
        try { $mt = ([System.IO.DirectoryInfo]::new($e.Path)).LastWriteTime.ToString('yyyy-MM-dd') } catch { }
        $null = $rowsSb.AppendLine('<tr><td class="p">' + [System.Net.WebUtility]::HtmlEncode([string]$e.Path) + '</td><td><span class="bx">' + [System.Net.WebUtility]::HtmlEncode([string]$e.EnvKind) + '</span></td><td>' + [System.Net.WebUtility]::HtmlEncode([string]$e.PyVer) + '</td><td>' + $mt + '</td><td class="r">' + (Format-Size -Bytes $e.Bytes) + '</td></tr>')
    }
    $tpl = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Env Audit</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Syne:wght@600;800&display=swap" rel="stylesheet">
<style>
:root{--blue:@@BLUE@@;--grey:@@GREY@@;--teal:@@TEAL@@;--red:@@RED@@;--bg:#16181d;--card:#1f232b;--line:#2c313b;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:#e8e6e1;font-family:'DM Sans',sans-serif;padding:32px;line-height:1.5}
h1{font-family:'Syne',sans-serif;font-weight:800;font-size:28px}
h1 .seal{color:var(--blue)}
.sub{color:var(--grey);font-family:'DM Mono',monospace;font-size:13px;margin-top:6px}
.big{font-family:'Syne',sans-serif;font-weight:800;font-size:26px;color:var(--teal);margin:18px 0}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:14px}
th{text-align:left;font-family:'DM Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--grey);padding:11px 14px;border-bottom:1px solid var(--line)}
td{padding:9px 14px;border-bottom:1px solid var(--line);font-size:13px}
td.p{font-family:'DM Mono',monospace;font-size:12px;color:#cfcdc7;word-break:break-all;max-width:560px}
td.r{font-family:'DM Mono',monospace;text-align:right;color:var(--teal);white-space:nowrap}
.bx{font-family:'DM Mono',monospace;font-size:11px;padding:2px 7px;border-radius:3px;background:#272c35;color:var(--blue)}
tr:hover td{background:#222630}
.foot{color:var(--grey);font-family:'DM Mono',monospace;font-size:12px;margin-top:24px}
</style></head><body>
<h1><span class="seal">理</span> VIA Env Audit · 環境盤點</h1>
<div class="sub">偵測散落各處的 venv / conda 環境（pyvenv.cfg / conda-meta / Scripts\python.exe）。本頁僅盤點，不刪除任何環境。</div>
<div class="big">@@COUNT@@ 個環境 · 合計 @@TOTAL@@</div>
<table><thead><tr><th>Env Path</th><th>Kind</th><th>Python</th><th>Modified</th><th>Size</th></tr></thead>
<tbody>@@ROWS@@</tbody></table>
<div class="foot">受保護根（C:\Users\tonyk\envs / VeritasIntelligenceAnalytics / OneDrive）不在此清單；刪除環境請自行確認後手動移除。</div>
</body></html>
'@
    $h = $tpl.Replace('@@BLUE@@',$script:CssBlue).Replace('@@GREY@@',$script:CssGrey).Replace('@@TEAL@@',$script:CssTeal).Replace('@@RED@@',$script:CssRed)
    $h = $h.Replace('@@COUNT@@',[string]$Envs.Count).Replace('@@TOTAL@@',(Format-Size -Bytes $Total))
    $h = $h.Replace('@@ROWS@@',$rowsSb.ToString())
    $path = Join-Path $script:OutDir ('VIA_EnvAudit_' + $script:Ts + '.html')
    [System.IO.File]::WriteAllText($path, $h, [System.Text.UTF8Encoding]::new($false))
    return $path
}

function Invoke-EnvAudit {
    Write-Host ''
    Write-Host '理  VIA Env Audit · 環境盤點' -ForegroundColor Cyan
    Write-Host ('   掃描根 ' + ($script:ScanRoots -join ', ')) -ForegroundColor DarkGray
    $found = Find-VenvRootsAccel -Roots $script:ScanRoots -Throttle $AccelThrottle
    $found = @($found)
    if ($found.Count -eq 0) {
        Write-Host '   未偵測到環境' -ForegroundColor Yellow
        return
    }
    $targets = [System.Collections.Generic.List[object]]::new()
    foreach ($e in $found) {
        $targets.Add([pscustomobject]@{ Path = $e.Path; Category = $e.EnvKind; Tier = 'Env'; Box = 'ENV'; Kind = 'Dir'; EnvKind = $e.EnvKind; PyVer = $e.PyVer })
    }
    $sized = Measure-TargetsAccel -Targets ($targets.ToArray()) -Throttle $AccelThrottle
    $map = [System.Collections.Generic.Dictionary[string,object]]::new()
    foreach ($t in $targets) { $map[$t.Path] = $t }
    $envs = [System.Collections.Generic.List[object]]::new()
    foreach ($s in $sized) {
        $src = $null
        if ($map.ContainsKey($s.Path)) { $src = $map[$s.Path] }
        $kind = ''
        $ver  = ''
        if ($null -ne $src) { $kind = [string]$src.EnvKind; $ver = [string]$src.PyVer }
        $envs.Add([pscustomobject]@{ Path = $s.Path; EnvKind = $kind; PyVer = $ver; Bytes = $s.Bytes })
    }
    $total = ($envs | Measure-Object -Property Bytes -Sum).Sum
    if ($null -eq $total) { $total = 0 }
    $report = New-EnvAuditHtml -Envs ($envs.ToArray()) -Total $total
    Write-Host ''
    Write-Host ('   環境數 ' + [string]$envs.Count + '   合計 ' + (Format-Size -Bytes $total)) -ForegroundColor Green
    $top5 = $envs | Sort-Object @{ e = 'Bytes'; desc = $true } | Select-Object -First 5
    foreach ($e in $top5) {
        Write-Host ('   ' + (Format-Size -Bytes $e.Bytes).PadLeft(11) + '  ' + $e.Path) -ForegroundColor DarkGray
    }
    Write-Host ('   報告 ' + $report) -ForegroundColor Cyan
    Write-Host ''
    if (-not $NoOpenReport) {
        try { Start-Process $report } catch { }
    }
}

# ---------- 7. 批次主流程 ----------
function Invoke-TriBoxBatch {
Write-Host ''
Write-Host '理  VIA TriBox Optimizer  三合一系統優化器' -ForegroundColor Cyan
Write-Host ('   Mode=' + $Mode + '  Admin=' + [string]$script:IsAdmin + '  Throttle=' + [string]$ThrottleLimit) -ForegroundColor DarkGray
Write-Host ''

Write-Host '   加速器 x10：runspace pool · .NET 列舉 · 剪枝 · 動態進度' -ForegroundColor DarkGray
$devFound = Find-CacheDirsAccel -Roots $script:ScanRoots -Throttle $AccelThrottle

Write-Progress -Id 1 -Activity 'VIA TriBox' -Status 'well-known caches and junk' -PercentComplete 30
$known = Get-WellKnownTargets

$all = [System.Collections.Generic.List[object]]::new()
$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($x in $devFound) { if ($seen.Add($x.Path)) { $all.Add($x) } }
foreach ($x in $known)    { if ($seen.Add($x.Path)) { $all.Add($x) } }

$sized = @()
if ($all.Count -gt 0) { $sized = Measure-TargetsAccel -Targets ($all.ToArray()) -Throttle $AccelThrottle }
$sized = @($sized | Where-Object { $_.Bytes -gt 0 })

Write-Progress -Id 1 -Activity 'VIA TriBox' -Status ('執行動作 ' + $Mode) -PercentComplete 70
foreach ($c in $sized) {
    if ($Mode -eq 'Scan') {
        $c | Add-Member -NotePropertyName Action -NotePropertyValue 'SCAN only' -Force
    } else {
        $act = Invoke-SafeRemove -Target $c -ActMode $Mode
        $c | Add-Member -NotePropertyName Action -NotePropertyValue $act -Force
    }
}

# 額外動作
if ($EmptyRecycleBin) {
    try { Clear-RecycleBin -Force -ErrorAction Stop; Write-Host '   資源回收筒已清空' -ForegroundColor DarkGray } catch { }
}

$perf = @()
if ($RunPerf)    { Write-Progress -Id 1 -Activity 'VIA TriBox' -Status 'BOX3 效能優化' -PercentComplete 82; $perf += (Invoke-Perf) }
if ($DeepClean)  { Write-Progress -Id 1 -Activity 'VIA TriBox' -Status 'DISM deep clean' -PercentComplete 88; $perf += (Invoke-DeepClean) }
if ($DockerPrune){ Write-Progress -Id 1 -Activity 'VIA TriBox' -Status 'docker prune' -PercentComplete 92; $perf += (Invoke-DockerPrune) }

Write-Progress -Id 1 -Activity 'VIA TriBox' -Status '產生 HTML 報告' -PercentComplete 96
$totalBytes = ($sized | Measure-Object -Property Bytes -Sum).Sum
if ($null -eq $totalBytes) { $totalBytes = 0 }
$devBytes = ($sized | Where-Object { $_.Box -eq 'DEV' } | Measure-Object -Property Bytes -Sum).Sum
if ($null -eq $devBytes) { $devBytes = 0 }
$sysBytes = ($sized | Where-Object { $_.Box -eq 'SYS' } | Measure-Object -Property Bytes -Sum).Sum
if ($null -eq $sysBytes) { $sysBytes = 0 }

New-HtmlReport -Items $sized -Perf $perf -TotalBytes $totalBytes -DevBytes $devBytes -SysBytes $sysBytes

Write-Progress -Id 1 -Activity 'VIA TriBox' -Completed

Write-Host ''
Write-Host ('   目標數 ' + [string]$sized.Count + '   可回收總量 ' + (Format-Size -Bytes $totalBytes)) -ForegroundColor Green
Write-Host ('   BOX1 DEV ' + (Format-Size -Bytes $devBytes) + '   BOX2 SYS ' + (Format-Size -Bytes $sysBytes)) -ForegroundColor DarkGray
Write-Host ('   報告 ' + $script:ReportPath) -ForegroundColor Cyan
if ($Mode -eq 'Quarantine') { Write-Host ('   隔離區 ' + $script:QuarantineRoot) -ForegroundColor DarkGray }
Write-Host ''

if (-not $NoOpenReport) {
    try { Start-Process $script:ReportPath } catch { }
}
}

# ---------- 8. 派發 ----------
$ErrorActionPreference = 'Stop'
Initialize-TriBox
if ($EnvAudit) {
    Invoke-EnvAudit
} elseif ($Control) {
    Start-ControlCenter
} elseif ($DownloadsManager) {
    Start-DownloadsManager
} else {
    Invoke-TriBoxBatch
}
