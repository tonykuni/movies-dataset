#requires -Version 7.0
param(
    [string[]]$Root = @('C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics'),
    [string[]]$Extension = @('.py', '.ps1', '.psm1', '.json', '.md', '.csv', '.html'),
    [string]$WorkRoot = 'C:\VeritasIntelligenceAnalytics\CGE\Consolidate',
    [string]$Token = '',
    [switch]$Commit,
    [switch]$IncludeDiverged,
    [switch]$NoBrowser
)

# ============================================================
# VIA Same-Name Consolidator v0100
#
# 你的規則：同名稱以「版本新的、容量大的」為主。
# 實作的排序是 版本記號 > 修改時間 > 檔案大小 > 路徑，主檔留原地。
#
# 但在搬任何東西之前，先分兩類 —— 這是上一次出事的教訓：
#
#   IDENTICAL  內容雜湊完全相同 -> 真重複，收走副本沒有損失
#   DIVERGED   同名但內容不同   -> **這不是重複，是分歧**
#
# 同名不等於同一個檔案。VRN\20260804\ 與 VRN\20260812\ 底下的同名檔
# 是兩個時間點的快照，內容不同就代表中間有改動；把舊的收走等於丟掉歷史。
# 所以 DIVERGED 預設只報告不處理，而且會列出「舊檔有、新檔沒有」的函式與
# 類別名稱 —— 如果新檔少了東西，那不是升級，是回退。
#
# 動檔案的條件比上一版更嚴：dry-run 預設 **加上** 核准權杖。
# 只有 -Token 對得上本次計畫的雜湊、且明示 -Commit，才會真的搬。
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>"
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$SkipDirs = @('_superseded', '_legacy', '_to_delete', '_backup', '_recover',
              '_versionguard', '_governance', '.git', '__pycache__', '.venv',
              'node_modules', 'site-packages', 'out', 'logs')

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

function Get-VersionRank {
    param([string]$Name)
    $m = [regex]::Match($Name, '[_-]v(\d{2,4})([A-Za-z]?)(?=$|[_.-])', 'IgnoreCase')
    if (-not $m.Success) { return 0 }
    $suffix = 0
    if ($m.Groups[2].Value) { $suffix = [int][char]($m.Groups[2].Value.ToUpperInvariant()[0]) - 64 }
    return ([int]$m.Groups[1].Value * 100) + $suffix
}

function Get-FileHash32 {
    param([string]$Path, [long]$Length)
    if ($Length -gt 67108864) { return 'SKIP_LARGE' }
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $stream = [System.IO.File]::OpenRead($Path)
        try { $bytes = $sha.ComputeHash($stream) } finally { $stream.Dispose(); $sha.Dispose() }
        return ([System.BitConverter]::ToString($bytes).Replace('-', '').Substring(0, 32).ToLowerInvariant())
    } catch { return 'HASH_FAIL' }
}

function Get-Symbols {
    param([string]$Path)
    $ext = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    $names = [System.Collections.Generic.List[string]]::new()
    try {
        if ($ext -eq '.ps1' -or $ext -eq '.psm1') {
            $tokens = $null
            $errs = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errs)
            foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
                $names.Add('fn:' + $fn.Name)
            }
        } elseif ($ext -eq '.py' -or $ext -eq '.pyw') {
            # 沒有 python 也要能跑，所以用行首正則；證據等級標 M
            foreach ($line in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
                $m = [regex]::Match($line, '^\s*(def|class)\s+([A-Za-z_]\w*)')
                if ($m.Success) { $names.Add($m.Groups[1].Value + ':' + $m.Groups[2].Value) }
            }
        }
    } catch { }
    # 單一元素的陣列從函式 return 時會被展開成純量字串，
    # StrictMode 下再取 .Count 就會炸。用逗號運算子強制保持陣列。
    return , @($names | Sort-Object -Unique)
}

foreach ($sub in @('out', 'plans')) {
    $dir = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
}

Write-Host ''
Write-Host '  VIA SAME-NAME CONSOLIDATOR v0100' -ForegroundColor Cyan
Write-Host '  主檔選取：版本記號 > 修改時間 > 檔案大小 > 路徑' -ForegroundColor DarkGray
Write-Host ''

# ------------------------------------------------------------
# 1. 收集同名檔
# ------------------------------------------------------------

$enumOptions = [System.IO.EnumerationOptions]::new()
$enumOptions.RecurseSubdirectories = $true
$enumOptions.IgnoreInaccessible = $true
$enumOptions.AttributesToSkip = [System.IO.FileAttributes]::ReparsePoint

$extSet = @{}
foreach ($ext in $Extension) { $extSet[$ext.ToLowerInvariant()] = $true }
$skipSet = @{}
foreach ($name in $SkipDirs) { $skipSet[$name.ToLowerInvariant()] = $true }

$byName = @{}
$scanned = 0
foreach ($path in $Root) {
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host ('  略過不存在：' + $path) -ForegroundColor DarkYellow
        continue
    }
    $base = (Resolve-Path -LiteralPath $path).Path
    Write-Host ('  掃描 ' + $base) -ForegroundColor DarkGray
    foreach ($file in [System.IO.Directory]::EnumerateFiles($base, '*', $enumOptions)) {
        $ext = [System.IO.Path]::GetExtension($file).ToLowerInvariant()
        if (-not $extSet.ContainsKey($ext)) { continue }
        $blocked = $false
        foreach ($segment in $file.Substring($base.Length).Split([char[]]@('\', '/'))) {
            if ($skipSet.ContainsKey($segment.ToLowerInvariant())) { $blocked = $true; break }
        }
        if ($blocked) { continue }
        $scanned++
        $info = [System.IO.FileInfo]::new($file)
        $key = $info.Name.ToLowerInvariant()
        if (-not $byName.ContainsKey($key)) { $byName[$key] = [System.Collections.Generic.List[object]]::new() }
        $byName[$key].Add([pscustomobject]@{
            name = $info.Name; path = $info.FullName
            dir = $info.DirectoryName
            size = $info.Length; mtime = $info.LastWriteTime
            rank = (Get-VersionRank -Name $info.Name)
            hash = ''; symbols = @()
        })
    }
}
$dupNames = @($byName.Keys | Where-Object { $byName[$_].Count -gt 1 })
Write-Host ('  掃描 ' + $scanned + ' 個檔案，同名群組 ' + $dupNames.Count + ' 組') -ForegroundColor Green
Write-Host ''

# ------------------------------------------------------------
# 2. 分類：真重複 vs 分歧
# ------------------------------------------------------------

$groups = [System.Collections.Generic.List[object]]::new()
$rows = [System.Collections.Generic.List[object]]::new()
$identicalGroups = 0
$divergedGroups = 0
$reclaim = 0L

foreach ($key in ($byName.Keys | Sort-Object)) {
    $members = @($byName[$key])
    if ($members.Count -lt 2) { continue }
    foreach ($member in $members) {
        $member.hash = Get-FileHash32 -Path $member.path -Length $member.size
        $member.symbols = Get-Symbols -Path $member.path
    }
    # 你的規則：版本新的優先，其次時間新的，再其次容量大的
    $ordered = @($members | Sort-Object -Property @{ e = 'rank'; desc = $true },
                                                  @{ e = 'mtime'; desc = $true },
                                                  @{ e = 'size'; desc = $true },
                                                  @{ e = 'path'; desc = $false })
    $primary = $ordered[0]
    $hashes = @($members | ForEach-Object { $_.hash } | Sort-Object -Unique)
    $identical = ($hashes.Count -eq 1 -and $hashes[0] -notmatch 'SKIP_LARGE|HASH_FAIL')
    $verdict = $(if ($identical) { 'IDENTICAL' } else { 'DIVERGED' })
    if ($identical) { $identicalGroups++ } else { $divergedGroups++ }

    foreach ($member in $ordered) {
        $role = 'SECONDARY'
        $lost = @()
        if ($member.path -eq $primary.path) {
            $role = 'PRIMARY'
        } else {
            if ($identical) { $reclaim += $member.size }
            # 副檔有、主檔沒有的符號 = 合併後會消失的東西
            $lost = @($member.symbols | Where-Object { $primary.symbols -notcontains $_ })
        }
        $rows.Add([pscustomobject]@{
            group = $key; verdict = $verdict; role = $role
            name = $member.name; rank = $member.rank
            size = $member.size; mtime = $member.mtime.ToString('yyyy-MM-dd HH:mm')
            hash = $member.hash.Substring(0, [math]::Min(12, $member.hash.Length))
            symbols = $member.symbols.Count
            lost = ($lost -join ', ')
            lost_count = $lost.Count
            path = $member.path
        })
    }
    $groups.Add([pscustomobject]@{
        key = $key; verdict = $verdict; count = $members.Count
        primary = $primary.path
        secondaries = @($ordered | Where-Object { $_.path -ne $primary.path } | ForEach-Object { $_.path })
        risk = @($rows | Where-Object { $_.group -eq $key -and $_.lost_count -gt 0 }).Count
    })

    $color = $(if ($identical) { 'Green' } else { 'Yellow' })
    Write-Host ('  [' + $verdict + '] ' + $members[0].name + '  ×' + $members.Count) -ForegroundColor $color
    foreach ($member in $ordered) {
        $tag = $(if ($member.path -eq $primary.path) { '主檔' } else { '副本' })
        Write-Host ('     ' + $tag + '  ' + $member.mtime.ToString('yyyy-MM-dd HH:mm') +
                    '  ' + ('{0,9}' -f $member.size) + ' B  ' + $member.path) -ForegroundColor DarkGray
    }
    $risky = @($rows | Where-Object { $_.group -eq $key -and $_.lost_count -gt 0 })
    foreach ($row in $risky) {
        Write-Host ('     ⚠ 副本獨有 ' + $row.lost_count + ' 個符號，合併後會消失：' +
                    ($row.lost.Substring(0, [math]::Min(90, $row.lost.Length)))) -ForegroundColor Red
    }
    Write-Host ''
}

# ------------------------------------------------------------
# 3. 核准權杖
# ------------------------------------------------------------

$actionable = @($groups | Where-Object { $_.verdict -eq 'IDENTICAL' -or $IncludeDiverged })
$planText = ($actionable | ForEach-Object { $_.key + '>' + $_.primary } | Sort-Object) -join "`n"
$digest = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::HashData(
        [System.Text.Encoding]::UTF8.GetBytes($planText))).Replace('-', '').Substring(0, 12).ToLowerInvariant()
$expected = '==VIA-CONSOLIDATE==' + $Script:Stamp + '-' + $digest
# 權杖只驗「計畫內容雜湊」，不驗時間戳 —— 時間戳每次執行都會變，
# 若連它一起比，使用者永遠不可能貼回一個對得上的權杖。
# 語意是「你看過的正是這份計畫」，計畫沒變就仍然有效；計畫一變立刻失效。
$tokenDigest = ''
$m = [regex]::Match($Token, '^==VIA-CONSOLIDATE==\d{8}_\d{6}-([0-9a-f]{12})$')
if ($m.Success) { $tokenDigest = $m.Groups[1].Value }
$approved = ($tokenDigest -eq $digest) -and $Commit -and $digest

# ------------------------------------------------------------
# 4. 執行（唯有核准才動）
# ------------------------------------------------------------

$moved = 0
$held = 0
if ($approved) {
    Write-Host '  已核准，開始收攏副本到 _duplicates\（不刪除）' -ForegroundColor Cyan
    foreach ($group in $actionable) {
        foreach ($secondary in $group.secondaries) {
            $dir = Split-Path -Path $secondary -Parent
            $dest = Join-Path $dir '_duplicates'
            if (-not (Test-Path -LiteralPath $dest)) { New-Item -Path $dest -ItemType Directory -Force | Out-Null }
            $target = Join-Path $dest (Split-Path -Path $secondary -Leaf)
            if (Test-Path -LiteralPath $target) {
                Write-Host ('    [跳過] 目標已存在：' + $target) -ForegroundColor DarkYellow
                $held++
                continue
            }
            Move-Item -LiteralPath $secondary -Destination $target
            Write-Host ('    [收攏] ' + $secondary) -ForegroundColor Green
            $moved++
        }
    }
} else {
    $held = @($actionable | ForEach-Object { $_.secondaries.Count } | Measure-Object -Sum).Sum
    if ($null -eq $held) { $held = 0 }
}

# ------------------------------------------------------------
# 5. 輸出
# ------------------------------------------------------------

$rowsHtml = ''
foreach ($row in ($rows | Sort-Object -Property @{ e = 'verdict'; desc = $true }, @{ e = 'group'; desc = $false }, @{ e = 'role'; desc = $false })) {
    $cls = ''
    if ($row.verdict -eq 'DIVERGED') { $cls = " class='warn'" }
    if ($row.lost_count -gt 0) { $cls = " class='fail'" }
    $rowsHtml += '<tr><td' + $cls + '>' + $row.verdict + '</td><td>' + $row.role + '</td><td>' +
                 (ConvertTo-HtmlText -Text $row.name) + '</td><td>' + $row.mtime + '</td><td>' +
                 $row.size + '</td><td>' + $row.rank + '</td><td>' + $row.hash + '</td><td>' +
                 $row.symbols + '</td><td' + $(if ($row.lost_count) { " class='fail'" } else { '' }) + '>' +
                 (ConvertTo-HtmlText -Text $row.lost) + '</td><td>' +
                 (ConvertTo-HtmlText -Text $row.path) + '</td></tr>'
}
if (-not $rowsHtml) { $rowsHtml = "<tr><td colspan='10' class='muted'>—— 沒有同名檔 ——</td></tr>" }

$htmlPath = Join-Path $WorkRoot ('out\VIA_Consolidate_' + $Script:Stamp + '.html')
$jsonPath = Join-Path $WorkRoot ('out\consolidate_' + $Script:Stamp + '.json')
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Same-Name Consolidator</title><style>
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
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
.token{background:#1d1f20;color:#f2f2f3;padding:10px 12px;border-radius:3px;font-family:Consolas,monospace;overflow-wrap:anywhere;margin:8px 0}
code{background:#ececed;padding:1px 5px;border-radius:2px}
</style></head><body>
<div class="seal">併</div>
<h1>Same-Name Consolidator</h1>
<p class="lede">$($Script:Stamp) · 主檔規則：版本記號 &gt; 修改時間 &gt; 檔案大小 · $(if ($approved) { '已核准，收攏 ' + $moved + ' 個' } else { 'DRY-RUN，尚未搬動任何檔案' })</p>
<div class="cards">
  <div class="card"><div class="k">同名群組</div><div class="v">$($groups.Count)</div></div>
  <div class="card"><div class="k">真重複</div><div class="v ok">$identicalGroups</div></div>
  <div class="card"><div class="k">內容分歧</div><div class="v warn">$divergedGroups</div></div>
  <div class="card"><div class="k">可回收</div><div class="v">$([math]::Round($reclaim/1MB,2)) MB</div></div>
  <div class="card"><div class="k">會消失的符號</div><div class="v fail">$(@($rows | Where-Object { $_.lost_count -gt 0 }).Count)</div></div>
</div>

<h2>核准權杖</h2>
<p class="lede"><strong>DIVERGED 群組預設不處理</strong>——同名但內容不同不是重複，是分歧。要一併處理必須加 <code>-IncludeDiverged</code>，而且權杖會因此改變。</p>
<div class="token">$(ConvertTo-HtmlText -Text $expected)</div>
<p class="lede"><code>-Token "$(ConvertTo-HtmlText -Text $expected)" -Commit</code></p>

<h2>同名群組明細</h2>
<p class="lede">「副本獨有符號」欄若有內容，代表把該副本收走會失去這些函式或類別——那不是重複，是回退。</p>
<table><colgroup><col style="width:8%"><col style="width:7%"><col style="width:15%"><col style="width:10%"><col style="width:7%"><col style="width:5%"><col style="width:8%"><col style="width:5%"><col style="width:15%"><col style="width:20%"></colgroup>
<tr><th>判定</th><th>角色</th><th>檔名</th><th>修改時間</th><th>大小</th><th>版本</th><th>Hash</th><th>符號</th><th>副本獨有符號</th><th>路徑</th></tr>$rowsHtml</table>
</body></html>
"@
[System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($jsonPath, (([ordered]@{
    tool = 'VIA_SameNameConsolidator'; version = 'v0100'; stamp = $Script:Stamp
    roots = $Root; scanned = $scanned
    groups = $groups.Count; identical = $identicalGroups; diverged = $divergedGroups
    reclaimable_bytes = $reclaim; moved = $moved; held = $held
    approved = $approved; token = $expected; include_diverged = $IncludeDiverged.IsPresent
    rows = @($rows)
} | ConvertTo-Json -Depth 6)), [System.Text.UTF8Encoding]::new($false))

Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   同名群組 ' + $groups.Count + '｜真重複 ' + $identicalGroups +
            '｜內容分歧 ' + $divergedGroups + '｜可回收 ' + [math]::Round($reclaim / 1MB, 2) + ' MB')
if ($approved) {
    Write-Host ('   已收攏 ' + $moved + ' 個副本到 _duplicates\（未刪除）') -ForegroundColor Green
} else {
    Write-Host '   DRY-RUN。要執行需同時給 -Token 與 -Commit：' -ForegroundColor Yellow
    Write-Host ('     ' + $expected) -ForegroundColor Yellow
}
Write-Host ('   報告：' + $htmlPath) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray

if (-not $NoBrowser) {
    try { Start-Process -FilePath $htmlPath | Out-Null } catch { }
}
