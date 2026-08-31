# ---------------------------------------------------------------------
# VIA_Accel20_Analyzer_v0100
# Accelerators 01-15 (analysis layer). 16-20 live in the PowerShell layer.
#
# Honest labelling rule: every accelerator reports what it actually
# computed. Anything heuristic is tagged HEURISTIC in its own output so a
# green light never overstates the evidence behind it.
# ---------------------------------------------------------------------

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

ANALYZER = "VIA_Accel20_Analyzer"
VERSION = "v0100"

SUBSYSTEM_HINTS = [
    ("VRN", re.compile(r"\bVRN[_-]|resonance|report_?pipeline|pdf_?(text|table)|nlp", re.I)),
    ("VDF", re.compile(r"\bVDF[_-]|dataforge|pricedaily|flowchip|backtest|revenue|valuation", re.I)),
    ("VAP", re.compile(r"\bVAP[_-]|autoplot|workbench|dashboard|plotly", re.I)),
    ("VETF", re.compile(r"\bVETF[_-]|etf", re.I)),
    ("CGE", re.compile(r"governance|registry|ssot|central", re.I)),
]

PROGRESS = []


def note(stage: str, msg: str):
    line = "{0}|{1}".format(stage, msg)
    PROGRESS.append(line)
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 18), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------
# staging: expand zips into the run directory, never into the mother tree
# ---------------------------------------------------------------------

def stage_sources(sources, stage_dir: Path) -> list:
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged = []
    for s in sources:
        p = Path(s)
        if not p.exists():
            staged.append({"source": s, "kind": "MISSING", "root": "", "error": "not found"})
            continue
        if p.suffix.lower() == ".zip":
            dest = stage_dir / p.stem.replace(" ", "_")
            try:
                with zipfile.ZipFile(p) as zf:
                    zf.extractall(dest)
                staged.append({"source": s, "kind": "ZIP", "root": str(dest), "error": ""})
            except Exception as exc:
                staged.append({"source": s, "kind": "ZIP", "root": "", "error": str(exc)})
        else:
            dest = stage_dir / "_loose"
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / p.name
            target.write_bytes(p.read_bytes())
            staged.append({"source": s, "kind": "FILE", "root": str(target), "error": ""})
    return staged


def collect_files(staged) -> list:
    out = []
    for entry in staged:
        root = entry.get("root") or ""
        if not root:
            continue
        rp = Path(root)
        if rp.is_file():
            out.append({"path": rp, "origin": entry["source"]})
        else:
            for f in rp.rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts:
                    out.append({"path": f, "origin": entry["source"]})
    return out


# --- A01 AST precision parser ----------------------------------------

def a01_ast(files) -> dict:
    parsed = 0
    errors = []
    trees = {}
    for item in files:
        f = item["path"]
        if f.suffix.lower() != ".py":
            continue
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
            trees[str(f)] = ast.parse(src, filename=str(f))
            parsed += 1
        except SyntaxError as exc:
            errors.append({
                "file": str(f), "line": exc.lineno or 0, "col": exc.offset or 0,
                "msg": str(exc.msg), "class": "SYNTAX",
            })
        except Exception as exc:
            errors.append({"file": str(f), "line": 0, "col": 0, "msg": str(exc), "class": "READ"})
    return {"status": "PASS" if not errors else "RED", "mode": "EXACT",
            "parsed": parsed, "errors": errors, "_trees": trees}


# --- A02 cross-language semantic inventory ---------------------------

PS_FUNC = re.compile(r"^\s*function\s+([A-Za-z0-9_\-]+)", re.I | re.M)
PS_PARAM = re.compile(r"^\s*param\s*\(", re.I | re.M)
PS_ALIAS = re.compile(r"(?<![\w\-])(ls|cat|rm|cp|mv|gci|%|\?)(?=\s)", re.M)


def a02_semantics(files, trees) -> dict:
    py_funcs = 0
    py_classes = 0
    ps_files = 0
    ps_funcs = 0
    alias_hits = []
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                py_funcs += 1
            elif isinstance(node, ast.ClassDef):
                py_classes += 1
    for item in files:
        f = item["path"]
        if f.suffix.lower() not in (".ps1", ".psm1"):
            continue
        ps_files += 1
        src = f.read_text(encoding="utf-8", errors="replace")
        ps_funcs += len(PS_FUNC.findall(src))
        for m in PS_ALIAS.finditer(src):
            alias_hits.append({"file": str(f), "alias": m.group(1),
                               "line": src[: m.start()].count("\n") + 1})
    return {"status": "PASS", "mode": "EXACT",
            "python_functions": py_funcs, "python_classes": py_classes,
            "powershell_files": ps_files, "powershell_functions": ps_funcs,
            "alias_violations": alias_hits[:50], "alias_violation_count": len(alias_hits)}


# --- A03 hydra risk (heuristic, declared as such) ---------------------

def build_import_graph(trees) -> dict:
    mods = {}
    for path in trees:
        mods[Path(path).stem] = path
    graph = defaultdict(set)
    for path, tree in trees.items():
        me = Path(path).stem
        graph[me]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    root = a.name.split(".")[0]
                    if root in mods:
                        graph[me].add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in mods:
                        graph[me].add(root)
    return {k: sorted(v) for k, v in graph.items()}


def a03_hydra(graph) -> dict:
    fan_in = defaultdict(int)
    for src, dsts in graph.items():
        for d in dsts:
            fan_in[d] += 1
    nodes = []
    for n in graph:
        out_deg = len(graph[n])
        in_deg = fan_in.get(n, 0)
        # coupling proxy only: a module many others import is expensive to change
        score = round(min(1.0, (in_deg * 0.18) + (out_deg * 0.05)), 3)
        band = "LOW"
        if score >= 0.60:
            band = "HIGH"
        elif score >= 0.30:
            band = "MEDIUM"
        nodes.append({"module": n, "fan_in": in_deg, "fan_out": out_deg,
                      "risk": score, "band": band})
    nodes.sort(key=lambda r: -r["risk"])
    high = [n for n in nodes if n["band"] == "HIGH"]
    return {"status": "PASS" if not high else "YELLOW", "mode": "HEURISTIC",
            "basis": "import fan-in/fan-out only; not a runtime blast-radius proof",
            "nodes": nodes[:60], "high_risk": [n["module"] for n in high]}


# --- A04 dependency topology -----------------------------------------

def a04_topology(graph) -> dict:
    indeg = {n: 0 for n in graph}
    for n in graph:
        for d in graph[n]:
            indeg[d] = indeg.get(d, 0)
    for n in graph:
        for d in graph[n]:
            indeg[n] = indeg.get(n, 0)
    # edge direction: n depends on d, so d must come first
    incoming = defaultdict(int)
    for n in graph:
        for d in graph[n]:
            incoming[n] += 1
    for n in graph:
        incoming.setdefault(n, 0)
    q = deque(sorted([n for n in graph if incoming[n] == 0]))
    order = []
    live = dict(incoming)
    dependents = defaultdict(list)
    for n in graph:
        for d in graph[n]:
            dependents[d].append(n)
    while q:
        n = q.popleft()
        order.append(n)
        for m in sorted(dependents.get(n, [])):
            live[m] -= 1
            if live[m] == 0:
                q.append(m)
    cyclic = sorted([n for n in graph if n not in order])
    return {"status": "PASS" if not cyclic else "RED", "mode": "EXACT",
            "order": order, "cycles_detected": cyclic,
            "nodes": len(graph), "edges": sum(len(v) for v in graph.values())}


# --- A05 sandbox isolation -------------------------------------------

def a05_sandbox(files) -> dict:
    checked = 0
    failures = []
    for item in files:
        f = item["path"]
        if f.suffix.lower() != ".py":
            continue
        checked += 1
        proc = subprocess.run(
            [sys.executable, "-I", "-m", "py_compile", str(f)],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            failures.append({"file": str(f), "stderr": (proc.stderr or "").strip()[:300]})
    return {"status": "PASS" if not failures else "RED", "mode": "EXACT",
            "basis": "isolated py_compile subprocess; not an import-time or runtime execution",
            "checked": checked, "failures": failures}


# --- A06 auto-fix suggestions (never applied automatically) -----------

def a06_fixes(files) -> dict:
    sugg = []
    for item in files:
        f = item["path"]
        if f.suffix.lower() not in (".py", ".ps1", ".psm1", ".json", ".md", ".txt", ".csv"):
            continue
        try:
            raw = f.read_bytes()
        except Exception:
            continue
        if raw.startswith(b"\xef\xbb\xbf") and f.suffix.lower() in (".py", ".ps1", ".psm1"):
            sugg.append({"file": str(f), "issue": "UTF8_BOM",
                         "fix": "rewrite with UTF8Encoding($false)", "class": "Parallel-Fixable"})
        if b"\r\n" in raw and b"\n" in raw.replace(b"\r\n", b""):
            sugg.append({"file": str(f), "issue": "MIXED_LINE_ENDINGS",
                         "fix": "normalise to a single convention", "class": "Parallel-Fixable"})
        if f.suffix.lower() == ".py":
            text = raw.decode("utf-8", "replace")
            if "\t" in text:
                sugg.append({"file": str(f), "issue": "TAB_INDENT",
                             "fix": "convert tabs to 4 spaces", "class": "Parallel-Fixable"})
    return {"status": "PASS" if not sugg else "YELLOW", "mode": "EXACT",
            "policy": "suggestions only; nothing is rewritten without an explicit GO token",
            "suggestions": sugg[:80], "count": len(sugg)}


# --- A08 SSOT alignment (fail-closed) --------------------------------

CODE_RE = re.compile(r"\b(ENG|MDL|SPT|FNT|SYS|SPJ)-?(\d{3})\b")


def a08_ssot(files, mother_root: Path) -> dict:
    registry = None
    reg_path = mother_root / "supportive modules" / "registry" / "VIA_AutoCode_Registry_v0100.json"
    if reg_path.exists():
        try:
            registry = json.loads(reg_path.read_text(encoding="utf-8"))
        except Exception:
            registry = None
    declared = defaultdict(set)
    for item in files:
        f = item["path"]
        if f.suffix.lower() not in (".py", ".ps1", ".md", ".json"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in CODE_RE.finditer(text):
            declared[m.group(1)].add(int(m.group(2)))
    summary = {k: sorted(v) for k, v in declared.items()}
    if registry is None:
        return {"status": "YELLOW", "mode": "EXACT", "verdict": "REGISTRY_ABSENT",
                "note": "no registry found; alignment is unproven, not 100%",
                "declared_codes": summary, "collisions": [], "registry_current": {}}
    cats = registry.get("categories", {})
    current = {v.get("prefix"): v.get("current") for v in cats.values() if isinstance(v, dict)}
    collisions = []
    for prefix, nums in declared.items():
        cur = current.get(prefix)
        if cur is None:
            continue
        for n in nums:
            if n <= int(cur):
                collisions.append({"code": "{0}-{1:03d}".format(prefix, n),
                                   "registry_current": cur, "verdict": "ALREADY_ALLOCATED"})
    return {"status": "PASS" if not collisions else "RED", "mode": "EXACT",
            "verdict": "REGISTRY_PRESENT", "declared_codes": summary,
            "collisions": collisions, "registry_current": current}


# --- A11 complexity ---------------------------------------------------

BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                ast.With, ast.AsyncWith, ast.BoolOp, ast.IfExp)


def a11_complexity(trees) -> dict:
    rows = []
    for path, tree in trees.items():
        loc = len(Path(path).read_text(encoding="utf-8", errors="replace").splitlines())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = 1 + sum(1 for c in ast.walk(node) if isinstance(c, BRANCH_NODES))
                if cc >= 12:
                    rows.append({"file": Path(path).name, "function": node.name,
                                 "cyclomatic": cc, "line": node.lineno})
        rows.append({"file": Path(path).name, "function": "<module>", "cyclomatic": 0, "loc": loc})
    hot = sorted([r for r in rows if r.get("cyclomatic", 0) >= 12],
                 key=lambda r: -r["cyclomatic"])[:30]
    return {"status": "PASS" if not hot else "YELLOW", "mode": "EXACT",
            "basis": "branch-node count per function (McCabe approximation)",
            "hotspots": hot}


# --- A12 subsystem routing -------------------------------------------

def a12_routing(files) -> dict:
    routes = []
    for item in files:
        f = item["path"]
        if f.suffix.lower() not in (".py", ".ps1", ".json", ".md", ".csv", ".html"):
            continue
        probe = f.name
        try:
            probe = probe + "\n" + f.read_text(encoding="utf-8", errors="replace")[:4000]
        except Exception:
            pass
        target = "OTHERS"
        for name, rx in SUBSYSTEM_HINTS:
            if rx.search(probe):
                target = name
                break
        routes.append({"file": f.name, "subsystem": target, "path": str(f)})
    tally = defaultdict(int)
    for r in routes:
        tally[r["subsystem"]] += 1
    return {"status": "PASS", "mode": "HEURISTIC",
            "basis": "filename and first 4KB keyword match; confirm before placement",
            "routes": routes, "tally": dict(tally)}


# --- A13 version diff against the mother tree ------------------------

def build_mother_index(mother_root: Path) -> dict:
    idx = {}
    if not mother_root.is_dir():
        return idx
    opts_skip = {".git", "__pycache__", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(mother_root):
        dirnames[:] = [d for d in dirnames if d not in opts_skip]
        for fn in filenames:
            idx.setdefault(fn.lower(), []).append(str(Path(dirpath) / fn))
    return idx


def a13_diff(files, mother_index: dict) -> dict:
    rows = []
    for item in files:
        f = item["path"]
        hits = mother_index.get(f.name.lower(), [])
        if not hits:
            rows.append({"file": f.name, "verdict": "NEW", "existing": "", "note": ""})
            continue
        mine = sha256_file(f)
        identical = ""
        for h in hits:
            try:
                if sha256_file(Path(h)) == mine:
                    identical = h
                    break
            except Exception:
                continue
        if identical:
            rows.append({"file": f.name, "verdict": "IDENTICAL", "existing": identical, "note": "skip"})
        else:
            rows.append({"file": f.name, "verdict": "CONFLICT", "existing": hits[0],
                         "note": "same name, different content -> versioned sibling"})
    tally = defaultdict(int)
    for r in rows:
        tally[r["verdict"]] += 1
    return {"status": "PASS" if tally.get("CONFLICT", 0) == 0 else "YELLOW", "mode": "EXACT",
            "rows": rows, "tally": dict(tally)}


# --- A14 coverage / regression ---------------------------------------

def a14_regression(files, stage_dir: Path) -> dict:
    tests = [str(i["path"]) for i in files
             if i["path"].name.startswith("test_") and i["path"].suffix == ".py"]
    if not tests:
        return {"status": "YELLOW", "mode": "EXACT", "verdict": "NO_TESTS_BUNDLED",
                "note": "no test_*.py shipped with these artifacts; regression is unproven",
                "tests": [], "passed": 0, "failed": 0, "output": ""}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"] + tests,
                          capture_output=True, text=True, cwd=str(stage_dir), timeout=900)
    tail = (proc.stdout or "")[-2500:]
    passed = len(re.findall(r"(\d+) passed", tail))
    return {"status": "PASS" if proc.returncode == 0 else "RED", "mode": "EXACT",
            "verdict": "EXECUTED", "tests": tests,
            "returncode": proc.returncode, "output": tail}


# --- A10 / A15 classification and fix order ---------------------------

def a10_classify(a01, a05, a06, a08, a13) -> dict:
    parallel = []
    sequence = []
    for s in a06.get("suggestions", []):
        parallel.append({"item": s["file"], "issue": s["issue"], "class": "Parallel-Fixable"})
    for e in a01.get("errors", []):
        sequence.append({"item": e["file"], "issue": "SYNTAX@{0}".format(e["line"]),
                         "class": "Sequence-Dependent"})
    for f in a05.get("failures", []):
        sequence.append({"item": f["file"], "issue": "COMPILE_FAIL", "class": "Sequence-Dependent"})
    for c in a08.get("collisions", []):
        sequence.append({"item": c["code"], "issue": "CODE_COLLISION", "class": "Sequence-Dependent"})
    for r in a13.get("rows", []):
        if r["verdict"] == "CONFLICT":
            sequence.append({"item": r["file"], "issue": "NAME_CONFLICT", "class": "Sequence-Dependent"})
    return {"status": "PASS", "mode": "EXACT",
            "parallel_fixable": parallel, "sequence_dependent": sequence,
            "counts": {"parallel": len(parallel), "sequence": len(sequence)}}


def a15_fix_order(a04, a10) -> dict:
    steps = []
    for i, p in enumerate(a10["parallel_fixable"], start=1):
        steps.append({"round": 1, "seq": i, "item": p["item"], "issue": p["issue"], "mode": "PARALLEL"})
    order = a04.get("order", [])
    rank = {m: i for i, m in enumerate(order)}
    seq = sorted(a10["sequence_dependent"], key=lambda s: rank.get(Path(s["item"]).stem, 9999))
    for i, s in enumerate(seq, start=1):
        steps.append({"round": 2, "seq": i, "item": s["item"], "issue": s["issue"], "mode": "TOPOLOGICAL"})
    return {"status": "PASS", "mode": "EXACT", "steps": steps,
            "round3": "formatting, dead-code removal and hardening are proposed only"}


# ---------------------------------------------------------------------
# three-round driver
# ---------------------------------------------------------------------

def run_round(rnd: int, files, mother_root: Path, mother_index, stage_dir: Path) -> dict:
    note("A01", "round {0} AST parse".format(rnd))
    a01 = a01_ast(files)
    trees = a01.pop("_trees")
    note("A02", "round {0} cross-language inventory".format(rnd))
    a02 = a02_semantics(files, trees)
    graph = build_import_graph(trees)
    note("A03", "round {0} hydra coupling".format(rnd))
    a03 = a03_hydra(graph)
    note("A04", "round {0} topology".format(rnd))
    a04 = a04_topology(graph)
    note("A05", "round {0} sandbox compile".format(rnd))
    a05 = a05_sandbox(files)
    note("A06", "round {0} fix suggestions".format(rnd))
    a06 = a06_fixes(files)
    note("A08", "round {0} SSOT alignment".format(rnd))
    a08 = a08_ssot(files, mother_root)
    note("A11", "round {0} complexity".format(rnd))
    a11 = a11_complexity(trees)
    note("A12", "round {0} subsystem routing".format(rnd))
    a12 = a12_routing(files)
    note("A13", "round {0} version diff".format(rnd))
    a13 = a13_diff(files, mother_index)
    if rnd == 1:
        note("A14", "round 1 regression")
        a14 = a14_regression(files, stage_dir)
    else:
        a14 = {"status": "SKIPPED", "mode": "EXACT", "verdict": "RUN_ONCE_IN_ROUND_1"}
    a10 = a10_classify(a01, a05, a06, a08, a13)
    a15 = a15_fix_order(a04, a10)
    return {"round": rnd, "A01": a01, "A02": a02, "A03": a03, "A04": a04, "A05": a05,
            "A06": a06, "A08": a08, "A10": a10, "A11": a11, "A12": a12, "A13": a13,
            "A14": a14, "A15": a15}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VIA 20-accelerator import analyzer")
    ap.add_argument("--sources", nargs="+", required=True)
    ap.add_argument("--mother-root", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--emit", required=True)
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    run_dir = Path(args.run_dir)
    stage_dir = run_dir / "_staged"
    mother_root = Path(args.mother_root)

    note("A20", "staging sources")
    staged = stage_sources(args.sources, stage_dir)
    files = collect_files(staged)
    note("A20", "staged {0} files".format(len(files)))

    note("A13", "indexing mother tree")
    mother_index = build_mother_index(mother_root)
    note("A13", "mother index {0} names".format(len(mother_index)))

    rounds = []
    for r in (1, 2, 3):
        note("A07", "panoramic round {0}/3".format(r))
        rounds.append(run_round(r, files, mother_root, mother_index, stage_dir))

    final = rounds[-1]
    regression = rounds[0]["A14"]
    final["A14"] = regression
    blockers = []
    if final["A01"]["errors"]:
        blockers.append("AST syntax errors")
    if final["A05"]["failures"]:
        blockers.append("sandbox compile failures")
    if final["A08"].get("collisions"):
        blockers.append("registry code collisions")
    if regression["status"] == "RED":
        blockers.append("bundled regression tests failed")
    overall = "GREEN"
    if blockers:
        overall = "RED"
    elif (final["A13"]["tally"].get("CONFLICT", 0) or final["A06"]["count"]
          or final["A08"]["status"] == "YELLOW" or regression["status"] == "YELLOW"):
        overall = "YELLOW"

    payload = {
        "analyzer": ANALYZER, "version": VERSION,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mother_root": str(mother_root),
        "run_dir": str(run_dir),
        "staged": staged,
        "file_count": len(files),
        "rounds": rounds,
        "overall": overall,
        "blockers": blockers,
        "elapsed_s": round(time.perf_counter() - t0, 2),
        "progress": PROGRESS,
    }
    Path(args.emit).parent.mkdir(parents=True, exist_ok=True)
    Path(args.emit).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                               encoding="utf-8", newline="\n")
    note("DONE", "overall={0}".format(overall))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
