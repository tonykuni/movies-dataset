# 主動 ETF 看板：名冊⋈NAV · Δ單位×NAV＝流 · HTML 矩陣。持股不造假。LIVE 關。
$ErrorActionPreference = 'Continue'
function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}
$py = $env:VIA_VDF_PY
if (-not $py -or -not (Test-Path $py)) { $py = 'C:\Python313\python.exe' }
if (-not $env:VIA_AETF_BOOK) {
    $f = Get-ChildItem 'C:\新增資料夾\新增資料夾\VIA_db_part3_rest' -Recurse -Filter 'tw__etf_book.parquet' -EA SilentlyContinue | Select-Object -First 1
    if ($f) { $env:VIA_AETF_BOOK = $f.FullName }
}
if (-not $env:VIA_AETF_STATS) {
    $f = Get-ChildItem 'C:\新增資料夾\新增資料夾\VIA_db_part3_rest' -Recurse -Filter 'gl__etf_stats_daily.parquet' -EA SilentlyContinue | Select-Object -First 1
    if ($f) { $env:VIA_AETF_STATS = $f.FullName }
}
if (-not $env:VIA_AETF_LAKE) {
    $env:VIA_AETF_LAKE = @('C:\Users\tonyk\Github\movies-dataset\data\vdf\aetf','C:\Users\tonyk\movies-dataset\data\vdf\aetf') |
        Where-Object { Test-Path (Split-Path (Split-Path $_ -Parent) -Parent) } | Select-Object -First 1
}
$env:VIA_AETF_HTML = Join-Path $PWD 'logs\via_aetf_board.html'
New-Item -ItemType Directory -Force -Path (Split-Path $env:VIA_AETF_HTML) | Out-Null
$env:VIA_AETF_VETF = 'C:\新增資料夾\新增資料夾\VIA_ActiveETF_FINAL (1)\VIA_ActiveETF_FINAL\vetf'
$tf = Join-Path $env:TEMP 'via_aetf_board.py'
@'
import duckdb, os, html
con = duckdb.connect()
book = (os.environ.get("VIA_AETF_BOOK") or "").replace("\\","/")
st = (os.environ.get("VIA_AETF_STATS") or "").replace("\\","/")
lake = os.environ.get("VIA_AETF_LAKE") or ""
html_path = os.environ.get("VIA_AETF_HTML") or ""
vetf = os.environ.get("VIA_AETF_VETF") or ""
uni = "00400A,00401A,00402A,00403A,00404A,00405A,00406A,00407A,00408A,00410A,00980A,00981A,00982A,00983A,00984A,00985A,00986A,00987A,00988A,00989A,00990A,00991A,00992A,00993A,00994A,00995A,00996A,00997A,00999A".split(",")
codes = ",".join("'"+c+".TW'" for c in uni)
codes_n = ",".join("'"+c+"'" for c in uni)
nav_sql = f"""
SELECT regexp_replace(upper(CAST(symbol AS VARCHAR)), '\\.TW(O)?','') AS fund,
       CAST(date AS DATE) AS as_of, aum, nav, price, shares_outstanding AS units,
       CASE WHEN nav IS NULL OR nav=0 THEN NULL ELSE price/nav - 1 END AS premium
FROM read_parquet('{st}')
WHERE upper(CAST(symbol AS VARCHAR)) IN ({codes})
"""
flow_sql = f"""
SELECT fund, as_of, aum, nav, price, units, premium,
       units - lag(units) OVER (PARTITION BY fund ORDER BY as_of) AS d_units,
       nav * (units - lag(units) OVER (PARTITION BY fund ORDER BY as_of)) AS flow_1d
FROM ({nav_sql})
"""
last_sql = f"""
SELECT fund, max(as_of) AS as_of,
       arg_max(aum, as_of) AS aum, arg_max(nav, as_of) AS nav, arg_max(price, as_of) AS price,
       arg_max(premium, as_of) AS premium, arg_max(units, as_of) AS units,
       arg_max(flow_1d, as_of) AS flow_1d
FROM ({flow_sql}) GROUP BY 1
"""
name_sql = f"""
SELECT regexp_replace(upper(CAST(fund_code AS VARCHAR)), '\\.TW(O)?','') AS fund,
       any_value(fund_name) AS fund_name, any_value(fund_type) AS fund_type,
       any_value(tracking_index) AS tracking_index, any_value(is_active) AS is_active
FROM read_parquet('{book}')
WHERE regexp_replace(upper(CAST(fund_code AS VARCHAR)), '\\.TW(O)?','') IN ({codes_n})
GROUP BY 1
"""
board_sql = f"""
SELECT n.fund, COALESCE(b.fund_name,'') AS fund_name, COALESCE(b.fund_type,'') AS fund_type,
       COALESCE(b.tracking_index,'') AS tracking_index, n.as_of, n.aum, n.nav, n.price,
       n.premium, n.units, n.flow_1d
FROM ({last_sql}) n LEFT JOIN ({name_sql}) b ON n.fund = b.fund
ORDER BY n.aum DESC NULLS LAST
"""
rows = con.execute(board_sql).fetchall()
cols = [d[0] for d in con.execute(board_sql).description]
print("BOARD", len(rows))
dest = os.path.join(lake, "year=2026"); os.makedirs(dest, exist_ok=True)
du = os.path.join(dest, "part-board.parquet").replace("\\","/")
con.execute(f"COPY ({board_sql}) TO '{du}' (FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)")
print("OK board", du)
net = 0.0
for r in rows:
    rec = dict(zip(cols, r))
    flow = rec.get("flow_1d") or 0
    net += float(flow)
    aum_e = (rec["aum"] or 0)/1e8
    prem = rec["premium"]
    prem_s = f"{prem*100:.2f}%" if prem is not None else "—"
    flow_e = (flow or 0)/1e8
    print(f"ROW {rec['fund']}\t{aum_e:.1f}億\t{prem_s}\t流{flow_e:.2f}億\t{rec['fund_name']}")
print("NETFLOW", net)
if vetf and os.path.isdir(vetf):
    for fn in sorted(os.listdir(vetf)):
        p = os.path.join(vetf, fn)
        sz = os.path.getsize(p) if os.path.isfile(p) else 0
        print("VETF", fn, sz)
else:
    print("NO vetf", vetf)

def cell(x):
    if x is None: return "—"
    if isinstance(x, float): return f"{x:.4g}"
    return html.escape(str(x))

trs = []
for r in rows:
    rec = dict(zip(cols, r))
    aum_e = (rec["aum"] or 0)/1e8
    prem = rec["premium"]
    pc = "g" if (prem or 0) < 0 else "y" if (prem or 0) > 0.04 else ""
    trs.append(
        "<tr><td>{}</td><td>{}</td><td>{:.1f}</td><td>{}</td><td>{}</td><td class='{}'>{:.2f}%</td><td>{:.2f}</td></tr>".format(
            rec["fund"], html.escape(rec["fund_name"] or ""), aum_e, rec["nav"], rec["price"],
            pc, (prem or 0)*100, (rec["flow_1d"] or 0)/1e8
        )
    )
doc = """<!doctype html><meta charset=utf-8><title>VIA AEA Board</title>
<style>
body{margin:0;background:#0e1116;color:#d7dde8;font:12px/1.35 Segoe UI,sans-serif}
h1{font-size:13px;margin:8px 12px;color:#8b93a7}
table{width:100%;border-collapse:collapse;table-layout:fixed}
td,th{border:1px solid #242a36;padding:3px 5px;word-wrap:break-word;overflow-wrap:anywhere}
th{background:#161b22;color:#8b93a7;font-size:11px;position:sticky;top:0}
.g{color:#3dd68c}.y{color:#e6b84d}
.z{font-size:10px;color:#8b93a7;margin:6px 12px}
</style>
<h1>VIA-AEA · 主動式台股 ETF 29 檔 · asOf 末列 · COPY_ONLY · LIVE 關</h1>
<p class=z>MODULE 宇宙29 · ENGINE DuckDB ⋈ book · FUNCTION-LIB stats NAV/流 · OTHERS 持股黃／px無00xxA／不造假</p>
<table><tr><th>代碼</th><th>名稱</th><th>AUM億</th><th>NAV</th><th>市價</th><th>溢價</th><th>末段流億</th></tr>
""" + "\n".join(trs) + "</table>"
os.makedirs(os.path.dirname(html_path), exist_ok=True)
open(html_path, "w", encoding="utf-8").write(doc)
print("HTML", html_path)
'@ | Set-Content $tf -Encoding utf8
Lamp 'GREEN' 'POLICY' '名冊⋈NAV · Δunits×NAV＝流 · 持股不造 · LIVE 關'
& $py $tf 2>&1 | ForEach-Object {
    $l = "$_"
    $c = if ($l -match '^OK|^ROW|^BOARD|^HTML') { 'GREEN' } elseif ($l -match '^NO|^MISS') { 'YELLOW' } else { 'GREY' }
    Lamp $c 'BOARD' $l
}
if (Test-Path $env:VIA_AETF_HTML) { Start-Process $env:VIA_AETF_HTML }
Lamp 'GREEN' 'SUM' '看板已寫 part-board.parquet · 封存未刪'
