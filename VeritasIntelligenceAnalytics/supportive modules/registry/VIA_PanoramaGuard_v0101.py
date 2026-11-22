#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA PanoramaGuard · Python 3.11+ · 全景 AST 掃描、隔離修復與唯讀 MCP。

scan 分析 manifest 指定的 Python 檔，缺 manifest 時遞迴盤點。
repair 在獨立輸出目錄建立修復覆層（僅含異動檔），保留原始工作樹。
serve 從指定收據目錄提供 summary / findings / handoff，適用本機 stdio 或 VCGC gateway。
selftest 使用暫存資料驗證。退出碼 0=完成、1=仍有紅燈、2=阻擋或執行失敗。
--suite 可重複指定 unittest 目錄，每組在獨立子行程執行。scan 只跑基線，repair 比對前後兩次。
repair --commit 在輸出目錄建立獨立 Git clone，通過專案測試與棘輪後才提交。
template manifest / ledger / powershell 將範本輸出至 stdout，ledger 僅供欄位示意。
manifest 的 api_contracts 以檔案相對路徑為鍵，接受 required_imports 字串陣列、
keyword_parameters（函式名 → 必須接受的關鍵字清單）及 column_lists（常數名 → 有序欄名）。
未提供子系統契約時，匯入方向與檔名前綴覆蓋率列為未設定。
新一輪有意調整 manifest 時，請選新的 --output 建立基線並保留舊帳。
修復草稿保留黃燈。--narrow-except 改變對 KeyboardInterrupt 等 BaseException 的處理。
"""
from __future__ import annotations
import argparse
import ast
import collections
import contextlib
import copy
import fnmatch
import functools
import hashlib
import html
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tokenize
import unittest
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

# [AST-ANCHOR: CONFIG]
VERSION = "0.1.1"
MANIFEST = "panorama.manifest.json"
LOCK = Path("supportive modules/registry/VIA_ToolVersion_Lock_v0100.json")
CEL_SHA = "ddcb5460bf64b0d8d773a8878cca1b4e642eac977f2d7aa2b0e267745d1ecea5"
WORKERS = min(4, os.cpu_count() or 1)
MAX_BYTES = 8 * 1024 * 1024
MAX_ROUNDS = 3
TEST_TIMEOUT = 300
FIX_RETRY = 4
HANDOFF_BYTES = 480
PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
RETRIES_BASE_SECONDS = 0.05
PROCESS_THRESHOLD = 64
RULES = dict(enforce_public_docstring=True, forbid_bare_except=True, forbid_global_mutation=True,
             enforce_ast_anchors=True, min_ast_anchors=1, enforce_subsystem_prefix=True,
             enforce_import_direction=True, forbid_nonlocal_mutation=True, max_nesting_depth=4)
ANCHOR = re.compile(r"#\s*\[AST-ANCHOR:\s*([A-Z0-9_]+)\s*\]$")
SECRET = re.compile(r"(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|private[_-]?key)$", re.I)
DOC_PREFIX = "TODO: describe "
FUN = (ast.FunctionDef, ast.AsyncFunctionDef)
LEVELS = ("GREEN", "YELLOW", "RED")
PROTECTED = {"references", "archive", "intake", "registry"}
DEFAULT_OUTPUT = Path(tempfile.gettempdir()) / "VIA_PanoramaGuard"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_link(path):
    st = path.lstat()
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def within(root, name):
    p = Path(name)
    if not name or p.is_absolute() or PureWindowsPath(name).drive or PureWindowsPath(name).root or ".." in p.parts or "\\" in name or ":" in name:
        raise ValueError(f"非法相對路徑 {name!r}")
    cur = root
    for part in p.parts:
        cur = cur / part
        if cur.exists() or cur.is_symlink():
            if is_link(cur):
                raise ValueError(f"連結或重新解析點 {name!r}")
    if not cur.resolve().is_relative_to(root):
        raise ValueError("路徑超出範圍")
    return cur


def read_limited(path):
    if not path.is_file():
        raise ValueError(f"缺少一般檔案 {path.name}")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("FILE_SIZE_LIMIT")
    return data


def checked_manifest(root):
    mf = within(root, MANIFEST)
    conf = json.loads(read_limited(mf).decode("utf-8-sig")) if mf.exists() else {}
    if not isinstance(conf, dict):
        raise ValueError("manifest 必須是 JSON 物件")
    for key in ("include_files", "exclude_patterns","test_suites"):
        if key in conf and (not isinstance(conf[key], list) or not all(isinstance(x,str) for x in conf[key])):
            raise ValueError(f"manifest {key} 必須是字串清單")
    for key in ("ssot_policy", "static_guard_rules", "subsystems"):
        if not isinstance(conf.get(key, {}), dict):
            raise ValueError(f"manifest {key} 必須是物件")
    for key, val in conf.get("static_guard_rules", {}).items():
        if key in RULES and (type(val) is not type(RULES[key]) or type(val) is int and val < 0):
            raise ValueError(f"無效守衛參數 {key}")
    policy = conf.get("ssot_policy",{})
    if policy.get("require_compile_sandbox",True) is not True or policy.get("allow_direct_text_replace",False) is not False:
        raise ValueError("manifest 與 AST 編譯或修改契約衝突")
    for key, spec in conf.get("subsystems", {}).items():
        if not isinstance(spec, dict) or not isinstance(spec.get("prefix", key+"_"), str) or not spec.get("prefix", key+"_"):
            raise ValueError("無效子系統前綴")
        if "allowed_imports" in spec and (not isinstance(spec["allowed_imports"], list) or
                                         not all(isinstance(x,str) for x in spec["allowed_imports"])):
            raise ValueError("allowed_imports 必須是字串清單")
    contracts = conf.get("api_contracts",{})
    if not isinstance(contracts,dict):
        raise ValueError("api_contracts 必須是物件")
    def strings(seq):
        return isinstance(seq,list) and all(isinstance(v,str) for v in seq)
    for rel,spec in contracts.items():
        if not within(root,rel).is_file() or not isinstance(spec,dict) or not strings(spec.get("required_imports",[])):
            raise ValueError("API 契約路徑或匯入清單錯誤")
        for field in ("keyword_parameters","column_lists"):
            mapping = spec.get(field,{})
            if not isinstance(mapping,dict) or not all(strings(v) for v in mapping.values()):
                raise ValueError("API 契約欄位格式錯誤 "+field)
    return conf


def inventory(root, conf):
    patterns = conf.get("exclude_patterns", [])
    def excluded(rel):
        return bool(SKIP.intersection(part.lower() for part in Path(rel).parts)) or any(
            fnmatch.fnmatchcase(rel, pat) or pat.endswith("/**") and fnmatch.fnmatchcase(rel, pat[:-3])
            for pat in patterns)
    if "include_files" in conf:
        hits = []
        for name in conf["include_files"]:
            path = within(root, name)
            if not excluded(name):
                if path.suffix.lower() != ".py" or not path.is_file():
                    raise ValueError(f"manifest 缺檔或格式錯誤 {name}")
                hits.append(path.relative_to(root).as_posix())
        return sorted(set(hits))
    hits = []
    def fail(err):
        raise err
    for folder, dirs, files in os.walk(root, onerror=fail, followlinks=False):
        base = Path(folder)
        dirs[:] = sorted(d for d in dirs if not is_link(base/d) and not excluded((base/d).relative_to(root).as_posix()))
        for name in files:
            p = base / name
            if p.suffix.lower() == ".py" and not is_link(p) and p.is_file():
                rel = p.relative_to(root).as_posix()
                if not excluded(rel):
                    hits.append(rel)
    return sorted(hits)


# [VIA:ACCEL-BRIDGE:v0100]
def accelerator(root, required):
    """只載入鎖冊驗指紋後的 parallel_map AST，不啟動同目錄其他模組。"""
    for via in (root / "VeritasIntelligenceAnalytics", root):
        if not (via / LOCK).exists():
            continue
        lock = within(root, (via / LOCK).relative_to(root).as_posix())
        entry = read_json(lock)["accelerator"]
        rel = Path(entry["path"]).relative_to("VeritasIntelligenceAnalytics").as_posix()
        source = read_limited(within(root, (via / rel).relative_to(root).as_posix()))
        if digest(source) != CEL_SHA and b"\r\n" in source:
            canonical = source.replace(b"\r\n",b"\n")
            if digest(canonical) == CEL_SHA:
                source = canonical
        if digest(source) != entry["sha256"] or digest(source) != CEL_SHA or entry["version"] != "v1141":
            raise ValueError("加速器版本或 SHA-256 與已審核版本不一致，請核對鎖冊")
        node, = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "parallel_map"]
        # Pinned implementation's thread branch only. An explicit worker count prevents global pool discovery.
        space = dict(ProcessPoolExecutor=ProcessPoolExecutor, ThreadPoolExecutor=ThreadPoolExecutor, as_completed=as_completed)
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<verified Celeritas.parallel_map>", "exec"), space)
        return space["parallel_map"], {"backend":"Celeritas.parallel_map", "version":entry["version"], "sha256":CEL_SHA}
    if required:
        raise ValueError("找不到 Celeritas 鎖冊")
    def local_map(fn, items, max_workers, mode):
        executor = ProcessPoolExecutor if mode == "process" else ThreadPoolExecutor
        with executor(max_workers=max_workers) as pool:
            return list(pool.map(fn, items))
    return local_map, {"backend":"stdlib.concurrent.futures","reason":"未找到專案鎖冊"}
# [VIA:ACCEL-BRIDGE:END]


def decode(raw):
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    text = raw.decode(encoding)
    if text.encode(encoding) != raw:
        raise ValueError("編碼無法無損往返")
    return text, encoding


def issue(level, code, rule, line, symbol=""):
    return dict(level=level, op=code, rule=rule, line=line, symbol=symbol)


def visit_source(tree, source, rel, conf):
    """檢查公開函式、靜態依賴、流程深度及少數可定位的敏感語法。"""
    rules = RULES | conf.get("static_guard_rules", {})
    subs = conf.get("subsystems", {})
    def subsystem(name):
        return next((s for s, v in sorted(subs.items(),key=lambda kv: -len(kv[1].get("prefix",kv[0]+"_"))) if name == s or name.startswith(v.get("prefix", s+"_"))), None)
    owner = subsystem(Path(rel).stem)
    findings, anchors, imports = [], {}, set()
    def add(level, op, rule, line, symbol=""):
        findings.append(issue(level, op, rule, line, symbol))
    if rules["enforce_subsystem_prefix"] and subs and not owner and Path(rel).name != "__init__.py":
        add("RED",500,"unregistered_prefix",1)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        match = ANCHOR.fullmatch(tok.string.strip()) if tok.type == tokenize.COMMENT else None
        if tok.type == tokenize.COMMENT and tok.string.lstrip().startswith("# [AST-ANCHOR:") and not match and rules["enforce_ast_anchors"]:
            add("YELLOW",300,"malformed_anchor",tok.start[0])
        if match:
            tag = match[1]
            if tag in anchors and rules["enforce_ast_anchors"]:
                add("RED",400,"duplicate_anchor",tok.start[0],tag)
            anchors[tag] = tok.start[0]
    if rules["enforce_ast_anchors"] and len(anchors) < rules["min_ast_anchors"] and Path(rel).name != "__init__.py":
        add("YELLOW",300,"missing_anchor",1)
    def inspect_import(name, n):
        imports.add(name)
        allowed = subs.get(owner, {}).get("allowed_imports")
        if rules["enforce_import_direction"] and allowed is not None:
            for target in {subsystem(part) for part in name.split(".")} - {None}:
                if target not in allowed:
                    add("RED",500,"forbidden_import",n.lineno,target)
    class PanoramaDiagnosticVisitor(ast.NodeVisitor):
        depth = 0
        def visit(self, n):
            branch = isinstance(n, (ast.For, ast.AsyncFor, ast.If, ast.While, ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.Match))
            self.depth += branch
            if branch and self.depth > rules["max_nesting_depth"]:
                add("RED",500,"deep_nesting",n.lineno)
            super().visit(n)
            self.depth -= branch
        def visit_FunctionDef(self, n):
            if rules["enforce_public_docstring"] and not n.name.startswith("_"):
                doc = ast.get_docstring(n)
                if doc is None or doc.startswith(DOC_PREFIX):
                    add("YELLOW",300,"missing_doc" if doc is None else "draft_doc",n.lineno,n.name)
            old, self.depth = self.depth, 0
            self.generic_visit(n)
            self.depth = old
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_Import(self, n):
            for a in n.names:
                inspect_import(a.name,n)
        def visit_ImportFrom(self, n):
            parents = list(Path(rel).parent.parts)
            package = ".".join(parents[:len(parents)-n.level+1]) if n.level and n.level <= len(parents) else ""
            for a in n.names:
                inspect_import(".".join(filter(None,(package,n.module,a.name))),n)
        def visit_Call(self, n):
            name = ast.unparse(n.func) if isinstance(n.func,(ast.Name,ast.Attribute)) else ""
            if name in {"__import__","importlib.import_module"} and n.args:
                val = n.args[0]
                if isinstance(val,ast.Constant) and isinstance(val.value,str):
                    inspect_import(val.value,n)
                else:
                    add("YELLOW",500,"dynamic_import",n.lineno)
            if name in {"eval","exec"}:
                add("YELLOW",500,"dynamic_execution_review",n.lineno)
            self.generic_visit(n)
        def visit_ExceptHandler(self,n):
            if n.type is None and rules["forbid_bare_except"]:
                add("RED",400,"bare_except",n.lineno)
            self.generic_visit(n)
        def visit_Global(self,n):
            if rules["forbid_global_mutation"]:
                add("RED",500,"global_declaration",n.lineno)
        def visit_Nonlocal(self,n):
            if rules["forbid_nonlocal_mutation"]:
                add("RED",500,"nonlocal_declaration",n.lineno)
        def visit_Assign(self,n):
            if isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and len(n.value.value)>=8:
                if any(isinstance(t,ast.Name) and SECRET.search(t.id) for t in n.targets):
                    add("RED",500,"possible_literal_secret",n.lineno)
            self.generic_visit(n)
    PanoramaDiagnosticVisitor().visit(tree)
    return findings, anchors, sorted(imports), owner


def structural_hash(tree, skeleton=False, disposable=False):
    if skeleton:
        if not disposable:
            tree = copy.deepcopy(tree)
        for n in ast.walk(tree):
            if isinstance(n, FUN+(ast.ClassDef,)):
                n.name = "_"
            elif isinstance(n, ast.Name):
                n.id = "_"
            elif isinstance(n, ast.arg):
                n.arg = "_"
            elif isinstance(n, ast.Constant):
                n.value = type(n.value).__name__
    return digest(ast.dump(tree).encode())


def audit_contract(tree, rel, conf, imports):
    """檢查 manifest.api_contracts 明列的公開函式、必要匯入及欄位宣告。"""
    contract = conf.get("api_contracts",{}).get(rel,{})
    functions = {n.name:n for n in tree.body if isinstance(n,FUN)}
    results = []
    for name,keywords in contract.get("keyword_parameters",{}).items():
        if name not in functions:
            results.append(issue("RED",500,"missing_public_function",1,name))
            continue
        func = functions[name]
        actual = {a.arg for a in func.args.args + func.args.kwonlyargs}
        for keyword in sorted(set(keywords)-actual):
            level = "YELLOW" if func.args.kwarg else "RED"
            results.append(issue(level,500,"keyword_contract",func.lineno,name+"."+keyword))
    for name in contract.get("required_imports",[]):
        if not any(imp==name or imp.startswith(name+".") for imp in imports):
            results.append(issue("RED",500,"missing_import_bridge",1,name))
    assignments = {}
    for stmt in tree.body:
        if isinstance(stmt,ast.Assign):
            assignments.update({t.id:stmt.value for t in stmt.targets if isinstance(t,ast.Name)})
        elif isinstance(stmt,ast.AnnAssign) and isinstance(stmt.target,ast.Name):
            assignments[stmt.target.id] = stmt.value
    for name,cols in contract.get("column_lists",{}).items():
        val = assignments.get(name)
        if not isinstance(val,(ast.Tuple,ast.List)) or not all(isinstance(c,ast.Constant) and isinstance(c.value,str) for c in val.elts):
            results.append(issue("YELLOW",500,"column_contract_unverified",getattr(val,"lineno",1),name))
        elif [c.value for c in val.elts] != cols:
            results.append(issue("RED",500,"column_order_or_name_mismatch",val.lineno,name))
    return results


def inspect_bytes(raw, rel, conf):
    row = dict(sha256=digest(raw), issues=[], anchors={}, imports=[], subsystem=None)
    try:
        src, _ = decode(raw)
        tree = ast.parse(src, rel, type_comments=True)
        compile(raw, rel, "exec", dont_inherit=True)
        row["issues"], row["anchors"], row["imports"], row["subsystem"] = visit_source(tree,src,rel,conf)
        row["issues"].extend(audit_contract(tree,rel,conf,row["imports"]))
        row.update(exact=structural_hash(tree), skeleton=structural_hash(tree,True,disposable=True))
    except (SyntaxError, UnicodeError, LookupError, ValueError, RecursionError, tokenize.TokenError) as err:
        row["issues"] = [issue("RED",500,type(err).__name__,getattr(err,"lineno",None) or 0)]
    row["status"] = max((i["level"] for i in row["issues"]), key=LEVELS.index, default="GREEN")
    return row


def inspect_file(root, conf, rel):
    p = within(root,rel)
    try:
        return inspect_bytes(read_limited(p),rel,conf)
    except (ValueError,OSError) as err:
        return dict(status="RED",issues=[issue("RED",500,"unreadable_or_oversize",0)],sha256=None,
                    anchors={},imports=[],subsystem=None,error=type(err).__name__)


class SpanCollisionError(ValueError):
    """拒絕重疊或相同起點的編輯。"""


def apply_spans(data, edits):
    last_start, last_end = -1, -1
    for start, end, _ in sorted(edits):
        if not (0 <= start <= end <= len(data)) or start < last_end or start == last_start:
            raise SpanCollisionError("SPAN_COLLISION")
        last_start, last_end = start, end
    buf = bytearray(data)
    for start,end,rep in sorted(edits,reverse=True):
        buf[start:end] = rep
    return bytes(buf)


# [AST-ANCHOR: SURGICAL_REPAIR]
def patch_bytes(raw, rel, row, narrow=False, docs=False, minimum=1):
    """以 AST 定位候選節點，以位元組切片保留註解，再檢查完整 AST 等價性。"""
    if "exact" not in row:
        return raw
    rules = {i["rule"] for i in row["issues"]}
    if not rules.intersection({"missing_anchor","missing_doc","bare_except"}):
        return raw
    src, enc = decode(raw)
    tree = ast.parse(src,rel,type_comments=True)
    data = src.encode("utf-8")
    lines = re.findall(rb"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$",data)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1]+len(line))
    nl = next(iter(re.findall(rb"\r\n|\r|\n",data)), b"\n")
    edits = []
    if "missing_anchor" in rules:
        definitions = [n for n in tree.body if isinstance(n,FUN+(ast.ClassDef,))]
        target = next((n for n in definitions if n.name == "main"), next(iter(definitions), None))
        if target:
            # The physical line before the earliest decorator is safe for a comment.
            lineno = min([target.lineno] + [d.lineno for d in target.decorator_list])
            pos = offsets[lineno-1]
        elif tree.body and ast.get_docstring(tree) is None:
            pos = offsets[tree.body[0].lineno-1]
        elif len(tree.body) > 1 and tree.body[0].end_lineno < tree.body[1].lineno:
            pos = offsets[tree.body[1].lineno-1]
        else:
            pos = len(data)
        tag = re.sub(r"[^A-Z0-9_]", "_", (target.name if target else Path(rel).stem).upper()) or "MODULE"
        names = set(row["anchors"])
        additions = []
        index = 0
        while len(names) < minimum:
            index += 1
            name = tag if index == 1 else f"{tag}_{index}"
            if name not in names:
                names.add(name)
                additions.append(f"# [AST-ANCHOR: {name}]".encode() + nl)
        prefix = nl if pos and data[pos-1:pos] not in (b"\r",b"\n") else b""
        if additions:
            edits.append((pos,pos,prefix + b"".join(additions)))

    doc_positions = {}
    if docs and "missing_doc" in rules:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        for idx,tok in enumerate(tokens):
            if tok.type != tokenize.NAME or tok.string != "def":
                continue
            cursor = idx+1
            while cursor < len(tokens) and tokens[cursor].type != tokenize.NEWLINE:
                cursor += 1
            if cursor == len(tokens):
                continue
            header_end = tokens[cursor].start[0]
            cursor += 1
            while cursor < len(tokens) and tokens[cursor].type in (tokenize.NL,tokenize.COMMENT):
                cursor += 1
            if cursor < len(tokens) and tokens[cursor].type == tokenize.INDENT:
                doc_positions[tok.start[0]] = (offsets[header_end],tokens[cursor].string.encode())

    class Candidate(ast.NodeTransformer):
        def visit_ExceptHandler(self,n):
            self.generic_visit(n)
            if narrow and "bare_except" in rules and n.type is None:
                pos = offsets[n.lineno-1] + n.col_offset
                if data[pos:pos+6] != b"except":
                    raise ValueError("EXCEPT_POSITION")
                edits.append((pos+6,pos+6,b" Exception"))
                n.type = ast.copy_location(ast.Name(id="Exception",ctx=ast.Load()), n)
            return n

        def visit_FunctionDef(self,n):
            self.generic_visit(n)
            if not docs or "missing_doc" not in rules or n.name.startswith("_") or ast.get_docstring(n) is not None:
                return n
            first = n.body[0]
            position = doc_positions.get(n.lineno)
            if position is None:
                return n
            pos,indent = position
            args = [a.arg for a in n.args.posonlyargs + n.args.args if a.arg not in ("self","cls")]
            if n.args.vararg:
                args.append("*"+n.args.vararg.arg)
            args.extend(a.arg for a in n.args.kwonlyargs)
            if n.args.kwarg:
                args.append("**"+n.args.kwarg.arg)
            msg = DOC_PREFIX+n.name
            if args:
                msg += ". Args: "+", ".join(args)
            if n.returns is not None:
                msg += ". Returns: TODO"
            edits.append((pos,pos,indent+('"""'+msg+'"""').encode()+nl))
            n.body.insert(0,ast.copy_location(ast.Expr(ast.Constant(msg)),first))
            return n

        visit_AsyncFunctionDef = visit_FunctionDef

    Candidate().visit(tree)
    if not edits:
        return raw
    compile(ast.fix_missing_locations(tree),rel,"exec",dont_inherit=True)
    patched = apply_spans(data,edits).decode().encode(enc)
    got = ast.parse(patched,rel,type_comments=True)
    # TypeIgnore.lineno is an AST field; normalise only these locations before comparing.
    for t in (got,tree):
        for ignored in t.type_ignores:
            ignored.lineno = 0
    if ast.dump(got) != ast.dump(tree):
        raise ValueError("PATCH_AST_MISMATCH")
    compile(patched,rel,"exec",dont_inherit=True)
    return patched


def counts(rows):
    counter = collections.Counter(r["status"] for r in rows.values())
    return {k:counter[k] for k in LEVELS}


def reds(rows):
    return collections.Counter((p,i["rule"],i["symbol"]) for p,r in rows.items()
                               for i in r["issues"] if i["level"] == "RED")


def duplicates(rows, field):
    groups = collections.defaultdict(list)
    for name,row in rows.items():
        if field in row:
            groups[row[field]].append(name)
    return [paths for paths in groups.values() if len(paths)>1]


def atomic_write(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        for attempt in range(FIX_RETRY):
            try:
                os.replace(tmp,path)
                return
            except PermissionError:
                if attempt+1 == FIX_RETRY:
                    raise
                time.sleep(RETRIES_BASE_SECONDS * 2**attempt)
    finally:
        Path(tmp).unlink(missing_ok=True)


@contextlib.contextmanager
def writer_lock(out):
    """OS lock is released by the kernel on exit, including interrupted runs."""
    lock = out / "writer.lock"
    with lock.open("a+b") as f:
        f.seek(0,os.SEEK_END)
        if f.tell()==0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def git_sha(root):
    try:
        p = subprocess.run(["git","-C",str(root),"rev-parse","--verify","HEAD"],capture_output=True,
                           stdin=subprocess.DEVNULL,timeout=5,check=True)
        return p.stdout.decode("ascii").strip()[:16]
    except (OSError,subprocess.SubprocessError):
        return None


def line_shape(raw, line):
    """Return a token outline of one source line, suppressing all literal values."""
    source,_ = decode(raw)
    safe=[]
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.start[0] > line:
            break
        if token.start[0] != line:
            continue
        if token.type in (tokenize.NAME,tokenize.OP):
            safe.append(token.string)
        elif token.type in (tokenize.NUMBER,tokenize.STRING):
            safe.append("…")
    return " ".join(safe)[:64]


def public_handoff(rows, root=None, overlay=None):
    hits = [(p,i) for p,r in rows.items() for i in r["issues"] if i["op"]==500]
    indegree = collections.Counter(part for r in rows.values() for part in
                                   {seg for imp in r["imports"] for seg in imp.split(".")})
    hits.sort(key=lambda x:(-LEVELS.index(x[1]["level"]),-indegree[Path(x[0]).stem],x[0],x[1]["line"]))
    lines = [f"AST-OP-500 · {len(hits)} 件待審"]
    visited = set()
    for path,item in hits:
        if len(visited)>=3:
            break
        if path in visited:
            continue
        visited.add(path)
        entry = f"{path}:{item['line']} {item['rule']}"
        anchors = rows[path]["anchors"]
        nearest = max(((line,tag) for tag,line in anchors.items() if line<=item["line"]),default=None)
        if nearest:
            entry += f" @{nearest[1]}"
        if len(("\n".join(lines+[entry])).encode()) > HANDOFF_BYTES:
            continue
        lines.append(entry)
        if root is not None and "exact" in rows[path] and item["rule"] != "possible_literal_secret":
            try:
                candidate = overlay/path if overlay is not None else None
                data = read_limited(candidate if candidate and candidate.is_file() else within(root,path))
                if digest(data) == rows[path]["sha256"]:
                    shape = line_shape(data,item["line"])
                    if shape and len(("\n".join(lines+[shape])).encode()) <= HANDOFF_BYTES:
                        lines.append(shape)
            except (ValueError,OSError,UnicodeError,tokenize.TokenError):
                pass
    return "\n".join(lines)


def matrix_page(report):
    esc = lambda x: html.escape(str(x),quote=True)
    summary = report["summary"]
    rows = []
    for path,after in report["files"].items():
        before = report["before_status"][path]
        issues = ", ".join(f"{i['rule']}@{i['line']}" for i in after["issues"])
        rows.append(f"<tr><td>{esc(path)}</td><td>{before}</td><td class='{after['status']}'>{after['status']}</td><td>{esc(issues)}</td></tr>")
    stats = collections.Counter((i["op"],i["rule"]) for row in report["files"].values() for i in row["issues"])
    rollup = "".join(f"<tr><td>AST-OP-{op}</td><td>{esc(rule)}</td><td>{n:,}</td></tr>"
                     for (op,rule),n in sorted(stats.items(),key=lambda kv:(kv[0][0],-kv[1])))
    return ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VIA 全景修復矩陣</title>"
            "<style>body{font:14px system-ui;background:#faf8f3;color:#292820;margin:2em}table{border-collapse:collapse;width:100%}"
            "td,th{padding:5px;text-align:left;border-bottom:1px solid #ccc;overflow-wrap:anywhere}.RED{color:#922}.YELLOW{color:#795400}.GREEN{color:#265a39}</style>"
            "<header>理 · VIA<br>PanoramaGuard · Python AST<br>"+esc(summary["utc"])+" · v"+VERSION+"</header>"
            "<h1>全景掃描與修復矩陣</h1><p>"+esc(summary["decision"])+" · "+esc(summary["backend"]["backend"])+
            "</p><p>基線 "+esc(summary["before"])+" → 本輪 "+esc(summary["after"])+"</p>"
            "<p>Git "+esc(summary["git_sha16"])+" · Python "+str(summary["files"])+" 檔 · 專案測試 "+esc(summary["project_tests"])+"</p>"
            "<p>測試選集 "+esc(", ".join(summary.get("test_suites") or []) or "見測試收據")+
            " · 完全相同 AST "+str(summary["duplicate_groups"]["exact"])+" 組 · 同骨架 "+str(summary["duplicate_groups"]["skeleton"])+" 組</p>"
            "<p>子系統契約 "+esc(summary["subsystems"])+"</p>"
            "<h2>異常分類</h2><table><thead><tr><th>分流</th><th>規則</th><th>件數</th></tr></thead><tbody>"+rollup+"</tbody></table><h2>逐檔明細</h2>"
            "<p>每檔採最高嚴重度計燈。下表列出規則及行號，同一檔可有多項。</p><table><thead><tr>"
            "<th>相對路徑</th><th>基線</th><th>本輪</th><th>規則與行號</th></tr></thead><tbody>"+
            "".join(rows)+"</tbody></table></html>")


def previous_receipts(out, scope, project):
    """Read accepted baselines for this rule set and the project's last scan."""
    by_scope = last_scan = last_project = None
    ledger = out/"universal_ledger.jsonl"
    if ledger.exists():
        with ledger.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                if record.get("accepted") is not True or record.get("project_key") != project:
                    continue
                last_project = record
                if record["scope"] == scope:
                    by_scope = record
                if record["mode"] == "scan":
                    last_scan = record
    return by_scope,last_scan,last_project


def append_ledger(out, record):
    """Append and flush a single audit record while the caller holds the writer lock."""
    with (out/"universal_ledger.jsonl").open("ab") as stream:
        stream.write(json_bytes(record)+b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def frozen(rel):
    p = Path(rel)
    return bool({x.lower() for x in p.parts} & PROTECTED) or p.name.startswith(("VeritasCeleritas","SUP_MDL737_"))


# [AST-ANCHOR: PROJECT_TEST_GATE]
def project_test_worker(root, destination, suite_rel):
    """Run unittest discovery in a separate process; export identifiers and outcomes only."""
    sys.path.insert(0,str(root))
    results = {}
    class Outcomes(unittest.TextTestResult):
        def record(self, case, status):
            results.setdefault(case.id(),[]).append(status)
        def addSuccess(self, case):
            self.record(case,"pass")
            super().addSuccess(case)
        def addFailure(self, case, err):
            self.record(case,"failure")
            super().addFailure(case,err)
        def addError(self, case, err):
            self.record(case,"error")
            super().addError(case,err)
        def addSkip(self, case, reason):
            self.record(case,"skip")
            super().addSkip(case,reason)
        def addExpectedFailure(self, case, err):
            self.record(case,"expected_failure")
            super().addExpectedFailure(case,err)
        def addUnexpectedSuccess(self, case):
            self.record(case,"unexpected_success")
            super().addUnexpectedSuccess(case)
        def addSubTest(self, case, subtest, err):
            # Avoid parameter values in logs. Preserve subtest sequence per method.
            self.record(case,"subpass" if err is None else "subfail")
            super().addSubTest(case,subtest,err)
    start = within(root,suite_rel)
    suite = unittest.TestLoader().discover(str(start),pattern="test*.py")
    with open(os.devnull,"w") as sink:
        result=unittest.TextTestRunner(stream=sink,resultclass=Outcomes).run(suite)
    atomic_write(destination,json_bytes({"ran":result.testsRun,"outcomes":results,"ok":result.wasSuccessful()}))


def compare_project_tests(root, overlay, work, baseline_only=False, suites=None):
    """Create two independent copies of a trusted project and test both with the same interpreter."""
    def ignore(folder,names):
        return [n for n in names if n.lower() in SKIP or is_link(Path(folder)/n)]
    results={}
    for phase in (("before",) if baseline_only else ("before","after")):
        target=work/phase
        shutil.copytree(root,target,ignore=ignore)
        if phase=="after" and overlay.is_dir():
            shutil.copytree(overlay,target,dirs_exist_ok=True)
        suite_dirs = suites or checked_manifest(root).get("test_suites") or ["tests" if (root/"tests").is_dir() else "."]
        aggregate = {"ran":0,"ok":True,"outcomes":{}}
        for index,rel in enumerate(dict.fromkeys(suite_dirs)):
            start = within(target,rel)
            if not start.is_dir():
                aggregate["ok"] = False
                aggregate["missing_suite"] = rel
                break
            dst=work/f"{phase}-{index}.json"
            cmd=[sys.executable,"-I","-B",str(Path(__file__).resolve()),"_unittest",str(target),str(dst),rel]
            try:
                proc=subprocess.run(cmd,cwd=target,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,timeout=TEST_TIMEOUT)
            except subprocess.TimeoutExpired:
                aggregate.update(ok=False,timeout=rel)
                break
            if proc.returncode or not dst.is_file():
                aggregate.update(ok=False,runner_failed=rel)
                break
            suite=read_json(dst)
            aggregate["ran"] += suite["ran"]
            aggregate["ok"] = aggregate["ok"] and suite["ok"] and suite["ran"] > 0
            for case,statuses in suite["outcomes"].items():
                aggregate["outcomes"][rel+"::"+case] = statuses
        results[phase] = aggregate
        shutil.rmtree(target)
    if baseline_only:
        baseline=results["before"]
        if not baseline.get("ran"):
            return results,"NO_TEST_EVIDENCE"
        if not baseline["ok"]:
            return results,"TEST_FAILURES_REMAIN"
        if not any("pass" in seq or "subpass" in seq for seq in baseline["outcomes"].values()):
            return results,"NO_PASS_EVIDENCE"
        return results,"PASS"
    old,new=results["before"],results["after"]
    if not old.get("ran") or not new.get("ran"):
        return results,"NO_TEST_EVIDENCE"
    bad={"error","failure","unexpected_success","subfail"}
    before,after=old["outcomes"],new["outcomes"]
    for case,statuses in before.items():
        latest=after.get(case,[])
        if len(latest)<len(statuses) or any(a in ("pass","subpass") and a!=b for a,b in zip(statuses,latest)):
            return results,"TEST_REGRESSION"
    for case,statuses in after.items():
        if sum(s in bad for s in statuses)>sum(s in bad for s in before.get(case,[])):
            return results,"TEST_REGRESSION"
    if not new["ok"]:
        return results,"TEST_FAILURES_REMAIN"
    if not any(s in {"pass","subpass"} for statuses in after.values() for s in statuses):
        return results,"NO_PASS_EVIDENCE"
    return results,"PASS"


def run_engine(root, out, mode, workers, narrow=False, docs=False, required=False, project_tests=False, commit=False, test_suites=None):
    root, out = root.resolve(strict=True), out.resolve()
    if not root.is_dir() or out.is_relative_to(root):
        raise ValueError("輸出目錄必須位於受掃工作樹之外")
    if not 1 <= workers <= 32:
        raise ValueError("workers 範圍 1–32")
    if commit and (mode != "repair" or git(root,"status","--porcelain").strip()):
        raise ValueError("Git 提交模式需要乾淨工作樹及 repair")
    project_tests = project_tests or commit or bool(test_suites)
    conf = checked_manifest(root)
    max_rounds = conf.get("ssot_policy",{}).get("max_ratchet_iterations",MAX_ROUNDS)
    if type(max_rounds) is not int or not 1 <= max_rounds <= MAX_ROUNDS:
        raise ValueError("max_ratchet_iterations 範圍 1–3")
    mapper, backend = accelerator(root,required)
    names = inventory(root,conf)
    if set(conf.get("api_contracts",{}))-set(names):
        raise ValueError("API 契約檔案位於掃描清單以外")
    if not names:
        raise ValueError("掃描範圍內沒有 Python 檔")
    out.mkdir(parents=True,exist_ok=True)
    with writer_lock(out), tempfile.TemporaryDirectory(prefix=".stage-",dir=out) as temp:
        staging = Path(temp)/"result"
        staging.mkdir()
        pool_mode = "process" if len(names) >= PROCESS_THRESHOLD and workers > 1 else "thread"
        backend["mode"] = pool_mode
        print(f"AST-OP-200 · {len(names)} files · {backend['backend']} · {workers} workers",file=sys.stderr,flush=True)
        records = mapper(functools.partial(inspect_file,root,conf), names,max_workers=workers,mode=pool_mode)
        if len(records)!=len(names) or any(not isinstance(row,dict) for row in records):
            raise RuntimeError("加速器回傳不完整")
        before = dict(zip(names,records,strict=True))
        after = before.copy()
        changed, rounds, blocked = set(), [], []
        run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"-"+uuid.uuid4().hex[:12]
        project_key = digest(json_bytes([str(root),VERSION]))
        scope = digest(json_bytes([project_key,mode,narrow,docs,project_tests]))
        policy_hash = digest(json_bytes([RULES,conf]))
        prev,prior_scan,last_project = previous_receipts(out,scope,project_key)
        if last_project and last_project["policy_hash"] != policy_hash:
            blocked.append(["*","BASELINE_RESET_REQUIRED"])
        if mode == "repair":
            # This evidence survives a crash. Only a completed run advances the ratchet.
            append_ledger(out,dict(event="PRE_REPAIR_BASELINE",accepted=False,run=run,
                                  utc=datetime.now(timezone.utc).isoformat(),project_key=project_key,
                                  scope=scope,policy_hash=policy_hash,mode=mode,git_sha16=git_sha(root),
                                  files=len(names),before=counts(before)))
            seen = {digest(json_bytes([r["sha256"] for r in before.values()]))}
            for round_no in range(1,max_rounds+1):
                if blocked:
                    break
                writes = 0
                for rel, row in list(after.items()):
                    if frozen(rel) or "exact" not in row or not any(i["op"] in (300,400) for i in row["issues"]):
                        continue
                    target = staging/"overlay"/rel
                    raw = read_limited(target if rel in changed else within(root,rel))
                    if digest(raw) != row["sha256"]:
                        raise ValueError("掃描期間來源已變更 "+rel)
                    try:
                        candidate = patch_bytes(raw,rel,row,narrow,docs,conf.get("static_guard_rules",{}).get("min_ast_anchors",1))
                        if candidate == raw:
                            continue
                        check = inspect_bytes(candidate,rel,conf)
                        if "exact" not in check or reds({rel:check}) - reds({rel:row}):
                            raise ValueError("NEW_RED")
                        atomic_write(target,candidate)
                        if digest(read_limited(target)) != check["sha256"]:
                            raise ValueError("OVERLAY_HASH")
                    except (ValueError,SyntaxError,RecursionError,UnicodeError) as err:
                        blocked.append([rel,type(err).__name__])
                        break
                    after[rel] = check
                    changed.add(rel)
                    writes += 1
                rounds.append({"round":round_no,"writes":writes})
                if not writes or blocked:
                    break
                state = digest(json_bytes([r["sha256"] for r in after.values()]))
                if state in seen:
                    blocked.append(["*","repair_oscillation"])
                    break
                seen.add(state)
        test_status = "NOT_RUN"
        if project_tests:
            outcomes,test_status = compare_project_tests(root,staging/"overlay",Path(temp),baseline_only=mode=="scan",suites=test_suites)
            atomic_write(staging/"project-tests.json",json_bytes(outcomes))
            if test_status != "PASS":
                blocked.append(["*",test_status])
        # Second independent enumeration and content read detect source drift before publication.
        if inventory(root,checked_manifest(root))!=names or checked_manifest(root)!=conf:
            blocked.append(["*","manifest_or_inventory_drift"])
        for rel in names:
            known = before[rel]["sha256"]
            if known is None:
                blocked.append([rel,"incomplete_coverage"])
            else:
                source = read_limited(within(root,rel))
                if digest(source) != known:
                    blocked.append([rel,"source_drift"])
                if mode == "repair" and "exact" in after[rel]:
                    disk = read_limited(staging/"overlay"/rel) if rel in changed else source
                    audit_tree = ast.parse(disk,rel,type_comments=True)
                    if digest(disk) != after[rel]["sha256"] or structural_hash(audit_tree) != after[rel]["exact"]:
                        blocked.append([rel,"panorama_B_mismatch"])
        if prior_scan and counts(after)["RED"] > prior_scan["after"]["RED"]:
            blocked.append(["*","scan_baseline_regression"])
        if prev and prev.get("test_suites") != test_suites:
            blocked.append(["*","TEST_SCOPE_RESET_REQUIRED"])
        if prev and prev.get("policy_hash") != policy_hash:
            blocked.append(["*","BASELINE_RESET_REQUIRED"])
        if reds(after)-reds(before):
            blocked.append(["*","new_red_issue"])
        if prev and counts(after)["RED"] > prev["after"]["RED"]:
            blocked.append(["*","historical_red_regression"])
        accepted = not blocked
        decision = "FAIL_STOP" if blocked else ("REVIEW_RED" if counts(after)["RED"] else
                                                "REVIEW_YELLOW" if counts(after)["YELLOW"] else "PASS")
        summary = dict(run=run,utc=datetime.now(timezone.utc).isoformat(),engine=VERSION,mode=mode,
                       git_sha16=git_sha(root),backend=backend,workers=workers,files=len(names),
                       project_key=project_key,test_suites=test_suites,policy_hash=policy_hash,active_rules=RULES | conf.get("static_guard_rules",{}),
                       before=counts(before),after=counts(after),decision=decision,rounds=rounds,
                       published_overlay_files=len(changed) if accepted else 0,scope=scope,
                       project_tests=test_status,accepted=accepted,prior_run=prev["run"] if prev else None)
        summary["event"] = ("RATCHET_FAIL_STOP" if blocked else "INIT_BASELINE" if prev is None and mode=="scan" else "RATCHET_PASS")
        if blocked:
            if (staging/"overlay").exists():
                shutil.rmtree(staging/"overlay")
        report = dict(summary=summary,blocked=blocked,files=after,
                      before_status={p:r["status"] for p,r in before.items()},
                      changes={p:{"before":before[p]["sha256"],"candidate":after[p]["sha256"]} for p in sorted(changed)},
                      duplicates={k:duplicates(after,k) for k in ("exact","skeleton")})
        if commit and accepted:
            try:
                result = commit_candidate(root,staging,report)
                if "repository" in result:
                    result["repository"] = str(out/run/"candidate-git")
            except (ValueError,OSError,subprocess.SubprocessError) as err:
                blocked.append(["*","git_candidate_rollback"])
                result = {"event":"GIT_FAIL_STOP","reason":str(err)}
                summary.update(event="RATCHET_FAIL_STOP",accepted=False,decision="FAIL_STOP",published_overlay_files=0)
                if (staging/"overlay").is_dir():
                    shutil.rmtree(staging/"overlay")
            summary["git_result"] = result
            atomic_write(staging/"git-result.json",json_bytes(result))
        summary["triage"] = dict(collections.Counter(str(i["op"]) for r in after.values() for i in r["issues"]))
        summary["duplicate_groups"] = {k:len(v) for k,v in report["duplicates"].items()}
        summary["subsystems"] = dict(collections.Counter(r.get("subsystem") or ("UNREGISTERED" if conf.get("subsystems") else "NOT_CONFIGURED") for r in after.values()))
        if "include_files" in conf:
            disk_names = inventory(root,{k:v for k,v in conf.items() if k!="include_files"})
            report["unregistered_files"] = sorted(set(disk_names)-set(names))
            summary["unregistered_count"] = len(report["unregistered_files"])
        if not (root/MANIFEST).exists():
            atomic_write(staging/MANIFEST,json_bytes({"include_files":names,"static_guard_rules":RULES}))
        for name,data in (("report.json",json_bytes(report)),("matrix.html",matrix_page(report).encode()),
                          ("handoff.txt",public_handoff(after,root,staging/"overlay").encode()),("summary.json",json_bytes(summary))):
            atomic_write(staging/name,data)
        path = out/run
        staging.rename(path)
        try:
            append_ledger(out,summary)
        except OSError:
            # A completed run not referenced by a durable ledger is not an accepted baseline.
            raise RuntimeError(f"收據已生成但帳本寫入失敗 {path}")
        return (2 if blocked else 1 if summary["after"]["RED"] else 0), path, summary


# [AST-ANCHOR: MCP_READ_ONLY]
def mcp_tools():
    no_args = {"type":"object","properties":{},"additionalProperties":False}
    page = {"type":"object","properties":{"offset":{"type":"integer","minimum":0},
            "limit":{"type":"integer","minimum":1,"maximum":50}},"additionalProperties":False}
    return [{"name":name,"description":desc,"inputSchema":schema,"annotations":{"readOnlyHint":True}}
            for name,desc,schema in (("summary","本輪範圍、燈號、測試狀態與加速器收據",no_args),
                                     ("findings","分頁讀取逐檔靜態診斷；省略原始碼與常值",page),
                                     ("handoff","壓縮的 AST-OP-500 待審清單",no_args))]


def tool_result(name,args,run):
    if not isinstance(args,dict):
        raise ValueError("arguments 必須是物件")
    if name in ("summary","handoff") and not args:
        return (run/"handoff.txt").read_text(encoding="utf-8") if name=="handoff" else read_json(run/"summary.json")
    if name=="findings" and not (set(args)-{"offset","limit"}):
        offset,limit = args.get("offset",0),args.get("limit",20)
        if type(offset) is not int or type(limit) is not int or offset<0 or not 1<=limit<=50:
            raise ValueError("無效分頁")
        rows = read_json(run/"report.json")["files"]
        import itertools
        seq = (dict(file=rel,**i) for rel,row in rows.items() for i in row["issues"])
        group = list(itertools.islice(seq,offset,offset+limit+1))
        return {"items":group[:limit],"next_offset":offset+limit if len(group)>limit else None}
    raise ValueError("未知工具或參數")


def serve(run, inp, out):
    """固定本次收據，不接受用戶端傳入檔案路徑、shell 指令或寫入操作。"""
    if not (run/"summary.json").is_file():
        raise ValueError("指定的 --run 缺少 summary.json")
    initialized = ready = False
    for line in inp:
        ident = None
        try:
            msg = json.loads(line)
        except (ValueError,UnicodeError):
            out.write(json_bytes({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Parse error"}})+b"\n")
            out.flush()
            continue
        valid = isinstance(msg,dict) and msg.get("jsonrpc")=="2.0" and isinstance(msg.get("method"),str)
        if valid and "id" not in msg:
            if initialized and msg["method"]=="notifications/initialized":
                ready=True
            continue
        try:
            if not valid or type(msg.get("id")) not in (str,int):
                raise KeyError((-32600,"Invalid Request"))
            ident,method,params = msg["id"],msg["method"],msg.get("params",{})
            if not isinstance(params,dict):
                raise ValueError("params 必須是物件")
            if method=="initialize" and not initialized:
                v = params.get("protocolVersion")
                result = {"protocolVersion":v if v in PROTOCOLS else PROTOCOLS[0],
                          "capabilities":{"tools":{"listChanged":False}},
                          "serverInfo":{"name":"VIA_PanoramaGuard","version":VERSION}}
                initialized=True
            elif method=="ping":
                result={}
            elif not ready:
                raise KeyError((-32002,"Client not initialized"))
            elif method=="tools/list":
                result={"tools":mcp_tools()}
            elif method=="tools/call":
                content = tool_result(params.get("name"),params.get("arguments",{}),run)
                result={"content":[{"type":"text","text":content if isinstance(content,str) else json_bytes(content).decode()}]}
            else:
                raise KeyError((-32601,"Method not found"))
            reply={"result":result}
        except KeyError as err:
            code,message = err.args[0] if isinstance(err.args[0],tuple) else (-32603,"Invalid receipt")
            reply={"error":{"code":code,"message":message}}
        except (ValueError,TypeError,OSError,OverflowError):
            reply={"error":{"code":-32602,"message":"Invalid arguments or unavailable receipt"}}
        out.write(json_bytes({"jsonrpc":"2.0","id":ident,**reply})+b"\n")
        out.flush()


# [AST-ANCHOR: ISOLATED_GIT]
def git(root, *args):
    """Run Git with literal pathspecs and return its result without echoing file contents."""
    proc = subprocess.run(["git","--literal-pathspecs","-C",str(root),*args],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL)
    if proc.returncode:
        raise ValueError(f"Git {args[0]} failed (rc={proc.returncode})")
    return proc.stdout


def commit_candidate(root, run, report=None):
    """Build one local candidate commit. A failed attempt discards only the temporary clone."""
    root = root.resolve(strict=True)
    if report is None:
        report = read_json(run/"report.json")
    summary = report["summary"]
    if not summary["accepted"] or summary["project_tests"] != "PASS":
        raise ValueError("Git 提交需要通過修復後的專案測試與棘輪")
    if not report["changes"]:
        return {"event":"FIXED_POINT","committed_files":0}
    if Path(os.fsdecode(git(root,"rev-parse","--show-toplevel")).strip()).resolve() != root:
        raise ValueError("Git 提交模式的 root 必須是儲存庫根目錄")
    head = git(root,"rev-parse","HEAD").decode().strip()
    if head[:16] != summary["git_sha16"] or git(root,"status","--porcelain=v1","--untracked-files=all").strip():
        raise ValueError("工作樹或版本已變更，來源修改已保留")
    with tempfile.TemporaryDirectory(dir=run,prefix=".git-transaction-") as tmp:
        candidate = Path(tmp)/"repository"
        git(root,"clone","--no-hardlinks","--no-checkout","--",str(root),str(candidate))
        git(candidate,"remote","remove","origin")
        branch = "via/panorama-"+summary["run"]
        git(candidate,"-c","core.hooksPath="+os.devnull,"checkout","-b",branch,head)
        for rel,change in report["changes"].items():
            original = within(candidate,rel)
            if not git(candidate,"ls-files","--error-unmatch","--",rel).strip():
                raise ValueError("候選檔未受 Git 追蹤")
            overlay = read_limited(within(run/"overlay",rel))
            if digest(overlay)!=change["candidate"] or digest(read_limited(original))!=change["before"]:
                raise ValueError("候選 SHA 對帳失敗 "+rel)
            filemode = original.stat().st_mode
            atomic_write(original,overlay)
            original.chmod(stat.S_IMODE(filemode))
        git(candidate,"add","-u")
        staged = {os.fsdecode(x) for x in git(candidate,"diff","--cached","--name-only","-z").split(b"\0") if x}
        if staged != set(report["changes"]):
            raise ValueError("Git 暫存清單與驗證收據不一致")
        git(candidate,"-c","core.hooksPath="+os.devnull,"-c","commit.gpgSign=false",
            "-c","user.name=VIA PanoramaGuard","-c","user.email=via-panorama@localhost",
            "commit","-m","chore(AST-AutoFix): panorama ratchet pass")
        sha = git(candidate,"rev-parse","HEAD").decode().strip()
        if git(root,"rev-parse","HEAD").decode().strip()!=head or git(root,"status","--porcelain").strip():
            raise ValueError("提交時來源工作樹已變更")
        final = run/"candidate-git"
        candidate.rename(final)
    return {"event":"LOCAL_COMMIT","commit":sha,"parent":head,"branch":branch,
            "committed_files":len(staged),"repository":str(final)}


def template(kind):
    """Print configuration, sample ledger, or an optional PS7 launcher to stdout."""
    if kind == "manifest":
        order = ["VCGC","VDF","VRN","VAP","VPNS"]
        return json.dumps({
            "$schema":"via-panorama-manifest-v1","project_name":"Veritas_Intelligence_Analytics",
            "ssot_policy":{"source_of_truth":"functional_filename","allow_direct_text_replace":False,
                           "require_compile_sandbox":True,"max_ratchet_iterations":MAX_ROUNDS},
            "exclude_patterns":[".git/**",".venv/**","node_modules/**"],
            "subsystems":{s:{"prefix":s+"_","allowed_imports":order[:i+1]} for i,s in enumerate(order)},
            "static_guard_rules":RULES,"api_contracts":{},"test_suites":["tests"]},indent=2)
    if kind == "ledger":
        return json.dumps({"example":True,"event":"INIT_BASELINE","accepted":True,"run":"example",
                           "scope":"example","policy_hash":"example","git_sha16":"0123456789abcdef",
                           "before":{"GREEN":2,"YELLOW":1,"RED":1},"after":{"GREEN":2,"YELLOW":1,"RED":1}})
    return r"""#requires -Version 7.0
param([string]$Root = (Get-Location).Path, [switch]$Repair, [switch]$Commit)
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$engine = Join-Path $PSScriptRoot 'VIA_PanoramaGuard_v0101.py'
$operation = if ($Repair -or $Commit) { 'repair' } else { 'scan' }
$viaArgs = @('-I', $engine, $operation, '--root', $Root)
if ($Repair -or $Commit) { $viaArgs += @('--project-tests','--draft-docstrings','--narrow-except') }
if ($Commit) { $viaArgs += '--commit' }
& python @viaArgs
exit $LASTEXITCODE"""


# [AST-ANCHOR: ACCEPTANCE]
def selftest():
    from unittest.mock import patch
    class Acceptance(unittest.TestCase):
        def setUp(self):
            self.temp = tempfile.TemporaryDirectory()
            self.addCleanup(self.temp.cleanup)
            self.root = Path(self.temp.name)/"source"
            self.root.mkdir()
            self.out = Path(self.temp.name)/"outputs"
        def file(self,rel,raw):
            p=self.root/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(raw)
            return p
        def run_case(self,mode="scan",**opts):
            return run_engine(self.root,self.out,mode,2,**opts)
        def test_bom_crlf_cookie_and_overlay(self):
            import codecs
            raw=codecs.BOM_UTF8+"#!/usr/bin/python\r\n# coding: utf-8\r\n# 中文\r\nX=1".encode()
            p=self.file("VCGC_Core.py",raw)
            rc,run,_=self.run_case("repair")
            self.assertEqual(rc,0)
            self.assertEqual(p.read_bytes(),raw)
            self.assertEqual((run/"overlay"/p.name).read_bytes(),raw[:-3]+b"# [AST-ANCHOR: VCGC_CORE]\r\nX=1")
        def test_legacy_encoding(self):
            raw="# coding: cp950\r\nx='台灣'".encode("cp950")
            self.file("VDF_1.py",raw)
            _,run,_=self.run_case("repair")
            self.assertEqual((run/"overlay/VDF_1.py").read_bytes(),raw.replace(b"x=", b"# [AST-ANCHOR: VDF_1]\r\nx="))
        def test_bare_except_requires_opt_in(self):
            raw=b"try: pass\nexcept:  # Keep\n    pass\n"
            self.file("x.py",raw)
            rc,path,_=self.run_case("repair")
            self.assertEqual(rc,1)
            self.assertIn(b"except:",(path/"overlay/x.py").read_bytes())
            rc,path,_=self.run_case("repair",narrow=True)
            self.assertEqual(rc,0)
            self.assertIn(b"except Exception:  # Keep",(path/"overlay/x.py").read_bytes())
        def test_docs_inline_and_decorator(self):
            self.file("x.py",b"def example():\n    @staticmethod\n    def _inner(): pass\n    return _inner\ndef inline(): return 1\n")
            _,path,_=self.run_case("repair",docs=True)
            src=(path/"overlay/x.py").read_bytes()
            self.assertIn(b'"""TODO: describe example"""',src)
            self.assertIn(b'def inline(): return 1',src)
            self.assertEqual(read_json(path/"summary.json")["after"]["YELLOW"],1)
        def test_colliding_spans(self):
            with self.assertRaisesRegex(ValueError,"SPAN_COLLISION"):
                apply_spans(b"abcdef",[(1,4,b"X"),(3,5,b"Y")])
        def test_dual_hash(self):
            a,b=[ast.parse(t) for t in ("def f(x): return x+1","def g(y): return y+2")]
            self.assertNotEqual(structural_hash(a),structural_hash(b))
            self.assertEqual(structural_hash(a,True),structural_hash(b,True))
        def test_import_guard_and_anchors(self):
            c={"subsystems":{"VDF":{"allowed_imports":["VDF"]},"VRN":{}}}
            row=inspect_bytes(b"# [AST-ANCHOR: A]\n# [AST-ANCHOR: A]\nfrom pkg import VRN_Helper\n", "VDF_Demo.py",c)
            self.assertEqual({i["rule"] for i in row["issues"]},{"duplicate_anchor","forbidden_import"})
        def test_handoff_limits_and_redaction(self):
            raw=b'api_key="private-value-example"\n'
            self.assertNotIn("private-value-example",line_shape(raw,1))
            row=inspect_bytes(raw,"secret.py",{})
            self.file("secret.py",raw)
            handoff=public_handoff({"secret.py":row},self.root)
            self.assertLessEqual(len(handoff.encode()),HANDOFF_BYTES)
            self.assertNotIn("private-value-example",handoff)

        def test_secret_redaction(self):
            row=inspect_bytes(b"api_key='private-value-example'\n","demo.py",{})
            self.assertIn("possible_literal_secret",str(row))
            self.assertNotIn("private-value-example",str(row))
        def test_fail_stop_preserves_ledger_baseline(self):
            p=self.file("x.py",b"pass\n")
            self.run_case("repair")
            p.write_bytes(b"try: pass\nexcept: pass\n")
            rc,run,_=self.run_case("repair")
            self.assertEqual(rc,2)
            self.assertFalse((run/"overlay").exists())
            p.write_bytes(b"pass\n")
            self.assertEqual(self.run_case("repair")[0],0)
        def test_boundary_and_manifest(self):
            self.file(MANIFEST,json_bytes({"include_files":["../other.py"]}))
            with self.assertRaises(ValueError):
                self.run_case()
        def test_retries(self):
            p=self.root/"x.txt"
            replace=os.replace
            calls=[]
            def flaky(a,b):
                calls.append(1)
                if len(calls)<3:
                    raise PermissionError()
                replace(a,b)
            with patch("os.replace",side_effect=flaky),patch("time.sleep"):
                atomic_write(p,b"ready")
            self.assertEqual(p.read_bytes(),b"ready")
            self.assertEqual(len(calls),3)
        def test_syntax_failure_and_no_execution(self):
            self.file("a.py",b"raise RuntimeError('must never execute')\n")
            self.file("b.py",b"return 1\n")
            rc,run,_=self.run_case()
            self.assertEqual(rc,1)
            self.assertEqual(read_json(run/"report.json")["files"]["b.py"]["status"],"RED")
        def test_mcp_transport(self):
            self.file("x.py",b"pass\n")
            _,run,_=self.run_case()
            methods=[("initialize",{"protocolVersion":PROTOCOLS[0]}),("notifications/initialized",{}),
                     ("tools/list",{}),("tools/call",{"name":"summary"}),("tools/call",{"name":"findings"}),
                     ("tools/call",{"name":"handoff"}),("tools/call",{"name":"repair"})]
            messages=[{"jsonrpc":"2.0","method":m,"params":p,**({} if i==1 else {"id":i})}
                      for i,(m,p) in enumerate(methods)]
            stream=io.BytesIO()
            serve(run,io.BytesIO(b"\n".join(map(json_bytes,messages))),stream)
            replies=[json.loads(x) for x in stream.getvalue().splitlines()]
            self.assertEqual(len(replies),6)
            self.assertEqual(len(replies[1]["result"]["tools"]),3)
            self.assertTrue(all("result" in x for x in replies[:-1]))
            self.assertIn("error",replies[-1])
        def test_project_regression_withholds_candidate(self):
            self.file("runner.py",b"def handle():\n    try: raise KeyboardInterrupt()\n    except: return 1\n")
            self.file("tests/test_runner.py",b"import unittest\nfrom runner import handle\nclass Test(unittest.TestCase):\n    def test_case(self):\n        self.assertEqual(handle(),1)\n")
            # A previously caught interrupt terminates discovery in the candidate process.
            rc,run,summary=self.run_case("repair",narrow=True,project_tests=True)
            self.assertEqual(rc,2)
            self.assertNotEqual(summary["project_tests"],"PASS")
            self.assertFalse((run/"overlay").exists())
        def test_project_suite_on_both_copies(self):
            self.file("tests/test_ok.py",b"import unittest\nclass Test(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n")
            rc,run,summary=self.run_case("repair",project_tests=True)
            self.assertEqual((rc,summary["project_tests"]),(0,"PASS"))
            self.assertEqual(read_json(run/"project-tests.json")["before"]["ran"],1)
        def test_commit_or_rollback_on_separate_branch(self):
            self.file("module.py",b"VALUE=1\n")
            self.file("tests/test_ok.py",b"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")
            git(self.root,"init","-q")
            git(self.root,"add",".")
            git(self.root,"-c","user.email=t@localhost","-c","user.name=Test","commit","-qm","baseline")
            rc,run,summary=self.run_case("repair",project_tests=True)
            self.assertEqual(rc,0)
            base=git(self.root,"rev-parse","HEAD").strip().decode()
            result=commit_candidate(self.root,run)
            self.assertEqual(result["parent"],base)
            self.assertNotEqual(result["commit"],base)
            self.assertEqual(git(self.root,"status","--porcelain"),b"")
            self.assertEqual(git(Path(result["repository"]),"remote"),b"")
            (run/"overlay/module.py").write_bytes(b"CHANGED=1\n")
            with self.assertRaisesRegex(ValueError,"SHA"):
                commit_candidate(self.root,run)
            self.assertFalse(list(run.glob(".git-transaction-*")))

        def test_git_failure_is_not_accepted(self):
            self.file("x.py",b"A=0\n")
            self.file("tests/test_ok.py",b"import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")
            git(self.root,"init","-q")
            git(self.root,"add",".")
            git(self.root,"-c","user.email=t@localhost","-c","user.name=T","commit","-qm","baseline")
            with patch(__name__+".commit_candidate",side_effect=ValueError("simulated")):
                rc,path,summary=self.run_case("repair",commit=True)
            self.assertEqual(rc,2)
            self.assertFalse(summary["accepted"])
            self.assertFalse((path/"overlay").exists())
            self.assertEqual(json.loads((self.out/"universal_ledger.jsonl").read_bytes().splitlines()[-1])["event"],"RATCHET_FAIL_STOP")

        def test_multiline_inline_suite_and_first_comment(self):
            raw=b"def first(\n x): return x\ndef second(\n *,x):\n # keep\n return x\n"
            row=inspect_bytes(raw,"demo.py",{})
            patched=patch_bytes(raw,"demo.py",row,docs=True)
            a,b=ast.parse(patched).body
            self.assertIsNone(ast.get_docstring(a))
            self.assertIn("Args: x",ast.get_docstring(b))
            self.assertLess(patched.index(b"TODO"),patched.index(b"# keep"))

        def test_manifest_api_contracts(self):
            cfg={"api_contracts":{"m.py":{"keyword_parameters":{"run":["x","y"]},
                 "required_imports":["bridge"],"column_lists":{"COLS":["ticker","date"]}}}}
            row=inspect_bytes(b'COLS=["date","ticker"]\ndef run(x): return x\n',"m.py",cfg)
            self.assertTrue({"keyword_contract","missing_import_bridge","column_order_or_name_mismatch"} <= {i["rule"] for i in row["issues"]})

        def test_required_minimum_and_policy_change(self):
            self.file(MANIFEST,json_bytes({"static_guard_rules":{"min_ast_anchors":3}}))
            self.file("demo.py",b"# [AST-ANCHOR: DEMO]\nx=1\n")
            rc,run,_=self.run_case("repair")
            self.assertEqual(rc,0)
            self.assertEqual(len(read_json(run/"report.json")["files"]["demo.py"]["anchors"]),3)
            self.file(MANIFEST,json_bytes({"static_guard_rules":{"min_ast_anchors":1}}))
            self.assertEqual(self.run_case("repair")[0],2)

        def test_accelerator_hash_gate(self):
            self.file("supportive modules/x.py",b"raise AssertionError()")
            self.file(LOCK.as_posix(),json_bytes({"accelerator":{"version":"v1141","sha256":CEL_SHA,
                "path":"VeritasIntelligenceAnalytics/supportive modules/x.py"}}))
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                self.run_case()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 2


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version",action="version",version=VERSION)
    subs=ap.add_subparsers(dest="mode",required=True)
    for name in ("scan","repair"):
        p=subs.add_parser(name)
        p.add_argument("--root",type=Path,default=Path.cwd(),help="專案或 VIA 根目錄")
        p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT,help="工作樹外的收據目錄")
        p.add_argument("--workers",type=int,default=WORKERS)
        p.add_argument("--require-accelerator",action="store_true")
        p.add_argument("--suite",action="append",help="unittest 目錄，相對於 root，可指定多次；啟動測試閘")
        p.add_argument("--project-tests",action="store_true",help="在獨立副本執行受信任專案的 unittest")
        if name=="repair":
            p.add_argument("--commit",action="store_true",help="通過前後專案測試後，在獨立本地 clone 提交")
            p.add_argument("--narrow-except",action="store_true",help="候選檔改抓 Exception，會放行 KeyboardInterrupt/SystemExit")
            p.add_argument("--draft-docstrings",action="store_true",help="產生文件草稿，維持黃燈待審")
    settings=subs.add_parser("template")
    settings.add_argument("kind",choices=["manifest","ledger","powershell"])
    subs.add_parser("selftest")
    p=subs.add_parser("serve",help="固定同一批收據的 MCP stdio")
    p.add_argument("--run",type=Path,required=True)
    argv=sys.argv[1:]
    if not argv or argv[0].startswith("--") and argv[0] not in ("--help","--version"):
        applying = "--apply" in argv
        argv = ["repair" if applying else "scan"] + [arg for arg in argv if arg!="--apply"]
    args=ap.parse_args(argv)
    if args.mode=="template":
        print(template(args.kind))
        return 0
    if args.mode=="selftest":
        return selftest()
    if args.mode=="serve":
        serve(args.run,sys.stdin.buffer,sys.stdout.buffer)
        return 0
    rc,path,summary=run_engine(args.root,args.output,args.mode,args.workers,getattr(args,"narrow_except",False),
                               getattr(args,"draft_docstrings",False),args.require_accelerator,args.project_tests,
                               getattr(args,"commit",False),args.suite)
    mcp_config={"mcpServers":{"VIA_PanoramaGuard":{"command":sys.executable,
                "args":["-I",str(Path(__file__).resolve()),"serve","--run",str(path)]}}}
    print(json.dumps({"receipt":str(path),"mcp_config":mcp_config,**summary},ensure_ascii=True,indent=2))
    return rc


if __name__=="__main__":
    try:
        if len(sys.argv)==5 and sys.argv[1]=="_unittest":
            project_test_worker(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
            sys.exit(0)
        sys.exit(main())
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,RecursionError) as err:
        print(f"VIA BLOCKED · {type(err).__name__} · {err}",file=sys.stderr)
        sys.exit(2)
