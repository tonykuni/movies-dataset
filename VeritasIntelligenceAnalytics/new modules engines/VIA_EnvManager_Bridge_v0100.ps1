#requires -Version 7.0
param(
    [string]$EnvManager  = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\supportive modules\VIA_EnvManager.py',
    [string]$PythonExe   = '',
    [string]$WorkRoot    = 'C:\VeritasIntelligenceAnalytics\CGE\EnvBridge',
    [string[]]$Package   = @(),
    [string]$PackageFile = '',
    [string]$PreferredEnv = '',
    [switch]$AllowBase,
    [string]$Token       = '',
    [switch]$Commit,
    [switch]$SkipSelfTest,
    [switch]$NoBrowser
)

# ============================================================
# VIA EnvManager Bridge v0100
#
# **決策權在 VIA_EnvManager.py，不在這支。**
#
# 它本身已經有完整的安裝決策機關：風險分級（HIGH/MEDIUM/LOW）、
# base 對中高風險封鎖、用途路由環境、via_core 白名單、
# plan-install / execute-install / conflicts / rebuild-candidates。
# 本橋接只做四件它沒做的事：
#
#   1. 批次   一次把整份工具清單送進 plan-install，彙整成一張表
#   2. 閘門   先跑它自己的 selftest，不過就不往下走
#   3. 核准   權杖綁計畫內容雜湊，核准後才逐一 execute-install
#   4. 留痕   成敗都寫成 lesson ledger 收得到的格式
#
# 任何被 EnvManager 判 blocked 的套件，本橋接**不會**繞過它。
# 它說不行就是不行，理由原樣呈現。
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>" -PackageFile tools.txt
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

function Invoke-EnvManager {
    param([string[]]$Arguments, [int]$TimeoutMs = 300000)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Script:PyExe
    $psi.ArgumentList.Add($EnvManager)
    foreach ($item in $Arguments) { $psi.ArgumentList.Add($item) }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    # 非同步同時讀 stdout 與 stderr；循序 ReadToEnd 在輸出量大時會死鎖
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit($TimeoutMs)) {
        try { $proc.Kill($true) } catch { }
        return [pscustomobject]@{ ok = $false; exit = -1; json = $null; raw = 'TIMEOUT' }
    }
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $parsed = $null
    try { $parsed = $stdout | ConvertFrom-Json } catch { $parsed = $null }
    return [pscustomobject]@{
        ok = ($proc.ExitCode -eq 0); exit = $proc.ExitCode
        json = $parsed; raw = ($stdout + "`n" + $stderr).Trim()
    }
}

foreach ($sub in @('out', 'logs')) {
    $dir = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
}

Write-Host ''
Write-Host '  VIA ENVMANAGER BRIDGE v0100' -ForegroundColor Cyan
Write-Host '  決策權在 VIA_EnvManager.py，本橋接只負責批次、閘門、核准與留痕' -ForegroundColor DarkGray
Write-Host ''

if (-not (Test-Path -LiteralPath $EnvManager)) {
    Write-Stage -Message ('找不到 VIA_EnvManager.py：' + $EnvManager) -Level 'FAIL'
    return
}
$Script:PyExe = $PythonExe
if (-not $Script:PyExe) {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $found) { $Script:PyExe = $found.Source; break }
    }
}
if (-not $Script:PyExe) {
    Write-Stage -Message '找不到 Python 執行期' -Level 'FAIL'
    return
}
Write-Stage -Message ('EnvManager: ' + $EnvManager) -Level 'OK'
Write-Stage -Message ('Python: ' + $Script:PyExe) -Level 'OK'

# ------------------------------------------------------------
# 1. 先跑它自己的 selftest
# ------------------------------------------------------------
$selftest = $null
if ($SkipSelfTest) {
    Write-Stage -Message 'selftest 略過（-SkipSelfTest）' -Level 'WARN'
} else {
    Write-Stage -Message '執行 EnvManager 內建 selftest'
    $selftest = Invoke-EnvManager -Arguments @('selftest')
    if ($null -eq $selftest.json) {
        Write-Stage -Message ('selftest 沒有回傳可解析的 JSON：' + ($selftest.raw -split "`n" | Select-Object -First 2)) -Level 'FAIL'
        return
    }
    $passed = @($selftest.json.passed).Count
    $failed = @($selftest.json.failed).Count
    Write-Stage -Message ('selftest：通過 ' + $passed + '，失敗 ' + $failed) -Level $(if ($failed) { 'FAIL' } else { 'OK' })
    if ($failed -gt 0) {
        Write-Stage -Message 'selftest 未全過，不繼續（不在有問題的決策機關上做安裝）' -Level 'FAIL'
        return
    }
}

# ------------------------------------------------------------
# 2. 現況：scan / conflicts / rebuild-candidates
# ------------------------------------------------------------
Write-Stage -Message '取得環境現況'
$scan = Invoke-EnvManager -Arguments @('scan')
$envCount = 0
if ($null -ne $scan.json -and $scan.json.PSObject.Properties.Name -contains 'env_count') {
    $envCount = [int]$scan.json.env_count
}
Write-Stage -Message ('scan：環境 ' + $envCount + ' 個') -Level $(if ($envCount -gt 0) { 'OK' } else { 'WARN' })
if ($envCount -eq 0) {
    Write-Stage -Message 'EnvManager 找不到任何受管環境，所有安裝決策都會被判 NO_HEALTHY_MANAGED_ENV_AVAILABLE' -Level 'WARN'
}

$conflicts = Invoke-EnvManager -Arguments @('conflicts')
$conflictCount = 0
if ($null -ne $conflicts.json) {
    $rows = @($conflicts.json)
    if ($conflicts.json.PSObject.Properties.Name -contains 'conflicts') { $rows = @($conflicts.json.conflicts) }
    $conflictCount = $rows.Count
}
Write-Stage -Message ('conflicts：' + $conflictCount + ' 筆') -Level $(if ($conflictCount) { 'WARN' } else { 'OK' })

$rebuild = Invoke-EnvManager -Arguments @('rebuild-candidates')
$rebuildRows = @()
if ($null -ne $rebuild.json) {
    $rebuildRows = @($rebuild.json)
    if ($rebuild.json.PSObject.Properties.Name -contains 'candidates') { $rebuildRows = @($rebuild.json.candidates) }
}
Write-Stage -Message ('rebuild-candidates：' + $rebuildRows.Count + ' 個環境建議重建') -Level $(if ($rebuildRows.Count) { 'WARN' } else { 'OK' })

# ------------------------------------------------------------
# 3. 批次送進 plan-install
# ------------------------------------------------------------
$packages = [System.Collections.Generic.List[string]]::new()
foreach ($item in $Package) {
    foreach ($piece in ($item -split '[,;]')) {
        $trimmed = $piece.Trim()
        if ($trimmed) { $packages.Add($trimmed) }
    }
}
if ($PackageFile -and (Test-Path -LiteralPath $PackageFile)) {
    foreach ($line in (Get-Content -LiteralPath $PackageFile -ErrorAction SilentlyContinue)) {
        $trimmed = ($line -split '#')[0].Trim()
        if ($trimmed) { $packages.Add($trimmed) }
    }
}
if ($packages.Count -eq 0) {
    Write-Stage -Message '沒有指定任何套件（-Package 或 -PackageFile），只做現況盤點' -Level 'WARN'
}

$decisions = [System.Collections.Generic.List[object]]::new()
foreach ($spec in $packages) {
    $name = $spec
    $version = ''
    if ($spec -match '^(?<n>[^=<>~!]+)(?<op>==|>=|<=|~=)(?<v>.+)$') {
        $name = $matches['n'].Trim()
        $version = $matches['v'].Trim()
    }
    $args = @('plan-install', $name, $version, $PreferredEnv)
    $result = Invoke-EnvManager -Arguments $args
    if ($null -eq $result.json) {
        $decisions.Add([pscustomobject]@{
            package = $name; version = $version; risk = ''; approved = $false
            target = ''; strategy = ''; blocked = 'NO_JSON_RESPONSE'
            reason = (($result.raw -split "`n" | Select-Object -First 1)); commands = 0 })
        continue
    }
    $decision = $result.json.decision
    $envDecision = $result.json.env_decision
    $cmdCount = 0
    foreach ($field in @('powershell_commands', 'python_commands', 'executable_commands')) {
        if ($decision.PSObject.Properties.Name -contains $field) {
            $cmdCount += @($decision.$field).Count
        }
    }
    $reason = ''
    if ($null -ne $envDecision -and $envDecision.PSObject.Properties.Name -contains 'reason') {
        $reason = [string]$envDecision.reason
    } elseif ($null -ne $envDecision -and $envDecision.PSObject.Properties.Name -contains 'error') {
        $reason = [string]$envDecision.error
    }
    $decisions.Add([pscustomobject]@{
        package = [string]$decision.package_name
        version = $version
        risk = [string]$decision.risk_level
        approved = [bool]$decision.approved
        target = [string]$decision.target_env
        strategy = [string]$decision.strategy
        blocked = [string]$decision.blocked_reason
        reason = $reason
        commands = $cmdCount
    })
}
$approvedRows = @($decisions | Where-Object { $_.approved })
$blockedRows = @($decisions | Where-Object { -not $_.approved })
if ($decisions.Count -gt 0) {
    Write-Stage -Message ('plan-install：核准 ' + $approvedRows.Count + '，封鎖 ' + $blockedRows.Count) `
        -Level $(if ($blockedRows.Count) { 'WARN' } else { 'OK' })
    foreach ($row in $decisions) {
        $level = $(if ($row.approved) { 'OK' } else { 'WARN' })
        Write-Stage -Message ('  ' + $row.package.PadRight(18) + $row.risk.PadRight(7) +
                              $(if ($row.approved) { '-> ' + $row.target } else { '封鎖：' + $row.blocked })) -Level $level
    }
}

# ------------------------------------------------------------
# 4. 核准權杖
# ------------------------------------------------------------
$planText = (($approvedRows | ForEach-Object { $_.package + '@' + $_.target }) | Sort-Object) -join "`n"
$digest = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::HashData(
        [System.Text.Encoding]::UTF8.GetBytes($planText))).Replace('-', '').Substring(0, 12).ToLowerInvariant()
$expected = '==VIA-ENVIMPORT==' + $Script:Stamp + '-' + $digest
$tokenDigest = ''
$m = [regex]::Match($Token, '^==VIA-ENVIMPORT==\d{8}_\d{6}-([0-9a-f]{12})$')
if ($m.Success) { $tokenDigest = $m.Groups[1].Value }
$approved = ($tokenDigest -eq $digest) -and $Commit -and $approvedRows.Count -gt 0

# ------------------------------------------------------------
# 5. 執行（交給 EnvManager 自己的 execute-install）
# ------------------------------------------------------------
$results = [System.Collections.Generic.List[object]]::new()
if ($approved) {
    Write-Stage -Message '已核准，逐一交給 EnvManager execute-install' -Level 'OK'
    foreach ($row in $approvedRows) {
        $result = Invoke-EnvManager -Arguments @('execute-install', $row.package, $row.version, $PreferredEnv) -TimeoutMs 900000
        $ok = $false
        $detail = ''
        if ($null -ne $result.json) {
            if ($result.json.PSObject.Properties.Name -contains 'ok') { $ok = [bool]$result.json.ok }
            $detail = ($result.json | ConvertTo-Json -Depth 3 -Compress)
            if ($detail.Length -gt 300) { $detail = $detail.Substring(0, 300) }
        } else {
            $detail = (($result.raw -split "`n" | Select-Object -Last 3) -join ' / ')
        }
        $results.Add([pscustomobject]@{ package = $row.package; target = $row.target; ok = $ok; detail = $detail })
        Write-Stage -Message ('  ' + $row.package + ' -> ' + $(if ($ok) { '成功' } else { '失敗' })) `
            -Level $(if ($ok) { 'OK' } else { 'FAIL' })
    }
} elseif ($approvedRows.Count -gt 0) {
    Write-Stage -Message 'DRY-RUN：未執行任何安裝' -Level 'WARN'
}

# ------------------------------------------------------------
# 6. 留痕（lesson ledger 收得到的格式）
# ------------------------------------------------------------
$failed = @($results | Where-Object { -not $_.ok })
$verdict = 'GREEN'
if ($blockedRows.Count -gt 0 -or $conflictCount -gt 0 -or $rebuildRows.Count -gt 0) { $verdict = 'AMBER' }
if ($failed.Count -gt 0 -or $envCount -eq 0) { $verdict = 'RED' }

$historyPath = Join-Path $WorkRoot 'logs\env_import_history.jsonl'
$record = [ordered]@{
    ts = (Get-Date).ToString('o'); stamp = $Script:Stamp
    engine = 'VIA_EnvManager_Bridge_v0100'; outcome = $verdict
    envmanager = $EnvManager; env_count = $envCount
    conflicts = $conflictCount; rebuild_candidates = $rebuildRows.Count
    requested = $decisions.Count; approved = $approvedRows.Count; blocked = $blockedRows.Count
    executed = @($results | Where-Object { $_.ok }).Count
    failures = @($failed | ForEach-Object { $_.package + ': ' + $_.detail })
    token = $expected
}
$dir = Split-Path -Path $historyPath -Parent
if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
[System.IO.File]::AppendAllText($historyPath, (($record | ConvertTo-Json -Depth 5 -Compress) + "`n"),
    [System.Text.UTF8Encoding]::new($false))

$jsonPath = Join-Path $WorkRoot ('out\env_import_' + $Script:Stamp + '.json')
Write-Utf8NoBom -TargetPath $jsonPath -Text (([ordered]@{
    engine = 'VIA_EnvManager_Bridge'; version = 'v0100'; stamp = $Script:Stamp
    verdict = $verdict; envmanager = $EnvManager
    gates = @(
        [ordered]@{ code = 'B01'; title = 'ENVMANAGER_SELFTEST'
            status = $(if ($SkipSelfTest) { 'WARN' } elseif ($null -ne $selftest -and @($selftest.json.failed).Count -eq 0) { 'PASS' } else { 'FAIL' })
            detail = $(if ($SkipSelfTest) { '略過' } else { '內建自我測試 ' + @($selftest.json.passed).Count + ' 項' }) }
        [ordered]@{ code = 'B02'; title = 'MANAGED_ENV_PRESENT'
            status = $(if ($envCount -gt 0) { 'PASS' } else { 'FAIL' })
            detail = ('受管環境 ' + $envCount + ' 個') }
        [ordered]@{ code = 'B03'; title = 'NO_BASE_VIA_CONFLICT'
            status = $(if ($conflictCount -eq 0) { 'PASS' } else { 'WARN' })
            detail = ('base/via 衝突 ' + $conflictCount + ' 筆') }
        [ordered]@{ code = 'B04'; title = 'ALL_PACKAGES_ROUTED'
            status = $(if ($blockedRows.Count -eq 0) { 'PASS' } else { 'WARN' })
            detail = ('封鎖 ' + $blockedRows.Count + ' 個套件') }
        [ordered]@{ code = 'B05'; title = 'INSTALL_SUCCEEDED'
            status = $(if ($failed.Count -eq 0) { 'PASS' } else { 'FAIL' })
            detail = ('安裝失敗 ' + $failed.Count + ' 個') }
    )
    decisions = @($decisions); results = @($results)
    rebuild_candidates = @($rebuildRows); token = $expected
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
                if ($value -match '^(True|PASS|LOW)$') { $cls = " class='ok'" }
                elseif ($value -match '^(False|FAIL|HIGH)$') { $cls = " class='fail'" }
                elseif ($value -match 'WARN|MEDIUM') { $cls = " class='warn'" }
            }
            $null = $sb.Append('<td' + $cls + '>' + (ConvertTo-HtmlText -Text $value) + '</td>')
        }
        $null = $sb.Append('</tr>')
    }
    if ($count -eq 0) { $null = $sb.Append("<tr><td colspan='" + $Fields.Count + "' class='muted'>—— 無 ——</td></tr>") }
    return $sb.ToString()
}

$htmlPath = Join-Path $WorkRoot ('out\VIA_EnvImport_' + $Script:Stamp + '.html')
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA EnvManager Bridge</title><style>
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
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:28vh;overflow:auto}
</style></head><body>
<div class="seal">導</div>
<h1>EnvManager Bridge</h1>
<p class="lede">$($Script:Stamp) · 判定 $verdict · 決策權在 VIA_EnvManager.py，本橋接不繞過它的任何封鎖</p>
<div class="cards">
  <div class="card"><div class="k">受管環境</div><div class="v">$envCount</div></div>
  <div class="card"><div class="k">base/via 衝突</div><div class="v warn">$conflictCount</div></div>
  <div class="card"><div class="k">建議重建</div><div class="v warn">$($rebuildRows.Count)</div></div>
  <div class="card"><div class="k">請求</div><div class="v">$($decisions.Count)</div></div>
  <div class="card"><div class="k">核准</div><div class="v ok">$($approvedRows.Count)</div></div>
  <div class="card"><div class="k">封鎖</div><div class="v fail">$($blockedRows.Count)</div></div>
</div>

<h2>核准權杖</h2>
<div class="token">$(ConvertTo-HtmlText -Text $expected)</div>
<p class="lede">核准後才會逐一呼叫 EnvManager 的 <code>execute-install</code>。被它封鎖的套件不在此列，本橋接不會代為放行。</p>

<h2>安裝決策（由 VIA_EnvManager.py 裁定）</h2>
<table><colgroup><col style="width:16%"><col style="width:9%"><col style="width:8%"><col style="width:8%"><col style="width:14%"><col style="width:18%"><col style="width:27%"></colgroup>
<tr><th>套件</th><th>版本</th><th>風險</th><th>核准</th><th>目標環境</th><th>封鎖理由</th><th>路由理由</th></tr>
$(New-Rows -Items @($decisions) -Fields @('package','version','risk','approved','target','blocked','reason') -StatusField 'risk')</table>

<h2>執行結果</h2>
<table><colgroup><col style="width:18%"><col style="width:16%"><col style="width:8%"><col style="width:58%"></colgroup>
<tr><th>套件</th><th>環境</th><th>成功</th><th>細節</th></tr>
$(New-Rows -Items @($results) -Fields @('package','target','ok','detail') -StatusField 'ok')</table>

<h2>執行日誌</h2>
<pre>$(ConvertTo-HtmlText -Text ($Script:Log -join "`n"))</pre>
</body></html>
"@
Write-Utf8NoBom -TargetPath $htmlPath -Text $html

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   VIA ENVMANAGER BRIDGE  ->  ' + $verdict)
Write-Host ('   環境 ' + $envCount + '｜衝突 ' + $conflictCount + '｜請求 ' + $decisions.Count +
            '｜核准 ' + $approvedRows.Count + '｜封鎖 ' + $blockedRows.Count)
if (-not $approved -and $approvedRows.Count -gt 0) {
    Write-Host '   DRY-RUN。要執行：' -ForegroundColor Yellow
    Write-Host ('     -Token "' + $expected + '" -Commit') -ForegroundColor Yellow
}
Write-Host ('   報告：' + $htmlPath) -ForegroundColor DarkCyan
Write-Host ('   歷史：' + $historyPath) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray

if (-not $NoBrowser) {
    try { Start-Process -FilePath $htmlPath | Out-Null } catch { }
}
