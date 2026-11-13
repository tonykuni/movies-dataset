#!/usr/bin/env python3
# [VIA:ACCEL-BRIDGE] VCGC 五階段測試、回饋與收尾
"""VCGC offline test orchestrator and model-neutral MCP adapter."""
import argparse
import ast
import asyncio
import contextlib
import csv
import hashlib
import importlib.metadata
import importlib.util
import html
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

VERSION = "v0100"
ROOT = Path(__file__).resolve().parent
NATIVE = ROOT / "native" / "CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py"
NATIVE_SHA = "66e8333349f53ce8269214cafa775035dd0f2582f2dac34066693416ffe69f6d"
AGENTOS_SHA = "97ca853d253ea58194a2938762899624852f8651c9853fa3224d93d46855f304"
DEFAULT_HOME = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "VCGC" / "Test_Closeout_v0100"
STAGES = ("UNIT", "INTEGRATION", "SYSTEM", "RESULT_VERIFICATION", "CLOSE_OUT")
STAGE_LABELS = ("Unit", "Integration", "System", "Result Verification", "Close-Out")
MAX_CHECKS = 120
MAX_FILES = 3000
MAX_BYTES = 512 * 1024 * 1024
MAX_JSON = 12 * 1024 * 1024
MAX_LOG = 128 * 1024
MAX_TIMEOUT = 3600
MAX_FEEDBACK = 3800
MAX_MCP_CASES = 8
RULES = ("add_missing", "replace_exact", "rename_key")
CHECKS = ("python_ast", "json", "file", "csv_equal", "command", "native_matrix",
          "agentos_matrix", "parquet", "closeout")
IGNORED = {".git", ".svn", ".venv", "venv", "__pycache__", "node_modules",
           ".pytest_cache", ".env", ".ssh", ".gnupg", ".codex", ".aws"}
TOKENS = ("read", "slice", "digest", "pack", "etag", "chain")
NATIVE_PRECHECKS = ("token", "handoff check", "functions", "token chain",
                    "ssot panorama", "test --quick")
KNOWN_EXE = {"python", "pwsh", "git", "node", "pytest"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")


class GateError(Exception):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, detail
        super().__init__(f"{code} {detail}".strip())


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def no_duplicates(pairs):
    output = {}
    for name, value in pairs:
        if name in output:
            raise GateError("F04", "duplicate JSON key")
        output[name] = value
    return output


def invalid_number(_):
    raise GateError("F16", "non-finite JSON number")


def decode(raw):
    try:
        value = json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=invalid_number)
        encoded(value)
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        raise GateError("F16", "invalid strict JSON") from error


def read_json(path, limit=MAX_JSON):
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except FileNotFoundError as error:
        raise GateError("F24", "JSON file missing") from error
    if len(data) > limit:
        raise GateError("F11", "JSON size limit")
    return decode(data)


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save(path, value):
    write_atomic(path, encoded(value) + b"\n")


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise GateError("F14", "invalid relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or not path.parts or path.as_posix() != value or
            any(p in ("..", ".") or p.rstrip(" .") != p or
                re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", p.split(".", 1)[0])
                for p in path.parts)):
        raise GateError("F14", "unsafe relative path")
    return path


def rooted(root, value):
    path = root
    for part in relative(value).parts:
        path = path / part
        if path.is_symlink() or (os.name == "nt" and path.exists() and
                                 getattr(path.lstat(), "st_reparse_tag", None) == stat.IO_REPARSE_TAG_MOUNT_POINT):
            raise GateError("F14", "symbolic link or junction in scope")
    if not path.resolve().is_relative_to(root.resolve()):
        raise GateError("F14", "path escaped workspace")
    return path


def key(value):
    if not isinstance(value, str) or not ID.fullmatch(value) or value in {".", ".."} or value.endswith("."):
        raise GateError("F14", "invalid identifier")
    return value


def run_id(value):
    if not isinstance(value, str):
        raise GateError("F14", "invalid run ID")
    try:
        if str(uuid.UUID(value)) == value:
            return value
    except ValueError:
        pass
    raise GateError("F14", "run ID must be a canonical UUID")


def require(ok, code, detail):
    if not ok:
        raise GateError(code, detail)


def function_node(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def literal_matrix_verbs(path):
    try:
        tree = ast.parse(path.read_bytes(), filename=path.name)
        main = function_node(tree, "main")
        choices = []
        for call in ast.walk(main):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "add_argument" and call.args and
                    isinstance(call.args[0], ast.Constant) and call.args[0].value == "action"):
                for field in call.keywords:
                    if field.arg == "choices":
                        choices = ast.literal_eval(field.value)
        return [name for name in dict.fromkeys(choices) if isinstance(name, str) and not name.startswith("_")]
    except (OSError, SyntaxError, ValueError, StopIteration):
        return []


def inventory(native=NATIVE, registry=None):
    selected = Path(native)
    actions = literal_matrix_verbs(selected)
    source_exists = selected.is_file()
    stations = None
    if registry:
        data = read_json(Path(registry))
        rows = data.get("stations") if isinstance(data, dict) else None
        require(isinstance(rows, list), "F04", "station registry schema")
        ids = [row.get("id") for row in rows if isinstance(row, dict)]
        require(len(ids) == len(rows) and all(isinstance(i, str) and i for i in ids)
                and len(set(ids)) == len(ids), "F04", "station registry ID conflict")
        stations = {"entries": len(ids), "registry_sha256": file_sha(Path(registry))}
    return {
        "source": selected.name, "source_sha256": file_sha(selected) if source_exists else None,
        "matrix": {"count": len(actions), "verbs": actions, "scope": "STATIC_CLI_CHOICES" if actions else "UNRESOLVED"},
        "token_history": {"count": len(TOKENS), "verbs": list(TOKENS), "option": "--brief",
                          "scope": "HISTORICAL_EVIDENCE"},
        "native_preflight_routes": list(NATIVE_PRECHECKS), "station_registry": stations,
        "installed_vcgc_total": None,
        "engine_calls": ["matrix selftest", "matrix resilience-test"],
    }


def cases():
    result = read_json(ROOT / "FailureMatrix_v0100.json")
    require(isinstance(result, list) and [r.get("id") for r in result] ==
            [f"F{i:02}" for i in range(1, 31)], "F04", "failure catalog")
    return result


def validate_profile(plan):
    require(isinstance(plan, dict) and plan.get("schema") == "via.closeout.profile/1",
            "F04", "profile schema")
    key(plan.get("id"))
    inputs, requirements, checks = (plan.get(name) for name in ("inputs", "requirements", "checks"))
    require(isinstance(plan.get("source"), str) and bool(plan["source"]), "F01", "profile source")
    require(isinstance(inputs, list) and inputs, "F21", "profile needs explicit inputs")
    for path in inputs:
        relative(path)
    require(isinstance(requirements, dict) and requirements, "F21", "profile needs requirements")
    require(isinstance(checks, list) and 5 <= len(checks) <= MAX_CHECKS, "F21", "invalid check count")
    seen, observed, previous = {}, set(), -1
    traced = {key(name): set() for name in requirements}
    for check in checks:
        require(isinstance(check, dict), "F21", "invalid check")
        name, stage, kind = key(check.get("id")), check.get("stage"), check.get("kind")
        require(name not in seen and stage in STAGES and kind in CHECKS, "F21", "unknown stage/check or duplicate ID")
        level = STAGES.index(stage)
        require(level >= previous, "F21", "checks must follow phase order")
        previous = level
        deps, links = check.get("depends", []), check.get("requirements", [])
        watches = check.get("watch", [])
        require(isinstance(watches, list) and len(watches) <= MAX_FILES, "F21", "invalid watch list")
        for path in watches:
            relative(path)
        require(isinstance(deps, list) and all(isinstance(d, str) and d in seen for d in deps),
                "F21", "dependency missing or cyclic")
        require(isinstance(links, list) and all(isinstance(k, str) and k in traced for k in links),
                "F21", "unregistered requirement")
        if kind == "closeout":
            require(stage == "CLOSE_OUT", "F21", "closeout must be in final stage")
        else:
            require(stage != "CLOSE_OUT", "F21", "final stage accepts closeout checks")
        if kind in ("python_ast", "json", "file", "csv_equal", "parquet"):
            relative(check.get("path"))
        if kind == "csv_equal":
            relative(check.get("reference"))
            require(isinstance(check.get("key"), list) and check["key"] and
                    all(isinstance(x, str) and x for x in check["key"]) and len(set(check["key"])) == len(check["key"]),
                    "F04", "CSV unique key contract")
        if kind == "command":
            argv = check.get("argv")
            require(isinstance(argv, list) and 2 <= len(argv) <= 48 and
                    all(isinstance(v, str) and 0 < len(v) <= 1024 and "\x00" not in v for v in argv)
                    and argv[0] in KNOWN_EXE, "F14", "command requires a supported executable and argument list")
            require(check.get("format") in ("json", "junit"), "F21", "command needs evidence format")
            require(check.get("format") != "json" or bool(check.get("assertions")), "F21", "command JSON needs assertions")
            relative(check.get("output"))
        if kind == "native_matrix":
            require(check.get("action") in ("selftest", "resilience-test"), "F14", "native action outside test scope")
        if kind == "agentos_matrix":
            relative(check.get("path"))
        if kind in ("command", "native_matrix", "agentos_matrix"):
            timeout = check.get("timeout", 120)
            require(type(timeout) is int and 1 <= timeout <= MAX_TIMEOUT, "F21", "timeout out of range")
            require(type(check.get("replay_safe", False)) is bool and
                    type(check.get("retry_timeout", False)) is bool and
                    (not check.get("retry_timeout") or check.get("replay_safe")),
                    "F21", "timeout retry requires replay-safe declaration")
        for requirement in links:
            traced[requirement].add(stage)
        seen[name] = check
        observed.add(stage)
    require(observed == set(STAGES), "F21", "all five stages require a check")
    for name, mandatory in requirements.items():
        require(isinstance(mandatory, list) and all(s in STAGES for s in mandatory) and
                len(set(mandatory)) >= 2 and set(mandatory) <= traced[name],
                "F21", f"incomplete trace for {name}")
    repairs = plan.get("repairs", [])
    require(isinstance(repairs, list) and len(repairs) <= 20, "F29", "repair count")
    registered = set()
    for rule in repairs:
        require(isinstance(rule, dict) and rule.get("op") in RULES and
                isinstance(rule.get("trigger"), str) and rule["trigger"] in seen,
                "F29", "unregistered repair")
        rule_id = key(rule.get("id"))
        relative(rule.get("path"))
        trigger = seen[rule["trigger"]]
        require(rule_id not in registered and trigger["kind"] == "json" and trigger.get("path") == rule["path"],
                "F29", "repair requires a unique rule and a JSON check for its own file")
        registered.add(rule_id)
        require(isinstance(rule.get("expected_sha256"), str) and HEX.fullmatch(rule["expected_sha256"]),
                "F29", "repair requires exact input hash")
        require(isinstance(rule.get("key"), str) and rule["key"], "F29", "repair key missing")
        require(rule["op"] == "rename_key" or "value" in rule, "F29", "repair value missing")
        require(rule["op"] == "add_missing" or "expected" in rule, "F29", "repair old value missing")
        if rule["op"] == "rename_key":
            require(isinstance(rule.get("new_key"), str) and rule["new_key"] and rule["new_key"] != rule["key"],
                    "F29", "invalid new key")
    return plan


def selected_files(source, names):
    require(source.is_dir(), "F01", "source root missing")
    files = {}
    count = total = 0
    folded = set()
    for name in names:
        target = rooted(source, name)
        require(target.exists(), "F01", f"declared input missing: {name}")
        paths = [target]
        while paths:
            path = paths.pop()
            rel = path.relative_to(source).as_posix()
            if any(part.casefold() in IGNORED or part.casefold().startswith(".env.")
                   for part in relative(rel).parts):
                continue
            rooted(source, rel)
            if path.is_dir():
                paths.extend(sorted(path.iterdir(), reverse=True))
                continue
            require(path.is_file(), "F01", "unsupported input file")
            if rel in files:
                continue
            count += 1
            total += path.stat().st_size
            require(count <= MAX_FILES and total <= MAX_BYTES, "F11", "snapshot scope limit")
            require(rel.casefold() not in folded, "F04", "case-insensitive path collision")
            folded.add(rel.casefold())
            files[rel] = file_sha(path)
    require(bool(files), "F01", "snapshot has no files")
    return files


def assert_protected(root, expected):
    for name, checksum in expected.items():
        path = rooted(root, name)
        require(path.is_file() and file_sha(path) == checksum, "F28", "protected input changed")


def snapshot(source, inputs, expected, destination):
    size = sum(rooted(source, name).stat().st_size for name in expected)
    require(shutil.disk_usage(destination.parent).free >= size * 2 + 2 * MAX_LOG,
            "F07", "insufficient workspace space")
    destination.mkdir()
    for name in expected:
        source_path = rooted(source, name)
        target = rooted(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
    assert_protected(destination, expected)
    require(selected_files(source, inputs) == expected, "F05", "source changed during snapshot")


@contextlib.contextmanager
def workspace_lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a+b") as file:
        if file.seek(0, os.SEEK_END) == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise GateError("F06", "run already owned by another process") from error
        yield


def resolve_command(name):
    path = sys.executable if name == "python" else shutil.which(name)
    require(bool(path), "F02", f"runtime dependency missing: {name}")
    require(Path(path).suffix.lower() not in {".cmd", ".bat", ".ps1"}, "F14", "use a native executable")
    return path


def collect_output(pipe, collected, tracker):
    try:
        for chunk in iter(lambda: pipe.read(8192), b""):
            if tracker["stop"]:
                break
            room = MAX_LOG - len(collected)
            collected.extend(chunk[:max(room, 0)])
            tracker["truncated"] |= len(chunk) > room
    except OSError:
        tracker["read_error"] = True
    finally:
        pipe.close()


def stop_process(process):
    if os.name == "nt":
        root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        binary = root / "System32" / "taskkill.exe"
        try:
            result = subprocess.run([str(binary), "/PID", str(process.pid), "/T", "/F"],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=8, check=False)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return True


def process_group_alive(process):
    if os.name == "nt":
        return False
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    return True


def local_environment():
    preserved = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TMP", "TEMP",
                 "TMPDIR", "LANG", "LC_ALL", "PROGRAMFILES", "PROGRAMFILES(X86)",
                 "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "LOCALAPPDATA", "APPDATA", "HOME")
    result = {key: value for key, value in os.environ.items() if key.upper() in preserved}
    result.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", GIT_TERMINAL_PROMPT="0",
                  GIT_OPTIONAL_LOCKS="0")
    return result


def run_command(argv, cwd, timeout, log):
    env = local_environment()
    env["VIA_CLOSEOUT_WORKSPACE"] = str(cwd)
    platform_flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, **platform_flags)
    except OSError as error:
        raise GateError("F02", "failed to start local executable") from error
    collected = bytearray()
    tracker = {"stop": False, "truncated": False, "read_error": False}
    reader = threading.Thread(target=collect_output, args=(process.stdout, collected, tracker), daemon=True)
    reader.start()
    timed_out = False
    cleaned = True
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        cleaned = stop_process(process)
    except BaseException:
        stop_process(process)
        if process.poll() is None:
            with contextlib.suppress(OSError):
                process.kill()
        raise
    if process.poll() is None:
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)
            cleaned = False
    if process_group_alive(process):
        stop_process(process)
        if not timed_out:
            cleaned = False
    reader.join(timeout=1.5)
    if reader.is_alive():
        tracker["stop"] = True
        cleaned = False
    raw = bytes(collected)
    write_atomic(log, raw)
    return {"exit": process.returncode, "timeout": timed_out,
            "cleaned": cleaned and not tracker["read_error"], "truncated": tracker["truncated"],
            "log_sha256": digest(raw), "log_file": log.name}


def select(value, path):
    require(isinstance(path, list) and len(path) <= 16, "F16", "JSON assertion path")
    for part in path:
        if isinstance(value, dict) and isinstance(part, str) and part in value:
            value = value[part]
        elif isinstance(value, list) and type(part) is int and 0 <= part < len(value):
            value = value[part]
        else:
            raise GateError("F16", "JSON assertion path missing")
    return value


def check_output(path, format_name, assertions):
    require(path.is_file() and path.stat().st_size > 0, "F24", "fresh evidence missing")
    if format_name == "json":
        value = read_json(path)
        for item in assertions:
            require(isinstance(item, dict) and "equals" in item, "F16", "invalid assertion")
            actual = select(value, item.get("path"))
            require(encoded(actual) == encoded(item["equals"]), "F16", "JSON assertion failed")
        return {"assertions": len(assertions), "sha256": file_sha(path)}
    require(path.stat().st_size <= MAX_JSON, "F11", "JUnit size limit")
    raw = path.read_bytes()
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "F16", "JUnit declarations forbidden")
    try:
        tree = ET.fromstring(raw)
    except ET.ParseError as error:
        raise GateError("F16", "JUnit parse failure") from error
    require(tree.tag in ("testsuites", "testsuite"), "F16", "JUnit root")
    rows = list(tree.iter("testcase"))
    require(bool(rows) and any(row.find("skipped") is None for row in rows), "F22", "no executed test case")
    require(not any(row.find(tag) is not None for row in rows for tag in ("failure", "error")), "F16", "JUnit failures")
    require(not any(row.find("skipped") is not None for row in rows), "F22", "JUnit contains skipped cases")
    return {"cases": len(rows), "sha256": digest(raw)}


def csv_rows(path, keys):
    require(path.is_file() and path.stat().st_size <= MAX_JSON, "F25", "CSV absent or too large")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        require(set(keys) <= set(columns) and len(set(columns)) == len(columns),
                "F25", "invalid CSV headers")
        rows = {}
        for row in reader:
            require(None not in row and all(value is not None for value in row.values()),
                    "F25", "CSV row width mismatch")
            ident = tuple(row[k] for k in keys)
            require(all(ident) and ident not in rows, "F25", "empty or duplicate CSV key")
            rows[ident] = row
    require(bool(rows), "F25", "empty CSV")
    return set(columns), rows


def check_native_receipt(path, action):
    report = read_json(path)
    expected = "via.matrix.qa/1" if action == "selftest" else "via.matrix.resilience.qa/1"
    require(isinstance(report, dict) and report.get("schema") == expected and
            report.get("version") == "v0194" and report.get("status") == "PASS" and
            type(report.get("tests")) is int and report["tests"] >= (45 if action == "selftest" else 22) and
            report["tests"] == report.get("passed") and report.get("failures") == report.get("errors") == 0,
            "F16", "native fixture evidence did not pass")
    if action == "resilience-test":
        rows = report.get("controls", [])
        require(report.get("engine_sha256") == NATIVE_SHA and len(rows) == 20 and
                {r.get("id") for r in rows if r.get("status") == "PASS"} ==
                {f"F{n:02}" for n in range(1, 21)}, "F18", "native fault evidence mismatch")
    return {"tests": report["tests"], "sha256": file_sha(path), "scope": "NATIVE_ISOLATED_FIXTURE"}


def run_check(check, candidate, local, outcomes):
    kind, name = check["kind"], check["id"]
    if kind == "closeout":
        require(all(item["status"] == "PASS" for item in outcomes.values()),
                "F30", "upstream evidence incomplete")
        return {"tracked_process_scope": "POSIX_PROCESS_GROUP" if os.name != "nt" else "WINDOWS_PARENT_AND_PIPES_TASKKILL_ON_TIMEOUT"}
    if kind == "python_ast":
        target = rooted(candidate, check["path"])
        require(target.is_file() and target.stat().st_size <= MAX_JSON, "F11", "Python input missing or too large")
        source = target.read_bytes()
        try:
            syntax = ast.parse(source, filename=target.name)
            compile(syntax, target.name, "exec")
        except (SyntaxError, ValueError, RecursionError) as error:
            raise GateError("F11", "Python parse or compile failed") from error
        return {"sha256": digest(source), "definitions": sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in ast.walk(syntax))}
    if kind == "file":
        target = rooted(candidate, check["path"])
        require(target.is_file() and target.stat().st_size > 0, "F24", "required file absent or empty")
        return {"sha256": file_sha(target)}
    if kind == "json":
        return check_output(rooted(candidate, check["path"]), "json", check.get("assertions", []))
    if kind == "csv_equal":
        target, reference = (rooted(candidate, check[p]) for p in ("path", "reference"))
        actual, expected = csv_rows(target, check["key"]), csv_rows(reference, check["key"])
        require(actual == expected, "F25", "CSV columns, keys or values differ")
        return {"rows": len(actual[1]), "sha256": file_sha(target), "reference_sha256": file_sha(reference)}
    if kind == "parquet":
        try:
            import pyarrow.parquet as parquet
        except ImportError as error:
            raise GateError("F02", "pyarrow required by this check") from error
        target = rooted(candidate, check["path"])
        require(target.is_file(), "F24", "Parquet file missing")
        try:
            file = parquet.ParquetFile(target)
            require(file.metadata.num_rows > 0 and set(check.get("columns", [])) <= set(file.schema.names),
                    "F16", "Parquet contract")
        except (ValueError, OSError) as error:
            raise GateError("F16", "Parquet format could not be opened") from error
        return {"rows": file.metadata.num_rows, "sha256": file_sha(target)}

    if kind == "native_matrix":
        require(NATIVE.is_file() and file_sha(NATIVE) == NATIVE_SHA, "F18", "v0194 executable hash")
        directory = local / name
        expected = directory / ("selftest.json" if check["action"] == "selftest" else "resilience_tests.json")
        argv = [sys.executable, "-B", str(NATIVE), "matrix", check["action"],
                "--out", str(directory), "--roots", str(candidate)]
    elif kind == "agentos_matrix":
        engine = rooted(candidate, check["path"])
        require(engine.is_file() and file_sha(engine) == AGENTOS_SHA, "F18", "v0300 executable hash")
        require(importlib.util.find_spec("pyarrow") is not None, "F02", "v0300 strict matrix requires pyarrow")
        expected = None
        argv = [sys.executable, "-B", str(engine), "--matrix-test", "--data-dir", str(local / name)]
    else:
        argv = [resolve_command(check["argv"][0]), *check["argv"][1:]]
        expected = rooted(candidate, check["output"])
    if expected is not None:
        require(not expected.exists(), "F24", "evidence path already exists before command")
    attempts = []
    for number in range(1, 2 + int(check.get("retry_timeout", False))):
        log = local / f"{name}.{number}.log"
        command = run_command(argv, candidate, check.get("timeout", 120), log)
        attempts.append(command)
        save(local / f"{name}.{number}.command.json", command)
        require(command["cleaned"], "F13", "tracked process cleanup failed")
        if not command["timeout"]:
            break
        if expected is not None and expected.exists():
            raise GateError("F24", "timed-out command produced partial evidence")
    require(not command["timeout"], "F13", "test command timed out")
    require(command["exit"] == 0, "F16", "test command returned nonzero")
    if kind == "native_matrix":
        result = check_native_receipt(expected, check["action"])
    elif kind == "agentos_matrix":
        report = read_json(log, MAX_LOG)
        require(isinstance(report, dict) and isinstance(report.get("gate"), dict) and
                report["gate"].get("local_reference_pass") is True and
                type(report.get("cases")) is int and report["cases"] >= 63,
                "F16", "v0300 result gate incomplete")
        result = {"cases": report["cases"], "scope": "V0300_LOCAL_REFERENCE"}
    else:
        expected = rooted(candidate, check["output"])
        result = check_output(expected, check["format"], check.get("assertions", []))
    if len(attempts) > 1:
        raise GateError("F23", "passed only after timeout retry")
    return {**result, "command": command}


def compact_receipt(row):
    return {k: row[k] for k in ("id", "stage", "status", "code", "round", "requirements", "proof") if k in row}


def make_receipt(check, label, status, code=None, detail=None, proof=None):
    row = {"id": check["id"], "stage": check["stage"], "status": status,
           "round": label, "requirements": check.get("requirements", [])}
    if code:
        row.update(code=code, detail=detail)
    if proof:
        row["proof"] = {k: v for k, v in proof.items() if k != "command"}
    return row


def changed_paths(first, second):
    return sorted(name for name in set(first) | set(second) if first.get(name) != second.get(name))


def graphify_index(candidate, output, plan, protected):
    setting = plan.get("graphify")
    if not setting:
        return {"state": "DISABLED"}
    exe = shutil.which("graphify")
    try:
        require(isinstance(setting, dict) and isinstance(setting.get("sha256"), str)
                and HEX.fullmatch(setting["sha256"]), "F18", "Graphify executable pin required")
        require(bool(exe), "F02", "Graphify CLI missing")
        require(Path(exe).suffix.lower() not in {".cmd", ".bat", ".ps1"} and
                file_sha(Path(exe)) == setting["sha256"], "F18", "Graphify executable hash")
        output.mkdir()
        command = run_command([exe, "extract", ".", "--code-only", "--out", str(output)],
                              candidate, 120, output / "graphify.log")
        require(command["cleaned"] and not command["timeout"] and command["exit"] == 0,
                "F18", "Graphify code-only execution failed")
        graph_path = output / "graphify-out" / "graph.json"
        graph = read_json(graph_path)
        require(isinstance(graph, dict) and isinstance(graph.get("nodes"), list), "F18", "Graphify graph schema")
        edges = graph.get("links", graph.get("edges", []))
        require(isinstance(edges, list), "F18", "Graphify edge schema")
        return {"state": "INDEXED", "nodes": len(graph["nodes"]), "edges": len(edges),
                "graph_sha256": file_sha(graph_path)}
    except GateError as error:
        return {"state": "UNAVAILABLE", "code": error.code}
    finally:
        assert_protected(candidate, protected)


def graph_impact(path, changed, workspace):
    if not path.is_file():
        return set()
    graph = read_json(path)
    if not isinstance(graph, dict):
        return set()
    files = {}
    for node in graph.get("nodes", []):
        if not isinstance(node, dict) or not isinstance(node.get("id"), (str, int)):
            continue
        origin = node.get("source_file")
        if isinstance(origin, str):
            selected = Path(origin)
            if selected.is_absolute():
                if not selected.is_relative_to(workspace):
                    continue
                selected = selected.relative_to(workspace)
            name = selected.as_posix()
            if not name.startswith("../"):
                files[node["id"]] = name
    starting = {identity for identity, name in files.items() if name in changed}
    impacted = set(changed)
    for edge in graph.get("links", graph.get("edges", [])):
        if not isinstance(edge, dict):
            continue
        source, target = edge.get("source"), edge.get("target")
        if isinstance(source, (str, int)) and isinstance(target, (str, int)):
            if source in starting and target in files:
                impacted.add(files[target])
            if target in starting and source in files:
                impacted.add(files[source])
    return impacted


def execute_round(plan, source, protected, epoch, state, run_dir, label, selection=None, prior=None,
                  progress=False, graph=False, changed=None):
    directory = epoch / label
    directory.mkdir()
    candidate = directory / "candidate"
    logs = directory / "logs"
    logs.mkdir()
    snapshot(source, list(protected), protected, candidate)
    if graph:
        state["graphify"] = graphify_index(candidate, directory / "graph", plan, protected)
        if changed and state["graphify"]["state"] == "INDEXED":
            graph_file = directory / "graph/graphify-out/graph.json"
            related = graph_impact(graph_file, set(changed), candidate)
            impacted = sorted(impact_checks(plan, set(), related))
            state["graphify"].update(related_files=len(related), related_checks=len(impacted),
                                     check_ids=impacted[:MAX_MCP_CASES])
    outcomes = {}
    for index, check in enumerate(plan["checks"], 1):
        name = check["id"]
        if selection is not None and name not in selection:
            outcomes[name] = prior[name]
            continue
        replay_safe = check.get("replay_safe", check["kind"] != "command")
        state["replay_safe"] = state["replay_safe"] and replay_safe
        state.update(active={"round": label, "check": name, "stage": check["stage"],
                             "index": index, "total": len(plan["checks"])})
        save(run_dir / "state.json", state)
        if progress:
            print(f"[{label} {index}/{len(plan['checks'])}] {check['stage']} · {name}",
                  file=sys.stderr, flush=True)
        if any(outcomes[d]["status"] != "PASS" for d in check.get("depends", [])):
            row = make_receipt(check, label, "SKIPPED")
        else:
            try:
                proof = run_check(check, candidate, logs, outcomes)
                row = make_receipt(check, label, "PASS", proof=proof)
            except GateError as error:
                row = make_receipt(check, label, "REVIEW" if error.code == "F23" else "FAIL",
                                   error.code, error.detail)
            except (OSError, UnicodeError, TypeError, csv.Error, RecursionError) as error:
                row = make_receipt(check, label, "FAIL", "F11", type(error).__name__)
        try:
            assert_protected(candidate, protected)
        except GateError:
            row = make_receipt(check, label, "FAIL", "F28", "test modified protected input")
        outcomes[name] = row
        save(directory / "receipts" / (name + ".json"), row)
        if row.get("code") == "F28":
            break
    for check in plan["checks"]:
        if check["id"] not in outcomes:
            row = make_receipt(check, label, "SKIPPED")
            outcomes[check["id"]] = row
            save(directory / "receipts" / (check["id"] + ".json"), row)
    return outcomes


def repair_candidate(rules, seed, protected, destination, baseline):
    selected = [rule for rule in rules if baseline[rule["trigger"]]["status"] == "FAIL"]
    if not selected or any(row.get("code") in ("F05", "F13", "F28") for row in baseline.values()):
        return [], protected
    touched, prepared = set(), []
    for rule in selected:
        name = rule["path"]
        require(name in protected and name.casefold() not in touched, "F29", "repair file scope or collision")
        touched.add(name.casefold())
        require(protected[name] == rule["expected_sha256"], "F29", "repair base hash changed")
        obj = read_json(rooted(seed, name))
        require(isinstance(obj, dict), "F29", "repair JSON object required")
        member, action = rule["key"], rule["op"]
        if action == "add_missing":
            require(member not in obj, "F29", "default would overwrite a value")
            obj[member] = rule["value"]
        else:
            require(member in obj and encoded(obj[member]) == encoded(rule["expected"]),
                    "F29", "repair precondition differs")
            if action == "rename_key":
                require(rule["new_key"] not in obj, "F29", "alias destination already exists")
                obj[rule["new_key"]] = obj.pop(member)
            else:
                obj[member] = rule["value"]
        payload = encoded(obj) + b"\n"
        require(digest(payload) != protected[name], "F29", "repair made no change")
        prepared.append((rule["id"], name, payload))
    snapshot(seed, list(protected), protected, destination)
    repaired, journal = dict(protected), []
    for identity, name, payload in prepared:
        write_atomic(rooted(destination, name), payload)
        repaired[name] = digest(payload)
        journal.append({"rule": identity, "path": name, "before": protected[name], "after": repaired[name]})
    assert_protected(destination, repaired)
    return journal, repaired


def check_paths(check):
    return {path for path in (check.get("path"), check.get("reference"), *check.get("watch", []),
                              *check.get("argv", [])[1:]) if isinstance(path, str)}


def impact_checks(plan, repairs, linked_files):
    by_name = {row["id"]: row for row in plan["checks"]}
    chosen = {rule["trigger"] for rule in plan["repairs"] if rule["id"] in repairs}
    chosen.update(row["id"] for row in plan["checks"] if linked_files.intersection(check_paths(row)))
    for row in plan["checks"]:
        if row["kind"] != "closeout" and chosen.intersection(row.get("depends", [])):
            chosen.add(row["id"])
    for row in reversed(plan["checks"]):
        if row["id"] in chosen and row["kind"] != "closeout":
            chosen.update(row.get("depends", []))
    return {name for name in chosen if by_name[name]["kind"] != "closeout"}


def failure_rows(outcomes, extra):
    result = {}
    for row in list(outcomes.values()) + extra:
        code = row.get("code")
        if code:
            signature = digest(encoded([code, row["id"], row.get("stage")]))[:16]
            result[signature] = {"fingerprint": signature, "case": code,
                                 "check": row["id"], "stage": row.get("stage")}
    return list(result.values())


def phase_counts(outcomes):
    return {stage: {state: sum(x["stage"] == stage and x["status"] == state for x in outcomes.values())
                    for state in ("PASS", "FAIL", "REVIEW", "SKIPPED")} for stage in STAGES}


def report_html(summary, faults, outcomes):
    def cell(value):
        return f"<td>{html.escape(str(value))}</td>"

    rows = "".join("<tr>" + "".join(map(cell, [label, *summary["phases"][stage].values()])) + "</tr>"
                   for stage, label in zip(STAGES, STAGE_LABELS))
    checks = "".join("<tr>" + "".join(map(cell, [row["id"], row["stage"], row["round"],
                                                  row["status"], row.get("code", "")])) + "</tr>"
                     for row in outcomes.values())
    matrix = "".join("<tr>" + "".join(map(cell, [row["id"], row["priority"], row["name"], row["solution"]])) + "</tr>"
                     for row in faults)
    return f"""<!doctype html><html lang="zh-Hant"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>VCGC 測試整合收尾</title>
<style>body{{margin:18px auto;padding:0 12px;max-width:1100px;background:#121b20;color:#edf3f4;font:13px/1.55 system-ui,sans-serif}}
header{{display:flex;align-items:center;gap:12px;border-bottom:1px solid #40515b;padding-bottom:10px}}
.seal{{font:30px serif;border:1px solid #b49354;color:#e0c484;padding:3px 10px}}h1,h2,p{{margin:3px 0}}h1{{font-size:20px}}h2{{font-size:15px;margin-top:16px}}
small,th{{color:#e0c484}}table{{border-collapse:collapse;width:100%;min-width:460px}}th,td{{text-align:left;padding:5px 8px;border:1px solid #40515b}}
.scroll{{overflow:auto}}code{{overflow-wrap:anywhere}}</style>
<header><div class="seal">理</div><div><small>VERITAS INTELLIGENCE ANALYTICS</small><h1>VCGC 測試整合收尾</h1><p>五階段測試 · 反饋 · 證據</p></div></header>
<p><strong>{html.escape(summary["state"])}</strong> · <code>{summary["run_id"]}</code></p>
<p>候選副本修正 {summary["repairs"]} 項 · 正式部署待原生驗收</p>
<h2>測試矩陣</h2><div class="scroll"><table><thead><tr><th>階段</th><th>通過</th><th>失敗</th><th>待確認</th><th>略過</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>測試收據</h2><div class="scroll"><table><thead><tr><th>檢查</th><th>階段</th><th>輪次</th><th>結果</th><th>案例</th></tr></thead><tbody>{checks}</tbody></table></div>
<h2>30 項故障與處置</h2><div class="scroll"><table><thead><tr><th>編號</th><th>優先</th><th>情境</th><th>處置</th></tr></thead><tbody>{matrix}</tbody></table></div></html>"""


def build_archive(epoch):
    files = {}
    for directory in epoch.iterdir():
        if directory.is_dir() and directory.name in ("baseline", "impact", "final"):
            for label in ("receipts", "logs"):
                folder = directory / label
                if folder.exists():
                    for current, dirs, names in os.walk(folder, followlinks=False):
                        require(not any((Path(current) / d).is_symlink() for d in dirs), "F14", "archive linked directory")
                        for name in names:
                            target = Path(current) / name
                            rel = target.relative_to(epoch).as_posix()
                            files[rel] = file_sha(rooted(epoch, rel))
    for name in ("summary.json", "report.html", "repairs.json", "provenance.json", "evidence.json"):
        path = epoch / name
        if path.is_file():
            files[name] = file_sha(path)
    for name in ("baseline/graph/graphify-out/graph.json", "baseline/graph/graphify.log"):
        path = epoch / name
        if path.is_file():
            files[name] = file_sha(rooted(epoch, name))
    for name, checksum in read_json(epoch / "evidence.json").items():
        require(file_sha(rooted(epoch, name)) == checksum, "F30", "evidence changed before closeout")
        files[name] = checksum
    save(epoch / "archive.json", files)
    return file_sha(epoch / "archive.json")


def completed_run(home, identity, verify=True):
    directory = home / "runs" / run_id(identity)
    data = read_json(directory / "state.json")
    if not data.get("archive_sha256"):
        return data, None, None
    epoch = rooted(directory, "epochs/" + key(data["epoch"]))
    manifest = epoch / "archive.json"
    require(file_sha(manifest) == data["archive_sha256"], "F30", "archive manifest changed")
    if verify:
        for name, checksum in read_json(manifest).items():
            target = rooted(epoch, name)
            require(target.is_file() and file_sha(target) == checksum, "F30", "archived evidence changed")
    return data, epoch, read_json(epoch / "summary.json")


def evidence_artifacts(plan, epoch, outcomes):
    artifacts = {}
    for check in plan["checks"]:
        row = outcomes[check["id"]]
        checksum = row.get("proof", {}).get("sha256")
        if not checksum or check["kind"] != "command" or row["status"] != "PASS":
            continue
        name = f"{row['round']}/candidate/{check['output']}"
        artifacts[name] = checksum
    return artifacts


def finish_run(state, directory, epoch, plan, outcomes, extras, journal, previous):
    phase = phase_counts(outcomes)
    failures = failure_rows(outcomes, extras)
    summary = {"run_id": state["run_id"], "profile": plan["id"], "state":
               "PASS_LOCAL" if not failures and all(x["status"] == "PASS" for x in outcomes.values()) else "BLOCKED",
               "phases": phase, "failures": failures, "repairs": len(journal),
               "changed_inputs": previous, "graphify": state.get("graphify", {"state": "DISABLED"}),
               "production_release": "NATIVE_ACCEPTANCE_REQUIRED"}
    save(epoch / "evidence.json", evidence_artifacts(plan, epoch, outcomes))
    save(epoch / "summary.json", summary)
    write_atomic(epoch / "report.html", report_html(summary, cases(), outcomes).encode("utf-8"))
    archive_sha = build_archive(epoch)
    state.update(state=summary["state"], active=None, archive_sha256=archive_sha, finished=stamp())
    save(directory / "state.json", state)
    return summary


def load_profile(path, expected_sha=None):
    path = path.resolve()
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON + 1)
    require(len(raw) <= MAX_JSON, "F11", "profile size limit")
    require(expected_sha is None or digest(raw) == expected_sha, "F15", "preselected MCP profile changed")
    plan = validate_profile(decode(raw))
    source = (path.parent / plan["source"]).resolve()
    return plan, source


def runtime_signature(plan):
    versions = {}
    for name in ("pyarrow", "pytest", "graphifyy"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    commands = {check["argv"][0] for check in plan["checks"] if check["kind"] == "command"}
    if plan.get("graphify"):
        commands.add("graphify")
    binary_paths = {name: sys.executable if name == "python" else shutil.which(name) for name in commands}
    return {"packages": versions, "binaries": {
        name: {"path": path, "sha256": file_sha(Path(path))} if path else None for name, path in binary_paths.items()
    }, "native_sha256": file_sha(NATIVE) if NATIVE.is_file() else None}


def run_pipeline(home, profile, identity, previous_id=None, progress=False, graphify_sha=None, profile_sha=None):
    plan, source = load_profile(profile, profile_sha)
    if graphify_sha:
        require(HEX.fullmatch(graphify_sha), "F18", "invalid Graphify executable pin")
        plan["graphify"] = {"sha256": graphify_sha}
    identity = run_id(identity)
    require(home.resolve() != source, "F14", "state root equals source root")
    protected = selected_files(source, plan["inputs"])
    run_root = home / "runs" / identity
    require(not any(rooted(source, name).is_relative_to(run_root) for name in protected),
            "F14", "state directory included in the input scope")
    context = {"plan": digest(encoded(plan)), "engine": file_sha(Path(__file__)),
               "python": platform.python_version(), "platform": platform.platform(),
               "interpreter": str(Path(sys.executable).resolve()), "source": str(source),
               "inputs": protected, "runtime": runtime_signature(plan)}
    fingerprint = digest(encoded(context))
    previous = None
    delta_paths = None
    if previous_id:
        require(run_id(previous_id) != identity, "F14", "previous run ID equals current")
        _, old, old_summary = completed_run(home, previous_id)
        require(old is not None and old_summary["profile"] == plan["id"],
                "F15", "previous run needs sealed evidence for the same profile")
        historical = read_json(old / "provenance.json")
        delta_paths = changed_paths(historical["inputs"], protected)
        previous = len(delta_paths)
    with workspace_lock(run_root):
        status_file = run_root / "state.json"
        if status_file.exists():
            state = read_json(status_file)
            require(state["fingerprint"] == fingerprint, "F15", "input, profile, engine or environment changed; start a new run")
            if state.get("archive_sha256"):
                return completed_run(home, identity)[2]
            require(state.get("replay_safe"), "F09", "interrupted non-replay-safe check; reconcile before a new run")
        epoch_id = uuid.uuid4().hex
        epoch = run_root / "epochs" / epoch_id
        epoch.mkdir(parents=True)
        state = {"run_id": identity, "profile": plan["id"], "state": "RUNNING",
                 "epoch": epoch_id, "fingerprint": fingerprint, "replay_safe": True, "started": stamp()}
        save(status_file, state)
        save(epoch / "provenance.json", context)
        seed = epoch / "seed"
        snapshot(source, plan["inputs"], protected, seed)
        baseline = execute_round(plan, seed, protected, epoch, state, run_root, "baseline",
                                 progress=progress, graph=True, changed=delta_paths)
        outcomes, extras, journal = baseline, [], []
        repaired = epoch / "repaired"
        try:
            journal, hashes = repair_candidate(plan.get("repairs", []), seed, protected, repaired, baseline)
        except GateError as error:
            extras.append({"id": "repair-guard", "stage": "RESULT_VERIFICATION", "code": error.code})
        if journal:
            paths = {row["path"] for row in journal}
            rule_ids = {row["rule"] for row in journal}
            graph = epoch / "baseline/graph/graphify-out/graph.json"
            initial = impact_checks(plan, rule_ids, paths)
            if state["graphify"]["state"] == "INDEXED":
                code_paths = {path for check in plan["checks"] if check["id"] in initial
                              for path in check_paths(check) if path in protected}
                paths.update(graph_impact(graph, paths | code_paths, epoch / "baseline/candidate"))
            selection = impact_checks(plan, rule_ids, paths)
            outcomes = execute_round(plan, repaired, hashes, epoch, state, run_root, "impact",
                                     selection, baseline, progress)
            if all(outcomes[name]["status"] == "PASS" for name in selection):
                outcomes = execute_round(plan, repaired, hashes, epoch, state, run_root, "final", progress=progress)
                if any(row["status"] != "PASS" for row in outcomes.values()):
                    extras.append({"id": "final-regression", "stage": "CLOSE_OUT", "code": "F30"})
        try:
            source_stable = selected_files(source, plan["inputs"]) == protected
        except (GateError, OSError):
            source_stable = False
        if not source_stable:
            extras.append({"id": "source-changed", "stage": "CLOSE_OUT", "code": "F05"})
        save(epoch / "repairs.json", journal)
        return finish_run(state, run_root, epoch, plan, outcomes, extras, journal, previous)


def feedback(home, identity, since=None, budget=MAX_FEEDBACK):
    require(type(budget) is int and 500 <= budget <= MAX_FEEDBACK, "F27", "feedback budget")
    state, _, summary = completed_run(home, identity)
    if summary is None:
        return {k: state[k] for k in ("run_id", "profile", "state", "active") if k in state}
    failures = summary["failures"]
    existing = set()
    if since:
        _, _, prior = completed_run(home, since)
        require(prior is not None and prior["profile"] == summary["profile"],
                "F15", "comparison requires sealed evidence for the same profile")
        existing = {item["fingerprint"] for item in prior["failures"]}
    selected = [item for item in failures if item["fingerprint"] not in existing]
    result = {"run_id": identity, "state": summary["state"], "failures": [], "failure_total": len(failures),
              "unchanged": len(failures) - len(selected), "omitted": len(selected),
              "repairs": summary["repairs"], "next": "OPEN_REPORT" if not failures else "CHECK_CASE_AND_RECEIPT"}
    for item in selected:
        result["failures"].append(item)
        result["omitted"] -= 1
        if len(encoded(result)) > budget:
            result["failures"].pop()
            result["omitted"] += 1
            break
    return result


def evidence(home, identity, check, label=None):
    _, epoch, _ = completed_run(home, identity)
    require(epoch is not None, "F15", "run has no sealed evidence")
    check = key(check)
    if label is not None:
        require(label in ("baseline", "impact", "final"), "F14", "unknown round")
    for selected in (label,) if label else ("final", "impact", "baseline"):
        target = rooted(epoch, f"{selected}/receipts/{check}.json")
        if target.is_file():
            return compact_receipt(read_json(target))
    raise GateError("F24", "check receipt missing")


def probe_cli(native):
    results = {}
    with tempfile.TemporaryDirectory(prefix="vcgc-verb-") as temporary:
        work = Path(temporary)
        for name in ("matrix", "token", "functions"):
            log = work / f"{name}.log"
            receipt = run_command([sys.executable, "-B", str(native.resolve()), name, "--help"], work, 15, log)
            raw = log.read_text(encoding="utf-8", errors="replace")
            choices = []
            for match in re.finditer(r"\{([a-zA-Z0-9_-]+(?:,[a-zA-Z0-9_-]+)+)\}", raw):
                for word in match.group(1).split(","):
                    if not word.startswith("_") and word not in choices:
                        choices.append(word)
            verified_help = receipt["exit"] == 0 and not receipt["timeout"] and bool(
                re.search(r"(?im)^usage:", raw))
            results[name] = {"state": "HELP_OBSERVED" if verified_help else "NOT_VERIFIED",
                             "count": len(choices) if verified_help and choices else None,
                             "choices": choices if verified_help else []}
    return results


def omniroute(home, identity, model, port):
    from urllib.error import HTTPError, URLError
    from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    require(isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model),
            "F14", "OmniRoute model/Combo ID")
    require(type(port) is int and 1 <= port <= 65535, "F14", "OmniRoute port")
    _, epoch, summary = completed_run(home, identity)
    require(epoch is not None, "F15", "run has no sealed evidence")
    signals = sorted({(row["case"], row.get("stage") or "CLOSE_OUT") for row in summary["failures"]})[:MAX_MCP_CASES]
    if not signals:
        return {"state": "NO_FAILURE_NO_ROUTE"}
    api_key = os.environ.get("VIA_OMNIROUTE_API_KEY")
    require(bool(api_key) and not any(c in api_key for c in "\r\n"), "F02", "OmniRoute key environment variable missing")
    rows = [{"case": code, "stage": stage} for code, stage in signals]
    body = {"model": model, "messages": [
        {"role": "system", "content": "Return one short Traditional Chinese diagnostic suggestion. Use only the supplied VCGC failure codes and test phases. Do not claim evidence passed. Do not ask for logs or secrets."},
        {"role": "user", "content": encoded(rows).decode("utf-8")}],
        "max_tokens": 220, "stream": False}
    sig = digest(encoded({"port": port, "request": body}))
    directory = epoch / "routing"
    target = directory / f"{sig}.json"
    with workspace_lock(directory):
        if target.exists():
            return read_json(target)
        save(target, {"state": "IN_DOUBT", "at": stamp(), "case_count": len(rows), "request_bytes": len(encoded(body))})
        request = Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=encoded(body),
                          headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                          method="POST")
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=20) as stream:
                raw = stream.read(MAX_LOG + 1)
            require(len(raw) <= MAX_LOG, "F27", "gateway response exceeded limit")
            response = decode(raw)
            content = response["choices"][0]["message"]["content"]
            require(isinstance(content, str) and bool(content.strip()), "F16", "gateway advice unavailable")
            usage = response.get("usage")
            usage = {k: usage[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                     if type(usage.get(k)) is int and usage[k] >= 0} if isinstance(usage, dict) else None
            result = {"state": "ADVICE_ONLY", "case_count": len(rows), "request_bytes": len(encoded(body)),
                      "model": model, "usage": usage, "advice": content.strip()[:1500]}
        except HTTPError as error:
            result = {"state": "GATEWAY_REJECTED", "code": "F17", "http_status": error.code}
        except (URLError, TimeoutError, OSError):
            result = {"state": "IN_DOUBT", "code": "F17"}
        except (GateError, ValueError, TypeError, KeyError, IndexError):
            result = {"state": "UNUSABLE_RESPONSE", "code": "F16"}
        save(target, result)
        return result


def make_mcp(home, profile=None):
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    server = FastMCP("VCGC Test Closeout", log_level="ERROR")
    readonly = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    localrun = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    profile_sha = None
    if profile:
        profile_sha = file_sha(profile)
        load_profile(profile, profile_sha)

    @server.tool(annotations=readonly)
    def vcgc_closeout_verbs() -> dict[str, Any]:
        """List separately counted VCGC verb evidence and executable test adapters."""
        return inventory()

    @server.tool(annotations=readonly)
    def vcgc_closeout_status(run_id: str) -> dict[str, Any]:
        """Check a run state or archived five-stage counts."""
        state, _, result = completed_run(home, run_id)
        if result:
            return {k: result[k] for k in ("run_id", "state", "phases", "repairs", "graphify", "production_release")}
        return {k: state[k] for k in ("run_id", "profile", "state", "active") if k in state}

    @server.tool(annotations=readonly)
    def vcgc_closeout_feedback(run_id: str, since: str | None = None, budget: int = 1800) -> dict[str, Any]:
        """Return bounded, deduplicated failure fingerprints; compare with a previous run optionally."""
        return feedback(home, run_id, since, budget)

    @server.tool(annotations=readonly)
    def vcgc_closeout_case(case_id: str) -> dict[str, Any]:
        """Read one of the thirty failure causes and remedies."""
        return next((row for row in cases() if row["id"] == case_id), {"state": "CASE_NOT_FOUND"})

    @server.tool(annotations=readonly)
    def vcgc_closeout_evidence(run_id: str, check_id: str, round_name: str | None = None) -> dict[str, Any]:
        """Return one receipt's status and hashes. Raw logs stay on the host."""
        return evidence(home, run_id, check_id, round_name)

    if profile:
        @server.tool(annotations=localrun)
        async def vcgc_closeout_run(request_id: str, since: str | None = None) -> dict[str, Any]:
            """Execute the local operator's preselected profile. Use the same UUID for a retry."""
            identity = run_id(request_id)
            await asyncio.to_thread(run_pipeline, home, profile, identity, since, profile_sha=profile_sha)
            return feedback(home, identity, since, 1800)
    return server


def emit_config(home, profile=None):
    argv = ["-X", "utf8", str(Path(__file__).resolve()), "--home", str(home), "mcp"]
    if profile:
        load_profile(profile)
        argv += ["--profile", str(profile.resolve())]
    return {"mcpServers": {"vcgc-closeout": {"command": sys.executable, "args": argv}}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=DEFAULT_HOME)
    sub = parser.add_subparsers(dest="verb", required=True)
    verbs = sub.add_parser("verbs")
    verbs.add_argument("--native", type=Path, default=NATIVE)
    verbs.add_argument("--registry", type=Path)
    verbs.add_argument("--probe", action="store_true")
    sub.add_parser("cases")
    plan = sub.add_parser("plan")
    plan.add_argument("profile", type=Path)
    run = sub.add_parser("run")
    run.add_argument("profile", type=Path)
    run.add_argument("--id")
    run.add_argument("--since")
    run.add_argument("--open", action="store_true")
    run.add_argument("--graphify-sha")
    for label in ("status", "verify", "feedback", "omniroute", "evidence"):
        part = sub.add_parser(label)
        part.add_argument("run_id")
        if label == "feedback":
            part.add_argument("--since")
            part.add_argument("--budget", type=int, default=MAX_FEEDBACK)
        elif label == "omniroute":
            part.add_argument("--model", required=True)
            part.add_argument("--port", type=int, default=20128)
        elif label == "evidence":
            part.add_argument("check_id")
            part.add_argument("--round", choices=("baseline", "impact", "final"))
    for name in ("mcp", "mcp-config"):
        sub.add_parser(name).add_argument("--profile", type=Path)
    args = parser.parse_args(argv)
    home = args.home.resolve()
    exit_code = 0
    if args.verb == "verbs":
        result = inventory(args.native, args.registry)
        if args.probe:
            result["runtime_help"] = probe_cli(args.native)
    elif args.verb == "cases":
        result = cases()
    elif args.verb == "plan":
        profile, source = load_profile(args.profile)
        result = {"profile": profile["id"], "checks": len(profile["checks"]),
                  "requirements": len(profile["requirements"]), "root_available": source.is_dir()}
    elif args.verb == "run":
        identity = args.id or str(uuid.uuid4())
        summary = run_pipeline(home, args.profile, identity, args.since, progress=True,
                               graphify_sha=args.graphify_sha)
        result = {k: v for k, v in summary.items() if k != "failures"}
        result["failure_total"] = len(summary["failures"])
        exit_code = 0 if result["state"] == "PASS_LOCAL" else 2
        if args.open:
            _, epoch, _ = completed_run(home, identity)
            webbrowser.open((epoch / "report.html").as_uri())
    elif args.verb == "feedback":
        result = feedback(home, args.run_id, args.since, args.budget)
    elif args.verb == "evidence":
        result = evidence(home, args.run_id, args.check_id, args.round)
    elif args.verb == "omniroute":
        result = omniroute(home, args.run_id, args.model, args.port)
    elif args.verb in ("status", "verify"):
        state, epoch, summary = completed_run(home, args.run_id)
        if args.verb == "verify":
            require(epoch is not None, "F15", "run has no sealed evidence")
            result = {"run_id": args.run_id, "archive": "VERIFIED", "state": summary["state"],
                      "report": str(epoch / "report.html")}
        else:
            result = summary if summary else {k: state[k] for k in ("run_id", "profile", "state", "active") if k in state}
    elif args.verb == "mcp-config":
        result = emit_config(home, args.profile)
    else:
        make_mcp(home, args.profile).run(transport="stdio")
        return 0
    print(encoded(result).decode("utf-8"))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as error:
        print(encoded({"state": "BLOCKED", "code": error.code, "detail": error.detail}).decode("utf-8"),
              file=sys.stderr)
        raise SystemExit(2) from None
    except (OSError, ImportError) as error:
        print(encoded({"state": "BLOCKED", "code": "F02" if isinstance(error, ImportError) else "F07",
                       "detail": type(error).__name__}).decode("utf-8"), file=sys.stderr)
        raise SystemExit(2) from None
