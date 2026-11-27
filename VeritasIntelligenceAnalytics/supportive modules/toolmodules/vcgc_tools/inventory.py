#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""AST contract index for module intake; no target import. [VIA:ACCEL-BRIDGE]"""
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

PARSER_REVISION = "vtm-ast-3"
SECRET_WORDS = ("password", "secret", "api_key", "private_key", "credential", "access_token")

import ast
import collections
import io
import os
import tokenize
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .core import MAX_FILES, SKIP_DIRS, SOURCE_SUFFIXES, budget, digest, is_link, node_id, read_bytes


def enumerate_inputs(roots):
    files, issues, seen = [], [], set()
    for label, original in roots:
        root = Path(original).expanduser().resolve()
        if not root.is_dir() or is_link(original):
            issues.append({"kind": "ROOT_UNAVAILABLE", "path": str(original), "severity": "RED"})
            continue
        def onerror(error):
            issues.append({"kind": "ENUMERATION_ERROR", "path": str(error.filename), "severity": "RED"})
        for parent, directories, names in os.walk(root, followlinks=False, onerror=onerror):
            keep = []
            for name in sorted(directories):
                p = Path(parent) / name
                if name in SKIP_DIRS:
                    continue
                try:
                    if is_link(p):
                        issues.append({"kind": "LINK_SKIPPED", "path": str(p), "severity": "YELLOW"})
                    else:
                        keep.append(name)
                except OSError:
                    issues.append({"kind": "DIRECTORY_UNREADABLE", "path": str(p), "severity": "RED"})
            directories[:] = keep
            for name in sorted(names):
                p = Path(parent) / name
                if p.suffix.lower() not in SOURCE_SUFFIXES:
                    continue
                try:
                    if is_link(p):
                        issues.append({"kind": "LINK_SKIPPED", "path": str(p), "severity": "YELLOW"})
                        continue
                except OSError:
                    issues.append({"kind": "FILE_UNREADABLE", "path": str(p), "severity": "RED"})
                    continue
                identity = str(p.resolve())
                if identity in seen:
                    continue
                seen.add(identity)
                files.append((label, root, p))
                if len(files) >= MAX_FILES:
                    issues.append({"kind": "FILE_LIMIT_REACHED", "severity": "RED", "limit": MAX_FILES})
                    return files, issues
    return files, issues


def subsystem(relative):
    name = relative.replace("\\", "/").upper()
    if "VRN2" in name or "VRN-2" in name:
        return "VRN-2"
    if "VRN1" in name or "VRN-1" in name:
        return "VRN-1"
    if "VRN" in name:
        return "VRN(未分辨)"
    return next((s for s in ("VCGC", "CGC", "VDF", "VAP", "VQG") if s in name), "OTHER").replace("CGC", "VCGC") if "VCGC" not in name else "VCGC"


def decode_source(raw):
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding)


def parameter_names(node):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    args = node.args
    return [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs] + (["*" + args.vararg.arg] if args.vararg else []) + (["**" + args.kwarg.arg] if args.kwarg else [])


def analyze_python(raw, label, relative):
    source = decode_source(raw)
    tree = ast.parse(source, filename=relative)
    compile(tree, relative, "exec")
    nodes, issues = [], []
    def visit_scope(body, scope="", id_scope=""):
        counts = collections.Counter(n.name for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        for name, count in counts.items():
            if count > 1:
                issues.append({"kind": "DUPLICATE_DEFINITION", "scope": scope, "name": name, "count": count, "severity": "YELLOW", "decision": "REVIEW_WRAPPER_CHAIN"})
        occurrences = collections.Counter()
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = (scope + "." if scope else "") + n.name
                occurrences[n.name] += 1
                # id_scope carries the parent's occurrence tag, so f@1.inner and f@2.inner stay distinct.
                identity = (id_scope + "." if id_scope else "") + n.name + ("@" + str(occurrences[n.name]) if counts[n.name] > 1 else "")
                nodes.append({"node_id": node_id(label, relative, identity), "name": qualified,
                              "kind": type(n).__name__, "start": n.lineno, "end": n.end_lineno,
                              "parameters": parameter_names(n), "has_docstring": bool(ast.get_docstring(n)),
                              "ast_sha256": digest(ast.dump(n, include_attributes=False).encode()),
                              "category": "ENTRY" if n.name == "main" else ("CONTRACT" if n.name in ("describe", "execute") else "FUNCTION")})
                visit_scope(n.body, qualified, identity)
            else:
                # Conditional definitions are indexed with explicit scope, not silently merged.
                for field in ("body", "orelse", "finalbody"):
                    children = getattr(n, field, None)
                    if isinstance(children, list):
                        tag = f".<{type(n).__name__}:{n.lineno}:{field}>"
                        visit_scope(children, scope + tag, id_scope + tag)
                for index, handler in enumerate(getattr(n, "handlers", [])):
                    tag = f".<except:{n.lineno}:{index}>"
                    visit_scope(handler.body, scope + tag, id_scope + tag)
                # match 的分支放在 cases,不在 body / orelse:每個 case 各自一個分支身分。
                for index, case in enumerate(getattr(n, "cases", [])):
                    tag = f".<match:{n.lineno}:{index}>"
                    visit_scope(case.body, scope + tag, id_scope + tag)
    visit_scope(tree.body)
    imports = sorted({n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec"):
            issues.append({"kind": "DYNAMIC_EXECUTION", "line": n.lineno, "severity": "YELLOW", "decision": "NO_AUTO_PATCH"})
    return {"status": "PARSED", "nodes": nodes, "imports": imports, "issues": issues,
            "accelerator_marker": "[VIA:ACCEL-BRIDGE" in source, "accelerator_executed": False}


def analyze_one(item, cache):
    label, root, path = item
    relative = path.relative_to(root).as_posix()
    row = {"root_id": label, "path": relative, "system": subsystem(relative), "bytes": None,
           "status": "UNREAD", "nodes": [], "imports": [], "issues": []}
    try:
        raw = read_bytes(path)
        row.update(bytes=len(raw), sha256=digest(raw))
        key = (label, relative, row["sha256"], PARSER_REVISION)
        if key in cache:
            return dict(cache[key], cache_hit=True)
        if path.suffix.lower() == ".py":
            row.update(analyze_python(raw, label, relative))
        else:
            row["status"] = "POWERSHELL_AST_NOT_RUN" if path.suffix.lower() in (".ps1", ".psm1") else "HASH_ONLY"
    except (OSError, ValueError, SyntaxError, UnicodeError, LookupError, RecursionError) as exc:
        row.update(status="ERROR", error=type(exc).__name__, error_line=getattr(exc, "lineno", None))
    row["cache_hit"] = False
    return row


def scan(roots, workers=6, previous=None):
    files, issues = enumerate_inputs(roots)
    cached = {(r["root_id"], r["path"], r.get("sha256"), PARSER_REVISION): r for r in (previous or {}).get("files", []) if r.get("status") != "ERROR"}
    with ThreadPoolExecutor(max_workers=budget(workers)["workers"]) as pool:
        rows = list(pool.map(lambda item: analyze_one(item, cached), files))
    rows.sort(key=lambda x: (x["root_id"], x["path"]))
    nodes = [dict(n, root_id=r["root_id"], path=r["path"], system=r["system"], file_sha256=r.get("sha256")) for r in rows for n in r["nodes"]]
    seen = collections.Counter(n["node_id"] for n in nodes)
    duplicates = [key for key, value in seen.items() if value > 1]
    # Only unambiguous same-root module basenames produce edges. Dynamic imports remain unknown.
    names = collections.defaultdict(list)
    for row in rows:
        if row["path"].endswith(".py"):
            names[(row["root_id"], Path(row["path"]).stem)].append(row["path"])
    edges = []
    for row in rows:
        for imported in row["imports"]:
            targets = names.get((row["root_id"], imported.split(".")[-1]), [])
            if len(targets) == 1:
                edges.append({"root_id": row["root_id"], "from": row["path"], "to": targets[0], "kind": "STATIC_IMPORT_CANDIDATE"})
    errors = sum(r["status"] == "ERROR" for r in rows) + sum(i["severity"] == "RED" for i in issues) + len(duplicates)
    result = {"parser": PARSER_REVISION, "files": rows, "nodes": nodes, "edges": edges, "issues": issues,
              "duplicate_node_ids": duplicates, "scope": "READ_ONLY_STATIC_INPUTS; target runtime not executed",
              "quantity": {"enumerated": len(files), "recorded": len(rows), "python": sum(r["path"].endswith(".py") for r in rows), "parsed": sum(r["status"] == "PARSED" for r in rows), "nodes": len(nodes), "errors": errors, "cache_hits": sum(r["cache_hit"] for r in rows)},
              "resource_budget": budget(workers), "status": "RED" if errors else "YELLOW",
              "coverage_note": "Python AST + compile only; PS requires native PowerShell Parser; no runtime coverage claim."}
    result["input_fingerprint"] = digest([{k: r.get(k) for k in ("root_id", "path", "sha256", "status")} for r in rows])
    return result
