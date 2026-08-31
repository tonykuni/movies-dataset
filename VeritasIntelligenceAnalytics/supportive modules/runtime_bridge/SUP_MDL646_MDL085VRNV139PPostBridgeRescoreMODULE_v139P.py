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
VIA_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
VRN_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
SUPPORTIVE_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE"

AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_PostBridge_Rescore_Matrix.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_PostBridge_Rescore_Matrix.json"
OUT_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_PostBridge_Rescore_Matrix.csv"
OUT_MODULE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_Strict_Production_Modules_PostBridge.csv"
OUT_REMAINING_PLAN = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_Remaining_Yellow_Plan.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_164003_VRN_V139P_POST_BRIDGE_RESCORE\VRN_v139P_PostBridge_Rescore_Registry.txt"

import ast
import csv
import hashlib
import html
import importlib.util
import json
import os
import py_compile
import re
import sys
import traceback
from pathlib import Path
from datetime import datetime

def def_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def def_html_escape(x):
    return html.escape(str(x))

def def_read_text(path):
    p = Path(path)
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            return p.read_text(encoding=enc, errors="ignore")
        except Exception:
            pass
    return p.read_text(errors="ignore")

def def_sha1(path):
    try:
        h = hashlib.sha1()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 256), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def def_add_matrix(rows, page, gate, value, status, severity, message):
    rows.append({
        "Time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "Page": str(page),
        "Gate": str(gate),
        "Value": str(value),
        "Status": str(status),
        "Severity": str(severity),
        "Message": str(message),
    })

def def_write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        Path(path).write_text("", encoding="utf-8-sig")
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def def_find_latest_n2_strict_csv():
    root = Path(VRN_ROOT) / "output" / "_route_lock_runs"
    runs = sorted(root.glob("RUN_*_VRN_V139N2_HEADER_NORMALIZED_RESCORE"), key=lambda p: p.stat().st_mtime, reverse=True)
    for r in runs:
        csv_path = r / "VRN_v139N2_Strict_Production_Modules.csv"
        if csv_path.exists():
            return str(csv_path), str(r)
    raise RuntimeError("Cannot find latest v139N2 strict production CSV")

def def_read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def def_import_core(label, path):
    r = {"module": label, "path": path, "exists": False, "ast_ok": False, "compile_ok": False, "import_ok": False, "functions": 0, "classes": 0, "error": ""}
    try:
        p = Path(path)
        if not p.exists():
            r["error"] = "missing"
            return r
        r["exists"] = True
        text = def_read_text(p)
        tree = ast.parse(text)
        r["ast_ok"] = True
        r["functions"] = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        r["classes"] = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        py_compile.compile(str(p), doraise=True)
        r["compile_ok"] = True
        spec = importlib.util.spec_from_file_location(label, str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[label] = mod
        spec.loader.exec_module(mod)
        r["import_ok"] = True
        return r
    except Exception:
        r["error"] = traceback.format_exc()[:800]
        return r

def def_strip_ps_comments(text):
    out = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)

def def_has_real_stop_risk(path, text, file_type):
    lower = text.lower()

    if file_type == "ps1":
        active = def_strip_ps_comments(text).lower()
        return bool(re.search(r"(?im)^\\s*stop-process\\b", active))

    if file_type == "py":
        try:
            tree = ast.parse(text)
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Attribute) and f.attr in ["kill", "terminate"]:
                        return True
                    if isinstance(f, ast.Name) and f.id in ["kill", "terminate"]:
                        return True
        except Exception:
            return ".kill(" in lower or "os.kill" in lower

    return False

def def_analyze_file(path, file_type):
    text = def_read_text(path)
    lower = text.lower()
    suffix = Path(path).suffix.lower()

    ft = file_type.lower().strip()
    if not ft:
        ft = suffix.replace(".", "")

    row = {
        "file_type": ft,
        "path": str(path),
        "sha1": def_sha1(path),
        "parse_ok": False,
        "compile_ok": False,
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "has_aegis_text": "veritasaegisnexus" in lower or "aegis" in lower,
        "has_celeritas_text": "veritasceleritas" in lower or "celeritas" in lower,
        "has_envmanager_text": "via_envmanager" in lower or "envmanager" in lower,
        "has_timeout_text": "timeout" in lower,
        "has_watchdog_text": "watchdog" in lower or "nohang" in lower or "nohang_watchdog" in lower,
        "has_stop_process_risk": False,
        "has_network_text": any(x in lower for x in ["requests", "urllib", "yfinance", "httpx", "openapi", "twstock", "finmind", "invoke-webrequest", "invoke-restmethod"]),
        "has_v139o_marker": "vrn_v139o_supportive_bridge_append_only" in lower,
        "risk": "UNKNOWN",
        "coverage_score": 0,
        "anchor_hint": "",
        "message": ""
    }

    row["has_stop_process_risk"] = def_has_real_stop_risk(path, text, ft)

    if ft == "py" or suffix == ".py":
        try:
            tree = ast.parse(text)
            row["parse_ok"] = True
            row["functions"] = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
            row["classes"] = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
            row["imports"] = sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
        except Exception as e:
            row["message"] = "AST parse failed: " + str(e)

        try:
            py_compile.compile(str(path), doraise=True)
            row["compile_ok"] = True
        except Exception as e:
            row["message"] += " compile failed: " + str(e)[:240]

    elif ft == "ps1" or suffix == ".ps1":
        row["parse_ok"] = True
        row["compile_ok"] = True
        row["functions"] = len(re.findall(r"(?im)^\\s*function\\s+[A-Za-z0-9_\\-]+", text))

    score = 0
    if row["parse_ok"]: score += 15
    if row["compile_ok"]: score += 15
    if row["has_aegis_text"]: score += 20
    if row["has_celeritas_text"]: score += 20
    if row["has_envmanager_text"]: score += 10
    if row["has_timeout_text"] or row["has_watchdog_text"]: score += 10
    if not row["has_stop_process_risk"]: score += 10
    if row["has_v139o_marker"]: score += 5
    row["coverage_score"] = min(score, 105)

    if not row["parse_ok"] or not row["compile_ok"] or row["has_stop_process_risk"]:
        row["risk"] = "RED"
    elif not row["has_aegis_text"] or not row["has_celeritas_text"] or not row["has_envmanager_text"] or (not row["has_timeout_text"] and not row["has_watchdog_text"]):
        row["risk"] = "YELLOW"
    else:
        row["risk"] = "GREEN"

    row["anchor_hint"] = "covered" if row["risk"] == "GREEN" else "remaining coverage gap"
    return row

def def_build_remaining_plan(rows):
    plan = []
    for r in rows:
        if r["risk"] == "GREEN":
            continue
        action = []
        if not r["has_aegis_text"]: action.append("ADD_AEGIS_BRIDGE")
        if not r["has_celeritas_text"]: action.append("ADD_CELERITAS_BRIDGE")
        if not r["has_envmanager_text"]: action.append("ADD_ENVMANAGER_GATE")
        if not r["has_timeout_text"] and not r["has_watchdog_text"]: action.append("ADD_NOHANG_WATCHDOG")
        if r["has_stop_process_risk"]: action.append("REVIEW_STOP_PROCESS_RISK")
        plan.append({
            "path": r["path"],
            "file_type": r["file_type"],
            "risk": r["risk"],
            "coverage_score": r["coverage_score"],
            "action": " + ".join(action) if action else "REVIEW",
            "has_v139o_marker": r["has_v139o_marker"],
            "message": r["message"],
        })
    return plan

def def_table(rows, title, max_rows=1200):
    if not rows:
        return f"<section class='card'><h2>{title}</h2><p>EMPTY</p></section>"
    keys = list(rows[0].keys())
    th = "".join(f"<th>{def_html_escape(str(k).replace('_',' ').strip())}</th>" for k in keys)
    body = ""
    for r in rows[:max_rows]:
        body += "<tr>"
        for k in keys:
            v = r.get(k, "")
            kind = "long" if len(str(v)) > 42 or "\\" in str(v) or "/" in str(v) or k in ["path","message","action"] else "short"
            body += f"<td data-cell-kind='{kind}'>{def_html_escape(v)}</td>"
        body += "</tr>"
    return f"<section class='card'><h2>{title}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_make_html(matrix, modules, remaining, meta):
    meta_json = json.dumps(meta, ensure_ascii=False, indent=2)
    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN v139P Post-Bridge Rescore Matrix</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535}}
*{{box-sizing:border-box}}
html{{font-size:10.5px}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;font-size:9.6px;line-height:1.16}}
header{{position:relative;padding:13px 20px 9px;background:#fff;border-bottom:1px solid var(--border)}}
header:before{{content:"";position:absolute;left:20px;right:20px;top:0;height:3px;background:linear-gradient(90deg,#e74c3c,#f39c12,#f1c40f,#2ecc71,#3498db,#9b59b6)}}
h1{{margin:0;font-size:20px;line-height:1.02;font-weight:800;letter-spacing:-.035em}}
h2{{margin:0 0 5px;font-size:11.5px;line-height:1.08;font-weight:800}}
.sub{{margin-top:4px;color:var(--muted);font-family:Consolas,"Cascadia Mono",monospace;font-size:9px}}
main{{padding:9px 14px}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(68px,1fr));gap:5px;margin-bottom:7px}}
.kpi{{background:#fff;border:1px solid var(--border);border-radius:7px;padding:5px 6px;min-height:40px}}
.v{{font-size:14px;line-height:1.02;font-weight:800;text-align:center;vertical-align:top}}
.k{{color:var(--muted);font-size:8.4px;line-height:1.05;margin-top:2px;text-align:center;vertical-align:top}}
.ok{{color:var(--ok)}}.warn{{color:var(--warn)}}.err{{color:var(--err)}}
.card{{background:#fff;border:1px solid var(--border);border-radius:7px;padding:7px;margin-top:7px;box-shadow:0 1px 7px rgba(0,0,0,.028)}}
.scroll{{overflow:auto;max-height:79vh;border:1px solid var(--border);border-radius:6px;background:#fff}}
table{{border-collapse:collapse;table-layout:auto;width:max-content;min-width:100%;font-size:9.2px;line-height:1.12}}
th{{position:sticky;top:0;z-index:3;background:var(--head);font-weight:800;text-align:center!important;vertical-align:top!important;padding:2px 4px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere;word-break:normal;height:auto;min-width:38px;max-width:150px}}
td{{padding:2px 4px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top!important;text-align:center;white-space:nowrap;height:auto;min-height:14px;max-height:none}}
tbody tr:nth-child(even){{background:#fbfaf7}}
tbody tr:hover{{background:#f0f5fb}}
td[data-cell-kind="short"]{{text-align:center!important;vertical-align:top!important;white-space:nowrap!important;width:1%;min-width:32px;max-width:96px}}
td[data-cell-kind="long"]{{text-align:left!important;vertical-align:top!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important;min-width:120px;max-width:760px}}
.code{{font-family:Consolas,"Cascadia Mono",monospace;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:6px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:8.8px;max-height:38vh;overflow:auto}}
</style>
</head>
<body>
<header>
<h1>VRN v139P Post-Bridge Strict Production Rescore</h1>
<div class="sub">Verify v139O append-only bridge · strict production only · no patch · no DB / no SSOT / no network</div>
</header>
<main>
<div class="grid">
<div class="kpi"><div class="v {'ok' if meta['system_pass'] else 'warn'}">{meta['system_pass']}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v">{meta['target_count']}</div><div class="k">Targets</div></div>
<div class="kpi"><div class="v ok">{meta['green_count']}</div><div class="k">Green</div></div>
<div class="kpi"><div class="v warn">{meta['yellow_count']}</div><div class="k">Yellow</div></div>
<div class="kpi"><div class="v err">{meta['red_count']}</div><div class="k">Red</div></div>
<div class="kpi"><div class="v">{meta['marker_count']}</div><div class="k">v139O Marker</div></div>
<div class="kpi"><div class="v">{meta['elapsed_sec']}</div><div class="k">Elapsed</div></div>
<div class="kpi"><div class="v">False</div><div class="k">Patch</div></div>
</div>
<section class="card"><h2>Meta</h2><div class="code">{def_html_escape(meta_json)}</div></section>
{def_table(matrix, "System Matrix")}
{def_table(modules, "Post Bridge Strict Production Modules")}
{def_table(remaining, "Remaining Yellow / Red Plan")}
</main>
</body>
</html>"""
    Path(OUT_HTML).write_text(html_doc, encoding="utf-8-sig")

def def_main():
    t0 = datetime.now()
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)

    matrix = []
    def_add_matrix(matrix, "Safety", "PATCH_ENABLE", False, "LOCKED", "OK", "No source patch")
    def_add_matrix(matrix, "Safety", "DB_WRITE", False, "LOCKED", "OK", "No DB write")
    def_add_matrix(matrix, "Safety", "SSOT_MUTATION", False, "LOCKED", "OK", "No SSOT mutation")
    def_add_matrix(matrix, "Safety", "NETWORK", False, "LOCKED", "OK", "No network")

    n2_csv, n2_run = def_find_latest_n2_strict_csv()
    def_add_matrix(matrix, "Input", "LatestN2StrictCsv", n2_csv, "FOUND", "OK", "Latest v139N2 strict production CSV resolved")

    core = [
        ("VeritasAegisNexus", AEGIS_PATH),
        ("VeritasCeleritas", CELERITAS_PATH),
        ("VIA_EnvManager", ENV_MANAGER_PATH),
    ]

    core_results = []
    for label, path in core:
        r = def_import_core(label, path)
        core_results.append(r)
        ok = r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"]
        def_add_matrix(matrix, "CoreImport", label, path, "PASS" if ok else "FAIL", "OK" if ok else "ERR",
                       f"exists={r['exists']} ast={r['ast_ok']} compile={r['compile_ok']} import={r['import_ok']} def={r['functions']} cls={r['classes']}")

    input_rows = def_read_csv(n2_csv)
    modules = []
    for r in input_rows:
        path = r.get("Path") or r.get("path") or ""
        file_type = r.get("FileType") or r.get("File Type") or r.get("file_type") or Path(path).suffix.replace(".", "")
        if path and Path(path).exists():
            modules.append(def_analyze_file(path, file_type))
        else:
            modules.append({
                "file_type": file_type,
                "path": path,
                "sha1": "",
                "parse_ok": False,
                "compile_ok": False,
                "functions": 0,
                "classes": 0,
                "imports": 0,
                "has_aegis_text": False,
                "has_celeritas_text": False,
                "has_envmanager_text": False,
                "has_timeout_text": False,
                "has_watchdog_text": False,
                "has_stop_process_risk": False,
                "has_network_text": False,
                "has_v139o_marker": False,
                "risk": "RED",
                "coverage_score": 0,
                "anchor_hint": "missing file",
                "message": "file missing"
            })

    modules = sorted(modules, key=lambda x: ({"RED":0, "YELLOW":1, "GREEN":2}.get(x["risk"], 1), x["path"]))

    remaining = def_build_remaining_plan(modules)

    green = sum(1 for r in modules if r["risk"] == "GREEN")
    yellow = sum(1 for r in modules if r["risk"] == "YELLOW")
    red = sum(1 for r in modules if r["risk"] == "RED")
    marker_count = sum(1 for r in modules if r["has_v139o_marker"])

    all_core_ok = all(r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"] for r in core_results)
    system_pass = all_core_ok and red == 0 and yellow == 0
    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    def_add_matrix(matrix, "Rescore", "TargetCount", len(modules), "COUNTED", "OK", "Strict production modules rescored")
    def_add_matrix(matrix, "Rescore", "Green", green, "COUNTED", "OK", "Green production modules")
    def_add_matrix(matrix, "Rescore", "Yellow", yellow, "COUNTED", "OK" if yellow == 0 else "WARN", "Remaining yellow modules")
    def_add_matrix(matrix, "Rescore", "Red", red, "COUNTED", "OK" if red == 0 else "ERR", "Remaining red modules")
    def_add_matrix(matrix, "Rescore", "v139OMarker", marker_count, "COUNTED", "OK", "Modules containing v139O bridge marker")
    def_add_matrix(matrix, "Rescore", "SystemPass", system_pass, "PASS" if system_pass else "REVIEW", "OK" if system_pass else "WARN", "Post-bridge strict production score")

    def_write_csv(OUT_CSV, matrix)
    def_write_csv(OUT_MODULE_CSV, modules)
    def_write_csv(OUT_REMAINING_PLAN, remaining)

    meta = {
        "version": "VRN_V139P_POST_BRIDGE_STRICT_PRODUCTION_RESCORE",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "all_core_ok": all_core_ok,
        "target_count": len(modules),
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "marker_count": marker_count,
        "remaining_plan_count": len(remaining),
        "elapsed_sec": elapsed,
        "source_n2_run": n2_run,
        "source_n2_csv": n2_csv,
        "matrix_csv": OUT_CSV,
        "module_csv": OUT_MODULE_CSV,
        "remaining_plan_csv": OUT_REMAINING_PLAN,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "registry": OUT_REGISTRY,
        "patch_enable": False,
        "db_write": False,
        "ssot_mutation": False,
        "network": False,
    }

    Path(OUT_JSON).write_text(json.dumps({"meta": meta, "matrix": matrix, "core": core_results, "modules": modules, "remaining": remaining}, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    registry = ["VRN_V139P_POST_BRIDGE_RESCORE_REGISTRY"]
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_make_html(matrix, modules, remaining, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {"system_pass": False, "fatal": traceback.format_exc(), "run_dir": RUN_DIR}
        Path(OUT_JSON).write_text(json.dumps(fatal, ensure_ascii=False, indent=2), encoding="utf-8-sig")
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
