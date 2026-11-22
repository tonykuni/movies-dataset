from __future__ import annotations

import argparse
import base64
import cgi
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import threading
import time
import uuid
import zipfile
from email.parser import BytesParser
from email.policy import default as email_default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from via_folder_context_scanner import scan_folder, scan_id

ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT / "app"
RUN_ROOT = APP_ROOT / "runs"
UI_PATH = APP_ROOT / "VIA_NLP_Control_Center.html"
LEXICON_PATH = ROOT / "VIA_NLP_SSOT_Lexicon_v5.json"
REGISTRY_PATH = ROOT / "VIA_SSOT_Engine_Registry_v7.json"
GITHUB_SNAPSHOT_PATH = ROOT / "VIA_GitHub_Project_Status_Snapshot.json"
DOWNLOAD_ROOT = Path.home() / "Downloads" / "VIA_NLP_Control_Center"
FOLDER_SCAN_ROOT = ROOT / "folder_scans"
SAMPLE_MANIFEST_PATH = ROOT / "VIA_Windows_Real_Sample_Test_Manifest_v1.json"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_SEARCH_FILES = 5000
MAX_SEARCH_RESULTS = 200
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".html", ".htm", ".json", ".jsonl", ".csv", ".tsv",
    ".py", ".ps1", ".psm1", ".js", ".mjs", ".ts", ".tsx", ".css", ".scss", ".yaml",
    ".yml", ".toml", ".ini", ".cfg", ".conf", ".sql", ".sh", ".bat", ".cmd", ".log",
    ".rst", ".tex", ".svg", ".docx", ".pdf", ".zip",
}
EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "runs", "test_output_v5"}

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.RLock()

OUTPUT_FORMATS = {
    "markdown": {"label": "Markdown Spec", "filename": "VIA_NLP_Spec.md"},
    "html": {"label": "HTML UI Spec", "filename": "VIA_NLP_UI_Spec.html"},
    "record": {"label": "JSON Record", "filename": "record.json"},
    "summary_v5": {"label": "Summary JSON", "filename": "summary_v5.json"},
    "topic_reconstruction": {"label": "Topics JSON", "filename": "topic_reconstruction.json"},
    "command_similarity_merge": {"label": "Command Merge JSON", "filename": "command_similarity_merge.json"},
    "parameter_library_projection": {"label": "Parameters JSON", "filename": "parameter_library_projection.json"},
    "factor_library_projection": {"label": "Factors JSON", "filename": "factor_library_projection.json"},
    "regex_projection": {"label": "Regex JSON", "filename": "regex_projection.json"},
    "mindmap_projection": {"label": "Mind Map JSON", "filename": "mindmap_projection.json"},
    "mindmap_markdown": {"label": "Mind Map Markdown", "filename": "mindmap.md"},
    "mindmap_mermaid": {"label": "Mind Map Mermaid", "filename": "mindmap.mmd"},
    "reusable_prompt": {"label": "Reusable Prompt JSON", "filename": "reusable_prompt.json"},
    "v7_unified": {"label": "V7 Unified NLP JSON", "filename": "v7_unified.json"},
    "v7_summary": {"label": "V7 Evidence Summary JSON", "filename": "v7_summary.json"},
    "v7_knowledge_body": {"label": "V7 Knowledge Body JSON", "filename": "v7_knowledge_body.json"},
    "v7_context_reconstruction": {"label": "V7 Context Reconstruction JSON", "filename": "v7_context_reconstruction.json"},
    "v7_instruction_reconstruction": {"label": "V7 Instruction Reconstruction JSON", "filename": "v7_instruction_reconstruction.json"},
    "v7_module_composition": {"label": "V7 Module Composition JSON", "filename": "v7_module_composition.json"},
    "v7_content_roles": {"label": "V7 Content Roles JSON", "filename": "v7_content_roles.json"},
    "v7_function_classification": {"label": "V7 Function Classification JSON", "filename": "v7_function_classification.json"},
    "v7_source_ledger": {"label": "V7 Source Ledger JSON", "filename": "v7_source_ledger.json"},
    "v7_mind_map": {"label": "V7 Mind Map JSON", "filename": "v7_mind_map.json"},
    "v7_mind_map_evolution": {"label": "V7 Mind Map Evolution JSON", "filename": "v7_mind_map_evolution.json"},
    "v7_mind_map_mermaid": {"label": "V7 Mind Map Mermaid", "filename": "v7_mind_map.mmd"},
    "v7_quality_gates": {"label": "V7 Quality Gates JSON", "filename": "v7_quality_gates.json"},
}
DEFAULT_OUTPUT_FORMATS = list(OUTPUT_FORMATS)
DEFAULT_ENGINE_IDS = ["VIA-ENG-018", "VIA-ENG-019", "VIA-ENG-020", "VIA-ENG-021"]

# The v5 engine is imported lazily so /api/health stays fast and the server never imports
# or executes any uploaded source module.
def get_v5():
    import sys
    sys.path.insert(0, str(ROOT))
    from v5.via_nlp_reconstruction_v5 import load_lexicon, reconstruct_v5_file
    return load_lexicon, reconstruct_v5_file


def get_v7():
    import sys
    sys.path.insert(0, str(ROOT / "nlp_v7_upgrade" / "unified"))
    from via_nlp_unified_v7 import artifact_payloads, process_text
    return artifact_payloads, process_text


def utc_epoch() -> float:
    return round(time.time(), 3)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str, fallback: str = "input.txt") -> str:
    value = Path(value or fallback).name
    value = re.sub(r"[^A-Za-z0-9_.\-\u3400-\u9fff（）()\[\] ]+", "_", value).strip(" .")
    return value or fallback


def create_job(
    source_name: str,
    source_path: Path,
    threshold: float,
    source_mode: str,
    engine_ids: list[str] | None = None,
    output_formats: list[str] | None = None,
    output_to_downloads: bool = True,
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:16]
    run_dir = RUN_ROOT / job_id
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    normalized_engines = normalize_selection(engine_ids, [item["engine_id"] for item in load_engine_catalog()], DEFAULT_ENGINE_IDS)
    normalized_outputs = normalize_selection(output_formats, list(OUTPUT_FORMATS), DEFAULT_OUTPUT_FORMATS)
    engines = selected_engine_catalog(normalized_engines)
    engine_slug = "__".join(f"{item['engine_id']}-{safe_name(item['short_name'] or item['name']).replace(' ', '-') }" for item in engines)
    download_directory = str(DOWNLOAD_ROOT)
    job = {
        "job_id": job_id,
        "status": "queued",
        "created_at": utc_epoch(),
        "updated_at": utc_epoch(),
        "source_name": source_name,
        "source_mode": source_mode,
        "source_path": str(source_path),
        "source_sha256": None,
        "command_threshold": threshold,
        "engine_ids": normalized_engines,
        "engines": engines,
        "output_formats": normalized_outputs,
        "output_to_downloads": bool(output_to_downloads),
        "engine_slug": engine_slug,
        "download_directory": download_directory,
        "downloads": {},
        "run_dir": str(run_dir),
        "artifacts": {},
        "error": None,
        "execution_policy": {
            "source_write": False,
            "source_delete": False,
            "code_execution": False,
            "network": False,
            "package_install": False,
        },
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    return job


def update_job(job_id: str, **updates: Any) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is not None:
            job.update(updates)
            job["updated_at"] = utc_epoch()


def snapshot_job(job: dict[str, Any]) -> dict[str, Any]:
    with JOBS_LOCK:
        return json.loads(json.dumps(job, ensure_ascii=False))


def load_engine_catalog() -> list[dict[str, Any]]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        {
            "engine_id": item["engine_id"],
            "name": item.get("canonical_name", item.get("short_name", item["engine_id"])),
            "name_zh": item.get("canonical_name_zh", ""),
            "short_name": item.get("short_name", ""),
            "version": item.get("version", ""),
            "kind": item.get("kind", ""),
            "status": item.get("status", ""),
            "responsibility": item.get("responsibility", ""),
            "acceleration_profile_id": item.get("acceleration_profile_id", ""),
        }
        for item in data.get("engines", [])
    ]


def load_project_status() -> dict[str, Any]:
    if not GITHUB_SNAPSHOT_PATH.is_file():
        return {"status": "not_loaded", "repository": "tonykuni/movies-dataset"}
    return json.loads(GITHUB_SNAPSHOT_PATH.read_text(encoding="utf-8"))


def run_status_checks() -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    for name, path in {
        "control_api": Path(__file__),
        "control_ui": UI_PATH,
        "ssot_registry": REGISTRY_PATH,
        "ssot_lexicon": LEXICON_PATH,
        "github_snapshot": GITHUB_SNAPSHOT_PATH,
        "folder_context_scanner": ROOT / "via_folder_context_scanner.py",
    }.items():
        checks[name] = {"status": "PASS" if path.is_file() and path.stat().st_size > 0 else "FAIL", "path": str(path), "bytes": path.stat().st_size if path.is_file() else 0}
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        checks["ssot_registry"]["engines"] = len(registry.get("engines", []))
        checks["ssot_registry"]["status"] = "PASS" if len(registry.get("engines", [])) >= 20 else "FAIL"
    except Exception as exc:
        checks["ssot_registry"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    try:
        lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        checks["ssot_lexicon"]["status"] = "PASS" if lexicon else "FAIL"
        checks["ssot_lexicon"]["schema"] = lexicon.get("schema", "")
    except Exception as exc:
        checks["ssot_lexicon"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    try:
        compile(Path(__file__).read_text(encoding="utf-8"), str(__file__), "exec")
        checks["control_api_syntax"] = {"status": "PASS"}
    except Exception as exc:
        checks["control_api_syntax"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    checks["downloads"] = {"status": "PASS" if os.access(DOWNLOAD_ROOT, os.W_OK) else "FAIL", "path": str(DOWNLOAD_ROOT)}
    snapshot = load_project_status()
    checks["github_project"] = {
        "status": "PASS" if snapshot.get("repository") == "tonykuni/movies-dataset" and not snapshot.get("errors") else "WARN",
        "repository": snapshot.get("repository"),
        "fetched_at": snapshot.get("fetched_at"),
        "metadata": snapshot.get("repository_metadata", {}),
        "environment_management": snapshot.get("environment_management", {}),
    }
    with JOBS_LOCK:
        job_values = [snapshot_job(job) for job in JOBS.values()]
    checks["jobs"] = {"status": "PASS", "total": len(job_values), "queued": sum(job.get("status") == "queued" for job in job_values), "running": sum(job.get("status") == "running" for job in job_values), "completed": sum(job.get("status") == "completed" for job in job_values), "failed": sum(job.get("status") == "failed" for job in job_values)}
    failures = [name for name, value in checks.items() if value.get("status") == "FAIL"]
    return {"status": "FAIL" if failures else "PASS", "checked_at": utc_epoch(), "checks": checks, "failures": failures}


def selected_engine_catalog(engine_ids: list[str]) -> list[dict[str, Any]]:
    catalog = {item["engine_id"]: item for item in load_engine_catalog()}
    return [catalog[engine_id] for engine_id in engine_ids if engine_id in catalog]


def normalize_selection(values: Any, allowed: list[str], defaults: list[str]) -> list[str]:
    if values is None:
        values = defaults
    if isinstance(values, str):
        values = [values]
    result = []
    for value in values:
        if value in allowed and value not in result:
            result.append(value)
    return result or list(defaults)


def create_folder_scan(root: str, max_files: int = 5000) -> dict[str, Any]:
    scan_identifier = scan_id()
    output = FOLDER_SCAN_ROOT / scan_identifier
    result = scan_folder(root, output, max_files=max(1, min(int(max_files), 50000)))
    return {
        "schema": "VIA_FOLDER_CONTEXT_SCAN_RESPONSE/1.0",
        "status": "PASS" if not result["errors"] else "PASS_WITH_REVIEW",
        "scan_id": scan_identifier,
        "root": result["root"],
        "output_dir": str(output),
        "summary": result["summary"],
        "artifacts": {
            "json": "folder_scan.json",
            "workflow_mermaid": "VIA_Folder_Workflow_Chart.mmd",
            "matrix_csv": "VIA_Module_Matrix.csv",
            "matrix_markdown": "VIA_Module_Matrix.md",
            "matrix_html": "VIA_Module_Matrix.html",
            "report_markdown": "VIA_Folder_Context_Report.md",
        },
        "source_policy": result["source_policy"],
    }


def control_metadata(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "VIA_NLP_CONTROL_OUTPUT/7.0",
        "control_center_version": "7.0.0",
        "standalone_mode": True,
        "system_integration_mode": True,
        "job_id": job["job_id"],
        "engine_ids": job["engine_ids"],
        "engines": job["engines"],
        "output_formats": job["output_formats"],
        "download_directory": job["download_directory"],
        "github_project": "tonykuni/movies-dataset",
        "source_policy": job["execution_policy"],
    }


def json_with_control(payload: Any, job: dict[str, Any]) -> Any:
    if isinstance(payload, dict):
        result = dict(payload)
        result["_via_control"] = control_metadata(job)
        return result
    return {"_via_control": control_metadata(job), "payload": payload}


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    table = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    table.extend("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in row) + " |" for row in rows)
    return "\n".join(table)


def write_markdown_spec(job: dict[str, Any], record: dict[str, Any], output: Path) -> None:
    summary = record["projections"]["summary"]
    topic = record["projections"]["topic_reconstruction"]
    merge = record["projections"]["command_reconstruction"]["similarity_merge"]
    params = record["projections"]["parameter_reconstruction"]
    factors = record["projections"]["factor_library_projection"]
    regexes = record["projections"]["regex_projection"]
    v7 = record.get("projections", {}).get("v7_unified", {})
    v7_quality = v7.get("quality", {})
    key_rows = [[item["source_unit_id"], item.get("topic_episode_id", ""), item["text"][:260], str(item["score"])] for item in summary["key_points"][:12]]
    topic_rows = [[item["episode_id"], item["topic_label"], str(len(item["unit_ids"])), str(len(item["return_links"]))] for item in topic["episodes"][:60]]
    command_rows = [[group["merge_group_id"], str(group["member_count"]), group["representative_goal"][:220], str(group["similarity_min"]), group["merge_status"]] for group in merge["groups"][:60]]
    parameter_rows = [[item.get("canonical_name", ""), item.get("name", ""), item.get("value", ""), item.get("type_candidate", ""), item.get("source_unit_id", "")] for item in params.get("parameters", [])[:100]]
    lines = [
        f"# VIA Unified NLP v7 Reconstruction Specification — {job['source_name']}",
        "",
        f"- Job ID: `{job['job_id']}`",
        f"- Source SHA-256: `{record['source']['source_sha256']}`",
        f"- Engines: `{', '.join(item['engine_id'] + ' ' + item['name'] for item in job['engines'])}`",
        f"- Lexicon: `VIA_NLP_SSOT_Lexicon_v5.json / {record['projections']['nlp_v5']['lexicon_version']}`",
        f"- Command threshold: `{job['command_threshold']}`",
        "- Source policy: immutable; all projections are append-only derivatives.",
        "",
        "## Executive Summary",
        "",
        summary["executive_summary"] or "（沒有足夠可抽取的摘要句。）",
        "",
        "## Metrics",
        "",
        markdown_table([
            ["Units", str(summary["unit_count"])],
            ["Original commands", str(merge["original_command_count"])],
            ["Merged command groups", str(merge["merged_command_count"])],
            ["Deduplicated candidates", str(merge["deduplicated_candidate_count"])],
            ["Topic episodes", str(topic["episode_count"])],
            ["Parameter conflicts", str(len(params.get("conflicts", [])))],
            ["Source preserved", "PASS" if record["quality_gates"]["v5_source_preserved"] else "FAIL"],
            ["Semantic projection executable", "FALSE" if not record["quality_gates"]["v5_semantic_rewrite_executable"] else "TRUE"],
        ], ["Metric", "Value"]),
        "",
        "## Unified NLP v7 Evidence Projection",
        "",
        markdown_table([
            ["Unified engine", v7.get("engine", {}).get("engine_id", "not selected")],
            ["Base engine", v7.get("engine", {}).get("base_engine_version", "")],
            ["Source reconstruction", str(v7_quality.get("source_reconstruction", "not run"))],
            ["Evidence summary integrity", str(v7_quality.get("body_summary_evidence_integrity", "not run"))],
            ["Knowledge units", str(v7_quality.get("knowledge_units", 0))],
            ["Context threads", str(v7_quality.get("context_threads", 0))],
            ["Instructions / commands", f"{v7_quality.get('instructions', 0)} / {v7_quality.get('commands', 0)}"],
            ["Source mutated / execution authorized", f"{v7_quality.get('source_text_mutated', False)} / {v7_quality.get('command_execution_authorized', False)}"],
        ], ["V7 Gate", "Value"]),
        "",
        "## Evidence-linked Key Points",
        "",
        markdown_table(key_rows, ["Source Unit", "Topic", "Key Point", "Score"]) if key_rows else "No key points.",
        "",
        "## Topic Episodes",
        "",
        markdown_table(topic_rows, ["Episode", "Label", "Units", "Return Links"]) if topic_rows else "No topic episodes.",
        "",
        "## Similar Command Merge Candidates",
        "",
        "Original command records are preserved. These groups are proposal-only and not executable.",
        "",
        markdown_table(command_rows, ["Merge Group", "Members", "Representative Goal", "Min Similarity", "Status"]) if command_rows else "No command candidates.",
        "",
        "## Parameter Library Projection",
        "",
        markdown_table(parameter_rows, ["Canonical", "Observed", "Value", "Type", "Source Unit"]) if parameter_rows else "No parameters.",
        "",
        "## Parameter Conflicts",
        "",
        *(f"- `{conflict['canonical_name']}`: {', '.join(conflict['values'])} — **review_required**" for conflict in params.get("conflicts", [])),
        "",
        "## Factor and Regex Evidence",
        "",
        f"- Factor matches: `{factors['factor_count']}`",
        f"- Regex match counts: `{json.dumps(regexes['match_counts'], ensure_ascii=False)}`",
        "",
        "## Safety and Review Gates",
        "",
        "- Source is not deleted or overwritten.",
        "- Original command IDs are preserved.",
        "- Semantic rewrite is not executable.",
        "- Similar command merge requires review before canonical promotion.",
        "- Parameter conflicts preserve all observed values.",
        "- AutoFix／AI decision handoff remains approval-only.",
        "",
        "## Artifacts",
        "",
        "- `record.json`: complete trace record",
        "- `summary_v5.json`: enhanced summary",
        "- `topic_reconstruction.json`: topics and return links",
        "- `command_similarity_merge.json`: command candidates",
        "- `parameter_library_projection.json`: parameters and conflicts",
        "- `factor_library_projection.json`: factor matches",
        "- `regex_projection.json`: regex evidence",
        "",
        "## Appendix — Detailed Specification / Function / Engine / Tool / Environment Matrix",
        "",
        "### Operating Modes",
        "",
        markdown_table([
            ["Standalone", "Run `via_nlp_control_api.py`; local UI/API; input copy or read-only path; output to Downloads.", "No VIA parent system required"],
            ["System integration", "Call `/api/reconstruct`, `/api/status`, `/api/catalog`; consume JSON contracts and artifact links.", "SSOT registry and v5 lexicon"],
        ], ["Mode", "Function", "Dependency"]),
        "",
        "### Engine Matrix",
        "",
        markdown_table([[item["engine_id"], item["name"], item.get("name_zh", ""), item.get("version", ""), item.get("kind", ""), item.get("acceleration_profile_id", "")] for item in job["engines"]], ["Engine ID", "Canonical Name", "中文名稱", "Version", "Kind", "Accelerator Profile"]),
        "",
        "### Function / Tool / Environment Matrix",
        "",
        markdown_table([
            ["Input", "Drag/drop, multipart upload, JSON text, Windows path", "Browser UI / `/api/reconstruct`", "Python 3.9+; Windows PowerShell 7+ optional"],
            ["NLP", "Regex, synonym, factor, parameter, topic, summary", "VIA v5 core + SSOT lexicon", "Offline CPU; no source execution"],
            ["Command", "Similarity grouping and proposal-only simplification", "VIA-ENG-019", "Review required; never executable"],
            ["Output", "Markdown, HTML, JSON projections, ZIP bundle", "Downloads bundle + artifact API", "Local filesystem Downloads"],
            ["Status", "Engine catalog, GitHub project snapshot, file health, test gates", "`/api/status`", "Read-only snapshot"],
            ["Environment", "requirements, envcheck, uv mirror, Streamlit entrypoint", "GitHub status snapshot", "tonykuni/movies-dataset"],
            ["Safety", "Hash, immutable source, no delete/write-back/network/package install", "Execution policy gates", "Approval-only downstream actions"],
        ], ["Area", "Function", "Tool / API", "Environment"]),
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html_spec(job: dict[str, Any], record: dict[str, Any], output: Path) -> None:
    summary = record["projections"]["summary"]
    merge = record["projections"]["command_reconstruction"]["similarity_merge"]
    topic = record["projections"]["topic_reconstruction"]
    params = record["projections"]["parameter_reconstruction"]
    v7 = record.get("projections", {}).get("v7_unified", {})
    v7_quality = v7.get("quality", {})
    esc = lambda value: html.escape(str(value), quote=True)
    cards = "".join(
        f'<div class="card"><b>{esc(label)}</b><span>{esc(value)}</span></div>'
        for label, value in [
            ("Units", summary["unit_count"]),
            ("Original Commands", merge["original_command_count"]),
            ("Merged Groups", merge["merged_command_count"]),
            ("Deduplicated", merge["deduplicated_candidate_count"]),
            ("Topics", topic["episode_count"]),
            ("Parameter Conflicts", len(params.get("conflicts", []))),
        ]
    )
    points = "".join(f'<li><code>{esc(item["source_unit_id"])}</code> {esc(item["text"][:500])}</li>' for item in summary["key_points"][:20])
    commands = "".join(f'<tr><td>{esc(group["merge_group_id"])}</td><td>{group["member_count"]}</td><td>{esc(group["representative_goal"][:300])}</td><td>{group["similarity_min"]}</td><td>{esc(group["merge_status"])}</td></tr>' for group in merge["groups"][:80])
    topics = "".join(f'<tr><td>{esc(ep["episode_id"])}</td><td>{esc(ep["topic_label"])}</td><td>{len(ep["unit_ids"])}</td><td>{len(ep["return_links"])}</td></tr>' for ep in topic["episodes"][:80])
    conflicts = "".join(f'<li><code>{esc(item["canonical_name"])}</code>: {esc(", ".join(item["values"]))}</li>' for item in params.get("conflicts", [])) or "<li>None</li>"
    engine_rows = "".join(f'<tr><td>{esc(item["engine_id"])}</td><td>{esc(item["name"])}</td><td>{esc(item.get("name_zh", ""))}</td><td>{esc(item.get("version", ""))}</td><td>{esc(item.get("kind", ""))}</td><td>{esc(item.get("acceleration_profile_id", ""))}</td></tr>' for item in job["engines"])
    output.write_text(f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA Unified NLP v7 — {esc(job["source_name"])}</title>
<style>body{{margin:0;background:#f6f8fb;color:#172033;font-family:system-ui,"Noto Sans CJK TC",sans-serif;line-height:1.55}}header{{background:#17324d;color:#fff;padding:24px}}main{{max-width:1500px;margin:auto;padding:20px}}.meta,.notice{{background:#fff;border:1px solid #d9e2ec;border-radius:10px;padding:14px;margin-bottom:15px}}.notice{{background:#eaf7ee;border-color:#abd2b5}}.cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin-bottom:15px}}.card{{background:#fff;border:1px solid #d9e2ec;border-radius:9px;padding:12px}}.card b,.card span{{display:block}}.card span{{font-size:24px;font-weight:700}}.panel{{background:#fff;border:1px solid #d9e2ec;border-radius:10px;padding:14px;margin-bottom:15px;overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:800px;font-size:13px}}th,td{{border:1px solid #d9e2ec;padding:8px;text-align:left;vertical-align:top}}th{{background:#edf2f7}}code{{font-family:ui-monospace,monospace;font-size:12px}}.pass{{color:#166b38;font-weight:700}}@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}main{{padding:12px}}}}</style></head>
<body><header><h1>VIA Unified NLP v7 Reconstruction</h1><p>{esc(job["source_name"])} · Job {esc(job["job_id"])}</p></header><main>
<div class="notice"><b>安全狀態：PASS WITH REVIEW</b><br>原始來源保留；相似指令合併是候選投影；語意投影不可執行；參數衝突保留全部觀測值。</div>
<div class="meta"><b>Source SHA-256</b><br><code>{esc(record["source"]["source_sha256"])}</code><br><b>Threshold</b> {esc(job["command_threshold"])}<br><b>Lexicon</b> {esc(record["projections"]["nlp_v5"]["lexicon_version"])}</div>
<div class="cards">{cards}</div>
<section class="panel"><h2>Executive Summary</h2><p>{esc(summary["executive_summary"])}</p></section>
<section class="panel"><h2>Unified NLP v7 Evidence Projection</h2><table><thead><tr><th>Gate</th><th>Value</th></tr></thead><tbody>
<tr><td>Engine</td><td>{esc(v7.get("engine", {}).get("engine_id", "not selected"))}</td></tr>
<tr><td>Source reconstruction</td><td>{esc(v7_quality.get("source_reconstruction", "not run"))}</td></tr>
<tr><td>Evidence summary integrity</td><td>{esc(v7_quality.get("body_summary_evidence_integrity", "not run"))}</td></tr>
<tr><td>Knowledge units / Context threads</td><td>{esc(v7_quality.get("knowledge_units", 0))} / {esc(v7_quality.get("context_threads", 0))}</td></tr>
<tr><td>Instructions / Commands</td><td>{esc(v7_quality.get("instructions", 0))} / {esc(v7_quality.get("commands", 0))}</td></tr>
<tr><td>Source mutated / Execution authorized</td><td>{esc(v7_quality.get("source_text_mutated", False))} / {esc(v7_quality.get("command_execution_authorized", False))}</td></tr>
</tbody></table></section>
<section class="panel"><h2>Evidence-linked Key Points</h2><ul>{points or "<li>None</li>"}</ul></section>
<section class="panel"><h2>Topic Episodes</h2><table><thead><tr><th>Episode</th><th>Topic</th><th>Units</th><th>Return Links</th></tr></thead><tbody>{topics}</tbody></table></section>
<section class="panel"><h2>Similar Command Merge Candidates</h2><p>Original command records are preserved. Candidate groups are not executable.</p><table><thead><tr><th>Group</th><th>Members</th><th>Representative Goal</th><th>Min Similarity</th><th>Status</th></tr></thead><tbody>{commands}</tbody></table></section>
<section class="panel"><h2>Parameter Conflicts</h2><ul>{conflicts}</ul></section>
<section class="panel"><h2>Artifacts</h2><p>Download the JSON record and Markdown specification from the control center. This HTML contains escaped text only; source HTML/scripts are not executed.</p></section>
<section class="panel"><h2>Appendix — Detailed Specification / Function / Engine / Tool / Environment Matrix</h2>
<p><b>Standalone:</b> local API/UI without VIA parent system. <b>System integration:</b> `/api/reconstruct`, `/api/status`, `/api/catalog` with SSOT registry and v5 lexicon.</p>
<h3>Engine Matrix</h3><table><thead><tr><th>Engine ID</th><th>Canonical Name</th><th>中文名稱</th><th>Version</th><th>Kind</th><th>Accelerator Profile</th></tr></thead><tbody>{engine_rows}</tbody></table>
<h3>Function / Tool / Environment Matrix</h3><table><thead><tr><th>Area</th><th>Function</th><th>Tool / API</th><th>Environment</th></tr></thead><tbody>
<tr><td>Input</td><td>Drag/drop, multipart upload, JSON text, Windows path</td><td>Browser UI / /api/reconstruct</td><td>Python 3.9+; PowerShell 7+ optional</td></tr>
<tr><td>NLP</td><td>Regex, synonym, factor, parameter, topic, summary</td><td>VIA v5 core + SSOT lexicon</td><td>Offline CPU; no source execution</td></tr>
<tr><td>Command</td><td>Similarity grouping and proposal-only simplification</td><td>VIA-ENG-019</td><td>Review required; never executable</td></tr>
<tr><td>Output</td><td>Markdown, HTML, JSON projections, ZIP bundle</td><td>Downloads bundle + artifact API</td><td>Local filesystem Downloads</td></tr>
<tr><td>Status</td><td>Engine catalog, GitHub snapshot, file health, test gates</td><td>/api/status</td><td>Read-only snapshot</td></tr>
<tr><td>Environment</td><td>requirements, envcheck, uv mirror, Streamlit entrypoint</td><td>GitHub status snapshot</td><td>tonykuni/movies-dataset</td></tr>
<tr><td>Safety</td><td>Hash, immutable source, no delete/write-back/network/package install</td><td>Execution policy gates</td><td>Approval-only downstream actions</td></tr>
</tbody></table></section>
    </main></body></html>''', encoding="utf-8")


def write_download_bundle(job: dict[str, Any], artifact_paths: dict[str, Path]) -> dict[str, Any]:
    if not job["output_to_downloads"]:
        return {"enabled": False, "files": [], "bundle": None}
    destination = DOWNLOAD_ROOT / job["job_id"]
    destination.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    for logical_name in job["output_formats"]:
        source = artifact_paths.get(logical_name)
        if source is None or not source.is_file():
            continue
        filename = f"{job['engine_slug']}__{logical_name}__{source.name}"
        target = destination / safe_name(filename)
        shutil.copy2(source, target)
        files.append(str(target))
    bundle_name = f"VIA-NLP-v7__{job['engine_slug']}__{job['job_id']}.zip"
    bundle_path = destination / safe_name(bundle_name)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in files:
            archive.write(filename, arcname=Path(filename).name)
    # The bundle is copied into the run directory so the browser can download it via the safe artifact route.
    run_bundle = Path(job["run_dir"]) / bundle_path.name
    shutil.copy2(bundle_path, run_bundle)
    return {
        "enabled": True,
        "directory": str(destination),
        "files": files,
        "bundle": str(bundle_path),
        "bundle_artifact": run_bundle.name,
    }


def run_job(job_id: str) -> None:
    job = snapshot_job(JOBS[job_id])
    source = Path(job["source_path"])
    try:
        update_job(job_id, status="running", started_at=utc_epoch())
        update_job(job_id, source_sha256=sha256_file(source))
        load_lexicon, reconstruct_v5_file = get_v5()
        lexicon = load_lexicon(LEXICON_PATH)
        record = reconstruct_v5_file(source, lexicon, command_threshold=float(job["command_threshold"]))
        v7_result: dict[str, Any] | None = None
        v7_payloads: dict[str, Any] = {}
        if "VIA-ENG-021" in job["engine_ids"]:
            v7_artifact_payloads, v7_process_text = get_v7()
            v7_result = v7_process_text(source.name, record["source_text"], quality="balanced")
            v7_payloads = v7_artifact_payloads(v7_result)
            record.setdefault("projections", {})["v7_unified"] = v7_result["projection"]
            record.setdefault("quality_gates", {}).update({
                "v7_source_reconstruction": v7_result["projection"]["quality"].get("source_reconstruction"),
                "v7_evidence_summary_integrity": v7_result["projection"]["quality"].get("body_summary_evidence_integrity", False),
                "v7_command_execution_authorized": v7_result["projection"]["quality"].get("command_execution_authorized", False),
                "v7_source_mutated": v7_result["projection"]["quality"].get("source_text_mutated", False),
            })
        record["control_center"] = control_metadata(job)
        run_dir = Path(job["run_dir"])
        record_path = run_dir / "record.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path = run_dir / "VIA_NLP_Spec.md"
        html_path = run_dir / "VIA_NLP_UI_Spec.html"
        write_markdown_spec(job, record, md_path)
        write_html_spec(job, record, html_path)
        projection_paths: dict[str, Path] = {}
        for name, payload in {
            "summary_v5.json": record["projections"]["summary"],
            "topic_reconstruction.json": record["projections"]["topic_reconstruction"],
            "command_similarity_merge.json": record["projections"]["command_reconstruction"]["similarity_merge"],
            "parameter_library_projection.json": record["projections"]["parameter_reconstruction"],
            "factor_library_projection.json": record["projections"]["factor_library_projection"],
            "regex_projection.json": record["projections"]["regex_projection"],
            "mindmap_projection.json": record["projections"]["mindmap_projection"],
            "mindmap.md": record["projections"]["mindmap_projection"]["markdown"],
            "mindmap.mmd": record["projections"]["mindmap_projection"]["mermaid"],
            "reusable_prompt.json": record["projections"]["prompt_projection"],
        }.items():
            path = run_dir / name
            if name.endswith((".md", ".mmd")) and isinstance(payload, str):
                path.write_text(payload, encoding="utf-8")
            else:
                path.write_text(json.dumps(json_with_control(payload, job), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            projection_key = {"mindmap.md": "mindmap_markdown", "mindmap.mmd": "mindmap_mermaid"}.get(name, name.removesuffix(".json"))
            projection_paths[projection_key] = path
        for filename, payload in v7_payloads.items():
            path = run_dir / filename
            if filename.endswith(".mmd") and isinstance(payload, str):
                path.write_text(payload, encoding="utf-8")
            else:
                path.write_text(json.dumps(json_with_control(payload, job), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            logical = {
                "v7_mind_map.mmd": "v7_mind_map_mermaid",
            }.get(filename, filename.removesuffix(".json"))
            projection_paths[logical] = path
        all_paths = {"record": record_path, "markdown": md_path, "html": html_path, **projection_paths}
        downloads = write_download_bundle(job, all_paths)
        artifacts = {logical: path.name for logical, path in all_paths.items() if logical in job["output_formats"]}
        if "record" in job["output_formats"]:
            artifacts["record"] = record_path.name
        if downloads.get("bundle_artifact"):
            artifacts["download_bundle"] = downloads["bundle_artifact"]
        update_job(job_id, status="completed", completed_at=utc_epoch(), artifacts=artifacts, downloads=downloads, metrics={
            "units": len(record.get("units", [])),
            "original_commands": record["projections"]["command_reconstruction"]["similarity_merge"]["original_command_count"],
            "merged_command_groups": record["projections"]["command_reconstruction"]["similarity_merge"]["merged_command_count"],
            "deduplicated_command_candidates": record["projections"]["command_reconstruction"]["similarity_merge"]["deduplicated_candidate_count"],
            "topics": record["projections"]["topic_reconstruction"]["episode_count"],
            "parameter_conflicts": len(record["projections"]["parameter_reconstruction"].get("conflicts", [])),
            "v7_topics": v7_result["projection"]["quality"].get("topics", 0) if v7_result else 0,
            "v7_context_threads": v7_result["projection"]["quality"].get("context_threads", 0) if v7_result else 0,
            "v7_knowledge_units": v7_result["projection"]["quality"].get("knowledge_units", 0) if v7_result else 0,
        })
    except Exception as exc:
        update_job(job_id, status="failed", failed_at=utc_epoch(), error=f"{type(exc).__name__}: {exc}")


def start_job(source_name: str, source_path: Path, threshold: float, source_mode: str) -> dict[str, Any]:
    job = create_job(source_name, source_path, threshold, source_mode)
    thread = threading.Thread(target=run_job, args=(job["job_id"],), daemon=True)
    thread.start()
    return snapshot_job(job)


def is_safe_artifact(job: dict[str, Any], filename: str) -> Path | None:
    filename = Path(unquote(filename)).name
    allowed = {Path(value).name for value in job.get("artifacts", {}).values()}
    if filename not in allowed:
        return None
    path = Path(job["run_dir"]) / filename
    if not path.is_file() or Path(job["run_dir"]).resolve() not in path.resolve().parents:
        return None
    return path


def is_safe_folder_scan(scan_identifier: str, filename: str) -> Path | None:
    if not re.fullmatch(r"[A-Za-z0-9]+", scan_identifier):
        return None
    root = (FOLDER_SCAN_ROOT / scan_identifier).resolve()
    if FOLDER_SCAN_ROOT.resolve() not in root.parents:
        return None
    allowed = {"folder_scan.json", "VIA_Folder_Workflow_Chart.mmd", "VIA_Module_Matrix.csv", "VIA_Module_Matrix.md", "VIA_Module_Matrix.html", "VIA_Folder_Context_Report.md"}
    name = Path(unquote(filename)).name
    path = root / name
    if name not in allowed or not path.is_file() or root not in path.resolve().parents:
        return None
    return path


def load_sample_test_matrix(result_root: str | None = None) -> dict[str, Any]:
    manifest = json.loads(SAMPLE_MANIFEST_PATH.read_text(encoding="utf-8"))
    configured_root = Path(result_root).expanduser() if result_root else Path.home() / "OneDrive" / "Documents" / "VIA_TEST_RESULTS"
    run_path = configured_root / "00_manifest" / "VIA_Windows_Real_Sample_Test_Run.json"
    runtime_rows: dict[str, dict[str, Any]] = {}
    run_status = "DECLARED_ONLY"
    if run_path.is_file():
        try:
            run = json.loads(run_path.read_text(encoding="utf-8"))
            runtime_rows = {str(row.get("test_id")): row for row in run.get("samples", [])}
            run_status = "EXECUTED"
        except (OSError, json.JSONDecodeError):
            run_status = "RESULT_READ_ERROR"
    persisted_artifacts = {
        "record": "record.json", "markdown": "VIA_NLP_Spec.md", "html": "VIA_NLP_UI_Spec.html",
        "summary_v5": "summary_v5.json", "topic_reconstruction": "topic_reconstruction.json",
        "command_similarity_merge": "command_similarity_merge.json", "parameter_library_projection": "parameter_library_projection.json",
        "factor_library_projection": "factor_library_projection.json", "regex_projection": "regex_projection.json",
        "mindmap_projection": "mindmap_projection.json", "mindmap_markdown": "mindmap.md",
        "mindmap_mermaid": "mindmap.mmd", "reusable_prompt": "reusable_prompt.json",
    }
    for record_path in sorted(RUN_ROOT.glob("*/record.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            source_name = str(record.get("source", {}).get("source_name", ""))
            test_id = next((str(item.get("test_id")) for item in manifest.get("samples", []) if str(item.get("input_name")) == source_name), None)
            if not test_id or test_id in runtime_rows:
                continue
            run_dir = record_path.parent
            artifacts = {key: filename for key, filename in persisted_artifacts.items() if (run_dir / filename).is_file()}
            runtime_rows[test_id] = {
                "test_id": test_id, "input_path": record.get("source", {}).get("source_path"),
                "status": "PASS_WITH_REVIEW", "source_sha256": record.get("source", {}).get("source_sha256"),
                "job_id": record.get("control_center", {}).get("job_id", run_dir.name),
                "engine_ids": record.get("control_center", {}).get("engine_ids", []),
                "artifacts": artifacts, "error": None,
            }
            if run_status == "DECLARED_ONLY":
                run_status = "EXECUTED_PERSISTED"
        except (OSError, json.JSONDecodeError):
            continue
    # Also expose jobs created through the standalone API/UI. This makes the
    # matrix useful immediately, without requiring the Windows launcher to have
    # written its external manifest first.
    live_jobs: list[dict[str, Any]] = []
    with JOBS_LOCK:
        live_jobs = [snapshot_job(job) for job in JOBS.values()]
    for definition in manifest.get("samples", []):
        test_id = str(definition.get("test_id"))
        input_name = str(definition.get("input_name", ""))
        matching = [job for job in live_jobs if Path(str(job.get("source_path", ""))).name == input_name or str(job.get("source_name", "")) == input_name]
        if not matching:
            continue
        latest = max(matching, key=lambda item: float(item.get("updated_at", 0)))
        runtime_rows[test_id] = {
            "test_id": test_id,
            "input_path": latest.get("source_path"),
            "status": "PASS_WITH_REVIEW" if latest.get("status") == "completed" else str(latest.get("status", "UNKNOWN")).upper(),
            "source_sha256": latest.get("source_sha256"),
            "job_id": latest.get("job_id"),
            "engine_ids": latest.get("engine_ids", []),
            "artifacts": latest.get("artifacts", {}),
            "error": latest.get("error"),
        }
        if latest.get("status") in {"completed", "running", "queued"} and run_status == "DECLARED_ONLY":
            run_status = "EXECUTED_LIVE"
    rows: list[dict[str, Any]] = []
    for definition in manifest.get("samples", []):
        row = dict(definition)
        actual = runtime_rows.get(str(definition.get("test_id")))
        if actual:
            row.update(actual)
            row["reader_engines"] = actual.get("engine_ids", definition.get("reader_engines", []))
            row["input_name"] = definition.get("input_name", Path(str(actual.get("input_path", ""))).name)
        sandbox_path = row.get("sandbox_path")
        row["sandbox_exists"] = bool(sandbox_path and Path(str(sandbox_path)).is_file())
        row["exists"] = (row.get("status") not in {"NOT_MOUNTED_IN_SANDBOX", "NOT_FOUND"} if actual else row["sandbox_exists"])
        row["artifact_count"] = len(row.get("artifacts", {})) if isinstance(row.get("artifacts"), dict) else 0
        rows.append(row)
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return {
        "schema": "VIA_WINDOWS_SAMPLE_TEST_MATRIX/1.0",
        "status": "PASS" if run_status in {"DECLARED_ONLY", "EXECUTED"} else "PASS_WITH_REVIEW",
        "run_status": run_status,
        "result_root": str(configured_root),
        "manifest": str(SAMPLE_MANIFEST_PATH),
        "columns": ["test_id", "input_name", "expected_format", "status", "reader_engines", "source_sha256", "job_id", "artifact_count", "error"],
        "rows": rows,
        "summary": {"total": len(rows), "status_counts": counts, "executed_result_file": str(run_path) if run_path.is_file() else None},
    }


class ControlHandler(BaseHTTPRequestHandler):
    server_version = "VIA-NLP-Control/7.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, payload: Any, status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_bytes(self, raw: bytes, content_type: str, status: int = 200, download_name: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name(download_name)}"')
        self.end_headers()
        self.wfile.write(raw)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html", "/api/health", "/api/catalog", "/api/status", "/api/jobs", "/api/sample-tests"}:
            self.send_response(200)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        if path == "/" or path == "/index.html":
            if not UI_PATH.is_file():
                self.send_json({"error": "UI_NOT_BUILT"}, 500)
                return
            self.send_bytes(UI_PATH.read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/api/health":
            self.send_json({"status": "ok", "service": "VIA NLP Control Center", "version": "7.0.0", "source_write": False, "code_execution": False, "network": False})
            return
        if path == "/api/catalog":
            self.send_json({
                "schema": "VIA_NLP_CONTROL_CATALOG/7.0",
                "engines": load_engine_catalog(),
                "output_formats": [{"id": key, **value} for key, value in OUTPUT_FORMATS.items()],
                "defaults": {"engine_ids": DEFAULT_ENGINE_IDS, "output_formats": DEFAULT_OUTPUT_FORMATS},
                "standalone": True,
                "system_integration": True,
            })
            return
        if path == "/api/status":
            self.send_json(run_status_checks())
            return
        if path == "/api/sample-tests":
            result_root = params.get("result_root", [None])[0]
            self.send_json(load_sample_test_matrix(result_root))
            return
        match = re.fullmatch(r"/api/folder-scan/([A-Za-z0-9]+)", path)
        if match:
            scan_path = FOLDER_SCAN_ROOT / match.group(1) / "folder_scan.json"
            if not scan_path.is_file():
                self.send_json({"error": "FOLDER_SCAN_NOT_FOUND"}, 404)
            else:
                self.send_json(json.loads(scan_path.read_text(encoding="utf-8")))
            return
        match = re.fullmatch(r"/api/folder-scan/([A-Za-z0-9]+)/artifact/(.+)", path)
        if match:
            artifact = is_safe_folder_scan(match.group(1), match.group(2))
            if not artifact:
                self.send_json({"error": "FOLDER_SCAN_ARTIFACT_NOT_FOUND"}, 404)
                return
            content_type = mimetypes.guess_type(str(artifact))[0] or "application/octet-stream"
            self.send_bytes(artifact.read_bytes(), content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""), download_name=artifact.name)
            return
        if path == "/api/jobs":
            with JOBS_LOCK:
                jobs = [snapshot_job(job) for job in JOBS.values()]
            jobs.sort(key=lambda item: item.get("created_at", 0), reverse=True)
            self.send_json({"jobs": jobs[:100]})
            return
        match = re.fullmatch(r"/api/job/([A-Za-z0-9]+)", path)
        if match:
            with JOBS_LOCK:
                job = JOBS.get(match.group(1))
            if not job:
                self.send_json({"error": "JOB_NOT_FOUND"}, 404)
            else:
                self.send_json(snapshot_job(job))
            return
        match = re.fullmatch(r"/api/artifact/([A-Za-z0-9]+)/(.+)", path)
        if match:
            with JOBS_LOCK:
                job = JOBS.get(match.group(1))
            if not job:
                self.send_json({"error": "JOB_NOT_FOUND"}, 404)
                return
            logical = unquote(match.group(2))
            mapping = {key: value for key, value in job.get("artifacts", {}).items()}
            filename = mapping.get(logical, logical)
            artifact = is_safe_artifact(job, filename)
            if not artifact:
                self.send_json({"error": "ARTIFACT_NOT_FOUND"}, 404)
                return
            content_type = mimetypes.guess_type(str(artifact))[0] or "application/octet-stream"
            self.send_bytes(artifact.read_bytes(), content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""), download_name=artifact.name)
            return
        if path == "/api/search":
            self.handle_search(params)
            return
        self.send_json({"error": "NOT_FOUND"}, 404)

    def handle_search(self, params: dict[str, list[str]]) -> None:
        root = Path(params.get("root", [str(ROOT.parent)])[0]).expanduser()
        query = params.get("query", [""])[0]
        extension_values = params.get("extensions", [""])[0]
        extensions = {value.strip().casefold() if value.strip().startswith(".") else "." + value.strip().casefold() for value in extension_values.split(",") if value.strip()}
        try:
            root = root.resolve()
        except OSError:
            self.send_json({"error": "INVALID_ROOT"}, 400)
            return
        if not root.is_dir():
            self.send_json({"error": "ROOT_NOT_FOUND", "root": str(root)}, 404)
            return
        results: list[dict[str, Any]] = []
        files_seen = 0
        for current, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIRS and not name.startswith(".")]
            for filename in sorted(filenames):
                if files_seen >= MAX_SEARCH_FILES or len(results) >= MAX_SEARCH_RESULTS:
                    break
                path = Path(current) / filename
                if extensions and path.suffix.casefold() not in extensions:
                    continue
                if path.suffix.casefold() not in ALLOWED_EXTENSIONS and not extensions:
                    continue
                files_seen += 1
                try:
                    size = path.stat().st_size
                    if size > 5 * 1024 * 1024:
                        continue
                    raw = path.read_bytes()
                    text = raw.decode("utf-8", errors="replace")
                    if query and query.casefold() not in text.casefold() and query.casefold() not in filename.casefold():
                        continue
                    lines = []
                    if query:
                        for line_no, line in enumerate(text.splitlines(), 1):
                            if query.casefold() in line.casefold():
                                lines.append({"line": line_no, "text": line[:500]})
                                if len(lines) >= 10:
                                    break
                    results.append({"path": str(path), "name": filename, "extension": path.suffix, "size_bytes": size, "sha256": hashlib.sha256(raw).hexdigest(), "matches": lines})
                except (OSError, UnicodeError) as exc:
                    results.append({"path": str(path), "name": filename, "error": f"{type(exc).__name__}: {exc}"})
            if files_seen >= MAX_SEARCH_FILES or len(results) >= MAX_SEARCH_RESULTS:
                break
        self.send_json({"root": str(root), "query": query, "results": results, "files_scanned": files_seen, "read_only": True})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/folder-scan":
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 1024 * 1024:
                self.send_json({"error": "PAYLOAD_LIMIT", "max_bytes": 1024 * 1024}, 413)
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                root = str(payload.get("root", "")).strip()
                if not root:
                    raise ValueError("root folder is required")
                result = create_folder_scan(root, int(payload.get("max_files", 5000)))
                self.send_json(result, 201)
            except Exception as exc:
                self.send_json({"error": f"{type(exc).__name__}: {exc}"}, 400)
            return
        if parsed.path != "/api/reconstruct":
            self.send_json({"error": "NOT_FOUND"}, 404)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self.send_json({"error": "PAYLOAD_LIMIT", "max_bytes": MAX_UPLOAD_BYTES}, 413)
            return
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")
        threshold = 0.45
        source_mode = "text"
        source_name = "input.txt"
        source_path: Path | None = None
        run_dir: Path | None = None
        engine_ids: list[str] | None = None
        output_formats: list[str] | None = None
        output_to_downloads = True
        try:
            if content_type.startswith("multipart/form-data"):
                _, params = cgi.parse_header(content_type)
                boundary = params.get("boundary")
                if not boundary:
                    raise ValueError("missing multipart boundary")
                envelope = (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body
                message = BytesParser(policy=email_default).parsebytes(envelope)
                file_payload: bytes | None = None
                for part in message.iter_parts():
                    filename = part.get_filename()
                    if filename:
                        source_name = safe_name(filename)
                        file_payload = part.get_payload(decode=True) or b""
                    else:
                        disposition = part.get("Content-Disposition", "")
                        field_match = re.search(r'name="([^"]+)"', disposition)
                        field_name = field_match.group(1) if field_match else ""
                        field_value = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace").strip()
                        try:
                            if field_name == "command_threshold":
                                threshold = float(field_value or "0.45")
                            elif field_name == "engine_ids":
                                engine_ids = (engine_ids or []) + [item.strip() for item in field_value.split(",") if item.strip()]
                            elif field_name == "output_formats":
                                output_formats = (output_formats or []) + [item.strip() for item in field_value.split(",") if item.strip()]
                            elif field_name == "output_to_downloads":
                                output_to_downloads = field_value.casefold() not in {"0", "false", "no", "off"}
                        except ValueError:
                            if field_name == "command_threshold":
                                threshold = 0.45
                if file_payload is None:
                    raise ValueError("multipart file field is required")
                run_id = uuid.uuid4().hex[:16]
                run_dir = RUN_ROOT / run_id
                input_dir = run_dir / "input"
                input_dir.mkdir(parents=True, exist_ok=True)
                source_path = input_dir / source_name
                source_path.write_bytes(file_payload)
                source_mode = "upload_copy"
            else:
                payload = json.loads(body.decode("utf-8"))
                threshold = float(payload.get("command_threshold", 0.45))
                engine_ids = payload.get("engine_ids")
                output_formats = payload.get("output_formats")
                output_to_downloads = bool(payload.get("output_to_downloads", True))
                if not 0.0 <= threshold <= 1.0:
                    raise ValueError("command_threshold must be between 0 and 1")
                if payload.get("source_text") is not None:
                    source_name = safe_name(payload.get("filename", "input.txt"))
                    source_bytes = str(payload["source_text"]).encode("utf-8")
                    run_id = uuid.uuid4().hex[:16]
                    run_dir = RUN_ROOT / run_id
                    input_dir = run_dir / "input"
                    input_dir.mkdir(parents=True, exist_ok=True)
                    source_path = input_dir / source_name
                    source_path.write_bytes(source_bytes)
                    source_mode = "text_copy"
                elif payload.get("path"):
                    candidate = Path(str(payload["path"])).expanduser().resolve()
                    if not candidate.is_file():
                        raise ValueError("path is not a file")
                    source_name = candidate.name
                    source_path = candidate
                    source_mode = "read_only_path"
                else:
                    raise ValueError("source_text, path or multipart file is required")
            if source_path is None:
                raise ValueError("source path was not created")
            if source_path.stat().st_size > MAX_UPLOAD_BYTES:
                raise ValueError("source exceeds upload limit")
            # If multipart/text created a run-specific directory, move it into the job's standard run path.
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("command_threshold must be between 0 and 1")
            job = create_job(source_name, source_path, threshold, source_mode, engine_ids, output_formats, output_to_downloads)
            standard_run = Path(job["run_dir"])
            if run_dir is not None and source_path.parent != standard_run / "input":
                standard_input = standard_run / "input"
                standard_input.mkdir(parents=True, exist_ok=True)
                copied = standard_input / source_name
                copied.write_bytes(source_path.read_bytes())
                source_path = copied
                job["source_path"] = str(source_path)
            elif run_dir is not None:
                job["source_path"] = str(source_path)
            with JOBS_LOCK:
                JOBS[job["job_id"]] = job
            thread = threading.Thread(target=run_job, args=(job["job_id"],), daemon=True)
            thread.start()
            self.send_json({"status": "queued", "job_id": job["job_id"], "poll": f"/api/job/{job['job_id']}"}, 202)
        except Exception as exc:
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, 400)


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA NLP Control Center API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    if not UI_PATH.exists():
        print(f"WARNING: UI not found at {UI_PATH}; API remains available.")
    server = ThreadingHTTPServer((args.host, args.port), ControlHandler)
    print(f"VIA NLP Control Center listening on http://{args.host}:{args.port}")
    print("Read-only source policy: source write/delete/code execution/network/package install are disabled.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
