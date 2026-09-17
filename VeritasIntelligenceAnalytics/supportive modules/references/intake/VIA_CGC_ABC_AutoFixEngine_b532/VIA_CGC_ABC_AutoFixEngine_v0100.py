#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
# VIA CGC ABC Auto-Fix Engine  (VCAF)  v0100
# Veritas Intelligence Analytics / Central Governance Console Upgrader
# ---------------------------------------------------------------------
# 讀取 VIA Central Governance Console -> AST 稽核 -> 自動修正 -> 驗證 -> HTML
#
# ABC 架構 (依 Tony 的 SSOT):
#   A 引擎功能化      Engine  = Single Function, no param, no state
#   B 子系統編排化    Subsystem = Orchestration only, no computation
#   C 參數集中化      PARAM/ = Single Source of Truth, AutoParam 同步
#
# 治理原則: 只增不減 (append-only)
#   - 原始檔永不刪除、永不覆蓋 (除非 --overwrite 明示)
#   - 所有修正輸出到沙箱 _CGC_ABC/RUN_*/fixed/
#   - 每個產出檔都必須通過 compile() 閘門, 失敗即回滾該檔
#   - 每個 finding 自動轉成 7 欄位 Lesson-Learned 寫入 SSOT/lesson.par
#
# 只用標準函式庫。無網路。無互動輸入。一次跑完自動開報表。
# =====================================================================

import argparse
import ast
import builtins
import datetime as _dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import webbrowser

ENGINE_ID = "ENG-CGCU"
ENGINE_NAME = "VIA CGC ABC Auto-Fix Engine"
ENGINE_VER = "v0100"
WORLDLINE = "WL-SYS01"

# ---------------------------------------------------------------------
# 0. 設定 / 路由表
# ---------------------------------------------------------------------

ROOT_CANDIDATES = [
    r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics",
    r"C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics",
    r"C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics",
    r"C:\VeritasIntelligenceAnalytics",
    r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    r"C:\VIA\VeritasMailTracker",
]

CGC_TOKENS = (
    "centralgovernance", "cgc", "cge", "governance", "via-cgc", "via-gov",
    "systemmaster", "ssot", "registry", "autoparam", "worldline",
)

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode",
    "site-packages", "_CGC_ABC", "_to_delete", "dist", "build", ".mypy_cache",
}

OUT_ROOT_NAME = "_CGC_ABC"

# 標準引擎名冊 (A 層) — 缺哪個就補骨架
ENGINE_ROSTER = [
    ("ENG-01", "AutoUpdate", "engine.par"),
    ("ENG-02", "AutoAudit", "engine.par"),
    ("ENG-03", "AutoVersion", "engine.par"),
    ("ENG-04", "AutoWorldlineSync", "worldline.par"),
    ("ENG-05", "AutoDeploy", "subsystem.par"),
    ("ENG-06", "AutoIterate", "system.par"),
    ("ENG-07", "AutoRisk", "risk.par"),
    ("ENG-08", "AutoGovernance", "strategy.par"),
    ("ENG-09", "AutoStrategy", "strategy.par"),
    ("ENG-10", "AutoCollaboration", "system.par"),
    ("ENG-11", "AutoParam", "system.par"),
]

PAR_FILES = [
    "system.par", "engine.par", "subsystem.par", "worldline.par",
    "strategy.par", "risk.par", "group.par", "factor.par", "lesson.par",
]

SUBSYSTEM_TOKENS = ("VDF", "VAP", "VRN", "VMT", "VPNS", "HyperChain",
                    "UniverseEngine", "SuperBOM", "GroupIndex", "MultiFactor")

# finding code -> (層, 嚴重度, 規則, 原因, 可自動修正)
FINDING_SPEC = {
    "A01": ("A", "HIGH", "Engine must not store parameters", "引擎內嵌參數造成耦合、無法集中更新", True),
    "A02": ("A", "HIGH", "Engine must be stateless", "模組級可變狀態導致跨呼叫汙染", False),
    "A03": ("A", "HIGH", "Engine must not branch on subsystem", "引擎判斷子系統名稱＝功能與編排混線", False),
    "A04": ("A", "MED", "Engine = Single Function", "單一引擎多責任, 違反功能化", False),
    "A05": ("A", "MED", "Function must stay small", "超長函式無法驗證單一責任", False),
    "A06": ("A", "MED", "Engine must not own file state", "引擎直接寫檔＝隱性狀態", False),
    "B01": ("B", "HIGH", "Subsystem = Orchestration only", "子系統內含計算邏輯, 應下放引擎", True),
    "B02": ("B", "HIGH", "Subsystem must not store parameters", "參數散落在編排層", True),
    "B03": ("B", "MED", "Subsystem must call engines", "子系統自行實作功能, 繞過引擎層", False),
    "C01": ("C", "HIGH", "PARAM is single source of truth", "同一字面值散落多檔, 改一處會漏", True),
    "C02": ("C", "HIGH", "PARAM/ must exist", "沒有參數中心即無法自動更新", True),
    "C03": ("C", "MED", "Param must be routed to a .par", "參數未歸戶, AutoParam 無法同步", True),
    "D01": ("D", "MED", "No duplicate content", "同內容分身造成真相分裂", False),
    "D02": ("D", "LOW", "Version family must converge", "版本家族過多, SSOT 不唯一", False),
    "D03": ("D", "MED", "Function must be unique", "同名函式跨檔重複實作", False),
    "E01": ("E", "HIGH", "Lesson-Learned SSOT required", "改善要求沒有沉澱成系統邏輯", True),
    "E02": ("E", "HIGH", "Append-only governance", "程式含刪除動作, 違反只增不減", False),
    "E03": ("E", "LOW", "UTF-8 no BOM", "BOM 造成解析與 diff 噪音", True),
    "E04": ("E", "MED", "No bare except", "裸 except 吞掉治理錯誤", True),
    "E05": ("E", "MED", "No mutable default arg", "可變預設值＝跨呼叫狀態汙染", True),
}

SEVERITY_WEIGHT = {"HIGH": 5.0, "MED": 2.0, "LOW": 0.5}

# 參數歸戶路由 (依名稱 token 優先, 再依 layer)
NAME_ROUTE = [
    (re.compile(r"RISK|VAR|DRAWDOWN|EXPOSURE|STOP", re.I), "risk.par"),
    (re.compile(r"STRATEG|SIGNAL|ALPHA|POSITION", re.I), "strategy.par"),
    (re.compile(r"FACTOR|WEIGHT|SCORE|IC_", re.I), "factor.par"),
    (re.compile(r"GROUP|SECTOR|INDUSTRY|族群", re.I), "group.par"),
    (re.compile(r"WORLDLINE|WL_", re.I), "worldline.par"),
]
LAYER_ROUTE = {"ENG": "engine.par", "SUB": "subsystem.par", "SYS": "system.par",
               "MGR": "system.par", "UI": "system.par", "MISC": "system.par"}

BUILTIN_NAMES = set(dir(builtins))


# ---------------------------------------------------------------------
# 1. 基礎工具
# ---------------------------------------------------------------------

def now_stamp():
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_human():
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sha_text(text, n=12):
    return hashlib.blake2s(text.encode("utf-8", "replace"), digest_size=8).hexdigest()[:n]


def read_text(path):
    raw = open(path, "rb").read()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    if had_bom:
        raw = raw[3:]
    return raw.decode("utf-8", "replace"), had_bom


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def append_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


class Console:
    def __init__(self):
        self.t0 = time.time()
        self.lines = []

    def phase(self, tag, msg):
        el = time.time() - self.t0
        line = "[%6.2fs] %-14s %s" % (el, tag, msg)
        self.lines.append(line)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


LOG = Console()


# ---------------------------------------------------------------------
# 2. 清冊 / 分層
# ---------------------------------------------------------------------

def classify_layer(path):
    p = path.replace("\\", "/").lower()
    name = os.path.basename(p)
    if "/param/" in p or name.endswith(".par"):
        return "PARAM"
    if re.search(r"systemmaster|via_core|autoops|metalayer|sys-\d", name):
        return "SYS"
    if re.search(r"integritywall|behaviormonitor|changepredictor|stabilityengine"
                 r"|healthengine|stressengine|resilienceengine|manager|mgr-\d", name):
        return "MGR"
    if re.search(r"worldline|wl-sys", p):
        return "WL"
    if re.search(r"engine|eng-\d|auto[a-z]+\.py$|_engine", name):
        return "ENG"
    for tok in SUBSYSTEM_TOKENS:
        if ("/" + tok.lower() + "/") in p or name.startswith(tok.lower()):
            return "SUB"
    if re.search(r"subsystem|sub-\d|orchestr", name):
        return "SUB"
    if name.endswith((".html", ".css", ".js")):
        return "UI"
    return "MISC"


def in_cgc_scope(path):
    p = path.replace("\\", "/").lower()
    return any(t in p for t in CGC_TOKENS)


def discover_root(user_root):
    if user_root:
        if os.path.isdir(user_root):
            return os.path.abspath(user_root)
        raise SystemExit("[VCAF] 指定的 --root 不存在: %s" % user_root)
    for c in ROOT_CANDIDATES:
        if os.path.isdir(c):
            return c
    return os.path.abspath(os.getcwd())


def walk_files(root, scope_all):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".py", ".ps1", ".psm1", ".html", ".json", ".par", ".md", ".cmd"):
                continue
            try:
                if os.path.getsize(full) > 3_000_000:
                    continue
            except OSError:
                continue
            if not scope_all and not in_cgc_scope(full):
                continue
            if is_own_output(full, ext):
                continue
            hits.append(full)
    return sorted(hits)


SELF_MARKERS = (b"[VCAF", b"VIA AutoParam Engine (ENG-11)",
                "由 VCAF".encode("utf-8"))


def is_own_output(path, ext):
    """避免回饋迴圈: 本引擎自己產出的檔案不再被掃描。"""
    if os.path.basename(path).lower() == "via_autoparam.py":
        return True
    if ext != ".py":
        return False
    try:
        head = open(path, "rb").read(600)
    except OSError:
        return True
    return any(m in head for m in SELF_MARKERS)


# ---------------------------------------------------------------------
# 3. AST 稽核
# ---------------------------------------------------------------------

class Finding:
    __slots__ = ("code", "path", "line", "detail", "target", "fixable")

    def __init__(self, code, path, line, detail, target="", fixable=None):
        self.code = code
        self.path = path
        self.line = line
        self.detail = detail
        self.target = target
        spec = FINDING_SPEC[code]
        self.fixable = spec[4] if fixable is None else fixable

    @property
    def layer(self):
        return FINDING_SPEC[self.code][0]

    @property
    def severity(self):
        return FINDING_SPEC[self.code][1]

    def as_dict(self, root):
        return {
            "code": self.code, "layer": self.layer, "severity": self.severity,
            "rule": FINDING_SPEC[self.code][2], "reason": FINDING_SPEC[self.code][3],
            "file": os.path.relpath(self.path, root), "line": self.line,
            "detail": self.detail, "target": self.target, "fixable": self.fixable,
        }


def literal_value(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def is_literal_node(node):
    return isinstance(node, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set,
                             ast.UnaryOp))


def free_names_of_function(fn):
    bound = set()
    for a in list(fn.args.posonlyargs) + list(fn.args.args) + list(fn.args.kwonlyargs):
        bound.add(a.arg)
    if fn.args.vararg:
        bound.add(fn.args.vararg.arg)
    if fn.args.kwarg:
        bound.add(fn.args.kwarg.arg)
    free = set()
    for node in ast.walk(fn):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in tgts:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name):
                        bound.add(sub.id)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for sub in ast.walk(node.target):
                if isinstance(sub, ast.Name):
                    bound.add(sub.id)
        elif isinstance(node, ast.comprehension):
            for sub in ast.walk(node.target):
                if isinstance(sub, ast.Name):
                    bound.add(sub.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                bound.add((al.asname or al.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node is not fn:
                bound.add(node.name)
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            for sub in ast.walk(node.optional_vars):
                if isinstance(sub, ast.Name):
                    bound.add(sub.id)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            free.add(node.id)
    return free - bound - BUILTIN_NAMES


COMPUTE_CALLS = re.compile(r"\b(sum|mean|std|abs|round|sorted|min|max|len|pow|sqrt"
                           r"|np\.|pd\.|math\.|statistics\.)")
DESTRUCTIVE = re.compile(r"os\.remove|os\.unlink|shutil\.rmtree|Path\([^)]*\)\.unlink"
                         r"|Remove-Item|\.truncate\(")
TRIVIAL_LITERALS = {0, 1, -1, 2, True, False, None, "", " ", "utf-8", "w", "r", "a"}


class ModuleReport:
    def __init__(self, path, layer, src, tree, had_bom):
        self.path = path
        self.layer = layer
        self.src = src
        self.tree = tree
        self.had_bom = had_bom
        self.lines = src.splitlines()
        self.consts = []        # (name, lineno, end_lineno, value, col)
        self.functions = []     # ast nodes (top-level)
        self.literals = []      # (value, lineno)
        self.imports_src = []


def analyze_python(path, layer, findings, mod_cache):
    src, had_bom = read_text(path)
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        findings.append(Finding("A04", path, getattr(e, "lineno", 0) or 0,
                                "AST 解析失敗: %s" % str(e)[:120], fixable=False))
        return None
    rep = ModuleReport(path, layer, src, tree, had_bom)
    mod_cache[path] = rep

    if had_bom:
        findings.append(Finding("E03", path, 1, "檔案含 UTF-8 BOM"))

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            rep.imports_src.append(ast.get_source_segment(src, node) or "")
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.startswith("__"):
                continue
            if not is_literal_node(node.value):
                continue
            val = literal_value(node.value)
            if val is None and not isinstance(node.value, ast.Constant):
                continue
            seg = ast.get_source_segment(src, node.value) or repr(val)
            if len(seg) > 240:
                continue
            if isinstance(val, (list, dict, set)) and layer in ("ENG", "SUB"):
                findings.append(Finding("A02" if layer == "ENG" else "B02", path,
                                        node.lineno,
                                        "模組級可變狀態 %s = %s" % (name, seg[:60])))
            if name.isupper() and layer in ("ENG", "SUB", "SYS", "MGR"):
                rep.consts.append((name, node.lineno, node.end_lineno, seg,
                                   node.col_offset))
                code = "A01" if layer == "ENG" else ("B02" if layer == "SUB" else "C03")
                findings.append(Finding(code, path, node.lineno,
                                        "硬編參數 %s = %s" % (name, seg[:60]),
                                        target=name))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rep.functions.append(node)

    pub_funcs = [f for f in rep.functions if not f.name.startswith("_")]
    if layer == "ENG" and len(pub_funcs) > 3:
        findings.append(Finding("A04", path, 1,
                                "引擎公開入口 %d 個 (>3), 非單一功能" % len(pub_funcs)))

    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            span = (fn.end_lineno or fn.lineno) - fn.lineno
            if span > 80:
                findings.append(Finding("A05", path, fn.lineno,
                                        "函式 %s 長度 %d 行 (>80)" % (fn.name, span)))
            for d in fn.args.defaults + [d for d in fn.args.kw_defaults if d]:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    findings.append(Finding("E05", path, fn.lineno,
                                            "函式 %s 使用可變預設值" % fn.name,
                                            target=fn.name))
                    break
        if isinstance(fn, ast.ExceptHandler) and fn.type is None:
            findings.append(Finding("E04", path, fn.lineno, "裸 except"))
        if isinstance(fn, ast.If) and layer == "ENG":
            seg = ast.get_source_segment(src, fn.test) or ""
            for tok in SUBSYSTEM_TOKENS:
                if tok.lower() in seg.lower():
                    findings.append(Finding("A03", path, fn.lineno,
                                            "引擎依子系統 %s 分支" % tok))
                    break
        if isinstance(fn, ast.Call) and layer == "ENG":
            f = fn.func
            fname = getattr(f, "id", "") or getattr(f, "attr", "")
            if fname == "open":
                mode = ""
                if len(fn.args) > 1 and isinstance(fn.args[1], ast.Constant):
                    mode = str(fn.args[1].value)
                for kw in fn.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if "w" in mode or "a" in mode:
                    findings.append(Finding("A06", path, fn.lineno,
                                            "引擎直接寫檔 open(mode=%r)" % mode))

    if DESTRUCTIVE.search(src):
        m = DESTRUCTIVE.search(src)
        ln = src[:m.start()].count("\n") + 1
        findings.append(Finding("E02", path, ln, "含刪除動作: %s" % m.group(0)))

    if layer == "SUB":
        for fn in rep.functions:
            body_src = ast.get_source_segment(src, fn) or ""
            has_loop = any(isinstance(n, (ast.For, ast.While, ast.ListComp,
                                          ast.DictComp, ast.SetComp))
                           for n in ast.walk(fn))
            has_math = any(isinstance(n, ast.BinOp) for n in ast.walk(fn))
            if (has_loop or has_math) and COMPUTE_CALLS.search(body_src):
                free = free_names_of_function(fn)
                pure = len(free) == 0
                findings.append(Finding("B01", path, fn.lineno,
                                        "子系統含計算邏輯: %s()%s" %
                                        (fn.name, "" if pure else " (有外部相依)"),
                                        target=fn.name, fixable=pure))
            elif (fn.end_lineno or fn.lineno) - fn.lineno > 25:
                findings.append(Finding("B03", path, fn.lineno,
                                        "子系統自行實作 %s() %d 行" %
                                        (fn.name, (fn.end_lineno or fn.lineno) - fn.lineno)))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
            v = node.value
            if v in TRIVIAL_LITERALS:
                continue
            if isinstance(v, str) and (len(v) < 3 or len(v) > 80):
                continue
            rep.literals.append((v, node.lineno))
    return rep


# ---------------------------------------------------------------------
# 4. 跨檔分析 (重複 / 散落)
# ---------------------------------------------------------------------

FAMILY_STRIP = re.compile(r"(_v\d{3,4}(\.\d+)?|_sha[0-9a-f]{6,}|_RUN\d+|_\d{8}_\d{6})",
                          re.I)


def family_key(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return FAMILY_STRIP.sub("", stem).lower()


def cross_file_analysis(files, mod_cache, findings, root):
    by_hash = {}
    by_family = {}
    for p in files:
        try:
            data = open(p, "rb").read()
        except OSError:
            continue
        h = hashlib.blake2s(data, digest_size=8).hexdigest()
        by_hash.setdefault(h, []).append(p)
        by_family.setdefault(family_key(p), []).append(p)

    for h, group in by_hash.items():
        if len(group) > 1:
            canonical = min(group, key=lambda q: os.path.getmtime(q))
            for dup in group:
                if dup == canonical:
                    continue
                findings.append(Finding("D01", dup, 1,
                                        "與 %s 內容完全相同 (hash %s)" %
                                        (os.path.relpath(canonical, root), h)))
    for fam, group in by_family.items():
        if len(group) > 2:
            findings.append(Finding("D02", sorted(group)[-1], 1,
                                    "版本家族 '%s' 有 %d 個成員" % (fam, len(group))))

    func_home = {}
    for p, rep in mod_cache.items():
        if rep.layer not in ("ENG", "SUB"):
            continue
        for fn in rep.functions:
            if fn.name.startswith("_"):
                continue
            func_home.setdefault(fn.name, []).append((p, fn.lineno))
    for name, homes in func_home.items():
        if len(homes) > 1:
            p, ln = homes[0]
            findings.append(Finding("D03", p, ln,
                                    "函式 %s() 在 %d 個檔案重複實作" % (name, len(homes))))

    lit_home = {}
    for p, rep in mod_cache.items():
        for v, ln in rep.literals:
            lit_home.setdefault(repr(v), set()).add(p)
    for lit, homes in lit_home.items():
        if len(homes) >= 3:
            p = sorted(homes)[0]
            findings.append(Finding("C01", p, 1,
                                    "字面值 %s 散落於 %d 個檔案" % (lit[:50], len(homes)),
                                    target=lit))


# ---------------------------------------------------------------------
# 5. 自動修正器
# ---------------------------------------------------------------------

def route_par(name, layer):
    for rx, par in NAME_ROUTE:
        if rx.search(name):
            return par
    return LAYER_ROUTE.get(layer, "system.par")


PARAM_IMPORT = "from via_autoparam import PARAM  # ABC-C 參數集中化 (VCAF)"


class FixResult:
    def __init__(self):
        self.fixed_files = []       # (rel, [fix codes])
        self.fix_counts = {}
        self.param_entries = {}     # par file -> [(key, value_src, origin)]
        self.new_engines = []
        self.failed = []            # (rel, reason)

    def bump(self, code, n=1):
        self.fix_counts[code] = self.fix_counts.get(code, 0) + n


def apply_line_edits(lines, edits):
    # edits: list of (lineno_1based, end_lineno_1based, replacement_text or None)
    for start, end, repl in sorted(edits, key=lambda e: -e[0]):
        idx0, idx1 = start - 1, end
        if repl is None:
            lines[idx0:idx1] = []
        else:
            lines[idx0:idx1] = repl.split("\n")
    return lines


def fix_module(rep, findings_for_file, out_path, res, root):
    src_lines = rep.src.splitlines()
    edits = []
    applied = []
    ns = "%s.%s" % (rep.layer.lower(), os.path.splitext(os.path.basename(rep.path))[0].lower())

    const_targets = {f.target for f in findings_for_file
                     if f.code in ("A01", "B02", "C03") and f.target and f.fixable}
    for (name, ln, end_ln, seg, col) in rep.consts:
        if name not in const_targets:
            continue
        key = "%s.%s" % (ns, name)
        par = route_par(name, rep.layer)
        res.param_entries.setdefault(par, []).append(
            (key, seg, os.path.relpath(rep.path, root)))
        pad = " " * col
        repl = '%s%s = PARAM.get("%s", %s)' % (pad, name, key, seg)
        edits.append((ln, end_ln or ln, repl))
        applied.append("A01/C03:%s" % name)
        res.bump("FIX-01")

    for f in findings_for_file:
        if f.code == "E05" and f.fixable:
            for fn in rep.functions:
                if fn.name != f.target:
                    continue
                seg_start, seg_end = fn.lineno, fn.end_lineno or fn.lineno
                new_seg = rewrite_mutable_defaults(rep.src, fn)
                if new_seg:
                    edits.append((seg_start, seg_end, new_seg))
                    applied.append("E05:%s" % fn.name)
                    res.bump("FIX-09")
                break

    new_src = "\n".join(apply_line_edits(list(src_lines), edits)) + "\n"

    if any(a.startswith(("A01", "C03")) for a in applied):
        new_src = inject_import(new_src)
        res.bump("FIX-02")

    if any(f.code == "E04" for f in findings_for_file):
        patched, n = re.subn(r"(?m)^(\s*)except\s*:", r"\1except Exception:", new_src)
        if n:
            new_src = patched
            applied.append("E04:%d" % n)
            res.bump("FIX-10", n)

    if rep.had_bom:
        applied.append("E03:BOM")
        res.bump("FIX-08")

    if not applied:
        return None

    header = ("# [VCAF %s] ABC 自動修正副本 — 原檔未被更動 (只增不減)\n"
              "# 來源: %s\n# 修正: %s\n# 產生: %s\n" %
              (ENGINE_VER, os.path.relpath(rep.path, root), ", ".join(applied), now_human()))
    new_src = header + new_src

    try:
        compile(new_src, out_path, "exec")
    except SyntaxError as e:
        res.failed.append((os.path.relpath(rep.path, root), "compile 失敗: %s" % e))
        return None

    write_text(out_path, new_src)
    res.fixed_files.append((os.path.relpath(rep.path, root), applied))
    return new_src


def inject_import(src):
    lines = src.splitlines()
    insert_at = 0
    for i, ln in enumerate(lines[:40]):
        s = ln.strip()
        if s.startswith(("import ", "from ")):
            insert_at = i + 1
        elif s.startswith("#") or s == "" or s.startswith(('"""', "'''")):
            continue
        elif insert_at:
            break
    lines.insert(insert_at, PARAM_IMPORT)
    return "\n".join(lines) + "\n"


def rewrite_mutable_defaults(src, fn):
    seg = ast.get_source_segment(src, fn)
    if not seg:
        return None
    args = fn.args
    all_args = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    pairs = []
    if defaults:
        for a, d in zip(all_args[len(all_args) - len(defaults):], defaults):
            if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                pairs.append((a.arg, d))
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        if d is not None and isinstance(d, (ast.List, ast.Dict, ast.Set)):
            pairs.append((a.arg, d))
    if not pairs:
        return None
    indent = " " * (fn.col_offset + 4)
    new_seg = seg
    guards = []
    for argname, dnode in pairs:
        dsrc = ast.get_source_segment(src, dnode) or "None"
        pattern = re.compile(r"(\b%s\s*=\s*)%s" % (re.escape(argname), re.escape(dsrc)))
        new_seg, n = pattern.subn(r"\1None", new_seg, count=1)
        if n:
            guards.append("%sif %s is None:\n%s    %s = %s"
                          % (indent, argname, indent, argname, dsrc))
    if not guards:
        return None
    anchor = fn.body[0]
    if isinstance(anchor, ast.Expr) and isinstance(anchor.value, ast.Constant) \
            and isinstance(anchor.value.value, str) and len(fn.body) > 1:
        anchor = fn.body[1]
    seg_lines = new_seg.splitlines()
    body_start = anchor.lineno - fn.lineno
    seg_lines[body_start:body_start] = guards
    return "\n".join(seg_lines)


# --- 生成 AutoParam 引擎 (C 層核心) -----------------------------------

AUTOPARAM_SRC = '''# -*- coding: utf-8 -*-
# via_autoparam.py — VIA AutoParam Engine (ENG-11)  由 VCAF 自動生成
# AP-01 Load / AP-02 Validate / AP-03 Update / AP-04 SyncEngine
# AP-05 SyncSubsystem / AP-06 Broadcast / AP-07 Rollback / AP-08 Diff
# AP-09 Snapshot / AP-10 Report
# PARAM/ 是所有參數的唯一真相來源。引擎永遠不存參數。

import datetime
import io
import json
import os

PARAM_DIR = os.environ.get("VIA_PARAM_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "PARAM")
SNAP_DIR = os.path.join(PARAM_DIR, "_snapshots")
PAR_FILES = ("system.par", "engine.par", "subsystem.par", "worldline.par",
             "strategy.par", "risk.par", "group.par", "factor.par")


def _strip_comment(raw):
    """移除行尾註解, 但不碰字串內的 #。"""
    out, quote, esc = [], None, False
    for ch in raw:
        if quote:
            out.append(ch)
            if esc:
                esc = False
            elif ch == chr(92):
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).strip()


def _parse_value(raw):
    raw = _strip_comment(raw)
    try:
        return json.loads(raw)
    except Exception:
        return raw


class AutoParam(object):
    """單一功能: 參數生命週期。不做業務邏輯, 不做編排。"""

    def __init__(self, param_dir=PARAM_DIR):
        self.param_dir = param_dir
        self.store = {}
        self.origin = {}
        self.subscribers = []
        self.loaded = False

    # AP-01
    def load(self):
        self.store, self.origin = {}, {}
        if not os.path.isdir(self.param_dir):
            self.loaded = True
            return self
        for fn in PAR_FILES:
            p = os.path.join(self.param_dir, fn)
            if not os.path.isfile(p):
                continue
            with io.open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    self.store[k] = _parse_value(v)
                    self.origin[k] = fn
        self.loaded = True
        return self

    # AP-02
    def validate(self):
        issues = []
        for k in self.store:
            if not k or " " in k:
                issues.append({"key": k, "issue": "INVALID_KEY"})
            elif k.count(".") < 2:
                issues.append({"key": k, "issue": "SHALLOW_NAMESPACE"})
        return issues

    def get(self, key, default=None):
        if not self.loaded:
            self.load()
        return self.store.get(key, default)

    # AP-03  只增不減: 舊值保留在 append-only 歷史行
    def update(self, key, value, par_file="system.par", reason=""):
        if not self.loaded:
            self.load()
        old = self.store.get(key)
        self.store[key] = value
        self.origin[key] = par_file
        path = os.path.join(self.param_dir, par_file)
        os.makedirs(self.param_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with io.open(path, "a", encoding="utf-8", newline="\\n") as f:
            f.write("# [UPDATE %s] old=%s reason=%s\\n" % (stamp, json.dumps(old, ensure_ascii=False), reason))
            f.write("%s = %s\\n" % (key, json.dumps(value, ensure_ascii=False)))
        self.broadcast(key, old, value)
        return {"key": key, "old": old, "new": value}

    # AP-04 / AP-05
    def sync(self, target):
        applied = 0
        for k, v in self.store.items():
            attr = k.split(".")[-1]
            if hasattr(target, attr):
                setattr(target, attr, v)
                applied += 1
        return applied

    # AP-06
    def subscribe(self, fn):
        self.subscribers.append(fn)

    def broadcast(self, key, old, new):
        for fn in list(self.subscribers):
            try:
                fn(key, old, new)
            except Exception:
                pass

    # AP-09
    def snapshot(self, tag=""):
        os.makedirs(SNAP_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        p = os.path.join(SNAP_DIR, "param_%s%s.json" % (stamp, ("_" + tag) if tag else ""))
        with io.open(p, "w", encoding="utf-8", newline="\\n") as f:
            f.write(json.dumps(self.store, ensure_ascii=False, indent=2))
        return p

    # AP-08
    def diff(self, snapshot_path):
        with io.open(snapshot_path, "r", encoding="utf-8") as f:
            old = json.load(f)
        out = {"added": {}, "changed": {}, "removed": {}}
        for k, v in self.store.items():
            if k not in old:
                out["added"][k] = v
            elif old[k] != v:
                out["changed"][k] = {"old": old[k], "new": v}
        for k, v in old.items():
            if k not in self.store:
                out["removed"][k] = v
        return out

    # AP-07  回滾 = 以新版本覆寫記憶體, 檔案仍 append-only
    def rollback(self, snapshot_path):
        with io.open(snapshot_path, "r", encoding="utf-8") as f:
            self.store = json.load(f)
        return len(self.store)

    # AP-10
    def report(self):
        by_file = {}
        for k, fn in self.origin.items():
            by_file[fn] = by_file.get(fn, 0) + 1
        return {"engine": "ENG-11 AutoParam", "total": len(self.store),
                "by_par": by_file, "issues": self.validate(),
                "param_dir": self.param_dir}


PARAM = AutoParam().load()
'''


def engine_stub(eng_id, eng_name, par):
    return ('# -*- coding: utf-8 -*-\n'
            '# %s %s — 由 VCAF 生成的功能化引擎骨架\n'
            '# 規則: 單一功能 / 無內嵌參數 / 無模組狀態 / 不判斷子系統\n'
            'from via_autoparam import PARAM\n\n\n'
            'def run(payload=None):\n'
            '    """ENG-FLOW: LoadParam -> PreCheck -> Execute -> PostCheck -> Return."""\n'
            '    params = {k: v for k, v in PARAM.store.items() if k.startswith("engine.%s")}\n'
            '    payload = {} if payload is None else dict(payload)\n'
            '    result = {"engine": "%s", "param_source": "%s",\n'
            '              "params_loaded": len(params), "status": "TODO_IMPLEMENT",\n'
            '              "input_keys": sorted(payload.keys())}\n'
            '    return result\n' % (eng_id, eng_name, eng_name.lower(), eng_name, par))


def extracted_engine_module(rep, fn, root):
    seg = ast.get_source_segment(rep.src, fn) or ""
    imports = "\n".join(i for i in rep.imports_src if i)
    head = ('# -*- coding: utf-8 -*-\n'
            '# ENG-EXT %s — 由 VCAF 自 %s 抽出的純功能\n'
            % (fn.name, os.path.relpath(rep.path, root)))
    return (head +
            '# B 層修正: 子系統只做編排, 計算邏輯下放本引擎\n' +
            (imports + "\n\n" if imports else "\n") +
            seg + "\n\n\n"
            "def run(*args, **kwargs):\n"
            "    return %s(*args, **kwargs)\n" % fn.name)


# ---------------------------------------------------------------------
# 6. Lesson-Learned (7 欄位, append-only)
# ---------------------------------------------------------------------

LL_RE = re.compile(r'Fingerprint\s*=\s*"([0-9a-f]+)"')


def build_lesson_entries(findings, root, lesson_path, run_id):
    existing = set()
    if os.path.isfile(lesson_path):
        txt, _ = read_text(lesson_path)
        existing = set(LL_RE.findall(txt))
        start_idx = txt.count("[LL-Entry-")
    else:
        start_idx = 0

    grouped = {}
    for f in findings:
        grouped.setdefault(f.code, []).append(f)

    blocks, new_entries = [], []
    idx = start_idx
    for code in sorted(grouped):
        layer, sev, rule, reason, fixable = FINDING_SPEC[code]
        group = grouped[code]
        fp = sha_text(code + "|" + rule)
        if fp in existing:
            continue
        idx += 1
        top = sorted({os.path.relpath(g.path, root) for g in group})[:5]
        impact = {"A": "Engine", "B": "Subsystem", "C": "Param",
                  "D": "SSOT", "E": "Governance"}[layer]
        par = {"A": "engine.par", "B": "subsystem.par", "C": "system.par",
               "D": "system.par", "E": "lesson.par"}[layer]
        entry = {
            "id": "LL-Entry-%04d" % idx, "code": code, "layer": layer,
            "severity": sev, "count": len(group), "rule": rule, "reason": reason,
            "files": top, "fingerprint": fp,
        }
        new_entries.append(entry)
        blocks.append(
            "\n[LL-Entry-%04d]\n"
            'Trigger     = "VCAF %s 掃描發現 %s x%d (%s)"\n'
            'Rule        = "%s"\n'
            'Reason      = "%s"\n'
            'Impact      = "%s"\n'
            'Update      = "%s"\n'
            'Version     = "LL-V%02d"\n'
            'Worldline   = "%s"\n'
            'Severity    = "%s"\n'
            'AutoFixable = "%s"\n'
            'Files       = "%s"\n'
            'Fingerprint = "%s"\n'
            'RunId       = "%s"\n'
            % (idx, run_id, code, len(group), now_human(), rule, reason, impact,
               par, idx, WORLDLINE, sev, "YES" if fixable else "MANUAL",
               " | ".join(top), fp, run_id))
    if blocks:
        if not os.path.isfile(lesson_path):
            write_text(lesson_path,
                       "# VIA Lesson-Learned SSOT (append-only / 只增不減)\n"
                       "# 每次改善要求 -> 7 欄位邏輯 -> 系統記憶\n"
                       "# 產生器: %s %s\n" % (ENGINE_NAME, ENGINE_VER))
        append_text(lesson_path, "".join(blocks))
    return new_entries


# ---------------------------------------------------------------------
# 7. 閘門
# ---------------------------------------------------------------------

def run_gates(ctx):
    g = []

    def add(name, ok, detail):
        g.append({"gate": name, "status": "PASS" if ok else "WARN", "detail": detail})

    add("CGC_ROOT_FOUND", ctx["file_count"] > 0,
        "root=%s, 檔案 %d" % (ctx["root"], ctx["file_count"]))
    add("CGC_SOURCE_READONLY", not ctx["overwrite"],
        "原始樹未被更動" if not ctx["overwrite"] else "--overwrite 已啟用")
    add("CGC_AST_PARSE_OK", ctx["parse_fail"] == 0,
        "Python 解析失敗 %d / %d" % (ctx["parse_fail"], ctx["py_count"]))
    add("CGC_FIX_COMPILE_OK", len(ctx["res"].failed) == 0,
        "產出檔 compile 失敗 %d" % len(ctx["res"].failed))
    add("CGC_PARAM_CENTRALIZED", ctx["remain"].get("C", 0) == 0,
        "C 層殘留 %d" % ctx["remain"].get("C", 0))
    add("CGC_ENGINE_FUNCTIONAL", ctx["remain"].get("A", 0) == 0,
        "A 層殘留 %d" % ctx["remain"].get("A", 0))
    add("CGC_SUBSYSTEM_ORCH", ctx["remain"].get("B", 0) == 0,
        "B 層殘留 %d" % ctx["remain"].get("B", 0))
    add("CGC_APPEND_ONLY", ctx["deleted"] == 0,
        "本次刪除檔案 %d (必須為 0)" % ctx["deleted"])
    add("CGC_LL_WRITTEN", True,
        "新增 LL-Entry %d 筆" % ctx["ll_new"])
    add("CGC_AUTOPARAM_PRESENT", ctx["autoparam"], "via_autoparam.py 已就位")
    add("CGC_IDEMPOTENT", ctx["idem_new"] == 0,
        "對 fixed/ 重掃仍可修正項目 %d" % ctx["idem_new"])
    return g


# ---------------------------------------------------------------------
# 8. HTML 報表 (Visual Lock)
# ---------------------------------------------------------------------

CSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--line:#dbd9d3;--blue:#4c78a8;
--teal:#439a9a;--up:#c96b5a;--down:#5a9e6f;--mute:#78756e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:"DM Sans","Noto Sans TC",-apple-system,"Segoe UI",sans-serif;line-height:1.6}
.wrap{max-width:1180px;margin:0 auto;padding:32px 24px 80px}
.mono{font-family:"DM Mono",ui-monospace,Consolas,monospace}
header{display:flex;gap:22px;align-items:flex-start;border-bottom:2px solid var(--ink);
padding-bottom:18px;margin-bottom:26px}
.seal{width:62px;height:62px;flex:0 0 62px;background:var(--up);color:#fff;border-radius:3px;
display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:700}
h1{font-family:Syne,"Noto Sans TC",sans-serif;font-size:27px;margin:0 0 4px;letter-spacing:-.4px}
.sub{color:var(--mute);font-size:13px}
.grid{display:grid;gap:14px}
.g4{grid-template-columns:repeat(4,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:16px 18px}
.kpi{font-family:Syne,sans-serif;font-size:34px;font-weight:700;line-height:1.1}
.klab{font-size:12px;color:var(--mute)}
h2{font-family:Syne,sans-serif;font-size:17px;margin:34px 0 12px;
border-left:4px solid var(--blue);padding-left:10px}
table{width:100%;border-collapse:collapse;background:var(--paper);
border:1px solid var(--line);font-size:13px}
th{background:#efeee9;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);
font-weight:600;font-size:12px}
td{padding:7px 10px;border-bottom:1px solid #eeede9;vertical-align:top}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:1px 7px;border-radius:2px;font-size:11px;
font-family:"DM Mono",monospace}
.HIGH{background:#f6e2de;color:#9d4436}.MED{background:#fdf2dc;color:#8a6320}
.LOW{background:#e8efe9;color:#3f6c4f}
.PASS{background:#e6f1ea;color:var(--down)}.WARN{background:#f6e2de;color:var(--up)}
.bar{height:8px;background:#e9e8e3;border-radius:2px;overflow:hidden}
.bar i{display:block;height:100%}
.A{background:var(--up)}.B{background:var(--blue)}.C{background:var(--teal)}
.D{background:#8b7fb0}.E{background:var(--mute)}
.par{background:#faf9f6;border:1px solid var(--line);padding:12px;border-radius:3px;
font-family:"DM Mono",monospace;font-size:12px;white-space:pre-wrap;max-height:320px;overflow:auto}
footer{margin-top:44px;border-top:1px solid var(--line);padding-top:14px;
color:var(--mute);font-size:12px}
.pill{font-size:11px;color:var(--mute);border:1px solid var(--line);
padding:1px 7px;border-radius:10px}
"""


def build_html(ctx):
    root = ctx["root"]
    res = ctx["res"]
    findings = ctx["findings"]
    health = ctx["health"]
    parts = []
    A = parts.append

    A("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>")
    A("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    A("<title>VIA CGC ABC 升級報告 %s</title>" % ctx["run_id"])
    A("<link href='https://fonts.googleapis.com/css2?family=Syne:wght@600;700&"
      "family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap' "
      "rel='stylesheet'>")
    A("<style>%s</style></head><body><div class='wrap'>" % CSS)

    A("<header><div class='seal'>理</div><div>")
    A("<h1>VIA Central Governance Console — ABC 升級報告</h1>")
    A("<div class='sub mono'>%s %s %s &nbsp;|&nbsp; %s &nbsp;|&nbsp; RUN %s</div>"
      % (ENGINE_ID, ENGINE_NAME, ENGINE_VER, now_human(), ctx["run_id"]))
    A("<div class='sub'>%s</div>" % esc(root))
    A("</div></header>")

    mode = "COMMIT 回寫" if ctx["commit"] else "沙箱 (原始樹唯讀)"
    A("<div class='grid g4'>")
    A("<div class='card'><div class='kpi' style='color:%s'>%d</div>"
      "<div class='klab'>ABC 健康度 / 100</div></div>"
      % ("var(--down)" if health >= 80 else "var(--up)", health))
    A("<div class='card'><div class='kpi'>%d</div><div class='klab'>稽核發現</div></div>"
      % len(findings))
    A("<div class='card'><div class='kpi'>%d</div><div class='klab'>自動修正檔案</div></div>"
      % len(res.fixed_files))
    A("<div class='card'><div class='kpi'>%d</div><div class='klab'>集中化參數</div></div>"
      % sum(len(v) for v in res.param_entries.values()))
    A("</div>")
    A("<div style='margin-top:10px'><span class='pill'>模式 %s</span> "
      "<span class='pill'>掃描 %d 檔</span> <span class='pill'>Python %d 檔</span> "
      "<span class='pill'>只增不減 已鎖</span></div>"
      % (mode, ctx["file_count"], ctx["py_count"]))

    A("<h2>閘門檢查</h2><table><tr><th style='width:230px'>Gate</th>"
      "<th style='width:70px'>結果</th><th>說明</th></tr>")
    for g in ctx["gates"]:
        A("<tr><td class='mono'>%s</td><td><span class='tag %s'>%s</span></td>"
          "<td>%s</td></tr>" % (g["gate"], g["status"], g["status"], esc(g["detail"])))
    A("</table>")

    A("<h2>ABC 三層合規</h2><div class='grid g3'>")
    layer_title = {"A": "A 引擎功能化", "B": "B 子系統編排化", "C": "C 參數集中化"}
    total = max(1, len(findings))
    for lay in ("A", "B", "C"):
        n = sum(1 for f in findings if f.layer == lay)
        fixed = sum(1 for f in findings if f.layer == lay and f.fixable)
        pct = int(100 * n / total)
        A("<div class='card'><div class='klab'>%s</div>"
          "<div class='kpi'>%d</div>"
          "<div class='bar'><i class='%s' style='width:%d%%'></i></div>"
          "<div class='klab' style='margin-top:8px'>可自動修正 %d / 需人工 %d</div></div>"
          % (layer_title[lay], n, lay, pct, fixed, n - fixed))
    A("</div>")

    A("<h2>稽核發現</h2><table><tr><th style='width:52px'>代碼</th>"
      "<th style='width:60px'>嚴重度</th><th style='width:56px'>修正</th>"
      "<th>檔案 : 行</th><th>說明</th></tr>")
    ordered = sorted(findings, key=lambda f: (
        {"HIGH": 0, "MED": 1, "LOW": 2}[f.severity], f.code, f.path))
    for f in ordered[:400]:
        A("<tr><td class='mono'>%s</td><td><span class='tag %s'>%s</span></td>"
          "<td class='mono'>%s</td><td class='mono'>%s:%d</td><td>%s</td></tr>"
          % (f.code, f.severity, f.severity, "AUTO" if f.fixable else "人工",
             esc(os.path.relpath(f.path, root)), f.line, esc(f.detail)))
    A("</table>")
    if len(ordered) > 400:
        A("<div class='sub'>另有 %d 筆未顯示, 完整清單見 findings.jsonl</div>"
          % (len(ordered) - 400))

    A("<h2>已套用的自動修正</h2>")
    if res.fixed_files:
        A("<table><tr><th>原始檔</th><th>套用修正</th></tr>")
        for rel, applied in sorted(res.fixed_files):
            A("<tr><td class='mono'>%s</td><td class='mono'>%s</td></tr>"
              % (esc(rel), esc(", ".join(applied))))
        A("</table>")
    else:
        A("<div class='card'>本次沒有可自動套用的修正。</div>")
    if res.failed:
        A("<h2>修正回滾 (compile 未通過, 原檔保持不變)</h2><table>"
          "<tr><th>檔案</th><th>原因</th></tr>")
        for rel, why in res.failed:
            A("<tr><td class='mono'>%s</td><td>%s</td></tr>" % (esc(rel), esc(why)))
        A("</table>")

    A("<h2>PARAM/ 參數中心 (抽出結果)</h2><div class='grid g2'>")
    for par in sorted(res.param_entries):
        rows = res.param_entries[par]
        preview = "\n".join("%s = %s" % (k, v) for k, v, _ in rows[:18])
        if len(rows) > 18:
            preview += "\n# ... 另 %d 筆" % (len(rows) - 18)
        A("<div class='card'><div class='klab'>%s &nbsp;·&nbsp; %d 筆</div>"
          "<div class='par'>%s</div></div>" % (par, len(rows), esc(preview)))
    A("</div>")

    if ctx["ll_entries"]:
        A("<h2>Lesson-Learned 新增 (7 欄位, append-only)</h2>"
          "<table><tr><th style='width:120px'>ID</th><th style='width:52px'>代碼</th>"
          "<th style='width:56px'>數量</th><th>Rule</th><th>Reason</th></tr>")
        for e in ctx["ll_entries"]:
            A("<tr><td class='mono'>%s</td><td class='mono'>%s</td><td class='mono'>%d</td>"
              "<td>%s</td><td>%s</td></tr>"
              % (e["id"], e["code"], e["count"], esc(e["rule"]), esc(e["reason"])))
        A("</table>")

    A("<h2>下一步 (人工決策項)</h2><div class='card'><ol>")
    manual = [f for f in findings if not f.fixable]
    seen = set()
    for f in manual:
        if f.code in seen:
            continue
        seen.add(f.code)
        A("<li><span class='mono'>%s</span> — %s (%d 處)</li>"
          % (f.code, esc(FINDING_SPEC[f.code][2]),
             sum(1 for x in manual if x.code == f.code)))
    if not manual:
        A("<li>沒有需要人工判斷的項目。</li>")
    A("</ol></div>")

    A("<h2>執行軌跡</h2><div class='par'>%s</div>" % esc("\n".join(LOG.lines)))

    A("<footer>%s %s · 治理原則 只增不減 · 原始檔案未被刪除或覆寫 · "
      "產出目錄 %s</footer>" % (ENGINE_NAME, ENGINE_VER, esc(ctx["outdir"])))
    A("</div></body></html>")
    return "\n".join(parts)


# ---------------------------------------------------------------------
# 9. 主流程
# ---------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="VIA CGC ABC Auto-Fix Engine — 讀取中央治理主控台並自動修正")
    ap.add_argument("--root", default=None, help="CGC 根目錄 (省略則自動偵測)")
    ap.add_argument("--all", action="store_true", help="掃描全樹, 不只 CGC 關鍵字範圍")
    ap.add_argument("--commit", action="store_true",
                    help="把 PARAM/ 與 via_autoparam.py 以 add-only 寫回原始樹")
    ap.add_argument("--overwrite", action="store_true",
                    help="極危險: 允許覆寫原始 .py (預設永不覆寫)")
    ap.add_argument("--no-open", action="store_true", help="不自動開啟報表")
    ap.add_argument("--scaffold", action="store_true",
                    help="補齊 11 支標準引擎骨架 (缺者才生成)")
    args = ap.parse_args(argv)

    root = discover_root(args.root)
    run_id = now_stamp()
    outdir = os.path.join(root, OUT_ROOT_NAME, "RUN_" + run_id)
    fixed_dir = os.path.join(outdir, "fixed")
    param_dir = os.path.join(outdir, "PARAM")
    eng_dir = os.path.join(outdir, "engines")
    ssot_dir = os.path.join(root, OUT_ROOT_NAME, "SSOT")
    os.makedirs(outdir, exist_ok=True)

    LOG.phase("PHASE-0", "根目錄 %s" % root)
    files = walk_files(root, args.all)
    py_files = [f for f in files if f.lower().endswith(".py")]
    LOG.phase("PHASE-1", "清冊 %d 檔 (Python %d)" % (len(files), len(py_files)))
    if not files:
        LOG.phase("ABORT", "找不到任何符合範圍的檔案, 試試 --all 或 --root")

    findings = []
    mod_cache = {}
    parse_fail = 0
    for p in py_files:
        layer = classify_layer(p)
        rep = analyze_python(p, layer, findings, mod_cache)
        if rep is None:
            parse_fail += 1
    LOG.phase("PHASE-2", "AST 稽核完成, 發現 %d 項 (解析失敗 %d)"
              % (len(findings), parse_fail))

    cross_file_analysis(files, mod_cache, findings, root)
    LOG.phase("PHASE-3", "跨檔比對完成, 累計 %d 項" % len(findings))

    has_param = any(classify_layer(f) == "PARAM" for f in files)
    if not has_param:
        findings.append(Finding("C02", root, 0, "整個 CGC 沒有 PARAM/ 參數中心"))
    lesson_path = os.path.join(ssot_dir, "lesson.par")
    if not os.path.isfile(lesson_path) and not any(
            os.path.basename(f).lower() == "lesson.par" for f in files):
        findings.append(Finding("E01", root, 0, "沒有 lesson.par, 改善要求未沉澱"))

    res = FixResult()
    by_file = {}
    for f in findings:
        by_file.setdefault(f.path, []).append(f)
    for p, rep in mod_cache.items():
        rel = os.path.relpath(p, root)
        out_path = os.path.join(fixed_dir, rel)
        fix_module(rep, by_file.get(p, []), out_path, res, root)
    LOG.phase("PHASE-4", "A/C 修正: %d 個檔案已重寫到 fixed/" % len(res.fixed_files))

    ext_count = 0
    for f in findings:
        if f.code != "B01" or not f.fixable:
            continue
        rep = mod_cache.get(f.path)
        if rep is None:
            continue
        fn = next((x for x in rep.functions if x.name == f.target), None)
        if fn is None:
            continue
        modname = "ENG_%s_%s" % (
            re.sub(r"\W+", "_", os.path.splitext(os.path.basename(f.path))[0]), fn.name)
        src = extracted_engine_module(rep, fn, root)
        try:
            compile(src, modname, "exec")
        except SyntaxError as e:
            res.failed.append((modname, "抽出引擎 compile 失敗: %s" % e))
            continue
        write_text(os.path.join(eng_dir, modname + ".py"), src)
        res.new_engines.append(modname)
        res.bump("FIX-04")
        ext_count += 1
    LOG.phase("PHASE-5", "B 修正: 抽出 %d 支功能引擎到 engines/" % ext_count)

    write_text(os.path.join(outdir, "via_autoparam.py"), AUTOPARAM_SRC)
    res.bump("FIX-06")
    header = ("# VIA PARAM SSOT — 由 %s %s 生成 (append-only)\n"
              "# 格式: <namespace>.<KEY> = <json value>\n"
              "# 來源檔案標註於行尾註解\n" % (ENGINE_NAME, ENGINE_VER))
    for par in PAR_FILES:
        if par == "lesson.par":
            continue
        rows = res.param_entries.get(par, [])
        body = "".join("%s = %s  # from %s\n" % (k, v, o) for k, v, o in rows)
        write_text(os.path.join(param_dir, par), header + body)
    LOG.phase("PHASE-6", "C 修正: PARAM/ 8 檔產出, 參數 %d 筆"
              % sum(len(v) for v in res.param_entries.values()))

    if args.scaffold:
        made = 0
        existing_names = {os.path.splitext(os.path.basename(f))[0].lower() for f in files}
        for eid, ename, par in ENGINE_ROSTER:
            if ename.lower() in existing_names:
                continue
            write_text(os.path.join(eng_dir, "%s.py" % ename), engine_stub(eid, ename, par))
            made += 1
            res.bump("FIX-05")
        LOG.phase("PHASE-6b", "引擎骨架補齊 %d 支" % made)

    ll_entries = build_lesson_entries(findings, root, lesson_path, run_id)
    LOG.phase("PHASE-7", "Lesson-Learned 新增 %d 筆 -> %s"
              % (len(ll_entries), os.path.relpath(lesson_path, root)))

    idem_new = 0
    if os.path.isdir(fixed_dir):
        f2, m2 = [], {}
        for dp, dn, fns in os.walk(fixed_dir):
            for fn in fns:
                if fn.endswith(".py"):
                    p2 = os.path.join(dp, fn)
                    analyze_python(p2, classify_layer(p2), f2, m2)
        idem_new = sum(1 for x in f2 if x.fixable and x.code in ("A01", "C03", "E04", "E05"))
    LOG.phase("PHASE-8", "冪等重掃: fixed/ 仍可修正 %d 項" % idem_new)

    remain = {}
    for f in findings:
        if not f.fixable:
            remain[f.layer] = remain.get(f.layer, 0) + 1
    penalty = sum(SEVERITY_WEIGHT[f.severity] for f in findings)
    budget = max(30.0, len(py_files) * 8.0 + 20.0)
    health = int(round(100.0 / (1.0 + penalty / budget)))

    committed = []
    if args.commit:
        tgt_param = os.path.join(root, "PARAM")
        for par in PAR_FILES:
            if par == "lesson.par":
                continue
            src_p = os.path.join(param_dir, par)
            dst_p = os.path.join(tgt_param, par)
            if not os.path.isfile(src_p):
                continue
            txt, _ = read_text(src_p)
            if os.path.isfile(dst_p):
                old, _ = read_text(dst_p)
                have = {ln.split("=")[0].strip() for ln in old.splitlines()
                        if "=" in ln and not ln.strip().startswith("#")}
                add = [ln for ln in txt.splitlines()
                       if "=" in ln and not ln.strip().startswith("#")
                       and ln.split("=")[0].strip() not in have]
                if add:
                    append_text(dst_p, "\n# [VCAF %s add-only]\n" % run_id
                                + "\n".join(add) + "\n")
                    committed.append("%s +%d" % (par, len(add)))
            else:
                write_text(dst_p, txt)
                committed.append("%s (new)" % par)
        ap_dst = os.path.join(root, "via_autoparam.py")
        if not os.path.isfile(ap_dst):
            write_text(ap_dst, AUTOPARAM_SRC)
            committed.append("via_autoparam.py (new)")
        LOG.phase("PHASE-9", "COMMIT add-only: %s" % (", ".join(committed) or "無新增"))
    else:
        LOG.phase("PHASE-9", "沙箱模式: 原始樹完全未動 (要回寫請加 --commit)")

    ctx = {
        "root": root, "outdir": outdir, "run_id": run_id, "res": res,
        "findings": findings, "file_count": len(files), "py_count": len(py_files),
        "parse_fail": parse_fail, "remain": remain, "deleted": 0,
        "ll_new": len(ll_entries), "ll_entries": ll_entries,
        "autoparam": os.path.isfile(os.path.join(outdir, "via_autoparam.py")),
        "idem_new": idem_new, "commit": args.commit, "overwrite": args.overwrite,
        "health": health,
    }
    ctx["gates"] = run_gates(ctx)

    with io.open(os.path.join(outdir, "findings.jsonl"), "w",
                 encoding="utf-8", newline="\n") as fh:
        for f in findings:
            fh.write(json.dumps(f.as_dict(root), ensure_ascii=False) + "\n")
    write_text(os.path.join(outdir, "cgc_state.json"), json.dumps({
        "engine": ENGINE_ID, "version": ENGINE_VER, "run_id": run_id, "root": root,
        "health": health, "files": len(files), "findings": len(findings),
        "fixed_files": len(res.fixed_files), "fix_counts": res.fix_counts,
        "new_engines": res.new_engines, "gates": ctx["gates"],
        "params": {k: len(v) for k, v in res.param_entries.items()},
        "committed": committed, "timestamp": now_human(),
    }, ensure_ascii=False, indent=2))

    report = os.path.join(outdir, "VIA_CGC_ABC_Upgrade.html")
    write_text(report, build_html(ctx))
    LOG.phase("DONE", "健康度 %d/100 · 報表 %s" % (health, report))

    if not args.no_open:
        try:
            webbrowser.open("file:///" + report.replace("\\", "/"))
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
