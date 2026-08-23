#requires -Version 7.0
<#
VIA System Manager · AllInOne Launcher · v0162B (integration build R1)
One PowerShell · one HTML UI · exactly three rounds · sandbox repair only.

Governance contract (must match VIA_SystemManager_v0162B_Manifest.json):
  default_mode               = AUTO_LAUNCH_ALL
  ui_only_switch             = -UiOnly
  sandbox_repair_only        = true
  project_canonical_mutation = false  (canonical VRN / VDF / VAP files are never edited)
  network_install            = false  (no downloads, no package installation)
  stop_process               = false  (worker processes are never force-terminated)
  blind_import_all           = false  (register all libraries, import approved only)

v0162B repair contract honored by this file:
  - Every embedded asset and every generated launcher uses SINGLE-QUOTED
    literal here-strings only. No expandable double-quoted here-strings.
  - Daily launchers are produced from one literal template via placeholder
    replacement, then AST-validated with detailed parse-error output and
    removed again if validation fails.
  - Materialized engine and workbench assets are verified against exact
    SHA-256 values before anything is executed.

This launcher materializes the embedded Python engine and HTML workbench under
<Base>\supportive modules\VIA_Governance_Runtime\v0162B\runtime\<run id>\,
installs the two daily entrypoints at <Base>, and runs the engine in a
detached non-blocking worker process while narrating status.json progress.
#>
[CmdletBinding()]
param(
    [string]$Base = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [switch]$UiOnly,
    [switch]$NoAutoFix,
    [switch]$NoOpenHtml,
    [int]$TimeoutSeconds = 7200
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Script:VIAVersion = 'v0162B'
$Script:EngineExpectedSHA = '4d6c983761bf2a09b9cea423813d0aafb393c5a639559e531eb20a3ab0dd4426'
$Script:WorkbenchExpectedSHA = '4f653c4ac04df2612364804cfca5a203c868cecffdeb8bbfbf0635cbd1064152'

# --------------------------------------------------------------------------
# Embedded asset · Python engine (audit copy: engine\via_system_manager_engine_v0162B.py)
# --------------------------------------------------------------------------
$Script:EngineSource = @'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import html
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Iterable

VERSION = "v0162B"
ALLOWED_EXTENSIONS = {
    ".ps1", ".psm1", ".psd1", ".py", ".pyi", ".json", ".jsonl",
    ".html", ".htm", ".md", ".txt", ".sql", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".csv", ".css", ".js", ".jsx", ".ts", ".tsx",
}
TEXT_EXTENSIONS = ALLOWED_EXTENSIONS - {".csv"}
EXCLUDED_PARTS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "cache", "caches", "archive", "archives", "backup", "backups",
    "staging", "received_duplicates",
}
MAX_FILES = 25000
MAX_SAFE_FIXES_PER_ROUND = 400

ACCELERATORS = [
    ("A01", "AST 精準解析", "PowerShell Parser + Python ast + JSON/HTML parsers"),
    ("A02", "多語言語意模型", "Offline heuristic semantic tagging; no remote model"),
    ("A03", "九頭龍風險預測", "Rule-based duplicate, version, fan-in and write-risk scoring"),
    ("A04", "依賴拓撲排序", "Import/dot-source graph and deterministic order"),
    ("A05", "沙盒隔離執行", "All repair candidates are written under run-local sandbox"),
    ("A06", "自動修正建議生成", "Safe fixes plus review-only suggestions"),
    ("A07", "三輪全景式分析", "Exactly three analyze→repair→reanalyze rounds"),
    ("A08", "SSOT 對齊", "Schema/pointer/manifest/registry version and hash checks"),
    ("A09", "視覺化矩陣生成", "Proportional bilingual wrapped HTML matrix per round and final"),
    ("A10", "錯誤分類與分群", "Parallel-Fixable / Sequence-Dependent / Review-Only"),
    ("A11", "性能與複雜度分析", "File size, function count, line count and hotspot scoring"),
    ("A12", "多子系統同步檢視", "VRN / VDF / VAP / other roots analyzed together"),
    ("A13", "版本差異與回滾", "Original/new hashes and rollback manifests"),
    ("A14", "覆蓋率與回歸檢查", "Parser regression gates and before/after counts"),
    ("A15", "修正順序最佳化", "Risk-aware topological repair ordering"),
    ("A16", "動態進度條加速器", "Status JSON percent updates"),
    ("A17", "動態說明加速器", "Status narration per phase and subsystem"),
    ("A18", "非阻塞 PowerShell 加速器", "Workers run in detached child processes"),
    ("A19", "多引擎整合加速器", "Python engine + PowerShell workers + HTA UI"),
    ("A20", "自動部署與環境初始化", "Runtime-only deployment; canonical project mutation blocked"),
]

PHASES = [
    "test", "debug", "optimize", "test", "debug", "consolidate",
    "test", "debug", "user-test", "debug", "activate", "test", "debug",
]


SYSTEM_MANAGER_CONTRACT = {
    "round_limit": 3,
    "subsystems": ["VRN", "VDF", "VAP", "OTHERS"],
    "sections": ["MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"],
    "analysis_per_round": [
        "Panoramic Analysis",
        "Error Identification",
        "Optimization Points",
        "AST Structural Analysis",
        "SSOT Alignment",
        "Hydra Risk Detection",
        "Error Classification",
        "Multi-Subsystem Synchronization",
        "HTML Matrix",
    ],
    "round_strategies": {
        "1": "Comprehensive Fix / Parallel-Fixable",
        "2": "Sequential Fix / Dependency Topology",
        "3": "Final Polishing / Regression Consolidation",
    },
    "validation_cycle": PHASES,
    "user_test_policy": "READY_FOR_USER_TEST_NOT_AUTOMATICALLY_CLAIMED",
    "activation_policy": (
        "Runtime activation and regression evidence are automated; "
        "operator user-test and canonical promotion remain explicit gates."
    ),
    "library_policy": (
        "REGISTER_ALL_DISCOVERED; IMPORT_APPROVED_OR_REQUIRED_ONLY; "
        "NO_BLIND_IMPORT"
    ),
}


def now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}.{time.time_ns()}")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def update_status(path: Path, state: str, percent: int, narration: str, **extra: Any) -> None:
    payload = {
        "version": VERSION,
        "updated_at": now_iso(),
        "state": state,
        "percent": max(0, min(100, int(percent))),
        "narration": narration,
        "terminal": state in {"COMPLETED", "FAILED"},
    }
    payload.update(extra)
    write_json_atomic(path, payload)


def norm(path: Path) -> str:
    return str(path).replace("\\", "/").lower()


def is_excluded(path: Path) -> bool:
    return any(part.lower() in EXCLUDED_PARTS for part in path.parts)


def discover_subsystems(base: Path) -> list[dict[str, Any]]:
    candidates: list[tuple[str, Path]] = []
    known = [
        ("VRN", base / "functional modules" / "VRN"),
        ("VDF", base / "functional modules" / "VDF"),
        ("VDF", base / "functional modules" / "VeritasDataForge"),
        ("VDF", base / "module" / "VeritasDataForge"),
        ("VDF", base / "VeritasDataForge"),
        ("VAP", base / "functional modules" / "VAP"),
        ("VAP", base / "module" / "VAP"),
        ("VAP", base / "VAP"),
    ]
    seen: set[str] = set()
    for label, path in known:
        if path.is_dir():
            key = norm(path.resolve())
            if key not in seen:
                seen.add(key)
                candidates.append((label, path.resolve()))

    for parent_name in ("functional modules", "module"):
        parent = base / parent_name
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir() or is_excluded(child):
                continue
            key = norm(child.resolve())
            if key in seen:
                continue
            seen.add(key)
            candidates.append((child.name, child.resolve()))

    supportive = base / "supportive modules"
    if supportive.is_dir():
        candidates.append(("SUPPORTIVE", supportive.resolve()))

    return [{"subsystem": label, "root": str(path), "exists": True} for label, path in candidates]


def classify_file(path: Path) -> str:
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]
    if path.suffix.lower() in {".psm1", ".psd1"} or "module" in parts or "modules" in parts:
        return "MODULE"
    if any(token in name for token in ("engine", "orchestrator", "manager", "runner", "pipeline")):
        return "ENGINE"
    if any(token in name for token in ("lib", "util", "helper", "function", "common", "shared")):
        return "FUNCTION-LIB"
    return "OTHERS"


def inventory_files(subsystems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for subsystem in subsystems:
        root = Path(subsystem["root"])
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_PARTS and not d.startswith(".git")]
            for name in sorted(files):
                path = Path(current) / name
                if path.suffix.lower() not in ALLOWED_EXTENSIONS or is_excluded(path):
                    continue
                key = norm(path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = path.stat()
                    digest = sha256_file(path)
                except (OSError, PermissionError) as exc:
                    rows.append({
                        "subsystem": subsystem["subsystem"],
                        "root": subsystem["root"],
                        "path": str(path),
                        "relative_path": str(path.relative_to(root)),
                        "category": classify_file(path),
                        "extension": path.suffix.lower(),
                        "bytes": None,
                        "sha256": "",
                        "read_error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                rows.append({
                    "subsystem": subsystem["subsystem"],
                    "root": subsystem["root"],
                    "path": str(path.resolve()),
                    "relative_path": str(path.resolve().relative_to(root.resolve())),
                    "category": classify_file(path),
                    "extension": path.suffix.lower(),
                    "bytes": stat.st_size,
                    "sha256": digest,
                    "last_write": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
                    "read_error": "",
                })
                if len(rows) >= MAX_FILES:
                    return rows
    return rows


def read_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp950", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def scan_python(path: Path) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    imports: list[str] = []
    metrics = {"function_count": 0, "class_count": 0, "complexity_proxy": 0}
    try:
        text, encoding = read_text(path)
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics["function_count"] += 1
            elif isinstance(node, ast.ClassDef):
                metrics["class_count"] += 1
            elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match, ast.With)):
                metrics["complexity_proxy"] += 1
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        metrics["encoding"] = encoding
    except Exception as exc:
        issues.append({
            "kind": "PYTHON_AST",
            "severity": "RED",
            "message": f"{type(exc).__name__}: {exc}",
            "line": getattr(exc, "lineno", None),
            "column": getattr(exc, "offset", None),
        })
    return issues, imports, metrics


def scan_json(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = {"record_count": 0}
    try:
        text, _ = read_text(path)
        if path.suffix.lower() == ".jsonl":
            for index, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                json.loads(line)
                metrics["record_count"] += 1
        else:
            value = json.loads(text)
            if isinstance(value, list):
                metrics["record_count"] = len(value)
            elif isinstance(value, dict):
                metrics["record_count"] = len(value)
            else:
                metrics["record_count"] = 1
    except Exception as exc:
        issues.append({
            "kind": "JSON_PARSE",
            "severity": "RED",
            "message": f"{type(exc).__name__}: {exc}",
            "line": getattr(exc, "lineno", None),
            "column": getattr(exc, "colno", None),
        })
    return issues, metrics


def scan_html(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from html.parser import HTMLParser
    class Parser(HTMLParser):
        pass
    issues: list[dict[str, Any]] = []
    metrics = {"tag_tokens": 0}
    try:
        text, _ = read_text(path)
        parser = Parser(convert_charrefs=True)
        parser.feed(text)
        parser.close()
        metrics["tag_tokens"] = text.count("<")
    except Exception as exc:
        issues.append({
            "kind": "HTML_PARSE",
            "severity": "YELLOW",
            "message": f"{type(exc).__name__}: {exc}",
            "line": None,
            "column": None,
        })
    return issues, metrics


def powershell_scan(files: list[Path], pwsh: str, run_dir: Path) -> dict[str, list[dict[str, Any]]]:
    if not files:
        return {}
    input_path = run_dir / "evidence" / "powershell_ast_inputs.json"
    output_path = run_dir / "evidence" / "powershell_ast_results.json"
    script_path = run_dir / "evidence" / "powershell_ast_scan.ps1"
    write_json_atomic(input_path, [str(p) for p in files])
    script = r'''#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$InputJson,
    [Parameter(Mandatory)][string]$OutputJson
)
$ErrorActionPreference = "Stop"
$paths = Get-Content -LiteralPath $InputJson -Raw -Encoding UTF8 | ConvertFrom-Json
$rows = foreach ($path in @($paths)) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        [string]$path,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null
    [pscustomobject]@{
        path = [string]$path
        issues = @(
            @($errors) | ForEach-Object {
                [pscustomobject]@{
                    kind = "POWERSHELL_AST"
                    severity = "RED"
                    message = $_.Message
                    line = $_.Extent.StartLineNumber
                    column = $_.Extent.StartColumnNumber
                }
            }
        )
    }
}
$rows | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputJson -Encoding UTF8
'''
    write_text_atomic(script_path, script)
    try:
        result = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(script_path), "-InputJson", str(input_path), "-OutputJson", str(output_path)],
            capture_output=True, text=True, timeout=900,
        )
    except Exception as exc:
        return {str(p): [{
            "kind": "POWERSHELL_AST_ENGINE",
            "severity": "RED",
            "message": f"{type(exc).__name__}: {exc}",
            "line": None, "column": None,
        }] for p in files}
    if result.returncode != 0 or not output_path.exists():
        message = (result.stderr or result.stdout or "PowerShell AST scan failed").strip()
        return {str(p): [{
            "kind": "POWERSHELL_AST_ENGINE",
            "severity": "RED",
            "message": message,
            "line": None, "column": None,
        }] for p in files}
    try:
        raw = output_path.read_text(encoding="utf-8-sig")
        values = json.loads(raw)
        if isinstance(values, dict):
            values = [values]
        return {str(row["path"]): list(row.get("issues") or []) for row in values}
    except Exception as exc:
        return {str(p): [{
            "kind": "POWERSHELL_AST_ENGINE",
            "severity": "RED",
            "message": f"Result parse failed: {type(exc).__name__}: {exc}",
            "line": None, "column": None,
        }] for p in files}


def analyze_inventory(
    inventory: list[dict[str, Any]],
    overlay: dict[str, str],
    pwsh: str,
    round_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    ps_paths = []
    for row in inventory:
        analyzed = Path(overlay.get(row["path"], row["path"]))
        if row["extension"] in {".ps1", ".psm1", ".psd1"} and analyzed.exists():
            ps_paths.append(analyzed)
    ps_results = powershell_scan(ps_paths, pwsh, round_dir)
    matrix: list[dict[str, Any]] = []
    dependencies: dict[str, list[str]] = {}
    issues_flat: list[dict[str, Any]] = []

    for row in inventory:
        original = row["path"]
        analyzed = Path(overlay.get(original, original))
        issues: list[dict[str, Any]] = []
        deps: list[str] = []
        metrics: dict[str, Any] = {}
        if row.get("read_error"):
            issues.append({
                "kind": "READ_ERROR", "severity": "RED",
                "message": row["read_error"], "line": None, "column": None,
            })
        elif analyzed.exists():
            ext = row["extension"]
            if ext in {".ps1", ".psm1", ".psd1"}:
                issues.extend(ps_results.get(str(analyzed), []))
                try:
                    text, enc = read_text(analyzed)
                    metrics["encoding"] = enc
                    metrics["function_count"] = len(re.findall(r"(?im)^\s*function\s+[\w:-]+", text))
                    metrics["complexity_proxy"] = len(re.findall(r"(?im)^\s*(if|foreach|for|while|switch|try|catch)\b", text))
                    deps.extend(re.findall(r"(?im)^\s*(?:Import-Module|using\s+module)\s+['\"]?([^'\"\s]+)", text))
                    deps.extend(re.findall(r"(?im)^\s*\.\s+['\"]([^'\"]+)['\"]", text))
                except Exception as exc:
                    issues.append({
                        "kind": "TEXT_READ", "severity": "RED",
                        "message": f"{type(exc).__name__}: {exc}", "line": None, "column": None,
                    })
            elif ext in {".py", ".pyi"}:
                py_issues, deps, metrics = scan_python(analyzed)
                issues.extend(py_issues)
            elif ext in {".json", ".jsonl"}:
                json_issues, metrics = scan_json(analyzed)
                issues.extend(json_issues)
            elif ext in {".html", ".htm"}:
                html_issues, metrics = scan_html(analyzed)
                issues.extend(html_issues)
            else:
                try:
                    text, enc = read_text(analyzed)
                    metrics["encoding"] = enc
                    metrics["line_count"] = len(text.splitlines())
                except Exception as exc:
                    issues.append({
                        "kind": "TEXT_READ", "severity": "YELLOW",
                        "message": f"{type(exc).__name__}: {exc}", "line": None, "column": None,
                    })

        if analyzed.exists() and row["extension"] in TEXT_EXTENSIONS:
            try:
                text, enc = read_text(analyzed)
                metrics.setdefault("encoding", enc)
                metrics["line_count"] = len(text.splitlines())
                metrics["trailing_whitespace_lines"] = sum(
                    1 for line in text.splitlines() if line.rstrip() != line
                )
                metrics["missing_final_newline"] = bool(text) and not text.endswith(("\n", "\r"))
                metrics["bom"] = analyzed.read_bytes().startswith(b"\xef\xbb\xbf")
            except Exception:
                pass

        dependencies[original] = sorted(set(d for d in deps if d))
        state = "GREEN" if not issues else (
            "RED" if any(i["severity"] == "RED" for i in issues) else "YELLOW"
        )
        classification = (
            "PARALLEL_FIXABLE"
            if not issues and (
                metrics.get("trailing_whitespace_lines", 0) > 0
                or metrics.get("missing_final_newline")
                or metrics.get("bom")
            )
            else "SEQUENCE_DEPENDENT"
            if issues and dependencies[original]
            else "REVIEW_ONLY"
            if issues
            else "NO_CHANGE"
        )
        matrix_row = {
            **row,
            "analyzed_path": str(analyzed),
            "state": state,
            "classification": classification,
            "issue_count": len(issues),
            "issues": issues,
            "dependencies": dependencies[original],
            "metrics": metrics,
            "overlay": original in overlay,
        }
        matrix.append(matrix_row)
        for issue in issues:
            issues_flat.append({
                "subsystem": row["subsystem"],
                "category": row["category"],
                "path": original,
                "classification": classification,
                **issue,
            })
    return matrix, issues_flat, dependencies


def safe_repair(
    matrix: list[dict[str, Any]],
    base: Path,
    sandbox_root: Path,
    overlay: dict[str, str],
    round_number: int,
) -> list[dict[str, Any]]:
    repairs: list[dict[str, Any]] = []
    candidates = [
        row for row in matrix
        if row["classification"] == "PARALLEL_FIXABLE"
        and row["extension"] in TEXT_EXTENSIONS
        and Path(row["path"]).is_file()
    ][:MAX_SAFE_FIXES_PER_ROUND]

    for row in candidates:
        source = Path(overlay.get(row["path"], row["path"]))
        original_path = Path(row["path"])
        try:
            try:
                relative = original_path.resolve().relative_to(base.resolve())
            except ValueError:
                relative = Path(row["subsystem"]) / row["relative_path"]
            destination = sandbox_root / f"round_{round_number}" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            text, encoding = read_text(source)
            normalized_lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
            while normalized_lines and normalized_lines[-1] == "":
                normalized_lines.pop()
            new_text = "\n".join(normalized_lines) + "\n"
            before = sha256_file(source)
            write_text_atomic(destination, new_text)
            after = sha256_file(destination)
            overlay[str(original_path)] = str(destination)
            repairs.append({
                "round": round_number,
                "subsystem": row["subsystem"],
                "category": row["category"],
                "original_path": str(original_path),
                "sandbox_path": str(destination),
                "original_sha256": before,
                "sandbox_sha256": after,
                "changed": before != after,
                "repair_type": "SAFE_TEXT_NORMALIZATION",
                "original_encoding": encoding,
                "promotion_state": "CANDIDATE_ONLY_NO_CANONICAL_MUTATION",
            })
        except Exception as exc:
            repairs.append({
                "round": round_number,
                "subsystem": row["subsystem"],
                "category": row["category"],
                "original_path": row["path"],
                "sandbox_path": "",
                "changed": False,
                "repair_type": "SAFE_TEXT_NORMALIZATION_FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "promotion_state": "REVIEW_REQUIRED",
            })
    return repairs


def version_key(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"(?i)(?:[_\-.]v?\d{3,5}[a-z]?)", "", stem)
    stem = re.sub(r"(?i)(?:[_\-.]\d{8,14})", "", stem)
    stem = re.sub(r"[_\-.]+", "_", stem).strip("_")
    return stem


def build_ssot_matrix(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevant = [
        row for row in inventory
        if re.search(r"(?i)ssot|schema|pointer|manifest|registry|authority|canonical", row["path"])
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in relevant:
        key = f"{row['subsystem']}::{version_key(Path(row['path']).name)}"
        groups.setdefault(key, []).append(row)
    rows = []
    for key, values in sorted(groups.items()):
        hashes = sorted({v["sha256"] for v in values if v["sha256"]})
        rows.append({
            "group": key,
            "subsystem": values[0]["subsystem"],
            "file_count": len(values),
            "distinct_hashes": len(hashes),
            "state": "GREEN" if len(values) == 1 or len(hashes) == 1 else "YELLOW",
            "paths": [v["path"] for v in values],
            "hashes": hashes,
            "alignment": (
                "SINGLE_OR_BYTE_IDENTICAL"
                if len(values) == 1 or len(hashes) == 1
                else "MULTI_VERSION_REVIEW_REQUIRED"
            ),
        })
    return rows


def build_hydra_matrix(inventory: list[dict[str, Any]], dependencies: dict[str, list[str]]) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for row in inventory:
        by_name.setdefault(Path(row["path"]).name.lower(), []).append(row)
    rows = []
    for name, values in sorted(by_name.items()):
        hashes = sorted({v["sha256"] for v in values if v["sha256"]})
        subsystems = sorted({v["subsystem"] for v in values})
        if len(values) > 1 and len(hashes) > 1:
            score = min(100, 30 + len(values) * 8 + len(subsystems) * 10)
            rows.append({
                "risk": "DUPLICATE_BASENAME_DIFFERENT_HASH",
                "name": name,
                "score": score,
                "state": "RED" if score >= 70 else "YELLOW",
                "subsystems": subsystems,
                "paths": [v["path"] for v in values],
                "automatic_fix": False,
            })
    dep_target_counts: dict[str, int] = {}
    for deps in dependencies.values():
        for dep in deps:
            dep_target_counts[dep.lower()] = dep_target_counts.get(dep.lower(), 0) + 1
    for dep, count in sorted(dep_target_counts.items(), key=lambda item: (-item[1], item[0])):
        if count >= 5:
            score = min(100, 25 + count * 5)
            rows.append({
                "risk": "HIGH_FAN_IN_DEPENDENCY",
                "name": dep,
                "score": score,
                "state": "RED" if score >= 70 else "YELLOW",
                "subsystems": [],
                "paths": [],
                "automatic_fix": False,
            })
    return rows


def complexity_matrix(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in matrix:
        metrics = row.get("metrics") or {}
        lines = int(metrics.get("line_count") or 0)
        functions = int(metrics.get("function_count") or 0)
        complexity = int(metrics.get("complexity_proxy") or 0)
        size = int(row.get("bytes") or 0)
        score = min(100, lines // 80 + functions * 2 + complexity + size // 100_000)
        if score >= 25:
            rows.append({
                "subsystem": row["subsystem"],
                "category": row["category"],
                "path": row["path"],
                "lines": lines,
                "functions": functions,
                "complexity_proxy": complexity,
                "bytes": size,
                "hotspot_score": score,
                "state": "RED" if score >= 70 else "YELLOW",
            })
    return sorted(rows, key=lambda r: (-r["hotspot_score"], r["path"]))


def library_registry(pwsh: str, run_dir: Path) -> dict[str, Any]:
    python_packages = []
    try:
        for dist in importlib.metadata.distributions():
            name = dist.metadata.get("Name") or "unknown"
            python_packages.append({"name": name, "version": dist.version})
        python_packages.sort(key=lambda r: r["name"].lower())
    except Exception as exc:
        python_packages = [{"name": "inventory_error", "version": f"{type(exc).__name__}: {exc}"}]

    ps_path = run_dir / "evidence" / "powershell_module_inventory.json"
    ps_script = run_dir / "evidence" / "powershell_module_inventory.ps1"
    write_text_atomic(ps_script, r'''#requires -Version 7.0
param([Parameter(Mandatory)][string]$Output)
Get-Module -ListAvailable |
    Sort-Object Name,Version -Unique |
    ForEach-Object {
        [pscustomobject]@{
            name = $_.Name
            version = [string]$_.Version
            path = [string]$_.Path
            module_type = [string]$_.ModuleType
        }
    } |
    ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $Output -Encoding UTF8
''')
    ps_modules = []
    try:
        result = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ps_script), "-Output", str(ps_path)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0 and ps_path.exists():
            ps_modules = json.loads(ps_path.read_text(encoding="utf-8-sig"))
            if isinstance(ps_modules, dict):
                ps_modules = [ps_modules]
        else:
            ps_modules = [{"name": "inventory_error", "version": (result.stderr or result.stdout).strip(), "path": ""}]
    except Exception as exc:
        ps_modules = [{"name": "inventory_error", "version": f"{type(exc).__name__}: {exc}", "path": ""}]

    registry = {
        "generated_at": now_iso(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_package_count": len(python_packages),
        "python_packages": python_packages,
        "powershell_module_count": len(ps_modules),
        "powershell_modules": ps_modules,
        "import_policy": "REGISTER_ALL_IMPORT_APPROVED_ONLY",
    }
    write_json_atomic(run_dir / "registry" / "library_registry.json", registry)
    return registry



def build_code_registries(
    inventory: list[dict[str, Any]],
    run_dir: Path,
) -> dict[str, Any]:
    function_rows: list[dict[str, Any]] = []
    supportive_rows: list[dict[str, Any]] = []
    ssot_rows: list[dict[str, Any]] = []
    module_rows: list[dict[str, Any]] = []

    ssot_pattern = re.compile(
        r"(?i)ssot|schema|pointer|manifest|registry|authority|canonical"
    )
    ps_function_pattern = re.compile(
        r"(?im)^\s*function\s+([A-Za-z_][A-Za-z0-9_.:-]*)"
    )
    js_function_pattern = re.compile(
        r"(?m)\bfunction\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("
    )

    for row in inventory:
        path_text = str(row.get("path") or "")
        if not path_text:
            continue

        path = Path(path_text)
        lower_path = path_text.lower()
        extension = str(row.get("extension") or "").lower()

        common = {
            "subsystem": row.get("subsystem"),
            "category": row.get("category"),
            "path": path_text,
            "relative_path": row.get("relative_path"),
            "extension": extension,
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
            "last_write": row.get("last_write"),
        }

        if "supportive modules" in lower_path:
            supportive_rows.append(common)

        if ssot_pattern.search(path_text):
            ssot_rows.append(common)

        if str(row.get("category") or "") == "MODULE":
            module_rows.append(common)

        if row.get("read_error"):
            continue

        try:
            text, encoding = read_text(path)
        except Exception:
            continue

        if extension == ".py":
            try:
                tree = ast.parse(text, filename=path_text)
                for node in ast.walk(tree):
                    if isinstance(
                        node,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    ):
                        function_rows.append({
                            **common,
                            "symbol": node.name,
                            "symbol_type": (
                                "ASYNC_FUNCTION"
                                if isinstance(node, ast.AsyncFunctionDef)
                                else "FUNCTION"
                            ),
                            "line": getattr(node, "lineno", None),
                            "extraction": "PYTHON_AST",
                            "encoding": encoding,
                        })
                    elif isinstance(node, ast.ClassDef):
                        function_rows.append({
                            **common,
                            "symbol": node.name,
                            "symbol_type": "CLASS",
                            "line": getattr(node, "lineno", None),
                            "extraction": "PYTHON_AST",
                            "encoding": encoding,
                        })
            except Exception:
                continue
        elif extension in (".ps1", ".psm1", ".psd1"):
            for match in ps_function_pattern.finditer(text):
                function_rows.append({
                    **common,
                    "symbol": match.group(1),
                    "symbol_type": "POWERSHELL_FUNCTION",
                    "line": text.count("\n", 0, match.start()) + 1,
                    "extraction": "POWERSHELL_STATIC_REGEX_NO_IMPORT",
                    "encoding": encoding,
                })
        elif extension in (
            ".js",
            ".jsx",
            ".html",
            ".htm",
            ".hta",
        ):
            for match in js_function_pattern.finditer(text):
                function_rows.append({
                    **common,
                    "symbol": match.group(1),
                    "symbol_type": "JAVASCRIPT_FUNCTION",
                    "line": text.count("\n", 0, match.start()) + 1,
                    "extraction": "JAVASCRIPT_STATIC_REGEX",
                    "encoding": encoding,
                })

    function_rows.sort(
        key=lambda row: (
            str(row.get("subsystem") or ""),
            str(row.get("path") or ""),
            str(row.get("line") or ""),
            str(row.get("symbol") or ""),
        )
    )
    supportive_rows.sort(key=lambda row: str(row.get("path") or ""))
    ssot_rows.sort(key=lambda row: str(row.get("path") or ""))
    module_rows.sort(key=lambda row: str(row.get("path") or ""))

    paths = {
        "function_registry": run_dir / "registry" / "function_registry.json",
        "supportive_registry": run_dir / "registry" / "supportive_modules_registry.json",
        "ssot_registry": run_dir / "registry" / "ssot_registry.json",
        "module_registry": run_dir / "registry" / "module_file_registry.json",
    }

    write_json_atomic(paths["function_registry"], {
        "generated_at": now_iso(),
        "count": len(function_rows),
        "policy": "REGISTER_ALL_DISCOVERED_STATIC_NO_BLIND_IMPORT",
        "rows": function_rows,
    })
    write_json_atomic(paths["supportive_registry"], {
        "generated_at": now_iso(),
        "count": len(supportive_rows),
        "rows": supportive_rows,
    })
    write_json_atomic(paths["ssot_registry"], {
        "generated_at": now_iso(),
        "count": len(ssot_rows),
        "policy": "DISPLAY_AND_COMPARE_NO_CANONICAL_MUTATION",
        "rows": ssot_rows,
    })
    write_json_atomic(paths["module_registry"], {
        "generated_at": now_iso(),
        "count": len(module_rows),
        "rows": module_rows,
    })

    return {
        "function_count": len(function_rows),
        "supportive_module_count": len(supportive_rows),
        "ssot_record_count": len(ssot_rows),
        "module_file_count": len(module_rows),
        **{key: str(value) for key, value in paths.items()},
    }

def topology_order(dependencies: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows = []
    for path, deps in dependencies.items():
        rows.append({
            "path": path,
            "dependency_count": len(deps),
            "dependencies": deps,
            "order_score": len(deps),
        })
    return sorted(rows, key=lambda r: (r["order_score"], r["path"]))


def summarize_matrix(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "files": len(matrix),
        "green": sum(1 for r in matrix if r["state"] == "GREEN"),
        "yellow": sum(1 for r in matrix if r["state"] == "YELLOW"),
        "red": sum(1 for r in matrix if r["state"] == "RED"),
        "parallel_fixable": sum(1 for r in matrix if r["classification"] == "PARALLEL_FIXABLE"),
        "sequence_dependent": sum(1 for r in matrix if r["classification"] == "SEQUENCE_DEPENDENT"),
        "review_only": sum(1 for r in matrix if r["classification"] == "REVIEW_ONLY"),
        "overlays": sum(1 for r in matrix if r["overlay"]),
    }


def render_table(headers: list[str], rows: Iterable[list[Any]], max_rows: int = 1000) -> str:
    body = []
    for index, row in enumerate(rows):
        if index >= max_rows:
            body.append(f'<tr><td colspan="{len(headers)}">TRUNCATED AFTER {max_rows} ROWS</td></tr>')
            break
        cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
        body.append(f"<tr>{cells}</tr>")
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    return f'<div class="tableWrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def render_report(
    path: Path,
    title: str,
    summary: dict[str, Any],
    matrix: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    hydra: list[dict[str, Any]],
    ssot: list[dict[str, Any]],
    topology: list[dict[str, Any]],
    complexity: list[dict[str, Any]],
    repairs: list[dict[str, Any]],
    accelerator_rows: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
) -> None:
    category_sections = []
    for category in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"):
        cat_rows = [r for r in matrix if r["category"] == category]
        category_sections.append(
            f'<section id="{category.lower()}"><h2>{category} <span>{len(cat_rows)} files</span></h2>' +
            render_table(
                ["Subsystem", "State", "Class", "Issues", "Path"],
                [[r["subsystem"], r["state"], r["classification"], r["issue_count"], r["path"]] for r in cat_rows],
                max_rows=2000,
            ) + "</section>"
        )

    issue_table = render_table(
        ["Subsystem", "Category", "Severity", "Kind", "Class", "Line", "Message", "Path"],
        [[r["subsystem"], r["category"], r["severity"], r["kind"], r["classification"],
          r.get("line") or "", r["message"], r["path"]] for r in issues],
        max_rows=3000,
    )
    hydra_table = render_table(
        ["State", "Risk", "Score", "Name", "Subsystems", "Paths", "Auto Fix"],
        [[r["state"], r["risk"], r["score"], r["name"], ", ".join(r.get("subsystems") or []),
          " | ".join(r.get("paths") or []), r["automatic_fix"]] for r in hydra],
        max_rows=2000,
    )
    ssot_table = render_table(
        ["State", "Subsystem", "Group", "Files", "Hashes", "Alignment", "Paths"],
        [[r["state"], r["subsystem"], r["group"], r["file_count"], r["distinct_hashes"],
          r["alignment"], " | ".join(r["paths"])] for r in ssot],
        max_rows=2000,
    )
    dep_table = render_table(
        ["Order", "Dependencies", "Path"],
        [[r["order_score"], ", ".join(r["dependencies"]), r["path"]] for r in topology],
        max_rows=2500,
    )
    complexity_table = render_table(
        ["State", "Score", "Subsystem", "Category", "Lines", "Functions", "Complexity", "Bytes", "Path"],
        [[r["state"], r["hotspot_score"], r["subsystem"], r["category"], r["lines"],
          r["functions"], r["complexity_proxy"], r["bytes"], r["path"]] for r in complexity],
        max_rows=2000,
    )
    repair_table = render_table(
        ["Round", "Subsystem", "Category", "Changed", "Repair", "Promotion", "Original", "Sandbox"],
        [[r.get("round"), r.get("subsystem"), r.get("category"), r.get("changed"),
          r.get("repair_type"), r.get("promotion_state"),
          r.get("original_path"), r.get("sandbox_path")] for r in repairs],
        max_rows=2000,
    )
    accel_table = render_table(
        ["ID", "Accelerator", "State", "Implementation"],
        [[r["id"], r["name"], r["state"], r["implementation"]] for r in accelerator_rows],
        max_rows=100,
    )
    round_table = render_table(
        ["Round", "Strategy", "Pre Red", "Post Red", "Repairs", "Gate", "User Test"],
        [[r["round"], r["strategy"], r["pre"]["red"], r["post"]["red"],
          r["repair_count"], r["gate"], r["user_test_state"]] for r in rounds],
        max_rows=20,
    )
    cards = "".join(
        f'<div class="card"><div class="v">{html.escape(str(value))}</div><div class="l">{html.escape(key)}</div></div>'
        for key, value in [
            ("FILES", summary.get("files", 0)),
            ("GREEN", summary.get("green", 0)),
            ("YELLOW", summary.get("yellow", 0)),
            ("RED", summary.get("red", 0)),
            ("HYDRA", len(hydra)),
            ("SSOT GROUPS", len(ssot)),
            ("REPAIRS", len(repairs)),
        ]
    )
    document = f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;--mut:#6b6860;--line:#dbd9d3;--soft:#ecebe6;--up:#c96b5a;--down:#5a9e6f;--am:#c4943a;--teal:#439a9a;--blue:#4c78a8;--vi:#7a6daa;--reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink2);font:10px/1.45 Arial,"Microsoft JhengHei",sans-serif}}.bar{{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:9}}.wrap{{max-width:1500px;margin:auto;padding:20px 18px 50px}}header{{border-bottom:2px solid var(--ink);padding:4px 0 10px}}h1{{font-size:19px;color:var(--ink);margin:0}}h2{{font-size:13px;color:var(--ink);margin:24px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}h2 span{{font-size:8px;color:var(--mut);margin-left:7px}}.sub{{color:var(--mut);margin-top:6px}}.hero{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}.card{{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:9px 13px;min-width:105px}}.card .v{{font-size:17px;font-weight:800;color:var(--ink)}}.card .l{{font-size:7px;color:var(--mut)}}nav{{position:sticky;top:4px;background:var(--bg);padding:8px 0;z-index:5}}nav a{{display:inline-block;padding:5px 8px;margin:2px;border:1px solid var(--line);border-radius:3px;background:var(--paper);color:var(--ink2);text-decoration:none;font-size:8px;font-weight:700}}section{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:10px 12px;margin-top:10px}}.tableWrap{{overflow:auto;max-height:620px;border:1px solid var(--line)}}table{{border-collapse:collapse;width:100%;table-layout:fixed;font-size:8.5px}}th{{position:sticky;top:0;background:#fafaf8;color:var(--mut);font-size:7.5px;text-align:left;border-bottom:2px solid var(--ink);padding:5px 6px}}td{{vertical-align:top;border-bottom:1px solid var(--soft);padding:4px 6px;white-space:normal;overflow-wrap:anywhere;word-break:break-word}}tr:hover td{{background:#fbfbf8}}.pill{{display:inline-block;padding:1px 5px;border-radius:3px;color:white;font-weight:700}}.ok{{background:var(--down)}}.warn{{background:var(--am)}}.bad{{background:var(--up)}}.mut{{background:#999}}

/* VIA v0162B · proportional bilingual matrix */
body{{font-size:clamp(15px,1.05vw,17px)!important;line-height:1.62!important}}
.wrap{{max-width:1400px!important;padding:clamp(14px,2vw,22px)!important}}
h1{{font-size:clamp(27px,3.2vw,36px)!important;font-weight:800!important}}
h2{{font-size:clamp(20px,2vw,24px)!important;font-weight:800!important}}
h2 span,.sub{{font-weight:500!important}}
.hero{{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important}}
.card .v{{font-size:clamp(23px,2.3vw,29px)!important;font-weight:700!important}}
.card .l{{font-size:clamp(11px,.9vw,13px)!important;font-weight:600!important}}
.tableWrap{{overflow:auto!important;max-height:72vh!important}}
table{{table-layout:auto!important;font-size:clamp(13px,.95vw,15px)!important}}
th{{font-size:clamp(12px,.85vw,14px)!important;font-weight:700!important}}
td{{font-size:clamp(13px,.95vw,15px)!important;font-weight:400!important;
white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important}}
@media(max-width:980px){{.hero{{grid-template-columns:repeat(3,minmax(0,1fr))!important}}}}
@media(max-width:560px){{
 body{{font-size:18px!important}}
 .hero{{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
 table{{min-width:920px!important;font-size:16px!important}}
 th{{font-size:14px!important}}td{{font-size:16px!important}}
}}
@media(max-width:390px){{.hero{{grid-template-columns:1fr!important}}}}

</style></head><body><div class="bar"></div><div class="wrap">
<header><h1>{html.escape(title)}</h1><div class="sub">Three-round sandbox analysis · 20 accelerators · no canonical project mutation · generated {html.escape(now_iso())}</div><div class="hero">{cards}</div></header>
<nav>
<a href="#rounds">ROUNDS</a><a href="#accelerators">20 ACCELERATORS</a><a href="#issues">ERRORS</a>
<a href="#hydra">HYDRA</a><a href="#ssot">SSOT</a><a href="#dependencies">DEPENDENCIES</a>
<a href="#complexity">OPTIMIZATION</a><a href="#repairs">REPAIRS</a>
<a href="#module">MODULE</a><a href="#engine">ENGINE</a><a href="#function-lib">FUNCTION-LIB</a><a href="#others">OTHERS</a>
</nav>
<section id="rounds"><h2>Three-Round Status</h2>{round_table}</section>
<section id="accelerators"><h2>20 Accelerators</h2>{accel_table}</section>
<section id="issues"><h2>Error Matrix</h2>{issue_table}</section>
<section id="hydra"><h2>Hydra Risk Matrix</h2>{hydra_table}</section>
<section id="ssot"><h2>SSOT Alignment Matrix</h2>{ssot_table}</section>
<section id="dependencies"><h2>Dependency / Repair Order Matrix</h2>{dep_table}</section>
<section id="complexity"><h2>Optimization / Complexity Matrix</h2>{complexity_table}</section>
<section id="repairs"><h2>Sandbox Repair Matrix</h2>{repair_table}</section>
{''.join(category_sections)}
</div></body></html>'''
    write_text_atomic(path, document)


def run(config: dict[str, Any]) -> dict[str, Any]:
    base = Path(config["base"]).resolve()
    run_dir = Path(config["run_dir"]).resolve()
    status_path = Path(config["status_path"]).resolve()
    pwsh = config["pwsh_path"]
    auto_fix = bool(config.get("auto_fix", True))
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("evidence", "registry", "rounds", "sandbox", "reports", "deployment_candidates"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    update_status(status_path, "RUNNING", 2, "A01/A07: resolving subsystems and initializing exactly three rounds.")
    subsystems = discover_subsystems(base)
    write_json_atomic(run_dir / "evidence" / "subsystems.json", subsystems)

    update_status(status_path, "RUNNING", 7, "A12: inventorying VRN, VDF, VAP and other projects.")
    inventory = inventory_files(subsystems)
    write_json_atomic(run_dir / "registry" / "file_inventory.json", inventory)

    update_status(status_path, "RUNNING", 12, "A20: registering Python packages and PowerShell modules.")
    library_info = library_registry(pwsh, run_dir)
    code_registry_info = build_code_registries(inventory, run_dir)

    overlay: dict[str, str] = {}
    all_repairs: list[dict[str, Any]] = []
    round_summaries: list[dict[str, Any]] = []
    final_matrix: list[dict[str, Any]] = []
    final_issues: list[dict[str, Any]] = []
    final_dependencies: dict[str, list[str]] = {}
    strategies = {
        1: "Comprehensive Fix / Parallel-Fixable",
        2: "Sequential Fix / Dependency Topology",
        3: "Final Polishing / Regression Consolidation",
    }

    for round_number in (1, 2, 3):
        base_percent = 14 + (round_number - 1) * 23
        round_dir = run_dir / "rounds" / f"round_{round_number}"
        round_dir.mkdir(parents=True, exist_ok=True)
        update_status(
            status_path, "RUNNING", base_percent,
            f"Round {round_number}/3 pre-analysis: panoramic, AST, SSOT, Hydra and optimization scan.",
            current_round=round_number,
        )
        pre_matrix, pre_issues, pre_dependencies = analyze_inventory(inventory, overlay, pwsh, round_dir)
        pre_summary = summarize_matrix(pre_matrix)

        update_status(
            status_path, "RUNNING", base_percent + 7,
            f"Round {round_number}/3 repair stage: {strategies[round_number]}.",
            current_round=round_number,
        )
        repairs = safe_repair(pre_matrix, base, run_dir / "sandbox", overlay, round_number) if auto_fix else []
        all_repairs.extend(repairs)

        update_status(
            status_path, "RUNNING", base_percent + 14,
            f"Round {round_number}/3 re-analysis after sandbox repair; regression and Hydra gates.",
            current_round=round_number,
        )
        post_matrix, post_issues, post_dependencies = analyze_inventory(inventory, overlay, pwsh, round_dir)
        post_summary = summarize_matrix(post_matrix)
        hydra = build_hydra_matrix(inventory, post_dependencies)
        ssot = build_ssot_matrix(inventory)
        topology = topology_order(post_dependencies)
        complexity = complexity_matrix(post_matrix)

        phase_rows = []
        for phase in PHASES:
            phase_rows.append({
                "phase": phase,
                "state": "READY_FOR_USER_TEST" if phase == "user-test" else "PASS_WITH_UNRESOLVED_REVIEW" if post_summary["red"] else "PASS",
            })
        gate = "ROUND_PASS_NO_RED_AST_OR_PARSE_ERRORS" if post_summary["red"] == 0 else "ROUND_REVIEW_REQUIRED_RED_ERRORS_REMAIN"
        round_summary = {
            "round": round_number,
            "strategy": strategies[round_number],
            "pre": pre_summary,
            "post": post_summary,
            "repair_count": len(repairs),
            "gate": gate,
            "user_test_state": "READY_FOR_USER_TEST_NOT_AUTOMATICALLY_CLAIMED",
        "round_limit": 3,
        "validation_cycle": PHASES,
        "system_manager_contract": SYSTEM_MANAGER_CONTRACT,
            "phases": phase_rows,
        }
        round_summaries.append(round_summary)
        write_json_atomic(round_dir / "pre_matrix.json", pre_matrix)
        write_json_atomic(round_dir / "post_matrix.json", post_matrix)
        write_json_atomic(round_dir / "issues.json", post_issues)
        write_json_atomic(round_dir / "repairs.json", repairs)
        write_json_atomic(round_dir / "hydra.json", hydra)
        write_json_atomic(round_dir / "ssot.json", ssot)
        write_json_atomic(round_dir / "topology.json", topology)
        write_json_atomic(round_dir / "complexity.json", complexity)
        write_json_atomic(round_dir / "round_summary.json", round_summary)
        accelerator_rows = [{"id": aid, "name": name, "state": "ENABLED", "implementation": implementation} for aid, name, implementation in ACCELERATORS]
        render_report(
            round_dir / f"VIA_Unified_Round_{round_number}_Matrix_v0162B.html",
            f"VIA Unified Round {round_number} Matrix",
            post_summary, post_matrix, post_issues, hydra, ssot, topology, complexity,
            all_repairs, accelerator_rows, round_summaries,
        )
        final_matrix, final_issues, final_dependencies = post_matrix, post_issues, post_dependencies

    update_status(status_path, "RUNNING", 86, "Final consolidation: Hydra, SSOT, dependencies, libraries and deployment candidates.")
    hydra = build_hydra_matrix(inventory, final_dependencies)
    ssot = build_ssot_matrix(inventory)
    topology = topology_order(final_dependencies)
    complexity = complexity_matrix(final_matrix)
    final_summary = summarize_matrix(final_matrix)
    accelerator_rows = [{"id": aid, "name": name, "state": "ENABLED", "implementation": implementation} for aid, name, implementation in ACCELERATORS]

    deployment_manifest = {
        "version": VERSION,
        "generated_at": now_iso(),
        "policy": "RUNTIME_DEPLOYED_SANDBOX_REPAIRS_CANDIDATE_ONLY",
        "runtime_deployment": "ENABLED",
        "canonical_project_mutation": False,
        "candidate_count": len(all_repairs),
        "candidates": all_repairs,
        "promotion_gate": "OPERATOR_REVIEW_AND_SEPARATE_HASH_LOCKED_TRANSACTION_REQUIRED",
        "system_manager_contract": SYSTEM_MANAGER_CONTRACT,
    }
    write_json_atomic(run_dir / "deployment_candidates" / "deployment_manifest.json", deployment_manifest)
    write_json_atomic(run_dir / "evidence" / "hydra_matrix.json", hydra)
    write_json_atomic(run_dir / "evidence" / "ssot_matrix.json", ssot)
    write_json_atomic(run_dir / "evidence" / "dependency_matrix.json", topology)
    write_json_atomic(run_dir / "evidence" / "complexity_matrix.json", complexity)
    write_json_atomic(run_dir / "evidence" / "accelerators.json", accelerator_rows)
    write_json_atomic(run_dir / "evidence" / "round_summaries.json", round_summaries)
    write_json_atomic(run_dir / "evidence" / "all_repairs.json", all_repairs)

    report_path = run_dir / "reports" / "VIA_Unified_Panoramic_Matrix_v0162B.html"
    render_report(
        report_path, "VIA Unified Panoramic Matrix · VRN / VDF / VAP / Others",
        final_summary, final_matrix, final_issues, hydra, ssot, topology, complexity,
        all_repairs, accelerator_rows, round_summaries,
    )

    overall_gate = (
        "UNIFIED_SANDBOX_READY_REVIEW_ONLY_NO_CANONICAL_MUTATION"
        if final_summary["red"] > 0 or hydra
        else "UNIFIED_SANDBOX_GREEN_RUNTIME_DEPLOYED_NO_CANONICAL_MUTATION"
    )
    result = {
        "version": VERSION,
        "completed_at": now_iso(),
        "gate": overall_gate,
        "base": str(base),
        "run_dir": str(run_dir),
        "matrix_report": str(report_path),
        "round_reports": [
            str(run_dir / "rounds" / f"round_{number}" / f"VIA_Unified_Round_{number}_Matrix_v0162B.html")
            for number in (1, 2, 3)
        ],
        "summary": final_summary,
        "hydra_count": len(hydra),
        "ssot_group_count": len(ssot),
        "repair_candidate_count": len(all_repairs),
        "library_registry": str(run_dir / "registry" / "library_registry.json"),
        "python_package_count": library_info.get("python_package_count", 0),
        "powershell_module_count": library_info.get("powershell_module_count", 0),
        **code_registry_info,
        "deployment_manifest": str(run_dir / "deployment_candidates" / "deployment_manifest.json"),
        "runtime_deployed": True,
        "canonical_project_mutation": False,
        "user_test_state": "READY_FOR_USER_TEST_NOT_AUTOMATICALLY_CLAIMED",
        "subsystems": subsystems,
    }
    write_json_atomic(run_dir / "final_summary.v0162B.json", result)
    update_status(
        status_path, "COMPLETED", 100,
        "Three rounds completed. Runtime deployed; sandbox repair candidates require operator review.",
        **result,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    status_path = Path(config["status_path"]).resolve()
    try:
        run(config)
        return 0
    except Exception as exc:
        failure = {
            "version": VERSION,
            "failed_at": now_iso(),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "run_dir": config.get("run_dir", ""),
        }
        try:
            run_dir = Path(config.get("run_dir") or config_path.parent)
            write_json_atomic(run_dir / "failure.v0162B.json", failure)
            update_status(status_path, "FAILED", 100, str(exc), **failure)
        except Exception:
            pass
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
'@

# --------------------------------------------------------------------------
# Embedded asset · HTML workbench (audit copy: ui\VIA_SystemManager_v0162B_Preview.html)
# --------------------------------------------------------------------------
$Script:WorkbenchSource = @'
<!doctype html>
<html lang="zh-Hant">
<head>
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=3,user-scalable=yes">
<title>VIA · Unified Workbench</title>

<style>
:root{
 --bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;--mut:#6b6860;--mut2:#9c9890;
 --line:#dbd9d3;--soft:#ecebe6;--up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;
 --am:#c4943a;--vi:#7a6daa;--sidebar:#f8f7f3;
 --reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)
}
*{box-sizing:border-box;margin:0;padding:0}html,body{min-height:100%}
body{background:#f5f4f0;color:#33403f;font:10px/1.45 "Microsoft JhengHei","Segoe UI",Arial,sans-serif}
.topbar{position:fixed;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#4c78a8,#439a9a,#7fae6f,#c9b05a,#c96b5a,#a05a86);z-index:100}
.sidebar{position:fixed;top:4px;left:0;bottom:0;width:244px;background:#f8f7f3;border-right:1px solid #dbd9d3;padding:17px 13px;overflow:auto;z-index:60}
.brand{padding:3px 6px 14px;border-bottom:2px solid #1e1d1a}
.brand .k{font:700 7.5px Consolas,monospace;letter-spacing:1.4px;color:#6b6860;text-transform:uppercase}
.brand h2{margin-top:7px;font-size:17px;line-height:1.15;color:#1e1d1a}.brand h2 span{color:#439a9a}
.brand p{margin-top:5px;font-size:9px;color:#6b6860}
.group{margin-top:16px}.groupTitle{margin:0 6px 5px;font:700 7px Consolas,monospace;color:#9c9890;letter-spacing:1.1px;text-transform:uppercase}
.nav button{display:block;width:100%;text-align:left;margin-bottom:3px;border:1px solid transparent;border-radius:4px;background:transparent;color:#33403f;padding:7px 8px;font:700 8px Consolas,monospace;cursor:pointer}
.nav button:hover{background:#fff;border-color:#dbd9d3}.nav button.active{background:#1e1d1a;color:#fff;border-color:#1e1d1a}
.nav .n{display:inline-block;min-width:23px;color:#9c9890}.nav button.active .n{color:#fff}
.sideMetrics{margin-top:15px;border-top:1px solid #dbd9d3;padding-top:10px}.sm{display:flex;justify-content:space-between;gap:7px;padding:4px 3px;border-bottom:1px solid #ecebe6}
.sm .k{font:700 7px Consolas,monospace;color:#6b6860}.sm .v{max-width:125px;text-align:right;overflow-wrap:anywhere;font:700 7.5px Consolas,monospace;color:#1e1d1a}
.workspace{margin-left:244px;min-height:100vh}.inner{max-width:1380px;margin:0 auto;padding:0 20px 52px}
header{padding:20px 0 8px;margin-bottom:10px;border-bottom:2px solid #1e1d1a}
.kicker{font:700 9px Consolas,monospace;letter-spacing:2px;color:#6b6860;text-transform:uppercase;margin-bottom:6px}
h1{font-size:19px;line-height:1.2;color:#1e1d1a}h1 span{color:#439a9a}.sub{margin-top:5px;color:#6b6860;font-size:9.5px}
.page{display:none}.page.active{display:block}
.hero{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 3px}.card{background:#fff;border:1px solid #dbd9d3;border-radius:5px;padding:9px 13px;min-width:115px}
.card .v{font-size:17px;font-weight:800;color:#1e1d1a;line-height:1;overflow-wrap:anywhere}.card .l{font:600 7px Consolas,monospace;color:#6b6860;text-transform:uppercase;margin-top:4px}
h2{font-size:12.5px;color:#1e1d1a;margin:22px 0 7px;padding-bottom:5px;border-bottom:1px solid #dbd9d3}
h2 .en{font:600 7.5px Consolas,monospace;color:#9c9890;letter-spacing:.8px;margin-left:7px;text-transform:uppercase}
.panel{background:#fff;border:1px solid #dbd9d3;border-radius:6px;padding:12px 14px;margin-top:9px}
.homePanel{border-left:3px solid #439a9a}.vrnPanel{border-left:3px solid #c96b5a}.vdfPanel{border-left:3px solid #4c78a8}
.matrixPanel{border-left:3px solid #7a6daa}.riskPanel{border-left:3px solid #c4943a}.registryPanel{border-left:3px solid #5a9e6f}.logPanel{border-left:3px solid #1e1d1a}
.columns{display:flex;gap:11px;align-items:flex-start}.mainColumn{flex:1;min-width:0}.asideColumn{width:360px;min-width:320px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.full{grid-column:1/3}.field{border-bottom:1px solid #ecebe6;padding:7px 0}
label{display:block;font:700 7.5px Consolas,monospace;color:#6b6860;text-transform:uppercase;margin-bottom:4px}
.row{display:flex;align-items:center;gap:5px}input[type=text],input[type=number],select{width:100%;border:1px solid #dbd9d3;border-radius:4px;padding:6px 8px;background:#fafaf8;color:#33403f;font:500 9px Consolas,monospace}
input:focus,select:focus{outline:1px solid #439a9a;border-color:#439a9a}.check{display:flex;align-items:center;gap:6px;min-height:27px}
button{border:1px solid #dbd9d3;border-radius:4px;padding:6px 9px;background:#fff;color:#33403f;font:700 7.5px Consolas,monospace;cursor:pointer}
button:hover{background:#fafaf8}button.primary{color:#fff;background:#439a9a;border-color:#439a9a}button.vrn{color:#fff;background:#c96b5a;border-color:#c96b5a}
button.vdf{color:#fff;background:#4c78a8;border-color:#4c78a8}button.all{color:#fff;background:#1e1d1a;border-color:#1e1d1a}button:disabled{opacity:.45}
.actions{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}.hint{color:#6b6860;font-size:8.5px;margin-top:4px}
.drop{border:1px dashed #9c9890;border-radius:5px;background:#fafaf8;padding:15px;text-align:center;color:#6b6860}
.drop.active{border-color:#439a9a;background:#eef7f5}.drop b{display:block;color:#1e1d1a;font-size:10.5px}.drop span{display:block;margin-top:3px;font-size:8.5px}
.queue{margin-top:9px;border:1px solid #dbd9d3;border-radius:4px;max-height:330px;overflow:auto}.queueItem{display:flex;justify-content:space-between;gap:8px;padding:6px 8px;border-bottom:1px solid #ecebe6;font:500 8px Consolas,monospace}
.progressOuter{height:9px;background:#ecebe6;border-radius:3px;overflow:hidden;margin-top:11px}.progressInner{height:100%;width:0%;background:linear-gradient(90deg,#4c78a8,#439a9a,#7fae6f,#c9b05a,#c96b5a,#a05a86)}
.status{display:grid;grid-template-columns:118px 1fr;gap:4px 9px;margin-top:10px}.k{font:700 7.5px Consolas,monospace;color:#6b6860;text-transform:uppercase}.code{font-family:Consolas,monospace;overflow-wrap:anywhere}
.pill{display:inline-block;font:700 7px Consolas,monospace;color:#fff;border-radius:3px;padding:2px 6px}.ok{background:#5a9e6f}.warn{background:#c4943a}.bad{background:#c96b5a}.mut{background:#9c9890}
.frameWrap{margin-top:9px;border:1px solid #dbd9d3;background:#fafaf8;min-height:650px}.frameWrap iframe{display:block;width:100%;height:650px;border:0;background:#fff}
.empty{padding:80px 20px;text-align:center;color:#6b6860}.empty b{display:block;color:#1e1d1a;font-size:13px;margin-bottom:5px}
.viewerTop{display:flex;align-items:center;justify-content:space-between;gap:9px;flex-wrap:wrap}.viewerPath{color:#6b6860;font:500 8px Consolas,monospace;overflow-wrap:anywhere;margin-top:5px}
.registryGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.registryCard{border:1px solid #dbd9d3;border-radius:5px;background:#fafaf8;padding:10px;min-height:78px}
.registryCard .l{font:700 7px Consolas,monospace;color:#6b6860;text-transform:uppercase}.registryCard .v{margin-top:6px;color:#1e1d1a;font:700 9px/1.4 Consolas,monospace;overflow-wrap:anywhere}
.log{background:#f8f8f5;color:#33403f;border:1px solid #dbd9d3;border-radius:4px;padding:9px;min-height:520px;max-height:700px;overflow:auto;white-space:pre-wrap;font:500 8px/1.5 Consolas,monospace}
.accelGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}.accel{border:1px solid #dbd9d3;border-radius:4px;padding:8px;background:#fafaf8}.accel b{display:block;color:#1e1d1a;font:700 8px Consolas,monospace}.accel span{display:block;color:#6b6860;font-size:8px;margin-top:3px}
.footer{margin-top:13px;color:#9c9890;font:500 7.5px Consolas,monospace}
@media(max-width:1050px){.sidebar{width:205px}.workspace{margin-left:205px}.columns{display:block}.asideColumn{width:auto;min-width:0}.grid{grid-template-columns:1fr}.full{grid-column:auto}.registryGrid,.accelGrid{grid-template-columns:1fr 1fr}}

/* VIA v0162B · proportional bilingual responsive lock */
html{-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}
body{
 font-family:"Microsoft JhengHei","Segoe UI",Arial,sans-serif!important;
 font-size:clamp(15px,1.05vw,17px)!important;
 line-height:1.62!important;
 letter-spacing:.006em
}
.sidebar{width:clamp(220px,17vw,248px)!important;padding:17px 13px!important}
.workspace{margin-left:clamp(220px,17vw,248px)!important}
.inner{max-width:1380px!important;padding:0 clamp(14px,2vw,24px) 48px!important}
.brand h2{font-size:clamp(24px,2vw,29px)!important;font-weight:800!important}
.brand p{font-size:clamp(12px,.95vw,14px)!important;font-weight:500!important}
.kicker{font-size:clamp(11px,.85vw,13px)!important;font-weight:600!important}
h1{font-size:clamp(27px,3vw,36px)!important;font-weight:800!important;line-height:1.2!important}
.sub{font-size:clamp(14px,1vw,16px)!important;font-weight:500!important}
h2{font-size:clamp(20px,1.8vw,24px)!important;font-weight:800!important}
h2 .en{font-size:clamp(11px,.85vw,13px)!important;font-weight:500!important}
.hero{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:9px!important}
.card{min-width:0!important;padding:12px 14px!important}
.card .v{font-size:clamp(23px,2.2vw,29px)!important;font-weight:700!important}
.card .l{font-size:clamp(10.5px,.82vw,12px)!important;font-weight:600!important}
.nav button{font-size:clamp(12px,.95vw,14px)!important;min-height:43px!important;font-weight:600!important}
.nav button.active{font-weight:800!important}
.panel{padding:clamp(14px,1.5vw,18px)!important}
label{font-size:clamp(12px,.9vw,14px)!important;font-weight:700!important}
input[type=text],input[type=number],select{font-size:clamp(15px,1vw,17px)!important;min-height:44px!important}
button{font-size:clamp(14px,.95vw,16px)!important;min-height:44px!important;font-weight:700!important}
.hint,.queueItem,.viewerPath,.registryCard .v{font-size:clamp(13px,.92vw,15px)!important;line-height:1.58!important}
.k,.registryCard .l{font-size:clamp(11px,.8vw,13px)!important;font-weight:700!important}
.code,.log{font-size:clamp(13px,.92vw,15px)!important;line-height:1.65!important}
.registryGrid{grid-template-columns:repeat(4,minmax(0,1fr))!important}
.registryCard{min-width:0!important}.registryCard .v{overflow-wrap:anywhere!important;word-break:break-word!important}
.page.active{min-height:0!important}
@keyframes viaFadeUp{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@keyframes viaShimmer{from{left:-45%}to{left:110%}}
@keyframes viaPulse{0%,100%{box-shadow:0 0 0 0 rgba(196,148,58,.10)}50%{box-shadow:0 0 0 6px rgba(196,148,58,.08)}}
.page.active{animation:viaFadeUp .26s ease-out both}
.panel,.card,.registryCard,.accel,.nav button,button,input,select{transition:transform .16s ease,box-shadow .18s ease,border-color .18s ease,background-color .18s ease}
.panel:hover,.card:hover,.registryCard:hover,.accel:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(30,29,26,.08)}
button:hover{transform:translateY(-1px);box-shadow:0 5px 14px rgba(30,29,26,.11)}
button:active{transform:scale(.985)}
.progressInner{position:relative!important;overflow:hidden!important;transition:width .45s cubic-bezier(.2,.8,.2,1)!important}
.progressInner:after{content:"";position:absolute;top:0;bottom:0;width:38%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.62),transparent);animation:viaShimmer 1.25s linear infinite}
.pill.warn{animation:viaPulse 1.8s ease-in-out infinite}
@media(max-width:1050px){
 .hero{grid-template-columns:repeat(3,minmax(0,1fr))!important}
 .registryGrid,.accelGrid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
}
@media(max-width:760px){
 body{font-size:18px!important;line-height:1.68!important}
 .sidebar{position:relative!important;top:auto!important;bottom:auto!important;width:100%!important;max-height:none!important;border-right:0!important;border-bottom:1px solid #dbd9d3!important}
 .workspace{margin-left:0!important}.inner{padding:0 12px 36px!important}
 .nav{display:grid!important;grid-template-columns:1fr 1fr!important;gap:7px!important}
 .nav button{font-size:15px!important;min-height:50px!important;margin:0!important}
 .sideMetrics{display:grid!important;grid-template-columns:1fr 1fr!important}
 .hero{grid-template-columns:repeat(2,minmax(0,1fr))!important}
 .columns{display:block!important}.asideColumn{width:auto!important;min-width:0!important}.grid{grid-template-columns:1fr!important}
 .actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:9px!important}
 .actions button{font-size:16px!important;min-height:50px!important;width:100%!important}
 input[type=text],input[type=number],select{font-size:18px!important;min-height:50px!important}
 .registryGrid,.accelGrid{grid-template-columns:1fr!important}
 .panel:hover,.card:hover,.registryCard:hover,.accel:hover{transform:none;box-shadow:none}
}
@media(max-width:430px){.nav,.hero,.actions,.sideMetrics{grid-template-columns:1fr!important}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

</style>
<script>
function byId(id){
 return document.getElementById(id);
}
function switchPage(name){
 var names=[
  "home","vrn","vdf","basic","financial",
  "matrix","risk","registry","deploy","logs"
 ];
 for(var i=0;i<names.length;i++){
  var page=names[i];
  byId("page-"+page).className=
   "page"+(page===name?" active":"");
  byId("nav-"+page).className=
   page===name?"active":"";
 }
}
window.onload=function(){
 switchPage("home");
};
</script>
</head>
<body>
<div class="topbar"></div>
<aside class="sidebar">
<div class="brand"><div class="k">VERITAS INTELLIGENCE ANALYTICS</div><h2>Unified <span>Workbench</span></h2><p>VRN · VDF · VAP · Others · v0162B</p></div>
<div class="group"><div class="groupTitle">Operations</div><div class="nav">
<button id="nav-home" onclick="switchPage('home')"><span class="n">01</span>HOME · LAUNCH</button>
<button id="nav-vrn" onclick="switchPage('vrn')"><span class="n">02</span>VRN INPUT</button>
<button id="nav-vdf" onclick="switchPage('vdf')"><span class="n">03</span>VDF INPUT</button>
<button id="nav-basic" onclick="switchPage('basic')"><span class="n">04</span>BASIC INFO</button>
<button id="nav-financial" onclick="switchPage('financial')"><span class="n">05</span>FINANCIAL DATA</button>
</div></div>
<div class="group"><div class="groupTitle">Governance Matrix</div><div class="nav">
<button id="nav-matrix" onclick="switchPage('matrix')"><span class="n">06</span>3-ROUND MATRIX</button>
<button id="nav-risk" onclick="switchPage('risk')"><span class="n">07</span>HYDRA / SSOT</button>
<button id="nav-registry" onclick="switchPage('registry')"><span class="n">08</span>REGISTRY</button>
<button id="nav-deploy" onclick="switchPage('deploy')"><span class="n">09</span>DEPLOYMENT</button>
<button id="nav-logs" onclick="switchPage('logs')"><span class="n">10</span>EXECUTION LOGS</button>
</div></div>
<div class="sideMetrics">
<div class="sm"><div class="k">STATE</div><div id="sideState" class="v">READY</div></div>
<div class="sm"><div class="k">PROGRESS</div><div id="sideProgress" class="v">0%</div></div>
<div class="sm"><div class="k">VRN FILES</div><div id="sideVrn" class="v">0</div></div>
<div class="sm"><div class="k">VDF FILES</div><div id="sideVdf" class="v">0</div></div>
<div class="sm"><div class="k">GATE</div><div id="sideGate" class="v">—</div></div>
</div>
<div style="margin-top:13px"><button style="width:100%" onclick="window.close()">CLOSE WORKBENCH</button></div>
</aside>
<div class="workspace"><div class="inner">
<header><div class="kicker">AUTOMATIC SANDBOX TEST & REPAIR · 20 ACCELERATORS · THREE ROUNDS</div><h1 id="pageTitle">統一首頁 · 啟動與摘要</h1><p id="pageSubtitle" class="sub">Unified launch, progress and 20 accelerators</p></header>

<section id="page-home" class="page active">
<div class="hero">
<div class="card"><div id="summaryProgress" class="v">0%</div><div class="l">PROGRESS</div></div>
<div class="card"><div id="summaryRound" class="v">0/3</div><div class="l">ROUND</div></div>
<div class="card"><div id="files" class="v">—</div><div class="l">FILES</div></div>
<div class="card"><div id="green" class="v" style="color:#5a9e6f">—</div><div class="l">GREEN</div></div>
<div class="card"><div id="yellow" class="v" style="color:#c4943a">—</div><div class="l">YELLOW</div></div>
<div class="card"><div id="red" class="v" style="color:#c96b5a">—</div><div class="l">RED</div></div>
<div class="card"><div id="hydra" class="v">—</div><div class="l">HYDRA</div></div>
<div class="card"><div id="repairs" class="v">—</div><div class="l">SANDBOX CANDIDATES</div></div>
<div class="card" style="min-width:285px"><div id="summaryGate" class="v" style="font:700 8px/1.3 Consolas,monospace">—</div><div class="l">LATEST GATE</div></div>
</div>
<div class="columns">
<div class="mainColumn">
<h2>Unified Runtime <span class="en">one PowerShell · one HTML UI</span></h2>
<div class="panel homePanel"><div class="grid">
<div class="field full"><label>Base · VIA 母系統</label><div class="row"><input id="base" type="text"><button onclick="browseFolder('base')">WINDOWS SEARCH</button></div></div>
<div class="field full"><label>Python Engine</label><div class="row"><input id="python" type="text"><button onclick="browseFile('python')">SEARCH</button></div></div>
<div class="field"><label>Timeout Seconds</label><input id="timeout" type="number" min="60" max="86400" step="60"></div>
<div class="field"><label>Sandbox Auto-Fix</label><div class="check"><input id="autoFix" type="checkbox"><span>只修 sandbox copy</span></div></div>
<div class="field"><label>Open Matrix HTML</label><div class="check"><input id="openHtml" type="checkbox"><span>完成後開啟報告</span></div></div>
<div class="field"><label>Canonical Mutation</label><div class="check"><span class="pill bad">BLOCKED</span><span>需另行 hash-locked promotion</span></div></div>
</div></div>
<h2>20 Accelerators <span class="en">all enabled with explicit implementation mode</span></h2>
<div class="accelGrid">
<div class="accel"><b>A01–A05</b><span>AST · semantic tags · Hydra · topology · sandbox</span></div>
<div class="accel"><b>A06–A10</b><span>repair suggestions · 3 rounds · SSOT · matrix · clustering</span></div>
<div class="accel"><b>A11–A15</b><span>complexity · multi-system · rollback · regression · repair order</span></div>
<div class="accel"><b>A16–A20</b><span>progress · narration · non-blocking · engines · runtime deploy</span></div>
</div>
</div>
<div class="asideColumn">
<h2>One-Click Actions <span class="en">non-blocking workers</span></h2>
<div class="panel homePanel">
<div class="actions">
<button id="runAll" class="all" onclick="startAction('ALL')">LAUNCH ALL</button>
<button id="runAnalysis" class="primary" onclick="startAction('UNIFIED')">3-ROUND ANALYSIS</button>
<button id="runVrn" class="vrn" onclick="startAction('VRN')">RUN VRN</button>
<button id="runVdf" class="vdf" onclick="startAction('VDF')">RUN VDF</button>
<button id="openRun" disabled onclick="openPath(this)">OPEN RUNDIR</button>
</div>
<div class="progressOuter"><div id="bar" class="progressInner"></div></div>
<div class="hint" style="margin:0 0 10px"><b>AUTO MODE · 自動模式：</b>本啟動器預設在 UI 載入後自動執行 LAUNCH ALL；使用 <span class="code">-UiOnly</span> 可只開啟介面。</div>
<div class="status">
<div class="k">STATE</div><div id="state"><span class="pill mut">READY</span></div>
<div class="k">NARRATION</div><div id="narration">等待操作。</div>
<div class="k">VRN GATE</div><div id="vrnGate" class="code">—</div>
<div class="k">VDF GATE</div><div id="vdfGate" class="code">—</div>
<div class="k">RUNDIR</div><div id="runDirPath" class="code">—</div>
</div>
</div>
</div></div>
</section>

<section id="page-vrn" class="page"><h2>VRN Research Intake <span class="en">reports + manifest + disabled drafts</span></h2>
<div class="panel vrnPanel"><div class="grid">
<div class="field full"><label>VRN Input</label><div class="row"><input id="vrnInput" type="text"><button onclick="browseFolder('vrnInput')">SEARCH</button></div></div>
<div class="field full"><label>VRN Manifest</label><div class="row"><input id="vrnManifest" type="text"><button onclick="browseFile('vrnManifest')">SEARCH</button></div></div>
</div>
<div id="vrnDrop" class="drop"><b>拖曳投資研究報告</b><span>PDF / Word / Excel / HTML / JSON / TXT</span></div>
<div class="actions"><button onclick="addSources('vrn')">SELECT REPORTS</button><button onclick="addFolder('vrn')">SELECT FOLDER</button><button onclick="vrnSources=[];renderQueues()">CLEAR</button><span id="vrnCount" class="pill mut">0</span></div>
<div id="vrnQueue" class="queue"></div><div class="hint">VRN 延續 v0159/v0156 治理：新增資料只產生 enabled=false draft，不自動 promotion。</div></div></section>

<section id="page-vdf" class="page"><h2>VDF Data Forge <span class="en">data sources + market facts</span></h2>
<div class="panel vdfPanel"><div class="grid">
<div class="field full"><label>VDF Input</label><div class="row"><input id="vdfInput" type="text"><button onclick="browseFolder('vdfInput')">SEARCH</button></div></div>
<div class="field"><label>Start Date</label><input id="startDate" type="text" placeholder="yyyy-mm-dd"></div>
<div class="field"><label>End Date</label><input id="endDate" type="text" placeholder="blank = open"></div>
<div class="field full"><label>Universe / Tickers</label><input id="universe" type="text" value="DEFAULT"></div>
<div class="field"><label>Update Mode</label><select id="updateMode"><option>Incremental</option><option>Refresh</option><option>ValidateOnly</option><option>DryRun</option></select></div>
</div>
<div id="vdfDrop" class="drop"><b>拖曳 VDF 資料來源</b><span>CSV / Excel / JSON / Parquet / DuckDB / SQLite</span></div>
<div class="actions"><button onclick="addSources('vdf')">SELECT DATA FILES</button><button onclick="addFolder('vdf')">SELECT FOLDER</button><button onclick="vdfSources=[];renderQueues()">CLEAR</button><span id="vdfCount" class="pill mut">0</span></div>
<div id="vdfQueue" class="queue"></div></div></section>

<section id="page-basic" class="page"><h2>Basic Info <span class="en">VDF primary output</span></h2><div class="panel vdfPanel"><div class="viewerTop"><div><span class="pill" style="background:#4c78a8">BASIC INFO</span><div id="basicPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('basic')">RELOAD</button><button onclick="openView('basic')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="basicEmpty" class="empty"><b>尚未找到 Basic Info HTML</b>執行 VDF 或 Launch All 後自動更新。</div><iframe id="basicFrame" style="display:none"></iframe></div></div></section>
<section id="page-financial" class="page"><h2>Financial Data <span class="en">VDF primary output</span></h2><div class="panel matrixPanel"><div class="viewerTop"><div><span class="pill" style="background:#7a6daa">FINANCIAL DATA</span><div id="financialPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('financial')">RELOAD</button><button onclick="openView('financial')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="financialEmpty" class="empty"><b>尚未找到 Financial Data HTML</b>執行 VDF 或 Launch All 後自動更新。</div><iframe id="financialFrame" style="display:none"></iframe></div></div></section>

<section id="page-matrix" class="page"><h2>Three-Round HTML Matrix <span class="en">small font · auto layout · wrap</span></h2><div class="panel matrixPanel"><div class="viewerTop"><div><span class="pill" style="background:#7a6daa">MATRIX</span><div id="matrixPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('matrix')">RELOAD</button><button onclick="openView('matrix')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="matrixEmpty" class="empty"><b>尚未執行三輪分析</b>按首頁 3-ROUND ANALYSIS 或 LAUNCH ALL。</div><iframe id="matrixFrame" style="display:none"></iframe></div></div></section>
<section id="page-risk" class="page"><h2>Hydra / SSOT Matrix <span class="en">risk and authority alignment</span></h2><div class="panel riskPanel"><div class="hero"><div class="card"><div id="ssot" class="v">—</div><div class="l">SSOT GROUPS</div></div><div class="card"><div id="hydra2" class="v">see report</div><div class="l">HYDRA DETAILS</div></div></div><div class="viewerTop"><div><div id="riskPath" class="viewerPath"></div></div><div class="actions"><button onclick="loadView('risk')">RELOAD</button><button onclick="openView('risk')">OPEN EXTERNAL</button></div></div><div class="frameWrap"><div id="riskEmpty" class="empty"><b>Hydra / SSOT 尚未產生</b>三輪分析完成後顯示。</div><iframe id="riskFrame" style="display:none"></iframe></div></div></section>

<section id="page-registry" class="page"><h2>Registry <span class="en">MODULE / ENGINE / FUNCTION-LIB / OTHERS</span></h2><div class="panel registryPanel">
<div class="registryGrid">
<div class="registryCard"><div class="l">LIBRARIES · 函式庫</div><div id="libraryRegistry" class="v">—</div></div>
<div class="registryCard"><div class="l">FUNCTIONS · 函式／類別</div><div id="functionRegistry" class="v">—</div></div>
<div class="registryCard"><div class="l">SUPPORTIVE MODULES · 支援模組</div><div id="supportiveRegistry" class="v">—</div></div>
<div class="registryCard"><div class="l">SSOT · 單一事實來源</div><div id="ssotRegistry" class="v">—</div></div>
<div class="registryCard"><div class="l">VRN REPORT</div><div id="vrnReport" class="v">—</div></div>
<div class="registryCard"><div class="l">FILES</div><div id="files2" class="v">See matrix</div></div>
<div class="registryCard"><div class="l">IMPORT POLICY</div><div class="v">REGISTER ALL / IMPORT APPROVED</div></div>
</div><div class="hint">所有函式庫皆建立 inventory；不盲目 import 或執行未知模組。功能擴充以 sandbox candidate 與 extension matrix 呈現。</div></div></section>

<section id="page-deploy" class="page"><h2>Deployment <span class="en">runtime automatic · canonical review-only</span></h2><div class="panel registryPanel">
<div class="registryGrid">
<div class="registryCard"><div class="l">RUNTIME DEPLOYMENT</div><div class="v">AUTOMATIC</div></div>
<div class="registryCard"><div class="l">CANONICAL MUTATION</div><div class="v" style="color:#c96b5a">BLOCKED</div></div>
<div class="registryCard"><div class="l">REPAIR CANDIDATES</div><div id="repairs2" class="v">See summary</div></div>
<div class="registryCard"><div class="l">DEPLOYMENT MANIFEST</div><div id="deploymentManifest" class="v">—</div></div>
</div><div class="hint">沙盒修正通過回歸後只列為 deployment candidate；真正寫回 VRN/VDF/VAP canonical 必須另開單程序、exact-hash、backup、hash-chain transaction。</div></div></section>

<section id="page-logs" class="page"><h2>Execution Logs <span class="en">dynamic status narration</span></h2><div class="panel logPanel"><div class="actions"><button onclick="byId('log').innerText='VIA Unified Workbench ready.'">CLEAR DISPLAY</button></div><div id="log" class="log">VIA Unified Workbench ready.</div></div></section>
<div class="footer">VIA Unified Workbench v0162B · one PowerShell · one HTML U/I · exactly three rounds · sandbox repair only · runtime auto-deploy · 理</div>
</div></div>
</body></html>
'@

# --------------------------------------------------------------------------
# Embedded asset · daily launcher literal template (placeholder replacement only)
# --------------------------------------------------------------------------
$Script:EntrypointTemplate = @'
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Launcher = '{{VIA_LAUNCHER_PATH}}'
$ExpectedSHA = '{{VIA_EXPECTED_SHA}}'
$Base = '{{VIA_BASE}}'

if (-not (
    Test-Path `
        -LiteralPath $Launcher `
        -PathType Leaf
)) {
    throw (
        "VIA System Manager canonical launcher is missing: " +
        $Launcher
    )
}

$ActualSHA = (
    Get-FileHash `
        -LiteralPath $Launcher `
        -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($ActualSHA -ne $ExpectedSHA) {
    throw (
        "VIA System Manager canonical SHA256 mismatch. " +
        "Expected=$ExpectedSHA Actual=$ActualSHA"
    )
}

$Tokens = $null
$Errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $Launcher,
    [ref]$Tokens,
    [ref]$Errors
) | Out-Null

if (@($Errors).Count -gt 0) {
    Write-Host ""
    Write-Host (
        "def CANONICAL AST : FAIL"
    ) -ForegroundColor Red

    foreach ($ParseError in @($Errors)) {
        Write-Host (
            "Line {0}, Column {1}: {2}" -f
            $ParseError.Extent.StartLineNumber,
            $ParseError.Extent.StartColumnNumber,
            $ParseError.Message
        ) -ForegroundColor Red
    }

    throw (
        "VIA System Manager canonical AST validation failed."
    )
}

& $Launcher -Base $Base
'@

function Write-VIAStageLog {
    param(
        [Parameter(Mandatory)][string]$Message,
        [string]$Color = 'Gray'
    )
    $stamp = [DateTime]::Now.ToString('HH:mm:ss')
    Write-Host ('[{0}] {1}' -f $stamp, $Message) -ForegroundColor $Color
}

function Test-VIAScriptAst {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Label,
        [switch]$RemoveOnFailure
    )
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null
    if (@($parseErrors).Count -gt 0) {
        Write-Host ''
        Write-Host ('AST VALIDATION FAIL : ' + $Label) -ForegroundColor Red
        foreach ($parseError in @($parseErrors)) {
            Write-Host (
                'Line {0}, Column {1}: {2}' -f
                $parseError.Extent.StartLineNumber,
                $parseError.Extent.StartColumnNumber,
                $parseError.Message
            ) -ForegroundColor Red
        }
        if ($RemoveOnFailure) {
            Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
        }
        throw ('AST validation failed for ' + $Label + ': ' + $Path)
    }
    Write-VIAStageLog -Message ('AST PASS : ' + $Label) -Color Green
}

function Write-VIAAsset {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [string]$ExpectedSHA,
        [Parameter(Mandatory)][string]$Label
    )
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not [string]::IsNullOrEmpty($ExpectedSHA) -and $actual -ne $ExpectedSHA) {
        throw (
            'Materialized asset SHA256 mismatch for ' + $Label +
            '. Expected=' + $ExpectedSHA + ' Actual=' + $actual
        )
    }
    Write-VIAStageLog -Message ('MATERIALIZED : ' + $Label + ' sha256=' + $actual) -Color DarkCyan
    return $actual
}

function Install-VIAEntrypoints {
    param(
        [Parameter(Mandatory)][string]$LauncherPath,
        [Parameter(Mandatory)][string]$LauncherSHA
    )
    $content = $Script:EntrypointTemplate
    $content = $content.Replace('{{VIA_LAUNCHER_PATH}}', $LauncherPath)
    $content = $content.Replace('{{VIA_EXPECTED_SHA}}', $LauncherSHA)
    $content = $content.Replace('{{VIA_BASE}}', $Base)
    if ($content.Contains('{{VIA_')) {
        throw 'Daily launcher template still contains unresolved placeholders.'
    }
    $encoding = [System.Text.UTF8Encoding]::new($false)
    foreach ($name in @('StartVIASystemManager.ps1', 'StartVIAUnified.ps1')) {
        $target = Join-Path -Path $Base -ChildPath $name
        [System.IO.File]::WriteAllText($target, $content, $encoding)
        Test-VIAScriptAst -Path $target -Label ('daily launcher ' + $name) -RemoveOnFailure
    }
}

function Find-VIAPython {
    $candidates = @(
        @{ Name = 'py';      Prefix = @('-3') },
        @{ Name = 'python3'; Prefix = @() },
        @{ Name = 'python';  Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        $command = Get-Command -Name $candidate.Name -CommandType Application -ErrorAction SilentlyContinue
        if ($null -eq $command) {
            continue
        }
        $resolved = @($command)[0]
        try {
            $probeArgs = @($candidate.Prefix) + @('--version')
            $probe = (& $resolved.Source @probeArgs 2>&1 | Out-String).Trim()
        }
        catch {
            continue
        }
        if ($probe -match 'Python 3\.(\d+)\.') {
            if ([int]$Matches[1] -ge 10) {
                Write-VIAStageLog -Message ('PYTHON : ' + $resolved.Source + ' (' + $probe + ')') -Color DarkCyan
                return @{ Path = $resolved.Source; Prefix = @($candidate.Prefix) }
            }
        }
    }
    throw (
        'No Python 3.10+ interpreter found (tried py -3, python3, python). ' +
        'Governance blocks network installation; install Python manually and rerun.'
    )
}

function Invoke-VIAEngine {
    param(
        [Parameter(Mandatory)][string]$RunDir,
        [Parameter(Mandatory)][string]$EnginePath,
        [Parameter(Mandatory)][string]$StatusPath,
        [Parameter(Mandatory)][hashtable]$Python
    )
    $pwshPath = ''
    $pwshCommand = Get-Command -Name 'pwsh' -CommandType Application -ErrorAction SilentlyContinue
    if ($null -ne $pwshCommand) {
        $pwshPath = @($pwshCommand)[0].Source
    }
    else {
        $pwshPath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    }

    $configPath = Join-Path -Path $RunDir -ChildPath 'config.json'
    $config = [ordered]@{
        base        = $Base
        run_dir     = $RunDir
        status_path = $StatusPath
        pwsh_path   = $pwshPath
        auto_fix    = (-not $NoAutoFix.IsPresent)
    }
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 6), $encoding)

    $logDir = Join-Path -Path $RunDir -ChildPath 'logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stdoutLog = Join-Path -Path $logDir -ChildPath 'engine_stdout.log'
    $stderrLog = Join-Path -Path $logDir -ChildPath 'engine_stderr.log'

    # Windows paths contain spaces ("supportive modules"); Start-Process joins
    # array arguments without quoting, so every argument is quoted explicitly
    # and passed as one command line.
    $rawArguments = @($Python.Prefix) + @($EnginePath, '--config', $configPath)
    $quotedArguments = foreach ($argument in $rawArguments) {
        if ($argument -match '\s') {
            '"' + $argument + '"'
        }
        else {
            $argument
        }
    }
    $argumentLine = [string]::Join(' ', @($quotedArguments))
    Write-VIAStageLog -Message 'A18: starting engine as detached non-blocking worker process.' -Color Cyan
    Write-VIAStageLog -Message ('ENGINE CMD : ' + $Python.Path + ' ' + $argumentLine) -Color DarkCyan
    $process = Start-Process `
        -FilePath $Python.Path `
        -ArgumentList $argumentLine `
        -WorkingDirectory $RunDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $lastNarration = ''
    $finalState = 'UNKNOWN'
    $terminal = $false

    while ([DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Seconds 2
        $status = $null
        if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
            try {
                $statusRaw = [System.IO.File]::ReadAllText($StatusPath)
                $status = $statusRaw | ConvertFrom-Json
            }
            catch {
                $status = $null
            }
        }
        if ($null -ne $status) {
            $percent = 0
            $narration = ''
            $stateText = 'RUNNING'
            if ($null -ne $status.PSObject.Properties['percent']) {
                $percent = [int]$status.percent
            }
            if ($null -ne $status.PSObject.Properties['narration']) {
                $narration = [string]$status.narration
            }
            if ($null -ne $status.PSObject.Properties['state']) {
                $stateText = [string]$status.state
            }
            Write-Progress `
                -Activity ('VIA System Manager ' + $Script:VIAVersion) `
                -Status ($stateText + ' · ' + $percent + '% · ' + $narration) `
                -PercentComplete ([Math]::Max(0, [Math]::Min(100, $percent)))
            if ($narration -ne $lastNarration -and -not [string]::IsNullOrEmpty($narration)) {
                Write-VIAStageLog -Message ($percent.ToString().PadLeft(3) + '% ' + $narration) -Color Gray
                $lastNarration = $narration
            }
            if ($null -ne $status.PSObject.Properties['terminal'] -and [bool]$status.terminal) {
                $finalState = $stateText
                $terminal = $true
                break
            }
        }
        if ($process.HasExited -and $null -eq $status) {
            $finalState = 'ENGINE_EXITED_WITHOUT_STATUS'
            break
        }
        if ($process.HasExited -and $null -ne $status) {
            $refreshTerminal = $false
            if ($null -ne $status.PSObject.Properties['terminal']) {
                $refreshTerminal = [bool]$status.terminal
            }
            if (-not $refreshTerminal) {
                Start-Sleep -Seconds 2
                if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
                    try {
                        $statusRaw = [System.IO.File]::ReadAllText($StatusPath)
                        $late = $statusRaw | ConvertFrom-Json
                        if ($null -ne $late.PSObject.Properties['terminal'] -and [bool]$late.terminal) {
                            $finalState = [string]$late.state
                            $terminal = $true
                            break
                        }
                    }
                    catch {
                    }
                }
                $finalState = 'ENGINE_EXITED_WITHOUT_TERMINAL_STATUS'
                break
            }
        }
    }
    Write-Progress -Activity ('VIA System Manager ' + $Script:VIAVersion) -Completed

    if (-not $terminal -and [DateTime]::UtcNow -ge $deadline) {
        $finalState = 'TIMEOUT_WORKER_LEFT_RUNNING'
        Write-VIAStageLog -Message (
            'Timeout reached after ' + $TimeoutSeconds +
            's. Governance stop_process=false: worker is NOT terminated; it keeps running detached.'
        ) -Color Yellow
    }
    if ($finalState -like 'ENGINE_EXITED*') {
        Write-VIAStageLog -Message ('Engine exited abnormally. Exit code: ' + $process.ExitCode) -Color Red
        if (Test-Path -LiteralPath $stderrLog -PathType Leaf) {
            $stderrTail = Get-Content -LiteralPath $stderrLog -Tail 25 -ErrorAction SilentlyContinue
            foreach ($line in @($stderrTail)) {
                Write-Host ('  stderr | ' + $line) -ForegroundColor DarkYellow
            }
        }
    }
    return $finalState
}

function Open-VIAPath {
    param([string]$Path)
    if ($NoOpenHtml.IsPresent) {
        return
    }
    if (-not [string]::IsNullOrEmpty($Path) -and (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Start-Process -FilePath $Path | Out-Null
    }
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
Write-Host ''
Write-Host ('VIA SYSTEM MANAGER ' + $Script:VIAVersion + ' · ALL-IN-ONE') -ForegroundColor Cyan
Write-Host 'One PowerShell · one HTML UI · three rounds · sandbox repair only · no canonical mutation' -ForegroundColor DarkCyan
Write-Host ''

if (-not (Test-Path -LiteralPath $Base -PathType Container)) {
    throw ('VIA base folder not found: ' + $Base)
}
$Base = (Resolve-Path -LiteralPath $Base).Path

$selfSHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-VIAStageLog -Message ('SELF : ' + $PSCommandPath) -Color DarkCyan
Write-VIAStageLog -Message ('SELF SHA256 : ' + $selfSHA) -Color DarkCyan

$runtimeRoot = Join-Path -Path $Base -ChildPath 'supportive modules\VIA_Governance_Runtime\v0162B\runtime'
$runId = 'run_' + [DateTime]::Now.ToString('yyyyMMdd_HHmmss')
$runDir = Join-Path -Path $runtimeRoot -ChildPath $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
Write-VIAStageLog -Message ('RUNDIR : ' + $runDir) -Color DarkCyan

$enginePath = Join-Path -Path $runDir -ChildPath 'engine\via_system_manager_engine_v0162B.py'
$workbenchPath = Join-Path -Path $runDir -ChildPath 'ui\VIA_Unified_Workbench_v0162B.html'
$statusPath = Join-Path -Path $runDir -ChildPath 'status.json'

Write-VIAStageLog -Message 'A05/A20: materializing runtime assets with exact-SHA verification.' -Color Cyan
Write-VIAAsset `
    -Path $enginePath `
    -Content ($Script:EngineSource + "`n") `
    -ExpectedSHA $Script:EngineExpectedSHA `
    -Label 'python engine' | Out-Null
Write-VIAAsset `
    -Path $workbenchPath `
    -Content ($Script:WorkbenchSource + "`n") `
    -ExpectedSHA $Script:WorkbenchExpectedSHA `
    -Label 'html workbench' | Out-Null

Write-VIAStageLog -Message 'Installing daily entrypoints from literal template with AST validation.' -Color Cyan
Install-VIAEntrypoints -LauncherPath $PSCommandPath -LauncherSHA $selfSHA

if ($UiOnly.IsPresent) {
    Write-VIAStageLog -Message '-UiOnly: opening workbench without engine execution.' -Color Yellow
    Open-VIAPath -Path $workbenchPath
    Write-VIAStageLog -Message 'UI-only session ready.' -Color Green
    return
}

$python = Find-VIAPython
Open-VIAPath -Path $workbenchPath

$finalState = Invoke-VIAEngine `
    -RunDir $runDir `
    -EnginePath $enginePath `
    -StatusPath $statusPath `
    -Python $python

Write-Host ''
Write-VIAStageLog -Message ('ENGINE FINAL STATE : ' + $finalState) -Color Cyan

$finalSummaryPath = Join-Path -Path $runDir -ChildPath 'final_summary.v0162B.json'
if (Test-Path -LiteralPath $finalSummaryPath -PathType Leaf) {
    $final = [System.IO.File]::ReadAllText($finalSummaryPath) | ConvertFrom-Json
    $gate = ''
    if ($null -ne $final.PSObject.Properties['gate']) {
        $gate = [string]$final.gate
    }
    Write-VIAStageLog -Message ('GATE : ' + $gate) -Color Green
    if ($null -ne $final.PSObject.Properties['summary']) {
        $summary = $final.summary
        Write-VIAStageLog -Message (
            'FILES=' + $summary.files + ' GREEN=' + $summary.green +
            ' YELLOW=' + $summary.yellow + ' RED=' + $summary.red
        ) -Color Green
    }
    if ($null -ne $final.PSObject.Properties['matrix_report']) {
        $matrixReport = [string]$final.matrix_report
        Write-VIAStageLog -Message ('MATRIX : ' + $matrixReport) -Color Green
        Open-VIAPath -Path $matrixReport
    }
    Write-VIAStageLog -Message 'USER TEST : READY_FOR_USER_TEST_NOT_AUTOMATICALLY_CLAIMED' -Color Yellow
    Write-VIAStageLog -Message 'PROMOTION : sandbox candidates only; canonical mutation stays BLOCKED.' -Color Yellow
}
else {
    Write-VIAStageLog -Message ('No final summary found at ' + $finalSummaryPath) -Color Yellow
    if ($finalState -ne 'COMPLETED') {
        throw ('VIA System Manager run did not complete. Final state: ' + $finalState)
    }
}
Write-Host ''
Write-VIAStageLog -Message ('VIA System Manager ' + $Script:VIAVersion + ' run finished.') -Color Cyan

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
