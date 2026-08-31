# -*- coding: utf-8 -*-
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

import csv
import hashlib
import html
import json
import os
import re
import shutil
import time
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_VERSION = "VRN_UNIFIED_OPERATION_DB_UI_V0582"

TW_TICKER_REGEX = re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")
DATE_YYYYMMDD = re.compile(r"(20\d{2})([01]\d)([0-3]\d)")
DATE_YYMMDD = re.compile(r"(?<!\d)([2-9]\d)([01]\d)([0-3]\d)(?!\d)")
DATE_ROC = re.compile(r"(?<!\d)(1\d{2})([01]\d)([0-3]\d)(?!\d)")

STATE = {
    "base": "",
    "vrn_root": "",
    "canonical_dir": "",
    "stable_dir": "",
    "run_dir": "",
    "preview_duckdb": "",
    "port": 8788,
    "logs": [],
    "progress": 0,
    "status": "READY",
    "input_files": [],
    "duplicates": [],
    "db_source": {},
    "db_views": [],
    "counts": {},
}


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_log(level: str, msg: str) -> None:
    STATE["logs"].append({"time": def_now(), "level": level, "message": msg})
    STATE["logs"] = STATE["logs"][-500:]


def def_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_hash_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:20].upper()


def def_ensure_base(base: str) -> dict:
    b = Path(base).expanduser()
    dirs = {
        "base": b,
        "input": b / "input",
        "temp": b / "temp",
        "output": b / "output",
        "db": b / "db",
        "logs": b / "logs",
        "queue": b / "queue",
        "archive": b / "archive",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    STATE["base"] = str(b)
    def_log("OK", f"BASE ready: {b}")
    return {k: str(v) for k, v in dirs.items()}


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_count_csv(path: Path) -> int:
    rows = def_read_csv(path)
    if len(rows) == 1 and not any((v or "").strip() for v in rows[0].values()):
        return 0
    return len(rows)


def def_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_normalize_filename(name: str) -> str:
    stem = Path(name).stem
    s = re.sub(r"[()\[\]{}【】（）,，、_＋+％%\-—–:：;；.。/\\|]", " ", stem)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def def_tokens(name: str) -> list[str]:
    return re.findall(r"[A-Za-z]+|\d+|[\u4e00-\u9fff]+", def_normalize_filename(name))


def def_parse_ticker(tokens: list[str]) -> str:
    for t in tokens:
        if TW_TICKER_REGEX.match(t):
            return t
    return ""


def def_parse_report_date(filename: str) -> tuple[str, str]:
    s = def_normalize_filename(filename)

    m = DATE_YYYYMMDD.search(s)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo}-{d}", "YYYYMMDD"

    m = DATE_ROC.search(s)
    if m:
        y, mo, d = m.groups()
        return f"{int(y)+1911:04d}-{mo}-{d}", "ROCYYYMMDD"

    m = DATE_YYMMDD.search(s)
    if m:
        yy, mo, d = m.groups()
        return f"20{yy}-{mo}-{d}", "YYMMDD"

    return "", ""


def def_parse_broker(tokens: list[str]) -> str:
    text = " ".join(tokens).lower()
    broker_map = {
        "CATHAY": ["cathay", "國泰"],
        "CLSA": ["clsa", "clst"],
        "DAIWA": ["daiwa"],
        "GS": ["gs", "goldman"],
        "JPM": ["jp", "jpm", "jpmorgan"],
        "MS": ["ms", "morgan"],
        "CTBC": ["ctbc", "中信"],
        "HUANAN": ["huanan", "華南"],
        "MEGA": ["mega", "兆豐"],
    }
    for broker, keys in broker_map.items():
        for k in keys:
            if k in text:
                return broker
    return ""


def def_file_record(path: Path) -> dict:
    toks = def_tokens(path.name)
    ticker = def_parse_ticker(toks)
    report_date, date_kind = def_parse_report_date(path.name)
    broker = def_parse_broker(toks)
    stat = path.stat()
    dup_key = f"{stat.st_size}|{ticker}|{broker}|{report_date}"

    return {
        "Filename": path.name,
        "Path": str(path),
        "Extension": path.suffix.lower(),
        "Size": stat.st_size,
        "SHA20": def_hash_file(path),
        "Filename Normalized": def_normalize_filename(path.name),
        "Filename Tokens": " | ".join(toks),
        "Ticker Parsed": ticker,
        "Broker Parsed": broker,
        "Report Date Parsed": report_date,
        "Report Date Kind": date_kind,
        "Duplicate Key": dup_key,
        "Duplicate Group": "",
        "Duplicate Warning": "",
        "Input Status": "READY",
    }


def def_scan_input(base: str, extra_paths: list[str]) -> dict:
    STATE["progress"] = 10
    dirs = def_ensure_base(base)
    input_dir = Path(dirs["input"])
    allowed = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

    paths = []
    for p in input_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in allowed:
            paths.append(p)

    for raw in extra_paths:
        p = Path(raw).expanduser()
        if p.is_file() and p.suffix.lower() in allowed:
            paths.append(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in allowed:
                    paths.append(f)

    seen = set()
    unique = []
    for p in paths:
        try:
            k = str(p.resolve()).lower()
        except Exception:
            k = str(p).lower()
        if k not in seen:
            seen.add(k)
            unique.append(p)

    rows = [def_file_record(p) for p in unique]

    groups = {}
    for r in rows:
        groups.setdefault(r["Duplicate Key"], []).append(r)

    duplicates = []
    gid = 0
    for k, grp in groups.items():
        if len(grp) > 1:
            gid += 1
            for r in grp:
                r["Duplicate Group"] = f"DUP-{gid:03d}"
                r["Duplicate Warning"] = "SIZE/TICKER/BROKER/DATE duplicated"
                duplicates.append(r)

    STATE["input_files"] = rows
    STATE["duplicates"] = duplicates
    STATE["progress"] = 30
    def_log("OK", f"Input scanned: files={len(rows)}, duplicates={len(duplicates)}")

    return {
        "dirs": dirs,
        "files": rows,
        "duplicates": duplicates,
        "counts": {
            "files": len(rows),
            "duplicates": len(duplicates),
            "pdf": sum(1 for r in rows if r["Extension"] == ".pdf"),
            "word": sum(1 for r in rows if r["Extension"] in {".doc", ".docx"}),
            "image": sum(1 for r in rows if r["Extension"] in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}),
        },
    }


def def_find_db_source(base: str) -> dict:
    base_path = Path(base)
    canonical_dir = Path(STATE["canonical_dir"])
    stable_dir = Path(STATE["stable_dir"])

    candidates = []

    def add_candidate(label: str, root: Path):
        candidates.append({
            "label": label,
            "root": root,
            "basic": root / "vrn_basicinfo_active.csv",
            "financial": root / "vrn_financial_active.csv",
            "data_trust": root / "vrn_data_trust_active.csv",
            "accepted": root / "vrn_data_trust_accepted_active.csv",
            "official_review": root / "vrn_official_coverage_review_active.csv",
            "external_optional": root / "vrn_external_optional_active.csv",
            "review_required": root / "vrn_review_required_active.csv",
            "system_error": root / "vrn_system_hard_error_active.csv",
            "duckdb": root / "vrn_active.duckdb",
        })

    add_candidate("BASE_CANONICAL_ACTIVE", base_path / "_vrn_canonical_active")
    add_candidate("GLOBAL_CANONICAL_ACTIVE", canonical_dir)
    add_candidate("STABLE_RELEASE", stable_dir)

    for c in candidates:
        if c["basic"].exists() and c["financial"].exists() and c["data_trust"].exists():
            STATE["db_source"] = {k: str(v) if isinstance(v, Path) else v for k, v in c.items()}
            def_log("OK", f"DB source selected: {c['label']}")
            return STATE["db_source"]

    STATE["db_source"] = {k: str(v) if isinstance(v, Path) else v for k, v in candidates[-1].items()}
    def_log("WARN", "No full DB source found; fallback stable paths assigned.")
    return STATE["db_source"]


def def_safe_df(rows: list[dict]):
    import pandas as pd
    if not rows:
        rows = [{"Status": "EMPTY"}]
    clean = []
    for r in rows:
        clean.append({str(k): "" if v is None else str(v) for k, v in r.items()})
    return pd.DataFrame(clean)


def def_build_preview_db(source: dict) -> tuple[bool, str, list[dict]]:
    try:
        import duckdb
        preview = Path(STATE["preview_duckdb"])
        preview.parent.mkdir(parents=True, exist_ok=True)

        tables = {
            "basicinfo_active_table": def_read_csv(Path(source["basic"])),
            "financial_active_table": def_read_csv(Path(source["financial"])),
            "data_trust_active_table": def_read_csv(Path(source["data_trust"])),
            "accepted_active_table": def_read_csv(Path(source["accepted"])),
            "official_review_queue_table": def_read_csv(Path(source["official_review"])),
            "external_optional_active_table": def_read_csv(Path(source["external_optional"])),
            "review_required_active_table": def_read_csv(Path(source["review_required"])),
            "system_error_active_table": def_read_csv(Path(source["system_error"])),
        }

        con = duckdb.connect(str(preview))
        con.execute("CREATE SCHEMA IF NOT EXISTS vrn;")

        for name, rows in tables.items():
            df = def_safe_df(rows)
            con.register("df_temp", df)
            con.execute(f"CREATE OR REPLACE TABLE vrn.{name} AS SELECT * FROM df_temp;")
            con.unregister("df_temp")

        view_sql = {
            "vrn.basicinfo_active": "vrn.basicinfo_active_table",
            "vrn.financial_active": "vrn.financial_active_table",
            "vrn.data_trust_active": "vrn.data_trust_active_table",
            "vrn.accepted_active": "vrn.accepted_active_table",
            "vrn.official_review_queue": "vrn.official_review_queue_table",
            "vrn.external_optional_active": "vrn.external_optional_active_table",
            "vrn.review_required_active": "vrn.review_required_active_table",
            "vrn.system_error_active": "vrn.system_error_active_table",
        }

        for view, table in view_sql.items():
            con.execute(f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM {table};")

        view_rows = []
        ok = True
        for view in view_sql:
            try:
                cnt = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
                view_rows.append({"View": view, "Rows": cnt, "Status": "OK", "Severity": "OK", "Detail": ""})
            except Exception as e:
                ok = False
                view_rows.append({"View": view, "Rows": "", "Status": "ERR", "Severity": "ERR", "Detail": str(e)})

        con.close()
        STATE["db_views"] = view_rows
        return ok, "", view_rows

    except Exception as e:
        return False, str(e), [{"View": "preview_db", "Rows": "", "Status": "ERR", "Severity": "ERR", "Detail": str(e)}]


def def_refresh_all(base: str, extra_paths: list[str]) -> dict:
    STATE["status"] = "RUNNING"
    STATE["progress"] = 5
    scan = def_scan_input(base, extra_paths)
    source = def_find_db_source(base)
    STATE["progress"] = 50
    ok, err, views = def_build_preview_db(source)
    STATE["progress"] = 80

    counts = {
        "input_files": len(STATE["input_files"]),
        "duplicates": len(STATE["duplicates"]),
        "basic_rows": def_count_csv(Path(source["basic"])),
        "financial_rows": def_count_csv(Path(source["financial"])),
        "accepted_rows": def_count_csv(Path(source["accepted"])),
        "official_review_rows": def_count_csv(Path(source["official_review"])),
        "external_optional_rows": def_count_csv(Path(source["external_optional"])),
        "review_required_rows": def_count_csv(Path(source["review_required"])),
        "system_error_rows": def_count_csv(Path(source["system_error"])),
    }

    validation = [
        {"Gate": "READ_ONLY_DISPLAY", "Value": True, "Severity": "OK", "Detail": "Only preview DB in RUN_DIR is created."},
        {"Gate": "DB_SOURCE", "Value": source.get("label", ""), "Severity": "OK", "Detail": source.get("root", "")},
        {"Gate": "INPUT_FILES", "Value": counts["input_files"], "Severity": "OK"},
        {"Gate": "DUPLICATES", "Value": counts["duplicates"], "Severity": "WARN" if counts["duplicates"] else "OK"},
        {"Gate": "BASIC_ROWS", "Value": counts["basic_rows"], "Severity": "OK" if counts["basic_rows"] else "ERR"},
        {"Gate": "FINANCIAL_ROWS", "Value": counts["financial_rows"], "Severity": "OK" if counts["financial_rows"] else "ERR"},
        {"Gate": "ACCEPTED_ROWS", "Value": counts["accepted_rows"], "Severity": "OK"},
        {"Gate": "OFFICIAL_REVIEW_ROWS", "Value": counts["official_review_rows"], "Severity": "WARN" if counts["official_review_rows"] else "OK"},
        {"Gate": "EXTERNAL_OPTIONAL_ROWS", "Value": counts["external_optional_rows"], "Severity": "OK"},
        {"Gate": "REVIEW_REQUIRED_ROWS", "Value": counts["review_required_rows"], "Severity": "OK" if counts["review_required_rows"] == 0 else "ERR"},
        {"Gate": "SYSTEM_ERROR_ROWS", "Value": counts["system_error_rows"], "Severity": "OK" if counts["system_error_rows"] == 0 else "ERR"},
        {"Gate": "PREVIEW_DB_VIEWS", "Value": ok, "Severity": "OK" if ok else "ERR", "Detail": err},
    ]

    result = {
        "version": APP_VERSION,
        "generated_at": def_now(),
        "base": base,
        "mode": "UNIFIED_INPUT_AND_DB_PREVIEW_READ_ONLY",
        "db_source": source,
        "preview_duckdb": STATE["preview_duckdb"],
        "counts": counts,
        "validation": validation,
        "views": views,
        "scan": scan,
        "preview_pass": bool(ok and counts["basic_rows"] > 0 and counts["financial_rows"] > 0 and counts["review_required_rows"] == 0 and counts["system_error_rows"] == 0),
        "rule_lock": [
            "Changing BASE refreshes input scan and DB preview.",
            "Preview DB is generated only in RUN_DIR.",
            "No formal Parquet/CSV/DuckDB/GoogleSheet output.",
            "No stable release mutation.",
            "No canonical mutation.",
            "No Summarizer.",
            "No classifier rewrite.",
        ],
    }

    STATE["counts"] = counts
    STATE["progress"] = 100
    STATE["status"] = "DONE" if result["preview_pass"] else "REVIEW"
    def_log("OK" if result["preview_pass"] else "WARN", f"Refresh completed. preview_pass={result['preview_pass']}")
    return result


def def_sample(rows: list[dict], n: int = 500) -> list[dict]:
    return rows[:n]


HTML = r'''
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN Unified Operation + DB Preview UI v05.8.2</title>
<style>
:root{
  --bg:#f5f4f0;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bl:#4c78a8;--tl:#439a9a;
  --gn:#5a9e6f;--gn-l:#cde8d5;--am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;
  --vi:#7a6daa;--i0:#1e1d1a;--i2:#6b6860;--i3:#9c9890;--mo:Consolas,monospace;--sa:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:var(--sa);font-size:11px;color:var(--i0)}
.wrap{max-width:1760px;margin:0 auto;padding:12px}
.hdr{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:16px 18px;margin-bottom:10px;display:flex;gap:12px;align-items:center;position:relative;overflow:hidden}
.hdr:before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}
.logo{width:42px;height:42px;border-radius:12px;background:#1e3a5f;color:#8dcff0;display:flex;align-items:center;justify-content:center;font-weight:900;font-family:var(--mo)}
.h1{font-size:20px;font-weight:850;letter-spacing:-.5px}.h1 span{color:var(--bl)}.sub{font-size:10px;color:var(--i3);margin-top:2px}
.tabs{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}
.tabs button,.btn{border:1px solid var(--bd);background:var(--sf);border-radius:999px;padding:8px 14px;font-weight:750;font-size:11px;cursor:pointer;transition:.16s;color:var(--i2)}
.tabs button:hover,.btn:hover{transform:translateY(-1px);box-shadow:0 8px 18px rgba(30,29,26,.08);border-color:var(--bl);color:var(--bl)}
.tabs button.on,.btn.primary{background:var(--bl);border-color:var(--bl);color:white}
.tabs button:active,.btn:active{transform:scale(.96)}
.page{display:none}.page.on{display:block}
.layout{display:grid;grid-template-columns:360px 1fr;gap:10px}@media(max-width:1100px){.layout{grid-template-columns:1fr}}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:16px;margin-bottom:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.035)}
.card h3{margin:0;padding:10px 12px;background:var(--sf2);border-bottom:1px solid var(--bd);font-size:12px;display:flex;justify-content:space-between}
.body{padding:10px 12px}
.input{width:100%;border:1px solid var(--bd);border-radius:9px;padding:8px 10px;font-family:var(--mo);font-size:11px;background:white;outline:none;transition:.15s}
.input:focus{border-color:var(--bl);box-shadow:0 0 0 3px rgba(76,120,168,.12)}
.row{display:flex;gap:6px;align-items:center;margin-bottom:7px}.row>*{flex:1}
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(115px,1fr));gap:8px;margin-bottom:10px}
.stat{background:var(--sf);border:1px solid var(--bd);border-radius:14px;padding:10px;transition:.15s}
.stat:hover{transform:translateY(-1px);box-shadow:0 8px 18px rgba(0,0,0,.06)}
.stat .n{text-align:right;font-family:var(--mo);font-size:20px;font-weight:900}.stat .l{text-align:center;color:var(--i3);font-size:9px;text-transform:uppercase}
.progress{height:8px;background:#e6e3dd;border-radius:999px;overflow:hidden}.bar{height:100%;width:0%;background:linear-gradient(90deg,var(--bl),var(--tl));transition:width .25s}
.drop{border:2px dashed #c8c4ba;background:var(--sf2);border-radius:14px;padding:18px;text-align:center;transition:.18s}
.drop:hover,.drop.over{background:#d0e1f0;border-color:var(--bl);transform:scale(1.005)}
.tablewrap{overflow:auto;max-height:72vh;border:1px solid var(--bd);border-radius:9px;resize:vertical}
table{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px}
th{position:sticky;top:0;background:#ef0000;color:white;padding:7px;border:1px solid var(--bd);text-align:center;vertical-align:top;z-index:1}
td{padding:5px 7px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;max-width:460px}
td.left{text-align:left;min-width:260px}td.center{text-align:center}td.num{text-align:right;font-family:var(--mo);white-space:nowrap}
tr.green td{background:var(--gn-l)}tr.yellow td{background:var(--am-l)}tr.red td{background:var(--co-l)}
.terminal{background:#1e1d1a;color:#c9d1d9;border-radius:14px;overflow:hidden;border:1px solid #333;font-family:var(--mo)}
.tbar{background:#2a2924;padding:8px 10px;color:#8b949e;text-align:center;font-size:9px}
.tbody{padding:10px;max-height:245px;overflow:auto;line-height:1.65}.oktxt{color:#3fb950}.warntxt{color:#d29922}.errtxt{color:#f85149}.dim{color:#8b949e}
.badge{font-family:var(--mo);font-size:9px;border-radius:4px;padding:2px 6px;background:#edecea;color:var(--i2)}
.kv{display:grid;grid-template-columns:110px 1fr;gap:8px;border-bottom:1px solid var(--bd);padding:6px 0}.kv span{font-family:var(--mo);overflow-wrap:anywhere}
pre{background:#1e1d1a;color:#d1fae5;border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="logo">VRN</div>
    <div style="flex:1">
      <div class="h1"><span>VeritasReportNova</span> Unified Operation + DB Preview UI <span style="font-size:12px;color:var(--i3)">v05.8.2</span></div>
      <div class="sub">BASE refresh · input matrix · duplicate review · transformed DB preview · validation status · no formal output</div>
    </div>
    <button class="btn primary" onclick="refreshAll()">重新整理 BASE + DB</button>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_input" onclick="tab('input')">02 Input Matrix</button>
    <button id="b_duplicate" onclick="tab('duplicate')">03 Duplicate</button>
    <button id="b_basic" onclick="tab('basic')">04 BasicInfo DB</button>
    <button id="b_financial" onclick="tab('financial')">05 Financial DB</button>
    <button id="b_trust" onclick="tab('trust')">06 Trust</button>
    <button id="b_queue" onclick="tab('queue')">07 Official Queue</button>
    <button id="b_views" onclick="tab('views')">08 DB Views</button>
    <button id="b_logs" onclick="tab('logs')">09 Logs</button>
  </div>

  <div id="overview" class="page on">
    <div class="layout">
      <div>
        <div class="card">
          <h3>BASE 設定 <span class="badge" id="sourceBadge">READY</span></h3>
          <div class="body">
            <div class="row"><input id="base" class="input" value="__BASE__"><button class="btn primary" onclick="confirmBase()">確認</button></div>
            <div class="row"><button class="btn" onclick="browseBase()">Window I/O 選 BASE</button><button class="btn" onclick="refreshAll()">重新擷取/轉化預覽</button></div>
            <div class="kv"><b>Mode</b><span>Preview only · no formal output</span></div>
            <div class="kv"><b>Stable</b><span id="stableText"></span></div>
            <div class="kv"><b>Preview DB</b><span id="previewDbText"></span></div>
          </div>
        </div>

        <div class="card">
          <h3>增加輸入 <span class="badge">PDF / Word / Image</span></h3>
          <div class="body">
            <div id="drop" class="drop" ondragover="event.preventDefault();this.classList.add('over')" ondragleave="this.classList.remove('over')" ondrop="dropFiles(event)">
              <div style="font-size:26px">📥</div>
              <b>拖曳檔案或資料夾到這裡</b>
              <div style="font-size:9px;color:var(--i3)">瀏覽器可能只給檔名；完整路徑用 Window I/O 或手動貼上</div>
            </div>
            <div class="row" style="margin-top:8px"><input id="manualPath" class="input" placeholder="貼上完整檔案/資料夾路徑"><button class="btn" onclick="addPath()">加入</button></div>
            <div class="row"><button class="btn" onclick="browseFile()">Window I/O 選檔</button><button class="btn" onclick="browseFolder()">Window I/O 選資料夾</button></div>
            <div id="pathList" style="font-family:var(--mo);font-size:10px;color:var(--i2)"></div>
          </div>
        </div>

        <div class="card">
          <h3>Live Progress</h3>
          <div class="body">
            <div style="display:flex;justify-content:space-between"><span id="progLabel">READY</span><span id="progPct">0%</span></div>
            <div class="progress"><div id="bar" class="bar"></div></div>
          </div>
        </div>
      </div>

      <div>
        <div class="statgrid">
          <div class="stat"><div class="n" id="stInput">0</div><div class="l">Input Files</div></div>
          <div class="stat"><div class="n" id="stDup">0</div><div class="l">Duplicates</div></div>
          <div class="stat"><div class="n" id="stBasic">0</div><div class="l">Basic Rows</div></div>
          <div class="stat"><div class="n" id="stFin">0</div><div class="l">Financial Rows</div></div>
          <div class="stat"><div class="n" id="stAccepted">0</div><div class="l">Accepted</div></div>
          <div class="stat"><div class="n" id="stOfficial">0</div><div class="l">Official Review</div></div>
          <div class="stat"><div class="n" id="stReview">0</div><div class="l">Review Required</div></div>
          <div class="stat"><div class="n" id="stPass">—</div><div class="l">Preview Pass</div></div>
        </div>
        <div class="card"><h3>Validation Matrix</h3><div class="body"><div class="tablewrap"><table id="validationTable"></table></div></div></div>
      </div>
    </div>
  </div>

  <div id="input" class="page"><div class="card"><h3>Input Matrix</h3><div class="body"><div class="tablewrap"><table id="inputTable"></table></div></div></div></div>
  <div id="duplicate" class="page"><div class="card"><h3>Duplicate Warning Matrix</h3><div class="body"><div class="tablewrap"><table id="duplicateTable"></table></div></div></div></div>
  <div id="basic" class="page"><div class="card"><h3>BasicInfo Active DB Preview</h3><div class="body"><div class="tablewrap"><table id="basicTable"></table></div></div></div></div>
  <div id="financial" class="page"><div class="card"><h3>Financial Active DB Preview</h3><div class="body"><div class="tablewrap"><table id="financialTable"></table></div></div></div></div>
  <div id="trust" class="page"><div class="card"><h3>Data Trust Preview</h3><div class="body"><div class="tablewrap"><table id="trustTable"></table></div></div></div></div>
  <div id="queue" class="page"><div class="card"><h3>Official Review Queue</h3><div class="body"><div class="tablewrap"><table id="queueTable"></table></div></div></div></div>
  <div id="views" class="page"><div class="card"><h3>Preview DuckDB Views</h3><div class="body"><div class="tablewrap"><table id="viewsTable"></table></div></div></div></div>
  <div id="logs" class="page"><div class="terminal"><div class="tbar">LIVE LOG</div><div class="tbody" id="logBox"></div></div></div>
</div>

<script>
let extraPaths = [];

function tab(id){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  document.getElementById('b_'+id).classList.add('on');
}

async function api(path, data={}){
  let r = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return await r.json();
}

function addPath(){
  let p = document.getElementById('manualPath').value.trim();
  if(!p) return;
  extraPaths.push(p);
  document.getElementById('manualPath').value='';
  renderPaths();
}

function renderPaths(){
  document.getElementById('pathList').innerHTML = extraPaths.map((p,i)=>`<div>${i+1}. ${p}</div>`).join('');
}

function dropFiles(e){
  e.preventDefault();
  document.getElementById('drop').classList.remove('over');
  let arr = [...e.dataTransfer.files].map(f=>f.path||f.name);
  extraPaths.push(...arr);
  renderPaths();
}

async function browseBase(){
  let r = await api('/api/browse_folder',{});
  if(r.path){ document.getElementById('base').value = r.path; await refreshAll(); }
}

async function browseFolder(){
  let r = await api('/api/browse_folder',{});
  if(r.path){ extraPaths.push(r.path); renderPaths(); await refreshAll(); }
}

async function browseFile(){
  let r = await api('/api/browse_file',{});
  if(r.path){ extraPaths.push(r.path); renderPaths(); await refreshAll(); }
}

async function confirmBase(){
  let base = document.getElementById('base').value;
  await api('/api/base',{base});
  await refreshAll();
}

async function refreshAll(){
  document.getElementById('progLabel').innerText='RUNNING';
  let base = document.getElementById('base').value;
  let r = await api('/api/refresh',{base,paths:extraPaths});
  applyResult(r);
  poll();
}

function applyResult(r){
  let c = r.counts || {};
  stInput.innerText = c.input_files || 0;
  stDup.innerText = c.duplicates || 0;
  stBasic.innerText = c.basic_rows || 0;
  stFin.innerText = c.financial_rows || 0;
  stAccepted.innerText = c.accepted_rows || 0;
  stOfficial.innerText = c.official_review_rows || 0;
  stReview.innerText = c.review_required_rows || 0;
  stPass.innerText = r.preview_pass ? 'TRUE' : 'FALSE';
  sourceBadge.innerText = (r.db_source && r.db_source.label) ? r.db_source.label : 'SOURCE';
  stableText.innerText = r.stable_dir || '';
  previewDbText.innerText = r.preview_duckdb || '';

  renderTable('validationTable', r.validation || []);
  renderTable('inputTable', (r.scan && r.scan.files) || []);
  renderTable('duplicateTable', (r.scan && r.scan.duplicates) || []);
  renderTable('viewsTable', r.views || []);
  renderTable('basicTable', r.basic_preview || []);
  renderTable('financialTable', r.financial_preview || []);
  renderTable('trustTable', r.trust_preview || []);
  renderTable('queueTable', r.queue_preview || []);
}

function renderTable(id, rows){
  let t = document.getElementById(id);
  if(!rows || !rows.length){ t.innerHTML='<tr><td>No rows</td></tr>'; return; }
  let cols = [];
  rows.forEach(r=>Object.keys(r).forEach(k=>{if(!cols.includes(k))cols.push(k)}));
  let html = '<thead><tr>'+cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{
    let sev = String(r.Severity || r.Status || r["Data Trust Band v05692"] || r["Final Trust Band"] || '').toUpperCase();
    let cls = sev.includes('ERR')||sev.includes('RED') ? 'red' : sev.includes('WARN')||sev.includes('YELLOW') ? 'yellow' : 'green';
    html += '<tr class="'+cls+'">'+cols.map(c=>{
      let lc=c.toLowerCase();
      let css = (lc.includes('filename')||lc.includes('path')||lc.includes('reason')||lc.includes('detail')||lc.includes('explanation'))?'left':((lc.includes('value')||lc.includes('rows')||lc.includes('score'))?'num':'center');
      return '<td class="'+css+'">'+esc(r[c]??'')+'</td>';
    }).join('')+'</tr>';
  });
  html += '</tbody>';
  t.innerHTML = html;
}

function esc(x){return String(x).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}

async function poll(){
  let s = await fetch('/api/status').then(r=>r.json());
  bar.style.width = (s.progress||0)+'%';
  progPct.innerText = (s.progress||0)+'%';
  progLabel.innerText = s.status || '';
  logBox.innerHTML = (s.logs||[]).slice(-120).map(x=>{
    let cls=x.level==='OK'?'oktxt':x.level==='WARN'?'warntxt':x.level==='ERR'?'errtxt':'dim';
    return `<div class="${cls}">[${x.time}][${x.level}] ${esc(x.message)}</div>`;
  }).join('');
  if((s.status||'')==='RUNNING') setTimeout(poll,500);
}

setInterval(poll,1600);
confirmBase();
</script>
</body>
</html>
'''


def def_render_page() -> str:
    return HTML.replace("__BASE__", STATE["base"].replace("\\", "\\\\"))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, data: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or "0")
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        try:
            if self.path == "/" or self.path.startswith("/?"):
                self._send(200, def_render_page().encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/status":
                self._send(200, def_json({
                    "status": STATE["status"],
                    "progress": STATE["progress"],
                    "logs": STATE["logs"],
                    "counts": STATE["counts"],
                }))
            else:
                self._send(404, def_json({"error": "not found"}))
        except Exception:
            self._send(500, def_json({"error": traceback.format_exc()}))

    def do_POST(self):
        try:
            payload = self._read_json()

            if self.path == "/api/base":
                dirs = def_ensure_base(payload.get("base") or STATE["base"])
                self._send(200, def_json(dirs))

            elif self.path == "/api/refresh":
                base = payload.get("base") or STATE["base"]
                paths = payload.get("paths") or []
                result = def_refresh_all(base, paths)
                source = STATE["db_source"]

                result["basic_preview"] = def_sample(def_read_csv(Path(source["basic"])), 300)
                result["financial_preview"] = def_sample(def_read_csv(Path(source["financial"])), 500)
                result["trust_preview"] = def_sample(def_read_csv(Path(source["data_trust"])), 500)
                result["queue_preview"] = def_sample(def_read_csv(Path(source["official_review"])), 500)
                result["stable_dir"] = STATE["stable_dir"]

                def_write_json(Path(STATE["run_dir"]) / "vrn_unified_operation_db_ui_last_result_v0582.json", result)
                self._send(200, def_json(result))

            elif self.path == "/api/browse_folder":
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    p = filedialog.askdirectory(title="Select BASE or input folder")
                    root.destroy()
                    self._send(200, def_json({"path": p}))
                except Exception as e:
                    self._send(200, def_json({"path": "", "error": str(e)}))

            elif self.path == "/api/browse_file":
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    p = filedialog.askopenfilename(
                        title="Select VRN input file",
                        filetypes=[
                            ("Supported", "*.pdf *.doc *.docx *.png *.jpg *.jpeg *.webp *.tif *.tiff"),
                            ("All files", "*.*"),
                        ],
                    )
                    root.destroy()
                    self._send(200, def_json({"path": p}))
                except Exception as e:
                    self._send(200, def_json({"path": "", "error": str(e)}))

            else:
                self._send(404, def_json({"error": "not found"}))

        except Exception:
            self._send(500, def_json({"error": traceback.format_exc()}))


def def_main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--vrn-root", required=True)
    ap.add_argument("--canonical-dir", required=True)
    ap.add_argument("--stable-dir", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--preview-duckdb", required=True)
    ap.add_argument("--port", type=int, default=8788)
    ap.add_argument("--bridge-json", required=True)
    args = ap.parse_args()

    STATE["base"] = args.base
    STATE["vrn_root"] = args.vrn_root
    STATE["canonical_dir"] = args.canonical_dir
    STATE["stable_dir"] = args.stable_dir
    STATE["run_dir"] = args.run_dir
    STATE["preview_duckdb"] = args.preview_duckdb
    STATE["port"] = args.port

    Path(args.run_dir).mkdir(parents=True, exist_ok=True)
    def_ensure_base(args.base)

    bridge = {
        "version": APP_VERSION,
        "generated_at": def_now(),
        "url": f"http://127.0.0.1:{args.port}/",
        "base": args.base,
        "canonical_dir": args.canonical_dir,
        "stable_dir": args.stable_dir,
        "run_dir": args.run_dir,
        "preview_duckdb": args.preview_duckdb,
        "rule_lock": [
            "Unified input interface and transformed DB preview interface.",
            "BASE change refreshes input scan and DB preview.",
            "Preview DB only in RUN_DIR.",
            "No formal export yet.",
            "No stable mutation.",
            "No canonical mutation.",
            "No Summarizer.",
            "No classifier rewrite.",
        ],
    }
    def_write_json(Path(args.bridge_json), bridge)

    url = bridge["url"]
    def_log("OK", f"Server started: {url}")
    webbrowser.open(url)

    print(json.dumps(bridge, ensure_ascii=False, indent=2))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    def_main()