# 主動 ETF：stats.symbol＝00400A.TW。px 無 00 開頭。stats 補 NAV/AUM/折溢價。持股不造假。
$ErrorActionPreference = 'Continue'
function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}
$py = $env:VIA_VDF_PY
if (-not $py -or -not (Test-Path $py)) { $py = 'C:\Python313\python.exe' }
if (-not $env:VIA_AETF_STATS) {
    $f = Get-ChildItem 'C:\新增資料夾\新增資料夾\VIA_db_part3_rest' -Recurse -Filter 'gl__etf_stats_daily.parquet' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($f) { $env:VIA_AETF_STATS = $f.FullName }
}
if (-not $env:VIA_AETF_LAKE) {
    $env:VIA_AETF_LAKE = @(
        'C:\Users\tonyk\Github\movies-dataset\data\vdf\aetf',
        'C:\Users\tonyk\movies-dataset\data\vdf\aetf'
    ) | Where-Object { Test-Path (Split-Path (Split-Path $_ -Parent) -Parent) } | Select-Object -First 1
}
$env:VIA_AETF_UNI = '00400A,00401A,00402A,00403A,00404A,00405A,00406A,00407A,00408A,00410A,00980A,00981A,00982A,00983A,00984A,00985A,00986A,00987A,00988A,00989A,00990A,00991A,00992A,00993A,00994A,00995A,00996A,00997A,00999A'
$tf = Join-Path $env:TEMP 'via_aetf_nav.py'
@'
import duckdb, os
con = duckdb.connect()
st = (os.environ.get("VIA_AETF_STATS") or "").replace("\\", "/")
lake = os.environ.get("VIA_AETF_LAKE") or ""
uni = [x.strip() for x in (os.environ.get("VIA_AETF_UNI") or "").split(",") if x.strip()]
if not st or not os.path.isfile(st):
    print("NO stats"); raise SystemExit(2)
codes = ",".join("'" + c + ".TW'" for c in uni)
sql = f"""
SELECT regexp_replace(upper(CAST(symbol AS VARCHAR)), '\\.TW(O)?','') AS fund,
       date, symbol, aum, nav, price, shares_outstanding,
       CASE WHEN nav IS NULL OR nav = 0 THEN NULL ELSE price/nav - 1 END AS premium
FROM read_parquet('{st}')
WHERE upper(CAST(symbol AS VARCHAR)) IN ({codes})
"""
n = con.execute(f"SELECT COUNT(*) FROM ({sql})").fetchone()[0]
print("NAV rows", n)
miss = []
for c in uni:
    k = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{st}') WHERE upper(CAST(symbol AS VARCHAR)) IN ('{c}.TW','{c}')"
    ).fetchone()[0]
    if k == 0:
        miss.append(c)
print("MISS", ",".join(miss) if miss else "none")
dest = os.path.join(lake, "year=2026")
os.makedirs(dest, exist_ok=True)
du = os.path.join(dest, "part-nav.parquet").replace("\\", "/")
con.execute(f"COPY ({sql}) TO '{du}' (FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)")
print("OK nav", du)
for r in con.execute(
    f"SELECT fund, max(date), arg_max(aum, date), arg_max(nav, date), arg_max(price, date), arg_max(premium, date) FROM ({sql}) GROUP BY 1 ORDER BY 3 DESC NULLS LAST"
).fetchall():
    print("FUND", r)
'@ | Set-Content $tf -Encoding utf8
Lamp 'GREEN' 'POLICY' 'stats 補 NAV/AUM/折溢價 · px 無 00xxA · 持股無 · LIVE 關'
& $py $tf 2>&1 | ForEach-Object {
    $l = "$_"
    $c = if ($l -match '^OK|^FUND') { 'GREEN' } elseif ($l -match '^MISS|^NO') { 'YELLOW' } else { 'GREY' }
    Lamp $c 'NAV' $l
}
Lamp 'YELLOW' 'HOLD' '封存無 DailyHoldings · 集中/法人黃 · 不造假'
Lamp 'YELLOW' 'PX' '日價庫只有個股 · 主動 ETF vs 0050 不能算'
