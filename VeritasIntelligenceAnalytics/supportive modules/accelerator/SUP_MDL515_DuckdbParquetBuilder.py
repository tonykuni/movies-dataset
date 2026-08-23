from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv, html, json, re, sqlite3, traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# def PARAMETERS
BASE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP")
INPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_input")
OUTPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output")
REGISTRY_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_registry")
WAREHOUSE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse")
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932")

HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\VAP_DuckDB_Parquet_Warehouse_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\vap_duckdb_parquet_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\vap_duckdb_parquet_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\vap_duckdb_parquet_matrix.csv")
SQLITE_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_registry\\vap_intelligence_registry.sqlite")
DUCKDB_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\vap_intelligence.duckdb")
PARQUET_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\parquet")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\Invoke-VAP-DuckDB-Parquet-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_DUCKDB_PARQUET_20260506_221932\\vap_duckdb_parquet_builder.py")

MAX_SAMPLE_ROWS = int("50")
MAX_SCAN_FILES = int("2000")
ALLOWED_EXTS = {".csv",".json",".jsonl",".html",".htm",".parquet",".txt"}

@dataclass
class Asset:
    asset_id: str
    file_name: str
    path: str
    ext: str
    kind: str
    taxonomy: str
    size: int
    modified: str
    headers: List[str]
    header_count: int
    sample_rows: List[Dict[str, Any]]
    row_count_estimate: int
    best_template: str
    template_score: int
    status: str
    detail: str
    warning_reason: str
    axes: int
    supports_stack: bool
    supports_event_matrix: bool
    supports_heatmap: bool
    supports_candle: bool
    supports_watchlist: bool
    visual_lock: bool
    plotly_present: bool

def now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def safe_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def slug(v: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", v).strip("_")[:90] or "asset"

def write_json(p: Path, payload: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def kind(p: Path) -> str:
    return {".csv":"csv_table",".json":"json_data",".jsonl":"jsonl_data",".html":"html_template_or_report",".htm":"html_template_or_report",".parquet":"parquet_table",".txt":"text_data"}.get(p.suffix.lower(),"unknown")

def norm_headers(headers: List[str]) -> List[str]:
    return [re.sub(r"[^a-z0-9]+","_",str(h).lower()).strip("_") for h in headers]

def extract_csv(p: Path) -> Dict[str, Any]:
    last = ""
    for enc in ["utf-8-sig","utf-8","cp950","big5"]:
        try:
            rows, count = [], 0
            with p.open("r", encoding=enc, errors="replace", newline="") as f:
                sample = f.read(4096); f.seek(0)
                try: dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
                except Exception: dialect = csv.excel
                reader = csv.DictReader(f, dialect=dialect)
                headers = list(reader.fieldnames or [])
                for row in reader:
                    count += 1
                    if len(rows) < MAX_SAMPLE_ROWS:
                        rows.append({str(k): v for k, v in row.items()})
                return {"headers":headers,"sample_rows":rows,"row_count_estimate":count,"detail":"encoding="+enc}
        except Exception as exc:
            last = str(exc)
    return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"CSV_FAIL="+last}

def extract_json(p: Path) -> Dict[str, Any]:
    text = safe_text(p).strip()
    if not text:
        return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"EMPTY"}
    try:
        if p.suffix.lower() == ".jsonl":
            rows = [json.loads(x) for x in text.splitlines() if x.strip()]
            rows = [x for x in rows if isinstance(x, dict)]
            headers = sorted({str(k) for r in rows for k in r.keys()})
            return {"headers":headers,"sample_rows":rows[:MAX_SAMPLE_ROWS],"row_count_estimate":len(rows),"detail":"jsonl"}
        payload = json.loads(text)
        if isinstance(payload, list):
            rows = [x for x in payload if isinstance(x, dict)]
            headers = sorted({str(k) for r in rows for k in r.keys()})
            return {"headers":headers,"sample_rows":rows[:MAX_SAMPLE_ROWS],"row_count_estimate":len(rows),"detail":"json_list"}
        if isinstance(payload, dict):
            for key in ["data","rows","records","items","charts","pages"]:
                if isinstance(payload.get(key), list):
                    rows = [x for x in payload[key] if isinstance(x, dict)]
                    headers = sorted({str(k) for r in rows for k in r.keys()})
                    return {"headers":headers,"sample_rows":rows[:MAX_SAMPLE_ROWS],"row_count_estimate":len(rows),"detail":"json_dict_rows:"+key}
            return {"headers":sorted(map(str,payload.keys())),"sample_rows":[payload],"row_count_estimate":1,"detail":"json_dict"}
    except Exception as exc:
        return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"JSON_FAIL="+str(exc)}
    return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"JSON_UNKNOWN"}

def extract_html(p: Path) -> Dict[str, Any]:
    text = safe_text(p)
    m = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I|re.S)
    title = re.sub(r"\s+"," ",m.group(1)).strip() if m else p.stem
    ids = re.findall(r"id=[\"']([^\"']+)[\"']", text, flags=re.I)
    classes = re.findall(r"class=[\"']([^\"']+)[\"']", text, flags=re.I)
    anchors = re.findall(r"(?:ANCHOR|ANC|VIA:ANCHOR)[A-Za-z0-9:_\-\[\]]+", text)
    sample = {"title":title,"ids":", ".join(ids[:30]),"classes":", ".join(classes[:30]),"anchors":", ".join(anchors[:30]),"plotly_present":"plotly" in text.lower(),"script_count":len(re.findall(r"<script", text, flags=re.I))}
    return {"headers":["title","ids","classes","anchors","plotly_present","script_count"],"sample_rows":[sample],"row_count_estimate":1,"detail":"html_meta"}

def extract_parquet(p: Path) -> Dict[str, Any]:
    try:
        import pandas as pd
        df = pd.read_parquet(p)
        s = df.head(MAX_SAMPLE_ROWS).astype(object)
        s = s.where(pd.notnull(s), None)
        return {"headers":[str(c) for c in df.columns],"sample_rows":s.to_dict(orient="records"),"row_count_estimate":int(len(df)),"detail":"pandas_parquet"}
    except Exception as exc:
        return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"PARQUET_FAIL="+str(exc)}

def extract_text(p: Path) -> Dict[str, Any]:
    lines = safe_text(p).splitlines()
    first = lines[0] if lines else ""
    headers = [x.strip() for x in first.split(",")] if "," in first else ["line"]
    return {"headers":headers,"sample_rows":[{"line":x} for x in lines[:MAX_SAMPLE_ROWS]],"row_count_estimate":len(lines),"detail":"text"}

def extract_file(p: Path) -> Dict[str, Any]:
    ext = p.suffix.lower()
    if ext == ".csv": return extract_csv(p)
    if ext in [".json",".jsonl"]: return extract_json(p)
    if ext in [".html",".htm"]: return extract_html(p)
    if ext == ".parquet": return extract_parquet(p)
    if ext == ".txt": return extract_text(p)
    return {"headers":[],"sample_rows":[],"row_count_estimate":0,"detail":"unsupported"}

def html_signals(p: Path) -> Dict[str, bool]:
    text = safe_text(p); lower = text.lower(); file = p.name.lower()
    return {
        "plotly": "plotly" in lower,
        "newplot": "newplot" in lower,
        "yaxis2": bool(re.search(r"yaxis2|y2|right axis|left axis", lower)),
        "candlestick": bool(re.search(r"candlestick|ohlc|k線|kline|k-line|ma_bb|ta3", lower+" "+file)),
        "heatmap": bool(re.search(r"heatmap|熱力|matrix|multicompare", lower+" "+file)),
        "stack": bool(re.search(r"stack|verticalstack|lane|subplot|grid", lower+" "+file)),
        "timeline": bool(re.search(r"timeline|時間軸|eventmatrix|event matrix|事件", lower+" "+file)),
        "dashboard": bool(re.search(r"dashboard|watchlist|control_center|panel|card|ultimate", lower+" "+file)),
        "visual_lock": bool(re.search(r"visual lock|視覺鎖|veritas intelligence analytics", lower)),
        "registry": bool(re.search(r"registry|catalog|asset|template|marketplace", lower+" "+file)),
        "notes": bool(re.search(r"notes|notion|archive|archivum", lower+" "+file)),
        "dual_axis": bool(re.search(r"dual|雙軸|yaxis2|right axis|left axis|t02", lower+" "+file)),
        "single_axis": bool(re.search(r"singleaxis|single axis|單軸|t01", lower+" "+file)),
    }

def taxonomy(p: Path, k: str) -> str:
    if k != "html_template_or_report":
        return "DATA_ASSET" if k in ["csv_table","json_data","jsonl_data","parquet_table","text_data"] else "UNKNOWN_ASSET"
    s = html_signals(p); f = p.name.lower()
    if s["candlestick"]: return "HTML_PLOT_CANDLE_TA"
    if s["heatmap"] or "t04" in f: return "HTML_PLOT_HEATMAP"
    if s["dual_axis"]: return "HTML_PLOT_DUAL_AXIS"
    if s["stack"] or "t05" in f: return "HTML_PLOT_STACK_TIMELINE"
    if s["timeline"] or "t07" in f: return "HTML_PLOT_EVENT_MATRIX"
    if s["single_axis"]: return "HTML_PLOT_SINGLE_AXIS"
    if s["registry"]: return "HTML_REGISTRY_OR_CATALOG"
    if s["notes"]: return "HTML_ARCHIVE_OR_NOTES"
    if s["dashboard"]: return "HTML_DASHBOARD_UI"
    if s["plotly"] or s["newplot"]: return "HTML_PLOT_TEMPLATE"
    return "HTML_UI_TEMPLATE"

def plot_dna(p: Path, tx: str, k: str) -> Dict[str, Any]:
    s = html_signals(p) if k == "html_template_or_report" else {}
    axes = 2 if (s.get("yaxis2") or s.get("dual_axis") or tx == "HTML_PLOT_DUAL_AXIS") else 1
    return {"axes":axes,"supports_stack":bool(s.get("stack") or tx=="HTML_PLOT_STACK_TIMELINE"),"supports_event_matrix":bool(s.get("timeline") or tx=="HTML_PLOT_EVENT_MATRIX"),"supports_heatmap":bool(s.get("heatmap") or tx=="HTML_PLOT_HEATMAP"),"supports_candle":bool(s.get("candlestick") or tx=="HTML_PLOT_CANDLE_TA"),"supports_watchlist":bool(s.get("dashboard")),"visual_lock":bool(s.get("visual_lock")),"plotly_present":bool(s.get("plotly") or s.get("newplot"))}

def best_template(headers: List[str], tx: str) -> str:
    mapping = {
        "HTML_PLOT_CANDLE_TA":"VAP_TPL_CANDLE_TA_007",
        "HTML_PLOT_HEATMAP":"VAP_TPL_HEATMAP_006",
        "HTML_PLOT_DUAL_AXIS":"VAP_TPL_DUAL_AXIS_003",
        "HTML_PLOT_STACK_TIMELINE":"VAP_TPL_STACK_TIMELINE_004",
        "HTML_PLOT_EVENT_MATRIX":"VAP_TPL_EVENT_MATRIX_008",
        "HTML_PLOT_SINGLE_AXIS":"VAP_TPL_SINGLE_LINE_001",
        "HTML_DASHBOARD_UI":"VAP_TPL_DASHBOARD_UI_009",
        "HTML_REGISTRY_OR_CATALOG":"VAP_TPL_REGISTRY_UI_010",
        "HTML_ARCHIVE_OR_NOTES":"VAP_TPL_ARCHIVE_UI_011",
        "HTML_PLOT_TEMPLATE":"VAP_TPL_IMPORTED_PLOTLY_HTML",
        "HTML_UI_TEMPLATE":"VAP_TPL_IMPORTED_HTML_UI",
    }
    if tx in mapping: return mapping[tx]
    hs = set(norm_headers(headers))
    date_like = bool(hs & {"date","trade_date","time","datetime","normalized_date"})
    price_like = bool(hs & {"close","adj_close","adjclose","price","value","index"})
    volume_like = bool(hs & {"volume","vol","turnover"})
    flow_like = bool(hs & {"net_buy","net_amount","foreign_net","flow","dealer_net"})
    if {"x","y","z"} <= hs or "corr" in hs: return "VAP_TPL_HEATMAP_006"
    if {"x","y"} <= hs and not date_like: return "VAP_TPL_SCATTER_005"
    if date_like and price_like and (volume_like or flow_like): return "VAP_TPL_DUAL_AXIS_003"
    if date_like and len(headers) >= 4: return "VAP_TPL_STACK_TIMELINE_004"
    if volume_like or flow_like: return "VAP_TPL_SINGLE_BAR_002"
    return "VAP_TPL_SINGLE_LINE_001"

def template_score(headers: List[str], status: str, tx: str, dna: Dict[str, Any]) -> int:
    if tx.startswith("HTML_"):
        score = 78
        if dna.get("plotly_present"): score += 8
        if dna.get("visual_lock"): score += 7
        if dna.get("supports_stack") or dna.get("supports_event_matrix") or dna.get("supports_heatmap") or dna.get("supports_candle"): score += 5
        return min(100, score)
    hs = set(norm_headers(headers))
    score = 55
    if bool(hs & {"date","trade_date","datetime","time"}): score += 8
    if bool(hs & {"close","adj_close","adjclose","price","value","index"}): score += 8
    if bool(hs & {"volume","vol","turnover","flow","net_buy","net_amount"}): score += 8
    if status != "OK": score -= 20
    return max(0, min(100, score))

def scan_files() -> List[Path]:
    files = []
    for root in [INPUT_ROOT, BASE_ROOT]:
        if root.exists():
            for p in root.rglob("*"):
                if len(files) >= MAX_SCAN_FILES: break
                if p.is_file() and p.suffix.lower() in ALLOWED_EXTS:
                    sp = str(p).lower()
                    if "_output" in sp and root == BASE_ROOT: continue
                    if "_warehouse" in sp: continue
                    files.append(p)
    seen, out = set(), []
    for p in files:
        s = str(p).lower()
        if s not in seen:
            seen.add(s); out.append(p)
    return out

def build_assets() -> List[Asset]:
    assets = []
    for i, p in enumerate(scan_files(), 1):
        k = kind(p)
        e = extract_file(p)
        tx = taxonomy(p, k)
        dna = plot_dna(p, tx, k)
        best = best_template(e["headers"], tx)
        status = "OK" if e["headers"] else "WARN"
        score = template_score(e["headers"], status, tx, dna)
        warning = ""
        if tx.startswith("HTML_"):
            if score < 70: warning = "HTML_LOW_CONFIDENCE"
        else:
            if status != "OK": warning = e["detail"]
            elif score < 50: warning = "LOW_TEMPLATE_SCORE"
        assets.append(Asset(
            asset_id=f"VAP_DATA_{i:05d}_{slug(p.stem)}", file_name=p.name, path=str(p), ext=p.suffix.lower(),
            kind=k, taxonomy=tx, size=p.stat().st_size, modified=datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
            headers=e["headers"], header_count=len(e["headers"]), sample_rows=e["sample_rows"], row_count_estimate=int(e["row_count_estimate"]),
            best_template=best, template_score=score, status=status, detail=e["detail"], warning_reason=warning,
            axes=int(dna["axes"]), supports_stack=bool(dna["supports_stack"]), supports_event_matrix=bool(dna["supports_event_matrix"]),
            supports_heatmap=bool(dna["supports_heatmap"]), supports_candle=bool(dna["supports_candle"]), supports_watchlist=bool(dna["supports_watchlist"]),
            visual_lock=bool(dna["visual_lock"]), plotly_present=bool(dna["plotly_present"])
        ))
    return assets

def write_sqlite(assets: List[Asset]) -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(SQLITE_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS asset_registry (asset_id TEXT PRIMARY KEY, file_name TEXT, path TEXT, ext TEXT, kind TEXT, taxonomy TEXT, size INTEGER, modified TEXT, headers_json TEXT, header_count INTEGER, sample_json TEXT, row_count_estimate INTEGER, best_template TEXT, template_score INTEGER, status TEXT, detail TEXT, warning_reason TEXT, axes INTEGER, supports_stack INTEGER, supports_event_matrix INTEGER, supports_heatmap INTEGER, supports_candle INTEGER, supports_watchlist INTEGER, visual_lock INTEGER, plotly_present INTEGER, indexed_at TEXT)")
    now_s = now()
    for a in assets:
        con.execute("INSERT OR REPLACE INTO asset_registry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            a.asset_id, a.file_name, a.path, a.ext, a.kind, a.taxonomy, a.size, a.modified, json.dumps(a.headers, ensure_ascii=False), a.header_count,
            json.dumps(a.sample_rows, ensure_ascii=False, default=str), a.row_count_estimate, a.best_template, a.template_score, a.status, a.detail, a.warning_reason,
            a.axes, int(a.supports_stack), int(a.supports_event_matrix), int(a.supports_heatmap), int(a.supports_candle), int(a.supports_watchlist), int(a.visual_lock), int(a.plotly_present), now_s
        ))
    con.commit(); con.close()

def assets_df(assets: List[Asset]):
    import pandas as pd
    rows = []
    for a in assets:
        d = asdict(a)
        d["headers_json"] = json.dumps(a.headers, ensure_ascii=False)
        d["sample_json"] = json.dumps(a.sample_rows, ensure_ascii=False, default=str)
        d.pop("headers", None); d.pop("sample_rows", None)
        rows.append(d)
    return pd.DataFrame(rows)

def write_duckdb_parquet(assets: List[Asset]) -> Dict[str, Any]:
    import duckdb
    df = assets_df(assets)
    taxonomy_df = df.groupby("taxonomy", dropna=False).size().reset_index(name="asset_count").sort_values("asset_count", ascending=False)
    warning_df = df[df["warning_reason"].fillna("") != ""].copy()
    plot_dna_df = df[["asset_id","file_name","taxonomy","best_template","axes","supports_stack","supports_event_matrix","supports_heatmap","supports_candle","supports_watchlist","visual_lock","plotly_present"]].copy()
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    PARQUET_ROOT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE OR REPLACE TABLE asset_registry AS SELECT * FROM df")
    con.execute("CREATE OR REPLACE TABLE taxonomy_summary AS SELECT * FROM taxonomy_df")
    con.execute("CREATE OR REPLACE TABLE warning_assets AS SELECT * FROM warning_df")
    con.execute("CREATE OR REPLACE TABLE plot_dna_registry AS SELECT * FROM plot_dna_df")
    for table, fname in [("asset_registry","asset_registry.parquet"),("taxonomy_summary","taxonomy_summary.parquet"),("warning_assets","warning_assets.parquet"),("plot_dna_registry","plot_dna_registry.parquet")]:
        out = str(PARQUET_ROOT / fname).replace("\\", "/")
        con.execute(f"COPY {table} TO '{out}' (FORMAT PARQUET)")
    con.close()
    return {"tables":["asset_registry","taxonomy_summary","warning_assets","plot_dna_registry"],"parquet_files":[str(PARQUET_ROOT / x) for x in ["asset_registry.parquet","taxonomy_summary.parquet","warning_assets.parquet","plot_dna_registry.parquet"]]}

def write_csv(assets: List[Asset]) -> None:
    MATRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["asset_id","file_name","path","ext","kind","taxonomy","header_count","headers","row_count_estimate","best_template","template_score","status","detail","warning_reason","axes","supports_stack","supports_event_matrix","supports_heatmap","supports_candle","supports_watchlist","visual_lock","plotly_present"]
    with MATRIX_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for a in assets:
            d = asdict(a); d["headers"] = " | ".join(a.headers)
            w.writerow({k:d.get(k,"") for k in fields})

def write_refresh() -> None:
    content = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "{PYTHON_EXE}"
$Builder = "{BUILDER_PY}"
$Html = "{HTML_PATH}"
Write-Host ""
Write-Host "Refreshing VAP DuckDB + Parquet Warehouse..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {{
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
}} else {{
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}}
"""
    REFRESH_PS1.write_text(content, encoding="utf-8-sig")

def write_html(assets: List[Asset], summary: Dict[str, Any]) -> None:
    tax = {}
    for a in assets: tax[a.taxonomy] = tax.get(a.taxonomy,0)+1
    tax_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k,v in sorted(tax.items(), key=lambda kv:kv[1], reverse=True))
    warns = [a for a in assets if a.warning_reason]
    warn_list = "".join(f"<li><code>{html.escape(a.file_name)}</code> — {html.escape(a.taxonomy)} — {html.escape(a.warning_reason)}</li>" for a in warns[:60]) or "<li>None</li>"
    rows = ""
    for a in assets[:800]:
        cls = "ok" if not a.warning_reason else "warn"
        rows += f"<tr><td><code>{html.escape(a.asset_id)}</code></td><td>{html.escape(a.file_name)}</td><td>{html.escape(a.taxonomy)}</td><td>{html.escape(a.best_template)}</td><td>{a.template_score}</td><td>{a.axes}</td><td>{a.visual_lock}</td><td>{a.plotly_present}</td><td><span class='badge {cls}'>{'OK' if not a.warning_reason else 'WARN'}</span></td><td>{html.escape(a.warning_reason)}</td></tr>"
    parquet_list = "".join(f"<li><code>{html.escape(p)}</code></li>" for p in summary.get("parquet_files", []))
    warn_class = "ok" if summary.get("warnings",0)==0 else "warn"
    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VAP DuckDB Parquet Warehouse</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1760px;margin:0 auto;padding:14px}}.hero{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:8px;margin-bottom:10px}}.grid2{{display:grid;grid-template-columns:380px 1fr;gap:10px}}@media(max-width:1100px){{.grid2{{grid-template-columns:1fr}}}}.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--blue);border-radius:10px;padding:10px}}.kpi.ok{{border-left-color:var(--green)}}.kpi.warn{{border-left-color:var(--amber)}}.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}table{{width:100%;border-collapse:collapse;font-size:11px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}tr:hover{{background:rgba(76,120,168,.04)}}code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}.badge{{padding:2px 6px;border-radius:5px;font-family:Consolas,monospace;font-size:9px;font-weight:800}}.badge.ok{{background:#d8ecd8;color:var(--green)}}.badge.warn{{background:#f3dfb4;color:var(--amber)}}.progress{{height:7px;background:#e3e0d8;border-radius:99px;overflow:hidden;margin-top:8px}}.bar{{height:100%;width:{summary.get('quality_score',0)}%;background:linear-gradient(90deg,var(--blue),var(--teal),var(--green));animation:load 1s ease-out}}@keyframes load{{from{{width:0}}}}
</style></head><body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Intelligence Warehouse · DuckDB + Parquet</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Windows I/O · Asset Taxonomy · Plot DNA · DuckDB · Parquet</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div style="font-size:20px;color:var(--green);font-weight:900">WAREHOUSE READY</div></div></div>
<div class="grid"><div class="kpi ok"><div class="k">Assets</div><div class="v">{summary.get('assets',0)}</div></div><div class="kpi ok"><div class="k">Quality</div><div class="v">{summary.get('quality_score',0)}%</div></div><div class="kpi {warn_class}"><div class="k">Warnings</div><div class="v">{summary.get('warnings',0)}</div></div><div class="kpi ok"><div class="k">Avg Score</div><div class="v">{summary.get('avg_template_score',0)}</div></div><div class="kpi ok"><div class="k">DuckDB Tables</div><div class="v">{len(summary.get('duckdb_tables',[]))}</div></div><div class="kpi ok"><div class="k">Parquet Files</div><div class="v">{len(summary.get('parquet_files',[]))}</div></div></div>
<div class="card"><b>Dynamic Quality Progress</b><div class="progress"><div class="bar"></div></div></div>
<div class="grid2"><div class="card"><b>Taxonomy Groups</b><div style="overflow:auto;max-height:460px"><table><thead><tr><th>Taxonomy</th><th>Count</th></tr></thead><tbody>{tax_rows}</tbody></table></div></div><div class="card"><b>Warnings</b><ol>{warn_list}</ol></div></div>
<div class="card"><b>DuckDB</b><br><code>{html.escape(summary.get('duckdb_path',''))}</code></div><div class="card"><b>Parquet Outputs</b><ol>{parquet_list}</ol></div><div class="card"><b>Refresh Launcher</b><br><code>{html.escape(str(REFRESH_PS1))}</code></div>
<div class="card"><b>Plot DNA / Warehouse Matrix</b><div style="overflow:auto;max-height:760px"><table><thead><tr><th>Asset ID</th><th>File</th><th>Taxonomy</th><th>Best Template</th><th>Score</th><th>Axes</th><th>Visual Lock</th><th>Plotly</th><th>Status</th><th>Warning</th></tr></thead><tbody>{rows}</tbody></table></div></div>
</div></body></html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")

def main() -> int:
    for p in [BASE_ROOT,INPUT_ROOT,OUTPUT_ROOT,REGISTRY_ROOT,WAREHOUSE_ROOT,PARQUET_ROOT,RUN_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    assets = build_assets()
    write_sqlite(assets)
    write_csv(assets)
    wh = write_duckdb_parquet(assets)
    write_refresh()
    warnings = [a for a in assets if a.warning_reason]
    avg_score = int(round(sum(a.template_score for a in assets) / max(1, len(assets))))
    quality = int(round(100 * (len(assets) - len(warnings)) / max(1, len(assets))))
    summary = {"generated_at":now(),"run_dir":str(RUN_DIR),"base_root":str(BASE_ROOT),"input_root":str(INPUT_ROOT),"sqlite_path":str(SQLITE_PATH),"duckdb_path":str(DUCKDB_PATH),"parquet_root":str(PARQUET_ROOT),"html_path":str(HTML_PATH),"matrix_csv":str(MATRIX_CSV),"payload_json":str(PAYLOAD_JSON),"refresh_ps1":str(REFRESH_PS1),"assets":len(assets),"warnings":len(warnings),"avg_template_score":avg_score,"quality_score":quality,"duckdb_tables":wh["tables"],"parquet_files":wh["parquet_files"],"warning_files":[{"file_name":a.file_name,"taxonomy":a.taxonomy,"warning_reason":a.warning_reason,"path":a.path} for a in warnings]}
    payload = {"summary":summary,"assets":[asdict(a) for a in assets],"plot_dna_registry":[{"asset_id":a.asset_id,"file_name":a.file_name,"taxonomy":a.taxonomy,"best_template":a.best_template,"axes":a.axes,"supports_stack":a.supports_stack,"supports_event_matrix":a.supports_event_matrix,"supports_heatmap":a.supports_heatmap,"supports_candle":a.supports_candle,"supports_watchlist":a.supports_watchlist,"visual_lock":a.visual_lock,"plotly_present":a.plotly_present} for a in assets]}
    write_json(SUMMARY_JSON, summary)
    write_json(PAYLOAD_JSON, payload)
    write_html(assets, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as sx:
        if getattr(sx, "code", 0) not in (0, None):
            raise
    except BaseException:
        print(traceback.format_exc())
        raise
