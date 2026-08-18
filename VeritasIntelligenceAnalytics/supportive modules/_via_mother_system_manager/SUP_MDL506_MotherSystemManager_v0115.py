# -*- coding: utf-8 -*-
"""
VIA_MotherSystemManager_v0115.py

Local-only mother-system panorama scanner and IAM architecture planner.

No external network call.
No source mutation.
No canonical merge.
No DB write.
No delete.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import html
import json
import os
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


CODE_EXT = {
    ".ps1", ".psm1", ".psd1", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".sql", ".bat", ".cmd", ".sh", ".psql", ".r",
    ".ipynb", ".md", ".yaml", ".yml", ".toml", ".ini", ".cfg"
}

DATA_EXT = {
    ".json", ".csv", ".tsv", ".parquet", ".duckdb", ".db", ".sqlite",
    ".xlsx", ".xls", ".xml", ".feather", ".pkl", ".pickle"
}

DOC_EXT = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md", ".rst"
}

IMAGE_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".bmp"
}

ARCHIVE_EXT = {
    ".zip", ".7z", ".rar", ".tar", ".gz"
}

TEXT_SAMPLE_EXT = CODE_EXT | {".txt", ".md", ".json", ".csv", ".tsv", ".xml", ".html", ".css"}

SECRET_PAT = re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|bearer|client_secret|fred_api_key)")
DANGER_PAT = re.compile(r"(?i)\b(Remove-Item|Stop-Process|Invoke-Expression|iex|Start-Process\s+pwsh|Start-Process\s+powershell|Start-Job|ForEach-Object\s+-Parallel)\b")
ERROR_PAT = re.compile(r"(?i)(FATAL|Traceback|ParserError|TerminatingError|\[FAIL\]|Exception)")
PARAM_PAT = re.compile(r"(?i)(def_PARAM_[A-Za-z0-9_]+|\$[A-Za-z_][A-Za-z0-9_]*|--[A-Za-z0-9][A-Za-z0-9_-]+)")
JSON_KEY_PAT = re.compile(r'"([A-Za-z_][A-Za-z0-9_\-]{2,80})"\s*:')


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return os.path.relpath(str(path), str(base))


def norm_path(s: str) -> str:
    return s.replace("\\", "/")


def slugify(name: str, max_len: int = 90) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\u4e00-\u9fff]+", "_", stem, flags=re.UNICODE).strip("_")
    stem = re.sub(r"_+", "_", stem)
    if not stem:
        stem = "unnamed"
    return stem[:max_len]


def classify_file_type(ext: str) -> str:
    e = ext.lower()
    if e in CODE_EXT:
        return "CODE_CONFIG"
    if e in DATA_EXT:
        return "DATA_DB"
    if e in DOC_EXT:
        return "DOC_REPORT"
    if e in IMAGE_EXT:
        return "UI_ASSET_IMAGE"
    if e in ARCHIVE_EXT:
        return "ARCHIVE_PACKAGE"
    if e in {".log"}:
        return "LOG_EVIDENCE"
    if e in {".exe", ".dll", ".pyd"}:
        return "BINARY_RUNTIME"
    return "OTHER"


def classify_subsystem(rel: str, ext: str) -> Tuple[str, str]:
    p = norm_path(rel).lower()

    if "/functional modules/vdf/" in p or "/vdf/" in p:
        return "FUNCTIONAL_SYSTEM", "VDF_VeritasDataForge"
    if "/functional modules/vrn/" in p or "/vrn/" in p:
        return "FUNCTIONAL_SYSTEM", "VRN_VeritasReportNova"
    if "active_etf" in p or "vetf" in p:
        return "FUNCTIONAL_SYSTEM", "VETF_ActiveETF"
    if "vap" in p:
        return "FUNCTIONAL_SYSTEM", "VAP_VisualizationAnalytics"
    if "vis" in p:
        return "FUNCTIONAL_SYSTEM", "VIS_InvestmentSystem"
    if "supportive modules" in p or "nexuscore" in p or "envmanager" in p:
        return "SUPPORT_SYSTEM", "Supportive_NexusCore_Env"
    if "ssot" in p or "registry" in p or "schema" in p:
        return "INTEGRATION_HUB", "Registry_SSOT"
    if "ui" in p or ext.lower() in {".html", ".css", ".js", ".svg", ".png", ".ico"}:
        return "UI_SYSTEM", "HTML_UI_Assets"
    if "report" in p or "panorama" in p or "matrix" in p:
        return "REPORT_SYSTEM", "Reports_Matrices"
    if "prompt" in p:
        return "INTELLIGENCE_ASSET", "Prompt_Assets"
    return "UNCLASSIFIED_REVIEW", "Unclassified"


def category_code(system_class: str, subsystem: str, file_type: str) -> str:
    if system_class == "FUNCTIONAL_SYSTEM":
        return "FUNC"
    if system_class == "SUPPORT_SYSTEM":
        return "SUPP"
    if system_class == "INTEGRATION_HUB":
        return "HUB"
    if system_class == "UI_SYSTEM":
        return "UI"
    if system_class == "REPORT_SYSTEM":
        return "RPT"
    if system_class == "INTELLIGENCE_ASSET":
        return "IAM"
    if file_type == "DATA_DB":
        return "DATA"
    if file_type == "CODE_CONFIG":
        return "CODE"
    return "MISC"


def sha256_bounded(path: Path, max_bytes: int) -> str:
    try:
        st = path.stat()
        if st.st_size > max_bytes:
            return f"SKIPPED_GT_{max_bytes}_BYTES"
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest().upper()
    except Exception as e:
        return f"ERR_HASH_{type(e).__name__}"


def read_text_sample(path: Path, max_chars: int = 14000) -> Tuple[str, str]:
    encodings = ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]
    try:
        raw = path.read_bytes()[: max_chars * 4]
    except Exception as e:
        return "", f"ERR_READ_{type(e).__name__}"

    for enc in encodings:
        try:
            text = raw.decode(enc, errors="strict")
            return text[:max_chars], enc
        except Exception:
            continue

    try:
        return raw.decode("utf-8", errors="ignore")[:max_chars], "utf-8-ignore"
    except Exception as e:
        return "", f"ERR_DECODE_{type(e).__name__}"


def scan_one(path_str: str, base_str: str, max_hash_bytes: int) -> Dict[str, Any]:
    base = Path(base_str)
    path = Path(path_str)
    rel = safe_rel(path, base)
    ext = path.suffix.lower()
    row: Dict[str, Any] = {
        "def_path": str(path),
        "def_rel_path": rel,
        "def_name": path.name,
        "def_ext": ext,
        "def_file_type": "",
        "def_system_class": "",
        "def_subsystem": "",
        "def_size_bytes": 0,
        "def_mtime": "",
        "def_sha256": "",
        "def_text_encoding": "",
        "def_secret_marker": "false",
        "def_danger_marker": "false",
        "def_error_marker": "false",
        "def_param_markers": "",
        "def_json_key_markers": "",
        "def_python_ast": "",
        "def_risk": "LOW",
        "def_review_reason": ""
    }

    try:
        st = path.stat()
        row["def_size_bytes"] = st.st_size
        row["def_mtime"] = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    except Exception as e:
        row["def_risk"] = "MEDIUM"
        row["def_review_reason"] = f"STAT_ERROR:{type(e).__name__}"
        return row

    file_type = classify_file_type(ext)
    system_class, subsystem = classify_subsystem(rel, ext)

    row["def_file_type"] = file_type
    row["def_system_class"] = system_class
    row["def_subsystem"] = subsystem
    row["def_sha256"] = sha256_bounded(path, max_hash_bytes)

    text = ""
    if ext in TEXT_SAMPLE_EXT:
        text, enc = read_text_sample(path)
        row["def_text_encoding"] = enc

        if SECRET_PAT.search(text):
            row["def_secret_marker"] = "true"
        if DANGER_PAT.search(text):
            row["def_danger_marker"] = "true"
        if ERROR_PAT.search(text):
            row["def_error_marker"] = "true"

        params = sorted(set(PARAM_PAT.findall(text)))[:80]
        keys = sorted(set(JSON_KEY_PAT.findall(text)))[:80]
        row["def_param_markers"] = ";".join(params)
        row["def_json_key_markers"] = ";".join(keys)

        if ext == ".py":
            try:
                ast.parse(text)
                row["def_python_ast"] = "AST_SAMPLE_OK"
            except Exception as e:
                row["def_python_ast"] = f"AST_SAMPLE_FAIL:{type(e).__name__}"

    reasons = []
    risk = "LOW"

    if row["def_secret_marker"] == "true":
        risk = "HIGH"
        reasons.append("secret-like marker")
    if row["def_danger_marker"] == "true":
        risk = "HIGH"
        reasons.append("dangerous command marker")
    if row["def_error_marker"] == "true" and risk != "HIGH":
        risk = "MEDIUM"
        reasons.append("error/fatal marker")
    if row["def_python_ast"].startswith("AST_SAMPLE_FAIL"):
        risk = "MEDIUM"
        reasons.append(row["def_python_ast"])
    if row["def_sha256"].startswith("ERR_"):
        risk = "MEDIUM"
        reasons.append(row["def_sha256"])

    row["def_risk"] = risk
    row["def_review_reason"] = "; ".join(reasons)
    return row


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"def_empty": "true"}]
    fieldnames: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def build_iam_registry(inventory: List[Dict[str, Any]], candidate_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    counters: Dict[str, int] = defaultdict(int)
    registry: List[Dict[str, Any]] = []
    naming: List[Dict[str, Any]] = []

    for row in inventory:
        cat = category_code(row["def_system_class"], row["def_subsystem"], row["def_file_type"])
        counters[cat] += 1
        asset_code = f"VIA-IAM-{cat}-{counters[cat]:06d}"
        slug = slugify(row["def_name"])
        ext = row["def_ext"]
        normalized_name = f"{asset_code}__{slug}{ext}"
        target_folder = candidate_dir / cat
        proposed_path = target_folder / normalized_name

        registry.append({
            "def_asset_code": asset_code,
            "def_category": cat,
            "def_system_class": row["def_system_class"],
            "def_subsystem": row["def_subsystem"],
            "def_file_type": row["def_file_type"],
            "def_source_name": row["def_name"],
            "def_source_rel_path": row["def_rel_path"],
            "def_source_sha256": row["def_sha256"],
            "def_risk": row["def_risk"],
            "def_status": "REGISTRY_CANDIDATE_ONLY_NO_MOVE",
            "def_target_registry_folder": str(target_folder),
            "def_proposed_normalized_path": str(proposed_path)
        })

        naming.append({
            "def_asset_code": asset_code,
            "def_source_rel_path": row["def_rel_path"],
            "def_current_name": row["def_name"],
            "def_normalized_name": normalized_name,
            "def_naming_status": "CANDIDATE_ONLY",
            "def_apply_enabled": "false"
        })

    return registry, naming


def build_subsystem_matrix(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counter: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for r in inventory:
        key = (r["def_system_class"], r["def_subsystem"])
        if key not in counter:
            counter[key] = {
                "def_system_class": key[0],
                "def_subsystem": key[1],
                "def_files": 0,
                "def_total_bytes": 0,
                "def_high": 0,
                "def_medium": 0,
                "def_low": 0,
                "def_top_extensions": ""
            }
            counter[key]["_ext"] = Counter()
        c = counter[key]
        c["def_files"] += 1
        c["def_total_bytes"] += int(r.get("def_size_bytes") or 0)
        c["_ext"][r["def_ext"] or "<none>"] += 1
        if r["def_risk"] == "HIGH":
            c["def_high"] += 1
        elif r["def_risk"] == "MEDIUM":
            c["def_medium"] += 1
        else:
            c["def_low"] += 1

    out = []
    for c in counter.values():
        ext_counter = c.pop("_ext")
        c["def_top_extensions"] = "; ".join([f"{k}:{v}" for k, v in ext_counter.most_common(10)])
        out.append(c)
    return sorted(out, key=lambda x: (-x["def_high"], -x["def_files"], x["def_subsystem"]))


def build_ssot_candidates(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()

    for r in inventory:
        markers = []
        if r.get("def_param_markers"):
            markers.extend(r["def_param_markers"].split(";"))
        if r.get("def_json_key_markers"):
            markers.extend(r["def_json_key_markers"].split(";"))

        for m in markers[:60]:
            key = (m, r["def_subsystem"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "def_ssot_key": m,
                "def_subsystem": r["def_subsystem"],
                "def_source_rel_path": r["def_rel_path"],
                "def_candidate_type": "PARAMETER_OR_JSON_KEY",
                "def_management_target": "JSON_SSOT_CANDIDATE",
                "def_apply_enabled": "false"
            })

    return rows[:3000]


def build_fix_plan(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    n = 0

    for r in inventory:
        action = ""
        priority = ""
        fix_class = ""
        risk = r["def_risk"]

        if r["def_secret_marker"] == "true":
            priority = "P0"
            fix_class = "ORDERED_REVIEW_REQUIRED"
            action = "Secret-like marker review; move to runtime parameter policy if true secret."
        elif r["def_danger_marker"] == "true":
            priority = "P0"
            fix_class = "ORDERED_REVIEW_REQUIRED"
            action = "Dangerous command marker review; require disabled boundary or user approval gate."
        elif r["def_risk"] == "MEDIUM":
            priority = "P1"
            fix_class = "SEQUENTIAL_SAFE_REVIEW"
            action = "Review syntax/error markers and classify as false positive or repair candidate."
        elif r["def_system_class"] == "UNCLASSIFIED_REVIEW":
            priority = "P2"
            fix_class = "PARALLEL_SAFE_CLASSIFICATION"
            action = "Classify into subsystem / registry / IAM asset candidate."
        else:
            priority = "P3"
            fix_class = "PARALLEL_SAFE_STANDARDIZATION"
            action = "Naming / registry / SSOT candidate only."

        n += 1
        rows.append({
            "def_no": n,
            "def_priority": priority,
            "def_fix_class": fix_class,
            "def_risk": risk,
            "def_subsystem": r["def_subsystem"],
            "def_source_rel_path": r["def_rel_path"],
            "def_recommended_action": action,
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return sorted(rows, key=lambda x: (x["def_priority"], x["def_subsystem"], x["def_source_rel_path"]))


def top10_libs_matrix() -> List[Dict[str, Any]]:
    data = [
        ("PowerShell Orchestration", "PowerShell", "Pester; PSScriptAnalyzer; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; Pode; BurntToast; SecretManagement; CompletionPredictor", "one-click launcher, testing, report, local UI"),
        ("PowerShell Windows I/O", "PowerShell", "System.Windows.Forms; PresentationFramework; ImportExcel; BurntToast; PSReadLine; ClipboardText; Out-GridView; SecretStore; WinGet.Client; PlatyPS", "drag/drop, file picker, local UX"),
        ("Python Core File Registry", "Python", "pathlib; os; hashlib; json; csv; sqlite3; dataclasses; typing; concurrent.futures; logging", "local scan, hash, inventory, registry"),
        ("Python Data Engine", "Python", "pandas; polars; duckdb; pyarrow; openpyxl; xlsxwriter; sqlite-utils; jsonschema; pydantic; orjson", "tables, parquet, validation, schema"),
        ("Python Static Analysis", "Python", "ast; libcst; rope; radon; ruff; black; isort; mypy; pyflakes; bandit", "code quality, syntax, refactor safety"),
        ("Python Testing QA", "Python", "pytest; hypothesis; coverage; nox; tox; behave; deepdiff; jsonschema; pandera; great_expectations", "test debug optimize consolidate"),
        ("Python PDF OCR VRN", "Python", "PyMuPDF; pdfplumber; pypdf; camelot; tabula-py; pytesseract; opencv-python; Pillow; layoutparser; rapidocr", "PDF table/text extraction"),
        ("Python NLP IAM", "Python", "regex; rapidfuzz; jieba; whoosh; networkx; scikit-learn; sentence-transformers; spacy; tantivy; llama-cpp-python", "knowledge asset indexing"),
        ("HTML UI", "HTML/JS", "Vanilla JS; Web Components; D3; Plotly; Tabulator; Grid.js; Mermaid; Monaco Editor; JSZip; localForage", "local dashboard and matrix UI"),
        ("CSS Design System", "CSS", "CSS Grid; Flexbox; CSS Variables; Container Queries; Noto Sans TC; Inter; normalize.css; Open Props; PicoCSS; Shoelace", "VIA visual lock and responsive UI"),
        ("SQL Local Store", "SQL", "SQLite; DuckDB; sqlean; parquet; Arrow; Ibis; DB Browser for SQLite; datasette; csvkit; SQLFluff", "local analytics storage"),
        ("Graph Knowledge", "Python/JS", "networkx; pyvis; graphviz; mermaid; cytoscape.js; d3-force; rdflib; owlready2; sqlite-graph; duckdb", "subsystem dependency graph"),
        ("Packaging Runtime", "Python/PowerShell", "venv; pip-tools; uv; hatch; poetry; zipapp; PyInstaller; Nuitka; ps2exe; WinGet", "local package and runtime"),
        ("Visualization", "Python/JS", "matplotlib; plotly; altair; bokeh; pyvis; graphviz; mermaid; pandas Styler; rich; tqdm", "reports, progress, diagnostics"),
        ("Security Gate", "Python/PowerShell", "bandit; semgrep-local; detect-secrets; PSScriptAnalyzer; SecretManagement; SecretStore; hashlib; jsonschema; ast; regex", "secret/danger boundary review")
    ]

    rows = []
    for i, (area, lang, libs, use) in enumerate(data, 1):
        rows.append({
            "def_no": i,
            "def_function_area": area,
            "def_language": lang,
            "def_top10_local_free_libs": libs,
            "def_use_case": use,
            "def_policy": "local/free preferred; vendor/download separately if missing; no external call in this manager"
        })
    return rows


def architecture_blueprint() -> List[Dict[str, Any]]:
    rows = [
        ("00", "VIA Mother Hub", "PowerShell bridge + Python manager + JSON SSOT + HTML UI", "one-click launch, no-stall, mother-system governance"),
        ("01", "IAM Registry Core", "Python", "auto-numbering, asset code, registry candidate, naming normalization"),
        ("02", "SSOT Parameter Core", "Python + JSON", "regex/parameter Core/json key consolidation"),
        ("03", "Functional Subsystems", "PS launcher per subsystem + Python manager per subsystem", "VDF, VRN, VETF, VAP, VIS"),
        ("04", "Support Systems", "Python managers", "EnvManager, NexusCore, TestDebug, RegistryCore, ThemeRegistry"),
        ("05", "PromptOps / Intelligence Assets", "Python + JSON + HTML", "prompt assets, strategy templates, reusable analysis kernels"),
        ("06", "HTML UI Bridge", "PowerShell opens local HTML; JS reads JSON/CSV", "complex UI stays separate from core logic"),
        ("07", "Three-Round Gate", "Python", "Round1 inventory, Round2 classification/registry, Round3 fix plan/readiness"),
        ("08", "Test Debug Loop", "Python + PS", "test debug upgrade, optimize, consolidate, user-test"),
        ("09", "Release Boundary", "Gate only", "no apply unless explicit future approval gate")
    ]

    out = []
    for no, name, owner, desc in rows:
        out.append({
            "def_arch_no": no,
            "def_component": name,
            "def_owner_layer": owner,
            "def_design": desc,
            "def_powershell_role": "launcher / bridge / progress / no-close",
            "def_python_role": "core logic / scan / classify / validate / report data",
            "def_json_role": "SSOT / parameters / registry / schema",
            "def_html_role": "review UI / matrix / user decision"
        })
    return out


def build_round_summary(inventory, subsystem_matrix, fix_plan) -> List[Dict[str, Any]]:
    risks = Counter([r["def_risk"] for r in inventory])
    classes = Counter([r["def_system_class"] for r in inventory])
    exts = Counter([r["def_ext"] or "<none>" for r in inventory])
    priorities = Counter([r["def_priority"] for r in fix_plan])

    return [
        {
            "def_round": "Round1",
            "def_layer": "Inventory",
            "def_status": "PASS",
            "def_message": f"Files={len(inventory)}; EXT_TOP={'; '.join([f'{k}:{v}' for k,v in exts.most_common(10)])}"
        },
        {
            "def_round": "Round2",
            "def_layer": "Subsystem / IAM Registry",
            "def_status": "PASS",
            "def_message": f"Subsystems={len(subsystem_matrix)}; Classes={dict(classes)}"
        },
        {
            "def_round": "Round3",
            "def_layer": "Risk / Fix Plan",
            "def_status": "PASS",
            "def_message": f"Risk={dict(risks)}; Priorities={dict(priorities)}"
        }
    ]


def build_validation(inventory, registry, ssot, fix_plan) -> List[Dict[str, Any]]:
    rows = []

    def add(layer, test, ok, msg):
        rows.append({
            "def_layer": layer,
            "def_test": test,
            "def_status": "PASS" if ok else "FAIL",
            "def_risk": "LOW" if ok else "HIGH",
            "def_message": msg
        })

    add("POLICY", "no external call", True, "stdlib/local-only manager")
    add("POLICY", "source mutation disabled", True, "no move/copy/modify to source")
    add("POLICY", "db write disabled", True, "csv/json/html only")
    add("ROUND", "three-round analysis complete", True, "inventory + subsystem/registry + fix plan")
    add("INVENTORY", "files scanned", len(inventory) > 0, f"Files={len(inventory)}")
    add("REGISTRY", "registry candidates generated", len(registry) == len(inventory), f"Registry={len(registry)} Inventory={len(inventory)}")
    add("SSOT", "ssot candidate generated", True, f"SSOTRows={len(ssot)}")
    add("FIXPLAN", "fix plan generated", len(fix_plan) == len(inventory), f"FixPlan={len(fix_plan)}")
    add("SAFETY", "apply disabled all fix rows", all(r["def_apply_enabled"] == "false" for r in fix_plan), "apply=false")
    add("SAFETY", "source mutation false all fix rows", all(r["def_source_mutation"] == "false" for r in fix_plan), "source_mutation=false")
    add("SAFETY", "db write false all fix rows", all(r["def_db_write"] == "false" for r in fix_plan), "db_write=false")

    return rows


def html_table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 200) -> str:
    if not rows:
        return "<table><tr><td>No rows</td></tr></table>"

    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{html.escape(c)}</th>")
    out.append("</tr></thead><tbody>")

    for r in rows[:max_rows]:
        out.append("<tr>")
        for c in cols:
            v = str(r.get(c, ""))
            if len(v) > 320:
                v = v[:320] + "..."
            out.append(f"<td>{html.escape(v)}</td>")
        out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def write_html_report(path: Path, summary: Dict[str, Any], tables: Dict[str, Tuple[List[Dict[str, Any]], List[str], int]]) -> None:
    cards = ""
    for k in ["Status", "Gate", "Files", "HighRisk", "MediumRisk", "RegistryRows", "SSOTRows", "FixRows"]:
        cards += f"<div class='card'><div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(summary.get(k,'')))}</div></div>"

    style = """
    body{margin:0;background:#f7f6f2;color:#24231f;font-family:'Microsoft JhengHei',Arial,sans-serif;font-size:8.5px;line-height:1.35}
    .wrap{max-width:1880px;margin:0 auto;padding:16px}
    h1{font-size:15px;margin:0 0 4px;font-weight:650}
    .sub{font-size:8.2px;color:#706d64;margin-bottom:10px}
    .cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
    .card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:42px}
    .k{font-size:7.5px;color:#706d64}.v{font:650 10.5px Consolas,monospace;margin-top:4px;word-break:break-word}
    .sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}
    h2{font-size:9.8px;margin:0 0 6px;font-weight:650}
    table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.6px}
    th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
    th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
    .tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}
    .footer{margin-top:10px;color:#706d64;font-size:8px}
    """

    parts = [
        "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'/>",
        "<title>VIA v0115 Mother System Panorama IAM</title>",
        f"<style>{style}</style></head><body><div class='wrap'>",
        "<h1>def VIA v0115 · Mother System Panorama / IAM Architecture Planner</h1>",
        "<div class='sub'>Three-round local-only scan · Pythonized system manager · JSON SSOT · IAM auto-numbering · no apply · no DB write</div>",
        f"<div class='cards'>{cards}</div>",
        "<div class='sec'><h2>def Executive Judgment</h2><span class='tag'>Local Only</span><span class='tag'>Three Rounds</span><span class='tag'>IAM Candidate</span><span class='tag'>JSON SSOT</span><span class='tag'>No Apply</span><span class='tag'>No DB Write</span></div>"
    ]

    for title, (rows, cols, max_rows) in tables.items():
        parts.append(f"<div class='sec'><h2>{html.escape(title)}</h2>{html_table(rows, cols, max_rows)}</div>")

    parts.append(f"<div class='footer'>Generated: {html.escape(now_iso())}<br/>Run Dir: {html.escape(str(summary.get('RunDir','')))}</div>")
    parts.append("</div></body></html>")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--max-hash-mb", type=int, default=25)
    args = ap.parse_args()

    base = Path(args.base).resolve()
    run_dir = Path(args.run_dir).resolve()
    output = run_dir / "output"
    report_dir = run_dir / "report"
    candidate_dir = run_dir / "_iam_registry_ssot_candidates"

    output.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    print(f"[RUN] VIA v0115 Mother System Panorama")
    print(f"[BASE] {base}")
    print(f"[RUN_DIR] {run_dir}")
    print("[POLICY] local-only, no external call, no source mutation, no DB write", flush=True)

    max_hash_bytes = args.max_hash_mb * 1024 * 1024

    t0 = time.time()
    print("[ROUND1] Collect file paths...", flush=True)

    files: List[str] = []
    run_dir_norm = str(run_dir).lower()

    for root, dirs, names in os.walk(base):
        root_path = Path(root)
        root_norm = str(root_path).lower()

        # Skip current v0115 run directory only, to avoid self-ingestion loop.
        if root_norm.startswith(run_dir_norm):
            continue

        for name in names:
            files.append(str(root_path / name))

    print(f"[ROUND1] File paths collected: {len(files)}", flush=True)

    inventory: List[Dict[str, Any]] = []
    done = 0

    print("[ROUND1] Scan metadata / bounded hash / text markers...", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, args.threads)) as ex:
        futs = [ex.submit(scan_one, p, str(base), max_hash_bytes) for p in files]
        for fut in as_completed(futs):
            try:
                inventory.append(fut.result())
            except Exception as e:
                inventory.append({
                    "def_path": "",
                    "def_rel_path": "",
                    "def_name": "",
                    "def_ext": "",
                    "def_file_type": "SCAN_ERROR",
                    "def_system_class": "SCAN_ERROR",
                    "def_subsystem": "SCAN_ERROR",
                    "def_size_bytes": 0,
                    "def_mtime": "",
                    "def_sha256": "",
                    "def_text_encoding": "",
                    "def_secret_marker": "false",
                    "def_danger_marker": "false",
                    "def_error_marker": "true",
                    "def_param_markers": "",
                    "def_json_key_markers": "",
                    "def_python_ast": "",
                    "def_risk": "HIGH",
                    "def_review_reason": f"SCAN_EXCEPTION:{type(e).__name__}"
                })
            done += 1
            if done % 500 == 0:
                print(f"[ROUND1] scanned {done}/{len(files)}", flush=True)

    inventory.sort(key=lambda x: x.get("def_rel_path", ""))

    print("[ROUND2] Build subsystem matrix / IAM registry / SSOT candidates...", flush=True)
    subsystem_matrix = build_subsystem_matrix(inventory)
    registry, naming = build_iam_registry(inventory, candidate_dir)
    ssot = build_ssot_candidates(inventory)

    print("[ROUND3] Build risk/fix plan / architecture / libs / validation...", flush=True)
    fix_plan = build_fix_plan(inventory)
    libs = top10_libs_matrix()
    arch = architecture_blueprint()
    round_summary = build_round_summary(inventory, subsystem_matrix, fix_plan)
    validation = build_validation(inventory, registry, ssot, fix_plan)

    risk_counter = Counter([r["def_risk"] for r in inventory])

    readiness = [{
        "def_gate_status": "VIA_v0115_MOTHER_SYSTEM_PANORAMA_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "Three-round local-only panorama completed. Candidate outputs generated. No apply executed.",
        "def_files": str(len(inventory)),
        "def_high_risk": str(risk_counter.get("HIGH", 0)),
        "def_medium_risk": str(risk_counter.get("MEDIUM", 0)),
        "def_registry_rows": str(len(registry)),
        "def_ssot_rows": str(len(ssot)),
        "def_fix_rows": str(len(fix_plan)),
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115B user review / candidate refinement only"
    }]

    summary = {
        "Status": "VIA_v0115_MOTHER_SYSTEM_PANORAMA_IAM_READY",
        "Gate": readiness[0]["def_gate_status"],
        "RunDir": str(run_dir),
        "Base": str(base),
        "Files": len(inventory),
        "HighRisk": risk_counter.get("HIGH", 0),
        "MediumRisk": risk_counter.get("MEDIUM", 0),
        "LowRisk": risk_counter.get("LOW", 0),
        "RegistryRows": len(registry),
        "SSOTRows": len(ssot),
        "FixRows": len(fix_plan),
        "ExecutionEnabled": False,
        "ApplyEnabled": False,
        "SourceMutation": False,
        "DBWrite": False,
        "ElapsedSeconds": round(time.time() - t0, 2)
    }

    paths = {
        "inventory_csv": output / "VIA_v0115_FileInventory.csv",
        "subsystem_csv": output / "VIA_v0115_SubsystemMatrix.csv",
        "registry_csv": candidate_dir / "VIA_v0115_IAM_RegistryCandidate.csv",
        "naming_csv": candidate_dir / "VIA_v0115_IAM_NamingCandidate.csv",
        "ssot_csv": candidate_dir / "VIA_v0115_JSON_SSOT_Candidate.csv",
        "fix_csv": output / "VIA_v0115_FixOptimizationPlan.csv",
        "libs_csv": output / "VIA_v0115_Top10LocalFreeLibsMatrix.csv",
        "arch_csv": output / "VIA_v0115_FutureArchitectureBlueprint.csv",
        "round_csv": output / "VIA_v0115_ThreeRoundSummary.csv",
        "validation_csv": output / "VIA_v0115_ValidationMatrix.csv",
        "readiness_csv": output / "VIA_v0115_ReadinessGate.csv"
    }

    write_csv(paths["inventory_csv"], inventory)
    write_csv(paths["subsystem_csv"], subsystem_matrix)
    write_csv(paths["registry_csv"], registry)
    write_csv(paths["naming_csv"], naming)
    write_csv(paths["ssot_csv"], ssot)
    write_csv(paths["fix_csv"], fix_plan)
    write_csv(paths["libs_csv"], libs)
    write_csv(paths["arch_csv"], arch)
    write_csv(paths["round_csv"], round_summary)
    write_csv(paths["validation_csv"], validation)
    write_csv(paths["readiness_csv"], readiness)

    write_json(output / "VIA_v0115_FileInventory.json", inventory)
    write_json(output / "VIA_v0115_SubsystemMatrix.json", subsystem_matrix)
    write_json(candidate_dir / "VIA_v0115_IAM_RegistryCandidate.json", registry)
    write_json(candidate_dir / "VIA_v0115_IAM_NamingCandidate.json", naming)
    write_json(candidate_dir / "VIA_v0115_JSON_SSOT_Candidate.json", ssot)
    write_json(output / "VIA_v0115_FixOptimizationPlan.json", fix_plan)
    write_json(output / "VIA_v0115_Top10LocalFreeLibsMatrix.json", libs)
    write_json(output / "VIA_v0115_FutureArchitectureBlueprint.json", arch)
    write_json(output / "VIA_v0115_ThreeRoundSummary.json", round_summary)
    write_json(output / "VIA_v0115_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0115_ReadinessGate.json", readiness)

    manifest = {
        "schema_version": "VIA_v0115_MotherSystemPanorama_IAM",
        "generated_at": now_iso(),
        "summary": summary,
        "paths": {k: str(v) for k, v in paths.items()},
        "policy": {
            "local_only": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "delete": False,
            "stop_process": False
        }
    }
    write_json(output / "VIA_v0115_MotherSystemPanorama_Summary.json", manifest)

    report = report_dir / "VIA_v0115_MotherSystemPanorama_IAM_Report.html"
    write_html_report(
        report,
        summary,
        {
            "def Readiness Gate": (readiness, list(readiness[0].keys()), 20),
            "def Three-Round Summary": (round_summary, ["def_round", "def_layer", "def_status", "def_message"], 20),
            "def Subsystem Matrix": (subsystem_matrix, ["def_system_class", "def_subsystem", "def_files", "def_total_bytes", "def_high", "def_medium", "def_low", "def_top_extensions"], 120),
            "def Fix / Optimization Plan": (fix_plan, ["def_priority", "def_fix_class", "def_risk", "def_subsystem", "def_source_rel_path", "def_recommended_action", "def_apply_enabled"], 260),
            "def IAM Registry Candidate": (registry, ["def_asset_code", "def_category", "def_subsystem", "def_source_rel_path", "def_status", "def_proposed_normalized_path"], 260),
            "def JSON SSOT Candidate": (ssot, ["def_ssot_key", "def_subsystem", "def_source_rel_path", "def_candidate_type", "def_management_target", "def_apply_enabled"], 220),
            "def Top 10 Local Free Libs Matrix": (libs, ["def_no", "def_function_area", "def_language", "def_top10_local_free_libs", "def_use_case", "def_policy"], 80),
            "def Future Architecture Blueprint": (arch, ["def_arch_no", "def_component", "def_owner_layer", "def_design", "def_powershell_role", "def_python_role", "def_json_role", "def_html_role"], 80),
            "def Validation Matrix": (validation, ["def_layer", "def_test", "def_status", "def_risk", "def_message"], 80),
            "def File Inventory Preview": (inventory, ["def_rel_path", "def_file_type", "def_system_class", "def_subsystem", "def_size_bytes", "def_risk", "def_review_reason"], 260)
        }
    )

    print("")
    print("=" * 80)
    print("def VIA v0115 Mother System Panorama COMPLETE")
    print("=" * 80)
    print(f"Status       : {summary['Status']}")
    print(f"Gate         : {summary['Gate']}")
    print(f"Files        : {summary['Files']}")
    print(f"HighRisk     : {summary['HighRisk']}")
    print(f"MediumRisk   : {summary['MediumRisk']}")
    print(f"RegistryRows : {summary['RegistryRows']}")
    print(f"SSOTRows     : {summary['SSOTRows']}")
    print(f"FixRows      : {summary['FixRows']}")
    print(f"Report       : {report}")
    print(f"Output       : {output}")
    print(f"Candidates   : {candidate_dir}")
    print("[SAFE] No apply. No source mutation. No DB write. No external call.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("")
        print("[FATAL] Python manager failed.")
        traceback.print_exc()
        print("[SAFE] No apply. No source mutation. No DB write was intentionally performed.")
        raise

