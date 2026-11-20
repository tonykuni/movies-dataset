#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL158_VIAPanoramaAuditRepair v0120 — 薄尾:四塊拼圖模組接進全景工具(v0119 以前一字不動)

操作員 2026-11-20:「有以下的功能可更強化:缺少的功能模塊化加入現有工具」「寫成py模組跟舊的結合」。
附件建議逐項對照後,VIA 已有的不重做(骨架卡 / 切片 / 整夾索引 / 省 Token 帳 = read · slice · pack;
加速器與網路工具 100% = scan 的 ACCEL / NET 類 + CGC_MDL230 覆蓋探針;安全修補 = fix)。真的缺的四塊,各自一段、各自自測:

  ① clones   AST 結構指紋去重:每個函式去掉行號 / 說明字串 / 變數名後算雜湊 → 完全相同(exact)與只差常數(near)兩級分群;
              同家族副本與跨家族(可合併候選)分開列。做法收自收容夾 VES(via_engine_standardizer _norm_ast_hash),VES 本身不動。
  ② baseline / sigdiff  工具零丟失閘:每家族「有效公開介面」(尾版 + 經 __getattr__ 轉接的前版鏈)的名稱與參數存成基準線(TEMP);
              合併 / 去重 / 刪舊版之後跑 sigdiff:少一個名稱、拿掉或改名參數、新增必填參數、整家不見 = 紅;只加有預設的參數 = 綠。
  ③ orphans  死碼候選:尾版的公開函式在全樹找不到任何引用(識別字 · 屬性 · 字串 · .ps1 / .json 文字都算引用)→ 只列候選(黃);
              刪之前照「刪舊版先證明」實跑。
  ④ secrets  祕密字串掃描:已追蹤的文字檔找金鑰樣式(AWS · GitHub · sk- · Slack · Google · 私鑰 · 具名高熵指派)→ 只印位置與遮罩,
              絕不印原值;高信度 = 紅、具名高熵 = 黃。

四塊都只讀不改,結果存 TEMP(VIA_TOKEN_CACHE 可改位置),只用 Python 標準庫(零新套件、零網路),都印三數(應掃 · 已掃 · 略過)。
動詞表 VERBS 照 v0119 規矩明寫在本檔(主控台舊本體的省 Token 門用字串找 "read" 等字)。其餘動詞原樣轉交 v0119。
"""
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import collections
import copy
import functools
import hashlib
import importlib.util
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import time
import warnings
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_V0120 = "v0120"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0119.py")
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# 本工具全部動詞(唯一來源;tools / verbs / 功能卡都照這張)。用法裡的 $E = 鎖冊 token 那一支。
VERBS = dict(PRIOR.VERBS)
VERBS.update({
    "read": ("read <檔或夾…> [--depth N] [--if-etag <etag>]", "讀任何約 >200 行的檔、整夾、.json / .jsonl 之前",
             "骨架卡:匯入 · 定義樹(行號 · 簽章 · 首行說明)· AST 問題;夾 = 一檔一行;.json 看兩層、.jsonl 看欄位次數與首末列"),
    "slice": ("slice <檔> <定義名|Class.method|JSON 路徑> [--if-etag <etag>]", "只要看或改其中一段",
              "只取一個定義的原始碼(帶行號);JSON 路徑 a.b[0] · [-1] · [*] · [鍵=值]"),
    "digest": ("digest <日誌>", "看跑測 / 執行日誌", "只留判決行;紅日誌誠實回 rc 1"),
    "--if-etag": ("<read|slice|pack> … --if-etag <上次的 etag>", "同一對話重讀同一檔", "位元沒變回 304,沿用上一張卡;新對話不要帶"),
    "clones": ("clones [--max N] [--json]", "合併 / 去重之前,找全樹重複的函式",
               "AST 結構指紋:exact(只差變數名)· near(連常數也不同);同家族副本與跨家族可合併候選分開列;結果存 TEMP"),
    "baseline": ("baseline", "合併 / 去重 / 刪舊版之前先鎖住現有介面", "每家族有效公開介面(名稱 + 參數)存成基準線(TEMP)"),
    "sigdiff": ("sigdiff [--max N]", "合併 / 去重 / 刪舊版之後驗收工具零丟失",
                "跟基準線比:少名稱 · 拿掉或改名參數 · 新增必填參數 · 整家不見 = 紅(rc 1);只加有預設參數 = 綠"),
    "orphans": ("orphans [--max N]", "想精簡程式、找死碼時", "尾版公開函式全樹零引用 → 候選清單(黃);刪前照「刪舊版先證明」"),
    "secrets": ("secrets [--max N]", "推送、打包、交給任何外部工具之前", "已追蹤文字檔找金鑰樣式;只印位置與遮罩,不印原值;高信度 = 紅(rc 1)"),
})


@functools.wraps(PRIOR.pack_payload)
def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


def digest_log(text: str) -> dict:
    """日誌摘要:原樣轉交前版鏈。"""
    return PRIOR.digest_log(text)


# ── 共用小件 ────────────────────────────────────────────────────────────
_VER_RX = re.compile(r"^(?P<stem>.+?)_v(?P<ver>\d{3,4})$")


def _out_dir() -> Path:
    d = Path(PRIOR.cache_root()) / _V0120
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save(name: str, data) -> Path:
    p = _out_dir() / name
    PRIOR.atomic_write_text(p, json.dumps(data, ensure_ascii=False, indent=1))
    return p


def _load(name: str):
    p = _out_dir() / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _rel(p: Path, root: Path) -> str:
    try:
        return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()


def _quiet_parse(text: str):
    """ast.parse,但不讓被讀的檔自己的 SyntaxWarning(跳脫字元)洗版。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(text)


def _parse(p: Path):
    try:
        text = Path(p).read_text(encoding="utf-8-sig", errors="replace")
        return text, _quiet_parse(text)
    except (OSError, SyntaxError, ValueError):
        return None, None


def _family(p: Path) -> str:
    m = _VER_RX.match(Path(p).stem)
    return m.group("stem") if m else Path(p).stem


def _opt(argv: list, name: str, default: int) -> int:
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            return int(argv[i + 1])
    return default


def _three(should: int, done: int, skipped: list) -> str:
    return "應掃 %d · 已掃 %d · 略過 %d%s" % (should, done, len(skipped), "" if should == done + len(skipped) else " · 對不上")


# ── ① clones:AST 結構指紋 ──────────────────────────────────────────────
MIN_NODES = 40          # 太小的函式(轉接 · getter)不算,免得薄尾的轉接殼全成一群
BRIDGE_FUNCS = {"_via_net"}   # 標準檔頭橋(每支都抄同一份是規定,不是可合併的重複)
_SYS_PREFIX = (("CGC_", "VCGC"), ("VDF_", "VDF"), ("VRN_", "VRN"), ("VRN2_", "VRN"), ("VAP_", "VAP"), ("VQG_", "VQG"))


def _system(rel: str) -> str:
    """成員屬於哪個系統(看檔名前綴,再看路徑段);認不出 = 共用。"""
    name = rel.rsplit("/", 1)[-1]
    for pre, sysname in _SYS_PREFIX:
        if name.startswith(pre):
            return sysname
    for seg in rel.split("/"):
        if seg in ("VDF", "VRN", "VAP", "VQG"):
            return seg
    return ""


class _Norm(ast.NodeTransformer):
    """去行號(dump 不帶位置)· 去說明字串 · 變數 / 參數名換成序號;keep_const=False 時常數只留型別。"""

    def __init__(self, keep_const: bool):
        self.keep_const = keep_const
        self.names: dict = {}

    def _n(self, x: str) -> str:
        return self.names.setdefault(x, "v%d" % len(self.names))

    def _strip_doc(self, node):
        b = getattr(node, "body", None)
        if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) and isinstance(b[0].value.value, str):
            node.body = b[1:] or [ast.Pass()]
        return node

    def visit_FunctionDef(self, node):
        node = self._strip_doc(node)
        node.name = "_"
        node.decorator_list = []
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        return self.generic_visit(self._strip_doc(node))

    def visit_Name(self, node):
        node.id = self._n(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self._n(node.arg)
        node.annotation = None
        return node

    def visit_Constant(self, node):
        if not self.keep_const:
            return ast.Constant(value=type(node.value).__name__)
        return node


def fn_prints(tree) -> list:
    """一支檔每個夠大的函式:(名, 行, 節點數, exact 指紋, near 指紋)。"""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = sum(1 for _ in ast.walk(node))
            if size < MIN_NODES or node.name in BRIDGE_FUNCS:
                continue
            fps = []
            for keep in (True, False):
                n = _Norm(keep).visit(copy.deepcopy(node))
                fps.append(hashlib.sha256(ast.dump(n, include_attributes=False).encode("utf-8")).hexdigest()[:16])
            out.append([node.name, node.lineno, size, fps[0], fps[1]])
    return out


def _cached_prints(p: Path, root: Path):
    try:
        raw = Path(p).read_bytes()
    except OSError:
        return None
    key = hashlib.sha256((_V0120 + "|clones|" + _rel(p, root) + "|").encode("utf-8") + raw.replace(b"\r\n", b"\n")).hexdigest()
    cp = _out_dir() / "clones" / key[:2] / (key + ".json")
    try:
        return json.loads(cp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        rows = fn_prints(_quiet_parse(raw.decode("utf-8-sig", errors="replace")))
    except (SyntaxError, ValueError):
        return None
    cp.parent.mkdir(parents=True, exist_ok=True)
    PRIOR.atomic_write_text(cp, json.dumps(rows))
    return rows


def clones(files=None, root: Path | None = None) -> dict:
    root = Path(root or VIA)
    files = list(files if files is not None else PRIOR.py_files())
    skipped, by_exact, by_near, nfn = [], collections.defaultdict(list), collections.defaultdict(list), 0
    for p in files:
        rows = _cached_prints(p, root)
        if rows is None:
            skipped.append(_rel(p, root))
            continue
        rel = _rel(p, root)
        for name, line, size, ex, nr in rows:
            nfn += 1
            item = {"at": "%s:%d" % (rel, line), "name": name, "size": size, "family": _family(Path(rel)), "system": _system(rel)}
            by_exact[ex].append(item)
            by_near[nr].append(item)

    def clusters(groups, kind, seen=frozenset()):
        res = []
        for fp, items in groups.items():
            if len(items) < 2:
                continue
            ids = frozenset(i["at"] for i in items)
            if ids in seen:
                continue
            fams = {i["family"] for i in items}
            systems = {i["system"] for i in items if i["system"]}
            scope = ("跨系統(獨立律:只記不併)" if len(systems) > 1 else
                     "跨家族(可合併候選)" if len(fams) > 1 else "同家族副本")
            res.append({"kind": kind, "fp": fp, "n": len(items), "size": items[0]["size"], "scope": scope, "members": items})
        return sorted(res, key=lambda c: (-c["n"] * c["size"], c["fp"]))

    ex = clusters(by_exact, "exact")
    nr = clusters(by_near, "near", frozenset(frozenset(i["at"] for i in c["members"]) for c in ex))
    cross = [c for c in ex + nr if c["scope"].startswith("跨家族")]
    cross_sys = [c for c in ex + nr if c["scope"].startswith("跨系統")]
    return {"should": len(files), "done": len(files) - len(skipped), "skipped": skipped, "functions": nfn,
            "exact": ex, "near": nr, "cross": len(cross), "cross_system": len(cross_sys), "redundant": sum(c["n"] - 1 for c in ex),
            "state": "YELLOW" if cross else "GREEN"}


def render_clones(r: dict, max_show: int = 20) -> str:
    out = ["[clones · AST 結構指紋] %s · %s · 函式 %d(≥%d 節點,不含標準橋)· exact 群 %d · near 群 %d · 跨家族候選 %d · 跨系統只記 %d · 多餘函式 %d"
           % (r["state"], _three(r["should"], r["done"], r["skipped"]), r["functions"], MIN_NODES, len(r["exact"]),
              len(r["near"]), r["cross"], r.get("cross_system", 0), r["redundant"])]
    show = sorted(r["exact"] + r["near"], key=lambda c: (not c["scope"].startswith("跨家族"), -c["n"] * c["size"]))[:max_show]
    for c in show:
        out.append("  %-5s %s · %d 處 · %d 節點 · %s" % (c["kind"], c["scope"], c["n"], c["size"],
                                                     " | ".join("%s %s" % (m["at"], m["name"]) for m in c["members"][:4])
                                                     + (" …" if c["n"] > 4 else "")))
    return "\n".join(out)


# ── ② baseline / sigdiff:工具零丟失 ───────────────────────────────────
def _sig(fn) -> dict:
    a = fn.args
    pos = [x.arg for x in a.posonlyargs + a.args]
    return {"args": pos, "defaults": len(a.defaults), "kwonly": [x.arg for x in a.kwonlyargs],
            "kwdefaults": sum(1 for d in a.kw_defaults if d is not None), "vararg": bool(a.vararg), "kwarg": bool(a.kwarg)}


def api_of(tree) -> tuple:
    """一支檔的頂層公開介面 + 有沒有模組 __getattr__(有 = 把其餘名稱轉接給前版)。"""
    api, forwards = {}, False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "__getattr__":
                forwards = True
            elif not node.name.startswith("_"):
                api[node.name] = _sig(node)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            api[node.name] = {"class": True}
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not sub.name.startswith("_") or sub.name == "__init__"):
                    api[node.name + "." + sub.name] = _sig(sub)
    return api, forwards


def family_api(tail: Path) -> dict:
    """尾版 + 經 __getattr__ 一路轉接的前版鏈 → 有效公開介面(越新的定義優先)。"""
    tail = Path(tail)
    m = _VER_RX.match(tail.stem)
    chain = [tail]
    if m:
        chain = sorted((p for p in tail.parent.glob(m.group("stem") + "_v*.py") if 0 <= _vnum(p) <= _vnum(tail)), key=_vnum, reverse=True)
    api = {}
    for p in chain:
        _, tree = _parse(p)
        if tree is None:
            break
        own, forwards = api_of(tree)
        for k, v in own.items():
            api.setdefault(k, v)
        if not forwards:
            break
    return api


def snapshot(files=None, root: Path | None = None) -> dict:
    root = Path(root or VIA)
    files = list(files if files is not None else PRIOR.py_files())
    fams, skipped = {}, []
    for p in files:
        _, tree = _parse(p)
        if tree is None:
            skipped.append(_rel(p, root))
            continue
        rel = _rel(p, root)
        key = rel.rsplit("/", 1)[0] + "/" + _family(Path(rel)) if "/" in rel else _family(Path(rel))
        fams[key] = {"tail": rel, "api": family_api(p)}
    return {"version": _V0120, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": str(root), "should": len(files),
            "done": len(files) - len(skipped), "skipped": skipped, "families": fams}


def _sig_break(old: dict, new: dict) -> str:
    if old.get("class") or new.get("class"):
        return "" if old.get("class") == new.get("class") else "類別 / 函式互換"
    oa, na = old["args"], new["args"]
    if na[:len(oa)] != oa:
        return "位置參數被拿掉或改名:%s → %s" % (oa, na)
    if len(na) - new["defaults"] > len(oa) - old["defaults"]:
        return "新增必填參數:%s" % na[len(oa):]
    if not set(old["kwonly"]) <= set(new["kwonly"]):
        return "關鍵字參數被拿掉:%s" % sorted(set(old["kwonly"]) - set(new["kwonly"]))
    if (old["vararg"] and not new["vararg"]) or (old["kwarg"] and not new["kwarg"]):
        return "*args / **kwargs 被拿掉"
    return ""


def sig_compare(base: dict, cur: dict) -> dict:
    lost_fam, lost, broke, added, grew = [], [], [], 0, 0
    for key, b in base["families"].items():
        c = cur["families"].get(key)
        if c is None:
            lost_fam.append(key)
            continue
        for name, s in b["api"].items():
            if name not in c["api"]:
                lost.append("%s :: %s" % (c["tail"], name))
                continue
            why = _sig_break(s, c["api"][name])
            if why:
                broke.append("%s :: %s · %s" % (c["tail"], name, why))
            elif c["api"][name] != s:
                grew += 1
        added += len(set(c["api"]) - set(b["api"]))
    red = bool(lost_fam or lost or broke)
    return {"state": "RED" if red else "GREEN", "lost_families": lost_fam, "lost": lost, "broke": broke,
            "added": added, "grew": grew, "families": len(base["families"])}


def render_sigdiff(d: dict, cur: dict, base: dict, max_show: int = 40) -> str:
    out = ["[sigdiff · 工具零丟失] %s · 基準 %s · 現在 %s · 家族 %d · 整家不見 %d · 名稱少 %d · 介面變 %d · 新名稱 %d · 只加有預設參數 %d"
           % (d["state"], base.get("at", "?"), _three(cur["should"], cur["done"], cur["skipped"]), d["families"],
              len(d["lost_families"]), len(d["lost"]), len(d["broke"]), d["added"], d["grew"])]
    for tag, rows in (("整家不見", d["lost_families"]), ("名稱少", d["lost"]), ("介面變", d["broke"])):
        for r in rows[:max_show]:
            out.append("  RED  %s · %s" % (tag, r))
    return "\n".join(out)


# ── ③ orphans:死碼候選 ────────────────────────────────────────────────
_WORD_RX = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
_KEEP = {"main", "selftest", "run", "setup", "teardown"}


def orphans(files=None, root: Path | None = None, extra_text=None) -> dict:
    """尾版頂層公開函式,全樹(.py 的識別字 / 屬性 / 字串 + .ps1 / .json 文字)零引用 → 候選。"""
    root = Path(root or VIA)
    files = list(files if files is not None else PRIOR.py_files())
    refs, defs, skipped = collections.Counter(), [], []
    for p in files:
        text, tree = _parse(p)
        if tree is None:
            skipped.append(_rel(p, root))
            continue
        rel = _rel(p, root)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                refs[node.id] += 1
            elif isinstance(node, ast.Attribute):
                refs[node.attr] += 1
            elif isinstance(node, ast.alias):
                refs[node.name.split(".")[-1]] += 1
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                refs.update(_WORD_RX.findall(node.value))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_") and node.name not in _KEEP:
                if any(isinstance(d, (ast.Name, ast.Attribute, ast.Call)) for d in node.decorator_list):
                    continue                                   # 被裝飾 = 由框架註冊呼叫,不算死
                defs.append((rel, node.lineno, node.name))
    texts = extra_text if extra_text is not None else _side_texts(root)
    for t in texts:
        refs.update(_WORD_RX.findall(t))
    cands = [{"at": "%s:%d" % (r, ln), "name": n} for r, ln, n in defs if refs[n] == 0]
    return {"should": len(files), "done": len(files) - len(skipped), "skipped": skipped, "defs": len(defs),
            "candidates": cands, "state": "YELLOW" if cands else "GREEN"}


def _side_texts(root: Path, cap: int = 2_000_000):
    """.ps1 / .psm1 / .json / .jsonl(≤2 MB)的文字也算引用:名字寫在冊上或 PS 裡 = 有人用。"""
    for ext in ("*.ps1", "*.psm1", "*.json", "*.jsonl"):
        for p in Path(root).rglob(ext):
            try:
                if p.stat().st_size <= cap:
                    yield p.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue


def render_orphans(r: dict, max_show: int = 40) -> str:
    out = ["[orphans · 死碼候選] %s · %s · 公開函式 %d · 零引用 %d(只是候選:懶載入 / 名字釘死前版也算用到,刪前照「刪舊版先證明」實跑)"
           % (r["state"], _three(r["should"], r["done"], r["skipped"]), r["defs"], len(r["candidates"]))]
    for c in r["candidates"][:max_show]:
        out.append("  YELLOW %s %s" % (c["at"], c["name"]))
    return "\n".join(out)


# ── ④ secrets:祕密字串(只遮罩) ───────────────────────────────────────
_SECRET_RULES = [
    ("aws-access-key", "RED", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("github-token", "RED", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("sk-api-key", "RED", re.compile(r"\b(sk-(?:ant-|proj-)?[A-Za-z0-9_\-]{32,})\b")),
    ("slack-token", "RED", re.compile(r"\b(xox[abprs]-[A-Za-z0-9\-]{10,})\b")),
    ("google-api-key", "RED", re.compile(r"\b(AIza[0-9A-Za-z_\-]{35})\b")),
    ("private-key", "RED", re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----)")),
    ("named-high-entropy", "YELLOW", re.compile(
        r"(?i)(api[_-]?key|secret|token|passw(?:or)?d|fred_api_key)[\"']?\s*[:=]\s*[\"']([A-Za-z0-9_\-/+=]{20,})[\"']")),
]
_PLACEHOLDER_RX = re.compile(r"(?i)x{4,}|your|example|dummy|placeholder|changeme|redacted|<|\$\{|test|fake|sample|0{8,}")
_TEXT_EXT = {".py", ".ps1", ".psm1", ".json", ".jsonl", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".env",
             ".html", ".js", ".csv", ".log"}


def _entropy(s: str) -> float:
    c = collections.Counter(s)
    return -sum(v / len(s) * math.log2(v / len(s)) for v in c.values()) if s else 0.0


def mask(v: str) -> str:
    return "%s…(%d 字)" % (v[:4], len(v))


def scan_secrets_text(text: str) -> list:
    hits = []
    for ln, line in enumerate(text.splitlines(), 1):
        for kind, lamp, rx in _SECRET_RULES:
            for m in rx.finditer(line):
                v = m.group(m.lastindex)
                lamp_now = lamp
                if kind == "named-high-entropy":
                    if _PLACEHOLDER_RX.search(v) or _entropy(v) < 3.5 or re.fullmatch(r"[A-Z][A-Z0-9_]*", v):
                        continue                               # 佔位字 · 低熵 · 全大寫常數片語(同意字串)不是金鑰
                    lamp_now = "YELLOW" if "token" in m.group(1).lower() else "RED"   # 名叫 key / secret / password 的高熵值 = 紅
                elif kind != "private-key" and _PLACEHOLDER_RX.search(v):
                    continue
                hits.append({"line": ln, "kind": kind, "lamp": lamp_now, "masked": mask(v)})
    return hits


def _tracked(root: Path) -> list:
    r = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [p for p in Path(root).rglob("*") if p.is_file()]
    return [Path(root) / x for x in r.stdout.decode("utf-8", errors="replace").split("\0") if x]


def secrets(root: Path | None = None, files=None, cap: int = 5_000_000) -> dict:
    root = Path(root or VIA)
    files = [p for p in (files if files is not None else _tracked(root)) if Path(p).suffix.lower() in _TEXT_EXT]
    found, skipped = [], []
    for p in files:
        try:
            if Path(p).stat().st_size > cap:
                skipped.append(_rel(p, root))
                continue
            text = Path(p).read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            skipped.append(_rel(p, root))
            continue
        for h in scan_secrets_text(text):
            h["at"] = "%s:%d" % (_rel(p, root), h.pop("line"))
            found.append(h)
    red = [h for h in found if h["lamp"] == "RED"]
    return {"should": len(files), "done": len(files) - len(skipped), "skipped": skipped, "found": found,
            "state": "RED" if red else ("YELLOW" if found else "GREEN")}


def render_secrets(r: dict, max_show: int = 40) -> str:
    out = ["[secrets · 祕密字串] %s · %s · 命中 %d(紅 %d)· 只印遮罩,原值不出本機"
           % (r["state"], _three(r["should"], r["done"], r["skipped"]), len(r["found"]),
              sum(1 for h in r["found"] if h["lamp"] == "RED"))]
    for h in sorted(r["found"], key=lambda h: h["lamp"] != "RED")[:max_show]:
        out.append("  %-6s %s · %s · %s" % (h["lamp"], h["at"], h["kind"], h["masked"]))
    return "\n".join(out)


# ── 入口 ───────────────────────────────────────────────────────────────
def render_verbs() -> str:
    out = ["[%s %s 動詞表] %d 個 · $E = 鎖冊 token 那一支" % (_STEM, _V0120, len(VERBS))]
    for k, (usage, when, what) in VERBS.items():
        out.append("  %-10s python3 \"$E\" %s" % (k, usage))
        out.append("             何時:%s · 做什麼:%s" % (when, what))
    return "\n".join(out)


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    verb = argv[0] if argv else ""
    mx = _opt(argv, "--max", 20)
    t0 = time.time()
    if verb == "clones":
        r = clones()
        p = _save("clones_last.json", r)
        print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in argv else render_clones(r, mx))
        print("  [TEMP] %s · %.1f s" % (p, time.time() - t0))
        return 0
    if verb == "baseline":
        s = snapshot()
        p = _save("sig_baseline.json", s)
        n = sum(len(f["api"]) for f in s["families"].values())
        print("[baseline · 工具零丟失基準線] %s · 家族 %d · 公開名稱 %d · 存 %s · %.1f s"
              % (_three(s["should"], s["done"], s["skipped"]), len(s["families"]), n, p, time.time() - t0))
        return 0
    if verb == "sigdiff":
        base = _load("sig_baseline.json")
        if not base:
            print("[sigdiff · 工具零丟失] YELLOW · 還沒有基準線:先跑 python3 \"$E\" baseline(合併 / 去重 / 刪舊版之前)")
            return 0
        cur = snapshot()
        d = sig_compare(base, cur)
        print(render_sigdiff(d, cur, base, mx))
        print("  [TEMP] %s · %.1f s" % (_save("sigdiff_last.json", d), time.time() - t0))
        return 1 if d["state"] == "RED" else 0
    if verb == "orphans":
        r = orphans()
        print(render_orphans(r, mx))
        print("  [TEMP] %s · %.1f s" % (_save("orphans_last.json", r), time.time() - t0))
        return 0
    if verb == "secrets":
        r = secrets()
        print(render_secrets(r, mx))
        print("  [TEMP] %s · %.1f s" % (_save("secrets_last.json", r), time.time() - t0))
        return 1 if r["state"] == "RED" else 0
    if verb == "verbs":
        print(render_verbs())
        return 0
    return PRIOR.main()


def selftest() -> int:
    rc_prior = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))
    need = {"read", "slice", "digest", "pack", "chain", "scan", "report", "fix", "tests", "cache", "delta", "tools", "verbs",
            "clones", "baseline", "sigdiff", "orphans", "secrets"}
    chk("① 動詞表涵蓋前版鏈全部動詞 + 本版五個", need <= set(VERBS), sorted(need - set(VERBS)))
    g = PRIOR.legacy_gate_sees(Path(__file__))
    chk("② 主控台舊本體字串門對本檔全綠", all(g.values()), g)
    body = ("    total = 0\n    for item in items:\n        if item > limit:\n            total += item * 2\n"
            "        else:\n            total -= 1\n    return [total, len(items), sorted(items)]\n")
    with tempfile.TemporaryDirectory(prefix="via_mdl158_v0120_") as td:
        root = Path(td)
        (root / "fam_a").mkdir()
        (root / "fam_b").mkdir()
        a = root / "fam_a" / "A_MDL001_Alpha_v0100.py"
        b = root / "fam_b" / "B_MDL002_Beta_v0100.py"
        c = root / "fam_b" / "B_MDL003_Gamma_v0100.py"
        a.write_text("def calc(items, limit):\n    '''說明 A'''\n" + body, encoding="utf-8")
        b.write_text("def compute(xs, cap):\n" + body.replace("items", "xs").replace("limit", "cap").replace("item", "x"), encoding="utf-8")
        c.write_text("def other(items, limit):\n" + body.replace("* 2", "* 3"), encoding="utf-8")
        r = clones([a, b, c], root)
        ex = [cl for cl in r["exact"] if cl["n"] == 2]
        chk("③ clones:只差變數名 / 說明字串 = exact 同群 · 跨家族列為候選", len(ex) == 1 and ex[0]["scope"].startswith("跨")
            and {m["name"] for m in ex[0]["members"]} == {"calc", "compute"}, r["exact"])
        chk("④ clones:常數不同 = near 同群(不混進 exact)· 三數對得上",
            any(cl["n"] == 3 for cl in r["near"]) and r["should"] == 3 and r["done"] == 3, r["near"])
        lib = root / "lib"
        lib.mkdir()
        t1 = lib / "C_MDL004_Tool_v0100.py"
        t1.write_text("def keep(a, b=1):\n    return a\n\ndef gone(x):\n    return x\n\nclass K:\n    def m(self, q):\n        return q\n",
                      encoding="utf-8")
        base = snapshot([t1], root)
        t2 = lib / "C_MDL004_Tool_v0101.py"
        t2.write_text("from __future__ import annotations\n\ndef __getattr__(name):\n    raise AttributeError(name)\n\n"
                      "def keep(a, b=1, c=2):\n    return a\n", encoding="utf-8")
        d_ok = sig_compare(base, snapshot([t2], root))
        chk("⑤ sigdiff:薄尾只加有預設參數、其餘經 __getattr__ 轉接前版 = 綠(零丟失)", d_ok["state"] == "GREEN" and d_ok["grew"] == 1, d_ok)
        t3 = lib / "C_MDL004_Tool_v0102.py"
        t3.write_text("def keep(a, z):\n    return a\n", encoding="utf-8")
        d_bad = sig_compare(base, snapshot([t3], root))
        chk("⑥ sigdiff:不轉接少了 gone / K、改了 keep 參數 = 紅且逐項點名", d_bad["state"] == "RED" and len(d_bad["lost"]) == 3
            and len(d_bad["broke"]) == 1, d_bad)
        d_fam = sig_compare(base, {"families": {}, "should": 0, "done": 0, "skipped": []})
        chk("⑦ sigdiff:整家不見 = 紅", d_fam["state"] == "RED" and d_fam["lost_families"], d_fam)
        o1 = root / "o" / "D_MDL005_Orph_v0100.py"
        o1.parent.mkdir()
        o1.write_text("def used():\n    return 1\n\ndef by_string():\n    return 2\n\ndef by_ps():\n    return 3\n\n"
                      "def lonely():\n    return 4\n\ndef main():\n    return used() + getattr(sys, 'by_string', 0)\n", encoding="utf-8")
        r_o = orphans([o1], root, extra_text=["Invoke-Thing by_ps"])
        chk("⑧ orphans:識別字 / 字串 / .ps1 文字都算引用;只剩 lonely 是候選",
            [c_["name"] for c_ in r_o["candidates"]] == ["lonely"] and r_o["state"] == "YELLOW", r_o)
        fake_aws = "AKIA" + "QWERTYUIOPASDFGH"
        fake_gh = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
        named = "api_key = '" + "Zq9" + "Xw7Lk2Pm5Rt8Vb4Nc6Hj3" + "'"
        s1 = root / "s" / "conf.json"
        s1.parent.mkdir()
        tok = "session_token = '" + "Hq8" + "Wd4Mn7Ks2Lp9Tx5Rv3" + "'"
        s1.write_text('{"k": "%s"}\n%s\nghtoken=%s\napi_key = "your_api_key_here_xxxxxxxx"\n%s\nconsent_token = "I_ACKNOWLEDGE_THE_RISK_OF_SCRAPING"\n'
                      % (fake_aws, named, fake_gh, tok), encoding="utf-8")
        r_s = secrets(root, [s1])
        got = sorted((h["kind"], h["lamp"]) for h in r_s["found"])
        chk("⑨ secrets:AWS / GitHub / 名叫 api_key 的高熵值 = 紅 · 名叫 token 的 = 黃 · 佔位字與全大寫同意字串不報",
            got == [("aws-access-key", "RED"), ("github-token", "RED"), ("named-high-entropy", "RED"), ("named-high-entropy", "YELLOW")]
            and r_s["state"] == "RED", got)
        chk("⑩ secrets:輸出只有遮罩,原值一個字都不出現", fake_aws not in json.dumps(r_s) and fake_gh not in json.dumps(r_s)
            and "Xw7Lk2Pm5Rt8" not in json.dumps(r_s) and "Wd4Mn7Ks2Lp9" not in json.dumps(r_s))
        br = root / "fam_a" / "E_MDL006_Bridge_v0100.py"
        br.write_text("def _via_net():\n" + body, encoding="utf-8")
        vd = root / "fam_a" / "VDF_MDL007_Same_v0100.py"
        vr = root / "fam_b" / "VRN_MDL008_Same_v0100.py"
        vd.write_text("def sy_check(items, limit):\n" + body.replace("* 2", "* 5"), encoding="utf-8")
        vr.write_text("def sy_check(items, limit):\n" + body.replace("* 2", "* 5"), encoding="utf-8")
        r_b = clones([a, br, vd, vr], root)
        scopes = sorted(cl["scope"] for cl in r_b["exact"])
        chk("⑬ clones:標準橋 _via_net 不算重複 · VDF / VRN 同碼標「跨系統只記不併」(獨立律)",
            scopes == ["跨系統(獨立律:只記不併)"] and r_b["cross_system"] == 2 and r_b["cross"] == 0
            and not any(m["name"] == "_via_net" for cl in r_b["exact"] + r_b["near"] for m in cl["members"]), r_b)
    buf = io.StringIO()
    with redirect_stdout(buf):
        sys_argv, sys.argv = sys.argv, [sys.argv[0], "verbs"]
        try:
            rc_v = main()
        finally:
            sys.argv = sys_argv
    chk("⑪ verbs 印出全部動詞", rc_v == 0 and all(("python3 \"$E\" " + VERBS[k][0]) in buf.getvalue() for k in VERBS))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不 import 第三方套件",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"^(import|from)\s+(rapidfuzz|libcst|deepdiff|datasketch|tree_sitter|ruff)\b", text, re.M))
    passed = rc_prior == 0 and all(ok)
    print("[計] %s %s 本版 %d/%d · 前版 %s · %s" % (_STEM, _V0120, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL", "PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
