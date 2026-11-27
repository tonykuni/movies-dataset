#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Small deterministic verbs and reviewable adapter contracts. [VIA:ACCEL-BRIDGE]"""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

CATALOG_PATH = "config/tools.json"
MAX_METRIC_ROWS = 100000
MODULE_SCHEMA = "via.toolmodule/1"

import ast
import collections
import csv
import importlib.util
import io
import json
import re
from pathlib import Path
from .core import MAX_CONTEXT_CHARS, VERBS, digest, encode, load_json, node_id, read_bytes, strict_json
from .inventory import analyze_python, decode_source


def catalog(package):
    rows = load_json(Path(package) / CATALOG_PATH)["tools"]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_TOOL_ID")
    return rows


def compact_context(snapshot, query="", budget=MAX_CONTEXT_CHARS):
    if not 200 <= budget <= MAX_CONTEXT_CHARS:
        raise ValueError("CONTEXT_BUDGET_RANGE")
    terms = query.casefold().split()
    selected = [n for n in snapshot["nodes"] if all(t in (n["name"] + " " + n["path"]).casefold() for t in terms)]
    selected.sort(key=lambda n: (n["root_id"], n["path"], n["start"]))
    answer = {"schema": "via.context-card/1", "input_fingerprint": snapshot["input_fingerprint"],
              "source_tokens": None, "selected_tokens": None, "token_saving": None,
              "measurement": "UTF-8 bytes and characters only; no tokenizer/provider billing data",
              "matched": len(selected), "returned": 0, "truncated": False, "nodes": []}
    for n in selected:
        card = {k: n[k] for k in ("node_id", "root_id", "path", "name", "kind", "start", "end", "parameters", "file_sha256")}
        candidate = dict(answer, nodes=answer["nodes"] + [card], returned=answer["returned"] + 1)
        if len(encode(candidate).decode("utf-8")) > budget - 24:
            answer["truncated"] = True
            break
        answer = candidate
    answer["truncated"] = answer["returned"] < len(selected)
    if len(encode(answer).decode("utf-8")) > budget:
        raise ValueError("BUDGET_TOO_SMALL_FOR_RECEIPT")
    return answer


def compare(before, after):
    old = {(r["root_id"], r["path"]): r for r in before["files"]}
    new = {(r["root_id"], r["path"]): r for r in after["files"]}
    rows = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        status = "ADDED" if a is None else "REMOVED" if b is None else "CHANGED" if a.get("sha256") != b.get("sha256") else "UNCHANGED"
        if status != "UNCHANGED":
            rows.append({"root_id": key[0], "path": key[1], "status": status, "before": (a or {}).get("sha256"), "after": (b or {}).get("sha256")})
    return {"changes": rows, "count": len(rows), "unchanged": len(set(old) & set(new)) - sum(r["status"] == "CHANGED" for r in rows)}


def module_check(manifest_path):
    """Check an intake contract without importing or executing its Python module."""
    path = Path(manifest_path).resolve()
    m = load_json(path)
    required = {"schema", "module_id", "verb", "description", "entry", "sha256", "input_schema", "output_schema", "capabilities"}
    if not isinstance(m, dict) or not required <= set(m) or m["schema"] != MODULE_SCHEMA:
        raise ValueError("MODULE_MANIFEST_SCHEMA")
    if not re.fullmatch(r"VTM-[A-Z0-9-]{3,60}", m["module_id"]) or not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", m["verb"]):
        raise ValueError("MODULE_ID_OR_VERB_INVALID")
    if m["module_id"] in {row["id"] for row in catalog(Path(__file__).resolve().parent.parent)} or m["verb"] in VERBS:
        raise ValueError("MODULE_ID_OR_VERB_COLLISION")
    entry = Path(m["entry"])
    if entry.is_absolute() or ".." in entry.parts or entry.suffix != ".py":
        raise ValueError("MODULE_ENTRY_ESCAPE")
    target = path.parent / entry
    if not target.resolve().is_relative_to(path.parent):
        raise ValueError("MODULE_ENTRY_ESCAPE")
    raw = read_bytes(target)
    if digest(raw) != m["sha256"]:
        raise ValueError("MODULE_HASH_MISMATCH")
    tree = ast.parse(decode_source(raw))
    compile(tree, str(target), "exec")
    defs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    counts = collections.Counter(n.name for n in defs)
    if any(counts[name] != 1 for name in ("describe", "execute", "main")):
        raise ValueError("MODULE_REQUIRED_DEFS: describe/execute/main exactly once")
    execute = next(n for n in defs if n.name == "execute")
    if len(execute.args.args) != 1 or execute.args.vararg or execute.args.kwarg or execute.args.kwonlyargs or execute.args.posonlyargs:
        raise ValueError("MODULE_EXECUTE_REQUIRES_ONE_REQUEST")
    if not isinstance(m["capabilities"], list) or not isinstance(m["input_schema"], dict) or not isinstance(m["output_schema"], dict):
        raise ValueError("MODULE_CONTRACT_TYPES")
    return {"status": "STATIC_CONTRACT_PASS", "module_id": m["module_id"], "ssot_id": None, "sha256": m["sha256"],
            "verb": m["verb"], "target_imported": False, "activated": False,
            "next": "Native VCGC registration, ID audit and manager-owned runtime receipt required."}


def skills_index(snapshot, roots):
    lookup = {label: Path(root).resolve() for label, root in roots}
    rows = []
    for r in snapshot["files"]:
        if Path(r["path"]).name != "SKILL.md" or r["status"] == "ERROR":
            continue
        raw = read_bytes(lookup[r["root_id"]] / r["path"])
        if digest(raw) != r["sha256"]:
            raise ValueError("SKILL_CHANGED_SINCE_SCAN")
        text = raw.decode("utf-8-sig")
        parts = text.split("---", 2)
        header = parts[1] if len(parts) == 3 and not parts[0].strip() else ""
        name = re.search(r"(?m)^name:\s*([^\r\n]+)", header)
        description = re.search(r"(?m)^description:\s*([^\r\n]+)", header)
        rows.append({"root_id": r["root_id"], "path": r["path"], "sha256": r["sha256"],
                     "name": name.group(1).strip("\"'") if name else None,
                     "status": "HEADER_FIELDS_FOUND_NOT_FULL_YAML_VALIDATION" if name and description else "REVIEW_HEADER",
                     "instruction_body_loaded": False, "executed": False})
    return {"skills": rows, "count": len(rows), "scope": "Local discovery only; no automatic install or skill execution."}


def token_metrics(path):
    raw = read_bytes(path)
    text = raw.decode("utf-8-sig")
    if Path(path).suffix.lower() == ".csv":
        rows = list(csv.DictReader(io.StringIO(text)))
    elif Path(path).suffix.lower() == ".jsonl":
        rows = [strict_json(line) for line in text.splitlines() if line.strip()]
    else:
        rows = strict_json(text)
    if not isinstance(rows, list) or len(rows) > MAX_METRIC_ROWS:
        raise ValueError("METRICS_ROWS_INVALID")
    seen, grouped, rejected = {}, collections.defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "events": 0}), []
    def count(value):
        if isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
            raise ValueError("TOKEN_COUNT_NOT_NONNEGATIVE_INTEGER")
        return int(value)
    duplicates = 0
    for i, row in enumerate(rows):
        try:
            event_id, action = row["event_id"], row["action"]
            if not isinstance(event_id, str) or not event_id or not isinstance(action, str) or not action:
                raise ValueError("EVENT_ID_ACTION_REQUIRED")
            normalized = {"event_id": event_id, "action": action, "input_tokens": count(row["input_tokens"]), "output_tokens": count(row["output_tokens"])}
            if event_id in seen:
                if seen[event_id] != normalized:
                    raise ValueError("DUPLICATE_EVENT_CONFLICT")
                duplicates += 1
                continue
            seen[event_id] = normalized
            aggregate = grouped[action]
            aggregate["input_tokens"] += normalized["input_tokens"]
            aggregate["output_tokens"] += normalized["output_tokens"]
            aggregate["events"] += 1
        except (KeyError, ValueError, TypeError) as exc:
            rejected.append({"row": i + 1, "reason": str(exc)})
    return {"status": "INVALID" if rejected else ("EMPTY" if not seen else "MEASURED"), "source_sha256": digest(raw),
            "rows": [{"action": a, **v} for a, v in sorted(grouped.items())], "accepted": len(seen), "duplicates": duplicates,
            "rejected": rejected, "estimated_savings": None, "cost": None,
            "note": "Reported usage only; duplicate event conflicts invalidate this report. No synthetic fallback."}


def duckdb_schema(path):
    if importlib.util.find_spec("duckdb") is None:
        return {"status": "DEPENDENCY_UNAVAILABLE", "dependency": "duckdb", "tables": [], "chartdb_import_validated": False}
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("DATABASE_NOT_FOUND")
    import duckdb
    connection = duckdb.connect(str(path), read_only=True, config={"enable_external_access": "false", "autoinstall_known_extensions": "false", "autoload_known_extensions": "false"})
    try:
        rows = connection.execute("SELECT table_schema,table_name,column_name,data_type,is_nullable,ordinal_position FROM information_schema.columns ORDER BY table_schema,table_name,ordinal_position").fetchall()
        return {"status": "SCHEMA_READ_ONLY", "tables": [{"schema": a, "table": b, "column": c, "type": d, "nullable": e, "position": f} for a,b,c,d,e,f in rows],
                "format": "via.relational-schema/1", "chartdb_import_validated": False, "row_data_read": False}
    finally:
        connection.close()


def registration_plan(rows, package):
    return {"schema": "via.registration-proposal/1", "status": "NOT_APPLIED", "owner": "VCGC",
            "ssot_ids": None, "namespace": "VTM local proposal IDs; not central CGC_MDL or SSOT IDs",
            "entry": str(Path(package) / "VIA_VCGC_ToolModules_v0100.py"),
            "proposed_native_verb": "toolmodules", "current_native_verb_available": False,
            "modules": [{"proposal_id": r["id"], "name": r["name"], "ssot_id": None, "verb": r["verb"]} for r in rows],
            "sequence": ["token", "functions", "handoff check", "chain CGC_MDL149_VeritasCentralGovernanceConsole", "ssot panorama", "new-version requirement/workflow/function-inventory proposal", "native registration and NumberingSystem audit", "manager tests", "handoff checkpoint"],
            "mcp": {"reuse": "CGC_MDL279_MCPServer + VIA_MCP_Engine", "session_url_is_mcp_endpoint": False, "new_tools_exposed": False,
                    "next": "Add reviewed read-only toolmodule methods to a new native MCP version; validate initialize/tools-list/tools-call on the host."},
            "canonical_writes": False, "github_push": False}


def graph_mermaid(snapshot):
    edges = snapshot.get("edges", [])
    paths = sorted({(e["root_id"], e[k]) for e in edges for k in ("from", "to")})
    names = {p: "N" + str(i) for i, p in enumerate(paths)}
    lines = ["flowchart TD"]
    for p in paths:
        label = re.sub(r"[^A-Za-z0-9_. /\u4e00-\u9fff-]", "_", p[0] + "/" + p[1])
        lines.append(f'  {names[p]}["{label}"]')
    for e in edges:
        lines.append(f'  {names[(e["root_id"], e["from"])]} --> {names[(e["root_id"], e["to"])]}')
    if not paths:
        return "No unambiguous static import edges in the selected inputs.\n"
    return "\n".join(lines) + "\n"
