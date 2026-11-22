#!/usr/bin/env python3
"""VIA ModuFuse v0101 | Python 3.11+ | 程式模組整合與去重引擎（前版「拳腳」）。

plan SOURCE         預覽可共用的程式碼、同名分支、來源指紋與去重位元組數
doctor              檢查 15 個支援套件與 Celeritas 路徑
build SOURCE        掃描一個 Python import root，在 TEMP 建立獨立 fnc_lib.py、稽核與精簡 Prompt
selftest            在暫存資料夾實測建置、分派、版本分支、異常與發布回復
serve SOURCE        使用 MCP stdio 提供一條建置指令，來源根目錄由啟動端指定
publish BUNDLE DEST / rollback DEST BACKUP    發布與還原本工具生成的單檔

SOURCE 是受信任引擎的共同匯入根目錄。有套件時選套件的上一層。收錄 .py；
資料檔、原生擴充與第三方套件須另備。建置只解析來源，實際 run 才匯入來源。
靜態註冊頂層公開函式與字典字面值 FNC_LIB_REGISTRY。方法與內部函式隨模組保留。
動態建立的 API 必須透過明確的字典鍵或公開轉接函式列出。可將 inputs 限定為工具子目錄。
同名行動可用 module::action 明確選版。Python API 保留同步、async、生成器及原始參數。
CLI 使用 JSON 可表示的參數與結果。--extras 額外輸出本機格式。全部操作可用 --help 查詢。
"""
from __future__ import annotations

import argparse
import ast
import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import contextlib
import functools
import hashlib
import importlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tokenize
from typing import Any
import zlib

# 01 · 集中設定
VERSION = "v0101"
DEFAULT_TEMP = Path(tempfile.gettempdir()) / "VIA_ModuFuse"
ACCEL_ENV = "VIA_CELERITAS_PATH"
MAX_WORKERS = 4
MIN_PYTHON = (3, 11)
IGNORE = {".git", ".hg", ".svn", ".venv", "venv", "__pycache__", "build", "dist",
          "site-packages", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "node_modules"}
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
MAGIC = "# VIA ModuFuse generated FNC-LIB v0101"
LEGACY_MAGIC = "# VIA QuanJiao generated FNC-LIB v0100"
LEGACY_TEMPLATE_SHA256 = "2c8d4714f1acb75020ae38578d56447c6fc25bf1d3f7053d28f1e513b8571fe2"
LIBS = {
    "joblib": ("joblib", "多檔平行掃描"),
    "psutil": ("psutil", "依可用記憶體限制工作數"),
    "asttokens": ("asttokens", "記錄函式來源 token 範圍"),
    "parso": ("parso", "補充語法錯誤定位"),
    "jsonschema": ("jsonschema", "檢核稽核資料契約"),
    "packaging": ("packaging", "檢查擴充套件版本相容性"),
    "more-itertools": ("more_itertools", "來源順序去重"),
    "msgpack": ("msgpack", "二進位稽核檔"),
    "zstandard": ("zstandard", "壓縮稽核 JSON"),
    "PyYAML": ("yaml", "YAML 調度目錄"),
    "XlsxWriter": ("xlsxwriter", "Excel 指令簽名稽核表"),
    "Pygments": ("pygments", "HTML 語法上色指令目錄"),
    "pydantic": ("pydantic", "MCP 輸入契約"),
    "mcp": ("mcp", "本機 stdio 巨集入口"),
    "anyio": ("anyio", "MCP 建置工作執行緒"),
}
MIN_VERSIONS = {"pydantic": "2", "mcp": "1.2"}
AUDIT_SCHEMA = {"type": "object", "required": ["version", "files", "actions", "backend"],
                "properties": {"files": {"type": "array", "minItems": 1},
                               "actions": {"type": "object", "minProperties": 1},
                               "backend": {"type": "string"}}}


@functools.lru_cache(maxsize=None)
def optional(name: str) -> Any:
    if importlib.util.find_spec(name) is None:
        return None
    return importlib.import_module(name)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_text(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)


def emit(obj: Any) -> None:
    sys.stdout.write(json_text(obj) + "\n")


def accelerator_path(arg: str | None) -> Path | None:
    candidate = arg or os.environ.get(ACCEL_ENV)
    if candidate:
        path = Path(candidate).expanduser().resolve(strict=True)
        if not path.is_file() or path.suffix.lower() != ".py":
            raise ValueError(f"加速器須為 .py 檔案：{path}")
        return path
    path = Path(__file__).resolve().with_name("VeritasCeleritas.py")
    if path.is_file():
        return path
    return None


# [VIA:ACCEL-BRIDGE] · 保留有序結果，辨識舊版回傳的 Exception 物件。
def parallel_scan(paths: list[Path], scan: Any, accel: str | None, workers: int) -> tuple[list, str]:
    if workers < 1:
        raise ValueError("workers 必須大於零")
    ps = optional("psutil")
    budget = max(1, ps.virtual_memory().available // (256 * 1024**2)) if ps else MAX_WORKERS
    count = min(workers, budget, len(paths))
    path = accelerator_path(accel)
    if path:
        spec = importlib.util.spec_from_file_location("_via_quanjiao_celeritas", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        with contextlib.redirect_stdout(sys.stderr):
            spec.loader.exec_module(module)
            results = list(module.parallel_map(scan, paths, max_workers=count, mode="thread"))
        backend = f"Celeritas {getattr(module, '__version__', '?')} | {path} | sha256={digest(path.read_bytes())}"
    elif count == 1:
        results, backend = list(map(scan, paths)), "serial"
    elif (job := optional("joblib")) is not None:
        results = job.Parallel(n_jobs=count, backend="threading")(job.delayed(scan)(p) for p in paths)
        backend = "joblib.threading"
    else:
        with ThreadPoolExecutor(max_workers=count) as pool:
            results = list(pool.map(scan, paths))
        backend = "stdlib.threads"
    if len(paths) != len(results):
        raise ValueError("加速器結果筆數不符")
    for path, item in zip(paths, results):
        if isinstance(item, Exception):
            raise ValueError(f"{path}: {item}") from item
        if item["origin"] != str(path):
            raise ValueError(f"加速器結果順序不符：{path}")
    return results, backend


# 02 · 靜態掃描、註冊與合規檢查
def module_id(rel: Path) -> str:
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    if not parts or any("." in p or "::" in p for p in parts):
        raise ValueError(f"模組路徑無法唯一識別，請選擇正確的匯入根目錄：{rel}")
    if parts[0] in sys.stdlib_module_names or parts[0] == "__main__":
        raise ValueError(f"來源與 Python 內建模組或執行入口同名：{rel}")
    return ".".join(parts)


def candidates(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError(f"需要來源資料夾：{root}")
    found = []
    def fail(error: OSError) -> None:
        raise error
    for parent, dirs, names in os.walk(root, onerror=fail):
        folder = Path(parent)
        dirs[:] = sorted(d for d in dirs if d not in IGNORE and not (folder / d).is_symlink()
                         and not (folder / d / "pyvenv.cfg").is_file())
        for name in sorted(names):
            path = folder / name
            if path.suffix != ".py":
                continue
            if path.is_symlink() or path.resolve() != path:
                raise ValueError(f"請使用實體來源：{path}")
            found.append(path)
    if not found:
        raise ValueError(f"沒有 Python 來源：{root}")
    return found


def static_aliases(tree: ast.Module, rel: str) -> dict:
    records = {}
    found = False
    for stmt in tree.body:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [getattr(stmt, "target", None)]
        if not any(isinstance(t, ast.Name) and t.id == "FNC_LIB_REGISTRY" for t in targets):
            continue
        value = getattr(stmt, "value", None)
        if found or not isinstance(value, ast.Dict):
            raise ValueError(f"{rel}: FNC_LIB_REGISTRY 需要唯一的字典字面值")
        found = True
        for key, val in zip(value.keys, value.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or not key.value or "::" in key.value:
                raise ValueError(f"{rel}: 註冊鍵須為非空字串常數，且不可含 ::")
            if key.value in records:
                raise ValueError(f"{rel}: 重複註冊鍵 {key.value}")
            records[key.value] = ast.unparse(val)
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.ctx, (ast.Store, ast.Del)):
            base = n.value
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {
            "update", "setdefault", "pop", "popitem", "clear", "__setitem__", "__delitem__"}:
            base = n.func.value
        elif isinstance(n, ast.AugAssign):
            base = n.target
        else:
            continue
        if isinstance(base, ast.Name) and base.id == "FNC_LIB_REGISTRY":
            raise ValueError(f"{rel}:{n.lineno} 動態註冊變更需先明列行動鍵")
    return records


def guard(node: Any) -> list[str]:
    args = node.args
    params = [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]
    defaults = [*args.defaults, *args.kw_defaults]
    issues = []
    if node.returns is None or any(a and a.annotation is None for a in params):
        issues.append("missing-type-hints")
    if not ast.get_docstring(node):
        issues.append("missing-docstring")
    if any(isinstance(v, (ast.List, ast.Set, ast.Dict, ast.ListComp, ast.DictComp, ast.SetComp))
           or (isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
               and v.func.id in {"list", "dict", "set"}) for v in defaults):
        issues.append("mutable-default")
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
           for n in ast.walk(node)):
        issues.append("print")
    return issues


def scan_file(path: Path, root: Path, snapshot: Path | None) -> dict:
    rel = path.relative_to(root)
    module = module_id(rel)
    raw = path.read_bytes()
    if snapshot is not None:
        backup = snapshot / rel
        backup.parent.mkdir(exist_ok=True, parents=True)
        backup.write_bytes(raw)
    encoding = tokenize.detect_encoding(io.BytesIO(raw).readline)[0]
    # Python 的來源行號採 universal newlines。以未改寫的 bytes 切片、還原。
    import re
    lines = re.findall(rb"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$", raw)
    source = raw.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")
    try:
        tree = ast.parse(source, filename=str(path))
        compile(tree, str(path), "exec", dont_inherit=True)
    except SyntaxError as exc:
        parser = optional("parso")
        hints = ""
        if parser:
            grammar = parser.load_grammar()
            hints = " / ".join(str(e) for e in grammar.iter_errors(grammar.parse(source)))
        raise ValueError(f"{path}:{exc.lineno} {exc.msg} {hints}") from exc
    records, chunks = {}, []
    token_lib = optional("asttokens")
    tokens = token_lib.ASTTokens(source, tree=tree) if token_lib else None
    pos = 0
    for node in tree.body:
        if not isinstance(node, FUNCTIONS):
            continue
        start = min(n.lineno for n in [node, *node.decorator_list]) - 1
        for segment in (lines[pos:start], lines[start:node.end_lineno]):
            if segment:
                chunks.append(b"".join(segment))
        pos = node.end_lineno
        if node.name.startswith("_"):
            continue
        if node.name in records:
            raise ValueError(f"{rel}:{node.lineno} 重複定義 {node.name}，請明確區分版本")
        record = {"definition_name": node.name, "kind": "function", "signature": ast.unparse(node.args),
                  "returns": ast.unparse(node.returns) if node.returns else None,
                  "ast_sha256": digest(ast.dump(node).encode()),
                  "source_sha256": digest(b"".join(lines[start:node.end_lineno])), "line": node.lineno,
                  "async": isinstance(node, ast.AsyncFunctionDef), "issues": guard(node)}
        if tokens:
            record["source_chars"] = list(tokens.get_text_range(node))
        records[node.name] = record
    if pos < len(lines):
        chunks.append(b"".join(lines[pos:]))
    for key, value in static_aliases(tree, str(rel)).items():
        if key in records and value != key:
            raise ValueError(f"{rel}: 舊註冊鍵與函式同名且對象不同：{key}")
        record = records.get(key, {}).copy() or records.get(value, {}).copy()
        record.update(kind="registry", target=value)
        records[key] = record
    if b"".join(chunks) != raw:
        raise ValueError(f"重建不一致：{rel}")
    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    order = optional("more_itertools")
    imports = list(order.unique_everseen(imports) if order else dict.fromkeys(imports))
    return {"origin": str(path), "path": rel.as_posix(), "module": module, "sha256": digest(raw),
            "imports": imports, "chunks": chunks, "actions": records}

# 03 · 產生可獨立匯入或當作 CLI 使用的單檔 FNC-LIB
RUNTIME = r'''
"""VIA ModuFuse FNC-LIB。list、verify、run ACTION [--variant MODULE] [--args JSON] [--kwargs JSON]。"""
import argparse
import asyncio
import base64
import contextlib
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import threading
import zlib

_DATA = json.loads(zlib.decompress(base64.b85decode(__PACKED__)))
# [ANCHOR:FNC_LIB_REGISTRY]
FNC_LIB_REGISTRY = _DATA["registry"]
VARIANTS = _DATA["variants"]
_ROOT = None
_LOCK = threading.RLock()


def reconstruct(entry):
    chunks = []
    for ref in entry["parts"]:
        crlf = isinstance(ref, list)
        key = ref[0] if crlf else ref
        raw = base64.b85decode(_DATA["blocks"][key])
        chunks.append(raw.replace(b"\n", b"\r\n") if crlf else raw)
    raw = b"".join(chunks)
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("來源指紋不符：" + entry["path"])
    return raw


def verify():
    for file in _DATA["files"]:
        compile(reconstruct(file), file["path"], "exec", dont_inherit=True)
    listed = [q for group in VARIANTS.values() for q in group]
    if len(listed) != len(set(listed)) or set(listed) != set(FNC_LIB_REGISTRY):
        raise ValueError("註冊筆數不守恆")
    return {"verified_files": len(_DATA["files"]), "qualified_actions": len(listed)}


def prepare():
    global _ROOT
    with _LOCK:
        if _ROOT is not None:
            return
        verify()
        temp = tempfile.TemporaryDirectory(prefix="via_fnc_")
        root = Path(temp.name)
        try:
            for file in _DATA["files"]:
                path = root / file["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(reconstruct(file))
            tops = {f["module"].split(".")[0] for f in _DATA["files"]}
            collisions = sorted(t for t in tops if t in sys.modules)
            if collisions:
                raise ImportError("已載入同名模組，請使用獨立 CLI 行程：" + ", ".join(collisions))
            sys.path.insert(0, str(root))
            _ROOT = temp
        except BaseException:
            temp.cleanup()
            raise


def resolve(action, variant=None):
    if variant:
        action = variant + "::" + action
    if action not in FNC_LIB_REGISTRY:
        choices = VARIANTS.get(action, [])
        if len(choices) != 1:
            raise KeyError("請指定 module::action：" + ", ".join(choices) if choices else "未知指令：" + action)
        action = choices[0]
    entry = FNC_LIB_REGISTRY[action]
    prepare()
    module = importlib.import_module(entry["module"])
    loaded = Path(module.__file__).resolve()
    if loaded != (Path(_ROOT.name) / entry["path"]).resolve():
        raise ImportError("載入來源與快照不符：" + str(loaded))
    name = entry["name"]
    fn = module.FNC_LIB_REGISTRY[name] if entry["kind"] == "registry" else getattr(module, name)
    if not callable(fn):
        raise TypeError(action + " 未繫結至可呼叫物件")
    return fn


def trigger_unified_engine(action_code, /, *args, **kwargs):
    """同步函式直接回傳；非同步函式回傳可 await 的物件。"""
    return resolve(action_code)(*args, **kwargs)


async def finish(awaitable):
    return await awaitable


def invoke(action, variant, positional, keywords):
    if not isinstance(positional, list) or not isinstance(keywords, dict):
        raise ValueError("args 需為 JSON 陣列，kwargs 需為 JSON 物件")
    with contextlib.redirect_stdout(sys.stderr):
        answer = resolve(action, variant)(*positional, **keywords)
        if inspect.isawaitable(answer):
            answer = asyncio.run(finish(answer))
    return answer


def batch(steps):
    """依序執行，pipe=true 將上一個結果當作第一個位置參數。"""
    if not isinstance(steps, list) or not steps:
        raise ValueError("batch 需要非空 JSON 陣列")
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not isinstance(step.get("action"), str):
            raise ValueError(f"步驟 {index + 1} 缺少 action")
        if set(step) - {"action", "variant", "args", "kwargs", "pipe"}:
            raise ValueError(f"步驟 {index + 1} 有未知欄位")
        if not isinstance(step.get("args", []), list) or not isinstance(step.get("kwargs", {}), dict):
            raise ValueError(f"步驟 {index + 1} 參數格式錯誤")
        if type(step.get("pipe", False)) is not bool or (index == 0 and step.get("pipe")):
            raise ValueError(f"步驟 {index + 1} 的 pipe 設定錯誤")
        if step.get("variant") is not None and not isinstance(step["variant"], str):
            raise ValueError(f"步驟 {index + 1} 的 variant 需為字串")
    answers = []
    for step in steps:
        positional = ([answers[-1]] if step.get("pipe") else []) + step.get("args", [])
        answers.append(invoke(step["action"], step.get("variant"), positional, step.get("kwargs", {})))
    return answers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    sub.add_parser("list")
    multi = sub.add_parser("batch", help="從 UTF-8 JSON 檔或 stdin 讀取一組步驟")
    multi.add_argument("file", nargs="?", default="-")
    run = sub.add_parser("run")
    run.add_argument("action")
    run.add_argument("--variant")
    run.add_argument("--args", default="[]")
    run.add_argument("--kwargs", default="{}")
    args = parser.parse_args()
    try:
        if args.cmd == "verify":
            answer = verify()
        elif args.cmd == "list":
            answer = VARIANTS
        elif args.cmd == "batch":
            text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8-sig")
            answer = batch(json.loads(text))
        else:
            answer = invoke(args.action, args.variant, json.loads(args.args), json.loads(args.kwargs))
        sys.stdout.write(json.dumps(answer, ensure_ascii=False, allow_nan=False) + "\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def canonical_block(raw: bytes) -> tuple[bytes, bool]:
    """僅轉換整段一致的 CRLF；混合換行或含單獨 CR 的片段原樣保存。"""
    if b"\r\n" in raw:
        lf = raw.replace(b"\r\n", b"\n")
        if b"\r" not in lf and lf.replace(b"\n", b"\r\n") == raw:
            return lf, True
    return raw, False


def index_sources(scans: list[dict], strict: bool) -> tuple[dict, list, dict, dict, dict]:
    blocks, files, registry = {}, [], {}
    variants = defaultdict(list)
    modules, raw_keys = {}, {}
    uses = defaultdict(int)
    raw_sizes = {}
    source_bytes = 0
    for s in scans:
        module = s["module"]
        if module in modules:
            raise ValueError(f"模組衝突：{s['path']} / {modules[module]}")
        modules[module] = s["path"]
        parts = []
        for chunk in s["chunks"]:
            data, crlf = canonical_block(chunk)
            key = digest(data)
            raw_hash = digest(chunk) if crlf else key
            blocks.setdefault(key, data)
            raw_keys[raw_hash] = key
            raw_sizes[raw_hash] = len(chunk)
            uses[key] += 1
            source_bytes += len(chunk)
            parts.append([key] if crlf else key)
        files.append({"path": s["path"], "module": module, "sha256": s["sha256"], "imports": s["imports"], "parts": parts})
        for name, info in s["actions"].items():
            qualified = f"{module}::{name}"
            if strict and info.get("issues"):
                raise ValueError(f"{qualified} 未通過 strict：{info['issues']}")
            registry[qualified] = {**info, "name": name, "module": module, "path": s["path"]}
            variants[name].append(qualified)
    for module in modules:
        parent = module.rpartition(".")[0]
        while parent:
            if parent in modules and not modules[parent].endswith("/__init__.py"):
                raise ValueError(f"模組遮蔽子套件：{modules[parent]} / {modules[module]}")
            parent = parent.rpartition(".")[0]
    if not registry:
        raise ValueError("來源中沒有可註冊的頂層公開函式或 FNC-LIB 行動鍵")
    for key, rec in registry.items():
        group = variants[rec["name"]]
        rec["routing"] = ("explicit-variant" if len(group) > 1 else "unique-short-name")
        rec["storage"] = ("shared-source" if uses.get(raw_keys.get(rec.get("source_sha256")), 0) > 1
                          else "original-module")
        rec["binding"] = "legacy-registry" if rec["kind"] == "registry" else "original-function"
    ast_groups = defaultdict(list)
    for q, rec in registry.items():
        if rec.get("definition_name") == rec["name"]:
            ast_groups[rec["ast_sha256"]].append(q)
    groups = []
    for ast_id, names in sorted(ast_groups.items()):
        if len(names) < 2:
            continue
        raw_ids = {registry[q]["source_sha256"] for q in names}
        canonical_ids = {raw_keys[key] for key in raw_ids}
        match = "same-ast" if len(canonical_ids) > 1 else (
            "identical-bytes" if len(raw_ids) == 1 else "line-endings-only")
        groups.append({"match": match, "functions": sorted(names), "ast_sha256": ast_id})
    input_state = sorted((f["path"], f["sha256"]) for f in files)
    plan_id = digest(json_text([VERSION, input_state]).encode())
    stored = sum(map(len, blocks.values()))
    exact_saved = source_bytes - sum(raw_sizes.values())
    report = {"plan_sha256": plan_id, "scanned_files": len(files), "qualified_actions": len(registry),
              "raw_source_bytes": source_bytes, "unique_block_bytes": stored,
              "shared_block_references": sum(uses.values()) - len(blocks),
              "exact_duplicate_bytes_saved": exact_saved,
              "line_ending_bytes_saved": source_bytes - stored - exact_saved,
              "source_bytes_saved": source_bytes - stored,
              "same_ast_groups": groups,
              "name_conflicts": {n: sorted(q) for n, q in variants.items() if len(q) > 1}}
    return blocks, files, registry, dict(variants), report


def plan(source: Path, workers: int, accelerator: str | None, strict: bool = False) -> dict:
    """與 build 共用掃描和去重規則。輸出 JSON 至 stdout，不建立快照或產物。"""
    root = source.resolve(strict=True)
    scan = functools.partial(scan_file, root=root, snapshot=None)
    results, backend = parallel_scan(candidates(root), scan, accelerator, workers)
    *_, report = index_sources(results, strict)
    return {"status": "PREVIEW", "backend": backend, **report}


def assemble(scans: list[dict], backend: str, strict: bool,
             expected_plan: str | None = None) -> tuple[str, dict, str]:
    raw_blocks, files, registry, variants, report = index_sources(scans, strict)
    if expected_plan is not None and expected_plan != report["plan_sha256"]:
        raise ValueError("來源與預覽指紋不一致。請重新執行 plan。")
    blocks = {k: base64.b85encode(v).decode("ascii") for k, v in raw_blocks.items()}
    payload = {"files": files, "blocks": blocks, "registry": registry, "variants": variants}
    encoded = base64.b85encode(zlib.compress(json_text(payload).encode(), level=9))
    bundle = MAGIC + "\n" + RUNTIME.replace("__PACKED__", repr(encoded))
    compile(bundle, "fnc_lib.py", "exec", dont_inherit=True)
    audit = {"deduplication": report, "version": VERSION, "backend": backend, "files": files, "actions": registry,
             "variants": dict(variants), "unique_source_blocks": len(blocks),
             "shared_block_references": sum(len(f["parts"]) for f in files) - len(blocks),
             "checks": ["source-byte-roundtrip", "compile", "qualified-registry-count"],
             "scope": "top-level public functions and literal FNC_LIB_REGISTRY keys"}
    if validator := optional("jsonschema"):
        validator.validate(audit, AUDIT_SCHEMA)
    prompt = ("呼叫 trigger_unified_engine(action_code, *args, **kwargs)。"
              "唯一行動名可簡寫，同名行動請選 module::action。多步驟可用 batch steps.json，pipe=true 串接前一步結果。\n")
    for name, group in variants.items():
        prompt += (name if len(group) == 1 else " | ".join(group)) + "\n"
    return bundle, audit, prompt


def export_extras(folder: Path, audit: dict) -> dict:
    """可選交換格式；每一項分開記錄是否產出。"""
    raw = json_text(audit).encode()
    output = {}
    for mod, ext in (("msgpack", "msgpack"), ("zstandard", "json.zst"), ("yaml", "yaml"),
                     ("xlsxwriter", "xlsx"), ("pygments", "html")):
        lib = optional(mod)
        if lib is None:
            output[ext] = "missing"
            continue
        path = folder / ("registry." + ext)
        if mod == "msgpack":
            path.write_bytes(lib.packb(audit, use_bin_type=True))
        elif mod == "zstandard":
            path.write_bytes(lib.ZstdCompressor().compress(raw))
        elif mod == "yaml":
            path.write_text(lib.safe_dump(audit["variants"], allow_unicode=True), encoding="utf-8")
        elif mod == "xlsxwriter":
            with lib.Workbook(str(path), {"strings_to_formulas": False, "strings_to_urls": False}) as book:
                sheet = book.add_worksheet("FNC-LIB")
                sheet.write_row(0, 0, ["Action", "Source", "Line", "Parameters", "Kind", "Issues"])
                for row, (q, rec) in enumerate(audit["actions"].items(), 1):
                    sheet.write_row(row, 0, [q, rec["path"], rec.get("line"), rec.get("signature"),
                                             rec["kind"], ", ".join(rec.get("issues", []))])
                sheet.freeze_panes(1, 1)
                sheet.autofilter(0, 0, row, 5)
                sheet.set_column(0, 1, 36)
                sheet.set_column(3, 3, 56)
        else:
            from pygments.formatters import HtmlFormatter
            from pygments.lexers import JsonLexer
            path.write_text(lib.highlight(json_text(audit["actions"]), JsonLexer(),
                                          HtmlFormatter(full=True, title="VIA ModuFuse · FNC-LIB")),
                            encoding="utf-8")
        output[ext] = path.name
    return output


def build(source: Path, temp: Path, workers: int, accelerator: str | None,
          strict: bool = False, extras: bool = False, expected_plan: str | None = None) -> dict:
    root, temp = source.resolve(strict=True), temp.resolve()
    if temp.is_relative_to(root):
        raise ValueError("TEMP 必須在來源樹以外，以免掃入輸出檔")
    paths = candidates(root)
    temp.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(prefix=".staging-", dir=temp) as private:
        stage = Path(private)
        scan = functools.partial(scan_file, root=root, snapshot=stage / "snapshots")
        results, backend = parallel_scan(paths, scan, accelerator, workers)
        bundle, audit, prompt = assemble(results, backend, strict, expected_plan)
        artifact = stage / "fnc_lib.py"
        artifact.write_bytes(bundle.encode("utf-8"))
        check = subprocess.run([sys.executable, "-I", "-X", "utf8", str(artifact), "verify"],
                               capture_output=True, check=True, encoding="utf-8",
                               env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        counts = json.loads(check.stdout)
        if counts != {"verified_files": len(paths),
                      "qualified_actions": sum(len(r["actions"]) for r in results)}:
            raise ValueError("執行時註冊筆數與掃描不同")
        audit["bundle_sha256"] = digest(artifact.read_bytes())
        audit["exports"] = export_extras(stage, audit) if extras else {}
        (stage / "panorama.manifest.json").write_text(json_text(audit), encoding="utf-8")
        (stage / "DISPATCH_PROMPT_MINIFIED.md").write_text(prompt, encoding="utf-8")
        import uuid
        dest = temp / ("run-" + uuid.uuid4().hex)
        os.replace(stage, dest)
    return {"status": "VERIFIED_STATIC", "plan_sha256": audit["deduplication"]["plan_sha256"],
            "source_bytes_saved": audit["deduplication"]["source_bytes_saved"], **counts, "backend": backend,
            "shared_block_references": audit["shared_block_references"], "output": str(dest),
            "bundle": str(dest / artifact.name), "sha256": audit["bundle_sha256"]}


# 04 · 單檔發布、備份與回復；只接受本版本產生的 FNC-LIB
def checked_bundle(path: Path) -> bytes:
    data = path.read_bytes()
    source = data.decode("utf-8")
    if source.startswith(LEGACY_MAGIC + "\n"):
        before, sep, tail = source.partition("_DATA = json.loads(zlib.decompress(base64.b85decode(")
        literal, closing, after = tail.partition(")))\n")
        template = before + sep + "__PACKED__" + closing + after
        if not sep or not closing or digest(template.encode()) != LEGACY_TEMPLATE_SHA256:
            raise ValueError("v0100 執行模板驗證失敗")
    else:
        prefix, suffix = (MAGIC + "\n" + RUNTIME).split("__PACKED__")
        if not source.startswith(prefix) or not source.endswith(suffix):
            raise ValueError(f"無法驗證此 FNC-LIB 產物：{path}")
        literal = source[len(prefix):-len(suffix)]
    packed = ast.literal_eval(literal)
    if not isinstance(packed, bytes) or repr(packed) != literal:
        raise ValueError("嵌入格式錯誤")
    payload = json.loads(zlib.decompress(base64.b85decode(packed)))
    for f in payload["files"]:
        rel = Path(f["path"])
        if rel.is_absolute() or rel.drive or ".." in rel.parts or "\\" in f["path"] or ":" in f["path"]:
            raise ValueError("內嵌模組路徑無效")
        if module_id(rel) != f["module"]:
            raise ValueError("內嵌模組名稱不一致")
    # 僅執行上方固定模板的 verify，完全不匯入來源模組。
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "fnc_lib.py"
        copy.write_bytes(data)
        subprocess.run([sys.executable, "-I", "-X", "utf8", str(copy), "verify"], capture_output=True, check=True)
    return data


def durable_replace(dest: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as staged:
        tmp = Path(staged.name)
        try:
            staged.write(data)
            staged.flush()
            os.fsync(staged.fileno())
        except BaseException:
            staged.close()
            tmp.unlink(missing_ok=True)
            raise
    try:
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)


@contextlib.contextmanager
def release_lock(path: Path):
    """鎖由作業系統持有，行程終止時自動釋放。保留鎖檔以免其他行程鎖到不同 inode。"""
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def publish(source: Path, dest: Path, rollback: bool = False) -> dict:
    if dest.is_symlink() or dest.suffix.lower() != ".py":
        raise ValueError("目的地須為一般 .py 檔")
    dest = dest.resolve()
    data = checked_bundle(source)
    if rollback:
        expected = dest.with_name(dest.name + "." + digest(data) + ".bak")
        if source.resolve() != expected or not dest.exists():
            raise ValueError("回復須指定該目的檔的原始指紋備份")
    dest.parent.mkdir(parents=True, exist_ok=True)
    lock = dest.with_suffix(dest.suffix + ".lock")
    backup = None
    with release_lock(lock):
        if dest.exists():
            old = checked_bundle(dest)
            if old == data:
                return {"status": "UNCHANGED", "file": str(dest)}
            backup = dest.with_name(dest.name + "." + digest(old) + ".bak")
            if backup.exists() and backup.read_bytes() != old:
                raise ValueError("備份指紋衝突")
            if not backup.exists():
                durable_replace(backup, old)
        durable_replace(dest, data)
    return {"status": "ROLLED_BACK" if rollback else "PUBLISHED", "file": str(dest),
            "backup": str(backup) if backup else None, "sha256": digest(data)}


def doctor(accel: str | None) -> dict:
    libs = {}
    for dist, (mod, purpose) in LIBS.items():
        try:
            version = importlib.metadata.version(dist)
            loaded = optional(mod) is not None
            if dist in MIN_VERSIONS and optional("packaging"):
                from packaging.version import Version
                loaded = loaded and Version(version) >= Version(MIN_VERSIONS[dist])
            libs[dist] = {"version": version, "status": "ok" if loaded else "incompatible",
                          "use": purpose}
        except Exception as exc:
            libs[dist] = {"status": "unavailable", "use": purpose, "reason": str(exc)}
    path = accelerator_path(accel)
    return {"version": VERSION, "python": sys.version.split()[0],
            "available": sum(x["status"] == "ok" for x in libs.values()),
            "accelerator": str(path) if path else None, "libraries": libs}


# 05 · 固定來源的 MCP stdio 工具。請以啟動參數設定來源與加速器。
def serve(options: argparse.Namespace) -> None:
    import anyio
    from mcp.server.fastmcp import FastMCP
    from pydantic import BaseModel, ConfigDict, Field
    class MergeRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        workers: int = Field(default=MAX_WORKERS, ge=1, le=MAX_WORKERS)
        strict: bool = False
        extras: bool = False
        preview_only: bool = False
        expected_plan: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    server = FastMCP("VIA-ModuFuse")
    build_lock = anyio.Lock()
    async def trigger_vcgc_ast_merge(request):
        """建置固定來源的單檔 FNC-LIB。回傳文件位置、指紋與指令數。"""
        if request.preview_only:
            task = functools.partial(plan, options.source, request.workers, options.accelerator, request.strict)
        else:
            task = functools.partial(build, options.source, options.temp, request.workers,
                                     options.accelerator, request.strict, request.extras, request.expected_plan)
        async with build_lock:
            return await anyio.to_thread.run_sync(task)
    trigger_vcgc_ast_merge.__annotations__ = {"request": MergeRequest, "return": dict}
    server.tool()(trigger_vcgc_ast_merge)
    server.run(transport="stdio")


def selftest(accel: str | None) -> dict:
    """以真實的 CLI 子行程驗證受控測資。"""
    completed = []
    def expect(name: str, condition: bool) -> None:
        if not condition:
            raise AssertionError(name)
        completed.append(name)
    def run(bundle: Path, *args: str, ok: bool = True) -> Any:
        result = subprocess.run([sys.executable, "-I", "-X", "utf8", str(bundle), *args],
                                capture_output=True, text=True, encoding="utf-8")
        if (result.returncode == 0) != ok:
            raise AssertionError(f"{args}: {result.stderr}")
        return json.loads(result.stdout) if ok else result.stderr
    with tempfile.TemporaryDirectory(prefix="via_quanjiao_test_") as private:
        base = Path(private)
        src, work = base / "inputs", base / "work"
        pkg = src / "engines"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_bytes(b"")
        common = "def score(x: int, /, *, n: int = 1) -> int:\n    return x * n + OFFSET\n"
        (pkg / "one.py").write_text("OFFSET = 2\n" + common +
            "FNC_LIB_REGISTRY = {'OLD_SCORE': score}\n", encoding="utf-8")
        (pkg / "two.py").write_text("OFFSET = 7\n" + common, encoding="utf-8")
        (pkg / "alt.py").write_text(
            "from .one import score as _score\n"
            "def score(x, bonus=10):\n    return _score(x) + bonus\n"
            "async def hello(name: str) -> str:\n    return name\n", encoding="utf-8")
        (src / "lazy.py").write_text("raise RuntimeError('should only run on use')\n"
                                     "def latent(): return 1\n", encoding="utf-8")
        # 在沙盒內模擬一份 Windows CRLF 來源與一份 LF 來源。
        win_file = pkg / "two.py"
        win_file.write_bytes(("OFFSET = 7\n" + common).replace("\n", "\r\n").encode())
        left = pkg / "one.py"
        left.write_bytes(left.read_bytes().replace(b"\r\n", b"\n"))
        preview = plan(src, 2, accel)
        expect("preview creates no staging artifacts", not work.exists())
        groups = preview["same_ast_groups"]
        expect("line ending matches exclude registry aliases",
               any(g["match"] == "line-endings-only" and g["functions"] ==
                   ["engines.one::score", "engines.two::score"] for g in groups))
        expect("conflicting implementations named individually",
               len(preview["name_conflicts"]["score"]) == 3)
        expect("preview accounts for source bytes", preview["raw_source_bytes"] ==
               sum(p.stat().st_size for p in src.rglob("*.py")) and
               preview["source_bytes_saved"] == preview["raw_source_bytes"] - preview["unique_block_bytes"]
               and preview["line_ending_bytes_saved"] >= len(common.encode()))
        probe = base / "probe"
        probe.mkdir()
        (probe / "first.py").write_bytes(common.encode())
        (probe / "second.py").write_bytes(common.encode())
        (probe / "third.py").write_bytes(common.replace("return x * n", "return x*n").encode())
        probe_plan = plan(probe, 1, accel)
        expect("format-only candidates preserve independent source",
               probe_plan["same_ast_groups"][0]["match"] == "same-ast" and
               probe_plan["exact_duplicate_bytes_saved"] == len(common.encode()))
        (probe / "third.py").unlink()
        expect("exact duplicates identified", plan(probe, 1, accel)["same_ast_groups"][0]["match"]
               == "identical-bytes")
        first = build(src, work, 2, accel, expected_plan=preview["plan_sha256"])
        expect("approved preview matches build", first["plan_sha256"] == preview["plan_sha256"] and
               first["source_bytes_saved"] == preview["source_bytes_saved"])
        bundle = Path(first["bundle"])
        expect("byte-for-byte snapshots", all(p.read_bytes() == (bundle.parent / "snapshots" /
               p.relative_to(src)).read_bytes() for p in src.rglob("*.py")))
        expect("registry conservation", run(bundle, "verify") == {"verified_files": 5, "qualified_actions": 6})
        expect("shared source storage", first["shared_block_references"] > 0)
        expect("legacy action and positional-only", run(bundle, "run", "OLD_SCORE", "--args", "[3]") == 5)
        expect("same AST, independent globals", run(bundle, "run", "score", "--variant", "engines.two",
               "--args", "[3]", "--kwargs", '{"n":2}') == 13)
        expect("variant signature and relative import", run(bundle, "run", "engines.alt::score",
               "--args", "[3]", "--kwargs", '{"bonus":4}') == 9)
        expect("await async action", run(bundle, "run", "hello", "--args", '["VIA"]') == "VIA")
        expect("ambiguous action", "engines.one::score" in run(bundle, "run", "score", ok=False))
        expect("unknown action", "KeyError" in run(bundle, "run", "unknown", ok=False))
        steps = base / "steps.json"
        steps.write_text(json_text([{"action": "OLD_SCORE", "args": [3]},
                                    {"action": "score", "variant": "engines.two", "pipe": True}]),
                         encoding="utf-8")
        expect("batch result chaining", run(bundle, "batch", str(steps)) == [5, 12])
        dest = base / "release" / "tools.py"
        publish(bundle, dest)
        expect("idempotent publish", publish(bundle, dest)["status"] == "UNCHANGED")
        (pkg / "two.py").write_text("OFFSET = 9\n" + common, encoding="utf-8")
        try:
            build(src, work, 1, accel, expected_plan=preview["plan_sha256"])
        except ValueError as exc:
            expect("stale preview refused without publishing", "指紋" in str(exc)
                   and len(list(work.iterdir())) == 1)
        else:
            raise AssertionError("stale preview gate")
        second = Path(build(src, work, 1, accel)["bundle"])
        receipt = publish(second, dest)
        expect("atomic replacement", run(dest, "run", "engines.two::score", "--args", "[0]") == 9)
        publish(Path(receipt["backup"]), dest, rollback=True)
        expect("rollback", dest.read_bytes() == bundle.read_bytes())
        try:
            build(src, work, 1, accel, strict=True)
        except ValueError as exc:
            expect("strict guard", "strict" in str(exc))
        else:
            raise AssertionError("strict guard")
        (pkg / "bad.py").write_text("def broken(:", encoding="utf-8")
        try:
            build(src, work, 1, accel)
        except ValueError as exc:
            expect("invalid source stops build", "bad.py" in str(exc))
        else:
            raise AssertionError("syntax gate")
        expect("failed builds publish nothing", len(list(work.iterdir())) == 2)
        shutil.rmtree(src)
        expect("run independent of originals", run(dest, "run", "OLD_SCORE", "--args", "[1]") == 3)
    return {"status": "PASS", "count": len(completed), "checks": completed, "backend": first["backend"]}


def main() -> int:
    if sys.version_info < MIN_PYTHON:
        raise SystemExit("需要 Python 3.11 以上")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "plan", "serve", "doctor", "selftest"):
        p = sub.add_parser(name)
        p.add_argument("--accelerator", help=f"信任的 VeritasCeleritas.py；亦可設定 {ACCEL_ENV}")
        if name in ("plan", "build", "serve"):
            p.add_argument("source", type=Path, help="Python 模組匯入根目錄")
        if name in ("build", "serve"):
            p.add_argument("--temp", type=Path, default=DEFAULT_TEMP)
        if name in ("plan", "build"):
            p.add_argument("--workers", type=int, default=MAX_WORKERS)
            p.add_argument("--strict", action="store_true", help="遇到型別、docstring、print 或可變預設值即停止")
        if name == "build":
            p.add_argument("--expect-plan", help="只接受這次 plan 回傳的 plan_sha256")
            p.add_argument("--extras", action="store_true", help="另輸出五種本機交換格式")
    for name in ("publish", "rollback"):
        p = sub.add_parser(name)
        if name == "publish":
            p.add_argument("bundle", type=Path)
        p.add_argument("destination", type=Path)
        if name == "rollback":
            p.add_argument("backup", type=Path)
    options = parser.parse_args()
    try:
        if options.command == "serve":
            serve(options)
            return 0
        if options.command == "build":
            answer = build(options.source, options.temp, options.workers, options.accelerator,
                           options.strict, options.extras, options.expect_plan)
        elif options.command == "plan":
            answer = plan(options.source, options.workers, options.accelerator, options.strict)
        elif options.command == "doctor":
            answer = doctor(options.accelerator)
        elif options.command == "selftest":
            answer = selftest(options.accelerator)
        elif options.command == "publish":
            answer = publish(options.bundle, options.destination)
        else:
            answer = publish(options.backup, options.destination, rollback=True)
        emit(answer)
        return 0
    except Exception as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
