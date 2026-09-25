#requires -Version 7.0
param(
    [ValidateSet('All', 'Spec', 'Visual', 'Layout', 'Interaction', 'Governance')]
    [string]$Mode        = 'Governance',
    [string]$Task        = 'env-provision',
    [string]$EnvRoot     = 'C:\Users\tonyk\envs',
    [string]$WorkRoot    = 'C:\VeritasIntelligenceAnalytics\CGE\Provision',
    [string]$LkgcRoot    = 'C:\VeritasIntelligenceAnalytics\CGE\EnvManager\lkgc',
    [string]$UvExe       = '',
    [string]$Token       = '',
    [switch]$Interactive,
    [switch]$Commit,
    [switch]$SkipMirrorProbe,
    [switch]$SkipResolve,
    [switch]$NoBrowser
)

# ============================================================
# VIA Environment Provisioner v0100
#
# 依 Invoke-VeritasCodexNexus.ps1 的**實際**簽章設計參數（-Mode/-Task），
# 所以可以當成 Codex Nexus 的一個 task 被呼叫，也可以單獨執行。
#
# 流程（每一步不過就停，不會硬著頭皮往下裝）：
#   1. 讀 LKGC —— 以「前一次成功的組合」為基準，不是從零猜
#   2. 盤點現況 —— base / via_core / via_* 的實裝與衝突
#   3. 風險分流 —— 中高風險工具一律獨立環境；plotly 這類允許多版本並存
#   4. 鏡像交互檢查 —— 清華／阿里／官方三方比對同一套件的可得版本
#   5. uv 解析預演 —— 只解析不安裝，解不出來就不進計畫
#   6. 核准 —— 預設權杖；-Interactive 才用 y/n 問答
#   7. 執行 —— 逐環境建置，成敗都寫回 log 供下一輪擬定計畫
#
# 治理：任何「重建」都是先建新環境、驗證通過才切換，舊環境改名保留不刪。
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:Log = [System.Collections.Generic.List[string]]::new()

function Write-Utf8NoBom {
    param([string]$TargetPath, [string]$Text)
    $dir = Split-Path -Path $TargetPath -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($TargetPath, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Write-Stage {
    param([string]$Message, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '][' + $Level + '] ' + $Message
    $Script:Log.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK') { $color = 'Green' }
    if ($Level -eq 'WARN') { $color = 'Yellow' }
    if ($Level -eq 'FAIL') { $color = 'Red' }
    Write-Host $line -ForegroundColor $color
}

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

foreach ($sub in @('out', 'logs', 'plans')) {
    $dir = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
}
$ProvisionLog = Join-Path $WorkRoot 'logs\provision_history.jsonl'

Write-Host ''
Write-Host '  VIA ENVIRONMENT PROVISIONER v0100' -ForegroundColor Cyan
Write-Host ('  Mode=' + $Mode + '  Task=' + $Task) -ForegroundColor DarkGray
Write-Host ''

if ($Task -ne 'env-provision') {
    Write-Stage -Message ('本外掛只處理 Task=env-provision，收到 ' + $Task + '，結束') -Level 'WARN'
    return
}

# ------------------------------------------------------------
# 0. 工具政策：類別、風險、落點
# ------------------------------------------------------------
# tier: CORE 可與核心同住；ISOLATE 中高風險必須獨立；MULTI 允許多版本並存
$ToolPolicy = @(
    [pscustomobject]@{ pkg='requests';         cat='爬蟲';   tier='CORE';    home='via_net';    pin='';              note='' }
    [pscustomobject]@{ pkg='httpx';            cat='爬蟲';   tier='CORE';    home='via_net';    pin='';              note='' }
    [pscustomobject]@{ pkg='beautifulsoup4';   cat='爬蟲';   tier='CORE';    home='via_net';    pin='';              note='與 bs4 同名混淆，統一用 beautifulsoup4' }
    [pscustomobject]@{ pkg='lxml';             cat='爬蟲';   tier='CORE';    home='via_net';    pin='';              note='' }
    [pscustomobject]@{ pkg='playwright';       cat='爬蟲';   tier='ISOLATE'; home='via_browser';pin='';              note='帶瀏覽器二進位，體積大且需額外 install' }
    [pscustomobject]@{ pkg='selenium';         cat='爬蟲';   tier='ISOLATE'; home='via_browser';pin='';              note='驅動版本綁瀏覽器版本' }
    [pscustomobject]@{ pkg='polars';           cat='加速器'; tier='CORE';    home='via_core';   pin='';              note='' }
    [pscustomobject]@{ pkg='pyarrow';          cat='加速器'; tier='CORE';    home='via_core';   pin='';              note='' }
    [pscustomobject]@{ pkg='duckdb';           cat='加速器'; tier='CORE';    home='via_core';   pin='';              note='' }
    [pscustomobject]@{ pkg='orjson';           cat='加速器'; tier='CORE';    home='via_core';   pin='';              note='' }
    [pscustomobject]@{ pkg='numba';            cat='加速器'; tier='ISOLATE'; home='via_numba';  pin='';              note='Python 上限 3.12，不得進 3.13 環境' }
    [pscustomobject]@{ pkg='ortools';          cat='加速器'; tier='ISOLATE'; home='via_numba';  pin='';              note='同上，Python 上限 3.12' }
    [pscustomobject]@{ pkg='aiohttp';          cat='網路';   tier='CORE';    home='via_net';    pin='';              note='' }
    [pscustomobject]@{ pkg='websockets';       cat='網路';   tier='CORE';    home='via_net';    pin='';              note='' }
    [pscustomobject]@{ pkg='winloop';          cat='網路';   tier='CORE';    home='via_net';    pin='';              note='Windows 用 winloop 取代 uvloop' }
    [pscustomobject]@{ pkg='plotly';           cat='繪圖';   tier='MULTI';   home='*';          pin='';              note='常用且易衝突，允許各環境不同版本' }
    [pscustomobject]@{ pkg='matplotlib';       cat='繪圖';   tier='MULTI';   home='*';          pin='';              note='同上' }
    [pscustomobject]@{ pkg='kaleido';          cat='繪圖';   tier='CORE';    home='via_core';   pin='';              note='plotly 靜態輸出用' }
    [pscustomobject]@{ pkg='pytesseract';      cat='OCR';    tier='CORE';    home='via_ocr';    pin='';              note='需系統層 tesseract' }
    [pscustomobject]@{ pkg='ocrmypdf';         cat='OCR';    tier='ISOLATE'; home='via_ocr';    pin='';              note='與 surya 的 pillow/pypdfium2 需求互斥' }
    [pscustomobject]@{ pkg='surya-ocr';        cat='OCR';    tier='ISOLATE'; home='via_surya';  pin='';              note='永久隔離：pillow<11 + pypdfium2==4.30 與 ocrmypdf 互斥' }
    [pscustomobject]@{ pkg='paddleocr';        cat='OCR';    tier='ISOLATE'; home='via_paddle'; pin='';              note='自帶深度學習相依，體積大' }
    [pscustomobject]@{ pkg='opencv-python';    cat='影像';   tier='CORE';    home='via_image';  pin='';              note='與 headless 版擇一' }
    [pscustomobject]@{ pkg='pillow';           cat='影像';   tier='CORE';    home='via_image';  pin='';              note='' }
    [pscustomobject]@{ pkg='onnxruntime';      cat='推論';   tier='ISOLATE'; home='vgf_core';   pin='';              note='' }
    [pscustomobject]@{ pkg='torch';            cat='推論';   tier='ISOLATE'; home='vgf_ml';     pin='';              note='體積最大，永久隔離' }
    [pscustomobject]@{ pkg='ray';              cat='分散式'; tier='ISOLATE'; home='via_ml';     pin='';              note='' }
)

# 黃金律：釘選規則集中在此，不散落在各環境
$GoldenPins = [ordered]@{}
$BannedPkgs = @('uvloop')
$PythonCeiling = [ordered]@{ 'numba' = '3.12'; 'ortools' = '3.12' }

# ------------------------------------------------------------
# 1. 讀 LKGC：以前一次成功組合為基準
# ------------------------------------------------------------
Write-Stage -Message '讀取前一次成功組合（LKGC）'
$lkgc = @{}
if (Test-Path -LiteralPath $LkgcRoot) {
    foreach ($file in (Get-ChildItem -LiteralPath $LkgcRoot -Filter '*.json' -ErrorAction SilentlyContinue)) {
        try {
            $doc = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $map = @{}
            foreach ($prop in $doc.packages.PSObject.Properties) { $map[$prop.Name] = [string]$prop.Value }
            $lkgc[[string]$doc.env] = [pscustomobject]@{
                python = [string]$doc.python; packages = $map; stamp = [string]$doc.stamp }
        } catch { }
    }
    Write-Stage -Message ('LKGC 基線 ' + $lkgc.Keys.Count + ' 個環境') -Level 'OK'
} else {
    Write-Stage -Message ('找不到 LKGC 目錄：' + $LkgcRoot + '，本輪將以現況為基準') -Level 'WARN'
}

# ------------------------------------------------------------
# 2. 盤點現況
# ------------------------------------------------------------
Write-Stage -Message ('盤點環境根目錄 ' + $EnvRoot)
$envs = [System.Collections.Generic.List[object]]::new()
if (Test-Path -LiteralPath $EnvRoot) {
    foreach ($dir in (Get-ChildItem -LiteralPath $EnvRoot -Directory -ErrorAction SilentlyContinue)) {
        $cfg = Join-Path $dir.FullName 'pyvenv.cfg'
        if (-not (Test-Path -LiteralPath $cfg)) { continue }
        $pyVersion = ''
        foreach ($line in (Get-Content -LiteralPath $cfg -ErrorAction SilentlyContinue)) {
            if ($line -match '^\s*version\s*=\s*(.+)$') { $pyVersion = $matches[1].Trim() }
        }
        $sp = ''
        foreach ($candidate in @('Lib\site-packages')) {
            $probe = Join-Path $dir.FullName $candidate
            if (Test-Path -LiteralPath $probe) { $sp = $probe }
        }
        if (-not $sp) {
            $lib = Join-Path $dir.FullName 'lib'
            if (Test-Path -LiteralPath $lib) {
                foreach ($sub in (Get-ChildItem -LiteralPath $lib -Directory -Filter 'python*' -ErrorAction SilentlyContinue)) {
                    $probe = Join-Path $sub.FullName 'site-packages'
                    if (Test-Path -LiteralPath $probe) { $sp = $probe; break }
                }
            }
        }
        $installed = @{}
        if ($sp) {
            foreach ($info in (Get-ChildItem -LiteralPath $sp -Directory -Filter '*.dist-info' -ErrorAction SilentlyContinue)) {
                $stem = $info.Name.Substring(0, $info.Name.Length - '.dist-info'.Length)
                if ($stem -match '^(?<n>.+)-(?<v>[^-]+)$') {
                    $installed[$matches['n'].ToLowerInvariant().Replace('_', '-')] = $matches['v']
                }
            }
        }
        $envs.Add([pscustomobject]@{
            name = $dir.Name; path = $dir.FullName; python = $pyVersion
            site_packages = $sp; packages = $installed
            managed = ($dir.Name -eq 'base' -or $dir.Name -match '^(via|vgf|vmt)[-_]')
        })
    }
}
$managed = @($envs | Where-Object { $_.managed })
Write-Stage -Message ('環境 ' + $envs.Count + ' 個，其中受管（base / via_ / vgf_ / vmt_）' + $managed.Count + ' 個') -Level 'OK'

# ------------------------------------------------------------
# 3. 衝突與風險分流
# ------------------------------------------------------------
Write-Stage -Message '衝突偵測與風險分流'
$findings = [System.Collections.Generic.List[object]]::new()
$policyByPkg = @{}
foreach ($row in $ToolPolicy) { $policyByPkg[$row.pkg] = $row }

foreach ($venv in $managed) {
    foreach ($pkg in $venv.packages.Keys) {
        $policy = $null
        if ($policyByPkg.ContainsKey($pkg)) { $policy = $policyByPkg[$pkg] }
        if ($BannedPkgs -contains $pkg) {
            $findings.Add([pscustomobject]@{ kind='BANNED'; severity='FAIL'; env=$venv.name; pkg=$pkg
                detail=('禁用套件（Windows 不支援）'); action='拔除，改用 winloop' })
            continue
        }
        if ($PythonCeiling.Contains($pkg) -and $venv.python) {
            $parts = @($venv.python -split '\.')
            $short = $venv.python
            if ($parts.Count -ge 2) { $short = $parts[0] + '.' + $parts[1] }
            $ceiling = $PythonCeiling[$pkg]
            if ([version]$short -gt [version]$ceiling) {
                $findings.Add([pscustomobject]@{ kind='PY_CEILING'; severity='FAIL'; env=$venv.name; pkg=$pkg
                    detail=('不支援 Python ' + $venv.python + '（上限 ' + $ceiling + '.x）')
                    action=('分流到 ' + $(if ($policy) { $policy.home } else { 'via_' + $pkg }) + '（以 py -' + $ceiling + ' 建立）') })
            }
        }
        if ($null -ne $policy -and $policy.tier -eq 'ISOLATE' -and $venv.name -ne $policy.home) {
            $findings.Add([pscustomobject]@{ kind='RISK_ISOLATION'; severity='WARN'; env=$venv.name; pkg=$pkg
                detail=('中高風險（' + $policy.cat + '）：' + $policy.note)
                action=('拔除並分流到專屬環境 ' + $policy.home) })
        }
    }
}
# 多版本白名單以外的跨環境漂移
$spread = @{}
foreach ($venv in $managed) {
    foreach ($pkg in $venv.packages.Keys) {
        if (-not $spread.ContainsKey($pkg)) { $spread[$pkg] = @{} }
        $spread[$pkg][$venv.packages[$pkg]] = $true
    }
}
foreach ($pkg in $spread.Keys) {
    if ($spread[$pkg].Keys.Count -lt 2) { continue }
    $policy = $null
    if ($policyByPkg.ContainsKey($pkg)) { $policy = $policyByPkg[$pkg] }
    if ($null -ne $policy -and $policy.tier -eq 'MULTI') { continue }
    $findings.Add([pscustomobject]@{ kind='VERSION_DRIFT'; severity='WARN'; env='(cross-env)'; pkg=$pkg
        detail=('跨環境 ' + $spread[$pkg].Keys.Count + ' 個版本：' + (($spread[$pkg].Keys | Sort-Object) -join ', '))
        action='收斂為單一版本，或列入多版本白名單' })
}
$failCount = @($findings | Where-Object { $_.severity -eq 'FAIL' }).Count
$warnCount = @($findings | Where-Object { $_.severity -eq 'WARN' }).Count
Write-Stage -Message ('衝突：FAIL ' + $failCount + '，WARN ' + $warnCount) -Level $(if ($failCount) { 'FAIL' } elseif ($warnCount) { 'WARN' } else { 'OK' })

# ------------------------------------------------------------
# 4. 鏡像交互檢查
# ------------------------------------------------------------
$Mirrors = @(
    [pscustomobject]@{ name='Tsinghua'; index='https://pypi.tuna.tsinghua.edu.cn/simple'; json='https://pypi.tuna.tsinghua.edu.cn/pypi/{0}/json' }
    [pscustomobject]@{ name='Aliyun';   index='https://mirrors.aliyun.com/pypi/simple';   json='' }
    [pscustomobject]@{ name='PyPI';     index='https://pypi.org/simple';                  json='https://pypi.org/pypi/{0}/json' }
)
$mirrorRows = [System.Collections.Generic.List[object]]::new()
$crossRows = [System.Collections.Generic.List[object]]::new()
$preferredIndex = 'https://pypi.org/simple'
if ($SkipMirrorProbe) {
    Write-Stage -Message '鏡像探測略過（-SkipMirrorProbe）' -Level 'WARN'
} else {
    Write-Stage -Message '鏡像可達性與延遲探測'
    foreach ($mirror in $Mirrors) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $state = 'UNREACHABLE'
        try {
            $null = Invoke-WebRequest -Uri $mirror.index -Method Head -TimeoutSec 8 -ErrorAction Stop
            $state = 'OK'
        } catch { $state = 'UNREACHABLE' }
        $sw.Stop()
        $mirrorRows.Add([pscustomobject]@{ name=$mirror.name; state=$state; ms=[int]$sw.ElapsedMilliseconds; index=$mirror.index })
    }
    $reachable = @($mirrorRows | Where-Object { $_.state -eq 'OK' } | Sort-Object -Property @{ e='ms'; desc=$false })
    if ($reachable.Count -gt 0) {
        $preferredIndex = $reachable[0].index
        Write-Stage -Message ('最快鏡像：' + $reachable[0].name + '（' + $reachable[0].ms + 'ms）') -Level 'OK'
    } else {
        Write-Stage -Message '所有鏡像都連不上，計畫標為離線模式' -Level 'FAIL'
    }

    # 交互檢查：同一套件在兩個以上鏡像的最新版是否一致
    Write-Stage -Message '鏡像交互檢查（同套件跨鏡像版本比對）'
    foreach ($row in $ToolPolicy) {
        $seen = @{}
        foreach ($mirror in $Mirrors) {
            if (-not $mirror.json) { continue }
            $probe = @($mirrorRows | Where-Object { $_.name -eq $mirror.name -and $_.state -eq 'OK' })
            if ($probe.Count -eq 0) { continue }
            try {
                $uri = [string]::Format($mirror.json, $row.pkg)
                $resp = Invoke-RestMethod -Uri $uri -TimeoutSec 10 -ErrorAction Stop
                $seen[$mirror.name] = [string]$resp.info.version
            } catch { }
        }
        if ($seen.Keys.Count -eq 0) { continue }
        $versions = @($seen.Values | Sort-Object -Unique)
        $crossRows.Add([pscustomobject]@{
            pkg = $row.pkg
            agreement = $(if ($versions.Count -le 1) { 'AGREE' } else { 'DISAGREE' })
            detail = (($seen.Keys | Sort-Object | ForEach-Object { $_ + '=' + $seen[$_] }) -join ', ')
        })
    }
    $disagree = @($crossRows | Where-Object { $_.agreement -eq 'DISAGREE' })
    Write-Stage -Message ('交互檢查 ' + $crossRows.Count + ' 個套件，鏡像版本不一致 ' + $disagree.Count + ' 個') `
        -Level $(if ($disagree.Count) { 'WARN' } else { 'OK' })
}

# ------------------------------------------------------------
# 5. 安裝計畫（依 LKGC + 政策）
# ------------------------------------------------------------
Write-Stage -Message '擬定安裝計畫'
$targets = @{}
foreach ($row in $ToolPolicy) {
    if ($row.tier -eq 'MULTI') { continue }
    if (-not $targets.ContainsKey($row.home)) { $targets[$row.home] = [System.Collections.Generic.List[object]]::new() }
    $targets[$row.home].Add($row)
}
$planRows = [System.Collections.Generic.List[object]]::new()
foreach ($envName in ($targets.Keys | Sort-Object)) {
    $existing = @($managed | Where-Object { $_.name -eq $envName })
    $exists = $existing.Count -gt 0
    $baseline = $null
    if ($lkgc.ContainsKey($envName)) { $baseline = $lkgc[$envName] }
    foreach ($row in $targets[$envName]) {
        $state = 'INSTALL'
        $current = ''
        if ($exists -and $existing[0].packages.ContainsKey($row.pkg)) {
            $current = $existing[0].packages[$row.pkg]
            $state = 'PRESENT'
        }
        $baseVersion = ''
        if ($null -ne $baseline -and $baseline.packages.ContainsKey($row.pkg)) {
            $baseVersion = $baseline.packages[$row.pkg]
            if ($state -eq 'PRESENT' -and $current -ne $baseVersion) { $state = 'DRIFT_FROM_LKGC' }
            if ($state -eq 'INSTALL') { $state = 'RESTORE_FROM_LKGC' }
        }
        $spec = $row.pkg
        if ($baseVersion) { $spec = $row.pkg + '==' + $baseVersion }
        elseif ($row.pin) { $spec = $row.pkg + $row.pin }
        $planRows.Add([pscustomobject]@{
            env = $envName; env_exists = $exists; pkg = $row.pkg; cat = $row.cat
            tier = $row.tier; state = $state; current = $current
            lkgc = $baseVersion; spec = $spec; note = $row.note
        })
    }
}
# 巢狀 Where-Object 裡的 $_ 會被內層改寫，外層的 $_.pkg 就找不到了。
# 先把外層值抓進具名變數再用。
$multiRows = [System.Collections.Generic.List[object]]::new()
foreach ($policy in @($ToolPolicy | Where-Object { $_.tier -eq 'MULTI' })) {
    $pkgName = $policy.pkg
    $owners = [System.Collections.Generic.List[string]]::new()
    foreach ($venv in $managed) {
        if ($venv.packages.ContainsKey($pkgName)) {
            $owners.Add($venv.name + '=' + $venv.packages[$pkgName])
        }
    }
    $multiRows.Add([pscustomobject]@{
        pkg = $pkgName; cat = $policy.cat; note = $policy.note
        present = (($owners) -join ', ') })
}
Write-Stage -Message ('計畫：' + $targets.Keys.Count + ' 個環境，' + $planRows.Count + ' 個套件動作') -Level 'OK'

# ------------------------------------------------------------
# 6. uv 解析預演（只解析不安裝）
# ------------------------------------------------------------
$uvPath = $UvExe
if (-not $uvPath) {
    $found = Get-Command 'uv' -ErrorAction SilentlyContinue
    if ($null -ne $found) { $uvPath = $found.Source }
}
$resolveRows = [System.Collections.Generic.List[object]]::new()
if (-not $uvPath) {
    Write-Stage -Message 'PATH 上找不到 uv，跳過解析預演（計畫仍可產出，但未經解析驗證）' -Level 'WARN'
} elseif ($SkipResolve) {
    Write-Stage -Message '解析預演略過（-SkipResolve）' -Level 'WARN'
} else {
    Write-Stage -Message ('uv 解析預演：' + $uvPath)
    foreach ($envName in ($targets.Keys | Sort-Object)) {
        $specs = @($planRows | Where-Object { $_.env -eq $envName } | ForEach-Object { $_.spec })
        if ($specs.Count -eq 0) { continue }
        $reqFile = Join-Path $WorkRoot ('plans\req_' + $envName + '_' + $Script:Stamp + '.txt')
        Write-Utf8NoBom -TargetPath $reqFile -Text (($specs -join "`n") + "`n")
        $outFile = Join-Path $WorkRoot ('plans\lock_' + $envName + '_' + $Script:Stamp + '.txt')
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $uvPath
        $psi.Arguments = ('pip compile "' + $reqFile + '" --index-url "' + $preferredIndex + '" -o "' + $outFile + '"')
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        try {
            $proc = [System.Diagnostics.Process]::Start($psi)
            $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
            $stderrTask = $proc.StandardError.ReadToEndAsync()
            if (-not $proc.WaitForExit(180000)) { $proc.Kill($true) }
            $combined = ($stdoutTask.Result + "`n" + $stderrTask.Result).Trim()
            $verdict = $(if ($proc.ExitCode -eq 0) { 'RESOLVED' } else { 'UNRESOLVABLE' })
            $resolveRows.Add([pscustomobject]@{ env=$envName; verdict=$verdict; exit=$proc.ExitCode
                detail=(($combined -split "`n" | Select-Object -Last 4) -join ' / '); lock=$outFile })
            Write-Stage -Message ('  ' + $envName + ' -> ' + $verdict) -Level $(if ($verdict -eq 'RESOLVED') { 'OK' } else { 'FAIL' })
        } catch {
            $resolveRows.Add([pscustomobject]@{ env=$envName; verdict='PROBE_FAIL'; exit=-1; detail=$_.Exception.Message; lock='' })
        }
    }
}
$unresolvable = @($resolveRows | Where-Object { $_.verdict -eq 'UNRESOLVABLE' })

# ------------------------------------------------------------
# 7. 核准
# ------------------------------------------------------------
$planText = (($planRows | ForEach-Object { $_.env + '>' + $_.spec }) | Sort-Object) -join "`n"
$digest = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::HashData(
        [System.Text.Encoding]::UTF8.GetBytes($planText))).Replace('-', '').Substring(0, 12).ToLowerInvariant()
$expected = '==VIA-PROVISION==' + $Script:Stamp + '-' + $digest
$tokenDigest = ''
$m = [regex]::Match($Token, '^==VIA-PROVISION==\d{8}_\d{6}-([0-9a-f]{12})$')
if ($m.Success) { $tokenDigest = $m.Groups[1].Value }
$approved = ($tokenDigest -eq $digest) -and $Commit -and $digest

if ($Interactive -and -not $approved) {
    Write-Host ''
    Write-Host ('  即將對 ' + $targets.Keys.Count + ' 個環境執行 ' + $planRows.Count + ' 個套件動作。') -ForegroundColor Yellow
    if ($unresolvable.Count -gt 0) {
        Write-Host ('  警告：' + $unresolvable.Count + ' 個環境的相依無法解析，建議先處理。') -ForegroundColor Red
    }
    $answer = Read-Host '  確認執行？(y/N)'
    if ($answer -match '^(y|Y)') { $approved = $true }
}

# ------------------------------------------------------------
# 8. 執行
# ------------------------------------------------------------
$executed = 0
$skipped = 0
$results = [System.Collections.Generic.List[object]]::new()
if ($approved) {
    if ($unresolvable.Count -gt 0) {
        Write-Stage -Message ('有 ' + $unresolvable.Count + ' 個環境相依無法解析，這些環境不執行') -Level 'FAIL'
    }
    if (-not $uvPath) {
        Write-Stage -Message '沒有 uv，無法執行建置' -Level 'FAIL'
    } else {
        foreach ($envName in ($targets.Keys | Sort-Object)) {
            if (@($unresolvable | Where-Object { $_.env -eq $envName }).Count -gt 0) { $skipped++; continue }
            $envPath = Join-Path $EnvRoot $envName
            $pyTag = '3.12'
            foreach ($row in $targets[$envName]) {
                if ($PythonCeiling.Contains($row.pkg)) { $pyTag = $PythonCeiling[$row.pkg] }
            }
            $steps = @()
            if (-not (Test-Path -LiteralPath $envPath)) {
                $steps += ('venv "' + $envPath + '" --python ' + $pyTag)
            }
            $lock = @($resolveRows | Where-Object { $_.env -eq $envName -and $_.lock })
            $reqArg = $(if ($lock.Count -gt 0) { '"' + $lock[0].lock + '"' }
                        else { (@($planRows | Where-Object { $_.env -eq $envName } | ForEach-Object { '"' + $_.spec + '"' }) -join ' ') })
            $steps += ('pip install --python "' + (Join-Path $envPath 'Scripts\python.exe') + '" --index-url "' + $preferredIndex + '" ' +
                       $(if ($lock.Count -gt 0) { '-r ' + $reqArg } else { $reqArg }))
            foreach ($step in $steps) {
                $psi = [System.Diagnostics.ProcessStartInfo]::new()
                $psi.FileName = $uvPath
                $psi.Arguments = $step
                $psi.UseShellExecute = $false
                $psi.RedirectStandardOutput = $false
                $psi.RedirectStandardError = $false
                $psi.CreateNoWindow = $true
                Write-Stage -Message ('  uv ' + $step)
                try {
                    $proc = [System.Diagnostics.Process]::Start($psi)
                    $proc.WaitForExit()
                    $ok = ($proc.ExitCode -eq 0)
                    $results.Add([pscustomobject]@{ env=$envName; step=$step; exit=$proc.ExitCode; ok=$ok })
                    if ($ok) { $executed++ } else { Write-Stage -Message ('  失敗，退出碼 ' + $proc.ExitCode) -Level 'FAIL' }
                } catch {
                    $results.Add([pscustomobject]@{ env=$envName; step=$step; exit=-1; ok=$false })
                    Write-Stage -Message ('  例外：' + $_.Exception.Message) -Level 'FAIL'
                }
            }
        }
    }
} else {
    Write-Stage -Message 'DRY-RUN：未執行任何安裝。需 -Token 加 -Commit，或 -Interactive 回答 y' -Level 'WARN'
}

# ------------------------------------------------------------
# 9. PATH 與啟動捷徑（只產檔，不改系統 PATH）
# ------------------------------------------------------------
$shimDir = Join-Path $WorkRoot 'plans\shims'
if (-not (Test-Path -LiteralPath $shimDir)) { New-Item -Path $shimDir -ItemType Directory -Force | Out-Null }
foreach ($envName in ($targets.Keys | Sort-Object)) {
    $envPath = Join-Path $EnvRoot $envName
    $shim = @(
        '# ' + $envName + ' 啟動捷徑（產生於 ' + $Script:Stamp + '）'
        '# 只在目前工作階段調整 PATH，不寫入系統環境變數'
        '$EnvPath = "' + $envPath + '"'
        '$Scripts = Join-Path $EnvPath "Scripts"'
        'if (-not (Test-Path -LiteralPath $Scripts)) { Write-Host "環境尚未建立：$EnvPath" -ForegroundColor Yellow; return }'
        'if ($env:PATH -notlike ("*" + $Scripts + "*")) { $env:PATH = $Scripts + ";" + $env:PATH }'
        '$env:VIRTUAL_ENV = $EnvPath'
        'Write-Host ("已切換到 ' + $envName + '：" + (& (Join-Path $Scripts "python.exe") --version)) -ForegroundColor Green'
    )
    Write-Utf8NoBom -TargetPath (Join-Path $shimDir ('Use-' + $envName + '.ps1')) -Text (($shim -join "`n") + "`n")
}
Write-Stage -Message ('啟動捷徑已產出到 ' + $shimDir + '（不改系統 PATH）') -Level 'OK'

# ------------------------------------------------------------
# 10. 落地：成敗都寫回歷史，供下一輪擬定計畫
# ------------------------------------------------------------
$verdict = 'GREEN'
if ($warnCount -gt 0 -or $unresolvable.Count -gt 0) { $verdict = 'AMBER' }
if ($failCount -gt 0 -or @($results | Where-Object { -not $_.ok }).Count -gt 0) { $verdict = 'RED' }

$record = [ordered]@{
    ts = (Get-Date).ToString('o'); stamp = $Script:Stamp; engine = 'VIA_EnvProvisioner_v0100'
    mode = $Mode; task = $Task; verdict = $verdict
    envs_scanned = $envs.Count; managed = $managed.Count
    findings_fail = $failCount; findings_warn = $warnCount
    plan_actions = $planRows.Count; unresolvable = $unresolvable.Count
    approved = $approved; executed = $executed; skipped = $skipped
    mirror = $preferredIndex; token = $expected
    failures = @($results | Where-Object { -not $_.ok } | ForEach-Object { $_.env + ': ' + $_.step })
}
$dir = Split-Path -Path $ProvisionLog -Parent
if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
[System.IO.File]::AppendAllText($ProvisionLog, (($record | ConvertTo-Json -Depth 5 -Compress) + "`n"),
    [System.Text.UTF8Encoding]::new($false))

$jsonPath = Join-Path $WorkRoot ('out\provision_' + $Script:Stamp + '.json')
Write-Utf8NoBom -TargetPath $jsonPath -Text (([ordered]@{
    engine='VIA_EnvProvisioner'; version='v0100'; stamp=$Script:Stamp; verdict=$verdict
    env_root=$EnvRoot; mirror=$preferredIndex; approved=$approved; token=$expected
    envs=@($envs | Select-Object name, python, managed, path)
    findings=@($findings); plan=@($planRows); multi_version=@($multiRows)
    mirrors=@($mirrorRows); cross_check=@($crossRows); resolve=@($resolveRows)
    results=@($results)
} | ConvertTo-Json -Depth 7))

function New-Rows {
    param([object[]]$Items, [string[]]$Fields, [string]$StatusField = '')
    $sb = [System.Text.StringBuilder]::new()
    $count = 0
    foreach ($item in $Items) {
        $count++
        $null = $sb.Append('<tr>')
        foreach ($field in $Fields) {
            $value = ''
            if ($item.PSObject.Properties.Name -contains $field) { $value = [string]$item.$field }
            $cls = ''
            if ($StatusField -and $field -eq $StatusField) {
                if ($value -match 'OK|AGREE|RESOLVED|PRESENT|GREEN') { $cls = " class='ok'" }
                elseif ($value -match 'FAIL|UNRESOLVABLE|DISAGREE|UNREACHABLE|RED') { $cls = " class='fail'" }
                elseif ($value -match 'WARN|DRIFT|ISOLATE|MULTI|INSTALL|RESTORE|AMBER') { $cls = " class='warn'" }
            }
            $null = $sb.Append('<td' + $cls + '>' + (ConvertTo-HtmlText -Text $value) + '</td>')
        }
        $null = $sb.Append('</tr>')
    }
    if ($count -eq 0) { $null = $sb.Append("<tr><td colspan='" + $Fields.Count + "' class='muted'>—— 無 ——</td></tr>") }
    return $sb.ToString()
}

$htmlPath = Join-Path $WorkRoot ('out\VIA_Provision_' + $Script:Stamp + '.html')
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Environment Provisioner</title><style>
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
.token{background:#1d1f20;color:#f2f2f3;padding:10px 12px;border-radius:3px;font-family:Consolas,monospace;overflow-wrap:anywhere;margin:8px 0}
code{background:#ececed;padding:1px 5px;border-radius:2px}
</style></head><body>
<div class="seal">佈</div>
<h1>Environment Provisioner</h1>
<p class="lede">$($Script:Stamp) · 判定 $verdict · $(if ($approved) { '已核准，執行 ' + $executed + ' 步' } else { 'DRY-RUN，未安裝任何東西' }) · 鏡像 $(ConvertTo-HtmlText -Text $preferredIndex)</p>
<div class="cards">
  <div class="card"><div class="k">受管環境</div><div class="v">$($managed.Count)</div></div>
  <div class="card"><div class="k">LKGC 基線</div><div class="v">$($lkgc.Keys.Count)</div></div>
  <div class="card"><div class="k">衝突 FAIL</div><div class="v fail">$failCount</div></div>
  <div class="card"><div class="k">衝突 WARN</div><div class="v warn">$warnCount</div></div>
  <div class="card"><div class="k">計畫動作</div><div class="v">$($planRows.Count)</div></div>
  <div class="card"><div class="k">無法解析</div><div class="v fail">$($unresolvable.Count)</div></div>
</div>

<h2>核准權杖</h2>
<div class="token">$(ConvertTo-HtmlText -Text $expected)</div>
<p class="lede"><code>-Token "$(ConvertTo-HtmlText -Text $expected)" -Commit</code>　或用 <code>-Interactive</code> 以 y/n 回答</p>

<h2>衝突與風險分流</h2>
<table><colgroup><col style="width:12%"><col style="width:8%"><col style="width:12%"><col style="width:12%"><col style="width:28%"><col style="width:28%"></colgroup>
<tr><th>種類</th><th>級別</th><th>環境</th><th>套件</th><th>說明</th><th>處置</th></tr>
$(New-Rows -Items @($findings) -Fields @('kind','severity','env','pkg','detail','action') -StatusField 'severity')</table>

<h2>安裝計畫（以 LKGC 為基準）</h2>
<table><colgroup><col style="width:12%"><col style="width:12%"><col style="width:8%"><col style="width:8%"><col style="width:14%"><col style="width:10%"><col style="width:10%"><col style="width:26%"></colgroup>
<tr><th>環境</th><th>套件</th><th>類別</th><th>層級</th><th>狀態</th><th>現況</th><th>LKGC</th><th>安裝規格／備註</th></tr>
$(New-Rows -Items @($planRows) -Fields @('env','pkg','cat','tier','state','current','lkgc','spec') -StatusField 'state')</table>

<h2>多版本並存白名單</h2>
<table><colgroup><col style="width:16%"><col style="width:10%"><col style="width:34%"><col style="width:40%"></colgroup>
<tr><th>套件</th><th>類別</th><th>目前所在環境</th><th>備註</th></tr>
$(New-Rows -Items @($multiRows) -Fields @('pkg','cat','present','note'))</table>

<h2>鏡像可達性</h2>
<table><colgroup><col style="width:14%"><col style="width:12%"><col style="width:10%"><col style="width:64%"></colgroup>
<tr><th>鏡像</th><th>狀態</th><th>ms</th><th>Index</th></tr>
$(New-Rows -Items @($mirrorRows) -Fields @('name','state','ms','index') -StatusField 'state')</table>

<h2>鏡像交互檢查</h2>
<p class="lede">同一套件在不同鏡像回報的最新版本是否一致。不一致代表某個鏡像同步落後，安裝結果會依鏡像而異。</p>
<table><colgroup><col style="width:18%"><col style="width:14%"><col style="width:68%"></colgroup>
<tr><th>套件</th><th>一致性</th><th>各鏡像版本</th></tr>
$(New-Rows -Items @($crossRows) -Fields @('pkg','agreement','detail') -StatusField 'agreement')</table>

<h2>uv 解析預演</h2>
<p class="lede">只解析不安裝。解不出來的環境不會進入執行階段。</p>
<table><colgroup><col style="width:16%"><col style="width:14%"><col style="width:8%"><col style="width:62%"></colgroup>
<tr><th>環境</th><th>結果</th><th>Exit</th><th>輸出</th></tr>
$(New-Rows -Items @($resolveRows) -Fields @('env','verdict','exit','detail') -StatusField 'verdict')</table>

<h2>執行日誌</h2>
<pre style="background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:30vh;overflow:auto">$(ConvertTo-HtmlText -Text ($Script:Log -join "`n"))</pre>
</body></html>
"@
Write-Utf8NoBom -TargetPath $htmlPath -Text $html

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   VIA ENVIRONMENT PROVISIONER  ->  ' + $verdict)
Write-Host ('   受管 ' + $managed.Count + '｜衝突 FAIL ' + $failCount + ' WARN ' + $warnCount +
            '｜計畫 ' + $planRows.Count + '｜無法解析 ' + $unresolvable.Count)
if (-not $approved) {
    Write-Host '   DRY-RUN。核准方式擇一：' -ForegroundColor Yellow
    Write-Host ('     -Token "' + $expected + '" -Commit') -ForegroundColor Yellow
    Write-Host '     -Interactive   （改用 y/n 問答）' -ForegroundColor Yellow
}
Write-Host ('   報告：' + $htmlPath) -ForegroundColor DarkCyan
Write-Host ('   歷史：' + $ProvisionLog) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray

if (-not $NoBrowser) {
    try { Start-Process -FilePath $htmlPath | Out-Null } catch { }
}
