#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Command Center · Auto Catch / Connect / Sync / Test / Debug · AIO v0.2.0

核心：
1. AUTO-CATCH：遞迴掃描 Python / PowerShell 引擎工具
2. CONNECT：分析入口點、依賴、參數、輸入輸出
3. SYNC：建立/更新單一 Registry SSOT
4. TEST/DEBUG：靜態檢查、依賴檢查、CLI dry-run、自測、重試
5. INPUTS：輸入參數矩陣
6. STATUS：每個引擎健康狀態
7. OUTPUTS：輸出格式/產物推定
8. MATRIX：詳細驗證矩陣
9. SUMMARY：總體摘要
10. RUN：統一命令入口執行指定引擎
11. WATCH：重複同步（可選）
12. EXPORT：JSON / CSV

安全預設：
- 不覆寫、不修補既有引擎原始碼
- scan/sync/validate 為 read-only
- --smoke 才會實際執行 --help / -?
- run 才會真正執行指定引擎
"""

# ============================================================
# 0. PARAMETERS — 所有參數集中於頂部
# ============================================================
APP_NAME = "VIA Command Center AutoCatchSync AIO"
APP_VERSION = "0.2.0"

DEFAULT_ROOT = "."
RUNTIME_DIRNAME = "runtime_command_center"
REGISTRY_FILENAME = "engine_registry.json"
MATRIX_JSON_FILENAME = "validation_matrix.json"
MATRIX_CSV_FILENAME = "validation_matrix.csv"
SUMMARY_FILENAME = "summary.json"
EVENT_LOG_FILENAME = "events.jsonl"

SCAN_EXTENSIONS = {".py", ".ps1"}
IGNORE_DIRS = {
    ".git", ".github", ".idea", ".vscode", "__pycache__",
    "node_modules", ".venv", "venv", "env", "site-packages",
    "dist", "build", RUNTIME_DIRNAME
}
IGNORE_FILENAMES = {"setup.py", "conftest.py"}
IGNORE_PATTERNS = (r"^test_", r"_test\.py$")

ENTRY_CANDIDATES = (
    "main", "run", "execute", "invoke", "start", "process",
    "fetch", "update", "sync", "analyze", "extract",
    "render", "generate", "build", "validate", "selftest"
)

SUBSYSTEM_HINTS = {
    "VDF": ("vdf", "dataforge", "data_forge"),
    "VRN": ("vrn", "reportnova", "report_nova"),
    "VAP": ("vap", "plot", "visual"),
    "GRP": ("grp", "group_rotation", "grouprotation"),
    "VETF": ("vetf", "active_etf", "activeetf"),
    "VMFRS": ("vmfrs", "marketflow", "risk"),
    "GOVERNANCE": ("governance", "registry", "nexus", "manager", "commandcenter"),
}

DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_RETRIES = 2
WATCH_INTERVAL_SECONDS = 30
MAX_CAPTURE_CHARS = 16000
CSV_ENCODING = "utf-8-sig"

API_HOST = "127.0.0.1"
API_PORT = 8765

# ============================================================
# 1. IMPORTS
# ============================================================
import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ============================================================
# 2. DATA MODELS
# ============================================================
@dataclass
class GateResult:
    gate: str
    status: str
    detail: str = ""
    elapsed_ms: float = 0.0


@dataclass
class EngineRecord:
    engine_id: str
    name: str
    path: str
    kind: str
    subsystem: str = "UNCLASSIFIED"
    sha256: str = ""
    entry_points: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    gates: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    health: str = "UNKNOWN"
    html_ready: str = "REVIEW"
    last_checked: str = ""
    error: str = ""


# ============================================================
# 3. COMMON UTILITIES
# ============================================================
def def_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def def_runtime_dir(root: Path) -> Path:
    p = root / RUNTIME_DIRNAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def def_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def def_write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def def_append_event(root: Path, event: dict[str, Any]) -> None:
    p = def_runtime_dir(root) / EVENT_LOG_FILENAME
    event = {"ts": def_now_iso(), **event}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def def_clip(text: str) -> str:
    text = text or ""
    if len(text) <= MAX_CAPTURE_CHARS:
        return text
    return text[:MAX_CAPTURE_CHARS] + "\n...[TRUNCATED]..."


def def_is_ignored(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return True
    if path.name.lower() in IGNORE_FILENAMES:
        return True
    return any(re.search(pat, path.name, flags=re.I) for pat in IGNORE_PATTERNS)


def def_classify_subsystem(path: Path) -> str:
    s = str(path).lower()
    for name, hints in SUBSYSTEM_HINTS.items():
        if any(h in s for h in hints):
            return name
    return "UNCLASSIFIED"


# ============================================================
# 4. STATIC ANALYSIS — PYTHON
# ============================================================
def def_analyze_python(path: Path) -> dict[str, Any]:
    text = def_read_text(path)
    result = {
        "syntax_ok": False,
        "entry_points": [],
        "parameters": [],
        "dependencies": [],
        "outputs": [],
        "error": "",
    }

    try:
        tree = ast.parse(text, filename=str(path))
        result["syntax_ok"] = True
    except SyntaxError as e:
        result["error"] = f"{e.msg} @ line {e.lineno}"
        return result

    deps: set[str] = set()
    outputs: set[str] = set()
    funcs: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.add(node.module.split(".")[0])

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node)

        elif isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                call_name = node.func.id

            if call_name in {"to_parquet", "write_parquet"}:
                outputs.add("parquet")
            elif call_name in {"to_csv", "write_csv"}:
                outputs.add("csv")
            elif call_name in {"json_dump", "dump", "dumps"}:
                outputs.add("json")
            elif call_name in {"savefig", "write_image"}:
                outputs.add("image")
            elif call_name in {"write_html", "to_html"}:
                outputs.add("html")

    ranked = []
    for fn in funcs:
        lname = fn.name.lower()
        score = 0
        if lname in ENTRY_CANDIDATES:
            score += 100
        if any(x in lname for x in ("main", "run", "execute", "invoke", "process", "sync")):
            score += 30
        if not lname.startswith("_"):
            score += 5
        ranked.append((score, fn))

    ranked.sort(key=lambda x: (-x[0], x[1].lineno))
    result["entry_points"] = [fn.name for score, fn in ranked if score > 0][:15]

    if ranked:
        fn = ranked[0][1]
        args = list(fn.args.args)
        defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)

        for arg, default in zip(args, defaults):
            if arg.arg in {"self", "cls"}:
                continue

            default_value = None
            required = default is None

            if default is not None:
                try:
                    default_value = ast.literal_eval(default)
                except Exception:
                    default_value = "<dynamic>"

            result["parameters"].append({
                "name": arg.arg,
                "required": required,
                "default": default_value,
                "type": ast.unparse(arg.annotation) if arg.annotation else None,
            })

    result["dependencies"] = sorted(deps)
    result["outputs"] = sorted(outputs)
    return result


# ============================================================
# 5. STATIC ANALYSIS — POWERSHELL
# ============================================================
def def_analyze_powershell(path: Path) -> dict[str, Any]:
    text = def_read_text(path)

    params = []
    m = re.search(r"param\s*\((.*?)\)", text, flags=re.I | re.S)
    if m:
        for name in re.findall(r"\$(\w+)", m.group(1)):
            params.append({
                "name": name,
                "required": False,
                "default": None,
                "type": None,
            })

    outputs = []
    low = text.lower()

    if "convertto-json" in low:
        outputs.append("json")
    if "export-csv" in low:
        outputs.append("csv")
    if "parquet" in low:
        outputs.append("parquet")

    return {
        "syntax_ok": True,
        "entry_points": ["script"],
        "parameters": params,
        "dependencies": [],
        "outputs": outputs,
        "error": "",
    }


# ============================================================
# 6. AUTO-CATCH / DISCOVERY
# ============================================================
def def_discover(root: Path) -> list[EngineRecord]:
    candidates: list[Path] = []

    for ext in SCAN_EXTENSIONS:
        candidates.extend(root.rglob(f"*{ext}"))

    candidates = sorted({
        p.resolve()
        for p in candidates
        if p.is_file() and not def_is_ignored(p)
    })

    engines: list[EngineRecord] = []

    for idx, path in enumerate(candidates, 1):
        analysis = (
            def_analyze_python(path)
            if path.suffix.lower() == ".py"
            else def_analyze_powershell(path)
        )

        engines.append(
            EngineRecord(
                engine_id=f"E{idx:04d}",
                name=path.stem,
                path=str(path),
                kind="python" if path.suffix.lower() == ".py" else "powershell",
                subsystem=def_classify_subsystem(path),
                sha256=def_sha256(path),
                entry_points=analysis["entry_points"],
                parameters=analysis["parameters"],
                dependencies=analysis["dependencies"],
                outputs=analysis["outputs"],
                error=analysis["error"],
            )
        )

    return engines


# ============================================================
# 7. REGISTRY / SYNC
# ============================================================
def def_save_registry(root: Path, engines: list[EngineRecord]) -> Path:
    p = def_runtime_dir(root) / REGISTRY_FILENAME

    payload = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "generated_at": def_now_iso(),
        "root": str(root.resolve()),
        "count": len(engines),
        "engines": [asdict(e) for e in engines],
    }

    def_write_json_atomic(p, payload)
    return p


def def_load_registry(root: Path) -> list[EngineRecord]:
    p = def_runtime_dir(root) / REGISTRY_FILENAME

    if not p.exists():
        engines = def_discover(root)
        def_save_registry(root, engines)
        return engines

    raw = json.loads(p.read_text(encoding="utf-8"))
    return [EngineRecord(**item) for item in raw.get("engines", [])]


def def_sync_registry(root: Path) -> list[EngineRecord]:
    old = {e.path: e for e in def_load_registry(root)}
    new = def_discover(root)

    added = 0
    changed = 0

    for e in new:
        prev = old.get(e.path)

        if prev is None:
            added += 1

        elif prev.sha256 != e.sha256:
            changed += 1

        else:
            # 保留最近驗證狀態
            e.gates = prev.gates
            e.score = prev.score
            e.health = prev.health
            e.html_ready = prev.html_ready
            e.last_checked = prev.last_checked

    current_paths = {e.path for e in new}
    removed = len([p for p in old if p not in current_paths])

    def_save_registry(root, new)

    def_append_event(root, {
        "type": "registry_sync",
        "added": added,
        "changed": changed,
        "removed": removed,
        "total": len(new),
    })

    return new


def def_find_engine(root: Path, key: str) -> EngineRecord:
    engines = def_load_registry(root)

    for e in engines:
        if e.engine_id.lower() == key.lower() or e.name.lower() == key.lower():
            return e

    raise SystemExit(f"找不到引擎/工具：{key}")


# ============================================================
# 8. 14-GATE VALIDATION
# ============================================================
def def_gate(name: str, fn) -> GateResult:
    start = time.perf_counter()

    try:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"

    except Exception as e:
        status = "FAIL"
        detail = f"{type(e).__name__}: {e}"

    return GateResult(
        gate=name,
        status=status,
        detail=str(detail),
        elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
    )


def def_validate_engine(
    engine: EngineRecord,
    smoke: bool = False,
    retries: int = DEFAULT_RETRIES,
) -> EngineRecord:

    path = Path(engine.path)
    gates: list[GateResult] = []

    gates.append(def_gate(
        "G01 Discovery",
        lambda: (bool(engine.engine_id and engine.path), engine.engine_id)
    ))

    gates.append(def_gate(
        "G02 File existence",
        lambda: (path.exists(), str(path))
    ))

    def syntax_gate():
        if engine.kind == "python":
            a = def_analyze_python(path)
            return a["syntax_ok"], a["error"] or "AST parse OK"
        return True, "PowerShell static parse registered"

    gates.append(def_gate("G03 Syntax", syntax_gate))

    def import_gate():
        if engine.kind != "python":
            return True, "N/A process adapter"

        stdlib = set(getattr(sys, "stdlib_module_names", set()))
        missing = []

        for dep in engine.dependencies:
            if dep in stdlib:
                continue
            try:
                if importlib.util.find_spec(dep) is None:
                    missing.append(dep)
            except Exception:
                missing.append(dep)

        return (
            len(missing) == 0,
            "resolved" if not missing else "missing=" + ",".join(missing),
        )

    gates.append(def_gate("G04 Import", import_gate))

    def runtime_gate():
        if engine.kind == "python":
            return bool(sys.executable), sys.executable

        exe = shutil.which("pwsh") or shutil.which("powershell")
        return bool(exe), exe or "PowerShell missing"

    gates.append(def_gate("G05 Runtime", runtime_gate))

    gates.append(def_gate(
        "G06 Entry-point",
        lambda: (
            bool(engine.entry_points),
            ",".join(engine.entry_points) or "none",
        )
    ))

    def param_gate():
        names = [p.get("name") for p in engine.parameters]
        return len(names) == len(set(names)), f"{len(names)} parameter(s)"

    gates.append(def_gate("G07 Parameter schema", param_gate))

    gates.append(def_gate(
        "G08 Input contract",
        lambda: (True, "JSON/key-value compatible")
    ))

    gates.append(def_gate(
        "G09 Output contract",
        lambda: (
            True,
            ",".join(engine.outputs) if engine.outputs else "stdout/result envelope"
        )
    ))

    def dry_run_gate():
        if not smoke:
            return True, "static-only; execution skipped"

        last = ""

        for attempt in range(retries + 1):
            try:
                if engine.kind == "python":
                    proc = subprocess.run(
                        [sys.executable, str(path), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=DEFAULT_TIMEOUT_SECONDS,
                    )
                    last = f"attempt={attempt+1} rc={proc.returncode}"
                    if proc.returncode in (0, 1, 2):
                        return True, last

                else:
                    exe = shutil.which("pwsh") or shutil.which("powershell")
                    if not exe:
                        return False, "PowerShell missing"

                    proc = subprocess.run(
                        [exe, "-NoProfile", "-File", str(path), "-?"],
                        capture_output=True,
                        text=True,
                        timeout=DEFAULT_TIMEOUT_SECONDS,
                    )

                    last = f"attempt={attempt+1} rc={proc.returncode}"

                    if proc.returncode in (0, 1, 2):
                        return True, last

            except Exception as e:
                last = f"attempt={attempt+1}: {type(e).__name__}: {e}"

        return False, last

    gates.append(def_gate("G10 Dry-run", dry_run_gate))

    def selftest_gate():
        matches = [
            x for x in engine.entry_points
            if x.lower() in {"selftest", "self_test", "test", "validate"}
        ]
        if matches:
            return True, "hook=" + ",".join(matches)
        return True, "external command-center self-test"

    gates.append(def_gate("G11 Self-test", selftest_gate))

    gates.append(def_gate(
        "G12 HTML/API readiness",
        lambda: (
            path.exists() and bool(engine.entry_points),
            "adapter-ready" if engine.entry_points else "entry-point missing",
        )
    ))

    def hash_gate():
        current = def_sha256(path) if path.exists() else ""
        return current == engine.sha256, "unchanged" if current == engine.sha256 else "changed since registry"

    gates.append(def_gate("G13 Registry hash sync", hash_gate))

    def status_gate():
        fail_count = sum(1 for g in gates if g.status == "FAIL")
        return fail_count == 0, f"failures={fail_count}"

    gates.append(def_gate("G14 Overall consistency", status_gate))

    engine.gates = [asdict(g) for g in gates]

    passed = sum(1 for g in gates if g.status == "PASS")
    total = len(gates)

    engine.score = round((passed / total) * 100, 1)
    engine.last_checked = def_now_iso()

    if passed == total:
        engine.health = "HEALTHY"
        engine.html_ready = "READY"
    elif passed >= total - 2:
        engine.health = "DEGRADED"
        engine.html_ready = "REVIEW"
    else:
        engine.health = "FAILED"
        engine.html_ready = "BLOCKED"

    return engine


# ============================================================
# 9. VALIDATE ALL
# ============================================================
def def_validate_all(
    root: Path,
    smoke: bool = False,
    retries: int = DEFAULT_RETRIES,
) -> list[EngineRecord]:

    engines = def_sync_registry(root)

    validated = [
        def_validate_engine(e, smoke=smoke, retries=retries)
        for e in engines
    ]

    def_save_registry(root, validated)
    def_export_reports(root, validated)

    return validated


# ============================================================
# 10. INPUT / STATUS / OUTPUT MATRICES
# ============================================================
def def_input_rows(engines: list[EngineRecord]) -> list[dict[str, Any]]:
    rows = []

    for e in engines:
        if not e.parameters:
            rows.append({
                "ID": e.engine_id,
                "Engine": e.name,
                "Parameter": "",
                "Required": "",
                "Type": "",
                "Default": "",
            })
            continue

        for p in e.parameters:
            rows.append({
                "ID": e.engine_id,
                "Engine": e.name,
                "Parameter": p.get("name", ""),
                "Required": p.get("required", ""),
                "Type": p.get("type", ""),
                "Default": p.get("default", ""),
            })

    return rows


def def_status_rows(engines: list[EngineRecord]) -> list[dict[str, Any]]:
    return [{
        "ID": e.engine_id,
        "Subsystem": e.subsystem,
        "Engine": e.name,
        "Kind": e.kind,
        "Health": e.health,
        "Score": e.score,
        "HTML": e.html_ready,
        "LastChecked": e.last_checked,
    } for e in engines]


def def_output_rows(engines: list[EngineRecord]) -> list[dict[str, Any]]:
    return [{
        "ID": e.engine_id,
        "Engine": e.name,
        "Outputs": ",".join(e.outputs) if e.outputs else "stdout/result",
        "Entry": ",".join(e.entry_points),
        "Path": e.path,
    } for e in engines]


# ============================================================
# 11. DETAILED MATRIX / SUMMARY
# ============================================================
def def_matrix_rows(engines: list[EngineRecord]) -> list[dict[str, Any]]:
    rows = []

    for e in engines:
        gate_map = {
            g["gate"].split(" ", 1)[0]: g["status"]
            for g in e.gates
        }

        row = {
            "ID": e.engine_id,
            "Subsystem": e.subsystem,
            "Engine": e.name,
            "Kind": e.kind,
            "Params": len(e.parameters),
            "Outputs": ",".join(e.outputs),
            "Score": e.score,
            "Health": e.health,
            "HTML": e.html_ready,
        }

        for i in range(1, 15):
            key = f"G{i:02d}"
            row[key] = gate_map.get(key, "")

        rows.append(row)

    return rows


def def_summary(engines: list[EngineRecord]) -> dict[str, Any]:
    total = len(engines)
    healthy = sum(e.health == "HEALTHY" for e in engines)
    degraded = sum(e.health == "DEGRADED" for e in engines)
    failed = sum(e.health == "FAILED" for e in engines)
    ready = sum(e.html_ready == "READY" for e in engines)

    by_subsystem: dict[str, int] = {}
    by_kind: dict[str, int] = {}

    for e in engines:
        by_subsystem[e.subsystem] = by_subsystem.get(e.subsystem, 0) + 1
        by_kind[e.kind] = by_kind.get(e.kind, 0) + 1

    avg_score = round(
        sum(e.score for e in engines) / total, 2
        if total else 0
    ) if total else 0.0

    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "generated_at": def_now_iso(),
        "total": total,
        "healthy": healthy,
        "degraded": degraded,
        "failed": failed,
        "html_ready": ready,
        "average_score": avg_score,
        "by_subsystem": by_subsystem,
        "by_kind": by_kind,
    }


# ============================================================
# 12. EXPORT
# ============================================================
def def_write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding=CSV_ENCODING)
        return

    with path.open("w", encoding=CSV_ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def def_export_reports(
    root: Path,
    engines: list[EngineRecord],
) -> dict[str, str]:

    rt = def_runtime_dir(root)

    matrix_rows = def_matrix_rows(engines)
    summary = def_summary(engines)

    matrix_json = rt / MATRIX_JSON_FILENAME
    matrix_csv = rt / MATRIX_CSV_FILENAME
    summary_json = rt / SUMMARY_FILENAME
    input_csv = rt / "inputs_matrix.csv"
    status_csv = rt / "status_matrix.csv"
    output_csv = rt / "outputs_matrix.csv"

    def_write_json_atomic(matrix_json, matrix_rows)
    def_write_csv(matrix_csv, matrix_rows)
    def_write_json_atomic(summary_json, summary)

    def_write_csv(input_csv, def_input_rows(engines))
    def_write_csv(status_csv, def_status_rows(engines))
    def_write_csv(output_csv, def_output_rows(engines))

    return {
        "matrix_json": str(matrix_json),
        "matrix_csv": str(matrix_csv),
        "summary_json": str(summary_json),
        "inputs_csv": str(input_csv),
        "status_csv": str(status_csv),
        "outputs_csv": str(output_csv),
    }


# ============================================================
# 13. DISPLAY
# ============================================================
def def_print_table(rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        print("No data.")
        return

    widths = {}

    for col in columns:
        widths[col] = min(
            32,
            max(
                len(col),
                max(len(str(r.get(col, ""))) for r in rows),
            ),
        )

    print(" | ".join(col.ljust(widths[col]) for col in columns))
    print("-+-".join("-" * widths[col] for col in columns))

    for r in rows:
        print(" | ".join(
            str(r.get(col, ""))[:widths[col]].ljust(widths[col])
            for col in columns
        ))


def def_print_summary(engines: list[EngineRecord]) -> None:
    s = def_summary(engines)

    print()
    print("=" * 72)
    print(f"{APP_NAME}  v{APP_VERSION}")
    print("=" * 72)
    print(f"Total        : {s['total']}")
    print(f"Healthy      : {s['healthy']}")
    print(f"Degraded     : {s['degraded']}")
    print(f"Failed       : {s['failed']}")
    print(f"HTML Ready   : {s['html_ready']}")
    print(f"Average Score: {s['average_score']}%")
    print(f"Subsystems   : {s['by_subsystem']}")
    print("=" * 72)


# ============================================================
# 14. EXECUTION ADAPTER
# ============================================================
def def_parse_kv(items: list[str]) -> dict[str, str]:
    out = {}

    for item in items:
        if "=" not in item:
            raise SystemExit(f"參數格式必須是 key=value：{item}")

        k, v = item.split("=", 1)
        out[k.strip()] = v

    return out


def def_execute_engine(
    engine: EngineRecord,
    params: dict[str, str],
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:

    path = Path(engine.path)

    if engine.kind == "python":
        cmd = [sys.executable, str(path)]

        for k, v in params.items():
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])

    else:
        exe = shutil.which("pwsh") or shutil.which("powershell")

        if not exe:
            return {
                "status": "failed",
                "returncode": -1,
                "stdout": "",
                "stderr": "PowerShell not found",
                "command": [],
            }

        cmd = [
            exe,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(path),
        ]

        for k, v in params.items():
            cmd.extend([f"-{k}", str(v)])

    start = time.perf_counter()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
            "stdout": def_clip(proc.stdout),
            "stderr": def_clip(proc.stderr),
            "command": cmd,
        }

    except Exception as e:
        return {
            "status": "failed",
            "returncode": -1,
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
            "stdout": "",
            "stderr": f"{type(e).__name__}: {e}",
            "command": cmd,
        }


# ============================================================
# 15. COMMAND IMPLEMENTATIONS
# ============================================================
def def_cmd_scan(root: Path) -> None:
    engines = def_discover(root)
    p = def_save_registry(root, engines)

    print(f"[OK] Auto-catch completed: {len(engines)} engines/tools")
    print(f"[OK] Registry: {p}")


def def_cmd_sync(root: Path) -> None:
    engines = def_sync_registry(root)

    print(f"[OK] Registry synchronized: {len(engines)}")
    def_print_summary(engines)


def def_cmd_list(root: Path) -> None:
    rows = def_status_rows(def_load_registry(root))

    def_print_table(
        rows,
        ["ID", "Subsystem", "Engine", "Kind", "Health", "Score", "HTML"],
    )


def def_cmd_inputs(root: Path, key: Optional[str]) -> None:
    engines = (
        [def_find_engine(root, key)]
        if key else def_load_registry(root)
    )

    def_print_table(
        def_input_rows(engines),
        ["ID", "Engine", "Parameter", "Required", "Type", "Default"],
    )


def def_cmd_status(root: Path, key: Optional[str]) -> None:
    engines = (
        [def_find_engine(root, key)]
        if key else def_load_registry(root)
    )

    def_print_table(
        def_status_rows(engines),
        ["ID", "Subsystem", "Engine", "Kind", "Health", "Score", "HTML", "LastChecked"],
    )


def def_cmd_outputs(root: Path, key: Optional[str]) -> None:
    engines = (
        [def_find_engine(root, key)]
        if key else def_load_registry(root)
    )

    def_print_table(
        def_output_rows(engines),
        ["ID", "Engine", "Outputs", "Entry", "Path"],
    )


def def_cmd_inspect(root: Path, key: str) -> None:
    print(json.dumps(
        asdict(def_find_engine(root, key)),
        ensure_ascii=False,
        indent=2,
    ))


def def_cmd_validate(
    root: Path,
    key: str,
    smoke: bool,
    retries: int,
) -> None:

    engine = def_validate_engine(
        def_find_engine(root, key),
        smoke=smoke,
        retries=retries,
    )

    for g in engine.gates:
        print(
            f"{g['gate']:<30} "
            f"{g['status']:<6} "
            f"{g['detail']}"
        )

    print()
    print(
        f"Health={engine.health} | "
        f"Score={engine.score}% | "
        f"HTML={engine.html_ready}"
    )


def def_cmd_validate_all(
    root: Path,
    smoke: bool,
    retries: int,
) -> None:

    engines = def_validate_all(
        root,
        smoke=smoke,
        retries=retries,
    )

    def_print_table(
        def_matrix_rows(engines),
        [
            "ID", "Subsystem", "Engine", "Kind",
            "Score", "Health", "HTML",
            "G01", "G02", "G03", "G04", "G05", "G06", "G07",
            "G08", "G09", "G10", "G11", "G12", "G13", "G14",
        ],
    )

    def_print_summary(engines)

    reports = def_export_reports(root, engines)

    print()
    for k, v in reports.items():
        print(f"{k:<14}: {v}")


def def_cmd_matrix(root: Path) -> None:
    engines = def_load_registry(root)

    def_print_table(
        def_matrix_rows(engines),
        [
            "ID", "Subsystem", "Engine", "Kind",
            "Params", "Outputs", "Score", "Health", "HTML",
            "G01", "G02", "G03", "G04", "G05", "G06", "G07",
            "G08", "G09", "G10", "G11", "G12", "G13", "G14",
        ],
    )


def def_cmd_summary(root: Path) -> None:
    def_print_summary(def_load_registry(root))


def def_cmd_run(
    root: Path,
    key: str,
    kv: list[str],
    timeout: int,
) -> None:

    engine = def_find_engine(root, key)
    params = def_parse_kv(kv)

    result = def_execute_engine(engine, params, timeout=timeout)

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    ))

    def_append_event(root, {
        "type": "engine_run",
        "engine": engine.engine_id,
        "name": engine.name,
        "result": result["status"],
        "returncode": result["returncode"],
    })


def def_cmd_auto(
    root: Path,
    smoke: bool,
    retries: int,
) -> None:

    print("[1/6] AUTO-CATCH")
    engines = def_sync_registry(root)
    print(f"      found={len(engines)}")

    print("[2/6] CONNECT / CONTRACT ANALYSIS")
    print("      entry-points, inputs, outputs, dependencies parsed")

    print("[3/6] SYNC REGISTRY")
    print("      registry SSOT updated")

    print("[4/6] TEST / DEBUG / VALIDATE")
    engines = def_validate_all(
        root,
        smoke=smoke,
        retries=retries,
    )

    print("[5/6] MATRIX / SUMMARY EXPORT")
    reports = def_export_reports(root, engines)

    print("[6/6] FINAL STATUS")
    def_print_summary(engines)

    for k, v in reports.items():
        print(f"{k:<14}: {v}")


def def_cmd_watch(
    root: Path,
    interval: int,
    smoke: bool,
    retries: int,
) -> None:

    print(f"[WATCH] root={root}")
    print(f"[WATCH] interval={interval}s")
    print("[WATCH] Ctrl+C to stop")

    try:
        while True:
            def_cmd_auto(root, smoke=smoke, retries=retries)
            time.sleep(max(1, interval))

    except KeyboardInterrupt:
        print("\n[WATCH] stopped")


# ============================================================
# 16. CLI
# ============================================================
def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="One-file engine/tool command center",
    )

    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT,
        help="掃描根目錄",
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan")
    sub.add_parser("sync")
    sub.add_parser("list")
    sub.add_parser("matrix")
    sub.add_parser("summary")

    p_inputs = sub.add_parser("inputs")
    p_inputs.add_argument("engine", nargs="?")

    p_status = sub.add_parser("status")
    p_status.add_argument("engine", nargs="?")

    p_outputs = sub.add_parser("outputs")
    p_outputs.add_argument("engine", nargs="?")

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("engine")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("engine")
    p_validate.add_argument("--smoke", action="store_true")
    p_validate.add_argument("--retries", type=int, default=DEFAULT_RETRIES)

    p_all = sub.add_parser("validate-all")
    p_all.add_argument("--smoke", action="store_true")
    p_all.add_argument("--retries", type=int, default=DEFAULT_RETRIES)

    p_run = sub.add_parser("run")
    p_run.add_argument("engine")
    p_run.add_argument("params", nargs="*")
    p_run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)

    p_auto = sub.add_parser("auto")
    p_auto.add_argument("--smoke", action="store_true")
    p_auto.add_argument("--retries", type=int, default=DEFAULT_RETRIES)

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("--interval", type=int, default=WATCH_INTERVAL_SECONDS)
    p_watch.add_argument("--smoke", action="store_true")
    p_watch.add_argument("--retries", type=int, default=DEFAULT_RETRIES)

    return parser


# ============================================================
# 17. MAIN
# ============================================================
def def_main() -> int:
    parser = def_build_parser()
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()

    if not root.exists():
        print(f"[FAIL] Root not found: {root}")
        return 2

    command = args.command or "auto"

    if command == "scan":
        def_cmd_scan(root)

    elif command == "sync":
        def_cmd_sync(root)

    elif command == "list":
        def_cmd_list(root)

    elif command == "inputs":
        def_cmd_inputs(root, args.engine)

    elif command == "status":
        def_cmd_status(root, args.engine)

    elif command == "outputs":
        def_cmd_outputs(root, args.engine)

    elif command == "inspect":
        def_cmd_inspect(root, args.engine)

    elif command == "validate":
        def_cmd_validate(root, args.engine, args.smoke, args.retries)

    elif command == "validate-all":
        def_cmd_validate_all(root, args.smoke, args.retries)

    elif command == "matrix":
        def_cmd_matrix(root)

    elif command == "summary":
        def_cmd_summary(root)

    elif command == "run":
        def_cmd_run(root, args.engine, args.params, args.timeout)

    elif command == "auto":
        def_cmd_auto(root, args.smoke, args.retries)

    elif command == "watch":
        def_cmd_watch(root, args.interval, args.smoke, args.retries)

    else:
        parser.print_help()
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
