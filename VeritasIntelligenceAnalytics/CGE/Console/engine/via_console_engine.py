"""VIA CGE v0501 ingest engine - stdlib only, read-only, no network."""
import ast
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

AST_MAX_BYTES = 2 * 1024 * 1024


def progress(pct, msg):
    sys.stdout.write("PROGRESS|%s|%s\n" % (pct, msg))
    sys.stdout.flush()


def read_text(path):
    with open(path, "rb") as handle:
        raw = handle.read(AST_MAX_BYTES)
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace"), "utf-8-replace"


def digest(path):
    hasher = hashlib.blake2s(digest_size=16)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(262144), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def first_line(text):
    if not text:
        return ""
    lines = text.strip().splitlines()
    return lines[0].strip()[:160] if lines else ""


def literal_preview(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    if isinstance(value, str):
        return value[:300]
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "%s(len=%d)" % (type(value).__name__, len(value))
    if isinstance(value, dict):
        return "dict(len=%d)" % len(value)
    return None


def collect_regex(tree):
    found = []

    def record(name, pattern, lineno):
        entry = {"name": name, "pattern": pattern[:300], "lineno": lineno,
                 "compile_ok": True, "error": ""}
        try:
            re.compile(pattern)
        except (re.error, RecursionError, OverflowError) as exc:
            entry["compile_ok"] = False
            entry["error"] = str(exc)[:200]
        found.append(entry)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            target = node.targets[0] if node.targets else None
            name = getattr(target, "id", None)
            if name and re.search(r"REGEX|PATTERN|RE_|_RE$|_RX|RX_|MATCH|EXTRACT", name, re.IGNORECASE):
                value = literal_preview(node.value)
                if isinstance(value, str) and value:
                    record(name, value, node.lineno)
        elif isinstance(node, ast.Call):
            func = node.func
            attr = getattr(func, "attr", None)
            mod = getattr(getattr(func, "value", None), "id", None)
            if mod == "re" and attr in ("compile", "match", "search", "fullmatch",
                                        "findall", "finditer", "sub", "split"):
                if node.args:
                    value = literal_preview(node.args[0])
                    if isinstance(value, str) and value:
                        record("re.%s@%d" % (attr, node.lineno), value, node.lineno)
    return found


def collect_cli(tree):
    flags = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "add_argument":
            for arg in node.args:
                value = literal_preview(arg)
                if isinstance(value, str) and value.startswith("-"):
                    flags.append(value)
    return sorted(set(flags))


def empty_shape():
    return {"parse_ok": False, "parse_error": "", "docstring": "", "functions": [],
            "classes": [], "constants": [], "regex": [], "imports": [],
            "cli_flags": [], "headings": [], "json_keys": []}


def analyze_python(text):
    out = empty_shape()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as exc:
        lineno = getattr(exc, "lineno", "?")
        out["parse_error"] = "line %s: %s" % (lineno, getattr(exc, "msg", str(exc)))[:200]
        return out
    out["parse_ok"] = True
    out["docstring"] = first_line(ast.get_docstring(tree) or "")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["functions"].append({
                "name": node.name,
                "args": [a.arg for a in node.args.args],
                "lineno": node.lineno,
                "doc": first_line(ast.get_docstring(node) or ""),
            })
        elif isinstance(node, ast.ClassDef):
            out["classes"].append({
                "name": node.name,
                "methods": [b.name for b in node.body
                            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))],
                "lineno": node.lineno,
                "doc": first_line(ast.get_docstring(node) or ""),
            })
        elif isinstance(node, ast.Assign):
            target = node.targets[0] if node.targets else None
            name = getattr(target, "id", None)
            if name and name.isupper():
                preview = literal_preview(node.value)
                if preview is not None:
                    out["constants"].append({"name": name, "value": preview,
                                             "lineno": node.lineno})

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    out["imports"] = sorted(imports)
    out["regex"] = collect_regex(tree)
    out["cli_flags"] = collect_cli(tree)
    return out


def analyze_markdown(text):
    out = empty_shape()
    out["parse_ok"] = True
    out["headings"] = [ln.strip()[:120] for ln in text.splitlines()
                       if ln.strip().startswith("#")][:30]
    return out


def analyze_json(text):
    out = empty_shape()
    try:
        data = json.loads(text)
    except (ValueError, RecursionError) as exc:
        out["parse_error"] = str(exc)[:200]
        return out
    out["parse_ok"] = True
    if isinstance(data, dict):
        out["json_keys"] = [str(k)[:60] for k in list(data.keys())[:40]]
    elif isinstance(data, list):
        out["json_keys"] = ["<array len=%d>" % len(data)]
    return out


def analyze_csv(text):
    out = empty_shape()
    out["parse_ok"] = True
    first = ""
    for line in text.splitlines():
        if line.strip():
            first = line
            break
    sep = "\t" if first.count("\t") > first.count(",") else ","
    out["json_keys"] = [c.strip().strip('"')[:60] for c in first.split(sep)][:40]
    return out


def main():
    manifest_path, out_path = sys.argv[1], sys.argv[2]
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if isinstance(manifest, dict):
        manifest = [manifest]

    modules = []
    total = max(len(manifest), 1)
    step = max(total // 50, 1)

    for index, item in enumerate(manifest):
        if index % step == 0:
            progress(int((index / float(total)) * 100),
                     "%d/%d %s" % (index, total, item.get("relpath", "")[-48:]))

        record = {
            "name": item.get("name", ""),
            "path": item.get("path", ""),
            "relpath": item.get("relpath", ""),
            "role": item.get("role", "NEW"),
            "module": item.get("module", "(root)"),
            "section": item.get("section", "OTHERS"),
            "kind": os.path.splitext(item.get("name", ""))[1].lower().lstrip("."),
            "exists": False, "size": 0, "sha": "", "mtime": "",
            "encoding": "", "loc": 0,
        }
        record.update(empty_shape())

        path = record["path"]
        if not path or not os.path.isfile(path):
            record["parse_error"] = "file not found"
            modules.append(record)
            continue

        try:
            stat = os.stat(path)
            record["exists"] = True
            record["size"] = stat.st_size
            record["sha"] = digest(path)
            record["mtime"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        except OSError as exc:
            record["parse_error"] = "stat/hash failed: %s" % str(exc)[:120]
            modules.append(record)
            continue

        if record["size"] > AST_MAX_BYTES:
            record["parse_error"] = "skipped: %d bytes over AST cap" % record["size"]
            modules.append(record)
            continue

        try:
            text, enc = read_text(path)
        except OSError as exc:
            record["parse_error"] = "read failed: %s" % str(exc)[:120]
            modules.append(record)
            continue

        record["encoding"] = enc
        record["loc"] = text.count("\n") + 1

        kind = record["kind"]
        if kind in ("py", "pyw"):
            record.update(analyze_python(text))
        elif kind in ("md", "txt", "rst"):
            record.update(analyze_markdown(text))
        elif kind == "json":
            record.update(analyze_json(text))
        elif kind == "csv":
            record.update(analyze_csv(text))
        else:
            record["parse_ok"] = True
            record["parse_error"] = "delegated to PowerShell AST"
        modules.append(record)

    payload = {
        "engine": "via_cge_ingest",
        "version": "v0504",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "count": len(modules),
        "modules": modules,
    }
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=1))
    progress(100, "inventory written: %d files" % len(modules))


if __name__ == "__main__":
    main()