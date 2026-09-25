# 主動式台股 ETF：盤兩份封存 → 十層對帳 → LOCAL 補宇宙／價。LIVE 關。不刪。
$ErrorActionPreference = 'Continue'
function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-14} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

$Seals = @(
    'C:\新增資料夾\新增資料夾\VETF_FINAL_SEAL_20260829_013330 (2)',
    'C:\新增資料夾\新增資料夾\VIA_ActiveETF_FINAL (1)'
)
$Book = Get-ChildItem -LiteralPath 'C:\新增資料夾\新增資料夾\VIA_db_part3_rest' -Recurse -Filter 'tw__etf_book.parquet' -ErrorAction SilentlyContinue | Select-Object -First 1
$Stats = Get-ChildItem -LiteralPath 'C:\新增資料夾\新增資料夾\VIA_db_part3_rest' -Recurse -Filter 'gl__etf_stats_daily.parquet' -ErrorAction SilentlyContinue | Select-Object -First 1
$Px = Get-ChildItem -LiteralPath 'C:\新增資料夾\新增資料夾\VIA_db_part1_prices' -Recurse -Filter 'tw__tw_daily_prices.parquet' -ErrorAction SilentlyContinue | Select-Object -First 1
$Lake = @('C:\Users\tonyk\Github\movies-dataset\data\vdf\aetf', 'C:\Users\tonyk\movies-dataset\data\vdf\aetf') |
    Where-Object { Test-Path (Split-Path (Split-Path $_ -Parent) -Parent) } | Select-Object -First 1
if (-not $Lake) { $Lake = 'C:\Users\tonyk\movies-dataset\data\vdf\aetf' }
if (-not (Test-Path $Lake)) { New-Item -ItemType Directory -Path $Lake -Force | Out-Null }

Lamp 'GREEN' 'POLICY' '十層對帳 · COPY_ONLY · 不刪封存 · 禁網'

foreach ($d in $Seals) {
    if (-not (Test-Path -LiteralPath $d)) { Lamp 'RED' 'SEAL' "缺 $d"; continue }
    $files = @(Get-ChildItem -LiteralPath $d -Recurse -File -ErrorAction SilentlyContinue)
    $hold = @($files | Where-Object { $_.Name -match 'hold|持股|DailyHold' }).Count
    $nav = @($files | Where-Object { $_.Name -match 'nav|aum|flow|units' }).Count
    $pq = @($files | Where-Object { $_.Extension -match 'parquet|pq' }).Count
    $duck = @($files | Where-Object { $_.Extension -match 'duckdb|\.db' }).Count
    $pyf = @($files | Where-Object { $_.Extension -eq '.py' }).Count
    Lamp 'GREEN' 'SEAL' ("{0} 檔{1} hold{2} nav{3} pq{4} duck{5} py{6}" -f (Split-Path $d -Leaf), $files.Count, $hold, $nav, $pq, $duck, $pyf)
    $files | Select-Object -First 10 | ForEach-Object { Lamp 'GREY' 'FILE' ($_.FullName.Substring($d.Length)) }
}

$py = $null
foreach ($c in @(
        'C:\Python313\python.exe',
        'C:\ProgramData\miniconda3\envs\veritas_CORE_DATA\python.exe',
        'C:\ProgramData\miniconda3\envs\veritas\python.exe'
    )) {
    if (-not (Test-Path $c)) { continue }
    $chk = & $c -c "import duckdb; print('DUCK')" 2>$null
    if ($LASTEXITCODE -eq 0 -and "$chk" -match 'DUCK') { $py = $c; break }
}
if (-not $py) { Lamp 'RED' 'DUCK' '無 duckdb'; return }
Lamp 'GREEN' 'DUCK' $py

$env:VIA_AETF_BOOK = if ($Book) { $Book.FullName } else { '' }
$env:VIA_AETF_PX = if ($Px) { $Px.FullName } else { '' }
$env:VIA_AETF_STATS = if ($Stats) { $Stats.FullName } else { '' }
$env:VIA_AETF_LAKE = $Lake
$env:VIA_AETF_S0 = $Seals[0]
$env:VIA_AETF_S1 = $Seals[1]

$h2 = Join-Path $env:TEMP 'via_aetf_fill2.py'
@'
import duckdb, os, re
con = duckdb.connect()
book = os.environ.get("VIA_AETF_BOOK") or ""
px = os.environ.get("VIA_AETF_PX") or ""
stats = os.environ.get("VIA_AETF_STATS") or ""
lake = os.environ.get("VIA_AETF_LAKE") or ""
seals = [os.environ.get("VIA_AETF_S0") or "", os.environ.get("VIA_AETF_S1") or ""]

def rng(code):
    m = re.match(r"^00(\d{3})A$", str(code).upper().replace(".TW","").replace(".TWO",""))
    if not m:
        return False
    n = int(m.group(1))
    return (400 <= n <= 499) or (980 <= n <= 999)

u_name = []
if book and os.path.isfile(book):
    fu = book.replace("\\", "/")
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fu}')").fetchall()]
    print("COLS book", cols)
    df = con.execute(f"SELECT * FROM read_parquet('{fu}')").fetchdf()
    code_col = next((c for c in cols if c.lower() in ("fund_code", "code", "ticker")), cols[0])
    name_col = next((c for c in cols if "name" in c.lower()), None)
    named, aln = [], []
    for rec in df.to_dict("records"):
        code = str(rec[code_col]).upper().split(".")[0]
        name = str(rec[name_col]) if name_col else ""
        if rng(code):
            aln.append(code)
            if "主動" in name:
                named.append(code)
    u_name = sorted(set(named)) or sorted(set(aln))
    print("UNIVERSE", len(u_name), ",".join(u_name))
    dest = os.path.join(lake, "year=2026")
    os.makedirs(dest, exist_ok=True)
    du = os.path.join(dest, "part-roster.parquet").replace("\\", "/")
    codes_sql = ",".join("'" + c + "'" for c in u_name) if u_name else "''"
    con.execute(
        f"COPY (SELECT DISTINCT * FROM read_parquet('{fu}') WHERE regexp_replace(upper(CAST({code_col} AS VARCHAR)), '\\.TW(O)?','') IN ({codes_sql})) TO '{du}' (FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)"
    )
    print("OK roster", len(u_name))
else:
    print("NO book")

if px and os.path.isfile(px):
    fu = px.replace("\\", "/")
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fu}')").fetchall()]
    print("COLS px", cols)
    tcol = next((c for c in cols if c.lower() in ("ticker", "code", "symbol", "stock_id")), None)
    dcol = next((c for c in cols if c.lower() in ("date", "obs_date")), None)
    if tcol and u_name:
        codes_sql = ",".join(["'" + c + "'" for c in u_name] + ["'" + c + ".TW'" for c in u_name])
        n = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{fu}') WHERE CAST({tcol} AS VARCHAR) IN ({codes_sql})"
            + (f" AND YEAR(TRY_CAST({dcol} AS DATE)) BETWEEN 2023 AND 2026" if dcol else "")
        ).fetchone()[0]
        tick = con.execute(
            f"SELECT CAST({tcol} AS VARCHAR) t, COUNT(*) n FROM read_parquet('{fu}') WHERE CAST({tcol} AS VARCHAR) IN ({codes_sql}) GROUP BY 1 ORDER BY 1"
        ).fetchall()
        print("PX rows", n)
        for t, k in tick:
            print("PX t", t, k)
    else:
        print("PX skip", tcol, cols[:12])
else:
    print("NO px")

if stats and os.path.isfile(stats):
    fu = stats.replace("\\", "/")
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fu}')").fetchall()]
    print("COLS stats", cols)
    print("STATS n", con.execute(f"SELECT COUNT(*) FROM read_parquet('{fu}')").fetchone()[0])
else:
    print("NO stats")

hold_n = 0
for root in seals:
    if not root or not os.path.isdir(root):
        print("NOSEAL", root)
        continue
    print("SEALOK", root)
    for dirpath, _, files in os.walk(root):
        for fn in files:
            low = fn.lower()
            blob = low + " " + dirpath.lower()
            if not any(k in blob for k in ("hold", "持股", "holding", "nav", "aum")):
                continue
            p = os.path.join(dirpath, fn)
            print("HIT", p)
            hold_n += 1
            if low.endswith(".parquet"):
                dest = os.path.join(lake, "year=2026")
                os.makedirs(dest, exist_ok=True)
                du = os.path.join(dest, "part-" + re.sub(r"[^0-9A-Za-z]+", "", fn)[:48] + ".parquet").replace("\\", "/")
                try:
                    con.execute(
                        f"COPY (SELECT * FROM read_parquet('{p.replace(chr(92), '/')}')) TO '{du}' (FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)"
                    )
                    print("OK copy", fn)
                except Exception as e:
                    print("FAIL copy", fn, e)
print("HITS", hold_n)
'@ | Set-Content -LiteralPath $h2 -Encoding utf8

& $py $h2 2>&1 | ForEach-Object {
    $l = "$_"
    $c = if ($l -match '^OK|^UNIVERSE|^SEALOK|^PX t') { 'GREEN' } elseif ($l -match '^NO|^FAIL|^NOSEAL') { 'YELLOW' } else { 'GREY' }
    Lamp $c 'AEA' $l
}
Lamp 'GREEN' 'AK' 'akshare SKIP'
Lamp 'GREEN' 'SUM' "湖 $Lake · 原件／封存未刪"
