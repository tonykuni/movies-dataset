VIA_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
VRN_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
SUPPORTIVE_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER"

CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"
RUNTIME_BRIDGE_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py"
SSOT_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py"
REGISTRY_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py"

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_RedFalsePositiveCrusher_Matrix.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_RedFalsePositiveCrusher_Matrix.json"
OUT_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_RedFalsePositiveCrusher_Matrix.csv"
OUT_MODULE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_Module_Coverage_Detail.csv"
OUT_PATCH_PLAN = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_Precise_Anchor_Patch_Plan.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_155826_VRN_V139M_RED_FALSE_POSITIVE_CRUSHER\VRN_v139M_RedFalsePositiveCrusher_Registry.txt"

MAX_FILES = int(260)
MAX_THREADS = int(8)

import ast, csv, hashlib, html, importlib.util, json, py_compile, re, sys, traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def def_import_file(label, path):
    result = {
        "module": label, "path": str(path), "exists": False, "ast_ok": False,
        "compile_ok": False, "import_ok": False, "functions": 0, "classes": 0, "error": ""
    }
    p = Path(path)
    try:
        if not p.exists():
            result["error"] = "missing file"
            return result
        result["exists"] = True
        text = def_read_text(p)
        tree = ast.parse(text)
        result["ast_ok"] = True
        result["functions"] = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        result["classes"] = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        py_compile.compile(str(p), doraise=True)
        result["compile_ok"] = True
        spec = importlib.util.spec_from_file_location(label, str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[label] = mod
        spec.loader.exec_module(mod)
        result["import_ok"] = True
        return result
    except Exception:
        result["error"] = traceback.format_exc()
        return result

def def_is_archive_or_generated(p):
    s = str(p).lower()
    name = p.name.lower()

    deny_parts = [
        "\\\\output\\\\", "\\\\_route_lock_runs\\\\", "\\\\_local_runs\\\\", "\\\\_gonow_runs\\\\",
        "\\\\_allinone_runs\\\\", "\\\\_backup", "\\\\backup\\\\", "\\\\bak\\\\", "\\\\__pycache__\\\\",
        "\\\\.venv", "\\\\site-packages\\\\", "\\\\others\\\\runs\\\\", "\\\\others\\\\",
        "\\\\archive\\\\", "\\\\old\\\\", "\\\\tmp\\\\", "\\\\temp\\\\", "\\\\work\\\\",
        "\\\\final_verify_copy", "\\\\verify_copy", "\\\\.bak", "\\\\.backup"
    ]

    deny_name_tokens = [
        ".bak", ".backup", ".tmp", ".work", "backup", "before_", "after_",
        "verify_copy", "final_verify_copy", "joined_", "copy"
    ]

    if any(x in s for x in deny_parts):
        return True
    if any(x in name for x in deny_name_tokens):
        return True
    return False

def def_is_production_candidate(p):
    if def_is_archive_or_generated(p):
        return False

    s = str(p).lower()
    name = p.name.lower()

    # keep root VRN production files
    if str(Path(VRN_ROOT)).lower() in s:
        if "\\\\output\\\\" in s:
            return False
        if name in [
            "vrn_go.ps1",
            "vrn_pipeline_launcher.ps1",
            "vrn_bridge_resolver_v2.ps1",
            "vrn_doctor.py",
            "activate_and_cross_validate.py",
            "activate_and_cross_validate_fast_wrapper.py",
        ]:
            return True
        if re.search(r"^vrn_mdl\\d+.*\\.py$", name):
            return True
        if any(x in name for x in ["officialconnector", "hardgate", "runtime", "bridge", "cross_validate", "yfinance"]):
            return True

    # keep main supportive files only, not runs/others
    if str(Path(SUPPORTIVE_DIR)).lower() in s:
        if "\\\\others\\\\" in s or "\\\\runs\\\\" in s:
            return False
        if name.endswith(".py") or name.endswith(".ps1"):
            return True

    return False

def def_scan_files_fast():
    roots = [Path(VRN_ROOT), Path(SUPPORTIVE_DIR)]
    files = []
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        for ext in ["*.py", "*.ps1"]:
            for p in root.rglob(ext):
                sp = str(p).lower()
                if sp in seen:
                    continue
                seen.add(sp)
                if def_is_production_candidate(p):
                    files.append(p)
                if len(files) >= MAX_FILES:
                    return files
    return files

def def_strip_ps_comments(text):
    out = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)

def def_has_real_stop_risk(path, text, file_type):
    lower = text.lower()
    name = Path(path).name.lower()

    # false positive: docs / analyzer / matrix generator containing the string only
    if any(x in name for x in ["analyzer", "matrix", "report", "scanner", "audit"]):
        if "stop-process" in lower and "no stop-process" in lower:
            return False

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
                    if isinstance(f, ast.Attribute) and f.attr == "kill":
                        return True
                    if isinstance(f, ast.Name) and f.id in ["kill", "terminate"]:
                        return True
        except Exception:
            return ".kill(" in lower or "os.kill" in lower
    return False

def def_analyze_python(path):
    text = def_read_text(path)
    lower = text.lower()
    row = {
        "file_type": "py", "path": str(path), "sha1": def_sha1(path),
        "parse_ok": False, "compile_ok": False, "functions": 0, "classes": 0, "imports": 0,
        "has_aegis_text": "veritasaegisnexus" in lower or "aegis" in lower,
        "has_celeritas_text": "veritasceleritas" in lower or "celeritas" in lower,
        "has_envmanager_text": "via_envmanager" in lower or "envmanager" in lower,
        "has_timeout_text": "timeout" in lower,
        "has_watchdog_text": "watchdog" in lower or "nohang" in lower,
        "has_stop_process_risk": False,
        "has_network_text": any(x in lower for x in ["requests", "urllib", "yfinance", "httpx", "openapi", "twstock", "finmind"]),
        "risk": "UNKNOWN", "coverage_score": 0, "anchor_hint": "", "message": ""
    }

    row["has_stop_process_risk"] = def_has_real_stop_risk(path, text, "py")

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

    score = 0
    if row["parse_ok"]: score += 15
    if row["compile_ok"]: score += 15
    if row["has_aegis_text"]: score += 20
    if row["has_celeritas_text"]: score += 20
    if row["has_envmanager_text"]: score += 10
    if row["has_timeout_text"] or row["has_watchdog_text"]: score += 10
    if not row["has_stop_process_risk"]: score += 10
    row["coverage_score"] = score

    if not row["parse_ok"] or not row["compile_ok"] or row["has_stop_process_risk"]:
        row["risk"] = "RED"
    elif not row["has_aegis_text"] or not row["has_celeritas_text"]:
        row["risk"] = "YELLOW"
    else:
        row["risk"] = "GREEN"

    row["anchor_hint"] = "covered" if row["risk"] == "GREEN" else "append guarded import bridge under AI_APPEND_ONLY anchor"
    return row

def def_analyze_powershell(path):
    text = def_read_text(path)
    lower = text.lower()
    row = {
        "file_type": "ps1", "path": str(path), "sha1": def_sha1(path),
        "parse_ok": True, "compile_ok": True,
        "functions": len(re.findall(r"(?im)^\\s*function\\s+[A-Za-z0-9_\\-]+", text)),
        "classes": 0,
        "imports": len(re.findall(r"(?im)Import-Module|\\.\\s+['\\\"]", text)),
        "has_aegis_text": "veritasaegisnexus" in lower or "aegis" in lower,
        "has_celeritas_text": "veritasceleritas" in lower or "celeritas" in lower,
        "has_envmanager_text": "via_envmanager" in lower or "envmanager" in lower,
        "has_timeout_text": "timeout" in lower,
        "has_watchdog_text": "watchdog" in lower or "nohang" in lower,
        "has_stop_process_risk": False,
        "has_network_text": any(x in lower for x in ["invoke-webrequest", "invoke-restmethod", "pip install", "openapi"]),
        "risk": "UNKNOWN", "coverage_score": 0, "anchor_hint": "", "message": ""
    }

    row["has_stop_process_risk"] = def_has_real_stop_risk(path, text, "ps1")

    score = 30
    if row["has_aegis_text"]: score += 20
    if row["has_celeritas_text"]: score += 20
    if row["has_envmanager_text"]: score += 10
    if row["has_timeout_text"] or row["has_watchdog_text"]: score += 10
    if not row["has_stop_process_risk"]: score += 10
    row["coverage_score"] = score

    if row["has_stop_process_risk"]:
        row["risk"] = "RED"
    elif not row["has_aegis_text"] or not row["has_celeritas_text"]:
        row["risk"] = "YELLOW"
    else:
        row["risk"] = "GREEN"

    row["anchor_hint"] = "covered" if row["risk"] == "GREEN" else "add launcher bridge variables for Aegis/Celeritas/EnvManager"
    return row

def def_analyze_file(path):
    try:
        if path.suffix.lower() == ".py":
            return def_analyze_python(path)
        if path.suffix.lower() == ".ps1":
            return def_analyze_powershell(path)
    except Exception as e:
        return {
            "file_type": path.suffix.lower(), "path": str(path), "sha1": def_sha1(path),
            "parse_ok": False, "compile_ok": False, "functions": 0, "classes": 0, "imports": 0,
            "has_aegis_text": False, "has_celeritas_text": False, "has_envmanager_text": False,
            "has_timeout_text": False, "has_watchdog_text": False, "has_stop_process_risk": False,
            "has_network_text": False, "risk": "RED", "coverage_score": 0,
            "anchor_hint": "review", "message": str(e)
        }
    return None

def def_build_patch_plan(rows):
    plan = []
    for r in rows:
        if r["risk"] == "GREEN":
            continue
        action = []
        if r["risk"] == "RED":
            action.append("REVIEW_RED_REAL_RISK")
        if not r["has_aegis_text"]:
            action.append("ADD_AEGIS_BRIDGE")
        if not r["has_celeritas_text"]:
            action.append("ADD_CELERITAS_BRIDGE")
        if not r["has_envmanager_text"]:
            action.append("ADD_ENVMANAGER_GATE")
        if not r["has_timeout_text"] and not r["has_watchdog_text"]:
            action.append("ADD_NOHANG_WATCHDOG")
        plan.append({
            "path": r["path"],
            "file_type": r["file_type"],
            "risk": r["risk"],
            "coverage_score": r["coverage_score"],
            "action": " + ".join(action),
            "anchor": r["anchor_hint"],
            "patch_enable": False,
            "message": "Plan only; no file modified"
        })
    return plan

def def_table(rows, title, max_rows=1000):
    if not rows:
        return f"<section class='card'><h2>{title}</h2><p>EMPTY</p></section>"
    keys = list(rows[0].keys())
    th = "".join(f"<th>{def_html_escape(k).replace('_',' ').title()}</th>" for k in keys)
    body = ""
    for r in rows[:max_rows]:
        body += "<tr>"
        for k in keys:
            v = r.get(k, "")
            cls = "long" if len(str(v)) > 34 or "\\" in str(v) or "/" in str(v) else ""
            body += f"<td class='{cls}'>{def_html_escape(v)}</td>"
        body += "</tr>"
    return f"<section class='card'><h2>{title}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_make_html(matrix, modules, patch_plan, meta):
    css = """
<style>
:root{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:'Segoe UI','Microsoft JhengHei',Arial,sans-serif;font-size:10.2px;line-height:1.22}
header{position:relative;padding:15px 22px 11px;background:#fff;border-bottom:1px solid var(--border)}
header:before{content:'';position:absolute;left:22px;right:22px;top:0;height:3px;background:linear-gradient(90deg,#e74c3c,#f39c12,#f1c40f,#2ecc71,#3498db,#9b59b6)}
h1{margin:0;font-size:22px;line-height:1.04;font-weight:800;letter-spacing:-.035em}
h2{margin:0 0 6px;font-size:12.5px}
.sub{font-family:Consolas,monospace;color:var(--muted);margin-top:5px;font-size:9.8px}
main{padding:11px 18px}
.grid{display:grid;grid-template-columns:repeat(8,minmax(82px,1fr));gap:6px;margin-bottom:8px}
.kpi{background:#fff;border:1px solid var(--border);border-radius:8px;padding:6px 8px;min-height:46px}
.v{font-size:15.5px;font-weight:800;text-align:center}.k{color:var(--muted);font-size:9px;text-align:center;margin-top:3px}
.ok{color:var(--ok)}.warn{color:var(--warn)}.err{color:var(--err)}
.card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:8px;margin-top:8px;box-shadow:0 2px 8px rgba(0,0,0,.032)}
.scroll{overflow:auto;max-height:78vh;border:1px solid var(--border);border-radius:7px;background:#fff}
table{border-collapse:collapse;table-layout:auto;width:max-content;min-width:100%;font-size:9.8px;line-height:1.16}
th{position:sticky;top:0;z-index:3;background:var(--head);font-weight:800;text-align:center;vertical-align:top;padding:3px 5px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere}
td{padding:3px 5px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:nowrap;height:auto}
tbody tr:nth-child(even){background:#fbfaf7} tbody tr:hover{background:#f0f5fb}
.long{text-align:left!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important;min-width:90px;max-width:680px}
.code{font-family:Consolas,monospace;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:9.4px;max-height:42vh;overflow:auto}
</style>
"""
    html_doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN v139M Red False-Positive Crusher Matrix</title>{css}</head><body>
<header><h1>VRN v139M Red False-Positive Crusher Matrix</h1>
<div class="sub">Production files only · false-red crusher · dual-core hardgate · no DB / no SSOT</div></header>
<main>
<div class="grid">
<div class="kpi"><div class="v {'ok' if meta['system_pass'] else 'warn'}">{meta['system_pass']}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v {'ok' if meta['dual_core_pass'] else 'err'}">{meta['dual_core_pass']}</div><div class="k">Dual Core Pass</div></div>
<div class="kpi"><div class="v">{meta['files_scanned']}</div><div class="k">Files Scanned</div></div>
<div class="kpi"><div class="v ok">{meta['green_count']}</div><div class="k">Green</div></div>
<div class="kpi"><div class="v warn">{meta['yellow_count']}</div><div class="k">Yellow</div></div>
<div class="kpi"><div class="v err">{meta['red_count']}</div><div class="k">Red</div></div>
<div class="kpi"><div class="v">{meta['patch_plan_count']}</div><div class="k">Patch Plan</div></div>
<div class="kpi"><div class="v">{meta['elapsed_sec']}</div><div class="k">Elapsed Sec</div></div>
</div>
<section class="card"><h2>Meta</h2><div class="code">{def_html_escape(json.dumps(meta, ensure_ascii=False, indent=2))}</div></section>
{def_table(matrix, "System Matrix")}
{def_table(modules, "Module Coverage Detail", 1200)}
{def_table(patch_plan, "Precise Anchor Patch Plan", 1200)}
</main></body></html>"""
    Path(OUT_HTML).write_text(html_doc, encoding="utf-8-sig")

def def_main():
    t0 = datetime.now()
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)
    matrix = []

    for gate, val, msg in [
        ("DB_WRITE", False, "No DB write"),
        ("SSOT_MUTATION", False, "No SSOT mutation"),
        ("NETWORK_ENABLE", False, "No live network"),
        ("PATCH_ENABLE", False, "Plan only"),
        ("FALSE_RED_CRUSHER", "ON", "Exclude generated/archive/venv/output/others/runs"),
        ("PRODUCTION_ONLY", "ON", "Only current root modules and main supportive files"),
        ("THREADPOOL", MAX_THREADS, "Parallel scan"),
    ]:
        def_add_matrix(matrix, "Safety", gate, val, "LOCKED" if val is False else "ENABLED", "OK", msg)

    core = [
        ("VeritasCeleritas", CELERITAS_PATH),
        ("VeritasAegisNexus", AEGIS_PATH),
        ("VIA_EnvManager", ENV_MANAGER_PATH),
        ("VIA_Runtime_Bridge", RUNTIME_BRIDGE_PATH),
        ("VIA_SSOT_Unified", SSOT_PATH),
        ("VIA_RegistryCore", REGISTRY_PATH),
    ]

    core_results = []
    for label, path in core:
        res = def_import_file(label, path)
        core_results.append(res)
        ok = res["exists"] and res["ast_ok"] and res["compile_ok"] and res["import_ok"]
        def_add_matrix(matrix, "CoreImport", label, path, "PASS" if ok else "FAIL", "OK" if ok else "ERR",
                       f"exists={res['exists']} ast={res['ast_ok']} compile={res['compile_ok']} import={res['import_ok']} def={res['functions']} cls={res['classes']} {res['error'][:200]}")

    files = def_scan_files_fast()
    def_add_matrix(matrix, "Scan", "ProductionTargetFiles", len(files), "SCANNED", "OK", "False-red filtered production scan completed")

    modules = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        futures = {ex.submit(def_analyze_file, p): p for p in files}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    modules.append(r)
            except Exception as e:
                p = futures[fut]
                modules.append({
                    "file_type": p.suffix.lower(), "path": str(p), "sha1": def_sha1(p),
                    "parse_ok": False, "compile_ok": False, "functions": 0, "classes": 0, "imports": 0,
                    "has_aegis_text": False, "has_celeritas_text": False, "has_envmanager_text": False,
                    "has_timeout_text": False, "has_watchdog_text": False, "has_stop_process_risk": False,
                    "has_network_text": False, "risk": "RED", "coverage_score": 0,
                    "anchor_hint": "review", "message": str(e)
                })

    modules = sorted(modules, key=lambda x: ({"RED":0, "YELLOW":1, "GREEN":2}.get(x["risk"], 1), x["path"]))
    patch_plan = def_build_patch_plan(modules)

    green = sum(1 for r in modules if r["risk"] == "GREEN")
    yellow = sum(1 for r in modules if r["risk"] == "YELLOW")
    red = sum(1 for r in modules if r["risk"] == "RED")

    def_write_csv(OUT_CSV, matrix)
    def_write_csv(OUT_MODULE_CSV, modules)
    def_write_csv(OUT_PATCH_PLAN, patch_plan)

    dual_core_pass = all(r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"] for r in core_results[:2])
    all_core_pass = all(r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"] for r in core_results)

    system_pass = dual_core_pass and all_core_pass and red == 0
    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": "VRN_V139M_RED_FALSE_POSITIVE_CRUSHER",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "dual_core_pass": dual_core_pass,
        "all_core_pass": all_core_pass,
        "files_scanned": len(files),
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "patch_plan_count": len(patch_plan),
        "elapsed_sec": elapsed,
        "max_threads": MAX_THREADS,
        "max_files": MAX_FILES,
        "aegis_path": AEGIS_PATH,
        "celeritas_path": CELERITAS_PATH,
        "env_manager_path": ENV_MANAGER_PATH,
        "module_detail_csv": OUT_MODULE_CSV,
        "patch_plan_csv": OUT_PATCH_PLAN,
        "matrix_csv": OUT_CSV,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "registry": OUT_REGISTRY,
        "db_write": False,
        "ssot_mutation": False,
        "patch_enable": False
    }

    Path(OUT_JSON).write_text(json.dumps({"meta": meta, "matrix": matrix, "core": core_results, "modules": modules, "patch_plan": patch_plan}, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    registry = ["VRN_V139M_RED_FALSE_POSITIVE_CRUSHER_REGISTRY"]
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    registry.append("false_red_crusher=YES")
    registry.append("production_only=YES")
    registry.append("no_db_write=YES")
    registry.append("no_ssot_mutation=YES")
    registry.append("no_destructive_patch=YES")
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_make_html(matrix, modules, patch_plan, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {"system_pass": False, "fatal": traceback.format_exc(), "run_dir": RUN_DIR}
        Path(OUT_JSON).write_text(json.dumps(fatal, ensure_ascii=False, indent=2), encoding="utf-8-sig")
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
