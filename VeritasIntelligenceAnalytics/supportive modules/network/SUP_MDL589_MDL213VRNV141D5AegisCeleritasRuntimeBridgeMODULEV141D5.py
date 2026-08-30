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
VERSION = "v1.0.41D5"
VRN_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
VRN_MODULE_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\modules"
INPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\input"
OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output"
TEMP_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp"
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE"

AEGIS = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
CELERITAS = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
ENV_MANAGER = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"
V139G_LIBS_JSON = r"C:\Users\tonyk\Downloads\v139g_libs.json"

APPROVE_SAFE_INSTALL = false
APPROVE_MEDIUM_RISK_INSTALL = false

DB_WRITE_ENABLE = False
SSOT_MUTATION_ENABLE = False
SOURCE_PATCH_ENABLE = False
NETWORK_DATA_FETCH_ENABLE = False

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_Aegis_Celeritas_Runtime_Bridge.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_Aegis_Celeritas_Runtime_Bridge.json"
OUT_MATRIX_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_Runtime_Bridge_Matrix.csv"
OUT_CORE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_Core_Tool_Import_Check.csv"
OUT_LIB_PLAN_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_20Lib_Safe_Approval_Plan.csv"
OUT_IMPORT_PROBE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_20Lib_Import_Probe.csv"
OUT_INSTALL_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_20Lib_Install_Result.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_runtime_bridge_runs\RUN_20260527_014918_VRN_V141D5_AEGIS_CELERITAS_MANDATORY_BRIDGE\VRN_v141D5_AEGIS_CELERITAS_RUNTIME_BRIDGE_REGISTRY.txt"

import csv
import html
import importlib
import importlib.util
import inspect
import json
import os
import py_compile
import subprocess
import sys
import traceback
from pathlib import Path
from datetime import datetime

def def_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def def_html_escape(x):
    return html.escape("" if x is None else str(x))

def def_status_lamp(status):
    s = str(status).upper()
    if s == "PASS":
        return "🟢 PASS"
    if s == "WARN":
        return "🟡 WARN"
    return "🔴 FAIL"

def def_write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        Path(path).write_text("", encoding="utf-8-sig")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def def_write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8-sig")

def def_add_matrix(rows, category, item, value, expected, passed, severity, note):
    rows.append({
        "Validation Status": def_status_lamp("PASS" if passed else ("WARN" if severity == "WARN" else "FAIL")),
        "Time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "Category": category,
        "Item": item,
        "Value": "" if value is None else str(value),
        "Expected": "" if expected is None else str(expected),
        "Pass": bool(passed),
        "Severity": severity,
        "Validation Note": "" if note is None else str(note)
    })

def def_import_file(path, name):
    p = Path(path)
    if not p.exists():
        return None, "missing"
    try:
        py_compile.compile(str(p), doraise=True)
        spec = importlib.util.spec_from_file_location(name, str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception:
        return None, traceback.format_exc()

def def_check_core_tools():
    rows = []
    out = {}
    for name, path, required in [
        ("VeritasAegisNexus", AEGIS, True),
        ("VeritasCeleritas", CELERITAS, True),
        ("VIA_EnvManager", ENV_MANAGER, True),
    ]:
        mod, err = def_import_file(path, name)
        ok = mod is not None
        fn_count = 0
        cls_count = 0
        if ok:
            fn_count = len([x for x in dir(mod) if callable(getattr(mod, x, None)) and not x.startswith("__")])
            cls_count = len([x for x in dir(mod) if inspect.isclass(getattr(mod, x, None))])
            out[name] = mod
        rows.append({
            "Validation Status": def_status_lamp("PASS" if ok else "FAIL"),
            "Name": name,
            "Required": required,
            "Path": path,
            "Exists": Path(path).exists(),
            "Compile Import": ok,
            "Functions": fn_count,
            "Classes": cls_count,
            "Validation Note": "Ready and mandatory" if ok else err[:1200]
        })
    return rows, out

def def_default_20_libs():
    return [
        {"name":"twstock","module":"twstock","category":"TW_OFFICIAL","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"TWSE/TPEX list and price helper"},
        {"name":"FinMind","module":"FinMind.data","category":"TW_OFFICIAL","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Taiwan market API"},
        {"name":"pandas-datareader","module":"pandas_datareader","category":"TW_OFFICIAL","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Multi-source data reader"},
        {"name":"yahooquery","module":"yahooquery","category":"TW_OFFICIAL","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Yahoo Finance alternative"},
        {"name":"yahoofinancials","module":"yahoofinancials","category":"TW_OFFICIAL","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Yahoo financial scraper"},
        {"name":"akshare","module":"akshare","category":"TW_FINANCE","risk":"MEDIUM","target_env_hint":"via_basic_tools","purpose":"CN/HK/TW financial data"},
        {"name":"mplfinance","module":"mplfinance","category":"TW_FINANCE","risk":"LOW","target_env_hint":"via_plot_basic","purpose":"OHLCV charting"},
        {"name":"stockstats","module":"stockstats","category":"TW_FINANCE","risk":"LOW","target_env_hint":"via_ds_light","purpose":"Technical indicators"},
        {"name":"tls-client","module":"tls_client","category":"ANTI_SCRAPE","risk":"MEDIUM","target_env_hint":"via_basic_tools","purpose":"TLS fingerprinting"},
        {"name":"httpx","module":"httpx","category":"ANTI_SCRAPE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"HTTP client"},
        {"name":"h2","module":"h2","category":"ANTI_SCRAPE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"HTTP2 protocol"},
        {"name":"brotli","module":"brotli","category":"ANTI_SCRAPE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Brotli compression"},
        {"name":"parsel","module":"parsel","category":"PARSE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"CSS/XPath parsing"},
        {"name":"selectolax","module":"selectolax","category":"PARSE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Fast HTML parser"},
        {"name":"html5lib","module":"html5lib","category":"PARSE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Robust HTML parser"},
        {"name":"requests-cache","module":"requests_cache","category":"CACHE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"HTTP cache"},
        {"name":"diskcache","module":"diskcache","category":"CACHE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Disk cache"},
        {"name":"tenacity","module":"tenacity","category":"CACHE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Retry/backoff"},
        {"name":"ratelimit","module":"ratelimit","category":"CACHE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Function-level rate limit"},
        {"name":"platformdirs","module":"platformdirs","category":"CACHE","risk":"LOW","target_env_hint":"via_basic_tools","purpose":"Cross-platform cache dir"},
    ]

def def_load_20_libs():
    p = Path(V139G_LIBS_JSON)
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig"))
            if isinstance(obj, list) and len(obj) > 0:
                return obj, str(p), ""
            if isinstance(obj, dict):
                for key in ["libs", "advised_libs", "ADVISED_TW_COVERAGE_LIBS"]:
                    if key in obj and isinstance(obj[key], list):
                        return obj[key], str(p), ""
        except Exception:
            return def_default_20_libs(), "default", traceback.format_exc()
    return def_default_20_libs(), "default", "v139g_libs.json not found or empty"

def def_module_import_probe(module_name):
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception:
        return False, traceback.format_exc(limit=1)

def def_make_plan(libs):
    rows = []
    for lib in libs:
        name = lib.get("name") or lib.get("lib") or ""
        module = lib.get("module") or name.replace("-", "_")
        risk = str(lib.get("risk") or "LOW").upper()
        category = lib.get("category") or ""
        target = lib.get("target_env_hint") or "via_core_312"
        purpose = lib.get("purpose") or ""

        approve = False
        blocked = ""
        if risk == "LOW" and APPROVE_SAFE_INSTALL:
            approve = True
        elif risk == "MEDIUM" and APPROVE_MEDIUM_RISK_INSTALL:
            approve = True
        else:
            blocked = "not_approved_safe_gate" if risk == "LOW" else "medium_risk_requires_isolation_or_explicit_gate"

        rows.append({
            "Validation Status": def_status_lamp("PASS" if approve else "WARN"),
            "Name": name,
            "Module": module,
            "Category": category,
            "Risk": risk,
            "Target Env Hint": target,
            "Approved": approve,
            "Blocked Reason": blocked,
            "Purpose": purpose,
            "Validation Note": "Approved for install" if approve else "Plan only; no install"
        })
    return rows

def def_probe_imports(plan_rows):
    rows = []
    for r in plan_rows:
        ok, err = def_module_import_probe(r["Module"])
        rows.append({
            "Validation Status": def_status_lamp("PASS" if ok else "WARN"),
            "Name": r["Name"],
            "Module": r["Module"],
            "Risk": r["Risk"],
            "Import OK": ok,
            "Validation Note": "Already importable" if ok else err[:900]
        })
    return rows

def def_install_approved(plan_rows):
    rows = []
    for r in plan_rows:
        if not r["Approved"]:
            rows.append({
                "Validation Status": "🟡 WARN",
                "Name": r["Name"],
                "Module": r["Module"],
                "Approved": False,
                "Installed": False,
                "Exit Code": "",
                "Validation Note": r["Blocked Reason"] or "not approved"
            })
            continue

        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", r["Name"]]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            ok = proc.returncode == 0
            rows.append({
                "Validation Status": def_status_lamp("PASS" if ok else "FAIL"),
                "Name": r["Name"],
                "Module": r["Module"],
                "Approved": True,
                "Installed": ok,
                "Exit Code": proc.returncode,
                "Validation Note": (proc.stdout[-1000:] + proc.stderr[-1000:])[:1800]
            })
        except Exception:
            rows.append({
                "Validation Status": "🔴 FAIL",
                "Name": r["Name"],
                "Module": r["Module"],
                "Approved": True,
                "Installed": False,
                "Exit Code": "exception",
                "Validation Note": traceback.format_exc()[:1800]
            })
    return rows

def def_table_html(rows, title):
    if not rows:
        return f"<section class='card'><h2>{def_html_escape(title)}</h2><p>EMPTY</p></section>"
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    if "Validation Status" in keys:
        keys = ["Validation Status"] + [k for k in keys if k != "Validation Status"]
    if "Validation Note" in keys:
        keys = [k for k in keys if k != "Validation Note"] + ["Validation Note"]

    th = "".join(f"<th>{def_html_escape(k)}</th>" for k in keys)
    body = ""
    for r in rows:
        status = str(r.get("Validation Status", ""))
        row_class = "row-ok"
        if "🟡" in status:
            row_class = "row-warn"
        if "🔴" in status:
            row_class = "row-fail"
        body += f"<tr class='{row_class}'>"
        for k in keys:
            v = r.get(k, "")
            kind = "status" if k == "Validation Status" else ("long" if len(str(v)) > 34 or "\\" in str(v) or "/" in str(v) or k == "Validation Note" else "short")
            body += f"<td data-cell-kind='{kind}'>{def_html_escape(v)}</td>"
        body += "</tr>"
    return f"<section class='card'><h2>{def_html_escape(title)}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_write_html(meta, matrix, core_rows, plan_rows, probe_rows, install_rows):
    meta_json = def_html_escape(json.dumps(meta, ensure_ascii=False, indent=2))
    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN v141D5 Aegis Celeritas Runtime Bridge</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535;--blue:#4c78a8;--mono:Consolas,"Cascadia Mono",monospace;--sans:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif}}
*{{box-sizing:border-box}}
html{{font-size:10px}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:8.5px;line-height:1.1}}
.wrap{{max-width:1880px;margin:0 auto;padding:10px 14px 18px}}
header{{position:relative;background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:8px;box-shadow:0 4px 12px rgba(0,0,0,.06)}}
header:before{{content:"";position:absolute;left:16px;right:16px;top:0;height:3px;background:linear-gradient(90deg,#4c78a8,#439a9a,#7a6daa,#c4943a,#c96b5a)}}
h1{{margin:0;font-size:20px;line-height:1.05;font-weight:900;letter-spacing:-.04em}}
.sub{{font-family:var(--mono);font-size:8.8px;font-weight:900;letter-spacing:.08em;margin-top:3px}}
.desc{{font-size:9px;color:var(--muted);margin-top:3px}}
.tabs{{display:flex;gap:3px;flex-wrap:wrap;margin:8px 0}}
.tabs button{{padding:7px 13px;border:1px solid var(--border);border-radius:8px 8px 0 0;background:#edecea;color:var(--muted);font:800 10px var(--sans);cursor:pointer}}
.tabs button.on{{background:#fff;color:var(--blue);border-bottom:2px solid var(--blue)}}
.page{{display:none}}.page.on{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(80px,1fr));gap:6px;margin-bottom:8px}}
.kpi{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:6px 7px;min-height:42px}}
.kpi .v{{font-size:14px;font-weight:900;text-align:center;line-height:1.05}}
.kpi .k{{font-size:8px;color:var(--muted);text-align:center;margin-top:3px;text-transform:uppercase;font-weight:900}}
.card{{background:#fff;border:1px solid var(--border);border-radius:9px;padding:8px;margin-bottom:8px;box-shadow:0 1px 6px rgba(0,0,0,.035)}}
.card h2{{margin:0 0 6px;font-size:11px;font-weight:900}}
.scroll{{overflow:auto;max-height:76vh;border:1px solid var(--border);border-radius:7px;background:#fff}}
table{{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%;font-size:8.25px;line-height:1.08}}
th{{position:sticky;top:0;z-index:8;background:var(--head);font-weight:900;text-align:center;vertical-align:top;padding:3px 5px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere;min-width:100px;max-width:360px}}
td{{padding:3px 5px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:normal;overflow-wrap:anywhere;word-break:break-word;min-width:88px;max-width:360px}}
td[data-cell-kind="status"],td:first-child,th:first-child{{text-align:center!important;min-width:82px;max-width:92px;font-weight:900}}
td[data-cell-kind="long"]{{text-align:left!important;min-width:180px;max-width:560px}}
.row-ok td:first-child{{color:var(--ok)}}.row-warn td:first-child{{color:var(--warn)}}.row-fail td:first-child{{color:var(--err)}}
pre{{font-family:var(--mono);font-size:8.25px;line-height:1.16;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;max-height:42vh;overflow:auto}}
.footer{{margin-top:10px;color:var(--muted);font-size:8.4px;text-align:left;border-top:1px solid var(--border);padding-top:8px}}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>VeritasReportNova {VERSION}</h1>
<div class="sub">VERITAS INTELLIGENCE ANALYTICS</div>
<div class="desc">Mandatory Aegis + Celeritas · 20-Lib Safe Approval Plan · No DB/SSOT Write</div>
</header>

<nav class="tabs">
<button class="on" onclick="swTab(this,'tab1')">Summary Matrix</button>
<button onclick="swTab(this,'tab2')">Core Tools</button>
<button onclick="swTab(this,'tab3')">20-Lib Approval Plan</button>
<button onclick="swTab(this,'tab4')">Import Probe</button>
<button onclick="swTab(this,'tab5')">Install Result</button>
</nav>

<section class="page on" id="tab1">
<div class="grid">
<div class="kpi"><div class="v">{meta.get('system_pass')}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v">{meta.get('core_ready')}</div><div class="k">Core Ready</div></div>
<div class="kpi"><div class="v">{meta.get('libs_total')}</div><div class="k">Libs</div></div>
<div class="kpi"><div class="v">{meta.get('approved')}</div><div class="k">Approved</div></div>
<div class="kpi"><div class="v">{meta.get('import_ok')}</div><div class="k">Import OK</div></div>
<div class="kpi"><div class="v">{meta.get('installed')}</div><div class="k">Installed</div></div>
<div class="kpi"><div class="v">{meta.get('db_write')}</div><div class="k">DB Write</div></div>
<div class="kpi"><div class="v">{meta.get('elapsed_sec')}</div><div class="k">Elapsed</div></div>
</div>
<section class="card"><h2>Meta</h2><pre>{meta_json}</pre></section>
{def_table_html(matrix, "Summary Matrix")}
</section>

<section class="page" id="tab2">{def_table_html(core_rows, "Mandatory Core Tools")}</section>
<section class="page" id="tab3">{def_table_html(plan_rows, "20-Lib Safe Approval Plan")}</section>
<section class="page" id="tab4">{def_table_html(probe_rows, "Import Probe")}</section>
<section class="page" id="tab5">{def_table_html(install_rows, "Install Result")}</section>

<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</div>
<script>
function swTab(btn,id){{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById(id).classList.add('on');
}}
</script>
</body>
</html>"""
    Path(OUT_HTML).write_text(html_doc, encoding="utf-8-sig")

def def_main():
    t0 = datetime.now()
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)

    matrix = []
    def_add_matrix(matrix, "Safety", "DB Write", DB_WRITE_ENABLE, False, DB_WRITE_ENABLE is False, "OK", "No DB write")
    def_add_matrix(matrix, "Safety", "SSOT Mutation", SSOT_MUTATION_ENABLE, False, SSOT_MUTATION_ENABLE is False, "OK", "No SSOT mutation")
    def_add_matrix(matrix, "Safety", "Source Patch", SOURCE_PATCH_ENABLE, False, SOURCE_PATCH_ENABLE is False, "OK", "No source patch")
    def_add_matrix(matrix, "Safety", "Network Data Fetch", NETWORK_DATA_FETCH_ENABLE, False, NETWORK_DATA_FETCH_ENABLE is False, "OK", "No data fetch")
    def_add_matrix(matrix, "Core", "Aegis Mandatory", AEGIS, "importable", Path(AEGIS).exists(), "OK" if Path(AEGIS).exists() else "ERR", "Required")
    def_add_matrix(matrix, "Core", "Celeritas Mandatory", CELERITAS, "importable", Path(CELERITAS).exists(), "OK" if Path(CELERITAS).exists() else "ERR", "Required")

    core_rows, core_modules = def_check_core_tools()
    core_ready = sum(1 for r in core_rows if "🟢" in r["Validation Status"])

    libs, lib_source, lib_err = def_load_20_libs()
    plan_rows = def_make_plan(libs)
    probe_rows = def_probe_imports(plan_rows)
    install_rows = def_install_approved(plan_rows)

    approved = sum(1 for r in plan_rows if r["Approved"])
    import_ok = sum(1 for r in probe_rows if r["Import OK"])
    installed = sum(1 for r in install_rows if r["Installed"])

    def_add_matrix(matrix, "Core", "Core Tool Import Ready", f"{core_ready}/{len(core_rows)}", "3/3", core_ready == len(core_rows), "OK" if core_ready == len(core_rows) else "ERR", "Aegis + Celeritas + EnvManager mandatory")
    def_add_matrix(matrix, "Advisor", "20 Lib Source", lib_source, "v139g_libs.json or default", True, "OK", lib_err or "Loaded")
    def_add_matrix(matrix, "Advisor", "20 Lib Count", len(plan_rows), "20", len(plan_rows) == 20, "OK" if len(plan_rows) == 20 else "WARN", "Coverage expansion library list")
    def_add_matrix(matrix, "Install Gate", "Approved", approved, "depends on gate", True, "OK", "Default is plan/probe only")
    def_add_matrix(matrix, "Import Probe", "Import OK", import_ok, ">=0", True, "OK", "Probe existing env only")
    def_add_matrix(matrix, "Install Result", "Installed", installed, "0 unless approved", True, "OK", "No unapproved install")

    def_write_csv(OUT_CORE_CSV, core_rows)
    def_write_csv(OUT_LIB_PLAN_CSV, plan_rows)
    def_write_csv(OUT_IMPORT_PROBE_CSV, probe_rows)
    def_write_csv(OUT_INSTALL_CSV, install_rows)
    def_write_csv(OUT_MATRIX_CSV, matrix)

    fail_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "ERR")
    warn_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "WARN")
    system_pass = fail_count == 0
    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": "VRN_V141D5_AEGIS_CELERITAS_RUNTIME_BRIDGE",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "python": sys.executable,
        "aegis": AEGIS,
        "celeritas": CELERITAS,
        "env_manager": ENV_MANAGER,
        "core_ready": f"{core_ready}/{len(core_rows)}",
        "libs_total": len(plan_rows),
        "approved": approved,
        "import_ok": import_ok,
        "installed": installed,
        "approve_safe_install": APPROVE_SAFE_INSTALL,
        "approve_medium_risk_install": APPROVE_MEDIUM_RISK_INSTALL,
        "lib_source": lib_source,
        "db_write": DB_WRITE_ENABLE,
        "ssot_mutation": SSOT_MUTATION_ENABLE,
        "source_patch": SOURCE_PATCH_ENABLE,
        "network_data_fetch": NETWORK_DATA_FETCH_ENABLE,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "matrix_csv": OUT_MATRIX_CSV,
        "core_csv": OUT_CORE_CSV,
        "lib_plan_csv": OUT_LIB_PLAN_CSV,
        "import_probe_csv": OUT_IMPORT_PROBE_CSV,
        "install_csv": OUT_INSTALL_CSV,
        "registry": OUT_REGISTRY,
        "elapsed_sec": elapsed
    }

    def_write_json(OUT_JSON, {
        "meta": meta,
        "matrix": matrix,
        "core_tools": core_rows,
        "lib_plan": plan_rows,
        "import_probe": probe_rows,
        "install_result": install_rows
    })

    registry = ["VRN_V141D5_AEGIS_CELERITAS_RUNTIME_BRIDGE_REGISTRY"]
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    registry += [
        "aegis_mandatory=YES",
        "celeritas_mandatory=YES",
        "env_manager_mandatory=YES",
        "v139g_result_interpreted=APPROVAL_GATE_BLOCKED_INSTALL_NOT_CORE_FAILURE",
        "default_install_mode=PLAN_AND_PROBE_ONLY",
        "low_risk_install_requires_APPROVE_SAFE_INSTALL_TRUE",
        "medium_risk_install_requires_APPROVE_MEDIUM_RISK_INSTALL_TRUE_OR_ISOLATION",
        "db_write=NO",
        "ssot_mutation=NO",
        "source_patch=NO",
        "network_data_fetch=NO",
        "next=v141D6_safe_adapter_call_official_functional_modules"
    ]
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_write_html(meta, matrix, core_rows, plan_rows, probe_rows, install_rows)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {
            "version": "VRN_V141D5_AEGIS_CELERITAS_RUNTIME_BRIDGE",
            "system_pass": False,
            "fatal": traceback.format_exc(),
            "run_dir": RUN_DIR
        }
        def_write_json(OUT_JSON, fatal)
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
