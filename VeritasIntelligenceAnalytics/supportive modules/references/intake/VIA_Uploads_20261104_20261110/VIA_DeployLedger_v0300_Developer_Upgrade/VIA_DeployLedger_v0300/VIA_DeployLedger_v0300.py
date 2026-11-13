from __future__ import annotations
"""VeritasDeployLedger 3.0.0 — developer-only, copy-first commercial release factory.

VIA:ACCEL-BRIDGE: resource budget + bounded streams + governed external bridge.
No installer bypasses VCGC. No successful plan is described as a built release.
"""

# def PART 1 — parameters / imports
VERSION = "3.0.0"
SCHEMA = "via.deploy-contract.v3"
LEGACY_NAME = "VIA_HybridEdgeCloud_AllInOne_v0200"
MAX_FILE_BYTES = 1024 * 1024 * 1024
MAX_FILES = 100000
CHUNK = 1024 * 1024
TIMEOUT = 180
BUILD_TIMEOUT = 7200
MAX_LOG_BYTES = 8 * 1024 * 1024
CPU_LIMIT = 4
MIN_FREE_BYTES = 2 * 1024 * 1024 * 1024
SOURCE_SUFFIXES = {".py", ".pyw", ".pyc", ".pyo", ".ps1", ".psm1", ".psd1"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".sqlite", ".duckdb", ".parquet"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
COMPONENTS = {"VCGC", "VRN", "VDF"}
REQUIRED_TOOL_ROLES = {"accelerator", "network", "environment", "registry", "ssot"}
RUNTIME_ROOTS = {
    "def_enforce_module_guard_from_environment", "def_launch_guarded_executable",
    "def_create_activation_request", "def_get_or_create_device_key",
    "def_store_product_key_state", "def_load_hardware_hashes",
    "def_load_product_key_state", "def_load_device_private_key",
    "def_load_trusted_public_key", "def_read_json", "def_write_json",
    "def_create_module_handshake", "def_verify_license", "def_public_key_raw_b64",
    "def_verify_package_tree_manifest", "def_collect_package_tree",
    "def_file_lock", "def_sha256_file", "def_verify_signed_payload",
    "def_verify_activation_request", "def_b64u_decode",
}
AUTHORITY_FORBIDDEN = {
    "def_issue_license", "def_generate_ed25519_keypair", "def_load_private_key",
    "def_create_product_record", "def_dispatch", "def_package_plan",
    "def_sign_module_manifest", "def_sign_package_tree_manifest",
}

import argparse
import ast
import contextlib
import hashlib
import html
import importlib.util
import json
import os
import platform
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def read(path):
    p = Path(path)
    if p.stat().st_size > MAX_LOG_BYTES:
        raise ValueError("JSON exceeds limit")
    return json.loads(p.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicates)


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".vdl-", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def now():
    return datetime.now(timezone.utc).isoformat()


def legacy():
    if LEGACY_NAME in sys.modules:
        return sys.modules[LEGACY_NAME]
    p = Path(__file__).parent / "legacy" / (LEGACY_NAME + ".py")
    spec = importlib.util.spec_from_file_location(LEGACY_NAME, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[LEGACY_NAME] = module
    spec.loader.exec_module(module)
    return module


def safe_rel(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Invalid relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")):
        raise ValueError("Unsafe relative path: " + value)
    for x in p.parts:
        if x.endswith((".", " ")) or x.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM"+str(i) for i in range(1,10)), *("LPT"+str(i) for i in range(1,10))}:
            raise ValueError("Windows reserved path")
    return value


def below(root, relative):
    root = Path(root).resolve()
    relative = safe_rel(relative)
    p = root / relative
    for parent in [p, *p.parents]:
        if parent == root:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Link/junction not allowed")
    if not p.resolve().is_relative_to(root):
        raise ValueError("Path escaped root")
    return p


def disjoint(a, b):
    a, b = Path(a).resolve(), Path(b).resolve()
    if a == b or a in b.parents or b in a.parents:
        raise ValueError("Source, staging, state and output must not overlap")


def tree(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    rows, folded = [], set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for name in dirs + files:
            p = Path(directory) / name
            if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
                raise ValueError("Source link/junction: " + str(p))
        for name in sorted(files):
            p = Path(directory) / name
            rel = safe_rel(p.relative_to(root).as_posix())
            if rel.casefold() in folded:
                raise ValueError("Case-insensitive file collision: " + rel)
            folded.add(rel.casefold())
            size = p.stat().st_size
            if size > MAX_FILE_BYTES or len(rows) >= MAX_FILES:
                raise ValueError("Inventory limit exceeded; no partial baseline")
            rows.append({"path": rel, "size": size, "sha256": sha(p)})
    if not rows:
        raise ValueError("Empty source tree")
    return sorted(rows, key=lambda r: r["path"])


def resource_env():
    threads = str(max(1, min(CPU_LIMIT, (os.cpu_count() or 2) // 2)))
    env = os.environ.copy()
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[key] = threads
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONUTF8="1")
    env.pop("PYTHONPATH", None)
    return env


def run(argv, cwd, timeout=TIMEOUT, extra_env=None):
    if not argv or any(not isinstance(x, str) or "\x00" in x for x in argv):
        raise ValueError("Command must be a string argv array")
    env = resource_env()
    env.update(extra_env or {})
    # Existing bounded runner limits streams, terminates children on timeout.
    return legacy().def_run_subprocess_bounded(argv, cwd=Path(cwd), env=env, timeout_seconds=timeout, max_output_bytes=MAX_LOG_BYTES)


def validate_contract(c):
    if c.get("schema") != SCHEMA or c.get("platform") != "Windows":
        raise ValueError("Windows deploy contract v3 required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", c.get("release_id", "")):
        raise ValueError("Invalid release_id")
    units = c.get("units", [])
    if not units or not any(x.get("component") == "VRN" for x in units):
        raise ValueError("At least one VRN unit is required")
    ids = set()
    for u in units:
        uid = u.get("id", "")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", uid) or uid in ids:
            raise ValueError("Duplicate/invalid unit id")
        ids.add(uid)
        if u.get("component") not in COMPONENTS:
            raise ValueError("Unknown component")
        safe_rel(u["entry"])
        if not u["entry"].endswith(".py"):
            raise ValueError("Native build entry must be Python")
        if not u.get("smoke_args") or not isinstance(u["smoke_args"], list):
            raise ValueError("Each unit requires explicit smoke_args")
        if not u.get("success_regex"):
            raise ValueError("Semantic smoke success_regex is required")
        re.compile(u["success_regex"])
        if u.get("closure_reviewed") is not True:
            raise ValueError("Dynamic imports/subprocess/data closure not yet reviewed: " + uid)
    roles = {t.get("role") for t in c.get("tools", [])}
    if not REQUIRED_TOOL_ROLES <= roles:
        raise ValueError("Missing governed tools: " + str(sorted(REQUIRED_TOOL_ROLES - roles)))
    for t in c["tools"]:
        if not re.fullmatch(r"[0-9a-f]{64}", t.get("sha256", "")):
            raise ValueError("Every tool must be pinned by SHA256")
    targets = set()
    for a in c.get("assets", []):
        target = safe_rel(a["target"])
        if not target.startswith("Assets/") or target.casefold() in targets:
            raise ValueError("Bundled native tool/model target must be unique under Assets/")
        targets.add(target.casefold())
        if a.get("redistribution_reviewed") is not True or not a.get("license_notice"):
            raise ValueError("Bundled third-party tools/models require reviewed redistribution and a notice")
        if not re.fullmatch(r"[0-9a-f]{64}", a.get("sha256", "")):
            raise ValueError("Bundled native tool/model hash required")
    if not c.get("vcgc", {}).get("audit"):
        raise ValueError("VCGC semantic conflict audit adapter required")
    if not c.get("accelerator", {}).get("command"):
        raise ValueError("Governed accelerator bridge probe required")
    if not c.get("readiness"):
        raise ValueError("Real component closeout evidence is required")
    if not {u["component"] for u in units} <= {r.get("component") for r in c["readiness"]}:
        raise ValueError("Every shipped component requires its own closeout evidence")
    for record in c["readiness"]:
        if not record.get("pass_values") or any(x not in {"PASS", "GREEN", "CLOSED"} for x in record["pass_values"]):
            raise ValueError("OPEN/BLOCKED/REVIEW/DATA_GAP cannot be promoted as a successful baseline")
    return c


def discover(output, roots=None):
    home = Path.home()
    roots = roots or [home / "Github/VIA-VDF-VRN", home / "OneDrive/Documents/movies-dataset/VeritasIntelligenceAnalytics", home / "Downloads/VeritasIntelligenceAnalytics"]
    patterns = ["ActivateVRN-2*.py", "VIA_ToolVersion_Lock*.json", "CGC_MDL056_InstallGate_v*.py", "CGC_MDL135_EnvGovernance_v*.py", "*VIA_ExecutionBridge*.py", "*SystemManager*.py"]
    found = []
    for value in roots:
        root = Path(value).expanduser()
        if not root.is_dir():
            continue
        for directory, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and x not in {"via_database", "VIA_Reports"}]
            for name in files:
                import fnmatch
                if any(fnmatch.fnmatch(name, pat) for pat in patterns):
                    p = Path(directory) / name
                    if not p.is_symlink():
                        found.append({"path": str(p), "sha256": sha(p)})
    envs = []
    for base in [home / "envs", *(Path(x) / "envs" for x in roots)]:
        if base.is_dir():
            for p in sorted(base.glob("*/Scripts/python.exe")):
                if p.parent.parent.name.startswith(("via_", "vrn2_")):
                    envs.append(str(p))
    closeouts = []
    for root in roots:
        rp = Path(root) / "VIA_Reports/vrn2/VRN2_CloseoutUI_latest.json"
        if rp.is_file():
            report = read(rp)
            closeouts.append({"path": str(rp), "sha256": sha(rp), "state": report.get("state"), "at": report.get("at"), "per_owner": report.get("per_owner", {}), "package": report.get("package"), "launcher": report.get("launcher")})
        ep = Path(root) / "VIA_Reports/vrn2/VRN2_Env_latest.json"
        if ep.is_file():
            actual_python = read(ep).get("python")
            if actual_python: envs.append(actual_python)
    result = {"status": "NEEDS_DEPLOY_CONTRACT", "captured_at": now(), "host": platform.system(), "files": found, "python_candidates": sorted(set(envs)), "observed_closeouts": closeouts, "baseline_sealed": False, "reason": "Inventory is not a deployable dependency closure; select real entrypoints and semantic tests in deploy_contract.json."}
    write(Path(output) / "discovery.json", result)
    render(result, Path(output) / "Deployment_Status.html")
    return result


def environment_probe(python, cwd):
    code = "import json,platform,struct,sys,importlib.metadata as m; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({'python':platform.python_version(),'bits':struct.calcsize('P')*8,'platform':platform.system(),'executable':sys.executable,'packages':[{'name':d.metadata['Name'],'version':d.version} for d in m.distributions()]}),encoding='utf-8')"
    with tempfile.TemporaryDirectory(prefix="vdl-probe-", dir=cwd) as temp:
        dest = Path(temp) / "environment.json"
        r = run([str(python), "-I", "-c", code, str(dest)], cwd)
        if not r["ok"] or not dest.is_file():
            raise RuntimeError("Environment probe failed: " + r["stderr_tail"][-400:])
        result = read(dest)
    names = [re.sub(r"[-_.]+", "-", x["name"].lower()) for x in result["packages"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate distribution in active environment")
    result["packages"].sort(key=lambda r: r["name"].lower())
    result["pip_check"] = run([str(python), "-I", "-m", "pip", "check"], cwd)
    return result


def native_hazards(source):
    """Identify source-file runtime assumptions that compilation alone cannot fix."""
    parsed = ast.parse(source)
    hazards = []
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if name.endswith(("spec_from_file_location", "runpy.run_path", "SourceFileLoader")):
            hazards.append({"line": node.lineno, "kind": "SOURCE_FILE_LOADER", "call": name})
        if name.endswith((".glob", ".rglob")) and any(isinstance(arg, ast.Constant) and isinstance(arg.value, str) and ".py" in arg.value for arg in node.args):
            hazards.append({"line": node.lineno, "kind": "SOURCE_FILENAME_DISCOVERY", "call": name})
        if name.startswith("subprocess.") and any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "sys" and n.attr == "executable" for arg in node.args for n in ast.walk(arg)):
            hazards.append({"line": node.lineno, "kind": "PYTHON_CHILD_RUNTIME", "call": name})
        if name.endswith("b64decode") and re.search(r"(?i)(runtime|payload|source|zip|engine)", ast.unparse(node)):
            hazards.append({"line": node.lineno, "kind": "EMBEDDED_PAYLOAD_REVIEW", "call": name})
    return hazards


def adapter(adapter_spec, cwd, receipt, expected_binding=None):
    """Execute an explicit VCGC command; require a fresh, nonce-bound receipt."""
    receipt = Path(receipt)
    receipt.unlink(missing_ok=True)
    nonce = secrets.token_hex(24)
    result = run(adapter_spec["command"], cwd, adapter_spec.get("timeout", 600), {"VIA_DEPLOY_RECEIPT": str(receipt.resolve()), "VIA_DEPLOY_NONCE": nonce, "VIA_DEPLOY_BINDING": expected_binding or ""})
    if not result["ok"] or not receipt.is_file():
        raise RuntimeError("VCGC adapter failed or did not write a fresh receipt")
    evidence = read(receipt)
    if evidence.get("nonce") != nonce or evidence.get("binding") != (expected_binding or "") or evidence.get("status") != "PASS":
        raise ValueError("VCGC receipt nonce/binding/status mismatch")
    if evidence.get("conflicts") != []:
        raise ValueError("VCGC conflicts remain or were not assessed")
    return {"result": result, "receipt": evidence, "receipt_sha256": sha(receipt)}


def audit(c, output):
    c = validate_contract(c)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    findings, units, tools, envs = [], [], [], {}
    for u in c["units"]:
        disjoint(u["source"], output)
        try:
            inventory = tree(u["source"])
            entry = below(u["source"], u["entry"])
            if not entry.is_file():
                raise FileNotFoundError(entry)
            syntax = []
            for item in inventory:
                p = below(u["source"], item["path"])
                if p.suffix == ".py":
                    source_text = p.read_text(encoding="utf-8-sig")
                    ast.parse(source_text, filename=str(p))
                    if any(pattern.search(source_text) for pattern in legacy().def_PARAM_SECRET_PATTERNS):
                        raise ValueError("Possible hardcoded credential/private key in source: " + item["path"])
                    hazards = native_hazards(source_text)
                    if hazards:
                        raise ValueError("Native runtime adapter required before source-free packaging: " + item["path"] + " " + json.dumps(hazards, ensure_ascii=False))
                    syntax.append(item["path"])
            py = str(Path(u["python"]).resolve())
            if py not in envs:
                envs[py] = environment_probe(py, output)
            env = envs[py]
            if env["platform"] != c["platform"] or env["bits"] != c.get("bits", 64) or not env["pip_check"]["ok"]:
                raise ValueError("Host/architecture/pip check does not meet deployment contract")
            stage = output / "source_smokes" / u["id"]
            copy_source(u["source"], stage, inventory)
            smoke = run([py, str(below(stage, u["entry"])), *u["smoke_args"]], stage, u.get("timeout", 600))
            text = smoke["stdout_tail"] + smoke["stderr_tail"]
            if not smoke["ok"] or not re.search(u["success_regex"], text):
                raise ValueError("Source smoke did not pass semantic criteria")
            if tree(stage) != inventory:
                raise ValueError("Source smoke wrote inside its immutable staged source; route outputs outside it")
            if tree(u["source"]) != inventory:
                raise ValueError("Source smoke modified the release source tree")
            units.append({"id": u["id"], "files": inventory, "tree_hash": digest(inventory), "ast_files": len(syntax), "smoke": smoke})
        except Exception as exc:
            findings.append({"owner": u["component"], "code": "UNIT_NOT_READY", "detail": str(exc)})
    for t in c["tools"]:
        try:
            if sha(t["path"]) != t["sha256"]:
                raise ValueError("Pinned tool changed")
            tools.append({k: t[k] for k in ("role", "path", "sha256")})
        except Exception as exc:
            findings.append({"owner": "VCGC", "code": "TOOL_LOCK", "detail": str(exc), "role": t["role"]})
    for asset in c.get("assets", []):
        try:
            legacy().def_validate_no_link_chain(Path(asset["source"]))
            if sha(asset["source"]) != asset["sha256"]:
                raise ValueError("Native tool/model content differs from lock")
        except Exception as exc:
            findings.append({"owner": "VCGC", "code": "ASSET_LOCK", "detail": str(exc)})
    readiness = []
    for record in c["readiness"]:
        try:
            rp = Path(record["path"])
            r = read(rp)
            status = r[record["status_field"]]
            if status not in record["pass_values"]:
                raise ValueError("Component closeout is " + str(status))
            if time.time() - rp.stat().st_mtime > record.get("max_age_hours", 24) * 3600:
                raise ValueError("Closeout evidence is stale")
            readiness.append({"path": str(rp), "sha256": sha(rp), "status": status, "component": record["component"]})
        except Exception as exc:
            findings.append({"owner": record.get("component", "VRN"), "code": "CLOSEOUT_NOT_READY", "detail": str(exc)})
    binding = digest({"units": [{"id": u["id"], "tree_hash": u["tree_hash"]} for u in units], "tools": tools, "environments": envs, "readiness": readiness, "contract_sha256": digest(c)})
    checks = {}
    for name, spec in [("vcgc", c["vcgc"]["audit"]), ("accelerator", c["accelerator"])]:
        try:
            checks[name] = adapter(spec, c["vcgc"]["root"], output / (name + "_receipt.json"), binding)
        except Exception as exc:
            findings.append({"owner": "VCGC", "code": name.upper() + "_UNVERIFIED", "detail": str(exc)})
    result = {"schema": "via.deploy-audit.v3", "version": VERSION, "captured_at": now(), "status": "PASS" if not findings else "BLOCKED", "baseline_sealed": False, "contract_sha256": digest(c), "binding": binding, "units": units, "tools": tools, "readiness": readiness, "environments": envs, "governance": checks, "findings": findings}
    write(output / "audit.json", result)
    render(result, output / "Deployment_Status.html")
    return result


def prepare(c, output, repair=False):
    first = audit(c, Path(output) / "round1")
    repairs = []
    if first["status"] != "PASS" and repair and c.get("vcgc", {}).get("repair"):
        spec = c["vcgc"]["repair"]
        if spec.get("scope") != "isolated_staging" or not spec.get("target"):
            raise ValueError("Automatic repair requires an explicit isolated staging target")
        for u in c["units"]:
            disjoint(u["source"], spec["target"])
        repairs.append(adapter(spec, c["vcgc"]["root"], Path(output) / "repair_receipt.json", first["binding"]))
        # Repair adapters return a separate complete contract for staged sources.
        staged = read(Path(spec["target"]) / "deploy_contract.json")
        for u in validate_contract(staged)["units"]:
            if not Path(u["source"]).resolve().is_relative_to(Path(spec["target"]).resolve()):
                raise ValueError("Repair contract source escaped staging")
        c = staged
    second = audit(c, Path(output) / "round2")
    third = audit(c, Path(output) / "round3")
    stable = second["binding"] == third["binding"]
    ready = second["status"] == third["status"] == "PASS" and stable
    result = {"schema": "via.deploy-baseline.v3", "version": VERSION, "status": "BASELINE_READY" if ready else "BLOCKED", "baseline_sealed": False, "captured_at": now(), "release_id": c["release_id"], "contract": c, "rounds": [first, second, third], "repairs": repairs, "stable": stable, "baseline_id": "VDL-" + third["binding"][:20].upper(), "audit_binding": third["binding"]}
    write(Path(output) / "baseline.json", result)
    render(result, Path(output) / "Deployment_Status.html")
    return result


# def PART 2 — source-independent runtime extraction / compilation
def client_runtime(source, authority_pin, release_pin):
    """AST dependency closure removes signing authority, tests and developer CLI."""
    for pin in (authority_pin, release_pin):
        if not re.fullmatch(r"[0-9a-f]{64}", pin):
            raise ValueError("Production public-key pin required")
    module = ast.parse(source)
    nodes = {}
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes[node.name] = node
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    nodes[t.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            nodes[node.target.id] = node
    client_tree = ast.parse((Path(__file__).parent / "VIA_Client_v0300.py").read_text(encoding="utf-8"))
    runtime_calls = {n.attr for n in ast.walk(client_tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "runtime"}
    needed, pending = set(), list(RUNTIME_ROOTS | runtime_calls)
    while pending:
        name = pending.pop()
        if name in needed or name not in nodes:
            continue
        needed.add(name)
        pending.extend(n.id for n in ast.walk(nodes[name]) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load))
    if AUTHORITY_FORBIDDEN & needed:
        raise ValueError("Signing authority leaked into runtime closure")
    patches = {"def_PARAM_BUILD_MODE": "PRODUCTION", "def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256": authority_pin, "def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256": release_pin}
    selected = []
    for node in module.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)) or any(node is nodes.get(x) for x in needed):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in patches:
                node.value = ast.Constant(patches[node.targets[0].id])
            selected.append(node)
    text = ast.unparse(ast.Module(body=selected, type_ignores=[])) + "\n"
    compile(text, "runtime", "exec")
    if any("def " + x + "(" in text for x in AUTHORITY_FORBIDDEN):
        raise ValueError("Runtime authority exclusion failed")
    return text


def inject_guard(source, unit_id, product_number):
    m = ast.parse(source)
    count = 0
    while count < len(m.body):
        n = m.body[count]
        if (count == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)) or (isinstance(n, ast.ImportFrom) and n.module == "__future__"):
            count += 1
        else:
            break
    if "VIA-PRODUCT-GUARD-v2.2" in source:
        raise ValueError("Already guarded source; duplicate injection rejected")
    snippet = legacy().def_guard_snippet(unit_id, "VIA_ALL_ENGINES", product_number, "EXE")
    m.body[count:count] = ast.parse(snippet).body
    result = ast.unparse(m) + "\n"
    compile(result, "guarded", "exec")
    return result


def copy_source(source, target, inventory):
    if Path(target).exists():
        raise FileExistsError("Staging must be a new directory")
    Path(target).mkdir(parents=True)
    for row in inventory:
        src, dst = below(source, row["path"]), below(target, row["path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha(dst) != row["sha256"]:
            raise ValueError("Copy hash mismatch")


def validate_client_tree(root):
    rows = tree(root)
    for r in rows:
        path = Path(r["path"])
        if path.suffix.lower() in SOURCE_SUFFIXES | SENSITIVE_SUFFIXES or any(t in path.name.lower() for t in ("private", "master_key", "credential", ".env", "authority.sqlite")):
            raise ValueError("Client bundle contains developer source/secret/database: " + r["path"])
        if path.suffix.lower() in {".json", ".txt", ".cfg", ".ini", ".toml", ".yaml", ".yml", ".html"}:
            raw = below(root, r["path"]).read_bytes()
            if re.search(rb"-----BEGIN [^-]*PRIVATE KEY-----|VIAK(?:-[A-HJ-NP-Z2-9]{4}){6}", raw):
                raise ValueError("Credential content in client bundle")
        if path.suffix.lower() in {".zip", ".whl", ".7z", ".tar", ".gz"}:
            raise ValueError("Nested archives require explicit source-disclosure review")
    return rows


def assert_baseline(b):
    if b.get("status") != "BASELINE_READY" or len(b.get("rounds", [])) != 3:
        raise ValueError("No verified three-round baseline")
    c = validate_contract(b["contract"])
    rounds = b["rounds"]
    if any(r["status"] != "PASS" for r in rounds[-2:]) or rounds[-2]["binding"] != rounds[-1]["binding"]:
        raise ValueError("Unstable baseline")
    if rounds[-1]["contract_sha256"] != digest(c):
        raise ValueError("Contract changed after audit")
    for u in c["units"]:
        old = next(x for x in rounds[-1]["units"] if x["id"] == u["id"])
        if tree(u["source"]) != old["files"]:
            raise ValueError("Source drift after baseline: " + u["id"])
    for t in c["tools"]:
        if sha(t["path"]) != t["sha256"]:
            raise ValueError("Tool drift after baseline")
    for record in rounds[-1].get("readiness", []):
        if sha(record["path"]) != record["sha256"]:
            raise ValueError("Component closeout changed after baseline")
    for asset in c.get("assets", []):
        if sha(asset["source"]) != asset["sha256"]:
            raise ValueError("Native tool/model changed after baseline")
    return c


def build(baseline, product, authority_public, release_public, output):
    b, p = read(baseline), read(product)
    c = assert_baseline(b)
    if platform.system() != "Windows":
        raise RuntimeError("Windows artifacts must be built and tested on Windows")
    out = Path(output).resolve()
    for python, snapshot in b["rounds"][-1]["environments"].items():
        if environment_probe(python, Path(baseline).parent) != snapshot:
            raise ValueError("Interpreter/packages changed after baseline; re-audit required")
    if out.exists():
        raise FileExistsError("Build output must be new; partial builds are retained for diagnosis")
    for u in c["units"]:
        disjoint(u["source"], out)
    if shutil.disk_usage(out.parent).free < MIN_FREE_BYTES:
        raise RuntimeError("Insufficient build disk space")
    out.mkdir(parents=True)
    l = legacy()
    binding = l.def_public_product_binding(p)
    legacy_source = (Path(__file__).parent / "legacy" / (LEGACY_NAME + ".py")).read_text(encoding="utf-8")
    rt = client_runtime(legacy_source, sha(authority_public), sha(release_public))
    artifacts = out / "payload"
    artifacts.mkdir()
    notices = []
    for asset in c.get("assets", []):
        target = below(artifacts, asset["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset["source"], target)
        if sha(target) != asset["sha256"]:
            raise ValueError("Native tool/model copy hash mismatch")
        notices.append({"path": asset["target"], "license_notice": asset["license_notice"]})
    if notices:
        write(artifacts / "THIRD_PARTY_NOTICES.json", notices)
    proof = []
    for u in c["units"]:
        inventory = next(x["files"] for x in b["rounds"][-1]["units"] if x["id"] == u["id"])
        stage = out / "staging" / u["id"]
        copy_source(u["source"], stage, inventory)
        ep = below(stage, u["entry"])
        ep.write_text(inject_guard(ep.read_text(encoding="utf-8-sig"), u["id"], binding["product_number"]), encoding="utf-8")
        (ep.parent / (LEGACY_NAME + ".py")).write_text(rt, encoding="utf-8")
        compile_out = out / "compiled" / u["id"]
        command = [u["python"], "-I", "-m", "nuitka", "--standalone", "--follow-imports", "--python-flag=isolated", "--output-dir=" + str(compile_out), "--output-filename=" + u["id"] + ".exe", "--include-module=" + LEGACY_NAME]
        for module in u.get("include_modules", []):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", module):
                raise ValueError("Invalid explicit dynamic import")
            command.append("--include-module=" + module)
        for item in u.get("data", []):
            src, dest = below(stage, item["source"]), safe_rel(item["target"])
            if not src.is_file() or src.suffix.lower() in SOURCE_SUFFIXES | SENSITIVE_SUFFIXES:
                raise ValueError("Data mapping must be a non-source, non-secret file")
            command.append("--include-data-files=" + str(src) + "=" + dest)
        command.append(str(ep))
        result = run(command, ep.parent, BUILD_TIMEOUT)
        write(out / (u["id"] + "_build.json"), result)
        if not result["ok"]:
            raise RuntimeError("Native build failed: " + u["id"])
        hits = list(compile_out.glob("*.dist/" + u["id"] + ".exe"))
        if len(hits) != 1:
            raise ValueError("Compiler did not produce one complete standalone directory")
        shutil.copytree(hits[0].parent, artifacts / u["id"])
        artifact = artifacts / u["id"] / (u["id"] + ".exe")
        deny_env = {k: "" for k in (l.def_PARAM_RUNTIME_TOKEN_ENV, l.def_PARAM_LICENSE_FILE_ENV, l.def_PARAM_MODULE_MANIFEST_ENV)}
        denied = run([str(artifact), *u["smoke_args"]], artifact.parent, u.get("timeout", 600), deny_env)
        if denied["ok"] or "Required runtime environment path is missing" not in denied["stderr_tail"] + denied["stdout_tail"]:
            raise ValueError("Extracted standalone entry did not prove license denial")
        proof.append({"id": u["id"], "artifact": artifact.relative_to(artifacts).as_posix(), "sha256": sha(artifact), "standalone_denial": denied, "smoke_args": u["smoke_args"], "success_regex": u["success_regex"], "timeout": u.get("timeout", 600)})
        if tree(u["source"]) != inventory:
            raise ValueError("Canonical source changed during compilation")
    bootstrap = out / "bootstrap"
    bootstrap.mkdir()
    (bootstrap / (LEGACY_NAME + ".py")).write_text(rt, encoding="utf-8")
    shutil.copy2(Path(__file__).parent / "VIA_Client_v0300.py", bootstrap / "VIA_Client_v0300.py")
    # Public pins compiled into bootstrap; bundle-supplied keys cannot choose trust.
    (bootstrap / "via_pins.py").write_text("AUTHORITY_PIN = " + repr(sha(authority_public)) + "\nRELEASE_PIN = " + repr(sha(release_public)) + "\n", encoding="utf-8")
    py = c["units"][0]["python"]
    result = run([py, "-I", "-m", "nuitka", "--standalone", "--follow-imports", "--enable-plugin=tk-inter", "--python-flag=isolated", "--output-filename=VIA_Setup.exe", "--output-dir=" + str(out / "setup_compiled"), str(bootstrap / "VIA_Client_v0300.py")], bootstrap, BUILD_TIMEOUT)
    write(out / "setup_build.json", result)
    if not result["ok"]:
        raise RuntimeError("Client bootstrap compilation failed")
    setup = list((out / "setup_compiled").glob("*.dist/VIA_Setup.exe"))
    if len(setup) != 1:
        raise ValueError("Missing bootstrap dist")
    shutil.copytree(setup[0].parent, artifacts / "Setup")
    validate_client_tree(artifacts)
    result = {"schema": "via.native-build.v3", "status": "BUILT_NOT_QUALIFIED", "release_id": c["release_id"], "baseline_id": b["baseline_id"], "baseline": b, "product": binding, "authority_pin": sha(authority_public), "release_pin": sha(release_public), "units": proof, "payload_tree": tree(artifacts), "payload": str(artifacts)}
    write(out / "build.json", result)
    return result


# def PART 3 — authority ledger / existing license schema compatibility
def authority_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS products(number TEXT PRIMARY KEY, key_hash TEXT NOT NULL, profile TEXT NOT NULL, status TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS licenses(id TEXT PRIMARY KEY, product TEXT NOT NULL, device TEXT NOT NULL, envelope TEXT NOT NULL, status TEXT NOT NULL, UNIQUE(product,device))")
    db.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at TEXT NOT NULL, kind TEXT NOT NULL, ref TEXT NOT NULL)")
    return db


def register_product(db_path, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    p = legacy().def_create_product_record()
    profile = legacy().def_sample_profile(p)
    profile["max_devices"] = {"pc": 1, "mobile": 0}
    profile["mobile_policy"] = {"allowed": False, "required": False}
    # Bounded renewable licenses enable eventual offline revocation.
    profile["expires_at"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    with contextlib.closing(authority_db(db_path)) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("INSERT INTO products VALUES(?,?,?,?)", (p["product_number"], legacy().def_public_product_binding(p)["master_key_hash"], json.dumps(profile), "ACTIVE"))
            output.mkdir(parents=True)
            write(output / "product_PRIVATE.json", p)
            write(output / "profile.json", profile)
            db.execute("INSERT INTO events(at,kind,ref) VALUES(?,?,?)", (now(), "PRODUCT_CREATED", p["product_number"]))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"status": "PRODUCT_CREATED", "product_number": p["product_number"], "private_record": str(output / "product_PRIVATE.json"), "key_disclosed": False}


def issue(db_path, request, private_key, output):
    l = legacy()
    envelope = read(request)
    req = l.def_verify_activation_request(envelope)
    number, device = req["product_number"], req["device_id"]
    key = l.def_load_private_key(Path(private_key))
    with contextlib.closing(authority_db(db_path)) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute("SELECT key_hash, profile, status FROM products WHERE number=?", (number,)).fetchone()
            if not row or row[2] != "ACTIVE" or not secrets.compare_digest(row[0], req["master_key_hash"]):
                raise ValueError("Unknown/revoked product or invalid master key")
            previous = db.execute("SELECT envelope,status FROM licenses WHERE product=? AND device=?", (number, device)).fetchone()
            if previous:
                if previous[1] != "ACTIVE":
                    raise ValueError("Device license revoked")
                result = json.loads(previous[0])
                if result["payload"].get("expires_at") and l.def_parse_utc(result["payload"]["expires_at"]) <= datetime.now(timezone.utc):
                    raise ValueError("Renewal required; expired license is not silently reissued")
            else:
                profile = json.loads(row[1])
                active = db.execute("SELECT envelope FROM licenses WHERE product=? AND status='ACTIVE'", (number,)).fetchall()
                same_type = sum(any(d["device_type"] == req["device_type"] for d in json.loads(a[0])["payload"]["devices"]) for a in active)
                if same_type >= profile["max_devices"].get(req["device_type"], 0):
                    raise ValueError("Seat limit exceeded; revoke/rehost explicitly")
                result = l.def_issue_license([envelope], profile, key, customer_ref=number)
                db.execute("INSERT INTO licenses VALUES(?,?,?,?,?)", (result["payload"]["license_id"], number, device, json.dumps(result), "ACTIVE"))
                db.execute("INSERT INTO events(at,kind,ref) VALUES(?,?,?)", (now(), "LICENSE_ISSUED", result["payload"]["license_id"]))
            db.commit()
        except Exception:
            db.rollback()
            raise
    write(output, result)
    return {"status": "LICENSE_ISSUED", "license_id": result["payload"]["license_id"], "output": str(output)}


def revoke(db_path, number):
    with contextlib.closing(authority_db(db_path)) as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM products WHERE number=?", (number,)).fetchone() is None:
            db.rollback()
            raise ValueError("Unknown product")
        db.execute("UPDATE products SET status='REVOKED' WHERE number=?", (number,))
        db.execute("UPDATE licenses SET status='REVOKED' WHERE product=?", (number,))
        db.execute("INSERT INTO events(at,kind,ref) VALUES(?,?,?)", (now(), "PRODUCT_REVOKED", number))
        db.commit()
    return {"status": "REVOKED_FOR_FUTURE_ISSUANCE", "product_number": number, "offline_limit": "Existing offline licenses remain valid until their signed expiry. Immediate remote revocation is not implemented."}


def qualify(build_file, license_path, device_key, product_state, authority_public, release_public, release_private, output):
    """Sign manifests, run real compiled smokes with a licensed QA device, seal exact tree."""
    b = read(build_file)
    if b.get("status") != "BUILT_NOT_QUALIFIED":
        raise ValueError("Native build evidence required")
    payload = Path(b["payload"])
    if tree(payload) != b["payload_tree"]:
        raise ValueError("Built payload changed before qualification")
    if sha(authority_public) != b["authority_pin"] or sha(release_public) != b["release_pin"]:
        raise ValueError("Public key pin changed")
    out = Path(output)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    candidate = out / "candidate"
    shutil.copytree(payload, candidate)
    l = legacy()
    rk = l.def_load_private_key(Path(release_private))
    ap, rp = l.def_load_public_key(Path(authority_public)), l.def_load_public_key(Path(release_public))
    # Challenge verifies the signing private key actually matches the pinned public key.
    challenge = secrets.token_bytes(32)
    rp.verify(rk.sign(challenge), challenge)
    state = l.def_load_product_key_state(Path(product_state))
    dk = l.def_load_device_private_key(Path(device_key))
    hw = l.def_load_hardware_hashes()
    lp = read(license_path)
    manifests = candidate / "Manifests"
    manifests.mkdir()
    shutil.copy2(authority_public, candidate / "authority.pub")
    shutil.copy2(release_public, candidate / "release.pub")
    passed = []
    for unit in b["units"]:
        artifact = below(candidate, unit["artifact"])
        m = l.def_build_module_manifest(artifact, unit["id"], l.def_PARAM_ENGINE_VERSION, [unit["id"] + "_RUN"], "VIA_ALL_ENGINES", "standalone", "main", b["release_id"], b["product"]["product_number"], b["product"]["master_key_hash"])
        signed = l.def_sign_module_manifest(m, rk)
        mp = manifests / (unit["id"] + ".json")
        write(mp, signed)
        handshake = l.def_create_module_handshake(signed, rp, artifact, lp, ap, dk, l.def_PARAM_PRODUCT_SKU, l.def_PARAM_ENGINE_VERSION, state["product_number"], state["master_key"], hw, secrets.token_hex(24), state_path=out / "qa-clock.json", execution_mode="CHILD_PROCESS")
        if not handshake.ok:
            raise ValueError("QA license invalid: " + str(handshake.errors))
        os.environ["VIA_ASSET_ROOT"] = str(candidate / "Assets")
        os.environ["VIA_HOME"] = str(out / "qa_data")
        (out / "qa_data").mkdir(exist_ok=True)
        before_smoke = tree(candidate)
        result = l.def_launch_guarded_executable(artifact, handshake.data["token"], Path(license_path), mp, Path(authority_public), Path(release_public), Path(device_key), Path(product_state), out / "qa-replay.jsonl", unit["smoke_args"], timeout_seconds=unit["timeout"])
        if not result["ok"] or not re.search(unit["success_regex"], result["stdout_tail"] + result["stderr_tail"]):
            raise ValueError("Compiled functional smoke failed: " + unit["id"])
        if tree(candidate) != before_smoke:
            raise ValueError("Compiled unit wrote inside immutable package; use VIA_HOME for outputs")
        passed.append({"id": unit["id"], "result": result})
    release = {"schema": "via.client-release.v3", "release_id": b["release_id"], "baseline_id": b["baseline_id"], "product_number": b["product"]["product_number"], "units": [{k: u[k] for k in ("id", "artifact", "smoke_args", "success_regex", "timeout")} for u in b["units"]]}
    write(candidate / "release.json", release)
    # All candidate files must be reviewed; no raw PY / authority commands / keys ship.
    rows = validate_client_tree(candidate)
    signed_tree = l.def_sign_package_tree_manifest(l.def_build_package_tree_manifest(candidate, release["product_number"], b["release_id"]), rk)
    write(out / "package.signed.json", signed_tree)
    qualification = {"status": "QUALIFIED_CANDIDATE", "native_smokes": passed, "baseline_id": b["baseline_id"], "candidate_tree": rows, "remaining": ["Clean Windows machine installation test", "Authenticode-sign VIA_Setup.exe and re-seal package after signing"]}
    write(out / "qualification.json", qualification)
    return qualification


def seal(candidate, release_private, release_public, output):
    """Final exact-tree seal after Authenticode signing and clean Windows acceptance."""
    root, out = Path(candidate).resolve(), Path(output).resolve()
    disjoint(root, out)
    release = read(root / "release.json")
    validate_client_tree(root)
    l = legacy()
    key = l.def_load_private_key(Path(release_private))
    public = l.def_load_public_key(Path(release_public))
    public.verify(key.sign(b"VDL release key check"), b"VDL release key check")
    if sha(root / "release.pub") != sha(release_public):
        raise ValueError("Release trust pin mismatch")
    # Clean-machine evidence must bind the exact package hash after code signing.
    signed = l.def_sign_package_tree_manifest(l.def_build_package_tree_manifest(root, release["product_number"], release["release_id"]), key)
    out.mkdir(parents=True, exist_ok=False)
    archive = out / ("VIA_" + release["release_id"] + "_CANDIDATE.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for row in tree(root):
            z.write(below(root, row["path"]), "payload/" + row["path"])
        z.writestr("package.signed.json", canonical(signed))
    write(out / "release_candidate.json", {"status": "CANDIDATE_NOT_CUSTOMER_APPROVED", "file": archive.name, "sha256": sha(archive), "release_id": release["release_id"], "clean_windows_acceptance": "REQUIRED"})
    return {"status": "CANDIDATE_NOT_CUSTOMER_APPROVED", "archive": str(archive), "sha256": sha(archive)}


def pipeline(job, output):
    """One invocation advances all configured stages; a failed gate stops the chain."""
    job = read(job)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    try:
        baseline = prepare(read(job["contract"]), output / "baseline", job.get("repair", False))
        if baseline["status"] != "BASELINE_READY":
            raise ValueError("VCGC/source/environment baseline is not ready")
        build(output / "baseline/baseline.json", job["product"], job["authority_public"], job["release_public"], output / "build")
        qualify(output / "build/build.json", job["qa_license"], job["qa_device_key"], job["qa_product_state"], job["authority_public"], job["release_public"], job["release_private"], output / "qualified")
        result = seal(output / "qualified/candidate", job["release_private"], job["release_public"], output / "package")
    except Exception as exc:
        result = {"status": "BLOCKED", "error": str(exc), "last_known_good_unchanged": True}
    write(output / "pipeline.json", result)
    render(result, output / "Deployment_Status.html")
    return result


def render(result, path):
    encoded = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
    status = html.escape(str(result.get("status", "UNKNOWN")))
    Path(path).write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>VIA DeployLedger</title><style>body{background:#f7f5ee;color:#23342d;font:13px/1.45 system-ui;margin:24px auto;max-width:1100px;padding:0 20px}header{display:flex;gap:16px;border-bottom:2px solid #9d8249;padding:16px 0}.seal{font:40px serif;color:#9d8249}h1{font-size:18px;margin:0}small{letter-spacing:2px}strong{display:block;background:#ece7d9;padding:14px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:18px}summary{cursor:pointer}</style><header><div class="seal">理</div><div><h1>VERITAS INTELLIGENCE ANALYTICS</h1><small>DISCIPLINA · PRUDENTIA · INTEGRITAS</small><div>VeritasDeployLedger 3.0 · 商業部署驗證</div></div></header><strong>'+status+'</strong><p>盤點、基線、編譯、授權、安裝與真實功能驗收分別留證。只有當輪完整證據可以作為發行依據。</p><details open><summary>可檢查證據</summary><pre>'+encoded+'</pre></details></html>', encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description="VeritasDeployLedger commercial upgrade factory")
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("discover"); q.add_argument("--output", required=True); q.add_argument("--root", action="append")
    q = sub.add_parser("prepare"); q.add_argument("--contract", required=True); q.add_argument("--output", required=True); q.add_argument("--repair", action="store_true")
    q = sub.add_parser("pipeline"); q.add_argument("--job", required=True); q.add_argument("--output", required=True)
    q = sub.add_parser("build")
    for x in ("baseline", "product", "authority-public", "release-public", "output"): q.add_argument("--"+x, required=True)
    q = sub.add_parser("product"); q.add_argument("--database", required=True); q.add_argument("--output", required=True)
    q = sub.add_parser("issue")
    for x in ("database", "request", "private-key", "output"): q.add_argument("--"+x, required=True)
    q = sub.add_parser("revoke"); q.add_argument("--database", required=True); q.add_argument("--product-number", required=True)
    q = sub.add_parser("qualify")
    for x in ("build-file", "license", "device-key", "product-state", "authority-public", "release-public", "release-private", "output"): q.add_argument("--"+x, required=True)
    q = sub.add_parser("seal")
    for x in ("candidate", "release-private", "release-public", "output"): q.add_argument("--"+x, required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "discover": result = discover(a.output, a.root)
        elif a.cmd == "prepare": result = prepare(read(a.contract), a.output, a.repair)
        elif a.cmd == "pipeline": result = pipeline(a.job, a.output)
        elif a.cmd == "build": result = build(a.baseline, a.product, a.authority_public, a.release_public, a.output)
        elif a.cmd == "product": result = register_product(a.database, a.output)
        elif a.cmd == "issue": result = issue(a.database, a.request, a.private_key, a.output)
        elif a.cmd == "revoke": result = revoke(a.database, a.product_number)
        elif a.cmd == "qualify": result = qualify(a.build_file, a.license, a.device_key, a.product_state, a.authority_public, a.release_public, a.release_private, a.output)
        else: result = seal(a.candidate, a.release_private, a.release_public, a.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] not in {"BLOCKED", "NEEDS_DEPLOY_CONTRACT"} else 2
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc), "type": type(exc).__name__}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
