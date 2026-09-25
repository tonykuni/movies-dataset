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

import ast
import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


VERSION = "VRN_FLOWA_OFFICIAL_PARSER_FLOWC_HEALTH_V061567"


# ==================================================================================================
# def BASIC UTILITIES
# ==================================================================================================
def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_flat(x: Any) -> str:
    return re.sub(r"\s+", " ", def_clean(x)).strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return default


def def_float(x: Any, default: Any = None) -> Any:
    s = def_flat(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "PARSER_READY", "FLOW_READY", "CELL_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "PLAN", "QUEUE", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_sha256(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    if not root.exists():
        return None
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_get(row: dict, aliases: list[str]) -> str:
    mp = {def_norm(k): k for k in row.keys()}
    for a in aliases:
        na = def_norm(a)
        if na in mp:
            return def_clean(row.get(mp[na]))
    for k in row.keys():
        nk = def_norm(k)
        for a in aliases:
            if def_norm(a) in nk:
                return def_clean(row.get(k))
    return ""


# ==================================================================================================
# def FLOW A HTML TABLE PARSER
# ==================================================================================================
class DefSimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_table = []
        self.current_row = []
        self.current_cell = []
        self.cell_tag = ""
        self.table_depth = 0

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "table":
            if not self.in_table:
                self.in_table = True
                self.current_table = []
                self.table_depth = 1
            else:
                self.table_depth += 1
        elif self.in_table and t == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and t in ["td", "th"]:
            self.in_cell = True
            self.cell_tag = t
            self.current_cell = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if self.in_table and self.in_row and self.in_cell and t in ["td", "th"]:
            txt = def_flat(" ".join(self.current_cell))
            self.current_row.append({"text": txt, "tag": self.cell_tag})
            self.in_cell = False
            self.current_cell = []
            self.cell_tag = ""
        elif self.in_table and self.in_row and t == "tr":
            if self.current_row:
                self.current_table.append(self.current_row)
            self.in_row = False
            self.current_row = []
        elif self.in_table and t == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.tables.append(self.current_table)
                self.in_table = False
                self.current_table = []
                self.table_depth = 0

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)


def def_parse_html_tables(path: Path) -> list[list[list[dict]]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    parser = DefSimpleTableParser()
    parser.feed(text)
    return parser.tables


def def_parse_cache_metadata(path: Path) -> dict:
    # filename format from previous run:
    # 6669_2021_BALANCE_SHEET_2_MOPS_T164SB03_OV.html
    stem = path.stem
    parts = stem.split("_")
    ticker = parts[0] if len(parts) > 0 else ""
    year = parts[1] if len(parts) > 1 else ""
    statement = ""
    source = ""
    if len(parts) >= 5:
        # find numeric ordinal before source
        ordinal_index = None
        for i, p in enumerate(parts):
            if i >= 2 and p.isdigit():
                ordinal_index = i
                break
        if ordinal_index:
            statement = "_".join(parts[2:ordinal_index])
            source = "_".join(parts[ordinal_index + 1:])
        else:
            statement = "_".join(parts[2:4])
            source = "_".join(parts[4:])
    return {
        "ticker": ticker,
        "period year": year,
        "statement": statement,
        "source": source,
    }


def def_is_number_text(x: str) -> bool:
    s = def_flat(x).replace(",", "").replace("%", "")
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s))


def def_extract_years_from_row(cells: list[str]) -> list[str]:
    years = []
    for c in cells:
        found = re.findall(r"(20\d{2}|1\d{2}年度|民國\s*1\d{2})", c)
        for f in found:
            y = f
            if "年度" in y:
                y = str(def_int(y.replace("年度", "")) + 1911)
            elif "民國" in y:
                y = str(def_int(re.sub(r"\D", "", y)) + 1911)
            years.append(y)
    return years


def def_parse_one_cache_file(path: Path) -> dict:
    meta = def_parse_cache_metadata(path)
    tables = def_parse_html_tables(path)

    cell_rows = []
    row_rows = []
    table_rows = []

    for ti, table in enumerate(tables, 1):
        max_cols = max([len(r) for r in table] + [0])
        nonempty = 0
        numeric = 0
        header_years = []

        for ri, row in enumerate(table, 1):
            texts = [def_flat(c.get("text", "")) for c in row]
            row_text = " | ".join([x for x in texts if x])
            row_years = def_extract_years_from_row(texts)
            if row_years:
                header_years.extend(row_years)

            row_nonempty = sum(1 for x in texts if x)
            row_numeric = sum(1 for x in texts if def_is_number_text(x))
            nonempty += row_nonempty
            numeric += row_numeric

            row_role = "HEADER" if ri <= 2 or row_years else ("DATA" if row_numeric > 0 else "TEXT")

            row_rows.append({
                "Status Lights": def_light("OK" if row_nonempty else "WARN"),
                **meta,
                "cache file": str(path),
                "table index": ti,
                "row index": ri,
                "row role": row_role,
                "cols": len(row),
                "numeric cells": row_numeric,
                "row text": row_text,
                "db write": "NO",
                "canonical mutation": "NO",
                "ssot mutation": "NO",
                "Severity": "OK" if row_nonempty else "WARN",
            })

            for ci, cell in enumerate(row, 1):
                txt = def_flat(cell.get("text", ""))
                if txt:
                    cell_rows.append({
                        "Status Lights": def_light("OK"),
                        **meta,
                        "cache file": str(path),
                        "table index": ti,
                        "row index": ri,
                        "col index": ci,
                        "cell tag": cell.get("tag", ""),
                        "row role": row_role,
                        "cell text": txt,
                        "is numeric": "YES" if def_is_number_text(txt) else "NO",
                        "numeric value": def_float(txt, ""),
                        "possible year": "YES" if re.search(r"20\d{2}|1\d{2}年度|民國\s*1\d{2}", txt) else "NO",
                        "db write": "NO",
                        "canonical mutation": "NO",
                        "ssot mutation": "NO",
                        "Severity": "OK",
                    })

        table_score = nonempty + numeric * 3 + len(set(header_years)) * 8
        sev = "OK" if nonempty > 5 and numeric > 0 else "WARN"
        table_rows.append({
            "Status Lights": def_light(sev),
            **meta,
            "cache file": str(path),
            "table index": ti,
            "rows": len(table),
            "max cols": max_cols,
            "nonempty cells": nonempty,
            "numeric cells": numeric,
            "header years": " | ".join(sorted(set(header_years))),
            "parser score": table_score,
            "parser route": "OFFICIAL_TABLE_PARSER_READY" if sev == "OK" else "OFFICIAL_TABLE_REVIEW",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": sev,
        })

    return {
        "file": str(path),
        "meta": meta,
        "tables": table_rows,
        "rows": row_rows,
        "cells": cell_rows,
    }


def def_flow_a_official_parser(fetch_run: Path, run_dir: Path) -> dict:
    cache_dir = fetch_run / "official_evidence_cache"
    cache_files = sorted(cache_dir.glob("*.html")) if cache_dir.exists() else []

    all_tables = []
    all_rows = []
    all_cells = []
    file_summary = []

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(def_parse_one_cache_file, p): p for p in cache_files}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                res = fut.result()
                all_tables.extend(res["tables"])
                all_rows.extend(res["rows"])
                all_cells.extend(res["cells"])
                file_summary.append({
                    "Status Lights": def_light("OK"),
                    "cache file": str(p),
                    "tables": len(res["tables"]),
                    "rows": len(res["rows"]),
                    "cells": len(res["cells"]),
                    "sha256": def_sha256(p),
                    "Severity": "OK",
                })
            except Exception as e:
                file_summary.append({
                    "Status Lights": def_light("ERR"),
                    "cache file": str(p),
                    "tables": 0,
                    "rows": 0,
                    "cells": 0,
                    "sha256": def_sha256(p),
                    "error": f"{type(e).__name__}: {e}",
                    "Severity": "ERR",
                })

    ready_tables = [r for r in all_tables if r.get("parser route") == "OFFICIAL_TABLE_PARSER_READY"]

    outputs = {
        "official_table_summary_csv": str(run_dir / "flowa_official_table_summary_v061567.csv"),
        "official_row_matrix_csv": str(run_dir / "flowa_official_row_matrix_v061567.csv"),
        "official_cell_matrix_csv": str(run_dir / "flowa_official_cell_matrix_v061567.csv"),
        "official_cache_file_summary_csv": str(run_dir / "flowa_official_cache_file_summary_v061567.csv"),
    }

    def_write_csv(Path(outputs["official_table_summary_csv"]), all_tables)
    def_write_csv(Path(outputs["official_row_matrix_csv"]), all_rows)
    def_write_csv(Path(outputs["official_cell_matrix_csv"]), all_cells)
    def_write_csv(Path(outputs["official_cache_file_summary_csv"]), file_summary)

    return {
        "system_pass": len(ready_tables) > 0 and len(all_cells) > 0,
        "counts": {
            "cache_files": len(cache_files),
            "tables": len(all_tables),
            "ready_tables": len(ready_tables),
            "rows": len(all_rows),
            "cells": len(all_cells),
            "file_errors": len([r for r in file_summary if r.get("Severity") == "ERR"]),
        },
        "outputs": outputs,
        "tables": all_tables,
        "file_summary": file_summary,
    }


# ==================================================================================================
# def FLOW C HEALTH
# ==================================================================================================
def def_scan_python_module(path: Path) -> dict:
    row = {
        "Status Lights": def_light("WARN"),
        "file": str(path),
        "name": path.name,
        "exists": path.exists(),
        "sha256": "",
        "ast": "NO",
        "compile": "NO",
        "functions": 0,
        "classes": 0,
        "error": "",
        "Severity": "WARN",
    }
    if not path.exists():
        row["error"] = "missing"
        row["Severity"] = "ERR"
        row["Status Lights"] = def_light("ERR")
        return row
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
        row["sha256"] = def_sha256(path)
        row["ast"] = "YES"
        row["compile"] = "YES"
        row["functions"] = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        row["classes"] = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        row["Severity"] = "OK"
        row["Status Lights"] = def_light("OK")
    except Exception as e:
        row["sha256"] = def_sha256(path)
        row["error"] = f"{type(e).__name__}: {e}"
        row["Severity"] = "ERR"
        row["Status Lights"] = def_light("ERR")
    return row


def def_scan_config(path: Path) -> dict:
    sev = "OK" if path.exists() else "ERR"
    return {
        "Status Lights": def_light(sev),
        "file": str(path),
        "name": path.name,
        "exists": path.exists(),
        "sha256": def_sha256(path) if path.exists() else "",
        "type": path.suffix,
        "Severity": sev,
    }


def def_flow_c_health(supportive_dir: Path, vrn_root: Path, run_root: Path, run_dir: Path) -> dict:
    supportive_names = [
        "VIA_SSOT_Unified.py",
        "VIA_RegistryCore_v1.py",
        "VIA_Runtime_Bridge_All_in_One.py",
        "VIA_EnvManager.py",
        "VIA_Panorama_AST_RuntimeInjector.py",
        "VIS_VRN_NewReportCompatibilityGate_v01.py",
        "VIS_VRN_MasterRegistryBridge_v0611.py",
        "SUP_MDL016_VISVRNBrokerAnalystAdaptersV06146.py",
    ]

    module_rows = [def_scan_python_module(supportive_dir / name) for name in supportive_names]

    config_rows = [
        def_scan_config(vrn_root / "config" / "VIS_VRN_AdapterRegistry_v01.json"),
        def_scan_config(vrn_root / "config" / "VIS_VRN_NewReport_Format_Playbook_v01.md"),
    ]

    lineage_specs = [
        ("Official Fetch Parser Ready", "VRN_OFFICIAL_FETCH_DRYRUN_PARSER_READY_V06156551"),
        ("Official Forecast Seal", "VRN_OFFICIAL_FORECAST_VALIDATION_PREFLIGHT_SEAL_V06156541"),
        ("Parser Router Gate", "VRN_PARSER_REPAIR_ROUTER_VALIDATION_GATE_V0615653"),
        ("Account Period Value Parser", "VRN_ACCOUNT_PERIOD_VALUE_PARSER_PREFLIGHT_V0615651"),
        ("Targeted Body Export", "VRN_TARGETED_TABLE_BODY_EXPORT_DRYRUN_V061564"),
    ]

    lineage_rows = []
    for label, prefix in lineage_specs:
        d = def_find_latest_dir(run_root, prefix)
        sev = "OK" if d else "ERR"
        lineage_rows.append({
            "Status Lights": def_light(sev),
            "lineage item": label,
            "prefix": prefix,
            "latest run": str(d) if d else "",
            "Severity": sev,
        })

    outputs = {
        "supportive_module_health_csv": str(run_dir / "flowc_supportive_module_health_v061567.csv"),
        "vrn_config_health_csv": str(run_dir / "flowc_vrn_config_health_v061567.csv"),
        "lineage_health_csv": str(run_dir / "flowc_lineage_health_v061567.csv"),
    }

    def_write_csv(Path(outputs["supportive_module_health_csv"]), module_rows)
    def_write_csv(Path(outputs["vrn_config_health_csv"]), config_rows)
    def_write_csv(Path(outputs["lineage_health_csv"]), lineage_rows)

    errors = [r for r in module_rows + config_rows + lineage_rows if r.get("Severity") == "ERR"]

    return {
        "system_pass": len(errors) == 0,
        "counts": {
            "module_rows": len(module_rows),
            "config_rows": len(config_rows),
            "lineage_rows": len(lineage_rows),
            "errors": len(errors),
        },
        "outputs": outputs,
        "module_rows": module_rows,
        "config_rows": config_rows,
        "lineage_rows": lineage_rows,
    }


# ==================================================================================================
# def FLOW B PLAN ONLY
# ==================================================================================================
def def_build_flow_b_plan(run_root: Path, run_dir: Path, flow_a_outputs: dict) -> dict:
    seal_run = def_find_latest_dir(run_root, "VRN_OFFICIAL_FORECAST_VALIDATION_PREFLIGHT_SEAL_V06156541")
    work_orders = def_read_csv(seal_run / "vrn_actual_official_validation_work_order_v06156541.csv") if seal_run else []

    plan_rows = []
    for i, wo in enumerate(work_orders, 1):
        plan_rows.append({
            "Status Lights": def_light("WARN"),
            "validation plan id": f"VRN_CELL_VALIDATION_PLAN_{i:04d}",
            "official work order id": def_get(wo, ["official work order id"]),
            "ticker": def_get(wo, ["ticker"]),
            "filename": def_get(wo, ["filename"]),
            "statement": def_get(wo, ["statement"]),
            "account raw": def_get(wo, ["account raw"]),
            "account canonical": def_get(wo, ["account canonical"]),
            "account key": def_get(wo, ["account key"]),
            "period year": def_get(wo, ["period year"]),
            "report value": def_get(wo, ["report value"]),
            "unit": def_get(wo, ["unit"]),
            "official cell source": flow_a_outputs.get("official_cell_matrix_csv", ""),
            "next route": "WAIT_FOR_FLOWA_CELL_MATRIX_THEN_MATCH_BY_ACCOUNT_PERIOD_VALUE",
            "tolerance plan": "mn TWD: absolute/relative tolerance; %: percent tolerance; zero: exact/near-zero",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "WARN",
        })

    outputs = {
        "flowb_cell_validation_plan_csv": str(run_dir / "flowb_official_cell_validation_plan_v061567.csv"),
    }
    def_write_csv(Path(outputs["flowb_cell_validation_plan_csv"]), plan_rows)

    return {
        "system_pass": len(plan_rows) > 0,
        "counts": {
            "work_orders": len(work_orders),
            "validation_plan_rows": len(plan_rows),
        },
        "outputs": outputs,
        "plan_rows": plan_rows,
    }


# ==================================================================================================
# def HTML REPORT
# ==================================================================================================
def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["file", "path", "run", "account", "route", "source", "tolerance", "error"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1120px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>" for k, v in counts.items())
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN FlowA Official Parser FlowC Health v061567</title><style>{css}</style></head>
<body><header><h1>VRN · FlowA Official HTML Parser Adapter + FlowC Health Seal v0.6.15.6.7</h1>
<div class="sub">official cell matrix staging · health seal · validation plan only · no mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: py <run_root> <supportive_dir> <vrn_root> <run_dir>")

    run_root = Path(sys.argv[1])
    supportive_dir = Path(sys.argv[2])
    vrn_root = Path(sys.argv[3])
    run_dir = Path(sys.argv[4])
    run_dir.mkdir(parents=True, exist_ok=True)

    fetch_run = def_find_latest_dir(run_root, "VRN_OFFICIAL_FETCH_DRYRUN_PARSER_READY_V06156551")
    if not fetch_run:
        raise RuntimeError("Missing latest official fetch run v06156551.")

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_a = ex.submit(def_flow_a_official_parser, fetch_run, run_dir)
        fut_c = ex.submit(def_flow_c_health, supportive_dir, vrn_root, run_root, run_dir)

        flow_a = fut_a.result()
        flow_c = fut_c.result()

    flow_b = def_build_flow_b_plan(run_root, run_dir, flow_a["outputs"])

    flow_summary = [
        {
            "Status Lights": def_light("OK" if flow_a["system_pass"] else "WARN"),
            "Flow": "A",
            "Name": "Official HTML Parser Adapter Staging",
            "System Pass": "YES" if flow_a["system_pass"] else "NO",
            "Counts": json.dumps(flow_a["counts"], ensure_ascii=False),
            "Output": json.dumps(flow_a["outputs"], ensure_ascii=False),
            "Severity": "OK" if flow_a["system_pass"] else "WARN",
        },
        {
            "Status Lights": def_light("OK" if flow_b["system_pass"] else "WARN"),
            "Flow": "B",
            "Name": "Cell-Level Validation Plan Only",
            "System Pass": "YES" if flow_b["system_pass"] else "NO",
            "Counts": json.dumps(flow_b["counts"], ensure_ascii=False),
            "Output": json.dumps(flow_b["outputs"], ensure_ascii=False),
            "Severity": "OK" if flow_b["system_pass"] else "WARN",
        },
        {
            "Status Lights": def_light("OK" if flow_c["system_pass"] else "WARN"),
            "Flow": "C",
            "Name": "Supportive / UI / Lineage Health Seal",
            "System Pass": "YES" if flow_c["system_pass"] else "NO",
            "Counts": json.dumps(flow_c["counts"], ensure_ascii=False),
            "Output": json.dumps(flow_c["outputs"], ensure_ascii=False),
            "Severity": "OK" if flow_c["system_pass"] else "WARN",
        },
    ]

    next_steps = [
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Run official cell-level validation dry run using Flow A official_cell_matrix and Flow B plan.",
            "Reason": "Official HTML is now converted into cell matrix staging; validation still must compare account/year/value.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Keep DB/canonical/SSOT locked.",
            "Reason": "Cell-level validation has not passed yet.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "If official table aliases are Chinese-only, add alias observation pack before SSOT patch.",
            "Reason": "MOPS labels may not match report English labels directly.",
            "Severity": "WARN",
        },
    ]

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "NO_DB_WRITE", "Reason": "Only staging reports/csv generated.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_CANONICAL_MUTATION", "Reason": "Official cell validation not executed yet.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_MUTATION", "Reason": "No alias patch in parser staging.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_RESTORE_NO_OCR_NO_DELETE", "Reason": "Only existing official HTML cache and existing modules are read.", "Severity": "OK"},
    ]

    final_pass = flow_a["system_pass"] and flow_b["system_pass"] and flow_c["system_pass"]

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Flow A": "PASS" if flow_a["system_pass"] else "REVIEW",
        "Flow B": "PASS" if flow_b["system_pass"] else "REVIEW",
        "Flow C": "PASS" if flow_c["system_pass"] else "REVIEW",
        "Official Tables": flow_a["counts"].get("tables", 0),
        "Ready Tables": flow_a["counts"].get("ready_tables", 0),
        "Official Cells": flow_a["counts"].get("cells", 0),
        "Validation Plans": flow_b["counts"].get("validation_plan_rows", 0),
        "Health Errors": flow_c["counts"].get("errors", 0),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "FLOWA_FLOWC_HEALTH_FINAL_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "LATEST_FETCH_RUN", "Value": str(fetch_run), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "OFFICIAL_CELLS", "Value": flow_a["counts"].get("cells", 0), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "VALIDATION_PLAN_ROWS", "Value": flow_b["counts"].get("validation_plan_rows", 0), "Severity": "OK"},
        {"Status Lights": def_light("OK" if flow_c["system_pass"] else "WARN"), "Gate": "HEALTH_ERRORS", "Value": flow_c["counts"].get("errors", 0), "Severity": "OK" if flow_c["system_pass"] else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_FlowA_Official_Parser_FlowC_Health_v061567.html"),
        "json": str(run_dir / "vrn_flowa_official_parser_flowc_health_v061567.json"),
        "flow_summary_csv": str(run_dir / "vrn_flow_summary_v061567.csv"),
        "next_steps_csv": str(run_dir / "vrn_next_steps_v061567.csv"),
        "hard_rules_csv": str(run_dir / "vrn_hard_rules_v061567.csv"),
        **flow_a["outputs"],
        **flow_b["outputs"],
        **flow_c["outputs"],
    }

    def_write_csv(Path(outputs["flow_summary_csv"]), flow_summary)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "counts": counts,
        "outputs": outputs,
        "latest_fetch_run": str(fetch_run),
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Flow Summary", flow_summary, None),
            ("03 Next Steps", next_steps, None),
            ("04 Official Table Summary", flow_a["tables"], 800),
            ("05 Official Cache File Summary", flow_a["file_summary"], 500),
            ("06 Flow B Validation Plan", flow_b["plan_rows"], 800),
            ("07 Supportive Module Health", flow_c["module_rows"], 200),
            ("08 VRN Config Health", flow_c["config_rows"], 50),
            ("09 Lineage Health", flow_c["lineage_rows"], 100),
            ("10 Hard Rules", hard_rules, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        import traceback
        print(traceback.format_exc())
        raise