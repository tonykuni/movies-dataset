#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0162 — 薄尾(操作員 2026-10-10):via_02_vrn(VRN 分類快照)全景整理。
  curate [--to <夾>] [--apply] [--purge] [--no-fill]
    ① 全景掃描(省 token):每檔 sha · 族 · 版 · 角色;.py 做 AST 卡(說明字串 · 函式 / 類別 · 依賴 · 動詞 · 加速器 · 出網 · 自測 · 薄尾鏈);mtime+大小沒變沿用快取
    ② AST 分類 + 詳細說明:分類口徑借 VCGC RegistryGovernor 尾版 _CAT_RULES(入口 / 驗證 / 讀取 / 寫出 / 解析 / 清理 / 重建 / 介面 / 治理)
       → 側冊 VIA_AstAnnotations_VRN02_v####.json(不改原始碼;內容沒變不出新版)
    ③ 補不足:正本(functional modules\\VRN)→ 快照只補新的 / 有變的;薄尾鏈族帶整條;intake 管線(分類器 / TableRepair)尾版;子夾引擎;.ps1 尾版(08_scripts)
    ④ 去重唯一:完全相同 / 只差註解格式鍵序 / 副本檔名 / 舊版(尾版在)/ 子集舊冊 / 舊報表 → 退役;被 import 的舊版、薄尾鏈、帳(.jsonl)、主控鏈不退
       不同族函式名重疊 ≥60% → 列整合候選(人裁定,不自動合併)
    ⑤ 退役 = 搬 via_02_vrn\\_retired\\<時間>\\(原相對路徑,可整批還原)+ 帳 _curate\\VRN02_Curate_Ledger.jsonl;--purge 才真刪
    輸出:VRN02_INDEX_latest.json · VRN02_CARD_AI.md(AI 一族一行)· VRN02_CURATE_latest.html(燈 · 動作 · 角色 · AST 說明 · 理由)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0162"


def _vnum_v0162(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0162(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0162(p) < _vnum_v0162(__file__)), key=_vnum_v0162)
PRIOR = _load_v0162(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_home = _resolve("_home")
_rep = _resolve("_rep")

# ───────── 分類規則:借 VCGC RegistryGovernor 尾版的 _CAT_RULES(同一套口徑);找不到才用內建同款 ─────────
_CAT_FALLBACK = [
    ("ENTRY", r"^(main|cli|run|selftest|chk)$"), ("GATE", r"(?i)(check|validate|verify|gate|test|assert|guard|precheck|audit|triage)"),
    ("IO_READ", r"(?i)(read|load|fetch|get|scan|discover|find|glob|open|download|pull)"), ("IO_WRITE", r"(?i)(write|save|emit|export|dump|persist|ledger|append|publish|issue|register)"),
    ("PARSE", r"(?i)(parse|extract|split|tokeni|block|table|period|label|regex|match)"), ("CLEAN", r"(?i)(clean|normal|std|canon|strip|dedup|sanit|fix|repair)"),
    ("REBUILD", r"(?i)(rebuild|build|merge|assemble|compose|reconstruct|restatus|rebalance|aggregate|matrix)"), ("UI", r"(?i)(html|render|ui|print|show|display|card|pack|chart|plot)"),
    ("GOVERN", r"(?i)(number|govern|ssot|adopt|retire|dormant|law|policy|collision|supersede)"), ("INTERNAL", r"^_"),
]
_CAT_ZH = {"ENTRY": "入口", "GATE": "驗證", "IO_READ": "讀取", "IO_WRITE": "寫出", "PARSE": "解析", "CLEAN": "清理", "REBUILD": "重建", "UI": "介面", "GOVERN": "治理", "INTERNAL": "內部", "OTHER": "其他"}
_CR = {}
_SCANSTAT = {}


def cat_rules() -> tuple:
    if "rules" in _CR:
        return _CR["rules"], _CR["src"]
    rules, src = _CAT_FALLBACK, "內建(同 VCGC 口徑)"
    try:
        reg = _home().parents[1] / "supportive modules" / "registry"
        tails = sorted(reg.glob("CGC_MDL*_RegistryGovernor_v*.py"), key=lambda q: _vnum_v0162(q.stem))
        if tails:
            txt = tails[-1].read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^_CAT_RULES = (\[.*?\n\])", txt, re.S | re.M)
            if m:
                cand = ast.literal_eval(m.group(1))
                if cand and all(isinstance(x, tuple) and len(x) == 2 for x in cand):
                    rules, src = cand, "VCGC %s" % tails[-1].name
    except Exception:  # noqa: BLE001
        pass
    _CR.update(rules=rules, src=src)
    return rules, src


def _cat(name: str) -> str:
    short = name.split(".")[-1]
    for c, rx in cat_rules()[0]:
        if re.search(rx, short):
            return c
    return "OTHER"


# ───────── 族名 / 版號 / 副本標記 ─────────
_COPY_RX = re.compile(r"(?i)(\s*\(\d+\)|[-_ ](copy|複製|副本)(\s*\d+)?|_sha[0-9a-f]{6,}\w*)$")


def fam_ver(stem: str) -> tuple:
    copy = bool(_COPY_RX.search(stem))
    s = _COPY_RX.sub("", stem)
    m = re.search(r"[-_][vV](\d{4})$", s)
    if m:
        return s[:m.start()], int(m.group(1)), copy
    m = re.search(r"[-_][vV](\d+)(?:[._](\d+))?$", s)
    if m:
        return s[:m.start()], int(m.group(1)) * 100 + int(m.group(2) or 0), copy
    return s, -1, copy


_SYS_FILES = re.compile(r"^(VRN02_|VIA_AstAnnotations_VRN02|VRN_EXPORT_MANIFEST|README_VRN_SNAPSHOT)")
_SKIP_DIRS = {"_retired", "_curate", "__pycache__", ".git", ".venv", "node_modules"}
_ROLE_DIR = {"01_manager": "MANAGER", "02_engines": "ENGINE", "03_ssot": "SSOT", "04_registry": "REGISTRY", "05_rules": "RULE", "06_reports": "REPORT", "07_docs": "DOC", "08_scripts": "SCRIPT"}
_ROLE_ZH = {"MANAGER": "主控鏈", "ENGINE": "引擎", "SCRIPT": "PS 指令", "SSOT": "SSOT 冊", "REGISTRY": "登記冊", "RULE": "規則冊", "REPORT": "報表", "DOC": "文件", "LEDGER": "帳", "DATA": "資料", "OTHER": "其他"}
_ROLE_HOME = {v: k for k, v in _ROLE_DIR.items()}


def _role(rel: Path) -> str:
    top = rel.parts[0] if len(rel.parts) > 1 else ""
    ext = rel.suffix.lower()
    if ext == ".jsonl":
        return "LEDGER"
    if ext in (".md", ".txt") and top != "06_reports":
        return "DOC"
    r = _ROLE_DIR.get(top)
    if r == "ENGINE" and ext == ".ps1":
        return "SCRIPT"
    if r:
        return r
    return {".py": "ENGINE", ".ps1": "SCRIPT", ".json": "SSOT", ".csv": "DATA", ".parquet": "DATA", ".html": "REPORT", ".md": "DOC", ".txt": "DOC"}.get(ext, "OTHER")


# ───────── AST 卡 ─────────
def _strip_docs(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:] or [ast.Pass()]
    return tree


def py_card(txt: str) -> dict:
    c = {"ast_ok": True, "doc": "", "defs": [], "classes": [], "imports": [], "verbs": [], "cats": {}, "sem": "", "accel": "無", "net": False, "net_canon": False, "selftest": False, "chain": False, "lines": txt.count("\n") + 1}
    try:
        tree = ast.parse(txt)
    except SyntaxError as exc:
        c.update(ast_ok=False, err="SyntaxError L%s" % exc.lineno)
        return c
    c["doc"] = " ".join((ast.get_docstring(tree) or "").split())[:400]
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            c["defs"].append({"name": n.name, "args": [a.arg for a in n.args.args][:8], "doc": " ".join((ast.get_docstring(n) or "").split())[:120], "cat": _cat(n.name)})
        elif isinstance(n, ast.ClassDef):
            c["classes"].append({"name": n.name, "methods": sum(1 for x in n.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))), "doc": " ".join((ast.get_docstring(n) or "").split())[:120]})
    imps = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imps.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imps.add(n.module.split(".")[0])
    c["imports"] = sorted(imps)
    verbs = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.comparators) == 1:
            left = ast.unparse(n.left) if hasattr(ast, "unparse") else ""
            if re.search(r"(?i)(verb|cmd|args\[:?[01]\]|argv\[1\]|a\.verb)", left):
                comp = n.comparators[0]
                vals = [comp] if isinstance(comp, ast.Constant) else (list(comp.elts) if isinstance(comp, (ast.List, ast.Tuple, ast.Set)) else [])
                for v in vals:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str) and re.fullmatch(r"[a-z][\w-]{1,24}", v.value):
                        verbs.add(v.value)
                    elif isinstance(v, (ast.List, ast.Tuple)):
                        for w in v.elts:
                            if isinstance(w, ast.Constant) and isinstance(w.value, str) and re.fullmatch(r"[a-z][\w-]{1,24}", w.value):
                                verbs.add(w.value)
    c["verbs"] = sorted(verbs)[:24]
    c["cats"] = dict(Counter(d["cat"] for d in c["defs"]))
    c["sem"] = hashlib.sha256(ast.dump(_strip_docs(tree)).encode("utf-8")).hexdigest()[:16]
    body = txt.split("\ndef selftest(")[0]
    c["accel"] = "正本" if "VeritasCeleritas_v1141" in txt else ("舊橋" if "VIA_SuperAccel_Module" in txt or "[VIA:ACCEL-BRIDGE" in txt else "無")
    c["net"] = bool(re.search(r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|yfinance|akshare|fredapi|pandas_datareader)\b", body, re.M))
    c["net_canon"] = "VeritasAegisNexus_v1652" in txt
    c["selftest"] = "def selftest(" in txt or "--selftest" in txt
    c["chain"] = bool(re.search(r"PRIOR_PATH\s*=", txt) and re.search(r"PRIOR\s*=\s*_load", txt))
    return c


def explain(role: str, card: dict, fam: str) -> str:
    """規則式詳細說明(不靠模型):用途(docstring 首句)· 動詞 · 函式分類計數 · 依賴 · 加速器 · 出網 · 自測 · 鏈。"""
    if role in ("MANAGER", "ENGINE"):
        if not card.get("ast_ok", True):
            return "AST 解析失敗(%s)→ 讀不了,要人看" % card.get("err", "")
        first = re.split(r"(?<=[。.!?])\s|—|──", card.get("doc", ""))[0][:90] or "(無說明字串)"
        cats = " · ".join("%s %d" % (_CAT_ZH.get(k, k), v) for k, v in sorted(card.get("cats", {}).items(), key=lambda kv: -kv[1])[:5])
        libs = [x for x in card.get("imports", []) if x not in ("os", "re", "sys", "json", "datetime", "pathlib", "hashlib", "collections", "typing", "__future__", "time", "shutil", "html", "csv", "importlib", "types", "math", "itertools", "functools", "subprocess", "argparse", "io", "glob", "tempfile", "inspect", "contextlib", "dataclasses", "statistics", "unicodedata", "warnings", "traceback", "zipfile", "string", "copy", "random", "uuid", "threading", "queue", "concurrent", "multiprocessing", "logging", "textwrap", "base64", "struct", "decimal", "fractions", "operator", "enum", "abc")]
        return "%s · 函式 %d(%s)%s%s · 加速器 %s%s · 自測 %s%s" % (
            first, len(card.get("defs", [])), cats or "—", (" · 動詞 " + "/".join(card["verbs"][:8])) if card.get("verbs") else "", (" · 依賴 " + "/".join(libs[:6])) if libs else "",
            card.get("accel", "無"), (" · 出網(%s)" % ("正本網路工具" if card.get("net_canon") else "未走正本網路工具")) if card.get("net") else "", "有" if card.get("selftest") else "無", " · 薄尾鏈(要整條前版)" if card.get("chain") else "")
    if role == "SCRIPT":
        return card.get("doc") or "PowerShell"
    return card.get("doc") or _ROLE_ZH.get(role, role)


def other_card(p: Path, raw: bytes) -> dict:
    ext = p.suffix.lower()
    c = {"doc": "", "sem": ""}
    try:
        if ext == ".json" and len(raw) <= 30 * 1024 * 1024:
            d = json.loads(raw.decode("utf-8-sig", errors="replace"))
            c["sem"] = hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
            if isinstance(d, dict):
                n = max((len(v) for v in d.values() if isinstance(v, (list, dict))), default=0)
                c["doc"] = "冊 %s · 鍵 %s · 最大集合 %d 項" % (d.get("schema") or d.get("name") or "—", "/".join(list(d.keys())[:6]), n)
                c["keys"] = list(d.keys())[:40]
                c["json"] = d if len(raw) <= 2 * 1024 * 1024 else None
            elif isinstance(d, list):
                c["doc"] = "清單 %d 項" % len(d)
        elif ext == ".jsonl":
            c["doc"] = "帳 %d 列(只增,不退役)" % raw.count(b"\n")
        elif ext == ".csv":
            head = raw[:2000].decode("utf-8-sig", errors="replace").splitlines()
            c["doc"] = "表 %d 列 · 欄 %s" % (raw.count(b"\n"), (head[0][:80] if head else "—"))
        elif ext == ".html":
            m = re.search(rb"<title>(.*?)</title>", raw[:20000], re.S | re.I)
            c["doc"] = "頁 · %s" % (m.group(1).decode("utf-8", errors="replace").strip()[:80] if m else "—")
        elif ext in (".md", ".txt"):
            t = raw[:4000].decode("utf-8-sig", errors="replace")
            m = re.search(r"^#+\s*(.+)$", t, re.M)
            c["doc"] = (m.group(1) if m else t.strip().splitlines()[0] if t.strip() else "")[:100]
        elif ext == ".ps1":
            t = raw.decode("utf-8-sig", errors="replace")
            fns = re.findall(r"(?im)^\s*function\s+([\w-]+)", t)
            prm = re.search(r"(?is)param\s*\((.*?)\)\s*\n", t[:6000])
            pn = re.findall(r"\$(\w+)", prm.group(1)) if prm else []
            acc = "正本" if re.search(r"VeritasCeleritas\.PS7|Initialize-VCAccel|CELERITAS-TEMPLATE-JOIN|\[VIA:PS-ACCEL", t) else "無"
            emb = len(re.findall(r"Install-VIAEmbedded", t))
            c["doc"] = "PowerShell · 參數 %s · 函式 %d%s · 加速器 %s" % ("/".join(pn[:8]) or "—", len(fns), (" · 內嵌落地 %d 檔(啟動器)" % emb) if emb else "", acc)
            c["sem"] = hashlib.sha256(re.sub(r"(?m)^\s*#.*$|\s+", "", t).encode("utf-8")).hexdigest()[:16]
    except Exception as exc:  # noqa: BLE001
        c["doc"] = "讀不了:%s" % type(exc).__name__
    return c


# ───────── 全景掃描(快取:mtime + 大小沒變 → 沿用)─────────
def _row(key: str, p: Path, st) -> dict:
    raw = p.read_bytes() if st.st_size <= 60 * 1024 * 1024 else b""
    fam, ver, copy = fam_ver(p.stem)
    role = _role(Path(key))
    r = {"rel": key, "name": p.name, "ext": p.suffix.lower(), "size": st.st_size, "mtime": st.st_mtime, "sha": hashlib.sha256(raw).hexdigest()[:16] if raw else "大檔略", "fam": fam, "ver": ver, "copy": copy, "role": role}
    if r["ext"] == ".py":
        card = py_card(raw.decode("utf-8-sig", errors="replace"))
        r.update(card=card, sem=card.get("sem", ""), doc=explain(role, card, fam))
    else:
        oc = other_card(p, raw)
        r.update(card={k: v for k, v in oc.items() if k != "json"}, sem=oc.get("sem", ""), doc=oc.get("doc", ""))
        if oc.get("json") is not None:
            r["_json"] = oc["json"]
    return r


def scan(T: Path, write_cache: bool = True) -> list:
    cache_p = T / "_curate" / "SCAN_CACHE.json"
    try:
        cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    except ValueError:
        cache = {}
    rows, reused = [], 0
    for p in sorted(T.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(T)
        if set(rel.parts[:-1]) & _SKIP_DIRS or p.suffix.lower() == ".pyc" or (len(rel.parts) == 1 and _SYS_FILES.match(p.name)):
            continue
        st = p.stat()
        key = rel.as_posix()
        c = cache.get(key)
        if c and c.get("mtime") == st.st_mtime and c.get("size") == st.st_size and c.get("ext") != ".json":
            rows.append(dict(c, rel=key, reused=True))
            reused += 1
            continue
        rows.append(_row(key, p, st))
    if write_cache:
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        cache_p.write_text(json.dumps({r["rel"]: {k: v for k, v in r.items() if k not in ("rel", "reused", "_json")} for r in rows}, ensure_ascii=False), encoding="utf-8")
    for r in rows:
        r.setdefault("reused", False)
    _SCANSTAT["reused"] = reused
    return rows


# ───────── 補不足:正本 → 快照(只補新的 / 有變的;鏈族整條;intake 管線;子夾引擎;.ps1)─────────
_EXCL_HOME = {"intake", "references", "_superseded", "retired", "quarantine", "_quarantine", "tests", "test", "__pycache__", "vendor", "_inbox", "bridges", "VIA_Reports"}


def snapshot_plan() -> list:
    home = _home()
    plan = []

    def ok(p: Path) -> bool:
        rel = p.relative_to(home)
        return not (set(x.lower() for x in rel.parts[:-1]) & {x.lower() for x in _EXCL_HOME}) and not any(x.startswith(("_superseded", "_retired", "_quarantine")) for x in rel.parts) and p.stat().st_size <= 20 * 1024 * 1024 and not _COPY_RX.search(p.stem)
    for p in sorted(home.glob(_STEM + "_v*.py"), key=lambda q: _vnum_v0162(q.stem)):
        plan.append(("01_manager/" + p.name, p))
    fams = defaultdict(list)
    for ext in ("*.py", "*.ps1"):
        for p in home.rglob(ext):
            if p.name.startswith(_STEM) or not ok(p):
                continue
            fams[(p.parent, fam_ver(p.stem)[0], p.suffix.lower())].append(p)
    for (d, fam, ext), ps in fams.items():
        ps.sort(key=lambda q: (fam_ver(q.stem)[1], q.name))
        tail = ps[-1]
        chain = ext == ".py" and py_card(tail.read_text(encoding="utf-8-sig", errors="replace")).get("chain")
        sub = d.relative_to(home).as_posix()
        top = "08_scripts" if ext == ".ps1" else "02_engines"
        for p in (ps if chain else [tail]):
            plan.append(("%s/%s%s" % (top, (sub + "/") if sub != "." else "", p.name), p))
    for pkg in ("VRN_ReportClassifier", "VRN_TableRepair"):
        d = home / "intake" / pkg
        if d.is_dir():
            pf = defaultdict(list)
            for p in d.glob("*.py"):
                pf[fam_ver(p.stem)[0]].append(p)
            for fam, ps in pf.items():
                ps.sort(key=lambda q: fam_ver(q.stem)[1])
                plan.append(("02_engines/intake/%s/%s" % (pkg, ps[-1].name), ps[-1]))
            for p in d.glob("README*"):
                plan.append(("02_engines/intake/%s/%s" % (pkg, p.name), p))
    for sub, cat in (("SSOT", "03_ssot"), ("registry", "04_registry"), ("knowledge", "05_rules"), ("rules", "05_rules"), ("70_VRN_Rules", "05_rules")):
        d = home / sub
        if d.is_dir():
            books = defaultdict(list)
            for p in d.rglob("*"):
                if p.is_file() and ok(p) and p.suffix.lower() in (".json", ".jsonl", ".csv", ".md", ".txt", ".yaml", ".yml"):
                    if p.suffix.lower() == ".jsonl":
                        plan.append(("%s/%s" % (cat, p.relative_to(d).as_posix()), p))          # 帳全帶(只增)
                    else:
                        books[(p.parent, fam_ver(p.stem)[0], p.suffix.lower())].append(p)
            for ps in books.values():                                                           # 冊只帶尾版(與去重同口徑,不再來回拉鋸)
                t = sorted(ps, key=lambda q: (fam_ver(q.stem)[1], q.name))[-1]
                plan.append(("%s/%s" % (cat, t.relative_to(d).as_posix()), t))
    rep = home.parents[1] / "VIA_Reports" / "vrn"
    if rep.is_dir():
        for p in list(rep.glob("*_latest.*")) + list(rep.glob("*_MANIFEST.json")):
            plan.append(("06_reports/" + p.name, p))
    docs = home.parents[1] / "docs" / "handoff" / "ai"
    if docs.is_dir():
        for p in docs.glob("*.md"):
            if re.search(r"(?i)vrn|closeout|handover|govern", p.name):
                plan.append(("07_docs/" + p.name, p))
    seen, out = set(), []
    for rel, p in plan:
        if rel not in seen:
            seen.add(rel)
            out.append((rel, p))
    return out


def _retired_memory(T: Path) -> dict:
    led = T / "_curate" / "VRN02_Curate_Ledger.jsonl"
    mem = {}
    if led.exists():
        for ln in led.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(ln)
            except ValueError:
                continue
            if x.get("op") == "退役":
                mem[x["rel"]] = x.get("sha", "")
            elif x.get("op") == "補入":
                mem.pop(x["rel"], None)
    return mem


def gaps(T: Path) -> list:
    g = []
    mem = _retired_memory(T)
    for rel, src in snapshot_plan():
        dst = T / rel
        if rel in mem and not dst.exists():
            try:
                if hashlib.sha256(src.read_bytes()).hexdigest()[:16] == mem[rel]:
                    continue                                                    # 已退役且正本沒變 → 不再補回
            except OSError:
                continue
        if not dst.exists():
            g.append({"rel": rel, "src": str(src), "why": "快照沒有"})
        else:
            try:
                if dst.stat().st_size != src.stat().st_size or hashlib.sha256(dst.read_bytes()).digest() != hashlib.sha256(src.read_bytes()).digest():
                    g.append({"rel": rel, "src": str(src), "why": "正本較新 / 內容不同"})
            except OSError:
                pass
    return g


# ───────── 去重唯一:決策 ─────────
def decide(rows: list) -> list:
    by_sha, by_sem, by_fam = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in rows:
        r.setdefault("action", "待補入" if r.get("virtual") else "保留")
        r.setdefault("why", "")
        if r["sha"] != "大檔略":
            by_sha[r["sha"]].append(r)
        if r.get("sem"):
            by_sem[(r["ext"], r["sem"])].append(r)
        by_fam[(r["fam"], r["ext"])].append(r)

    def pref(r):
        home_dir = _ROLE_HOME.get(r["role"], "")
        return (r["copy"], not r["rel"].startswith(home_dir + "/") if home_dir else True, r["ver"] * -1, r["rel"].count("/"), len(r["rel"]), r["rel"])

    def retire(r, why):
        if r["action"] == "保留" and not r.get("virtual") and r["role"] not in ("LEDGER",) and not (r["role"] == "MANAGER"):
            r["action"], r["why"] = "退役", why
    for grp in by_sha.values():
        if len(grp) > 1:
            keep = sorted(grp, key=pref)[0]
            for r in grp:
                if r is not keep:
                    retire(r, "完全相同(sha %s)→ 留 %s" % (r["sha"][:8], keep["rel"]))
    for grp in by_sem.values():
        live = [r for r in grp if r["action"] in ("保留", "待補入")]
        if len(live) > 1:
            keep = sorted(live, key=lambda r: (not r.get("virtual"),) + pref(r))[0] if any(r.get("virtual") for r in live) else sorted(live, key=pref)[0]
            for r in live:
                if r is not keep:
                    retire(r, "內容相同(只差註解 / 格式 / 鍵序)→ 留 %s" % keep["rel"])
    for (fam, ext), grp in by_fam.items():
        live = [r for r in grp if r["action"] in ("保留", "待補入")]
        if len(live) < 2:
            continue
        roles = {r["role"] for r in live}
        if roles & {"MANAGER", "LEDGER", "DOC"}:
            continue
        chain = any(r.get("card", {}).get("chain") for r in live)
        if chain:
            for r in live:
                r["why"] = r["why"] or "薄尾鏈 · 整條保留(尾版靠前版才跑得動)"
            continue
        tail = sorted(live, key=lambda r: (r["copy"], -r["ver"], not r.get("virtual"), -r["mtime"]))[0]
        for r in live:
            if r is tail:
                continue
            stem = Path(r["name"]).stem
            if r["ver"] >= 0 and any(stem in x.get("card", {}).get("imports", []) for x in rows if x is not r and x["action"] in ("保留", "待補入")):
                r["why"] = "舊版但被引用 → 保留"
                continue
            if r["copy"]:
                retire(r, "副本檔名 → 留 %s" % tail["rel"])
            elif r["role"] == "REPORT":
                retire(r, "舊報表 → 留最新 %s" % tail["rel"])
            elif ext == ".json" and isinstance(r.get("_json"), dict) and isinstance(tail.get("_json"), dict) and _subset(r["_json"], tail["_json"]):
                retire(r, "舊冊是尾版的子集(一筆沒少)→ 留 %s" % tail["rel"])
            elif r["ver"] >= 0 and tail["ver"] > r["ver"]:
                retire(r, "舊版 → 尾版 %s 在" % tail["name"])
            else:
                r["why"] = "同族不同內容 · 無版號可比 → 保留(列整合候選)"
                r["merge"] = tail["rel"]
    return rows


def _subset(a, b) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return all(k in b and _subset(v, b[k]) for k, v in a.items() if k not in ("version", "ts", "generated", "updated", "schema_version"))
    if isinstance(a, list) and isinstance(b, list):
        return all(x in b for x in a) if len(a) <= 5000 else False
    return a == b


def merge_candidates(rows: list) -> list:
    py = [r for r in rows if r["ext"] == ".py" and r["action"] == "保留" and r["role"] == "ENGINE" and r.get("card", {}).get("ast_ok", True)]
    sets = {}
    for r in py:
        s = {d["name"] for d in r.get("card", {}).get("defs", []) if not d["name"].startswith("_") and d["name"] not in ("main", "selftest", "chk", "cli", "run")}
        if len(s) >= 5:
            sets[r["rel"]] = (r, s)
    out, keys = [], list(sets)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            (ra, sa), (rb, sb) = sets[keys[i]], sets[keys[j]]
            if ra["fam"] == rb["fam"]:
                continue
            jac = len(sa & sb) / len(sa | sb)
            if jac >= 0.6:
                out.append({"a": ra["rel"], "b": rb["rel"], "jaccard": round(jac, 2), "shared": sorted(sa & sb)[:10]})
    return sorted(out, key=lambda x: -x["jaccard"])[:60]


# ───────── 套用:補入 / 退役(搬 _retired\時間\)/ 清除 ─────────
def apply(T: Path, gp: list, rows: list, ts: str) -> dict:
    led = T / "_curate" / "VRN02_Curate_Ledger.jsonl"
    led.parent.mkdir(parents=True, exist_ok=True)
    filled = moved = 0
    with led.open("a", encoding="utf-8") as fh:
        for g in gp:
            dst = T / g["rel"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(g["src"], dst)
            filled += 1
            fh.write(json.dumps({"ts": ts, "op": "補入", "rel": g["rel"], "src": g["src"], "why": g["why"]}, ensure_ascii=False) + "\n")
        batch = T / "_retired" / ts.replace(":", "").replace("-", "")
        for r in rows:
            if r["action"] != "退役":
                continue
            src = T / r["rel"]
            if not src.exists():
                continue
            dst = batch / r["rel"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
            fh.write(json.dumps({"ts": ts, "op": "退役", "rel": r["rel"], "to": str(dst), "sha": r["sha"], "why": r["why"]}, ensure_ascii=False) + "\n")
    for d in sorted((x for x in T.rglob("*") if x.is_dir() and "_retired" not in x.parts and "_curate" not in x.parts), key=lambda x: -len(x.parts)):
        try:
            d.rmdir()
        except OSError:
            pass
    return {"filled": filled, "moved": moved, "batch": str(T / "_retired" / ts.replace(":", "").replace("-", "")), "ledger": str(led)}


def purge(T: Path) -> dict:
    rd = T / "_retired"
    n, size = 0, 0
    if rd.is_dir():
        for p in rd.rglob("*"):
            if p.is_file():
                n += 1
                size += p.stat().st_size
        shutil.rmtree(rd, ignore_errors=True)
    led = T / "_curate" / "VRN02_Curate_Ledger.jsonl"
    led.parent.mkdir(parents=True, exist_ok=True)
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "op": "清除", "files": n, "bytes": size}, ensure_ascii=False) + "\n")
    return {"files": n, "mb": round(size / 1024 ** 2, 1)}


# ───────── 輸出:AST 側冊(只增)· 索引 · AI 卡 · HTML ─────────
def write_outputs(T: Path, rows: list, mc: list, gp: list, s: dict, into_T: bool = True) -> dict:
    live = [r for r in rows if r["action"] != "退役"]
    items = {}
    for r in live:
        c = r.get("card", {})
        items[r["rel"]] = {"kind": {"MANAGER": "MDL", "ENGINE": "ENG"}.get(r["role"], r["role"]), "cat": r["role"], "zh": r.get("doc", "")[:240], "sha": r["sha"]}
        for d in c.get("defs", []):
            items["%s::%s" % (r["rel"], d["name"])] = {"kind": "FNC", "cat": d["cat"], "zh": d["doc"] or "%s(%s)" % (re.sub(r"_+", " ", d["name"]).strip(), ", ".join(d["args"])), "sha": r["sha"]}
        for k in c.get("classes", []):
            items["%s::%s" % (r["rel"], k["name"])] = {"kind": "CLS", "cat": "CLASS", "zh": k["doc"] or "類別 %s,%d 個方法" % (k["name"], k["methods"]), "sha": r["sha"]}
    prev = sorted(T.glob("VIA_AstAnnotations_VRN02_v*.json"), key=lambda q: _vnum_v0162(q.stem))
    old = {}
    if prev:
        try:
            old = json.loads(prev[-1].read_text(encoding="utf-8")).get("items", {})
        except ValueError:
            old = {}
    side = prev[-1] if prev else None
    if into_T and old != items:
        nv = (_vnum_v0162(prev[-1].stem) + 1) if prev else 100
        side = T / ("VIA_AstAnnotations_VRN02_v%04d.json" % nv)
        side.write_text(json.dumps({"schema": "VIA.AstAnnotations.v1", "sub": "VRN02(via_02_vrn 快照)", "version": "v%04d" % nv, "rule": "全景 AST 注入:分類 + 說明寫在側冊,不改原始碼;分類口徑 = %s" % s["cat_src"], "ts": s["ts"], "items": items}, ensure_ascii=False, indent=0), encoding="utf-8")
    idx = [{k: v for k, v in r.items() if k not in ("_json", "reused")} for r in live]
    if into_T:
        (T / "VRN02_INDEX_latest.json").write_text(json.dumps({"schema": "VIA.VRN02.Index.v1", "ts": s["ts"], "summary": s, "files": idx, "merge_candidates": mc}, ensure_ascii=False, indent=0, default=str), encoding="utf-8")
    fams = defaultdict(list)
    for r in live:
        fams[(r["role"], r["fam"])].append(r)
    lines = ["# via_02_vrn 現況 %s(VRN 快照 · 正本在 functional modules\\VRN)" % s["ts"][:16].replace("T", " "),
             "檔 %d · 族 %d · 退役 %d · 補入 %d · 鏈族 %d · 整合候選 %d 對 · AST 項 %d(側冊 %s)" % (len(live), len(fams), s["retire"], s["fill"], s["chains"], len(mc), len(items), side.name if side else "—"),
             "角色|族|版|檔數|說明"]
    order = ["MANAGER", "ENGINE", "SCRIPT", "SSOT", "REGISTRY", "RULE", "LEDGER", "REPORT", "DOC", "DATA", "OTHER"]
    for (role, fam), rs in sorted(fams.items(), key=lambda kv: (order.index(kv[0][0]) if kv[0][0] in order else 99, kv[0][1])):
        t = sorted(rs, key=lambda r: -r["ver"])[0]
        lines.append("%s|%s|%s|%d|%s" % (_ROLE_ZH.get(role, role), fam, ("v%04d" % t["ver"]) if t["ver"] >= 0 else "—", len(rs), re.sub(r"\s+", " ", t.get("doc", ""))[:70]))
    if mc:
        lines.append("整合候選(不同族 · 函式名重疊 ≥60%,人裁定):" + " · ".join("%s ~ %s(%.0f%%)" % (Path(x["a"]).name, Path(x["b"]).name, x["jaccard"] * 100) for x in mc[:8]))
    if into_T:
        (T / "VRN02_CARD_AI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    page = _resolve("_page")
    lamp_of = lambda r: "GRAY" if r["action"] == "退役" else ("RED" if not r.get("card", {}).get("ast_ok", True) else ("YELLOW" if r["ext"] == ".py" and (r.get("card", {}).get("accel") != "正本" or (r.get("card", {}).get("net") and not r.get("card", {}).get("net_canon")) or not r.get("card", {}).get("selftest")) else "GREEN"))  # noqa: E731
    order_l = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    trs = [(lamp_of(r), [r["action"] + (" · 補入" if r["rel"] in {g["rel"] for g in gp} else ""), _ROLE_ZH.get(r["role"], r["role"]), r["fam"], ("v%04d" % r["ver"]) if r["ver"] >= 0 else "—", r["rel"], r.get("doc", "")[:180],
                           " ".join("%s%d" % (_CAT_ZH.get(k, k), v) for k, v in sorted(r.get("card", {}).get("cats", {}).items(), key=lambda kv: -kv[1])[:4]), "/".join(r.get("card", {}).get("verbs", [])[:6]), r.get("card", {}).get("accel", "—") if r["ext"] == ".py" else "—", r.get("why", "")]) for r in sorted(rows, key=lambda r: (order_l[lamp_of(r)], r["role"], r["fam"], r["rel"]))]
    restore = "Get-ChildItem -LiteralPath '%s' -Recurse -File | ForEach-Object { $d = Join-Path '%s' ($_.FullName.Substring(%d)); New-Item -ItemType Directory -Force (Split-Path $d) | Out-Null; Move-Item -LiteralPath $_.FullName $d }" % (s.get("batch", ""), T, len(s.get("batch", "")) + 1)
    h = page("via_02_vrn 全景 · AST 分類與說明 · 去重唯一 · 補不足", "檔 %d → 保留 %d · 退役 %d(搬 _retired,可還原)· 補入 %d · 鏈族 %d(整條保留)· 整合候選 %d 對 · 分類口徑 %s · 還原整批:%s · 確認後真刪:curate --purge" % (len(rows), len(live), s["retire"], s["fill"], s["chains"], len(mc), html.escape(s["cat_src"]), html.escape(restore)),
             ["動作", "角色", "族", "版", "檔", "AST 說明", "函式分類", "動詞", "加速器", "理由"], trs)
    if mc:
        h = h.replace("</body>", "<h2 style='font-size:13px;margin:12px 0 4px'>整合候選(不同族 · 函式名重疊 ≥60% · 由操作員裁定合併)</h2><table><tr><th>A</th><th>B</th><th>重疊</th><th>共同函式</th></tr>" + "".join("<tr><td>%s</td><td>%s</td><td>%.0f%%</td><td>%s</td></tr>" % (html.escape(x["a"]), html.escape(x["b"]), x["jaccard"] * 100, html.escape(", ".join(x["shared"]))) for x in mc) + "</table></body>", 1)
    out = _rep() / "vrn02"
    out.mkdir(parents=True, exist_ok=True)
    hp = out / "VRN02_CURATE_latest.html"
    hp.write_text(h, encoding="utf-8")
    if into_T:
        (T / "VRN02_CURATE_latest.html").write_text(h, encoding="utf-8")
    return {"side": side.name if side else "—", "html": str(hp), "card": str(T / "VRN02_CARD_AI.md"), "items": len(items)}


def curate(T: Path, do_apply: bool = False, fill: bool = True) -> dict:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    gp = gaps(T) if fill else []
    res = {}
    if do_apply and gp:
        res = apply(T, gp, [], ts)
    rows = scan(T, write_cache=do_apply)
    if not do_apply:
        have = {r["rel"] for r in rows}
        for g in gp:
            src = Path(g["src"])
            v = _row(g["rel"], src, src.stat())
            v.update(virtual=True, why="(待補入)" + g["why"])
            if g["rel"] in have:
                for r in rows:
                    if r["rel"] == g["rel"]:
                        r.update(action="待更新", why="正本較新 → 套用時覆蓋")
            else:
                rows.append(v)
    rows = decide(rows)
    mc = merge_candidates(rows)
    if do_apply:
        r2 = apply(T, [], rows, ts)
        res = {"filled": res.get("filled", 0), "moved": r2["moved"], "batch": r2["batch"], "ledger": r2["ledger"]}
    s = {"ts": ts, "files": len(rows), "keep": sum(1 for r in rows if r["action"] not in ("退役",)), "retire": sum(1 for r in rows if r["action"] == "退役"), "fill": len(gp), "chains": len({r["fam"] for r in rows if r.get("card", {}).get("chain")}),
         "cat_src": cat_rules()[1], "reused": _SCANSTAT.get("reused", 0), "applied": do_apply, "batch": res.get("batch", ""), "why": dict(Counter(r["why"].split("(")[0].split(" →")[0] for r in rows if r["action"] == "退役")),
         "roles": dict(Counter(r["role"] for r in rows if r["action"] != "退役"))}
    o = write_outputs(T, rows, mc, gp, s, into_T=do_apply)
    s.update(o, merge=len(mc))
    return s


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["curate"]:
        vr = _resolve("via_roots")
        T = Path(args[args.index("--to") + 1]) if "--to" in args and args.index("--to") + 1 < len(args) else (vr()["via_02_vrn"] if vr else None)
        if not T or not T.is_dir():
            print("[計] curate · 快照夾不在 %s · RED" % T)
            return 1
        if "--purge" in args:
            o = purge(T)
            print("[計] curate --purge · 真刪 _retired:%d 檔 · %.1f MB · 帳留紀錄 · GREEN" % (o["files"], o["mb"]))
            return 0
        s = curate(T, do_apply="--apply" in args, fill="--no-fill" not in args)
        print("[計] curate %s · %s · 檔 %d → 保留 %d · 退役 %d%s · 補入 %d · 鏈族 %d · 整合候選 %d 對 · 掃描沿用 %d · 分類口徑 %s" % ("套用" if s["applied"] else "只列(加 --apply 才動)", T, s["files"], s["keep"], s["retire"], "(已搬 _retired,可還原)" if s["applied"] else "", s["fill"], s["chains"], s["merge"], s["reused"], s["cat_src"]))
        if s["why"]:
            print("[計] 退役理由 · " + " · ".join("%s %d" % kv for kv in sorted(s["why"].items(), key=lambda kv: -kv[1])))
        print("[計] 保留角色 · " + " · ".join("%s %d" % (_ROLE_ZH.get(k, k), v) for k, v in sorted(s["roles"].items(), key=lambda kv: -kv[1])))
        print("[計] AST 側冊 %s(%d 項 · 不改原始碼)· AI 卡 %s" % (s["side"], s["items"], s["card"]))
        if s["applied"] and s["retire"]:
            print("[計] 確認 HTML 沒問題後真刪:-Sub VRN -Verb curate -VerbArgs '~~apply,~~purge'(或整批還原:HTML 頂部那行)")
        print("  [U/I] %s" % s["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    prc = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("  ── 前版鏈自測(v0161 起 · 快取隔離)──")
        try:
            prc = PRIOR.selftest()
        except Exception as exc:  # noqa: BLE001
            prc = 1
            print("  [前版鏈中斷] %s: %s" % (type(exc).__name__, str(exc)[:120]))
    rc_ = _resolve("_reset_chain_caches")
    if rc_:
        rc_()
    _CR.clear()
    td = Path(tempfile.mkdtemp(prefix="vrn162-"))
    home = td / "functional modules" / "VRN"
    T = td / "via_02_vrn"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn")})
    try:
        def w(path: Path, txt: str):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(txt, encoding="utf-8")
        reg = td / "supportive modules" / "registry"
        w(reg / "CGC_MDL270_RegistryGovernor_v0106.py", '_CAT_RULES = [\n    ("ENTRY", r"^(main|run)$"), ("IO_READ", r"(?i)(read|load)"), ("INTERNAL", r"^_"),\n]\n')
        A0 = '"""引擎 A:讀報告。"""\nimport VeritasCeleritas_v1141\ndef read_report(p):\n    return p\ndef main():\n    return 0\ndef selftest():\n    return 0\n'
        A1 = A0 + "def load_more(x):\n    return x\n"
        C0 = '"""鏈底。"""\ndef base():\n    return 1\n'
        C1 = '"""薄尾。"""\nPRIOR_PATH = 1\nPRIOR = _load(PRIOR_PATH, "x")\ndef extra():\n    return 2\n'
        w(home / "VRN_SystemManager_v0100.py", "def main():\n    return 0\n")
        w(home / "VRN_ENG001_A_v0100.py", A0)
        w(home / "VRN_ENG001_A_v0101.py", A1)
        w(home / "VRN_ENG002_C_v0100.py", C0)
        w(home / "VRN_ENG002_C_v0101.py", C1)
        w(home / "engine" / "VRN_OldTool.py", '"""子夾引擎。"""\ndef run():\n    return 0\n')
        w(home / "Invoke-VRN-Tool-v0100.ps1", "param([string]$A)\nWrite-Host 1\n")
        w(home / "Invoke-VRN-Tool-v0101.ps1", "param([string]$A, [int]$B)\n# VeritasCeleritas.PS7\nWrite-Host 2\n")
        w(home / "intake" / "VRN_TableRepair" / "VRN_TableGeometry_v0101.py", "X = 1\n")
        w(home / "intake" / "VRN_TableRepair" / "VRN_TableGeometry_v0102.py", "X = 2\n")
        w(home / "intake" / "pack" / "huge.py", "X = 0\n")
        w(home / "SSOT" / "VRN_Book_v0100.json", json.dumps({"schema": "B", "items": {"a": 1}}))
        w(home / "SSOT" / "VRN_Book_v0101.json", json.dumps({"schema": "B", "items": {"a": 1, "b": 2}}))
        w(home / "SSOT" / "VRN_Run_Ledger.jsonl", '{"x":1}\n')
        w(T / "01_manager" / "VRN_SystemManager_v0100.py", "def main():\n    return 0\n")
        w(T / "02_engines" / "VRN_ENG001_A_v0100.py", A0)
        w(T / "02_engines" / "VRN_ENG001_A_v0100 (1).py", A0)
        w(T / "misc" / "VRN_ENG001_A_v0100.py", A0)
        w(T / "02_engines" / "VRN_ENG003_B_v0100.py", '"""B。"""\ndef f():\n    return 1  # 舊註解\n')
        w(T / "02_engines" / "VRN_ENG003_B_v0101.py", '"""B 新說明。"""\ndef f():\n    return 1\n')
        w(T / "03_ssot" / "VRN_Book_v0100.json", json.dumps({"schema": "B", "items": {"a": 1}}))
        w(T / "02_engines" / "VRN_Lib_v0100.py", "def g():\n    return 1\n")
        w(T / "02_engines" / "VRN_Lib_v0101.py", "def g():\n    return 2\n")
        w(T / "02_engines" / "VRN_ENG020_User_v0100.py", "import VRN_Lib_v0100\ndef use():\n    return VRN_Lib_v0100.g()\n")
        w(T / "04_registry" / "VRN_Log.jsonl", '{"a":1}\n')
        w(T / "04_registry" / "VRN_Log (1).jsonl", '{"a":1}\n{"b":2}\n')
        defs = "".join("def %s():\n    return 0\n" % n for n in ("read_pdf", "split_table", "fix_cells", "emit_html", "verify_sum", "parse_period"))
        w(T / "02_engines" / "VRN_ENG010_X_v0100.py", '"""X。"""\n' + defs)
        w(T / "02_engines" / "VRN_ENG011_Y_v0100.py", '"""Y。"""\n' + defs + "def other():\n    return 1\n")
        s0 = curate(T, do_apply=False)
        chk("① 只列不動:退役候選 %d(含將被補入尾版取代的舊版)· 待補入 %d · 快照夾一個檔都沒多沒少 · 分類口徑來自 VCGC Governor" % (s0["retire"], s0["fill"]), s0["retire"] >= 5 and s0["fill"] >= 6 and (T / "02_engines" / "VRN_ENG001_A_v0100 (1).py").exists() and "VCGC" in s0["cat_src"] and not (T / "_retired").exists() and not (T / "_curate").exists() and not list(T.glob("VRN02_*")) and not list(T.glob("VIA_AstAnnotations_*")))
        s1 = curate(T, do_apply=True)
        ex = lambda r: (T / r).exists()  # noqa: E731
        chk("② 補不足:尾版 A v0101 · 鏈族 C 整條(v0100+v0101)· 子夾引擎 engine/ · .ps1 尾版 · intake 管線尾版(v0102 不帶 v0101)· intake 大包不進",
            ex("02_engines/VRN_ENG001_A_v0101.py") and ex("02_engines/VRN_ENG002_C_v0100.py") and ex("02_engines/VRN_ENG002_C_v0101.py") and ex("02_engines/engine/VRN_OldTool.py") and ex("08_scripts/Invoke-VRN-Tool-v0101.ps1") and not ex("08_scripts/Invoke-VRN-Tool-v0100.ps1")
            and ex("02_engines/intake/VRN_TableRepair/VRN_TableGeometry_v0102.py") and not ex("02_engines/intake/VRN_TableRepair/VRN_TableGeometry_v0101.py") and not any("huge" in x.name for x in T.rglob("*.py") if "_retired" not in x.parts))
        chk("③ 去重唯一:完全相同(別夾 / (1) 副本)退 · 舊版 A v0100 退 · 只差註解的 B v0100 退 · 子集舊冊退 · 被 import 的舊版 Lib v0100 留 · 帳不退 · 鏈族不退",
            not ex("misc/VRN_ENG001_A_v0100.py") and not ex("02_engines/VRN_ENG001_A_v0100 (1).py") and not ex("02_engines/VRN_ENG001_A_v0100.py") and not ex("02_engines/VRN_ENG003_B_v0100.py") and ex("02_engines/VRN_ENG003_B_v0101.py")
            and not ex("03_ssot/VRN_Book_v0100.json") and ex("03_ssot/VRN_Book_v0101.json") and ex("02_engines/VRN_Lib_v0100.py") and ex("04_registry/VRN_Log.jsonl") and ex("04_registry/VRN_Log (1).jsonl") and ex("02_engines/VRN_ENG002_C_v0100.py"))
        batch = Path(s1["batch"])
        chk("④ 退役是搬 _retired\\時間\\(保留相對路徑,可整批還原)· 帳有補入 / 退役 · HTML 有還原指令", batch.is_dir() and (batch / "misc" / "VRN_ENG001_A_v0100.py").exists() and "退役" in (T / "_curate" / "VRN02_Curate_Ledger.jsonl").read_text(encoding="utf-8") and "Move-Item" in (T / "VRN02_CURATE_latest.html").read_text(encoding="utf-8"))
        side = json.loads((T / s1["side"]).read_text(encoding="utf-8"))
        it = side["items"]
        chk("⑤ AST 注入側冊(不改原始碼):每檔一項 + 每函式分類與說明(read_report → IO_READ · 有 docstring 用 docstring)· 原檔內容不變",
            "02_engines/VRN_ENG001_A_v0101.py::read_report" in it and it["02_engines/VRN_ENG001_A_v0101.py::read_report"]["cat"] == "IO_READ" and (T / "02_engines" / "VRN_ENG001_A_v0101.py").read_text(encoding="utf-8") == A1 and "讀報告" in it["02_engines/VRN_ENG001_A_v0101.py"]["zh"])
        chk("⑥ 整合候選:不同族函式名重疊 ≥60%(X ~ Y)列給人裁定,不自動合併", s1["merge"] >= 1 and ex("02_engines/VRN_ENG010_X_v0100.py") and ex("02_engines/VRN_ENG011_Y_v0100.py"))
        card = (T / "VRN02_CARD_AI.md").read_text(encoding="utf-8")
        chk("⑦ AI 現況卡:一族一行 · 有退役 / 補入 / 鏈族 / 整合候選數 · 精簡", "鏈族" in card and "整合候選" in card and len(card) < 6000)
        _CR.clear()
        _SCANSTAT.clear()
        s2 = curate(T, do_apply=True)
        s3 = curate(T, do_apply=True)
        nj = sum(1 for x in T.rglob("*.json") if "_curate" not in x.parts and "_retired" not in x.parts and not x.name.startswith(("VRN02_", "VIA_AstAnnotations_", "VRN_EXPORT")))
        chk("⑧ 再跑兩次:已唯一 → 退役 0 · 補入 0(冊只補尾版 · 已退役且正本沒變不補回 → 不拉鋸)· 帳全帶 · 掃描沿用快取(.json 例外)· 分類規則快取不崩 · 側冊不出新版",
            s2["retire"] == 0 and s2["fill"] == 0 and s3["retire"] == 0 and s3["fill"] == 0 and s2["side"] == s1["side"] and s2["reused"] >= s2["files"] - nj and ex("03_ssot/VRN_Run_Ledger.jsonl") and not ex("03_ssot/VRN_Book_v0100.json"))
        o = purge(T)
        chk("⑨ --purge 真刪 _retired(%d 檔)· 帳留清除紀錄" % o["files"], o["files"] >= 5 and not (T / "_retired").exists() and "清除" in (T / "_curate" / "VRN02_Curate_Ledger.jsonl").read_text(encoding="utf-8"))
    finally:
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        shutil.rmtree(td, ignore_errors=True)
    chk("⑩ 前版鏈(v0161 起)自測 rc 0%s" % ("(本次略過)" if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else ""), prc == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("[計] VRN_SystemManager_v0162 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
