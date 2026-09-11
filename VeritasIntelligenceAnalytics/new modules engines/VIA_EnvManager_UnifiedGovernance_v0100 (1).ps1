#requires -Version 7.0
param(
    [string]$EnvRoot     = 'C:\Users\tonyk\envs',
    [string]$WorkRoot    = 'C:\VeritasIntelligenceAnalytics\CGE\EnvManager',
    [string[]]$ExtraEnvs = @(),
    [string]$UvExe       = '',
    [switch]$SkipMirrorProbe,
    [switch]$SkipUvCheck,
    [switch]$NoBrowser
)

# ============================================================
# VIA_EnvManager Unified Governance Engine v0100
#
# 防衝突原則（依 Tony 的規格）：
#   1. 掃 base + via_core + 所有 via_* 環境，判定健康度
#   2. 用 local-free 的方式快篩相依衝突：直接讀 dist-info/METADATA 的
#      Requires-Dist，與實際安裝版本比對，不連網、不呼叫 pip、不裝任何東西
#   3. 一發現衝突風險 -> 產生重建計畫並拔除風險因子
#   4. 被拔除的工具 / 中高風險 libs / 特殊工具鏈 -> 分流到獨立環境 via_isolated_*
#   5. plotly 這類常用套件允許多版本並存於不同環境，Python 版本各自對應
#   6. base 極致精簡化
#   7. 成功失敗都寫 logs\env_governance.log，供下一次基線比對
#   8. 新計畫一律基於前一次成功組合（LKGC）擬定
#   9. 沙盒驗證通過後仍需使用者明確同意才可執行
#
# 同意機制：本引擎本身是唯讀的。它只產出計畫 + 核准權杖 + apply 腳本。
# 不用 Read-Host（會卡住非阻塞架構），改用權杖：把 HTML 上的
# ==VEM-APPROVE== 權杖貼進 apply 腳本的 -Token，才會真的動環境。
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>"
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:Log   = [System.Collections.Generic.List[string]]::new()
$Script:Start = Get-Date

# ------------------------------------------------------------
# 0. 工具
# ------------------------------------------------------------

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Add-Utf8NoBomLine {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::AppendAllText($Path, ($Text + "`n"), [System.Text.UTF8Encoding]::new($false))
}

function Write-Stage {
    param([string]$Message, [int]$Percent = 0, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '][' + $Level + '] ' + $Message
    $Script:Log.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK')   { $color = 'Green' }
    if ($Level -eq 'WARN') { $color = 'Yellow' }
    if ($Level -eq 'FAIL') { $color = 'Red' }
    Write-Host $line -ForegroundColor $color
    Write-Progress -Activity 'VIA EnvManager Unified Governance v0100' -Status $Message -PercentComplete ([math]::Min(100, [math]::Max(0, $Percent)))
}

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

# PEP440-lite：只取數字段比較，前置後綴（rc/post/dev/+local）截斷。
# 這是啟發式，足以標出衝突風險，不足以當安裝器用 —— 證據等級 M。
function ConvertTo-VersionParts {
    param([string]$Version)
    $clean = ($Version -split '\+')[0]
    $clean = [regex]::Replace($clean, '(?i)(a|b|rc|\.post|\.dev)\d*.*$', '')
    $parts = @()
    foreach ($token in ($clean -split '\.')) {
        $number = 0
        if ([int]::TryParse(($token -replace '\D', ''), [ref]$number)) { $parts += $number } else { $parts += 0 }
    }
    while ($parts.Count -lt 4) { $parts += 0 }
    return , $parts
}

function Compare-PyVersion {
    param([string]$Left, [string]$Right)
    $a = ConvertTo-VersionParts -Version $Left
    $b = ConvertTo-VersionParts -Version $Right
    for ($i = 0; $i -lt 4; $i++) {
        if ($a[$i] -lt $b[$i]) { return -1 }
        if ($a[$i] -gt $b[$i]) { return 1 }
    }
    return 0
}

function Test-Specifier {
    param([string]$Installed, [string]$Specifier)
    $spec = $Specifier.Trim()
    if (-not $spec) { return $true }
    foreach ($clause in ($spec -split ',')) {
        $piece = $clause.Trim()
        if (-not $piece) { continue }
        $m = [regex]::Match($piece, '^(?<op>===|==|!=|>=|<=|~=|>|<)\s*(?<ver>[0-9][\w\.\*\+!-]*)$')
        if (-not $m.Success) { continue }
        $op  = $m.Groups['op'].Value
        $ver = $m.Groups['ver'].Value.TrimEnd('.', '*')
        $cmp = Compare-PyVersion -Left $Installed -Right $ver
        switch ($op) {
            '>='  { if ($cmp -lt 0) { return $false } }
            '>'   { if ($cmp -le 0) { return $false } }
            '<='  { if ($cmp -gt 0) { return $false } }
            '<'   { if ($cmp -ge 0) { return $false } }
            '=='  { if ($cmp -ne 0) { return $false } }
            '===' { if ($Installed -ne $ver) { return $false } }
            '!='  { if ($cmp -eq 0) { return $false } }
            '~='  {
                if ($cmp -lt 0) { return $false }
                $base = ConvertTo-VersionParts -Version $ver
                $have = ConvertTo-VersionParts -Version $Installed
                if ($have[0] -ne $base[0]) { return $false }
            }
            default { }
        }
    }
    return $true
}

# ------------------------------------------------------------
# 1. 治理政策（黃金律 / 禁用 / 風險分級 / 多版本白名單）
# ------------------------------------------------------------

$Policy = [ordered]@{
    GoldenPins = [ordered]@{
        'numpy' = '>=1.24,<2.0'
    }
    Banned = @('uvloop')
    BannedReason = @{ 'uvloop' = 'Windows 不支援，以 winloop 取代' }
    # 中高風險：不得與核心環境同住，必須分流到專屬隔離環境
    HighRisk = [ordered]@{
        'torch'        = 'vgf_ml'
        'torchvision'  = 'vgf_ml'
        'ray'          = 'via_ml'
        'surya-ocr'    = 'via_isolated_surya'
        'onnxruntime'  = 'vgf_core'
        'rembg'        = 'vgf_core'
        'tensorflow'   = 'via_isolated_tf'
        'pm4py'        = 'vmt_pm'
    }
    # Python 版本天花板（LL#16）
    PythonCeiling = [ordered]@{
        'numba'   = '3.12'
        'ortools' = '3.12'
    }
    # 允許多版本並存於不同環境
    MultiVersionAllowed = @('plotly', 'matplotlib', 'pyarrow')
    # base 只准留這些，其餘視為污染
    BaseAllowList = @('pip', 'setuptools', 'wheel', 'uv', 'virtualenv', 'packaging',
                      'rich', 'typing-extensions', 'certifi')
}

$Mirrors = @(
    [pscustomobject]@{ name = 'Tsinghua'; url = 'https://pypi.tuna.tsinghua.edu.cn/simple' }
    [pscustomobject]@{ name = 'Aliyun';   url = 'https://mirrors.aliyun.com/pypi/simple' }
    [pscustomobject]@{ name = 'PyPI';     url = 'https://pypi.org/simple' }
)

foreach ($sub in @('logs', 'out', 'plans', 'lkgc')) {
    $target = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
}
$GovernanceLog = Join-Path $WorkRoot 'logs\env_governance.log'
$HtmlPath      = Join-Path $WorkRoot ('out\VIA_EnvManager_Matrix_' + $Script:Stamp + '.html')
$SnapshotPath  = Join-Path $WorkRoot ('out\env_snapshot_' + $Script:Stamp + '.json')
$PlanPath      = Join-Path $WorkRoot ('plans\apply_env_plan_' + $Script:Stamp + '.ps1')
$LkgcDir       = Join-Path $WorkRoot 'lkgc'

Write-Stage -Message 'VIA EnvManager Unified Governance v0100 啟動（唯讀分析）' -Percent 1 -Level 'OK'

# ------------------------------------------------------------
# 2. 環境探索
# ------------------------------------------------------------

Write-Stage -Message ('掃描環境根目錄：' + $EnvRoot) -Percent 4

$envPaths = [System.Collections.Generic.List[string]]::new()
if (Test-Path -LiteralPath $EnvRoot) {
    foreach ($dir in (Get-ChildItem -LiteralPath $EnvRoot -Directory -ErrorAction SilentlyContinue)) {
        $envPaths.Add($dir.FullName)
    }
} else {
    Write-Stage -Message ('環境根目錄不存在：' + $EnvRoot) -Percent 5 -Level 'WARN'
}
foreach ($extra in $ExtraEnvs) { if ($extra) { $envPaths.Add($extra) } }

if ($envPaths.Count -eq 0) {
    Write-Stage -Message '找不到任何環境，結束' -Percent 100 -Level 'FAIL'
    return
}

function Get-SitePackagesPath {
    param([string]$EnvPath)
    $windows = Join-Path $EnvPath 'Lib\site-packages'
    if (Test-Path -LiteralPath $windows) { return $windows }
    $lib = Join-Path $EnvPath 'lib'
    if (Test-Path -LiteralPath $lib) {
        $candidate = @(Get-ChildItem -LiteralPath $lib -Directory -Filter 'python*' -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'site-packages' } |
            Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1)
        if ($candidate.Count -gt 0) { return $candidate[0] }
    }
    return ''
}

function Get-EnvTier {
    param([string]$Name)
    $lower = $Name.ToLowerInvariant()
    if ($lower -eq 'base' -or $lower -eq 'venv_core') { return 'BASE' }
    if ($lower -match 'isolated|_ml$|surya|_tf$') { return 'ISOLATED' }
    if ($lower -match '^via_core$|^vgf_core$') { return 'CORE' }
    if ($lower -match '^via_|^vgf_|^vmt_') { return 'SUBSYSTEM' }
    return 'OTHERS'
}

$envs = [System.Collections.Generic.List[object]]::new()
$allDists = [System.Collections.Generic.List[object]]::new()

$index = 0
foreach ($envPath in $envPaths) {
    $index++
    $name = Split-Path -Path $envPath -Leaf
    $percent = 4 + [int](26 * $index / [math]::Max(1, $envPaths.Count))
    Write-Stage -Message ('  讀取 ' + $name) -Percent $percent

    $cfgPath = Join-Path $envPath 'pyvenv.cfg'
    $pyVersion = ''
    $basePath  = ''
    $cfgOk = $false
    if (Test-Path -LiteralPath $cfgPath) {
        $cfgOk = $true
        foreach ($line in (Get-Content -LiteralPath $cfgPath -ErrorAction SilentlyContinue)) {
            if ($line -match '^\s*version\s*=\s*(.+)$')      { $pyVersion = $matches[1].Trim() }
            if ($line -match '^\s*version_info\s*=\s*(.+)$') { $pyVersion = $matches[1].Trim() }
            if ($line -match '^\s*home\s*=\s*(.+)$')         { $basePath  = $matches[1].Trim() }
        }
    }

    $pyExe = ''
    foreach ($candidate in @('Scripts\python.exe', 'bin/python', 'bin/python3')) {
        $probe = Join-Path $envPath $candidate
        if (Test-Path -LiteralPath $probe) { $pyExe = $probe; break }
    }

    $sitePackages = Get-SitePackagesPath -EnvPath $envPath
    $dists = [System.Collections.Generic.List[object]]::new()
    $brokenDists = 0
    if ($sitePackages) {
        foreach ($info in (Get-ChildItem -LiteralPath $sitePackages -Directory -Filter '*.dist-info' -ErrorAction SilentlyContinue)) {
            $metaPath = Join-Path $info.FullName 'METADATA'
            if (-not (Test-Path -LiteralPath $metaPath)) { $brokenDists++; continue }
            $pkgName = ''
            $pkgVer  = ''
            $requires = [System.Collections.Generic.List[object]]::new()
            foreach ($line in (Get-Content -LiteralPath $metaPath -ErrorAction SilentlyContinue)) {
                if ($line -eq '') { break }
                if ($line -match '^Name:\s*(.+)$')    { $pkgName = $matches[1].Trim(); continue }
                if ($line -match '^Version:\s*(.+)$') { $pkgVer  = $matches[1].Trim(); continue }
                if ($line -match '^Requires-Dist:\s*(.+)$') {
                    $raw = $matches[1].Trim()
                    if ($raw -match 'extra\s*==') { continue }
                    $depName = ''
                    $depSpec = ''
                    $mm = [regex]::Match($raw, '^(?<n>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:\((?<s1>[^)]*)\)|(?<s2>[^;]*))?')
                    if ($mm.Success) {
                        $depName = $mm.Groups['n'].Value
                        if ($mm.Groups['s1'].Success -and $mm.Groups['s1'].Value) { $depSpec = $mm.Groups['s1'].Value }
                        elseif ($mm.Groups['s2'].Success) { $depSpec = $mm.Groups['s2'].Value }
                    }
                    if ($depName) {
                        $requires.Add([pscustomobject]@{ name = $depName.ToLowerInvariant().Replace('_', '-'); spec = $depSpec.Trim() })
                    }
                    continue
                }
            }
            if (-not $pkgName) { $brokenDists++; continue }
            $record = [pscustomobject]@{
                env = $name; package = $pkgName.ToLowerInvariant().Replace('_', '-')
                display = $pkgName; version = $pkgVer
                requires = $requires; has_record = (Test-Path -LiteralPath (Join-Path $info.FullName 'RECORD'))
            }
            $dists.Add($record)
            $allDists.Add($record)
        }
    }

    $envs.Add([pscustomobject]@{
        name = $name; path = $envPath; tier = (Get-EnvTier -Name $name)
        python = $pyVersion; home = $basePath; python_exe = $pyExe
        site_packages = $sitePackages; cfg_ok = $cfgOk
        packages = $dists.Count; broken = $brokenDists; dists = $dists
        health = 'UNKNOWN'; issues = [System.Collections.Generic.List[string]]::new()
    })
}

Write-Stage -Message ('環境 ' + $envs.Count + ' 個，套件記錄 ' + $allDists.Count + ' 筆') -Percent 32 -Level 'OK'

# ------------------------------------------------------------
# 3. 健康檢查
# ------------------------------------------------------------

Write-Stage -Message '健康檢查' -Percent 36

foreach ($venv in $envs) {
    if (-not $venv.cfg_ok)        { $venv.issues.Add('pyvenv.cfg 缺失或無法讀取') }
    if (-not $venv.python_exe)    { $venv.issues.Add('找不到直譯器可執行檔') }
    elseif ($venv.python_exe -match '(?i)WindowsApps') { $venv.issues.Add('直譯器指向 Microsoft Store 別名（安裝樁），視為不存在') }
    if (-not $venv.site_packages) { $venv.issues.Add('找不到 site-packages') }
    if ($venv.packages -eq 0)     { $venv.issues.Add('沒有任何已安裝套件記錄') }
    if ($venv.broken -gt 0)       { $venv.issues.Add($venv.broken.ToString() + ' 個 dist-info 損毀（缺 METADATA 或 Name）') }
    if ($venv.issues.Count -eq 0) { $venv.health = 'HEALTHY' }
    elseif (-not $venv.python_exe -or -not $venv.site_packages) { $venv.health = 'BROKEN' }
    else { $venv.health = 'DEGRADED' }
}
$healthy = @($envs | Where-Object { $_.health -eq 'HEALTHY' }).Count
Write-Stage -Message ('健康 ' + $healthy + ' / ' + $envs.Count) -Percent 40 -Level $(if ($healthy -eq $envs.Count) { 'OK' } else { 'WARN' })

# ------------------------------------------------------------
# 4. Local-free 衝突快篩（不連網、不呼叫 pip）
# ------------------------------------------------------------

Write-Stage -Message 'Local-free 相依衝突快篩（讀 METADATA，不連網）' -Percent 44

$findings = [System.Collections.Generic.List[object]]::new()
function Add-Finding {
    param([string]$Kind, [string]$Severity, [string]$EnvName, [string]$Package,
          [string]$Detail, [string]$Action)
    $findings.Add([pscustomobject]@{
        kind = $Kind; severity = $Severity; env = $EnvName; package = $Package
        detail = $Detail; action = $Action
    })
}

foreach ($venv in $envs) {
    $installed = @{}
    foreach ($dist in $venv.dists) { $installed[$dist.package] = $dist.version }
    foreach ($dist in $venv.dists) {
        foreach ($req in $dist.requires) {
            if (-not $installed.ContainsKey($req.name)) {
                if ($req.spec) {
                    Add-Finding -Kind 'MISSING_DEP' -Severity 'WARN' -EnvName $venv.name -Package $req.name `
                        -Detail ($dist.display + ' ' + $dist.version + ' 需要 ' + $req.name + ' ' + $req.spec + '，但環境內沒有') `
                        -Action ('於 ' + $venv.name + ' 補裝 ' + $req.name + $req.spec)
                }
                continue
            }
            $have = $installed[$req.name]
            if (-not (Test-Specifier -Installed $have -Specifier $req.spec)) {
                Add-Finding -Kind 'VERSION_CONFLICT' -Severity 'FAIL' -EnvName $venv.name -Package $req.name `
                    -Detail ($dist.display + ' ' + $dist.version + ' 要求 ' + $req.name + ' ' + $req.spec + '，實際安裝 ' + $have) `
                    -Action ('降/升 ' + $req.name + ' 至 ' + $req.spec + '，或把 ' + $dist.display + ' 分流獨立環境')
            }
        }
    }
}

# 黃金律
foreach ($venv in $envs) {
    foreach ($dist in $venv.dists) {
        if (-not $Policy.GoldenPins.Contains($dist.package)) { continue }
        $pin = $Policy.GoldenPins[$dist.package]
        if (-not (Test-Specifier -Installed $dist.version -Specifier $pin)) {
            Add-Finding -Kind 'GOLDEN_RULE' -Severity 'FAIL' -EnvName $venv.name -Package $dist.package `
                -Detail ($dist.display + ' ' + $dist.version + ' 違反黃金律 ' + $pin) `
                -Action ('釘選 ' + $dist.package + $pin + ' 並重建 ' + $venv.name)
        }
    }
}

# 禁用套件
foreach ($venv in $envs) {
    foreach ($dist in $venv.dists) {
        if ($Policy.Banned -notcontains $dist.package) { continue }
        $reason = ''
        if ($Policy.BannedReason.ContainsKey($dist.package)) { $reason = $Policy.BannedReason[$dist.package] }
        Add-Finding -Kind 'BANNED' -Severity 'FAIL' -EnvName $venv.name -Package $dist.package `
            -Detail ($dist.display + ' 為禁用套件：' + $reason) `
            -Action ('自 ' + $venv.name + ' 拔除 ' + $dist.package)
    }
}

# 中高風險套件必須隔離
foreach ($venv in $envs) {
    foreach ($dist in $venv.dists) {
        if (-not $Policy.HighRisk.Contains($dist.package)) { continue }
        $riskHome = $Policy.HighRisk[$dist.package]
        if ($venv.name -ieq $riskHome) { continue }
        if ($venv.tier -eq 'ISOLATED') { continue }
        Add-Finding -Kind 'RISK_ISOLATION' -Severity 'WARN' -EnvName $venv.name -Package $dist.package `
            -Detail ($dist.display + ' ' + $dist.version + ' 是中高風險套件，不應與 ' + $venv.tier + ' 環境同住') `
            -Action ('立拔並分流到專屬環境 ' + $riskHome)
    }
}

# Python 版本天花板
foreach ($venv in $envs) {
    foreach ($dist in $venv.dists) {
        if (-not $Policy.PythonCeiling.Contains($dist.package)) { continue }
        $ceiling = $Policy.PythonCeiling[$dist.package]
        if (-not $venv.python) { continue }
        if ((Compare-PyVersion -Left $venv.python -Right $ceiling) -gt 0) {
            Add-Finding -Kind 'PY_CEILING' -Severity 'FAIL' -EnvName $venv.name -Package $dist.package `
                -Detail ($dist.display + ' 不支援 Python ' + $venv.python + '（上限 ' + $ceiling + '）') `
                -Action ('以 py -' + $ceiling + ' 重建 ' + $venv.name + '，或把 ' + $dist.package + ' 分流')
        }
    }
}

# base 精簡化
foreach ($venv in $envs) {
    if ($venv.tier -ne 'BASE') { continue }
    foreach ($dist in $venv.dists) {
        if ($Policy.BaseAllowList -contains $dist.package) { continue }
        Add-Finding -Kind 'BASE_BLOAT' -Severity 'WARN' -EnvName $venv.name -Package $dist.package `
            -Detail ($dist.display + ' ' + $dist.version + ' 不在 base 白名單內') `
            -Action ('自 base 移出，改裝到需要它的 via_* 環境')
    }
}

# 多版本並存：白名單內是合法，白名單外是漂移
$versionSpread = @{}
foreach ($dist in $allDists) {
    if (-not $versionSpread.ContainsKey($dist.package)) { $versionSpread[$dist.package] = @{} }
    $versionSpread[$dist.package][$dist.version] = $true
}
$multiRows = [System.Collections.Generic.List[object]]::new()
foreach ($pkg in $versionSpread.Keys) {
    $versions = @($versionSpread[$pkg].Keys | Sort-Object)
    if ($versions.Count -lt 2) { continue }
    $allowed = ($Policy.MultiVersionAllowed -contains $pkg)
    $owners = @($allDists | Where-Object { $_.package -eq $pkg } |
        ForEach-Object { $_.env + '=' + $_.version }) -join ', '
    $multiRows.Add([pscustomobject]@{
        package = $pkg; versions = ($versions -join ' | '); owners = $owners
        verdict = $(if ($allowed) { 'ALLOWED' } else { 'DRIFT' })
    })
    if (-not $allowed) {
        Add-Finding -Kind 'VERSION_DRIFT' -Severity 'WARN' -EnvName '(cross-env)' -Package $pkg `
            -Detail ('跨環境存在 ' + $versions.Count + ' 個版本：' + $owners) `
            -Action ('收斂為單一版本，或加入多版本白名單')
    }
}

$failCount = @($findings | Where-Object { $_.severity -eq 'FAIL' }).Count
$warnCount = @($findings | Where-Object { $_.severity -eq 'WARN' }).Count
Write-Stage -Message ('快篩結果：FAIL ' + $failCount + '，WARN ' + $warnCount) -Percent 56 -Level $(if ($failCount) { 'FAIL' } elseif ($warnCount) { 'WARN' } else { 'OK' })

# ------------------------------------------------------------
# 5. uv 與鏡像源
# ------------------------------------------------------------

$uvPath = $UvExe
if (-not $uvPath) {
    $found = Get-Command 'uv' -ErrorAction SilentlyContinue
    if ($null -ne $found) { $uvPath = $found.Source }
}
$uvRows = [System.Collections.Generic.List[object]]::new()
if (-not $uvPath) {
    Write-Stage -Message 'PATH 上找不到 uv，跳過 uv 交叉驗證（local-free 快篩仍已完成）' -Percent 60 -Level 'WARN'
} elseif ($SkipUvCheck) {
    Write-Stage -Message 'uv 交叉驗證已略過（-SkipUvCheck）' -Percent 60 -Level 'WARN'
} else {
    Write-Stage -Message ('uv 交叉驗證：' + $uvPath) -Percent 60
    foreach ($venv in $envs) {
        if (-not $venv.python_exe) { continue }
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $uvPath
        $psi.Arguments = 'pip check --python "' + $venv.python_exe + '"'
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.CreateNoWindow = $true
        try {
            $proc = [System.Diagnostics.Process]::Start($psi)
            $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
            $stderrTask = $proc.StandardError.ReadToEndAsync()
            if (-not $proc.WaitForExit(20000)) { $proc.Kill($true) }
            $combined = ($stdoutTask.Result + "`n" + $stderrTask.Result).Trim()
            $uvVerdict = 'CLEAN'
            if ($proc.ExitCode -ne 0) {
                # 檢查不到直譯器不是衝突，是探測失敗。證據誠實：兩者不可混為一談。
                if ($combined -match '(?i)failed to inspect|no such file|not found|cannot find') {
                    $uvVerdict = 'UNAVAILABLE'
                } else {
                    $uvVerdict = 'CONFLICT'
                }
            }
            $uvRows.Add([pscustomobject]@{
                env = $venv.name; exit = $proc.ExitCode; verdict = $uvVerdict
                output = ($combined -split "`n" | Select-Object -First 6) -join ' / '
            })
        } catch {
            $uvRows.Add([pscustomobject]@{ env = $venv.name; exit = -1; verdict = 'PROBE_FAIL'; output = $_.Exception.Message })
        }
    }
    Write-Stage -Message ('uv pip check 完成：' + $uvRows.Count + ' 個環境') -Percent 66 -Level 'OK'
}

$mirrorRows = [System.Collections.Generic.List[object]]::new()
if ($SkipMirrorProbe) {
    Write-Stage -Message '鏡像源探測已略過（-SkipMirrorProbe）' -Percent 70 -Level 'WARN'
} else {
    Write-Stage -Message '鏡像源延遲探測' -Percent 68
    foreach ($mirror in $Mirrors) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $state = 'UNREACHABLE'
        try {
            $null = Invoke-WebRequest -Uri $mirror.url -Method Head -TimeoutSec 6 -ErrorAction Stop
            $state = 'OK'
        } catch {
            $state = 'UNREACHABLE'
        }
        $sw.Stop()
        $mirrorRows.Add([pscustomobject]@{ name = $mirror.name; url = $mirror.url; state = $state; ms = [int]$sw.ElapsedMilliseconds })
    }
    $reachable = @($mirrorRows | Where-Object { $_.state -eq 'OK' } | Sort-Object -Property @{ e = 'ms'; desc = $false })
    if ($reachable.Count -gt 0) {
        Write-Stage -Message ('最快鏡像：' + $reachable[0].name + ' (' + $reachable[0].ms + 'ms)') -Percent 72 -Level 'OK'
    } else {
        Write-Stage -Message '所有鏡像源都連不上，計畫將以離線模式標註' -Percent 72 -Level 'WARN'
    }
}
$preferredMirror = 'https://pypi.org/simple'
$fastest = @($mirrorRows | Where-Object { $_.state -eq 'OK' } | Sort-Object -Property @{ e = 'ms'; desc = $false })
if ($fastest.Count -gt 0) { $preferredMirror = $fastest[0].url }

# ------------------------------------------------------------
# 6. LKGC：與前一次成功組合比對
# ------------------------------------------------------------

Write-Stage -Message 'LKGC 基線比對' -Percent 76

$lkgcRows = [System.Collections.Generic.List[object]]::new()
foreach ($venv in $envs) {
    $baselinePath = Join-Path $LkgcDir ($venv.name + '.json')
    $current = @{}
    foreach ($dist in $venv.dists) { $current[$dist.package] = $dist.version }

    if (-not (Test-Path -LiteralPath $baselinePath)) {
        $lkgcRows.Add([pscustomobject]@{ env = $venv.name; state = 'NO_BASELINE'; detail = '尚無成功基線，本次若健康將建立' })
        continue
    }
    try {
        $baseline = Get-Content -LiteralPath $baselinePath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $lkgcRows.Add([pscustomobject]@{ env = $venv.name; state = 'BASELINE_UNREADABLE'; detail = $_.Exception.Message })
        continue
    }
    $baseMap = @{}
    foreach ($prop in $baseline.packages.PSObject.Properties) { $baseMap[$prop.Name] = [string]$prop.Value }

    $added = @($current.Keys | Where-Object { -not $baseMap.ContainsKey($_) })
    $removed = @($baseMap.Keys | Where-Object { -not $current.ContainsKey($_) })
    $changed = @($current.Keys | Where-Object { $baseMap.ContainsKey($_) -and $baseMap[$_] -ne $current[$_] } |
        ForEach-Object { $_ + ': ' + $baseMap[$_] + ' -> ' + $current[$_] })
    $delta = $added.Count + $removed.Count + $changed.Count
    $lkgcRows.Add([pscustomobject]@{
        env = $venv.name
        state = $(if ($delta -eq 0) { 'MATCHES_LKGC' } else { 'DRIFTED' })
        detail = ('新增 ' + $added.Count + '，移除 ' + $removed.Count + '，變版 ' + $changed.Count +
                  $(if ($changed.Count -gt 0) { '｜' + (($changed | Select-Object -First 5) -join '；') } else { '' }))
    })
}

# 只有健康且無 FAIL 的環境才可以更新基線
$baselineUpdated = 0
foreach ($venv in $envs) {
    if ($venv.health -ne 'HEALTHY') { continue }
    $envFails = @($findings | Where-Object { $_.env -eq $venv.name -and $_.severity -eq 'FAIL' }).Count
    if ($envFails -gt 0) { continue }
    $packages = [ordered]@{}
    foreach ($dist in ($venv.dists | Sort-Object -Property @{ e = 'package'; desc = $false })) {
        $packages[$dist.package] = $dist.version
    }
    $doc = [ordered]@{
        env = $venv.name; python = $venv.python; recorded = (Get-Date).ToString('o')
        stamp = $Script:Stamp; packages = $packages
    }
    Write-Utf8NoBom -Path (Join-Path $LkgcDir ($venv.name + '.json')) -Text ($doc | ConvertTo-Json -Depth 5)
    $baselineUpdated++
}
Write-Stage -Message ('LKGC：更新 ' + $baselineUpdated + ' 個成功基線') -Percent 80 -Level 'OK'

# ------------------------------------------------------------
# 7. 變更計畫（分為可並行 / 相依順序兩類）
# ------------------------------------------------------------

Write-Stage -Message '擬定變更計畫' -Percent 84

$parallelFix = [System.Collections.Generic.List[object]]::new()
$sequential  = [System.Collections.Generic.List[object]]::new()

foreach ($finding in $findings) {
    $isSequential = ($finding.kind -eq 'PY_CEILING' -or $finding.kind -eq 'GOLDEN_RULE' -or
                     $finding.kind -eq 'RISK_ISOLATION' -or $finding.kind -eq 'VERSION_CONFLICT')
    $item = [pscustomobject]@{
        order = 0; env = $finding.env; package = $finding.package
        kind = $finding.kind; severity = $finding.severity; action = $finding.action
    }
    if ($isSequential) { $sequential.Add($item) } else { $parallelFix.Add($item) }
}

$rank = @{ 'PY_CEILING' = 1; 'GOLDEN_RULE' = 2; 'VERSION_CONFLICT' = 3; 'RISK_ISOLATION' = 4 }
$sequenced = @($sequential | Sort-Object -Property @{ e = { $rank[$_.kind] }; desc = $false }, @{ e = 'env'; desc = $false })
$order = 0
foreach ($item in $sequenced) { $order++; $item.order = $order }

$rebuildTargets = @($findings |
    Where-Object { $_.kind -eq 'GOLDEN_RULE' -or $_.kind -eq 'PY_CEILING' -or $_.kind -eq 'BANNED' } |
    ForEach-Object { $_.env } | Sort-Object -Unique | Where-Object { $_ -ne '(cross-env)' })
$isolationTargets = @($findings | Where-Object { $_.kind -eq 'RISK_ISOLATION' } |
    ForEach-Object { $_.package + ' -> ' + ($_.action -replace '^.*專屬環境\s*', '') } | Sort-Object -Unique)

$approvalToken = '==VEM-APPROVE==' + $Script:Stamp + '-' +
    ([System.BitConverter]::ToString(
        [System.Security.Cryptography.SHA256]::HashData(
            [System.Text.Encoding]::UTF8.GetBytes(($findings | ConvertTo-Json -Depth 4 -Compress))
        )).Replace('-', '').Substring(0, 12).ToLowerInvariant())

Write-Stage -Message ('計畫：並行 ' + $parallelFix.Count + ' 項，順序 ' + $sequenced.Count + ' 項，重建 ' + $rebuildTargets.Count + ' 個環境') -Percent 88 -Level 'OK'

# ------------------------------------------------------------
# 8. apply 腳本（預設 dry-run，需權杖 + -Commit）
# ------------------------------------------------------------

$planLines = [System.Collections.Generic.List[string]]::new()
$planLines.Add('#requires -Version 7.0')
$planLines.Add('param([string]$Token = '''', [switch]$Commit)')
$planLines.Add('# ============================================================')
$planLines.Add('# VIA EnvManager 變更計畫 ' + $Script:Stamp)
$planLines.Add('# 這支腳本預設什麼都不做。要實際執行必須同時滿足兩件事：')
$planLines.Add('#   1. -Token 帶入 HTML 報表上的核准權杖（代表你看過這份計畫）')
$planLines.Add('#   2. -Commit 明示提交')
$planLines.Add('# 基線：前一次成功組合（LKGC）。鏡像源：' + $preferredMirror)
$planLines.Add('# ============================================================')
$planLines.Add('$ErrorActionPreference = ''Stop''')
$planLines.Add('$Expected = ''' + $approvalToken + '''')
$planLines.Add('$Mirror = ''' + $preferredMirror + '''')
$planLines.Add('$approved = ($Token -eq $Expected) -and $Commit')
$planLines.Add('if (-not $approved) {')
$planLines.Add('    Write-Host ''[DRY-RUN] 未核准，只列出將執行的動作。'' -ForegroundColor Yellow')
$planLines.Add('    Write-Host ''  需要： -Token <報表上的權杖> -Commit'' -ForegroundColor Yellow')
$planLines.Add('}')
$planLines.Add('function Invoke-Step { param([string]$Label, [string]$Command)')
$planLines.Add('    if (-not $approved) { Write-Host ("[DRY] " + $Label) -ForegroundColor Yellow; Write-Host ("      " + $Command) -ForegroundColor DarkGray; return }')
$planLines.Add('    Write-Host ("[RUN] " + $Label) -ForegroundColor Green')
$planLines.Add('    Invoke-Expression $Command }')
$planLines.Add('')
$planLines.Add('Write-Host ''--- 第 1 輪：可並行修正 ---'' -ForegroundColor Cyan')
if ($parallelFix.Count -eq 0) {
    $planLines.Add('Write-Host ''  (無)'' -ForegroundColor DarkGray')
} else {
    foreach ($item in $parallelFix) {
        $label = ($item.kind + ' | ' + $item.env + ' | ' + $item.package + ' | ' + $item.action).Replace("'", "''")
        $planLines.Add("Invoke-Step -Label '" + $label + "' -Command 'Write-Host ''需人工確認具體指令：" + $item.action.Replace("'", "''") + "'''")
    }
}
$planLines.Add('')
$planLines.Add('Write-Host ''--- 第 2 輪：依拓撲順序修正 ---'' -ForegroundColor Cyan')
if ($sequenced.Count -eq 0) {
    $planLines.Add('Write-Host ''  (無)'' -ForegroundColor DarkGray')
} else {
    foreach ($item in $sequenced) {
        $label = ('#' + $item.order + ' ' + $item.kind + ' | ' + $item.env + ' | ' + $item.package + ' | ' + $item.action).Replace("'", "''")
        $planLines.Add("Invoke-Step -Label '" + $label + "' -Command 'Write-Host ''需人工確認具體指令：" + $item.action.Replace("'", "''") + "'''")
    }
}
$planLines.Add('')
$planLines.Add('Write-Host ''--- 第 3 輪：收尾與硬化 ---'' -ForegroundColor Cyan')
$planLines.Add('Write-Host ''  重建後請重新執行 VIA_EnvManager 產生新的 LKGC 基線。''')
Write-Utf8NoBom -Path $PlanPath -Text (($planLines -join "`n") + "`n")

Add-Utf8NoBomLine -Path $GovernanceLog -Text (([ordered]@{
    ts = (Get-Date).ToString('o'); stamp = $Script:Stamp; engine = 'VIA_EnvManager_v0100'
    envs = $envs.Count; healthy = $healthy; packages = $allDists.Count
    fail = $failCount; warn = $warnCount
    parallel = $parallelFix.Count; sequential = $sequenced.Count
    rebuild = $rebuildTargets; isolate = $isolationTargets
    lkgc_updated = $baselineUpdated; mirror = $preferredMirror
    uv = [bool]$uvPath; token = $approvalToken
    outcome = $(if ($failCount -gt 0) { 'RED' } elseif ($warnCount -gt 0) { 'AMBER' } else { 'GREEN' })
} | ConvertTo-Json -Depth 5 -Compress))

# ------------------------------------------------------------
# 9. HTML UI Matrix
# ------------------------------------------------------------

Write-Stage -Message '渲染 UI Matrix' -Percent 92

function New-Rows {
    param([object[]]$Items, [string[]]$Fields, [string]$StatusField = '', [int]$Limit = 600)
    $sb = [System.Text.StringBuilder]::new()
    $count = 0
    foreach ($item in $Items) {
        if ($count -ge $Limit) { break }
        $count++
        $null = $sb.Append('<tr>')
        foreach ($field in $Fields) {
            $value = ''
            if ($item.PSObject.Properties.Name -contains $field) {
                $raw = $item.$field
                if ($raw -is [System.Array]) { $value = ($raw -join ', ') } else { $value = [string]$raw }
            }
            $cls = ''
            if ($StatusField -and $field -eq $StatusField) {
                if ($value -match 'HEALTHY|CLEAN|OK|GREEN|ALLOWED|MATCHES_LKGC') { $cls = " class='ok'" }
                elseif ($value -match 'FAIL|BROKEN|CONFLICT|RED') { $cls = " class='fail'" }
                elseif ($value -match 'WARN|DEGRADED|DRIFT|NO_BASELINE|UNREACHABLE|UNAVAILABLE|AMBER') { $cls = " class='warn'" }
            }
            $null = $sb.Append('<td' + $cls + '>' + (ConvertTo-HtmlText -Text $value) + '</td>')
        }
        $null = $sb.Append('</tr>')
    }
    if ($count -eq 0) { $null = $sb.Append("<tr><td colspan='" + $Fields.Count + "' class='muted'>—— 無 ——</td></tr>") }
    return $sb.ToString()
}

$tierRows = [System.Collections.Generic.List[object]]::new()
foreach ($tier in @('BASE', 'CORE', 'SUBSYSTEM', 'ISOLATED', 'OTHERS')) {
    $members = @($envs | Where-Object { $_.tier -eq $tier })
    if ($members.Count -eq 0) { continue }
    $tierRows.Add([pscustomobject]@{
        tier = $tier; envs = $members.Count
        packages = (@($members | ForEach-Object { $_.packages }) | Measure-Object -Sum).Sum
        health = (($members | ForEach-Object { $_.name + '=' + $_.health }) -join ', ')
    })
}

$envRows      = New-Rows -Items @($envs | Sort-Object -Property @{ e = 'tier'; desc = $false }, @{ e = 'name'; desc = $false }) -Fields @('name','tier','python','health','packages','broken','path') -StatusField 'health'
$findingRows  = New-Rows -Items @($findings | Sort-Object -Property @{ e = 'severity'; desc = $false }, @{ e = 'env'; desc = $false }) -Fields @('severity','kind','env','package','detail','action') -StatusField 'severity'
$parallelRows = New-Rows -Items @($parallelFix) -Fields @('kind','env','package','action')
$seqRows      = New-Rows -Items @($sequenced) -Fields @('order','kind','env','package','action')
$multiRowsHtml= New-Rows -Items @($multiRows | Sort-Object -Property @{ e = 'verdict'; desc = $true }) -Fields @('package','versions','owners','verdict') -StatusField 'verdict'
$lkgcRowsHtml = New-Rows -Items @($lkgcRows) -Fields @('env','state','detail') -StatusField 'state'
$mirrorRowsHtml = New-Rows -Items @($mirrorRows | Sort-Object -Property @{ e = 'ms'; desc = $false }) -Fields @('name','state','ms','url') -StatusField 'state'
$uvRowsHtml   = New-Rows -Items @($uvRows) -Fields @('env','verdict','exit','output') -StatusField 'verdict'
$logText      = ConvertTo-HtmlText -Text ($Script:Log -join "`n")

$verdict = 'GREEN'
if ($warnCount -gt 0) { $verdict = 'AMBER' }
if ($failCount -gt 0) { $verdict = 'RED' }
$verdictClass = 'ok'
if ($verdict -eq 'AMBER') { $verdictClass = 'warn' }
if ($verdict -eq 'RED')   { $verdictClass = 'fail' }
$elapsed = [int]((Get-Date) - $Script:Start).TotalSeconds

$html = @"
<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA EnvManager Unified Governance Matrix</title>
<style>
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
.token{background:#1d1f20;color:#f2f2f3;padding:10px 12px;border-radius:3px;font-family:Consolas,monospace;font-size:12px;overflow-wrap:anywhere;margin:8px 0}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:34vh;overflow:auto}
code{background:#ececed;padding:1px 5px;border-radius:2px}
</style></head><body>
<div class="seal">環</div>
<h1>EnvManager Unified Governance</h1>
<p class="lede">$(ConvertTo-HtmlText -Text $EnvRoot) · $($Script:Stamp) · 唯讀分析，未變更任何環境 · 耗時 ${elapsed}s</p>
<div class="cards">
  <div class="card"><div class="k">Verdict</div><div class="v $verdictClass">$verdict</div></div>
  <div class="card"><div class="k">Envs</div><div class="v">$($envs.Count)</div></div>
  <div class="card"><div class="k">Healthy</div><div class="v ok">$healthy</div></div>
  <div class="card"><div class="k">Packages</div><div class="v">$($allDists.Count)</div></div>
  <div class="card"><div class="k">Fail</div><div class="v fail">$failCount</div></div>
  <div class="card"><div class="k">Warn</div><div class="v warn">$warnCount</div></div>
  <div class="card"><div class="k">Parallel Fix</div><div class="v">$($parallelFix.Count)</div></div>
  <div class="card"><div class="k">Sequential</div><div class="v">$($sequenced.Count)</div></div>
  <div class="card"><div class="k">LKGC Saved</div><div class="v">$baselineUpdated</div></div>
</div>

<h2>核准權杖</h2>
<p class="lede">看完計畫後，把下面這串貼進 apply 腳本才會真的動環境。沒有權杖它只會列印，不會執行。</p>
<div class="token">$(ConvertTo-HtmlText -Text $approvalToken)</div>
<p class="lede"><code>pwsh -NoProfile -File "$(ConvertTo-HtmlText -Text $PlanPath)" -Token "$(ConvertTo-HtmlText -Text $approvalToken)" -Commit</code></p>

<h2>環境分層矩陣</h2>
<table><colgroup><col style="width:12%"><col style="width:8%"><col style="width:64%"><col style="width:16%"></colgroup>
<tr><th>Tier</th><th>Envs</th><th>Health</th><th>Packages</th></tr>
$(New-Rows -Items @($tierRows) -Fields @('tier','envs','health','packages'))</table>

<h2>環境健康度</h2>
<table><colgroup><col style="width:13%"><col style="width:10%"><col style="width:8%"><col style="width:10%"><col style="width:7%"><col style="width:7%"><col style="width:45%"></colgroup>
<tr><th>Env</th><th>Tier</th><th>Python</th><th>Health</th><th>Pkgs</th><th>Broken</th><th>Path</th></tr>$envRows</table>

<h2>衝突與政策違規（local-free 快篩）</h2>
<p class="lede">全部由 dist-info/METADATA 的 Requires-Dist 與實際安裝版本比對得出，未連網、未呼叫 pip、未安裝任何東西。版本比較為 PEP440-lite 啟發式（證據等級 M）。</p>
<table><colgroup><col style="width:7%"><col style="width:12%"><col style="width:10%"><col style="width:10%"><col style="width:34%"><col style="width:27%"></colgroup>
<tr><th>Severity</th><th>Kind</th><th>Env</th><th>Package</th><th>Detail</th><th>Action</th></tr>$findingRows</table>

<h2>多版本並存</h2>
<table><colgroup><col style="width:14%"><col style="width:20%"><col style="width:56%"><col style="width:10%"></colgroup>
<tr><th>Package</th><th>Versions</th><th>Owners</th><th>Verdict</th></tr>$multiRowsHtml</table>

<h2>第 1 輪：可並行修正</h2>
<table><colgroup><col style="width:14%"><col style="width:12%"><col style="width:14%"><col style="width:60%"></colgroup>
<tr><th>Kind</th><th>Env</th><th>Package</th><th>Action</th></tr>$parallelRows</table>

<h2>第 2 輪：依拓撲順序修正</h2>
<table><colgroup><col style="width:5%"><col style="width:14%"><col style="width:12%"><col style="width:14%"><col style="width:55%"></colgroup>
<tr><th>#</th><th>Kind</th><th>Env</th><th>Package</th><th>Action</th></tr>$seqRows</table>

<h2>LKGC 基線比對</h2>
<table><colgroup><col style="width:14%"><col style="width:16%"><col style="width:70%"></colgroup>
<tr><th>Env</th><th>State</th><th>Detail</th></tr>$lkgcRowsHtml</table>

<h2>鏡像源</h2>
<table><colgroup><col style="width:14%"><col style="width:12%"><col style="width:10%"><col style="width:64%"></colgroup>
<tr><th>Mirror</th><th>State</th><th>ms</th><th>URL</th></tr>$mirrorRowsHtml</table>

<h2>uv 交叉驗證</h2>
<table><colgroup><col style="width:14%"><col style="width:12%"><col style="width:8%"><col style="width:66%"></colgroup>
<tr><th>Env</th><th>Verdict</th><th>Exit</th><th>Output</th></tr>$uvRowsHtml</table>

<h2>執行日誌</h2>
<pre>$logText</pre>
</body></html>
"@

Write-Utf8NoBom -Path $HtmlPath -Text $html

$snapshot = [ordered]@{
    engine = 'VIA_EnvManager_UnifiedGovernance'; version = 'v0100'; stamp = $Script:Stamp
    env_root = $EnvRoot; verdict = $verdict; elapsed_seconds = $elapsed
    envs = @($envs | Select-Object name, tier, python, health, packages, broken, path)
    findings = @($findings); multi_version = @($multiRows); lkgc = @($lkgcRows)
    mirrors = @($mirrorRows); uv = @($uvRows)
    plan = [ordered]@{ parallel = @($parallelFix); sequential = @($sequenced)
                       rebuild = $rebuildTargets; isolate = $isolationTargets }
    approval_token = $approvalToken; plan_script = $PlanPath
}
Write-Utf8NoBom -Path $SnapshotPath -Text ($snapshot | ConvertTo-Json -Depth 8)

Write-Stage -Message ('完成。裁決 ' + $verdict) -Percent 100 -Level $(if ($verdict -eq 'RED') { 'FAIL' } elseif ($verdict -eq 'AMBER') { 'WARN' } else { 'OK' })
Write-Progress -Activity 'VIA EnvManager Unified Governance v0100' -Completed

Write-Host ''
Write-Host (' matrix   : ' + $HtmlPath)      -ForegroundColor DarkCyan
Write-Host (' snapshot : ' + $SnapshotPath)  -ForegroundColor DarkCyan
Write-Host (' plan     : ' + $PlanPath)      -ForegroundColor DarkCyan
Write-Host (' log      : ' + $GovernanceLog) -ForegroundColor DarkCyan
Write-Host ''
Write-Host ' 核准權杖（要動環境才需要）：' -ForegroundColor Yellow
Write-Host ('   ' + $approvalToken) -ForegroundColor Yellow
Write-Host ''
Write-Host '============================================================'
Write-Host (' VIA ENVMANAGER UNIFIED GOVERNANCE  ->  ' + $verdict)
Write-Host ' 唯讀分析完成。未安裝、未移除、未變更任何環境。'
Write-Host '============================================================'

if (-not $NoBrowser) {
    try { Start-Process -FilePath $HtmlPath | Out-Null } catch { Write-Host ' (browser launch skipped)' -ForegroundColor DarkGray }
}
