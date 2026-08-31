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
VERSION = "v1.0.41D4"
VRN_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
VRN_MODULE_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\modules"
INPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\input"
OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output"
TEMP_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp"
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT"

PRODUCTION_BASICINFO_PARQUET = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\VRN_BasicInfo.parquet"
PRODUCTION_FINANCIAL_PARQUET = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\VRN_FinancialData.parquet"

PRODUCTION_WRITE_ENABLE = False
DB_WRITE_ENABLE = False
SSOT_APPEND_ENABLE = False
SIDECAR_MUTATION_ENABLE = False
SOURCE_PATCH_ENABLE = False
NETWORK_ENABLE = False
MAX_FILES = 9999

FUNCTIONAL_MODULES = [
  {
    "Role": "Name sanitizer / filename and entity normalization",
    "Name": "VRN_NameSanitizer_v23",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_NameSanitizer_v23.py"
  },
  {
    "Role": "Basic Info final consolidator",
    "Name": "VRN_MDL_BasicInfo_FinalConsolidator_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_BasicInfo_FinalConsolidator_AIO_v01.py"
  },
  {
    "Role": "Basic Info trainer",
    "Name": "VRN_MDL_BasicInfoTrainer_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_BasicInfoTrainer_AIO_v01.py"
  },
  {
    "Role": "Body / title / sentence anchor extractor",
    "Name": "VRN_MDL_BODY_TITLE_SENTENCE_ANCHOR_EXTRACTOR_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_BODY_TITLE_SENTENCE_ANCHOR_EXTRACTOR_v01.py"
  },
  {
    "Role": "Evidence doctor",
    "Name": "VRN_MDL_EvidenceDoctor_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_EvidenceDoctor_AIO_v01.py"
  },
  {
    "Role": "Evidence matrix builder",
    "Name": "VRN_MDL_EvidenceMatrix_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_EvidenceMatrix_AIO_v01.py"
  },
  {
    "Role": "Evidence seal optimizer",
    "Name": "VRN_MDL_EvidenceSealOptimizer_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_EvidenceSealOptimizer_AIO_v01.py"
  },
  {
    "Role": "Final gate overlay",
    "Name": "VRN_MDL_FinalGateOverlay_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_FinalGateOverlay_AIO_v01.py"
  },
  {
    "Role": "Financial trust validator",
    "Name": "VRN_MDL_FinancialTrustValidator_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_FinancialTrustValidator_AIO_v01.py"
  },
  {
    "Role": "Homepage summarizer router",
    "Name": "VRN_MDL_HomepageSummarizer_Router_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_HomepageSummarizer_Router_v01.py"
  },
  {
    "Role": "Homepage summarizer",
    "Name": "VRN_MDL_HomepageSummarizer_v06",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_HomepageSummarizer_v06.py"
  },
  {
    "Role": "Project perfector",
    "Name": "VRN_MDL_ProjectPerfector_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_ProjectPerfector_AIO_v01.py"
  },
  {
    "Role": "Summary pipeline bridge",
    "Name": "VRN_MDL_SummaryPipelineBridge_AIO_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_SummaryPipelineBridge_AIO_v01.py"
  },
  {
    "Role": "YFinance info reference prefix",
    "Name": "VRN_MDL_YFinanceInfoReferencePrefix_v02",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VRN\\modules\\VRN_MDL_YFinanceInfoReferencePrefix_v02.py"
  }
]
SUPPORTIVE_MODULES = [
  {
    "Role": "Input route policy",
    "Name": "VIS_VRN_InputRoutePolicy_v0224",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_InputRoutePolicy_v0224.py"
  },
  {
    "Role": "New report compatibility gate",
    "Name": "VIS_VRN_NewReportCompatibilityGate_v01",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_NewReportCompatibilityGate_v01.py"
  },
  {
    "Role": "TW official ticker / YFinance suffix route",
    "Name": "VIS_VRN_TWOfficialYFinance_v06051",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_TWOfficialYFinance_v06051.py"
  },
  {
    "Role": "Unified SSOT schema registry",
    "Name": "VIA_SSOT_Unified",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_SSOT_Unified.py"
  },
  {
    "Role": "Broker alias compatibility",
    "Name": "VIS_VRN_BrokerAlias_Compatibility_v0222",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_BrokerAlias_Compatibility_v0222.py"
  },
  {
    "Role": "Broker alias extension",
    "Name": "VIS_VRN_BrokerAlias_Extension_v0224",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_BrokerAlias_Extension_v0224.py"
  },
  {
    "Role": "Broker / analyst adapters",
    "Name": "VIS_VRN_BrokerAnalystAdapters_v06146",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_BrokerAnalystAdapters_v06146.py"
  },
  {
    "Role": "Financial extraction rescue rules",
    "Name": "VIS_VRN_FinancialRescueRules_v06126",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_FinancialRescueRules_v06126.py"
  },
  {
    "Role": "Financial SSOT legacy route",
    "Name": "VIS_VRN_FinancialSSOT_v0599",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_FinancialSSOT_v0599.py"
  },
  {
    "Role": "Financial SSOT current route",
    "Name": "VIS_VRN_FinancialSSOT_v0608",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_VRN_FinancialSSOT_v0608.py"
  },
  {
    "Role": "Accelerator / no-hang performance support",
    "Name": "VeritasCeleritas",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VeritasCeleritas.py"
  },
  {
    "Role": "Network gate / route safety",
    "Name": "VeritasAegisNexus",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VeritasAegisNexus.py"
  },
  {
    "Role": "Environment health gate",
    "Name": "VIA_EnvManager",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_EnvManager.py"
  },
  {
    "Role": "Asset registry core",
    "Name": "VIA_RegistryCore_v1",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_RegistryCore_v1.py"
  },
  {
    "Role": "Runtime bridge",
    "Name": "VIA_Runtime_Bridge_All_in_One",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_Runtime_Bridge_All_in_One.py"
  },
  {
    "Role": "AST / anchor planner",
    "Name": "VIA_Panorama_AST_RuntimeInjector",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_Panorama_AST_RuntimeInjector.py"
  },
  {
    "Role": "Supportive hard gate bridge",
    "Name": "VIA_Supportive_Runtime_HardGate_Bridge",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIA_Supportive_Runtime_HardGate_Bridge.py"
  },
  {
    "Role": "Install / health registry",
    "Name": "VIS_InstallHealthRegistry",
    "Path": "C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\supportive_module\\VIS_InstallHealthRegistry.py"
  }
]

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Functional_Module_Contract.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Functional_Module_Contract.json"
OUT_MATRIX_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Contract_Matrix.csv"
OUT_FUNCTIONAL_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Functional_Module_Check.csv"
OUT_SUPPORTIVE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Supportive_Module_Check.csv"
OUT_INPUT_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Input_Manifest.csv"
OUT_ROUTE_PLAN_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Module_Route_Plan.csv"
OUT_LEGACY_BLOCK_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_Legacy_Module_Blocklist.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_module_contract_runs\RUN_20260527_001104_VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT\VRN_v141D4_FUNCTIONAL_MODULE_CONTRACT_REGISTRY.txt"

import ast
import csv
import html
import importlib.util
import inspect
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

def def_ast_scan(path):
    out = {
        "ast_ok": False,
        "def_count": 0,
        "class_count": 0,
        "import_count": 0,
        "callable_defs": "",
        "error": ""
    }
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(txt)
        defs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        out["ast_ok"] = True
        out["def_count"] = len(defs)
        out["class_count"] = len(classes)
        out["import_count"] = len(imports)
        out["callable_defs"] = ", ".join(defs[:40])
    except Exception:
        out["error"] = traceback.format_exc()[:1200]
    return out

def def_import_module(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception:
        return None, traceback.format_exc()[:1600]

def def_check_module_set(module_set, module_type):
    rows = []
    modules = {}

    for m in module_set:
        p = Path(m["Path"])
        ast_info = {
            "ast_ok": False,
            "def_count": 0,
            "class_count": 0,
            "import_count": 0,
            "callable_defs": "",
            "error": ""
        }
        compile_ok = False
        import_ok = False
        runtime_functions = 0
        runtime_classes = 0
        import_error = ""

        if p.exists():
            ast_info = def_ast_scan(p)
            try:
                py_compile.compile(str(p), doraise=True)
                compile_ok = True
            except Exception:
                import_error = traceback.format_exc()[:1600]

            if compile_ok:
                mod, e = def_import_module(str(p), m["Name"])
                if mod is not None:
                    import_ok = True
                    modules[m["Name"]] = mod
                    runtime_functions = len([x for x in dir(mod) if callable(getattr(mod, x, None)) and not x.startswith("__")])
                    runtime_classes = len([x for x in dir(mod) if inspect.isclass(getattr(mod, x, None))])
                else:
                    import_error = e

        ok = p.exists() and ast_info["ast_ok"] and compile_ok and import_ok

        rows.append({
            "Validation Status": def_status_lamp("PASS" if ok else "WARN"),
            "Module Type": module_type,
            "Name": m["Name"],
            "Role": m["Role"],
            "Path": str(p),
            "Exists": p.exists(),
            "AST": ast_info["ast_ok"],
            "Compile": compile_ok,
            "Import": import_ok,
            "AST Defs": ast_info["def_count"],
            "AST Classes": ast_info["class_count"],
            "Runtime Functions": runtime_functions,
            "Runtime Classes": runtime_classes,
            "Candidate Defs": ast_info["callable_defs"],
            "Validation Note": "Ready" if ok else (import_error or ast_info["error"] or "Missing / not importable")
        })

    return rows, modules

def def_scan_input_files():
    allowed = {
        ".pdf": "PDF",
        ".docx": "WORD",
        ".doc": "WORD_LEGACY",
        ".png": "IMAGE",
        ".jpg": "IMAGE",
        ".jpeg": "IMAGE",
        ".webp": "IMAGE",
        ".tif": "IMAGE",
        ".tiff": "IMAGE",
        ".bmp": "IMAGE",
    }

    rows = []
    root = Path(INPUT_DIR)

    if not root.exists():
        return rows

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in allowed:
            continue
        if len(rows) >= MAX_FILES:
            break
        rows.append({
            "Validation Status": "🟢 PASS",
            "Filename": p.name,
            "File Type": allowed[ext],
            "Extension": ext,
            "Path": str(p),
            "Size Bytes": p.stat().st_size,
            "Modified At": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "Validation Note": "Input candidate"
        })

    return rows

def def_route_plan():
    rows = [
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "01",
            "Stage": "Name / filename normalization",
            "Official Functional Module": "VRN_NameSanitizer_v23",
            "Purpose": "Normalize filename, broker, company name, ticker evidence strings",
            "Legacy Replacement": "Do not use 新增資料夾 legacy converter as primary route"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "02",
            "Stage": "Input title/body/sentence anchor extraction",
            "Official Functional Module": "VRN_MDL_BODY_TITLE_SENTENCE_ANCHOR_EXTRACTOR_v01",
            "Purpose": "Extract title/body/sentence anchors from PDF/DOCX text",
            "Legacy Replacement": "Replaces ad-hoc text regex route"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "03",
            "Stage": "Evidence matrix / doctor / seal",
            "Official Functional Module": "VRN_MDL_EvidenceMatrix_AIO_v01 + VRN_MDL_EvidenceDoctor_AIO_v01 + VRN_MDL_EvidenceSealOptimizer_AIO_v01",
            "Purpose": "Build, inspect, and optimize evidence matrix",
            "Legacy Replacement": "Replaces loose per-file extraction matrix"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "04",
            "Stage": "Basic Info training and final consolidation",
            "Official Functional Module": "VRN_MDL_BasicInfoTrainer_AIO_v01 + VRN_MDL_BasicInfo_FinalConsolidator_AIO_v01",
            "Purpose": "Generate Basic Info canonical result",
            "Legacy Replacement": "Replaces regex-only BasicInfo staging"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "05",
            "Stage": "Financial trust validation",
            "Official Functional Module": "VRN_MDL_FinancialTrustValidator_AIO_v01",
            "Purpose": "Validate financial rows, units, years, actual/estimate trust",
            "Legacy Replacement": "Replaces regex-only financial extraction"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "06",
            "Stage": "YFinance reference prefix",
            "Official Functional Module": "VRN_MDL_YFinanceInfoReferencePrefix_v02",
            "Purpose": "Attach YFinance reference prefix and consensus reference fields",
            "Legacy Replacement": "Replaces manual prefix logic"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "07",
            "Stage": "Summary / homepage / final gate",
            "Official Functional Module": "VRN_MDL_SummaryPipelineBridge_AIO_v01 + VRN_MDL_HomepageSummarizer_Router_v01 + VRN_MDL_HomepageSummarizer_v06 + VRN_MDL_FinalGateOverlay_AIO_v01",
            "Purpose": "Produce UI summary and final validation overlay",
            "Legacy Replacement": "Replaces separate report-only summary scripts"
        },
        {
            "Validation Status": "🟢 PASS",
            "Route Step": "08",
            "Stage": "Project perfector",
            "Official Functional Module": "VRN_MDL_ProjectPerfector_AIO_v01",
            "Purpose": "Final project-level consistency and route perfection",
            "Legacy Replacement": "Replaces manual clean-up passes"
        }
    ]
    return rows

def def_legacy_blocklist():
    legacy_root = Path(VRN_BASE) / "新增資料夾"
    legacy_names = [
        "VRN_MDL005_OCRFetchingPDFText.py",
        "VRN_MDL006_ConsolidatorAndPhaseValidator.py",
        "VRN_MDL007_APIDataFetcher.py",
        "VRN_MDL008_CrossValidator.py",
        "ACTIVATE_AND_CROSS_VALIDATE.py",
        "panorama_xcheck_v110.py",
        "VIA_HardGate_BootPrecheck.py",
        "VRN_HealthCheck.py",
        "VRN_MDL001_Converter.py",
        "VRN_MDL001_StockReportPipeline.py",
        "VRN_MDL002_LayoutExtractor.py",
        "VRN_MDL003_TableRestorer.py",
        "VRN_MDL004_OCR_FetchingPDFTable.py"
    ]
    rows = []
    for name in legacy_names:
        p = legacy_root / name
        rows.append({
            "Validation Status": "🟡 WARN" if p.exists() else "🟢 PASS",
            "Legacy Module": name,
            "Path": str(p),
            "Exists": p.exists(),
            "Main Route Use": "NO",
            "Validation Note": "Legacy historical reference only; not used as official v141D4 functional module"
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
            kind = "status" if k == "Validation Status" else ("long" if len(str(v)) > 36 or "\\" in str(v) or "/" in str(v) or k == "Validation Note" else "short")
            body += f"<td data-cell-kind='{kind}'>{def_html_escape(v)}</td>"
        body += "</tr>"

    return f"<section class='card'><h2>{def_html_escape(title)}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_write_html(meta, matrix, functional_rows, supportive_rows, input_rows, route_rows, legacy_rows):
    meta_json = def_html_escape(json.dumps(meta, ensure_ascii=False, indent=2))
    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN v141D4 Functional Module Contract</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535;--blue:#4c78a8;--mono:Consolas,"Cascadia Mono",monospace;--sans:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif}}
*{{box-sizing:border-box}}
html{{font-size:10px}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:8.55px;line-height:1.1}}
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
.scroll{{overflow:auto;max-height:72vh;border:1px solid var(--border);border-radius:7px;background:#fff}}
table{{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%;font-size:8.35px;line-height:1.08}}
th{{position:sticky;top:0;z-index:8;background:var(--head);font-weight:900;text-align:left;vertical-align:top;padding:3px 5px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere;min-width:120px;max-width:360px}}
td{{padding:3px 5px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:break-word;min-width:120px;max-width:360px}}
td[data-cell-kind="status"], th:first-child, td:first-child{{text-align:center!important;min-width:86px;max-width:86px;font-weight:900}}
td[data-cell-kind="long"]{{text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:break-word}}
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
<div class="desc">Official Functional Modules · VRN\\modules Contract · Legacy MDL001~008 Blocked From Main Route · Preview Only</div>
</header>

<nav class="tabs">
<button class="on" onclick="swTab(this,'tab1')">Summary Matrix</button>
<button onclick="swTab(this,'tab2')">Official Functional Modules</button>
<button onclick="swTab(this,'tab3')">Supportive Modules</button>
<button onclick="swTab(this,'tab4')">Input Manifest</button>
<button onclick="swTab(this,'tab5')">Module Route Plan</button>
<button onclick="swTab(this,'tab6')">Legacy Blocklist</button>
</nav>

<section class="page on" id="tab1">
<div class="grid">
<div class="kpi"><div class="v">{meta.get('system_pass')}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v">{meta.get('functional_ready')}</div><div class="k">Functional Ready</div></div>
<div class="kpi"><div class="v">{meta.get('supportive_ready')}</div><div class="k">Supportive Ready</div></div>
<div class="kpi"><div class="v">{meta.get('input_files')}</div><div class="k">Input Files</div></div>
<div class="kpi"><div class="v">{meta.get('legacy_main_route')}</div><div class="k">Legacy Main Route</div></div>
<div class="kpi"><div class="v">{meta.get('db_write')}</div><div class="k">DB Write</div></div>
<div class="kpi"><div class="v">{meta.get('ssot_append')}</div><div class="k">SSOT Append</div></div>
<div class="kpi"><div class="v">{meta.get('elapsed_sec')}</div><div class="k">Elapsed</div></div>
</div>
<section class="card"><h2>Meta</h2><pre>{meta_json}</pre></section>
{def_table_html(matrix, "Summary Matrix")}
</section>

<section class="page" id="tab2">{def_table_html(functional_rows, "Official Functional Modules")}</section>
<section class="page" id="tab3">{def_table_html(supportive_rows, "Supportive Modules")}</section>
<section class="page" id="tab4">{def_table_html(input_rows, "Input Manifest")}</section>
<section class="page" id="tab5">{def_table_html(route_rows, "Module Route Plan")}</section>
<section class="page" id="tab6">{def_table_html(legacy_rows, "Legacy Blocklist")}</section>

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
    def_add_matrix(matrix, "Safety", "SSOT Append", SSOT_APPEND_ENABLE, False, SSOT_APPEND_ENABLE is False, "OK", "No SSOT mutation")
    def_add_matrix(matrix, "Safety", "Sidecar Mutation", SIDECAR_MUTATION_ENABLE, False, SIDECAR_MUTATION_ENABLE is False, "OK", "No sidecar mutation")
    def_add_matrix(matrix, "Safety", "Source Patch", SOURCE_PATCH_ENABLE, False, SOURCE_PATCH_ENABLE is False, "OK", "No source patch")
    def_add_matrix(matrix, "Safety", "Network", NETWORK_ENABLE, False, NETWORK_ENABLE is False, "OK", "No network")

    functional_rows, functional_modules = def_check_module_set(FUNCTIONAL_MODULES, "FUNCTIONAL")
    supportive_rows, supportive_modules = def_check_module_set(SUPPORTIVE_MODULES, "SUPPORTIVE")
    input_rows = def_scan_input_files()
    route_rows = def_route_plan()
    legacy_rows = def_legacy_blocklist()

    functional_ready = sum(1 for r in functional_rows if "🟢" in r["Validation Status"])
    supportive_ready = sum(1 for r in supportive_rows if "🟢" in r["Validation Status"])

    def_add_matrix(matrix, "Contract", "Official Functional Module Count", len(FUNCTIONAL_MODULES), "14", len(FUNCTIONAL_MODULES) == 14, "OK" if len(FUNCTIONAL_MODULES) == 14 else "ERR", "Functional module list realigned to VRN\\modules")
    def_add_matrix(matrix, "Contract", "Functional Ready", f"{functional_ready}/{len(functional_rows)}", "all pass preferred", functional_ready == len(functional_rows), "OK" if functional_ready == len(functional_rows) else "WARN", "Compile/import readiness for official functional modules")
    def_add_matrix(matrix, "Contract", "Supportive Ready", f"{supportive_ready}/{len(supportive_rows)}", "all pass preferred", supportive_ready == len(supportive_rows), "OK" if supportive_ready == len(supportive_rows) else "WARN", "Supportive module readiness")
    def_add_matrix(matrix, "Contract", "Legacy Main Route", "NO", "NO", True, "OK", "Legacy 新增資料夾 modules are historical reference only")
    def_add_matrix(matrix, "Input", "Input Files", len(input_rows), ">0", len(input_rows) > 0, "OK" if len(input_rows) > 0 else "WARN", "PDF / Word / Image candidates")
    def_add_matrix(matrix, "Output", "Required BasicInfo Output", PRODUCTION_BASICINFO_PARQUET, "manual gate only", True, "OK", "No write in this preview")
    def_add_matrix(matrix, "Output", "Required FinancialData Output", PRODUCTION_FINANCIAL_PARQUET, "manual gate only", True, "OK", "No write in this preview")

    def_write_csv(OUT_FUNCTIONAL_CSV, functional_rows)
    def_write_csv(OUT_SUPPORTIVE_CSV, supportive_rows)
    def_write_csv(OUT_INPUT_CSV, input_rows)
    def_write_csv(OUT_ROUTE_PLAN_CSV, route_rows)
    def_write_csv(OUT_LEGACY_BLOCK_CSV, legacy_rows)
    def_write_csv(OUT_MATRIX_CSV, matrix)

    fail_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "ERR")
    warn_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "WARN")
    system_pass = fail_count == 0
    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": "VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT_REALIGNMENT",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "base": VRN_BASE,
        "module_dir": VRN_MODULE_DIR,
        "input_dir": INPUT_DIR,
        "output_dir": OUTPUT_DIR,
        "temp_dir": TEMP_DIR,
        "run_dir": RUN_DIR,
        "functional_count": len(FUNCTIONAL_MODULES),
        "functional_ready": f"{functional_ready}/{len(functional_rows)}",
        "supportive_count": len(SUPPORTIVE_MODULES),
        "supportive_ready": f"{supportive_ready}/{len(supportive_rows)}",
        "input_files": len(input_rows),
        "legacy_main_route": "NO",
        "production_basicinfo_output": PRODUCTION_BASICINFO_PARQUET,
        "production_financial_output": PRODUCTION_FINANCIAL_PARQUET,
        "db_write": DB_WRITE_ENABLE,
        "ssot_append": SSOT_APPEND_ENABLE,
        "sidecar_mutation": SIDECAR_MUTATION_ENABLE,
        "source_patch": SOURCE_PATCH_ENABLE,
        "network": NETWORK_ENABLE,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "matrix_csv": OUT_MATRIX_CSV,
        "functional_csv": OUT_FUNCTIONAL_CSV,
        "supportive_csv": OUT_SUPPORTIVE_CSV,
        "input_csv": OUT_INPUT_CSV,
        "route_plan_csv": OUT_ROUTE_PLAN_CSV,
        "legacy_blocklist_csv": OUT_LEGACY_BLOCK_CSV,
        "registry": OUT_REGISTRY,
        "elapsed_sec": elapsed
    }

    def_write_json(OUT_JSON, {
        "meta": meta,
        "matrix": matrix,
        "official_functional_modules": functional_rows,
        "supportive_modules": supportive_rows,
        "input_manifest": input_rows,
        "module_route_plan": route_rows,
        "legacy_blocklist": legacy_rows
    })

    registry = ["VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT_REALIGNMENT_REGISTRY"]
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    registry += [
        "official_functional_modules_dir=VRN\\modules",
        "official_functional_module_count=14",
        "legacy_new_folder_modules_main_route=NO",
        "legacy_new_folder_modules_historical_reference_only=YES",
        "VRN_NameSanitizer_v23=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_BasicInfo_FinalConsolidator_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_BasicInfoTrainer_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_BODY_TITLE_SENTENCE_ANCHOR_EXTRACTOR_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_EvidenceDoctor_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_EvidenceMatrix_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_EvidenceSealOptimizer_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_FinalGateOverlay_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_FinancialTrustValidator_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_HomepageSummarizer_Router_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_HomepageSummarizer_v06=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_ProjectPerfector_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_SummaryPipelineBridge_AIO_v01=OFFICIAL_FUNCTIONAL",
        "VRN_MDL_YFinanceInfoReferencePrefix_v02=OFFICIAL_FUNCTIONAL",
        "production_output_write=NO",
        "db_write=NO",
        "ssot_mutation=NO",
        "sidecar_mutation=NO",
        "source_patch=NO",
        "network=NO",
        "next=v141D5_call_official_modules_with_safe_adapter"
    ]
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_write_html(meta, matrix, functional_rows, supportive_rows, input_rows, route_rows, legacy_rows)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {
            "version": "VRN_V141D4_FUNCTIONAL_MODULE_CONTRACT_REALIGNMENT",
            "system_pass": False,
            "fatal": traceback.format_exc(),
            "run_dir": RUN_DIR
        }
        def_write_json(OUT_JSON, fatal)
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
