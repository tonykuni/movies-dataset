&{
# ============================================================================
# Optimize-VIA-Repo_v0101.ps1  -  tonykuni/movies-dataset repo hygiene, one click
#   1. data/  ->  C:\Users\tonyk\Github\movies-dataset\data   (untrack, move, ignore; history untouched)
#   2. branch audit: is claude/via-system-followup-tz7k9t uploaded? merged? ahead/behind main?
#   3. tracked-file audit: data-type files, >5MB files, secret-like strings (report only)
#   4. VLL registration candidate (VIA-SPJ id) + registry discovery
#   5. commit + push (logic only)  ->  HTML report
# Append-only: nothing deleted from disk; git history not rewritten; existing files never overwritten.
# ============================================================================
$ErrorActionPreference = "Continue"
$env:GIT_TERMINAL_PROMPT = "0"
$script:Sw = [System.Diagnostics.Stopwatch]::StartNew()
$script:Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$script:Utf8 = [System.Text.UTF8Encoding]::new($false)
$script:Log = [System.Collections.Generic.List[string]]::new()
$script:Warn = [System.Collections.Generic.List[string]]::new()
$script:TargetBranch = "claude/via-system-followup-tz7k9t"
$script:DataHomeRoot = "C:\Users\tonyk\Github"
if (-not $IsWindows) { $script:DataHomeRoot = Join-Path $HOME "Github" }

function Write-Log {
    param([string]$Msg, [string]$Lvl = "INFO")
    $color = "Gray"
    if ($Lvl -eq "OK") { $color = "Green" }
    if ($Lvl -eq "WARN") { $color = "Yellow"; $script:Warn.Add($Msg) }
    if ($Lvl -eq "ERR") { $color = "Red"; $script:Warn.Add($Msg) }
    if ($Lvl -eq "STEP") { $color = "Cyan" }
    $line = ("[{0}] [{1,-4}] {2}" -f $script:Sw.Elapsed.ToString("mm\:ss\.f"), $Lvl, $Msg)
    Write-Host $line -ForegroundColor $color
    $script:Log.Add($line)
}
function Invoke-Git {
    param([string[]]$GitArgs)
    $lines = [System.Collections.Generic.List[string]]::new()
    & git -C $script:Repo @GitArgs 2>&1 | ForEach-Object { $t = if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message } else { "$_" }; $lines.Add($t) }
    return [pscustomobject]@{ Code = $LASTEXITCODE; Lines = $lines; Text = ($lines -join "`n") }
}
function Write-NewFile {
    param([string]$Path, [string]$Content)
    if (Test-Path -LiteralPath $Path) { Write-Log ("exists, untouched: " + $Path) "INFO"; return $false }
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { [System.IO.Directory]::CreateDirectory($dir) | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8)
    Write-Log ("NEW " + $Path) "OK"
    return $true
}
function Add-IgnoreLines {
    param([string]$IgnorePath, [string[]]$Lines, [string]$Header)
    $existing = @()
    if (Test-Path -LiteralPath $IgnorePath) { $existing = @([System.IO.File]::ReadAllLines($IgnorePath) | ForEach-Object { $_.Trim() }) }
    $add = @($Lines | Where-Object { $existing -notcontains $_ })
    if ($add.Count -eq 0) { Write-Log ".gitignore already has all rules" "INFO"; return @() }
    $block = "`n" + $Header + "`n" + ($add -join "`n") + "`n"
    [System.IO.File]::AppendAllText($IgnorePath, $block, $script:Utf8)
    Write-Log (".gitignore += " + ($add -join " | ")) "OK"
    return $add
}
function Get-HtmlSafe { param([string]$S) return [System.Net.WebUtility]::HtmlEncode($S) }

# ---------------------------------------------------------------- STEP 1 repo
Write-Log "STEP 1  locate repo" "STEP"
$cands = @("C:\Users\tonyk\movies-dataset", "C:\Users\tonyk\Downloads\movies-dataset", (Join-Path $HOME "movies-dataset"), (Join-Path $HOME "Downloads\movies-dataset"))
$script:Repo = $null
foreach ($c in $cands) { if ((Test-Path -LiteralPath (Join-Path $c ".git") -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath (Join-Path $c "VeritasIntelligenceAnalytics") -ErrorAction SilentlyContinue)) { $script:Repo = $c; break } }
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $script:Repo -or -not $gitCmd) { Write-Log "repo clone or git not found - nothing done" "ERR"; return }
$script:ViaRoot = Join-Path $script:Repo "VeritasIntelligenceAnalytics"
$script:VllRoot = Join-Path $script:ViaRoot "functional modules\VLL"
$repoName = Split-Path $script:Repo -Leaf
$script:DataHome = Join-Path (Join-Path $script:DataHomeRoot $repoName) "data"
Write-Log "repo = $script:Repo" "OK"
$remote = (Invoke-Git @("remote", "get-url", "origin")).Text.Trim()
$curBranch = (Invoke-Git @("rev-parse", "--abbrev-ref", "HEAD")).Text.Trim()
Write-Log "origin = $remote  |  HEAD = $curBranch" "INFO"
$dirty = @((Invoke-Git @("status", "--porcelain")).Lines | Where-Object { $_ -ne "" })
if ($dirty.Count -gt 0) { Write-Log ("working tree has {0} uncommitted change(s) before start (kept, committed together)" -f $dirty.Count) "WARN" }

# ---------------------------------------------------------------- STEP 2 branch audit
Write-Log "STEP 2  fetch + branch audit ($script:TargetBranch)" "STEP"
$f = Invoke-Git @("fetch", "--all", "--prune", "--quiet")
if ($f.Code -ne 0) { Write-Log ("fetch failed: " + $f.Text) "WARN" }
$remoteHeads = @((Invoke-Git @("ls-remote", "--heads", "origin")).Lines | Where-Object { $_ -match "refs/heads/" } | ForEach-Object { ($_ -split "refs/heads/")[1].Trim() })
$localHeads = @((Invoke-Git @("for-each-ref", "--format=%(refname:short)", "refs/heads")).Lines | Where-Object { $_ -ne "" })
$defaultBranch = "main"
$symR = Invoke-Git @("symbolic-ref", "refs/remotes/origin/HEAD")
if ($symR.Code -eq 0 -and $symR.Text.Trim() -match "origin/(.+)$") { $defaultBranch = $Matches[1] }
elseif ($remoteHeads -contains "main") { $defaultBranch = "main" } elseif ($remoteHeads -contains "master") { $defaultBranch = "master" } else { $defaultBranch = $curBranch }
Write-Log "default branch = $defaultBranch" "INFO"
$script:BranchRows = [System.Collections.Generic.List[object]]::new()
$allClaude = @(($remoteHeads + $localHeads) | Where-Object { $_ -like "claude/*" } | Sort-Object -Unique)
if ($allClaude -notcontains $script:TargetBranch) { $allClaude += $script:TargetBranch }
foreach ($b in $allClaude) {
    $onRemote = $remoteHeads -contains $b
    $onLocal = $localHeads -contains $b
    $ref = $null
    if ($onRemote) { $ref = "origin/$b" } elseif ($onLocal) { $ref = $b }
    $ahead = "-"; $behind = "-"; $merged = "-"; $last = "-"; $lastMsg = "-"
    if ($ref) {
        $lr = (Invoke-Git @("rev-list", "--left-right", "--count", "origin/${defaultBranch}...$ref")).Text.Trim()
        if ($lr -match "^(\d+)\s+(\d+)$") { $behind = $Matches[1]; $ahead = $Matches[2] }
        $mb = Invoke-Git @("merge-base", "--is-ancestor", $ref, "origin/$defaultBranch")
        $merged = if ($mb.Code -eq 0) { "YES" } else { "NO" }
        $last = (Invoke-Git @("log", "-1", "--format=%ci", $ref)).Text.Trim()
        $lastMsg = (Invoke-Git @("log", "-1", "--format=%s", $ref)).Text.Trim()
    }
    $script:BranchRows.Add([pscustomobject]@{ Branch = $b; Remote = $onRemote; Local = $onLocal; Ahead = $ahead; Behind = $behind; Merged = $merged; LastCommit = $last; Msg = $lastMsg; Target = ($b -eq $script:TargetBranch) })
    $tag = if ($b -eq $script:TargetBranch) { "TARGET " } else { "" }
    Write-Log ("{0}{1}: remote={2} local={3} ahead={4} behind={5} merged-into-{6}={7}" -f $tag, $b, $onRemote, $onLocal, $ahead, $behind, $defaultBranch, $merged) $(if ($b -eq $script:TargetBranch) { "OK" } else { "INFO" })
}
$script:TargetRow = $script:BranchRows | Where-Object { $_.Target } | Select-Object -First 1
$script:Uploaded = if ($script:TargetRow.Remote) { "YES - branch exists on origin" } elseif ($script:TargetRow.Local) { "NO - exists locally only, never pushed" } else { "NOT FOUND - neither on origin nor local (deleted after merge, or name differs)" }
Write-Log ("uploaded? " + $script:Uploaded) $(if ($script:TargetRow.Remote) { "OK" } else { "WARN" })
# PRs (unauthenticated GitHub API from this machine; best effort)
$script:PrRows = [System.Collections.Generic.List[object]]::new()
$script:RepoVisibility = "unknown"
if ($remote -match "github\.com[:/]([^/]+)/([^/.]+)") {
    $own = $Matches[1]; $nm = $Matches[2]
    try {
        $ri = Invoke-RestMethod -Uri "https://api.github.com/repos/$own/$nm" -Headers @{ "User-Agent" = "VIA" } -TimeoutSec 15
        $script:RepoVisibility = if ($ri.private) { "PRIVATE" } else { "PUBLIC" }
        $prs = Invoke-RestMethod -Uri "https://api.github.com/repos/$own/$nm/pulls?state=all&per_page=30" -Headers @{ "User-Agent" = "VIA" } -TimeoutSec 15
        foreach ($p in $prs) { $script:PrRows.Add([pscustomobject]@{ Num = $p.number; State = $(if ($p.merged_at) { "merged" } else { $p.state }); Head = $p.head.ref; Base = $p.base.ref; Title = $p.title; Updated = $p.updated_at; Url = $p.html_url }) }
        Write-Log ("GitHub API: visibility={0}, {1} PR(s)" -f $script:RepoVisibility, $script:PrRows.Count) "INFO"
    } catch { Write-Log ("GitHub API not reachable (fine): " + $_.Exception.Message) "INFO" }
}

# ---------------------------------------------------------------- STEP 3 move data/ out
Write-Log "STEP 3  data/ -> $script:DataHome (untrack + move + ignore)" "STEP"
$dataSrc = Join-Path $script:Repo "data"
$script:MovedFiles = 0; $script:MovedMB = 0; $script:UntrackedCount = 0; $script:MoveStatus = "no data/ folder in repo"
if (Test-Path -LiteralPath $dataSrc) {
    $tracked = @((Invoke-Git @("ls-files", "--", "data")).Lines | Where-Object { $_ -ne "" })
    $script:UntrackedCount = $tracked.Count
    if ($tracked.Count -gt 0) { $null = Invoke-Git @("rm", "-r", "--cached", "--quiet", "--", "data"); Write-Log ("git rm --cached: {0} file(s) untracked (disk copies kept)" -f $tracked.Count) "OK" }
    $files = @([System.IO.Directory]::EnumerateFiles($dataSrc, "*", [System.IO.SearchOption]::AllDirectories))
    $script:MovedFiles = $files.Count
    foreach ($fp in $files) { $script:MovedMB += [System.IO.FileInfo]::new($fp).Length / 1MB }
    $script:MovedMB = [math]::Round($script:MovedMB, 2)
    if (-not (Test-Path -LiteralPath $script:DataHome)) { [System.IO.Directory]::CreateDirectory($script:DataHome) | Out-Null }
    $robo = Get-Command robocopy -ErrorAction SilentlyContinue
    if ($robo) {
        $out = & robocopy $dataSrc $script:DataHome /E /MOVE /NFL /NDL /NJH /NJS /NP /R:1 /W:1 2>&1 | Out-String
        if ($LASTEXITCODE -lt 8) { $script:MoveStatus = ("moved {0} file(s), {1} MB via robocopy (rc={2})" -f $script:MovedFiles, $script:MovedMB, $LASTEXITCODE) } else { $script:MoveStatus = "robocopy FAILED rc=$LASTEXITCODE"; Write-Log ($script:MoveStatus + " " + $out) "ERR" }
    } else {
        foreach ($fp in $files) {
            $rel = $fp.Substring($dataSrc.Length).TrimStart([char]92, [char]47)
            $dst = Join-Path $script:DataHome $rel
            $dd = Split-Path $dst -Parent
            if (-not (Test-Path -LiteralPath $dd)) { [System.IO.Directory]::CreateDirectory($dd) | Out-Null }
            if (Test-Path -LiteralPath $dst) { $dst = $dst + ".dup_" + $script:Ts }
            Move-Item -LiteralPath $fp -Destination $dst -Force
        }
        Get-ChildItem -LiteralPath $dataSrc -Directory -Recurse | Sort-Object -Property @{e = "FullName"; desc = $true } | ForEach-Object { if (-not (Get-ChildItem -LiteralPath $_.FullName -Force)) { Remove-Item -LiteralPath $_.FullName -Force } }
        $script:MoveStatus = ("moved {0} file(s), {1} MB via Move-Item" -f $script:MovedFiles, $script:MovedMB)
    }
    if ($script:MoveStatus -notlike "*FAILED*") { Write-Log $script:MoveStatus "OK" }
    if (-not (Test-Path -LiteralPath $dataSrc)) { [System.IO.Directory]::CreateDirectory($dataSrc) | Out-Null }
    $pointer = "# data moved out of git`n`nLocal data home: " + $script:DataHome + "`nMoved: " + $script:Ts + " (" + $script:MovedFiles + " files, " + $script:MovedMB + " MB)`n`nRule: data never enters git or the AI context. VLL reads it via functional modules/VLL/config/local_paths.json (gitignored).`n"
    $null = Write-NewFile (Join-Path $dataSrc "WHERE_IS_DATA.md") $pointer
} else { Write-Log $script:MoveStatus "INFO" }
$script:IgnoreAdded = Add-IgnoreLines (Join-Path $script:Repo ".gitignore") @("/data/*", "!/data/WHERE_IS_DATA.md", "*.parquet", "*.duckdb", "*.feather", "*.h5", "*.hdf5", "*.sqlite", "*.sqlite3", "*.pkl", "*.pickle") ("# VIA data governance " + $script:Ts + ": data lives in " + $script:DataHomeRoot + " (never in git / never in AI context)")
# VLL local_paths.json (gitignored) pointing at the new data home
$lp = Join-Path $script:VllRoot "config\local_paths.json"
if (Test-Path -LiteralPath (Join-Path $script:VllRoot "config")) {
    $lpJson = '{' + "`n" + '  "data_home": "' + ($script:DataHome -replace "\\", "\\\\") + '",' + "`n" + '  "price_daily": "' + ((Join-Path $script:DataHome "price_daily.parquet") -replace "\\", "\\\\") + '",' + "`n" + '  "duckdb_table": "price_daily",' + "`n" + '  "_note": "gitignored. Paths only. Put real parquet/csv/duckdb here; VLL runner reads price_daily."' + "`n" + '}' + "`n"
    $null = Write-NewFile $lp $lpJson
}

# ---------------------------------------------------------------- STEP 4 tracked-file audit (report only)
Write-Log "STEP 4  tracked-file audit (data-type / >5MB / secret-like) - report only" "STEP"
$all = @((Invoke-Git @("ls-files")).Lines | Where-Object { $_ -ne "" })
$script:AuditRows = [System.Collections.Generic.List[object]]::new()
$secretRx = [regex]'(?i)(api[_-]?key|secret|token|passw(or)?d)\s*[:=]\s*["'']?[A-Za-z0-9_\-]{20,}'
$totalMB = 0
foreach ($rel in $all) {
    $fp = Join-Path $script:Repo $rel
    if (-not (Test-Path -LiteralPath $fp)) { continue }
    $fi = [System.IO.FileInfo]::new($fp)
    $totalMB += $fi.Length / 1MB
    $why = [System.Collections.Generic.List[string]]::new()
    if ($fi.Length -gt 5MB) { $why.Add(("{0:N1} MB" -f ($fi.Length / 1MB))) }
    if ($rel -match "\.(csv|parquet|duckdb|db|sqlite3?|feather|h5|hdf5|pkl|pickle|xlsx|xls|zip|7z|rar)$" -and $rel -notmatch "/mock/") { $why.Add("data-type") }
    if ($fi.Length -lt 2MB -and $rel -match "\.(ps1|py|json|md|txt|yaml|yml|toml|cfg|ini|env|cmd|bat|sh|js|ts|html)$") {
        $txt = [System.IO.File]::ReadAllText($fp)
        if ($secretRx.IsMatch($txt)) { $why.Add("secret-like string") }
    }
    if ($why.Count -gt 0) { $script:AuditRows.Add([pscustomobject]@{ File = $rel; SizeKB = [math]::Round($fi.Length / 1KB, 1); Why = ($why -join ", ") }) }
}
$totalMB = [math]::Round($totalMB, 1)
$dataTypeCount = @($script:AuditRows | Where-Object { $_.Why -like "*data-type*" }).Count
$secretCount = @($script:AuditRows | Where-Object { $_.Why -like "*secret*" }).Count
$bigCount = @($script:AuditRows | Where-Object { $_.Why -match "MB" }).Count
Write-Log ("tracked files: {0} ({1} MB) | data-type: {2} | >5MB: {3} | secret-like: {4}" -f $all.Count, $totalMB, $dataTypeCount, $bigCount, $secretCount) $(if ($secretCount -gt 0) { "WARN" } else { "INFO" })

# ---------------------------------------------------------------- STEP 5 VLL registration candidate + registry discovery
Write-Log "STEP 5  VLL registration candidate (VIA-SPJ) + registry discovery" "STEP"
$script:RegistryHits = [System.Collections.Generic.List[string]]::new()
$opts = [System.IO.EnumerationOptions]::new(); $opts.RecurseSubdirectories = $true; $opts.IgnoreInaccessible = $true; $opts.AttributesToSkip = [System.IO.FileAttributes]::ReparsePoint
foreach ($fp in [System.IO.Directory]::EnumerateFiles($script:ViaRoot, "*.json", $opts)) {
    if ($fp -like "*\.venv\*" -or $fp -like "*\results\*" -or $fp -like "*\node_modules\*") { continue }
    if ([System.IO.FileInfo]::new($fp).Length -gt 3MB) { continue }
    $head = [System.IO.File]::ReadAllText($fp)
    if ($head -match '"SPJ-\d{3}' -or $head -match '"ENG-\d{3}') { $script:RegistryHits.Add($fp.Substring($script:Repo.Length + 1)) }
    if ($script:RegistryHits.Count -ge 25) { break }
}
Write-Log ("registry-like JSON files with SPJ-/ENG- codes: {0}" -f $script:RegistryHits.Count) "INFO"
$regId = "VIA-SPJ-" + (Get-Date -Format "yyyyMMdd") + "-" + ([guid]::NewGuid().ToString("N").Substring(0, 6).ToUpper())
$reg = '{' + "`n" +
'  "via_id": "' + $regId + '",' + "`n" +
'  "type": "SPJ",' + "`n" +
'  "code": "VLL",' + "`n" +
'  "name": "Veritas Logic Loop",' + "`n" +
'  "version": "v0100",' + "`n" +
'  "status": "CANDIDATE_PENDING_REGISTRY",' + "`n" +
'  "path": "functional modules/VLL",' + "`n" +
'  "entry": "bin/via-vll.cmd",' + "`n" +
'  "layers": {"ai_logic": ["schemas", "mock", "strategies", "feedback"], "local_data": ["runner", "config/local_paths.json"], "github_tools": ["engine", "runner", "strategies", "schemas", "mock", "feedback"]},' + "`n" +
'  "principles": ["AI never reads real data", "append-only strategies (_vNNNN)", "data never in git"],' + "`n" +
'  "data_home": "' + ($script:DataHome -replace "\\", "\\\\") + '",' + "`n" +
'  "registered_at": "' + $script:Ts + '",' + "`n" +
'  "next": "append this record into the via-code SPJ registry (pick registry file from optimizer report)"' + "`n" +
'}' + "`n"
$regPath = Join-Path $script:VllRoot "VLL_REGISTRATION_CANDIDATE.json"
$script:RegWritten = Write-NewFile $regPath $reg

# ---------------------------------------------------------------- STEP 6 commit + push
Write-Log "STEP 6  commit + push" "STEP"
$null = Invoke-Git @("add", "-A", "--", ".gitignore", "data", "VeritasIntelligenceAnalytics/functional modules/VLL/VLL_REGISTRATION_CANDIDATE.json")
$staged = @((Invoke-Git @("diff", "--cached", "--name-status")).Lines | Where-Object { $_ -ne "" })
$script:GitResult = "nothing to commit"
if ($staged.Count -gt 0) {
    $c = Invoke-Git @("commit", "-q", "-m", ("chore(data-governance): move data/ out of git to local data home; harden .gitignore; VLL registration candidate [" + $script:Ts + "]"))
    $p = Invoke-Git @("push")
    if ($p.Code -eq 0) { $script:GitResult = ("committed + pushed ({0} index change(s))" -f $staged.Count); Write-Log $script:GitResult "OK" }
    else { $script:GitResult = ("committed locally ({0} change(s)); push failed: {1}" -f $staged.Count, $p.Text.Trim()); Write-Log $script:GitResult "WARN" }
} else { Write-Log $script:GitResult "INFO" }

# ---------------------------------------------------------------- STEP 7 HTML
Write-Log "STEP 7  HTML report" "STEP"
$H = [System.Collections.Generic.List[string]]::new()
$H.Add('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA Repo Optimizer v0101</title>')
$H.Add(@'
<style>
body{font-family:"Segoe UI","Microsoft JhengHei",Consolas,sans-serif;background:#0b0e14;color:#dde3ea;margin:0;padding:28px 36px}
h1{color:#f0c674;margin:0 0 4px}h2{color:#8be9fd;border-bottom:1px solid #223;padding-bottom:4px;margin-top:26px}
.sub{color:#7a8595;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.box{background:#121826;border:1px solid #243049;border-radius:10px;padding:12px 14px}.box h3{margin:0 0 6px;color:#f0c674;font-size:13px}.box .v{font-size:22px;font-weight:700}
.tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:12px;font-weight:600}.ok{background:#1d4d2b;color:#9fe3b0}.warn{background:#5a4a12;color:#ffe08a}.err{background:#5a1d1d;color:#ffb3b3}.info{background:#1d2e4d;color:#a9c8ff}
table{border-collapse:collapse;margin:10px 0;font-size:13px;width:100%}td,th{border:1px solid #243049;padding:6px 10px;text-align:left;vertical-align:top}th{background:#121826;color:#8be9fd}
.mono{font-family:Consolas,monospace;font-size:12px;color:#9ab}pre{background:#121826;border:1px solid #243049;border-radius:8px;padding:12px;font-size:12px;color:#9ab;overflow:auto;max-height:320px}
.cmd{background:#0f1420;border-left:3px solid #f0c674;padding:8px 12px;margin:6px 0;font-family:Consolas,monospace;color:#ffe08a}
</style></head><body>
'@)
$H.Add('<h1>VIA Repo Optimizer v0101 · ' + (Get-HtmlSafe $repoName) + '</h1>')
$H.Add('<div class="sub">' + (Get-HtmlSafe $remote) + ' · HEAD ' + (Get-HtmlSafe $curBranch) + ' · visibility ' + $script:RepoVisibility + ' · ' + $script:Ts + '</div>')
$upCls = if ($script:TargetRow.Remote) { "ok" } else { "warn" }
$H.Add('<div class="grid">')
$H.Add('<div class="box"><h3>' + (Get-HtmlSafe $script:TargetBranch) + ' 上傳了嗎</h3><div class="v"><span class="tag ' + $upCls + '">' + (Get-HtmlSafe $script:Uploaded) + '</span></div></div>')
$H.Add('<div class="box"><h3>data/ 移出</h3><div class="v">' + $script:MovedFiles + ' 檔 · ' + $script:MovedMB + ' MB</div><div class="mono">' + (Get-HtmlSafe $script:DataHome) + '</div></div>')
$H.Add('<div class="box"><h3>Git 追蹤檔</h3><div class="v">' + $all.Count + ' · ' + $totalMB + ' MB</div><div class="mono">data-type ' + $dataTypeCount + ' · &gt;5MB ' + $bigCount + ' · secret-like ' + $secretCount + '</div></div>')
$H.Add('<div class="box"><h3>Git</h3><div class="mono">' + (Get-HtmlSafe $script:GitResult) + '</div></div>')
$H.Add('</div>')

$H.Add('<h2>① 分支狀態（claude/* 全部）</h2><table><tr><th>branch</th><th>origin</th><th>local</th><th>ahead of ' + $defaultBranch + '</th><th>behind</th><th>merged into ' + $defaultBranch + '</th><th>last commit</th><th>msg</th></tr>')
foreach ($r in $script:BranchRows) {
    $st = if ($r.Target) { ' style="background:#16213a"' } else { '' }
    $H.Add('<tr' + $st + '><td class="mono">' + (Get-HtmlSafe $r.Branch) + '</td><td>' + $r.Remote + '</td><td>' + $r.Local + '</td><td>' + $r.Ahead + '</td><td>' + $r.Behind + '</td><td>' + $r.Merged + '</td><td class="mono">' + (Get-HtmlSafe $r.LastCommit) + '</td><td>' + (Get-HtmlSafe $r.Msg) + '</td></tr>')
}
$H.Add('</table>')
if ($script:TargetRow.Remote -and $script:TargetRow.Merged -eq "NO") {
    $H.Add('<p><span class="tag warn">待收留</span> 分支已在 GitHub，但尚未併入 ' + $defaultBranch + '（ahead ' + $script:TargetRow.Ahead + ' commits）。要收留就跑：</p>')
    $H.Add('<div class="cmd">git -C "' + (Get-HtmlSafe $script:Repo) + '" merge --no-ff origin/' + (Get-HtmlSafe $script:TargetBranch) + ' -m "merge ' + (Get-HtmlSafe $script:TargetBranch) + '" ; git -C "' + (Get-HtmlSafe $script:Repo) + '" push</div>')
    $H.Add('<p class="mono">沒自動 merge：behind ' + $script:TargetRow.Behind + ' commits 可能有衝突，需人看一眼。</p>')
} elseif ($script:TargetRow.Merged -eq "YES") { $H.Add('<p><span class="tag ok">已收留</span> 分支內容已在 ' + $defaultBranch + ' 裡。</p>') }
if ($script:PrRows.Count -gt 0) {
    $H.Add('<h3>Pull Requests</h3><table><tr><th>#</th><th>state</th><th>head → base</th><th>title</th><th>updated</th></tr>')
    foreach ($p in $script:PrRows) { $H.Add('<tr><td><a style="color:#8be9fd" href="' + $p.Url + '">#' + $p.Num + '</a></td><td>' + $p.State + '</td><td class="mono">' + (Get-HtmlSafe $p.Head) + ' → ' + (Get-HtmlSafe $p.Base) + '</td><td>' + (Get-HtmlSafe $p.Title) + '</td><td class="mono">' + $p.Updated + '</td></tr>') }
    $H.Add('</table>')
}

$H.Add('<h2>② data/ 移出 git</h2>')
$H.Add('<p>' + (Get-HtmlSafe $script:MoveStatus) + '。git index 移除 ' + $script:UntrackedCount + ' 個追蹤檔；磁碟檔案全部搬到 <span class="mono">' + (Get-HtmlSafe $script:DataHome) + '</span>；repo 內留 <span class="mono">data/WHERE_IS_DATA.md</span> 指標。</p>')
if ($script:IgnoreAdded.Count -gt 0) { $H.Add('<p>.gitignore 新增：<span class="mono">' + (Get-HtmlSafe ($script:IgnoreAdded -join "  ")) + '</span></p>') }
$H.Add('<p><span class="tag warn">注意</span> 歷史 commit 仍含這些檔（未改寫 history，只增不減）。repo 目前 <b>' + $script:RepoVisibility + '</b>。若 data 內容不該公開：(a) 改 Private，或 (b) 另下指令做 history 清洗（git filter-repo，會改寫所有 commit hash）。</p>')
$H.Add('<p><span class="tag info">Streamlit</span> streamlit_app.py 若讀 data/ 下的 csv，部署會找不到檔；那是 template 範例資料，如要保留範例可只把該 csv 放回並 !ignore。</p>')

$H.Add('<h2>③ 追蹤檔稽核（report only，未動）</h2>')
if ($script:AuditRows.Count -gt 0) {
    $H.Add('<table><tr><th>file</th><th>KB</th><th>why</th></tr>')
    foreach ($a in ($script:AuditRows | Sort-Object -Property @{e = "SizeKB"; desc = $true } | Select-Object -First 80)) { $H.Add('<tr><td class="mono">' + (Get-HtmlSafe $a.File) + '</td><td>' + $a.SizeKB + '</td><td>' + (Get-HtmlSafe $a.Why) + '</td></tr>') }
    $H.Add('</table><p class="mono">data-type 檔通常也該搬去 data home（VLL mock 例外）；secret-like 請人工確認是否真 key。</p>')
} else { $H.Add('<p><span class="tag ok">乾淨</span> 沒有 data-type / 大檔 / secret-like 追蹤檔。</p>') }

$H.Add('<h2>④ VLL 註冊（待收錄）</h2>')
$H.Add('<p>候選登記檔：<span class="mono">functional modules/VLL/VLL_REGISTRATION_CANDIDATE.json</span> (' + $regId + ')，status = CANDIDATE_PENDING_REGISTRY。</p>')
if ($script:RegistryHits.Count -gt 0) {
    $H.Add('<p>找到含 SPJ-/ENG- 代碼的 registry JSON（下一輪選一個把 VLL 併入）：</p><pre>' + (Get-HtmlSafe ($script:RegistryHits -join "`n")) + '</pre>')
} else { $H.Add('<p class="mono">VeritasIntelligenceAnalytics 內沒掃到含 SPJ-/ENG- 代碼的 JSON registry；via-code registry 可能在別處，告訴我路徑即可併入。</p>') }

if ($script:Warn.Count -gt 0) { $H.Add('<h2>警告</h2><ul>'); foreach ($w in $script:Warn) { $H.Add('<li>' + (Get-HtmlSafe $w) + '</li>') }; $H.Add('</ul>') }
$H.Add('<h2>Log</h2><pre>' + (Get-HtmlSafe ($script:Log -join "`n")) + '</pre></body></html>')
$reportDir = Join-Path $script:VllRoot "results"
if (-not (Test-Path -LiteralPath $reportDir)) { $reportDir = Join-Path $script:Repo "_via_reports"; if (-not (Test-Path -LiteralPath $reportDir)) { [System.IO.Directory]::CreateDirectory($reportDir) | Out-Null } }
$reportPath = Join-Path $reportDir ("VIA_REPO_OPTIMIZER_" + $script:Ts + ".html")
[System.IO.File]::WriteAllText($reportPath, ($H -join "`n"), $script:Utf8)
Write-Log ("DONE {0} | uploaded? {1} | data moved: {2} | git: {3}" -f $script:Sw.Elapsed.ToString("mm\:ss"), $script:Uploaded, $script:MoveStatus, $script:GitResult) "OK"
Write-Log "report = $reportPath" "OK"
Start-Process $reportPath
}
