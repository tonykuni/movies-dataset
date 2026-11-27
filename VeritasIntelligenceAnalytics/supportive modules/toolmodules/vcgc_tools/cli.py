#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""One entry, modular verbs, read-only source review. [VIA:ACCEL-BRIDGE]"""
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

MAX_ROUNDS = 3

import argparse
import sys
import webbrowser
from pathlib import Path
from .core import VERBS, encode, event, is_link, load_json, new_run, now, write_new
from .inventory import scan
from .actions import catalog, compact_context, compare, duckdb_schema, graph_mermaid, module_check, registration_plan, skills_index, token_metrics
from .report import matrices, render


def parse_roots(values):
    roots = []
    for index, value in enumerate(values or []):
        label, path = value.split("=", 1) if "=" in value else ("root" + str(index + 1), value)
        if not label or any(label == x[0] for x in roots):
            raise ValueError("ROOT_ID_MISSING_OR_DUPLICATE")
        original = Path(path).expanduser()
        if original.exists() and is_link(original):
            raise ValueError("ROOT_LINK_REJECTED")
        roots.append((label, original.resolve()))
    return roots


def main(argv=None):
    package = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="VCGC 模組化補強：唯讀來源、run-local 輸出；不改正本")
    parser.add_argument("verb", choices=VERBS)
    parser.add_argument("--root", action="append", help="StableName=path; repeat for multiple roots")
    parser.add_argument("--out", default=str(Path.home() / "VIA_ToolModules_Runs"))
    parser.add_argument("--input")
    parser.add_argument("--before")
    parser.add_argument("--query", default="")
    parser.add_argument("--budget", type=int, default=12000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--rounds", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--open-html", action="store_true")
    args = parser.parse_args(argv)
    try:
        roots = parse_roots(args.root)
        if args.verb in ("panorama", "skills") and not roots:
            raise ValueError("AT_LEAST_ONE_EXPLICIT_ROOT_REQUIRED")
        read_inputs = [Path(value).resolve().parent for value in (args.input, args.before) if value]
        run = new_run(args.out, [p for _, p in roots] + read_inputs)
        tools = catalog(package)
        head = event(run, "START", {"verb": args.verb, "version": "v0100", "roots": [str(p) for _,p in roots]})
        result, code = {}, 0
        if args.verb == "panorama":
            previous = None
            rounds = []
            for number in range(1, args.rounds + 1):
                print(f"def [{number}/{args.rounds}] AST / contract scan", flush=True)
                snapshot = scan(roots, args.workers, previous)
                delta = compare(previous, snapshot) if previous else None
                folder = run / f"round_{number}"
                write_new(folder / "snapshot.json", snapshot)
                write_new(folder / "matrices.json", matrices(snapshot, tools, number, delta))
                write_new(folder / "Matrix.html", render(snapshot, tools, number, delta))
                if delta is not None:
                    write_new(folder / "delta.json", delta)
                head = event(run, "ROUND", {"round": number, "fingerprint": snapshot["input_fingerprint"], "quantity": snapshot["quantity"], "source_mutated": False}, head)
                rounds.append({"round": number, "status": snapshot["status"], "quantity": snapshot["quantity"], "source_mutated": False, "kind": "STATIC_RESCAN_NOT_SOURCE_REPAIR"})
                previous = snapshot
            write_new(run / "Context_Card.json", compact_context(snapshot, args.query, args.budget))
            write_new(run / "Registration_Proposal.json", registration_plan(tools, package))
            write_new(run / "Tool_Catalog.json", tools)
            html = run / f"round_{args.rounds}" / "Matrix.html"
            result = {"status": snapshot["status"], "rounds": rounds, "html": str(html), "central_registration": "PENDING", "external_activation": False, "windows_runtime": "NOT_TESTED", "celeritas_15": "NOT_VERIFIED", "audit_head": head}
            code = 2 if snapshot["quantity"]["errors"] else 0
            if args.open_html:
                result["browser_open_requested"] = webbrowser.open(html.as_uri())
        elif args.verb == "catalog":
            result = {"tools": tools, "count": len(tools)}
        elif args.verb == "registration-plan":
            result = registration_plan(tools, package)
        elif args.verb == "skills":
            result = skills_index(scan(roots, args.workers), roots)
        else:
            if not args.input:
                raise ValueError("INPUT_REQUIRED")
            if args.verb == "context":
                result = compact_context(load_json(args.input), args.query, args.budget)
            elif args.verb == "module-check":
                result = module_check(args.input)
            elif args.verb == "metrics":
                result = token_metrics(args.input)
                code = 2 if result["status"] == "INVALID" else 0
            elif args.verb == "schema":
                result = duckdb_schema(args.input)
                code = 2 if result["status"] == "DEPENDENCY_UNAVAILABLE" else 0
            elif args.verb == "compare":
                if not args.before:
                    raise ValueError("BEFORE_REQUIRED")
                result = compare(load_json(args.before), load_json(args.input))
            elif args.verb == "graph":
                write_new(run / "Dependencies.mmd", graph_mermaid(load_json(args.input)))
                result = {"status": "EXPORTED_STATIC_IMPORT_CANDIDATES", "path": str(run / "Dependencies.mmd"), "graphify_executed": False}
        write_new(run / "result.json", result)
        event(run, "FINISH", {"exit_code": code, "result": "result.json"}, head)
        print(encode({"run": str(run), "result": str(run / "result.json"), "exit_code": code}).decode("utf-8"))
        return code
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(encode({"status": "ERROR", "error": str(exc)}).decode("utf-8"), file=sys.stderr)
        return 2
