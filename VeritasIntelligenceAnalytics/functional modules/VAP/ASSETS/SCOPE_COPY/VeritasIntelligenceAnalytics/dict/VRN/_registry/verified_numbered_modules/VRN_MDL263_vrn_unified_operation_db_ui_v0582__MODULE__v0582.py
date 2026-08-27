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


# ==================================================================================================
# HTML TEMPLATE · P7 VISUAL LOCK
# ASSET_ID         : AST-HTML-TPL-VRN-582-001
# LOCK ANCESTOR    : AST-HTML-TPL-VIA-P7-TWFOCUS
#                    AST-HTML-TPL-VIA-305-003  (Resonance Stock Stack)
# FAMILY           : VRN_OPS_UI_P7L
# ANCHORS          : S07-HEAD / S07-STYLE / S07-TOPBAR / S07-TABS
#                    S07-OVERVIEW / S07-TABLES / S07-LOGS / S07-SCRIPT
# DOM/JS contract  : UNCHANGED — all #ids and fn names preserved from v0582
# ==================================================================================================
HTML = r'''
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN Unified Operation + DB Preview UI v05.8.2</title>

<!-- ─── ANCHOR[VIA:ANCHOR:S07-HEAD] · VAOS governance ─────────── -->
<meta name="vaos-asset-id"          content="AST-HTML-TPL-VRN-582-001">
<meta name="vaos-display"           content="SYS_VRN.MDL582.TPL-UNIFIED-OPS-UI">
<meta name="vaos-version"           content="5.8.2">
<meta name="vaos-status"            content="stable">
<meta name="vaos-family"            content="VRN_OPS_UI_P7L">
<meta name="vaos-lock-ancestor"     content="AST-HTML-TPL-VIA-P7-TWFOCUS,AST-HTML-TPL-VIA-305-003">
<meta name="vaos-data-locked"       content="true">
<meta name="vaos-chart-rules"       content="p7-visual-lock;muji-notion-paper;syne-dmsans-dmmono;seaborn-tokens;no-formal-output;read-only-preview;anti-overlap">

<!-- P7-locked typography (Syne + DM Sans + DM Mono + Noto Sans TC fallback) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">

<!-- ─── ANCHOR[VIA:ANCHOR:S07-STYLE] · P7 paper lock ─────────── -->
<style>
:root{
  /* P7 MUJI/Notion paper palette */
  --bg:#f5f4f0; --bg1:#edecea; --bg2:#e5e3df; --sf:#fff; --sf2:#fafaf8;
  --bd:#dbd9d3; --bd2:#ccc9c1;

  /* Seaborn tokens (locked) */
  --bl:#4c78a8; --bl-l:#d0e1f0;
  --tl:#439a9a; --tl-l:#c8e6e6;
  --gn:#5a9e6f; --gn-l:#cde8d5;
  --am:#c4943a; --am-l:#f5e2b8;
  --co:#c96b5a; --co-l:#f5d0c8;
  --vi:#7a6daa; --vi-l:#dcd8f0;
  --ro:#b05580; --ro-l:#ecd0e0;

  --i0:#1e1d1a; --i1:#3d3c38; --i2:#6b6860; --i3:#9c9890; --i4:#c4c0b8;

  --mo:'DM Mono',Consolas,monospace;
  --sa:'DM Sans','Noto Sans TC',system-ui,-apple-system,"Microsoft JhengHei",sans-serif;
  --hf:'Syne','Noto Sans TC',system-ui,sans-serif;

  --r:5px; --r2:8px; --r3:12px;
  --sh:0 1px 3px rgba(0,0,0,.06);
  --sh2:0 4px 12px rgba(0,0,0,.08);

  /* severity locked */
  --sev-ok:var(--gn);   --sev-ok-bg:var(--gn-l);
  --sev-warn:var(--am); --sev-warn-bg:var(--am-l);
  --sev-err:var(--co);  --sev-err-bg:var(--co-l);
}

*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sa);background:var(--bg);color:var(--i0);font-size:11px;line-height:1.55;min-width:1180px}
.wrap{max-width:1760px;margin:0 auto;padding:10px 14px}

/* ─── HEADER (P7) ─────────────────────────────────────────── */
.hdr{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r3);padding:14px 16px;margin-bottom:8px;position:relative;overflow:hidden;display:flex;align-items:center;gap:12px}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--co),var(--am),var(--vi),var(--bl),var(--tl))}
.hdr .h-icon{width:38px;height:38px;border-radius:var(--r2);background:linear-gradient(135deg,var(--co),var(--am));display:flex;align-items:center;justify-content:center;color:#fff;font-family:var(--hf);font-weight:800;font-size:12px;flex-shrink:0;letter-spacing:-1px}
.h1t{font-size:18px;font-weight:700;letter-spacing:-.5px;font-family:var(--hf)}
.h1t span{color:var(--co)}
.h2t{color:var(--i3);font-size:10px;margin-top:1px;font-family:var(--mo);letter-spacing:.3px}
.hdr .h-meta{margin-left:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--gn);box-shadow:0 0 0 3px rgba(90,158,111,.18);animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 3px rgba(90,158,111,.18)}50%{box-shadow:0 0 0 5px rgba(90,158,111,.05)}}
.h-stamp{font-family:var(--mo);font-size:9.5px;color:var(--i2);letter-spacing:.2px}
.data-lock-pill{display:inline-flex;align-items:center;gap:5px;padding:3px 8px;border:1px solid var(--bd);border-radius:14px;background:var(--bg1);font-family:var(--mo);font-size:9px;color:var(--am);font-weight:700;letter-spacing:.4px;text-transform:uppercase}
.data-lock-pill::before{content:'';width:5px;height:5px;background:var(--am);border-radius:50%}

/* ─── BUTTONS (P7) ────────────────────────────────────────── */
.btn{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;border:1px solid var(--bd);border-radius:14px;background:var(--sf);cursor:pointer;font:600 11px var(--mo);color:var(--i1);transition:.12s;letter-spacing:.2px;user-select:none;text-transform:uppercase}
.btn:hover{border-color:var(--co);background:var(--co-l);color:var(--co)}
.btn.primary{background:var(--co);color:#fff;border-color:var(--co)}
.btn.primary:hover{background:var(--ro);border-color:var(--ro);color:#fff}
.btn:active{transform:translateY(1px)}

/* ─── TABS (P7 period-grp style) ──────────────────────────── */
.tabs{display:flex;gap:3px;background:var(--bg1);padding:4px;border-radius:var(--r2);margin-bottom:8px;flex-wrap:wrap}
.tabs button{background:transparent;border:0;color:var(--i2);font-family:var(--mo);font-size:10px;letter-spacing:.3px;padding:6px 11px;cursor:pointer;border-radius:var(--r);font-weight:600;text-transform:uppercase;display:inline-flex;align-items:center;gap:5px}
.tabs button:hover{color:var(--i0)}
.tabs button.on{background:var(--sf);color:var(--co);box-shadow:var(--sh)}
.tabs button .idx{font-size:9px;background:var(--bg1);padding:1px 5px;border-radius:8px;color:var(--i3);font-weight:700}
.tabs button.on .idx{background:var(--co-l);color:var(--co)}

.page{display:none}
.page.on{display:block}

/* ─── LAYOUT ──────────────────────────────────────────────── */
.layout{display:grid;grid-template-columns:380px 1fr;gap:8px;align-items:flex-start}
@media(max-width:1100px){.layout{grid-template-columns:1fr}}

/* ─── CARDS (P7 cd/cd-h/cd-b) ─────────────────────────────── */
.cd{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);overflow:hidden;margin-bottom:8px;transition:.15s}
.cd:hover{box-shadow:var(--sh)}
.cd-h{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--bd);background:var(--sf2)}
.cd-i{width:22px;height:22px;border-radius:var(--r);display:flex;align-items:center;justify-content:center;font-size:9.5px;font-weight:700;font-family:var(--mo);flex-shrink:0;color:#fff;letter-spacing:-.5px}
.cd-i.bl{background:var(--bl)} .cd-i.tl{background:var(--tl)} .cd-i.vi{background:var(--vi)}
.cd-i.am{background:var(--am)} .cd-i.co{background:var(--co)} .cd-i.gn{background:var(--gn)} .cd-i.ro{background:var(--ro)}
.cd-t{font-weight:700;font-size:11.5px;flex:1;font-family:var(--hf);letter-spacing:-.2px}
.cd-s{font-family:var(--mo);font-size:9px;color:var(--i3);padding:1px 7px;background:var(--bg1);border-radius:10px;letter-spacing:.3px;text-transform:uppercase;font-weight:600}
.cd-b{padding:10px 12px}

/* ─── INPUTS ──────────────────────────────────────────────── */
.input{width:100%;padding:6px 10px;border:1.5px solid var(--bd);border-radius:var(--r);font:500 11px var(--mo);color:var(--i0);background:var(--sf);outline:none;letter-spacing:.2px;transition:.12s}
.input:focus{border-color:var(--co);box-shadow:0 0 0 2px rgba(201,107,90,.12)}

.row{display:flex;gap:6px;align-items:center;margin-bottom:7px}
.row > .input{flex:1}
.kv{display:grid;grid-template-columns:90px 1fr;gap:8px;padding:5px 0;border-bottom:1px solid var(--bg2);font-family:var(--mo);font-size:10px}
.kv:last-child{border-bottom:0}
.kv b{color:var(--i3);font-weight:600;text-transform:uppercase;font-size:9px;letter-spacing:.3px}
.kv span{color:var(--i1);overflow-wrap:anywhere}

/* ─── STAT TILES (P7) ─────────────────────────────────────── */
.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:8px}
.sc{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);padding:8px 10px;border-left:3px solid var(--bd2);transition:.12s}
.sc:hover{box-shadow:var(--sh)}
.sc.bl{border-left-color:var(--bl)}
.sc.tl{border-left-color:var(--tl)}
.sc.am{border-left-color:var(--am)}
.sc.vi{border-left-color:var(--vi)}
.sc.co{border-left-color:var(--co)}
.sc.gn{border-left-color:var(--gn)}
.sc.ro{border-left-color:var(--ro)}
.sc .l{font-size:8.5px;color:var(--i3);text-transform:uppercase;letter-spacing:.4px;font-weight:600;font-family:var(--mo)}
.sc .n{font-size:18px;font-weight:700;font-family:var(--mo);letter-spacing:-.3px;margin-top:2px;color:var(--i0)}

/* ─── PROGRESS BAR ────────────────────────────────────────── */
.progress{height:6px;background:var(--bg2);border-radius:999px;overflow:hidden;margin-top:6px}
.bar{height:100%;width:0%;background:linear-gradient(90deg,var(--co),var(--am));transition:width .25s;border-radius:999px}
.prog-head{display:flex;justify-content:space-between;align-items:center;font-family:var(--mo);font-size:10px;color:var(--i2)}
.prog-head #progPct{font-weight:700;color:var(--co)}

/* ─── DROP ZONE ───────────────────────────────────────────── */
.drop{border:1.5px dashed var(--bd2);background:var(--bg1);border-radius:var(--r2);padding:18px;text-align:center;transition:.16s;cursor:pointer}
.drop:hover,.drop.over{background:var(--co-l);border-color:var(--co);color:var(--co)}
.drop .ico{font-size:22px;margin-bottom:6px;opacity:.7}
.drop b{font-family:var(--mo);font-size:11px;letter-spacing:.3px}
.drop .hint{font-size:9px;color:var(--i3);margin-top:4px;font-family:var(--mo);letter-spacing:.2px}

#pathList{margin-top:8px;display:flex;flex-direction:column;gap:3px;max-height:140px;overflow-y:auto}
#pathList:not(:empty){padding:6px;background:var(--bg1);border-radius:var(--r);border:1px solid var(--bd)}
#pathList > div{font-family:var(--mo);font-size:9.5px;color:var(--i2);padding:3px 6px;background:var(--sf);border-radius:3px;border-left:2px solid var(--vi);overflow-wrap:anywhere}

/* ─── TABLES ──────────────────────────────────────────────── */
.tablewrap{overflow:auto;max-height:72vh;border:1px solid var(--bd);border-radius:var(--r);background:var(--sf2);resize:vertical}
.tablewrap::-webkit-scrollbar{width:8px;height:8px}
.tablewrap::-webkit-scrollbar-thumb{background:var(--bd2);border-radius:4px}
table{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px;font-family:var(--mo)}
th{position:sticky;top:0;background:var(--co);color:#fff;padding:7px 8px;border:1px solid var(--ro);text-align:center;vertical-align:middle;z-index:1;font-weight:700;letter-spacing:.3px;font-size:9.5px;text-transform:uppercase}
td{padding:5px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;max-width:460px;color:var(--i1)}
td.left{text-align:left;min-width:240px}
td.center{text-align:center}
td.num{text-align:right;white-space:nowrap;font-feature-settings:"tnum"}
tr:nth-child(even) td{background:var(--bg1)}
tr.green td{background:var(--sev-ok-bg) !important;border-left:2px solid var(--sev-ok)}
tr.green td:first-child{border-left:3px solid var(--sev-ok)}
tr.yellow td{background:var(--sev-warn-bg) !important}
tr.yellow td:first-child{border-left:3px solid var(--sev-warn)}
tr.red td{background:var(--sev-err-bg) !important}
tr.red td:first-child{border-left:3px solid var(--sev-err)}

/* severity inline badges */
.badge{display:inline-block;font-family:var(--mo);font-size:9px;border-radius:4px;padding:2px 7px;background:var(--bg1);color:var(--i2);font-weight:700;letter-spacing:.3px;text-transform:uppercase}
.badge.ok{background:var(--sev-ok-bg);color:var(--sev-ok)}
.badge.warn{background:var(--sev-warn-bg);color:var(--sev-warn)}
.badge.err{background:var(--sev-err-bg);color:var(--sev-err)}

/* ─── LOG TERMINAL (P7 inverted — soft cream "paper terminal") ── */
.terminal{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);overflow:hidden;font-family:var(--mo);box-shadow:var(--sh)}
.tbar{background:var(--bg1);padding:8px 12px;color:var(--i2);font-size:9.5px;letter-spacing:.4px;text-transform:uppercase;font-weight:700;border-bottom:1px solid var(--bd);display:flex;align-items:center;gap:8px}
.tbar::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--gn);box-shadow:0 0 0 3px rgba(90,158,111,.18);animation:pulse 1.6s ease-in-out infinite}
.tbody{padding:10px 14px;max-height:280px;overflow-y:auto;line-height:1.7;font-size:10px;background:var(--sf2)}
.tbody > div{padding:2px 0;border-bottom:1px dashed var(--bg2);overflow-wrap:anywhere}
.tbody > div:last-child{border-bottom:0}
.oktxt{color:var(--gn)}
.warntxt{color:var(--am)}
.errtxt{color:var(--co)}
.dim{color:var(--i3)}

/* ─── FOOTER (P7) ─────────────────────────────────────────── */
.foot{display:flex;justify-content:space-between;align-items:center;font-size:9px;color:var(--i3);letter-spacing:.4px;text-transform:uppercase;padding:8px 4px 4px;gap:10px;flex-wrap:wrap;font-family:var(--mo);margin-top:6px}
.foot .src{color:var(--i2)}
.foot .anc-tag{display:inline-block;padding:1px 6px;border-radius:3px;font-family:var(--mo);font-size:8.5px;font-weight:700;background:var(--co-l);color:var(--co);letter-spacing:.4px}
.foot .vap-tag{display:inline-block;padding:1px 6px;border-radius:3px;font-family:var(--mo);font-size:8.5px;font-weight:700;background:linear-gradient(135deg,var(--co),var(--vi));color:#fff;letter-spacing:.4px}
</style>
</head>

<body>
<div class="wrap">

  <!-- ─── ANCHOR[VIA:ANCHOR:S07-TOPBAR] ─────────────────── -->
  <div class="hdr">
    <div class="h-icon">VRN</div>
    <div style="flex:1">
      <div class="h1t">Veritas<span>ReportNova</span> · Unified Operation + DB Preview UI</div>
      <div class="h2t">v05.8.2 · BASE refresh · input matrix · duplicate review · transformed DB preview · validation status · no formal output</div>
    </div>
    <div class="h-meta">
      <span class="data-lock-pill">DATA-LOCKED · AST-HTML-TPL-VRN-582-001</span>
      <span class="live-dot"></span>
      <span class="h-stamp" id="hdrStatusStamp">READY</span>
      <button class="btn primary" onclick="refreshAll()">⟲ 重新整理 BASE + DB</button>
    </div>
  </div>

  <!-- ─── ANCHOR[VIA:ANCHOR:S07-TABS] ──────────────────── -->
  <div class="tabs">
    <button id="b_overview"  class="on" onclick="tab('overview')"><span class="idx">01</span>Overview</button>
    <button id="b_input"     onclick="tab('input')"><span class="idx">02</span>Input Matrix</button>
    <button id="b_duplicate" onclick="tab('duplicate')"><span class="idx">03</span>Duplicate</button>
    <button id="b_basic"     onclick="tab('basic')"><span class="idx">04</span>BasicInfo DB</button>
    <button id="b_financial" onclick="tab('financial')"><span class="idx">05</span>Financial DB</button>
    <button id="b_trust"     onclick="tab('trust')"><span class="idx">06</span>Trust</button>
    <button id="b_queue"     onclick="tab('queue')"><span class="idx">07</span>Official Queue</button>
    <button id="b_views"     onclick="tab('views')"><span class="idx">08</span>DB Views</button>
    <button id="b_logs"      onclick="tab('logs')"><span class="idx">09</span>Logs</button>
  </div>

  <!-- ─── ANCHOR[VIA:ANCHOR:S07-OVERVIEW] ──────────────── -->
  <div id="overview" class="page on">
    <div class="layout">
      <!-- LEFT COLUMN: control panel -->
      <div>
        <div class="cd">
          <div class="cd-h">
            <div class="cd-i bl">BS</div>
            <div class="cd-t">BASE 設定</div>
            <span class="cd-s" id="sourceBadge">READY</span>
          </div>
          <div class="cd-b">
            <div class="row">
              <input id="base" class="input" value="__BASE__">
              <button class="btn primary" onclick="confirmBase()">確認</button>
            </div>
            <div class="row">
              <button class="btn" onclick="browseBase()">📁 選 BASE</button>
              <button class="btn" onclick="refreshAll()">⟲ 重新整理</button>
            </div>
            <div class="kv"><b>Mode</b><span>Preview only · no formal output</span></div>
            <div class="kv"><b>Stable</b><span id="stableText">—</span></div>
            <div class="kv"><b>Preview DB</b><span id="previewDbText">—</span></div>
          </div>
        </div>

        <div class="cd">
          <div class="cd-h">
            <div class="cd-i vi">IN</div>
            <div class="cd-t">增加輸入</div>
            <span class="cd-s">PDF · Word · Image</span>
          </div>
          <div class="cd-b">
            <div id="drop" class="drop"
                 ondragover="event.preventDefault();this.classList.add('over')"
                 ondragleave="this.classList.remove('over')"
                 ondrop="dropFiles(event)">
              <div class="ico">📥</div>
              <b>拖曳檔案或資料夾到這裡</b>
              <div class="hint">瀏覽器可能只給檔名 · 完整路徑用 Window I/O 或手動貼上</div>
            </div>
            <div class="row" style="margin-top:8px">
              <input id="manualPath" class="input" placeholder="貼上完整檔案/資料夾路徑">
              <button class="btn" onclick="addPath()">加入</button>
            </div>
            <div class="row">
              <button class="btn" onclick="browseFile()">📄 選檔</button>
              <button class="btn" onclick="browseFolder()">📁 選資料夾</button>
            </div>
            <div id="pathList"></div>
          </div>
        </div>

        <div class="cd">
          <div class="cd-h">
            <div class="cd-i co">LP</div>
            <div class="cd-t">Live Progress</div>
            <span class="cd-s" id="progLabel">READY</span>
          </div>
          <div class="cd-b">
            <div class="prog-head">
              <span style="font-family:var(--mo);font-size:10px;color:var(--i2)">pipeline</span>
              <span id="progPct">0%</span>
            </div>
            <div class="progress"><div id="bar" class="bar"></div></div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: stats + validation -->
      <div>
        <div class="sg">
          <div class="sc bl"><div class="l">Input Files</div><div class="n" id="stInput">0</div></div>
          <div class="sc am"><div class="l">Duplicates</div><div class="n" id="stDup">0</div></div>
          <div class="sc tl"><div class="l">Basic Rows</div><div class="n" id="stBasic">0</div></div>
          <div class="sc vi"><div class="l">Financial Rows</div><div class="n" id="stFin">0</div></div>
          <div class="sc gn"><div class="l">Accepted</div><div class="n" id="stAccepted">0</div></div>
          <div class="sc co"><div class="l">Official Review</div><div class="n" id="stOfficial">0</div></div>
          <div class="sc ro"><div class="l">Review Required</div><div class="n" id="stReview">0</div></div>
          <div class="sc co"><div class="l">Preview Pass</div><div class="n" id="stPass">—</div></div>
        </div>

        <div class="cd">
          <div class="cd-h">
            <div class="cd-i co">VM</div>
            <div class="cd-t">Validation Matrix</div>
            <span class="cd-s">12 gates</span>
          </div>
          <div class="cd-b" style="padding:0">
            <div class="tablewrap"><table id="validationTable"></table></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ─── ANCHOR[VIA:ANCHOR:S07-TABLES] ─────────────────── -->
  <div id="input" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i bl">02</div><div class="cd-t">Input Matrix</div><span class="cd-s">all parsed files</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="inputTable"></table></div></div>
    </div>
  </div>

  <div id="duplicate" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i am">03</div><div class="cd-t">Duplicate Warning Matrix</div><span class="cd-s">size · ticker · broker · date</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="duplicateTable"></table></div></div>
    </div>
  </div>

  <div id="basic" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i tl">04</div><div class="cd-t">BasicInfo Active DB Preview</div><span class="cd-s">top 300 rows</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="basicTable"></table></div></div>
    </div>
  </div>

  <div id="financial" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i vi">05</div><div class="cd-t">Financial Active DB Preview</div><span class="cd-s">top 500 rows</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="financialTable"></table></div></div>
    </div>
  </div>

  <div id="trust" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i gn">06</div><div class="cd-t">Data Trust Preview</div><span class="cd-s">trust band</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="trustTable"></table></div></div>
    </div>
  </div>

  <div id="queue" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i co">07</div><div class="cd-t">Official Review Queue</div><span class="cd-s">pending coverage</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="queueTable"></table></div></div>
    </div>
  </div>

  <div id="views" class="page">
    <div class="cd">
      <div class="cd-h"><div class="cd-i ro">08</div><div class="cd-t">Preview DuckDB Views</div><span class="cd-s">RUN_DIR only</span></div>
      <div class="cd-b" style="padding:0"><div class="tablewrap"><table id="viewsTable"></table></div></div>
    </div>
  </div>

  <!-- ─── ANCHOR[VIA:ANCHOR:S07-LOGS] ────────────────────── -->
  <div id="logs" class="page">
    <div class="terminal">
      <div class="tbar">LIVE LOG · runtime stream · last 120 lines</div>
      <div class="tbody" id="logBox"></div>
    </div>
  </div>

  <!-- ─── FOOTER ─────────────────────────────────────────── -->
  <div class="foot">
    <div class="src">
      <span class="vap-tag">VRN 0582</span>
      &nbsp;mode: read-only preview · no formal export · no stable/canonical mutation
    </div>
    <div>
      <span class="anc-tag">P7 VISUAL LOCK</span>
      &nbsp;family: VRN_OPS_UI_P7L · ancestor: AST-HTML-TPL-VIA-P7-TWFOCUS / 305-003
    </div>
  </div>

</div>

<!-- ─── ANCHOR[VIA:ANCHOR:S07-SCRIPT] · logic unchanged ── -->
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
  document.getElementById('pathList').innerHTML = extraPaths.map((p,i)=>`<div>${i+1}. ${esc(p)}</div>`).join('');
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
  document.getElementById('hdrStatusStamp').innerText='RUNNING';
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
  if(!rows || !rows.length){ t.innerHTML='<tr><td>— no rows —</td></tr>'; return; }
  let cols = [];
  rows.forEach(r=>Object.keys(r).forEach(k=>{if(!cols.includes(k))cols.push(k)}));
  let html = '<thead><tr>'+cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{
    let sev = String(r.Severity || r.Status || r["Data Trust Band v05692"] || r["Final Trust Band"] || '').toUpperCase();
    let cls = sev.includes('ERR')||sev.includes('RED') ? 'red' : sev.includes('WARN')||sev.includes('YELLOW') ? 'yellow' : (sev.includes('OK')||sev.includes('GREEN')?'green':'');
    html += '<tr class="'+cls+'">'+cols.map(c=>{
      let lc=c.toLowerCase();
      let css = (lc.includes('filename')||lc.includes('path')||lc.includes('reason')||lc.includes('detail')||lc.includes('explanation'))?'left':((lc.includes('value')||lc.includes('rows')||lc.includes('score')||lc.includes('size'))?'num':'center');
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
  hdrStatusStamp.innerText = s.status || '';
  logBox.innerHTML = (s.logs||[]).slice(-120).map(x=>{
    let cls=x.level==='OK'?'oktxt':x.level==='WARN'?'warntxt':x.level==='ERR'?'errtxt':'dim';
    return `<div class="${cls}">[${esc(x.time)}] <b>[${esc(x.level)}]</b> ${esc(x.message)}</div>`;
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