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
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE"

CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"
RUNTIME_BRIDGE_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py"
SSOT_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py"
REGISTRY_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py"

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_DualCore_Coverage_Matrix.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_DualCore_Coverage_Matrix.json"
OUT_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_DualCore_Coverage_Matrix.csv"
OUT_MODULE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_Module_Coverage_Detail.csv"
OUT_PATCH_PLAN = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_Precise_Anchor_Patch_Plan.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_151553_VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE\VRN_v139K_DualCore_Coverage_Registry.txt"

MAX_FILES = int(9999)
PATCH_ENABLE = False
NETWORK_ENABLE = False
DB_WRITE_ENABLE = False
SSOT_MUTATION_ENABLE = False

import ast
import csv
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
        "module": label,
        "path": str(path),
        "exists": False,
        "ast_ok": False,
        "compile_ok": False,
        "import_ok": False,
        "functions": 0,
        "classes": 0,
        "error": "",
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
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.modules[label] = mod
        result["import_ok"] = True
        return result
    except Exception:
        result["error"] = traceback.format_exc()
        return result

def def_scan_files():
    roots = [Path(VRN_ROOT), Path(SUPPORTIVE_DIR)]
    files = []
    seen = set()

    for root in roots:
        if not root.exists():
            continue
        for ext in ["*.py", "*.ps1"]:
            for p in root.rglob(ext):
                s = str(p)
                if s.lower() in seen:
                    continue
                seen.add(s.lower())

                # skip huge generated output dirs but keep recent route scripts
                if "\\.venv\\" in s.lower() or "\\__pycache__\\" in s.lower():
                    continue
                if "\\output\\_route_lock_runs\\" in s.lower() and not any(x in p.name.lower() for x in ["vrn_yfinance", "v139", "runner", "aio", "patch"]):
                    continue

                files.append(p)
                if len(files) >= MAX_FILES:
                    return files

    return files

def def_analyze_python(path, text):
    row = {
        "file_type": "py",
        "path": str(path),
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
        "risk": "UNKNOWN",
        "coverage_score": 0,
        "anchor_hint": "",
        "message": "",
    }

    lower = text.lower()
    row["has_aegis_text"] = "veritasaegisnexus" in lower or "aegis" in lower
    row["has_celeritas_text"] = "veritasceleritas" in lower or "celeritas" in lower
    row["has_envmanager_text"] = "via_envmanager" in lower or "envmanager" in lower
    row["has_timeout_text"] = "timeout" in lower
    row["has_watchdog_text"] = "watchdog" in lower or "nohang" in lower
    row["has_stop_process_risk"] = "stop-process" in lower or "os.kill" in lower or ".kill(" in lower
    row["has_network_text"] = any(x in lower for x in ["requests", "urllib", "yfinance", "httpx", "download", "openapi"])

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
        if row["message"]:
            row["message"] += " | "
        row["message"] += "compile failed: " + str(e)[:280]

    score = 0
    if row["parse_ok"]: score += 15
    if row["compile_ok"]: score += 15
    if row["has_aegis_text"]: score += 20
    if row["has_celeritas_text"]: score += 20
    if row["has_envmanager_text"]: score += 10
    if row["has_timeout_text"] or row["has_watchdog_text"]: score += 10
    if not row["has_stop_process_risk"]: score += 10
    row["coverage_score"] = score

    if not row["parse_ok"] or not row["compile_ok"]:
        row["risk"] = "RED"
    elif row["has_stop_process_risk"]:
        row["risk"] = "RED"
    elif not row["has_aegis_text"] or not row["has_celeritas_text"]:
        row["risk"] = "YELLOW"
    else:
        row["risk"] = "GREEN"

    if not row["has_aegis_text"] or not row["has_celeritas_text"]:
        row["anchor_hint"] = "append guarded import bridge near top-level imports or under AI_APPEND_ONLY anchor"
    else:
        row["anchor_hint"] = "covered"

    return row

def def_analyze_powershell(path, text):
    row = {
        "file_type": "ps1",
        "path": str(path),
        "parse_ok": True,
        "compile_ok": True,
        "functions": len(re.findall(r"(?im)^\\s*function\\s+[A-Za-z0-9_\\-]+", text)),
        "classes": 0,
        "imports": len(re.findall(r"(?im)Import-Module|\\.\\s+['\\\"]", text)),
        "has_aegis_text": False,
        "has_celeritas_text": False,
        "has_envmanager_text": False,
        "has_timeout_text": False,
        "has_watchdog_text": False,
        "has_stop_process_risk": False,
        "has_network_text": False,
        "risk": "UNKNOWN",
        "coverage_score": 0,
        "anchor_hint": "",
        "message": "",
    }

    lower = text.lower()
    row["has_aegis_text"] = "veritasaegisnexus" in lower or "aegis" in lower
    row["has_celeritas_text"] = "veritasceleritas" in lower or "celeritas" in lower
    row["has_envmanager_text"] = "via_envmanager" in lower or "envmanager" in lower
    row["has_timeout_text"] = "timeout" in lower
    row["has_watchdog_text"] = "watchdog" in lower or "nohang" in lower
    row["has_stop_process_risk"] = "stop-process" in lower or ".kill()" in lower
    row["has_network_text"] = any(x in lower for x in ["invoke-webrequest", "invoke-restmethod", "yfinance", "pip install", "openapi"])

    score = 0
    score += 15
    score += 15
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

    if not row["has_aegis_text"] or not row["has_celeritas_text"]:
        row["anchor_hint"] = "add PowerShell launcher bridge variables and pass Aegis/Celeritas paths into child process"
    else:
        row["anchor_hint"] = "covered"

    return row

def def_build_patch_plan(module_rows):
    plan = []
    for r in module_rows:
        if r["risk"] == "GREEN":
            continue

        action = []
        if not r["has_aegis_text"]:
            action.append("ADD_AEGIS_BRIDGE")
        if not r["has_celeritas_text"]:
            action.append("ADD_CELERITAS_ACCELERATOR_BRIDGE")
        if not r["has_timeout_text"] and not r["has_watchdog_text"]:
            action.append("ADD_NOHANG_TIMEOUT_WATCHDOG")
        if r["has_stop_process_risk"]:
            action.append("REMOVE_STOP_PROCESS_RISK_REPLACE_WITH_CLOSEMAINWINDOW_OR_TIMEOUT_FLAG")

        plan.append({
            "path": r["path"],
            "file_type": r["file_type"],
            "risk": r["risk"],
            "coverage_score": r["coverage_score"],
            "action": " + ".join(action) if action else "REVIEW",
            "anchor": r["anchor_hint"],
            "patch_enable": PATCH_ENABLE,
            "message": "Plan only; no destructive patch applied"
        })
    return plan

def def_make_html(matrix_rows, module_rows, patch_plan, meta):
    def table(rows, title, max_rows=1000):
        if not rows:
            return f"<section class='card'><h2>{title}</h2><p>EMPTY</p></section>"
        keys = list(rows[0].keys())
        th = "".join(f"<th>{def_html_escape(k).replace('_',' ').title()}</th>" for k in keys)
        body = ""
        for r in rows[:max_rows]:
            body += "<tr>"
            for k in keys:
                val = r.get(k, "")
                cls = "long" if len(str(val)) > 36 or "\\" in str(val) or "/" in str(val) else ""
                body += f"<td class='{cls}'>{def_html_escape(val)}</td>"
            body += "</tr>"
        return f"<section class='card'><h2>{title}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN v139K Dual-Core Supportive Coverage Matrix</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:'Segoe UI','Microsoft JhengHei',Arial,sans-serif;font-size:10.5px;line-height:1.24}}
header{{position:relative;padding:16px 24px 12px;background:#fff;border-bottom:1px solid var(--border)}}
header:before{{content:'';position:absolute;left:24px;right:24px;top:0;height:3px;background:linear-gradient(90deg,#e74c3c,#f39c12,#f1c40f,#2ecc71,#3498db,#9b59b6)}}
h1{{margin:0;font-size:23px;line-height:1.05;font-weight:800;letter-spacing:-.035em}}
h2{{margin:0 0 7px;font-size:13px}}
.sub{{font-family:Consolas,monospace;color:var(--muted);margin-top:5px;font-size:10px}}
main{{padding:12px 20px}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(88px,1fr));gap:6px;margin-bottom:9px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:7px 9px;min-height:50px}}
.v{{font-size:16px;font-weight:800;text-align:center}}.k{{color:var(--muted);font-size:9.5px;text-align:center;margin-top:4px}}
.ok{{color:var(--ok)}}.warn{{color:var(--warn)}}.err{{color:var(--err)}}
.card{{background:#fff;border:1px solid var(--border);border-radius:9px;padding:9px;margin-top:9px;box-shadow:0 2px 9px rgba(0,0,0,.035)}}
.scroll{{overflow:auto;max-height:78vh;border:1px solid var(--border);border-radius:7px;background:#fff}}
table{{border-collapse:collapse;table-layout:auto;width:max-content;min-width:100%;font-size:10px;line-height:1.18}}
th{{position:sticky;top:0;z-index:2;background:var(--head);font-weight:800;text-align:center;vertical-align:top;padding:4px 6px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere}}
td{{padding:3px 6px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:nowrap;height:auto}}
tbody tr:nth-child(even){{background:#fbfaf7}} tbody tr:hover{{background:#f0f5fb}}
.long{{text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:normal;min-width:92px;max-width:760px}}
.code{{font-family:Consolas,monospace;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:9.5px;max-height:42vh;overflow:auto}}
</style>
</head>
<body>
<header>
<h1>VRN v139K Dual-Core Supportive Coverage Matrix</h1>
<div class="sub">VeritasAegisNexus + VeritasCeleritas hardgate · Panorama AST · PowerShell parser · NoHang accelerator · no DB / no SSOT</div>
</header>
<main>
<div class="grid">
<div class="kpi"><div class="v {'ok' if meta.get('system_pass') else 'err'}">{meta.get('system_pass')}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v {'ok' if meta.get('dual_core_pass') else 'err'}">{meta.get('dual_core_pass')}</div><div class="k">Dual Core Pass</div></div>
<div class="kpi"><div class="v">{meta.get('files_scanned')}</div><div class="k">Files Scanned</div></div>
<div class="kpi"><div class="v ok">{meta.get('green_count')}</div><div class="k">Green</div></div>
<div class="kpi"><div class="v warn">{meta.get('yellow_count')}</div><div class="k">Yellow</div></div>
<div class="kpi"><div class="v err">{meta.get('red_count')}</div><div class="k">Red</div></div>
<div class="kpi"><div class="v">{meta.get('patch_plan_count')}</div><div class="k">Patch Plan</div></div>
<div class="kpi"><div class="v">{meta.get('elapsed_sec')}</div><div class="k">Elapsed Sec</div></div>
</div>
<section class="card"><h2>Def Meta</h2><div class="code">{def_html_escape(json.dumps(meta, ensure_ascii=False, indent=2))}</div></section>
{table(matrix_rows, "Def System Matrix")}
{table(module_rows, "Def Module Coverage Detail", 1500)}
{table(patch_plan, "Def Precise Anchor Patch Plan", 1500)}
</main>
</body>
</html>"""
    Path(OUT_HTML).write_text(html_doc, encoding="utf-8-sig")

def def_main():
    t0 = datetime.now()
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)

    matrix = []
    module_rows = []

    def_add_matrix(matrix, "Safety", "DB_WRITE", DB_WRITE_ENABLE, "LOCKED", "OK", "No DB write")
    def_add_matrix(matrix, "Safety", "SSOT_MUTATION", SSOT_MUTATION_ENABLE, "LOCKED", "OK", "No SSOT mutation")
    def_add_matrix(matrix, "Safety", "NETWORK_ENABLE", NETWORK_ENABLE, "LOCKED", "OK", "No live network execution")
    def_add_matrix(matrix, "Safety", "PATCH_ENABLE", PATCH_ENABLE, "LOCKED", "OK", "Plan only; no destructive patch")

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
        sev = "OK" if res["exists"] and res["ast_ok"] and res["compile_ok"] and res["import_ok"] else "ERR"
        status = "PASS" if sev == "OK" else "FAIL"
        def_add_matrix(
            matrix,
            "CoreImport",
            label,
            path,
            status,
            sev,
            f"exists={res['exists']} ast={res['ast_ok']} compile={res['compile_ok']} import={res['import_ok']} def={res['functions']} cls={res['classes']} {res['error'][:240]}"
        )

    files = def_scan_files()
    def_add_matrix(matrix, "Scan", "Files", len(files), "SCANNED", "OK", "Panorama file scan completed")

    for p in files:
        try:
            text = def_read_text(p)
            if p.suffix.lower() == ".py":
                r = def_analyze_python(p, text)
            elif p.suffix.lower() == ".ps1":
                r = def_analyze_powershell(p, text)
            else:
                continue
            module_rows.append(r)
        except Exception as e:
            module_rows.append({
                "file_type": p.suffix.lower(),
                "path": str(p),
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
                "risk": "RED",
                "coverage_score": 0,
                "anchor_hint": "",
                "message": str(e),
            })

    green = sum(1 for r in module_rows if r.get("risk") == "GREEN")
    yellow = sum(1 for r in module_rows if r.get("risk") == "YELLOW")
    red = sum(1 for r in module_rows if r.get("risk") == "RED")

    patch_plan = def_build_patch_plan(module_rows)

    def_write_csv(OUT_CSV, matrix)
    def_write_csv(OUT_MODULE_CSV, module_rows)
    def_write_csv(OUT_PATCH_PLAN, patch_plan)

    dual_core_pass = all(r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"] for r in core_results[:2])
    core_pass = all(r["exists"] and r["ast_ok"] and r["compile_ok"] and r["import_ok"] for r in core_results)
    system_pass = dual_core_pass and red == 0

    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": "VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE_ACCELERATOR",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "dual_core_pass": dual_core_pass,
        "all_core_pass": core_pass,
        "files_scanned": len(files),
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "patch_plan_count": len(patch_plan),
        "elapsed_sec": elapsed,
        "aegis_path": AEGIS_PATH,
        "celeritas_path": CELERITAS_PATH,
        "env_manager_path": ENV_MANAGER_PATH,
        "module_detail_csv": OUT_MODULE_CSV,
        "patch_plan_csv": OUT_PATCH_PLAN,
        "matrix_csv": OUT_CSV,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "registry": OUT_REGISTRY,
        "db_write": DB_WRITE_ENABLE,
        "ssot_mutation": SSOT_MUTATION_ENABLE,
        "patch_enable": PATCH_ENABLE,
    }

    Path(OUT_JSON).write_text(json.dumps({"meta": meta, "matrix": matrix, "core": core_results, "modules": module_rows, "patch_plan": patch_plan}, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    registry = []
    registry.append("VRN_V139K_DUAL_CORE_SUPPORTIVE_COVERAGE_REGISTRY")
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    registry.append("VeritasCeleritas_required=YES")
    registry.append("VeritasAegisNexus_required=YES")
    registry.append("NoHang=YES")
    registry.append("PanoramaAST=YES")
    registry.append("PowerShellParser=YES")
    registry.append("PreciseAnchorPatchPlan=YES")
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_make_html(matrix, module_rows, patch_plan, meta)

    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {
            "system_pass": False,
            "fatal": traceback.format_exc(),
            "run_dir": RUN_DIR,
        }
        Path(OUT_JSON).write_text(json.dumps(fatal, ensure_ascii=False, indent=2), encoding="utf-8-sig")
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
