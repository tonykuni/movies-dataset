# 需要 PowerShell 7（pwsh）。貼在 PS>。不要貼 cmd。不要 cd /d。
# VIA Ingest 2023→最新 · 本機三庫 COPY 進 GitHub hive 湖
# 政策: 原件不刪不搬、不卸載、不殺行程、不 exit、預設禁網、AKShare 跳過、勿重做 DCT
# 擷取: LAKE 已有→SKIP · 否則 LOCAL COPY · CACHE 種子 · LIVE 要 $Live=$true 且 32hex KEY
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$StartYear = 2023
$EndYear = [int](Get-Date).Year
$Live = $false
$FredKey = $env:VIA_FRED_KEY

$env:PYTHONNOUSERSITE = '1'
$env:VIA_LKGC = '2026-09-06'
$env:VIA_START_YEAR = "$StartYear"
$env:VIA_NET = $(if ($Live) { '1' } else { '0' })

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

function New-Dir([string]$p) {
    if ($p -and -not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
}

function Encode-Html([string]$t) {
    if ([string]::IsNullOrEmpty($t)) { return '' }
    return [System.Net.WebUtility]::HtmlEncode($t)
}

function Enter-ViaProject {
    $roots = @(
        'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
    )
    $root = $roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $root) {
        Lamp 'RED' 'ENTER' '找不到母系統 · 仍嘗試三庫 COPY（絕對路徑）'
        return $false
    }
    Set-Location -LiteralPath $root
    $env:PYTHONNOUSERSITE = '1'
    $env:VIA_LKGC = '2026-09-06'
    $env:VIA_START_YEAR = "$StartYear"
    $env:VIA_NET = $(if ($Live) { '1' } else { '0' })
    $env:VIA_ROOT = $root
    $vdfHome = @(
        "$env:USERPROFILE\miniconda3\envs\via_vdf",
        "$env:USERPROFILE\anaconda3\envs\via_vdf",
        "$env:USERPROFILE\Miniconda3\envs\via_vdf",
        'C:\Users\tonyk\miniconda3\envs\via_vdf',
        'C:\Users\tonyk\anaconda3\envs\via_vdf',
        'C:\Users\tonyk\Miniconda3\envs\via_vdf'
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($vdfHome) {
        $env:CONDA_PREFIX = $vdfHome
        $env:CONDA_DEFAULT_ENV = 'via_vdf'
        $env:PATH = "$vdfHome;$vdfHome\Scripts;$vdfHome\Library\bin;" + $env:PATH
        Lamp 'GREEN' 'ENV' "via_vdf  $vdfHome"
    }
    else {
        Lamp 'YELLOW' 'ENV' 'via_vdf 未見 · 不 conda create · 不混 base'
    }
    Lamp 'GREEN' 'ENTER' $root
    Lamp 'GREEN' 'CWD' (Get-Location).Path
    return $true
}

[void](Enter-ViaProject)

$SrcRoot = 'C:\新增資料夾\新增資料夾'
$GitLake = 'C:\Users\tonyk\Github\movies-dataset\data\vdf'
$GitAlt  = 'C:\Users\tonyk\movies-dataset\data\vdf'
$Mother  = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics\data\vdf'
$DataDb  = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\DATABASE'
$ReportDir = Join-Path $DataDb '_reports'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

$Parts = @(
    @{ Id = 'PX';   Name = '價量'; Lake = 'px';   Folder = 'VIA_db_part1_prices'; Order = 'ticker, obs_date' }
    @{ Id = 'CHIP'; Name = '籌碼'; Lake = 'chip'; Folder = 'VIA_db_part2_chips';  Order = 'ticker, obs_date' }
    @{ Id = 'REST'; Name = '其餘'; Lake = 'rest'; Folder = 'VIA_db_part3_rest';   Order = 'kind, ticker, obs_date' }
)

function Resolve-LakeRoot {
    foreach ($c in @($GitLake, $GitAlt, $Mother)) {
        $probe = Split-Path (Split-Path $c -Parent) -Parent
        if (Test-Path -LiteralPath $probe) { return $c }
    }
    return $GitLake
}

$LakeRoot = Resolve-LakeRoot
New-Dir $LakeRoot
New-Dir $ReportDir

Lamp 'GREEN' 'POLICY' "COPY_ONLY · 不刪原件 · $StartYear → $EndYear · 網 $($env:VIA_NET)"
Lamp 'GREEN' 'SRC' $SrcRoot
Lamp 'GREEN' 'LAKE' $LakeRoot
if (Test-Path -LiteralPath $Mother) { Lamp 'GREEN' 'MOTHER' $Mother } else { Lamp 'YELLOW' 'MOTHER' '未見 · 只寫 GitHub 湖' }
if (Test-Path -LiteralPath $DataDb) { Lamp 'GREEN' 'DATA' $DataDb } else { Lamp 'YELLOW' 'DATA' '資料盤未見' }

if ($Live) {
    if ($FredKey -notmatch '^[0-9a-fA-F]{32}$') {
        Lamp 'RED' 'LIVE' 'KEY 不是 32 hex · 拒絕外呼 · 改走 LOCAL/CACHE'
        $Live = $false
        $env:VIA_NET = '0'
    }
    else {
        Lamp 'YELLOW' 'LIVE' '雙閘開 · FRED 才外呼 · AKShare 仍 SKIP · KEY 不寫檔'
    }
}
else {
    Lamp 'GREEN' 'NET' '禁網 · AKShare SKIP · YF/TWSE SKIP'
}

function Get-Python {
    foreach ($p in @(
            "$env:CONDA_PREFIX\python.exe",
            "$env:USERPROFILE\miniconda3\envs\via_vdf\python.exe",
            "$env:USERPROFILE\anaconda3\envs\via_vdf\python.exe",
            "$env:USERPROFILE\Miniconda3\envs\via_vdf\python.exe",
            'C:\Users\tonyk\miniconda3\envs\via_vdf\python.exe',
            'C:\Users\tonyk\anaconda3\envs\via_vdf\python.exe',
            'C:\Users\tonyk\Miniconda3\envs\via_vdf\python.exe',
            'C:\Users\tonyk\envs\via_vdf\python.exe'
        )) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    $conda = Get-Command conda -ErrorAction SilentlyContinue
    if ($conda) {
        $exe = & conda run -n via_vdf --no-banner python -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) {
            $hit = ($exe | Select-Object -Last 1).ToString().Trim()
            if ($hit -and (Test-Path -LiteralPath $hit)) { return $hit }
        }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$Py = Get-Python
if ($Py) { Lamp 'GREEN' 'PY' $Py } else { Lamp 'YELLOW' 'PY' '無 python · 改 parquet 檔案複製' }

$PyHelper = Join-Path $env:TEMP "via_ingest_$Stamp.py"
@'
import glob, os, sys
src, dest, year_s, order = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
year = int(year_s)
os.makedirs(os.path.dirname(dest), exist_ok=True)
try:
    import duckdb
except ImportError:
    sys.stderr.write("NO_DUCKDB\n")
    sys.exit(4)
src_u = src.replace("\\", "/")
dest_u = dest.replace("\\", "/")
con = duckdb.connect()
con.execute("PRAGMA enable_object_cache")
con.execute("SET enable_object_cache=true")
con.execute("SET enable_http_metadata_cache=false")
pq = glob.glob(os.path.join(src, "**", "*.parquet"), recursive=True)
csv = glob.glob(os.path.join(src, "**", "*.csv"), recursive=True)
if pq:
    read = f"read_parquet('{src_u}/**/*.parquet', hive_partitioning=true, union_by_name=false)"
elif csv:
    read = f"read_csv_auto('{src_u}/**/*.csv', union_by_name=false)"
else:
    sys.stderr.write("NO_FILES\n")
    sys.exit(2)
where = f"COALESCE(TRY_CAST(year AS INTEGER), YEAR(TRY_CAST(obs_date AS DATE)), YEAR(TRY_CAST(date AS DATE)), YEAR(TRY_CAST(as_of AS DATE))) = {year}"
def run(read_sql, order_sql):
    q = f"COPY (SELECT * FROM {read_sql} WHERE {where} ORDER BY {order_sql}) TO '{dest_u}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 65536, OVERWRITE_OR_IGNORE)"
    con.execute(q)
try:
    run(read, order)
except Exception:
    try:
        run(read, "1")
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(3)
if not os.path.isfile(dest) or os.path.getsize(dest) <= 0:
    sys.exit(2)
sys.stdout.write(f"OK {os.path.getsize(dest)}\n")
'@ | Set-Content -LiteralPath $PyHelper -Encoding utf8

function Test-LakeYear([string]$root, [int]$year) {
    $dir = Join-Path $root "year=$year"
    if (-not (Test-Path -LiteralPath $dir)) { return $false }
    return (@(Get-ChildItem -LiteralPath $dir -Filter 'part-*.parquet' -File -ErrorAction SilentlyContinue).Count -gt 0)
}

function Copy-YearTree([string]$src, [string]$destDir, [int]$year) {
    New-Dir $destDir
    $copied = 0
    $hive = @(Get-ChildItem -LiteralPath $src -Recurse -Directory -Filter "year=$year" -ErrorAction SilentlyContinue)
    foreach ($d in $hive) {
        $files = @(Get-ChildItem -LiteralPath $d.FullName -Filter 'part-*.parquet' -File -ErrorAction SilentlyContinue)
        if ($files.Count -eq 0) { $files = @(Get-ChildItem -LiteralPath $d.FullName -Filter '*.parquet' -File -ErrorAction SilentlyContinue) }
        foreach ($f in $files) {
            $target = Join-Path $destDir $(if ($f.Name -like 'part-*.parquet') { $f.Name } else { 'part-000.parquet' })
            Copy-Item -LiteralPath $f.FullName -Destination $target -Force
            $copied++
        }
    }
    if ($copied -eq 0) {
        $files = @(Get-ChildItem -LiteralPath $src -Recurse -Filter '*.parquet' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "$year" -or $_.DirectoryName -match "year=$year" })
        $i = 0
        foreach ($f in $files) {
            Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $destDir ('part-{0:000}.parquet' -f $i)) -Force
            $copied++
            $i++
        }
    }
    return $copied
}

function Publish-Part([string]$file) {
    if (-not (Test-Path -LiteralPath $file)) { return }
    if (-not $file.StartsWith($LakeRoot, [System.StringComparison]::OrdinalIgnoreCase)) { return }
    $rel = $file.Substring($LakeRoot.Length).TrimStart('\')
    foreach ($root in @($Mother, $DataDb)) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $dest = Join-Path $root $rel
        New-Dir (Split-Path $dest -Parent)
        Copy-Item -LiteralPath $file -Destination $dest -Force
    }
}

$Rows = [System.Collections.Generic.List[object]]::new()
$Years = @()
for ($y = $EndYear; $y -ge $StartYear; $y--) { $Years += $y }

foreach ($p in $Parts) {
    $src = Join-Path $SrcRoot $p.Folder
    $srcOk = Test-Path -LiteralPath $src
    Lamp $(if ($srcOk) { 'GREEN' } else { 'RED' }) $p.Id $(if ($srcOk) { $src } else { "缺原件 $($p.Folder)" })
    foreach ($year in $Years) {
        $lakeDir = Join-Path $LakeRoot (Join-Path $p.Lake "year=$year")
        $part0 = Join-Path $lakeDir 'part-000.parquet'
        New-Dir $lakeDir
        $action = 'SKIP'
        $lamp = 'GREEN'
        $note = '年檔已在湖'
        if (Test-LakeYear (Join-Path $LakeRoot $p.Lake) $year) {
            $action = 'SKIP'
        }
        elseif (-not $srcOk) {
            $action = 'SKIP'
            $lamp = 'YELLOW'
            $note = '原件資料夾不在 · 年檔槽保留'
        }
        else {
            $did = $false
            if ($Py) {
                $out = & $Py $PyHelper $src $part0 "$year" $p.Order 2>&1
                if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $part0)) {
                    $did = $true
                    $action = 'COPY'
                    $note = "DuckDB COPY · $out"
                }
            }
            if (-not $did) {
                $n = Copy-YearTree $src $lakeDir $year
                if ($n -gt 0) {
                    $did = $true
                    $action = 'COPY'
                    $note = "檔案複製 $n 個 · 不刪原件"
                }
            }
            if ($did) {
                Get-ChildItem -LiteralPath $lakeDir -Filter 'part-*.parquet' -File -ErrorAction SilentlyContinue | ForEach-Object { Publish-Part $_.FullName }
                $lamp = 'GREEN'
            }
            else {
                $action = 'SEED'
                $lamp = 'YELLOW'
                $note = '該年無原件可 COPY · 槽保留 · 不抄新值 · 不 LIVE'
            }
        }
        $Rows.Add([pscustomobject]@{ Lamp = $lamp; Id = $p.Id; Name = $p.Name; Year = $year; Action = $action; Dest = $part0; Note = $note })
        Lamp $lamp "$($p.Id)-$year" "$action  $note"
    }
}

$FredDir = Join-Path $LakeRoot 'fred'
$FredSrc = @(
    (Join-Path $DataDb 'fred'),
    (Join-Path $Mother 'fred'),
    (Join-Path $SrcRoot 'VIA_db_part3_rest')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
foreach ($year in $Years) {
    $destDir = Join-Path $FredDir "year=$year"
    $dest = Join-Path $destDir 'part-000.parquet'
    New-Dir $destDir
    $action = 'SKIP'; $lamp = 'GREEN'; $note = 'FRED 年檔已在湖'
    if (Test-LakeYear $FredDir $year) {
        $action = 'SKIP'
    }
    elseif ($Live -and $FredKey -match '^[0-9a-fA-F]{32}$') {
        $action = 'LIVE'
        $lamp = 'YELLOW'
        $note = '閘已開 · 請用總管／Invoke-VDF-Fetch · 本腳本不把 KEY 寫進檔 · 不外呼'
    }
    elseif ($FredSrc) {
        $n = Copy-YearTree $FredSrc $destDir $year
        if ($n -gt 0) {
            $action = 'COPY'
            $note = "本地 FRED COPY $n"
            if (Test-Path -LiteralPath $dest) { Publish-Part $dest }
        }
        else {
            $action = 'SEED'
            $lamp = 'YELLOW'
            $note = 'CACHE 期末種子 · 年檔槽保留 · 不外呼'
        }
    }
    else {
        $action = 'SEED'
        $lamp = 'YELLOW'
        $note = 'CACHE 期末種子 · 年檔槽保留 · 不外呼'
    }
    $Rows.Add([pscustomobject]@{ Lamp = $lamp; Id = 'FRED'; Name = '宏觀'; Year = $year; Action = $action; Dest = $dest; Note = $note })
    Lamp $lamp "FRED-$year" "$action  $note"
}

$copyN = @($Rows | Where-Object { $_.Action -eq 'COPY' }).Count
$skipN = @($Rows | Where-Object { $_.Action -eq 'SKIP' }).Count
$seedN = @($Rows | Where-Object { $_.Action -eq 'SEED' }).Count
$liveN = @($Rows | Where-Object { $_.Action -eq 'LIVE' }).Count

Write-Host ''
Write-Host ('{0,-6} {1,-5} {2,-6} {3,-6} {4}' -f 'LAMP', 'ID', 'YEAR', 'ACT', 'NOTE') -ForegroundColor Cyan
foreach ($r in $Rows) {
    Lamp $r.Lamp "$($r.Id)" ("{0} {1}  {2}" -f $r.Year, $r.Action, $r.Note)
}
Lamp 'GREEN' 'SUM' "COPY $copyN · SKIP $skipN · SEED $seedN · LIVE $liveN · 原件未動"
Lamp 'GREEN' 'AK' 'akshare_call SKIP · 依指示不跑'

$tr = ($Rows | ForEach-Object {
        $cls = switch ($_.Lamp) { 'GREEN' { 'ok' } 'RED' { 'bad' } default { 'warn' } }
        "<tr class='$cls'><td>$cls</td><td>$(Encode-Html $_.Id)</td><td>$($_.Year)</td><td>$(Encode-Html $_.Action)</td><td>$(Encode-Html $_.Dest)</td><td>$(Encode-Html $_.Note)</td></tr>"
    }) -join "`n"

$html = @"
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA Ingest $StartYear-$EndYear</title>
<style>
body{margin:24px;background:#0e1116;color:#d7dde8;font:13px/1.45 ui-sans-serif,system-ui}
h1{font-size:16px;font-weight:600;letter-spacing:.04em}
.meta{color:#8b93a7;font-family:ui-monospace,monospace;font-size:12px}
table{border-collapse:collapse;width:100%;margin-top:16px;font-size:12px}
th,td{border-bottom:1px solid #242a36;padding:6px 8px;text-align:left;vertical-align:top}
th{color:#8b93a7;font-weight:500}
tr.ok td:first-child{color:#3dd68c}tr.warn td:first-child{color:#e6b84d}tr.bad td:first-child{color:#ff5d5d}
td{word-break:break-all}
</style></head><body>
<h1>VIA Ingest · $StartYear → $EndYear · COPY_ONLY</h1>
<p class="meta">$Stamp · 源 $SrcRoot · 湖 $LakeRoot · 網 $($env:VIA_NET) · AK SKIP · 原件不刪</p>
<p class="meta">COPY $copyN · SKIP $skipN · SEED $seedN · LIVE $liveN</p>
<table><thead><tr><th>燈</th><th>庫</th><th>年</th><th>動作</th><th>目的</th><th>註</th></tr></thead><tbody>
$tr
</tbody></table>
</body></html>
"@

$HtmlPath = Join-Path $ReportDir "VIA_ingest_${StartYear}_${EndYear}_$Stamp.html"
if (-not (Test-Path -LiteralPath $ReportDir)) { $HtmlPath = Join-Path $env:TEMP "VIA_ingest_$Stamp.html" }
New-Dir (Split-Path $HtmlPath -Parent)
Set-Content -LiteralPath $HtmlPath -Value $html -Encoding utf8
Lamp 'GREEN' 'HTML' $HtmlPath
Start-Process $HtmlPath

Write-Host ''
Write-Host '不可關閉 · 矩陣報告已開瀏覽器 · 原件三庫未刪 · 按 Enter 才結束' -ForegroundColor Yellow
if ($args -contains '-Yes' -or $env:VIA_INGEST_YES -eq '1') {
    Lamp 'GREEN' 'DONE' 'VIA_INGEST_YES · 不暫停'
    return
}
[void](Read-Host)
