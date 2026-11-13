#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL281_ShadowMerge v0100 — 影子隔離 + 兩支舊版引擎逐定義比對 + 零遺失證明(VCGC 只讀工具;只寫 VIA_Reports/shadow_merge)

操作員 2026-11-13:「依照過去規定成功自動註冊的…引擎…功能只增不減不重複原則注入 AST 將引擎全面性模塊化簡化後進行安全整併
  VCGC 應該有相關功能可整合動作 整合要先複製不影響舊的 … 合併去重測試」→「接進 VCGC」。

先量再寫(L116):VCGC 樹上的 MDL092 稽核冊、MDL166 稽核四庫、MDL045 去重索引、MDL086 裁定雙位置正典、MDL143 修合併衝突,
  沒有一支做「兩支引擎逐定義比對 → 影子合併 → 零遺失證明」。PEIS 的函式正規化把字串常數一律當成同一個值(為了分群),
  拿來去重會把「只差一條路徑 / 一句 SQL」的兩支函式當成重複刪掉——違 L67 / L75。所以本器的去重判準是**含常數的完整 AST**,
  α 改名 + 字串遮罩的「近似」只拿來提示。薄尾判定不另寫尺:問鎖版 token 工具的 `chain`(VIA_ToolVersion_Lock 的 token 席位)。

做什麼(照本倉律,不照「取參數最多的那支當核心」):
  ① 影子複製:兩支原檔 sha256 先記帳 → 複製進 <VIA>/VIA_Reports/shadow_merge/<UTC>_<sha8>/orig/(唯讀)
     → 全程只讀影子副本;結束時原檔 sha256 再量一次,變了就 rc 2(量的動作不得改變被量的東西,LL368)。
  ② 逐定義比對(頂層函式 / 類別 + 類別方法):
       SAME               含常數的完整 AST 相同 → 可去重(留一份)
       DOC_ONLY           只差 docstring → 低風險,但 B 的說明沒遷 → 列「未遷」
       SAME_SIG_DIFF_BODY 簽章同、本體不同 → **不准遷**(L75 證不出零損失)
       DIFF_SIG           簽章不同 → **不准遷**
       ONLY_A / ONLY_B    單邊才有 → 保留 / 注入合併候選(帶環繞斷言)
  ③ 合併候選(只在影子區):以 A 為底,補 B 才有的 import 與 ONLY_B 定義;
     環繞斷言 = 影子 A 的 sha 與計畫時相同 + 錨點那一行逐字相同,否則拒絕注入。
     插入點避開 `if __name__ == "__main__":`(插在它後面 = main 先跑、定義後到)。
     ONLY_B 定義用到合併檔裡沒有的名字 → 標 RISK 不搬(搬過去會 NameError)。
  ④ 零遺失證明:合併候選 ast.parse + compile;A 每個定義原樣在;B 每個定義要嘛原樣在、要嘛列進「未遷」並附理由。
     未遷為空 → PROVEN_ZERO_LOSS(rc 0);否則 BLOCKED_NEEDS_RULING(rc 1,候選照寫,但不准拿去替換)。

不做的事(刻意):不執行被比對的引擎(--selftest 走各系統自己的 manager,AGENTS.md 第 5 條)、不寫回原檔、
  不註冊、不發號、不裝套件(LibCST 有就只拿來取帶前置註解的原文;沒有就用標準庫 ast,判準相同)。

用法(經 VCGC):
  VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL281_ShadowMerge compare <A.py> <B.py> [--json] [--out DIR]
  VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL281_ShadowMerge --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import builtins
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:                                    # LibCST 只用來取「含前置註解」的原文;判準一律走標準庫 ast(兩條路同一把尺)
    import libcst as cst                # noqa: F401
except Exception:                       # noqa: BLE001
    cst = None

NAME = "CGC_MDL281_ShadowMerge"
VERSION = "v0100"
SCHEMA = "VIA.ShadowMerge.v1"
DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__", "__builtins__"}


# ---------------------------------------------------------------- 小工具
def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]


def via_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
    return None


def _strip_doc(node):
    """回傳拿掉 docstring 的淺拷貝(只為了判 DOC_ONLY)。"""
    body = list(getattr(node, "body", []))
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:] or [ast.Pass()]
    clone = type(node)(**{k: getattr(node, k) for k in node._fields})
    clone.body = body
    return clone


def exact_sha(node) -> str:
    """含常數的完整 AST(不含行號、不含註解)——去重唯一判準。"""
    return _h(ast.dump(node, include_attributes=False))


def loose_sha(node) -> str:
    """α 改名 + 字串遮罩:只拿來提示「近似」,永不拿來去重。"""
    class _N(ast.NodeTransformer):
        def __init__(self):
            self.m = {}

        def visit_Name(self, n):
            if isinstance(n.ctx, ast.Store) or n.id in self.m:
                n.id = self.m.setdefault(n.id, f"v{len(self.m)}")
            return n

        def visit_Constant(self, n):
            if isinstance(n.value, str):
                n.value = "S"
            return n
    import copy
    return _h(ast.dump(_N().visit(copy.deepcopy(node)), include_attributes=False))


def signature(node) -> str:
    if isinstance(node, ast.ClassDef):
        return "(" + ", ".join(ast.unparse(b) for b in node.bases) + ")"
    ret = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    return f"({ast.unparse(node.args)}){ret}"


def free_names(node) -> set[str]:
    """定義裡讀到、但不是自己參數 / 區域變數 / 內建的名字(搬家前要確認合併檔裡有)。"""
    loads, stores = set(), set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            (stores if isinstance(n.ctx, (ast.Store, ast.Del)) else loads).add(n.id)
        elif isinstance(n, ast.arg):
            stores.add(n.arg)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not node:
            stores.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            stores.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            stores.add(n.name)
    return loads - stores - _BUILTINS


def module_names(tree: ast.Module) -> set[str]:
    got = set()
    for st in tree.body:
        if isinstance(st, DEF_NODES):
            got.add(st.name)
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            got.update((a.asname or a.name).split(".")[0] for a in st.names)
        else:
            for n in ast.walk(st):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    got.add(n.id)
    return got


# ---------------------------------------------------------------- 載入(LibCST 或標準庫)
@dataclass
class Def:
    qual: str
    kind: str
    sig: str
    exact: str
    nodoc: str
    loose: str
    start: int
    end: int
    prev: str | None = None
    next: str | None = None
    free: list = field(default_factory=list)
    text: str = ""


def load_defs(path: Path) -> tuple[ast.Module, list[str], dict[str, Def], dict]:
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src, filename=str(path))
    lines = src.splitlines()
    defs: dict[str, Def] = {}
    top = [st for st in tree.body if isinstance(st, DEF_NODES)]
    for i, st in enumerate(top):
        start = min([d.lineno for d in st.decorator_list] + [st.lineno])
        kind = "class" if isinstance(st, ast.ClassDef) else ("async def" if isinstance(st, ast.AsyncFunctionDef) else "def")
        defs[st.name] = Def(st.name, kind, signature(st), exact_sha(st), exact_sha(_strip_doc(st)), loose_sha(st),
                            start, st.end_lineno or st.lineno,
                            top[i - 1].name if i else None, top[i + 1].name if i + 1 < len(top) else None,
                            sorted(free_names(st)), "\n".join(lines[start - 1:st.end_lineno]))
        if isinstance(st, ast.ClassDef):
            for m in st.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = f"{st.name}.{m.name}"
                    ms = min([d.lineno for d in m.decorator_list] + [m.lineno])
                    defs[q] = Def(q, "method", signature(m), exact_sha(m), exact_sha(_strip_doc(m)), loose_sha(m),
                                  ms, m.end_lineno or m.lineno, text="\n".join(lines[ms - 1:m.end_lineno]))
    backend = "stdlib-ast"
    if cst is not None:                                  # 只換原文來源:LibCST 的原文帶前置註解與空行
        try:
            mod = cst.parse_module(src)
            for st in mod.body:
                if isinstance(st, (cst.FunctionDef, cst.ClassDef)) and st.name.value in defs:
                    defs[st.name.value].text = mod.code_for_node(st).rstrip("\n")
            backend = "libcst"
        except Exception as exc:                          # noqa: BLE001
            backend = f"stdlib-ast(LibCST 讀不了:{type(exc).__name__})"
    meta = {"backend": backend, "top_defs": len(top), "lines": len(lines)}
    return tree, lines, defs, meta


def thin_tail(path: Path) -> dict:
    """薄尾判定:先問鎖版 token 工具的 `chain`(L116 不另寫第二把尺);問不到才退回字面判準並標明出處。"""
    path = Path(path).resolve()
    fam = re.sub(r"_v\d{4}$", "", path.stem)
    m = re.search(r"_v(\d{4})$", path.stem)
    root = via_root(path.parent)
    if root and m:
        try:
            lock = json.loads((root / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
            tool = root.parent / lock["token"]["path"]
            if not tool.is_file():
                tool = root / lock["token"]["path"]
            out = subprocess.run([sys.executable, "-I", str(tool), "chain", str(path)], capture_output=True, text=True,
                                 timeout=120, cwd=str(root.parent)).stdout
            line = next((ln for ln in out.splitlines() if ln.strip().startswith("v" + m.group(1) + " ")), "")
            parts = [x.strip() for x in line.split(" · ")]
            if len(parts) >= 2:                           # 第二欄 = 連結:「本體(無前版連結)」/「glob 取前版」/「釘名 v0101(…)」…
                return {"thin_tail": not parts[1].startswith("本體"), "family": fam, "link": parts[1],
                        "how": f"chain({tool.name})", "chain_line": " ".join(line.split())[:160]}
        except Exception as exc:                          # noqa: BLE001
            fam_note = f"chain 問不到:{type(exc).__name__}"
        else:
            fam_note = "chain 沒列出這一版"
    else:
        fam_note = "不在 VIA 樹內或檔名無版號"
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    thin = fam != path.stem and fam in src and any(k in src for k in ("glob(", "import_module", "spec_from_file_location", "exec("))
    return {"thin_tail": thin, "family": fam, "how": f"字面判準({fam_note})"}


# ---------------------------------------------------------------- 比對與合併
def classify(a: dict[str, Def], b: dict[str, Def]) -> list[dict]:
    rows = []
    for q in sorted(set(a) | set(b), key=lambda k: (k.count("."), k)):
        x, y = a.get(q), b.get(q)
        if x and not y:
            cls = "ONLY_A"
        elif y and not x:
            cls = "ONLY_B"
        elif x.exact == y.exact:
            cls = "SAME"
        elif x.nodoc == y.nodoc:
            cls = "DOC_ONLY"
        elif x.sig == y.sig:
            cls = "SAME_SIG_DIFF_BODY"
        else:
            cls = "DIFF_SIG"
        near = bool(x and y and cls in ("SAME_SIG_DIFF_BODY", "DIFF_SIG") and x.loose == y.loose)
        rows.append({"qual": q, "class": cls, "near": near,
                     "a": f"L{x.start}-{x.end} {x.sig}" if x else None,
                     "b": f"L{y.start}-{y.end} {y.sig}" if y else None})
    return rows


def _main_guard_line(tree: ast.Module) -> int | None:
    for st in tree.body:
        if isinstance(st, ast.If) and "__name__" in ast.unparse(st.test) and "__main__" in ast.unparse(st.test):
            return st.lineno
    return None


def build_candidate(a_path: Path, a_sha: str, tree_a, lines_a, defs_a, tree_b, defs_b, rows) -> tuple[str, list, list]:
    """回 (合併候選原文, 注入紀錄, 未遷清單)。只在影子區用;每次注入都過環繞斷言。"""
    inserts, moved, not_moved = [], [], []
    have = module_names(tree_a)
    # 1. B 才有的 import:插在 A 最後一個頂層 import 之後
    a_imps = {ast.unparse(s) for s in tree_a.body if isinstance(s, (ast.Import, ast.ImportFrom))}
    b_imps = [s for s in tree_b.body if isinstance(s, (ast.Import, ast.ImportFrom)) and ast.unparse(s) not in a_imps]
    last_imp = max((s.end_lineno for s in tree_a.body if isinstance(s, (ast.Import, ast.ImportFrom))), default=0)
    if b_imps:
        inserts.append((last_imp, "\n".join(ast.unparse(s) for s in b_imps), "import", lines_a[last_imp - 1] if last_imp else ""))
        for s in b_imps:
            have.update((n.asname or n.name).split(".")[0] for n in s.names)
            moved.append({"what": ast.unparse(s), "how": f"import 併在 A 第 {last_imp} 行之後"})
    # 2. B 的其他模組層陳述式(常數、設定…)不自動搬:那是要人判的真相差異(L61)
    a_stmts = {ast.dump(s, include_attributes=False) for s in tree_a.body}
    for s in tree_b.body:
        if not isinstance(s, (ast.Import, ast.ImportFrom, *DEF_NODES)) and ast.dump(s, include_attributes=False) not in a_stmts \
                and not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant)) \
                and not (isinstance(s, ast.If) and "__main__" in ast.unparse(s.test)):
            not_moved.append({"qual": f"<模組層 L{s.lineno}>", "why": "B 的模組層陳述式與 A 不同(常數 / 設定),不代判",
                              "src": ast.unparse(s)[:120]})
    # 3. ONLY_B 頂層定義:錨點 = B 裡排在它前面的定義;A 有且唯一 → 插在它後面;否則插在 __main__ 之前 / 檔尾
    guard = _main_guard_line(tree_a)
    tail = (guard - 1) if guard else len(lines_a)
    for r in rows:
        if r["class"] != "ONLY_B" or "." in r["qual"]:
            continue
        d = defs_b[r["qual"]]
        anchor = d.prev if d.prev in defs_a and "." not in d.prev else None
        at = defs_a[anchor].end if anchor else tail
        if guard and at >= guard:
            at, anchor = tail, None
        missing = [n for n in d.free if n not in have and n not in defs_a and n not in defs_b]
        if missing:
            not_moved.append({"qual": r["qual"], "why": f"RISK:用到合併檔沒有的名字 {missing}(搬過去會 NameError)"})
            continue
        inserts.append((at, d.text, r["qual"], lines_a[at - 1] if at else ""))
        moved.append({"what": r["qual"], "how": f"插在 A 第 {at} 行之後(錨點 {anchor or ('__main__ 之前' if guard else '檔尾')})"})
    # 4. 不准遷的
    for r in rows:
        if r["class"] in ("SAME_SIG_DIFF_BODY", "DIFF_SIG"):
            not_moved.append({"qual": r["qual"], "why": f"{r['class']}:保留 A 版;B 版不准遷(L75 證不出零損失)"
                              + ("· 只差字串 / 變數名,行為可能不同" if r["near"] else "")})
        elif r["class"] == "DOC_ONLY":
            not_moved.append({"qual": r["qual"], "why": "DOC_ONLY:本體相同,B 的 docstring 沒遷(低風險,仍要人看)"})
        elif r["class"] == "ONLY_B" and "." in r["qual"]:
            not_moved.append({"qual": r["qual"], "why": "ONLY_B 方法:不往既有類別裡注入,需裁定"})
    # 5. 環繞斷言 + 由下往上注入(行號不位移)
    if sha256_file(a_path) != a_sha:
        raise RuntimeError("環繞斷言失敗:影子 A 在計畫後被改過,拒絕注入")
    out = list(lines_a)
    for at, text, what, anchor_line in sorted(inserts, key=lambda t: -t[0]):
        if (out[at - 1] if at else "") != anchor_line:
            raise RuntimeError(f"環繞斷言失敗:{what} 的錨點第 {at} 行已變,拒絕注入")
        block = text.split("\n")
        out[at:at] = ([""] if what == "import" else ["", ""]) + block + ([] if what == "import" else [""])
    return "\n".join(out) + "\n", moved, not_moved


def prove(merged_src: str, defs_a, defs_b, rows, not_moved) -> dict:
    tree = ast.parse(merged_src)
    compile(merged_src, "<merged>", "exec")
    tmp = Path(tempfile.mkstemp(suffix=".py")[1])
    try:
        tmp.write_text(merged_src, encoding="utf-8")
        _, _, defs_m, _ = load_defs(tmp)
    finally:
        tmp.unlink(missing_ok=True)
    lost_a = [q for q, d in defs_a.items() if q not in defs_m or defs_m[q].exact != d.exact]
    nm = {x["qual"] for x in not_moved}
    lost_b = [q for q, d in defs_b.items()
              if not (q in defs_m and defs_m[q].exact == d.exact) and q not in nm]
    ok = not lost_a and not lost_b and not not_moved
    return {"parse": True, "compile": True, "a_defs_kept": len(defs_a) - len(lost_a), "a_defs": len(defs_a),
            "a_lost": lost_a, "b_unaccounted": lost_b, "not_moved": len(not_moved),
            "verdict": "PROVEN_ZERO_LOSS" if ok else ("FAIL_LOSS" if (lost_a or lost_b) else "BLOCKED_NEEDS_RULING")}


# ---------------------------------------------------------------- 主流程
def resolve_input(p: str | Path) -> Path:
    """經 VCGC `run` 時工作目錄是引擎所在的夾:相對路徑依序找 目前目錄 → 倉根 → VIA 根。找不到 = FileNotFoundError(由 main 報 ABSENT)。"""
    q = Path(p)
    if q.is_absolute():
        cands = [q]
    else:
        via = via_root(Path(__file__).resolve().parent)
        cands = [Path.cwd() / q] + ([via.parent / q, via / q] if via else [])
    for c in cands:
        if c.is_file():
            return c.resolve()
    raise FileNotFoundError(f"找不到 {p}(試過:{' · '.join(str(c) for c in cands)})")


def run(a: Path, b: Path, out_root: Path | None = None) -> dict:
    a, b = resolve_input(a), resolve_input(b)
    before = {str(a): sha256_file(a), str(b): sha256_file(b)}
    root = via_root(a.parent)
    base = out_root or ((root / "VIA_Reports" / "shadow_merge") if root else Path(tempfile.gettempdir()) / "via_shadow_merge")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shadow = base / f"{stamp}_{_h(before[str(a)] + before[str(b)])[:8]}"
    (shadow / "orig").mkdir(parents=True, exist_ok=False)          # 新夾;不覆蓋任何舊影子
    sa, sb = shadow / "orig" / ("A__" + a.name), shadow / "orig" / ("B__" + b.name)
    shutil.copy2(a, sa)
    shutil.copy2(b, sb)
    for p in (sa, sb):
        p.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)          # 影子副本唯讀
    sha_sa = sha256_file(sa)
    tree_a, lines_a, defs_a, meta_a = load_defs(sa)
    tree_b, _, defs_b, meta_b = load_defs(sb)
    meta_a.update(thin_tail(a))                           # 問原檔(影子副本改了名,chain 認不得)
    meta_b.update(thin_tail(b))
    rows = classify(defs_a, defs_b)
    merged, moved, not_moved = build_candidate(sa, sha_sa, tree_a, lines_a, defs_a, tree_b, defs_b, rows)
    proof = prove(merged, defs_a, defs_b, rows, not_moved)
    cand = shadow / "merged" / f"{a.stem}__MERGE_CANDIDATE.py"
    cand.parent.mkdir()
    cand.write_text(merged, encoding="utf-8")
    after = {k: sha256_file(Path(k)) for k in before}
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    pay = {"schema": SCHEMA, "utc": stamp, "shadow": str(shadow), "candidate": str(cand),
           "a": {"path": str(a), "sha256": before[str(a)], **meta_a},
           "b": {"path": str(b), "sha256": before[str(b)], **meta_b},
           "originals_unchanged": before == after, "counts": counts, "rows": rows,
           "moved": moved, "not_moved": not_moved, "proof": proof,
           "warnings": [f"{x} 是薄尾(從前版 import / glob),只比得到它自己覆寫的定義;先跑 token 工具 chain 看全鏈"
                        for x, m in (("A", meta_a), ("B", meta_b)) if m["thin_tail"]]}
    (shadow / "PLAN.json").write_text(json.dumps(pay, ensure_ascii=False, indent=1), encoding="utf-8")
    return pay


def render(p: dict) -> str:
    c = p["counts"]
    lines = [f"[{NAME} {VERSION}] {p['proof']['verdict']} · 原檔未動 {p['originals_unchanged']} · 讀法 {p['a']['backend']}",
             f"  A {Path(p['a']['path']).name} ({p['a']['top_defs']} 頂層定義) · B {Path(p['b']['path']).name} ({p['b']['top_defs']})",
             "  " + " · ".join(f"{k} {v}" for k, v in sorted(c.items())),
             f"  已注入 {len(p['moved'])} · 未遷 {len(p['not_moved'])} · A 定義原樣保留 {p['proof']['a_defs_kept']}/{p['proof']['a_defs']}"]
    for x in p["not_moved"][:12]:
        lines.append(f"    [未遷] {x['qual']}: {x['why']}")
    if len(p["not_moved"]) > 12:
        lines.append(f"    …另 {len(p['not_moved']) - 12} 件見 PLAN.json")
    lines += [f"  [警告] {w}" for w in p["warnings"]]
    lines.append(f"  影子區 {p['shadow']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 自測(合成夾具;不碰真樹)
A_SRC = '''"""A 版。"""
import json
from pathlib import Path

ROOT = "/data/a"


def same(x):
    return x + 1


def doc_only(x):
    """舊說明。"""
    return x * 2


def path_of(name):
    return Path("/srv/old") / name


def sig_changed(a, b):
    return a - b


def only_a():
    return "a"


class Box:
    def put(self, v):
        return [v]

    def get(self):
        return 1


def main():
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

B_SRC = '''"""B 版。"""
import json
import os
from pathlib import Path

ROOT = "/data/b"
LIMIT = 10


def same(x):
    return x + 1


def doc_only(x):
    """新說明。"""
    return x * 2


def path_of(name):
    return Path("/srv/new") / name


def sig_changed(a, b, c=0):
    return a - b - c


def only_b_ok(p):
    return os.path.basename(p)


def only_b_risky():
    return LIMIT * 2


class Box:
    def put(self, v):
        return [v]

    def get(self):
        return 2

    def clear(self):
        return None


def main():
    return 0
'''


def selftest() -> int:
    fails, total = [], [0]

    def chk(name, cond, note=""):
        total[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        a, b = T / "X_ENG001_Demo_v0100.py", T / "X_ENG001_Demo_v0101.py"
        a.write_text(A_SRC, encoding="utf-8")
        b.write_text(B_SRC, encoding="utf-8")
        p = run(a, b, out_root=T / "shadow")
        cls = {r["qual"]: r["class"] for r in p["rows"]}
        mode = (Path(p["shadow"]) / "orig" / ("A__" + a.name)).stat().st_mode
        chk("① 原檔 sha256 前後一致;影子副本唯讀(看權限位,root 也照驗)",
            p["originals_unchanged"] and not mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), oct(mode & 0o777))
        chk("② 分類:SAME / DOC_ONLY / SAME_SIG_DIFF_BODY / DIFF_SIG / ONLY_A / ONLY_B 各就各位",
            cls["same"] == "SAME" and cls["doc_only"] == "DOC_ONLY" and cls["path_of"] == "SAME_SIG_DIFF_BODY"
            and cls["sig_changed"] == "DIFF_SIG" and cls["only_a"] == "ONLY_A" and cls["only_b_ok"] == "ONLY_B"
            and cls["Box.clear"] == "ONLY_B" and cls["Box.get"] == "SAME_SIG_DIFF_BODY", str(sorted(p["counts"].items())))
        near = {r["qual"]: r["near"] for r in p["rows"]}
        chk("③ 負控(L75):path_of 只差一條路徑字串 → 遮罩後「近似」,但**不准去重**(B 版列未遷)",
            near["path_of"] and any(x["qual"] == "path_of" for x in p["not_moved"]))
        merged = Path(p["candidate"]).read_text(encoding="utf-8")
        mt = ast.parse(merged)
        names = [s.name for s in mt.body if isinstance(s, DEF_NODES)]
        guard = _main_guard_line(mt)
        ob = next(s for s in mt.body if isinstance(s, ast.FunctionDef) and s.name == "only_b_ok")
        chk("④ ONLY_B 注入且排在 __main__ 之前;B 才有的 import os 併進來",
            "only_b_ok" in names and guard and ob.lineno < guard and "import os" in merged)
        chk("⑤ RISK:only_b_risky 用到 B 才有的常數 LIMIT → 不搬,列未遷並寫原因",
            "only_b_risky" not in names and any("LIMIT" in x["why"] for x in p["not_moved"]))
        chk("⑥ 不往既有類別注入方法(Box.clear 列未遷);模組層常數差異(ROOT/LIMIT)不代判",
            any(x["qual"] == "Box.clear" for x in p["not_moved"]) and sum("模組層" in x["qual"] for x in p["not_moved"]) == 2)
        chk("⑦ 證明:合併候選 parse + compile 過;A 定義全數原樣保留;有未遷 → BLOCKED_NEEDS_RULING(不是 PROVEN)",
            p["proof"]["compile"] and p["proof"]["a_defs_kept"] == p["proof"]["a_defs"] and not p["proof"]["b_unaccounted"]
            and p["proof"]["verdict"] == "BLOCKED_NEEDS_RULING")
        c = T / "X_ENG002_Same_v0101.py"
        c.write_text(A_SRC, encoding="utf-8")
        p2 = run(a, c, out_root=T / "shadow")
        chk("⑧ 正控:A 對 A 的副本 → 全 SAME · PROVEN_ZERO_LOSS · 合併候選與 A 位元組相同",
            set(p2["counts"]) == {"SAME"} and p2["proof"]["verdict"] == "PROVEN_ZERO_LOSS"
            and Path(p2["candidate"]).read_text(encoding="utf-8") == A_SRC)
        try:
            shadow_a = Path(p["shadow"]) / "orig" / ("A__" + a.name)
            tree_a, lines_a, defs_a, _ = load_defs(shadow_a)
            tree_b, _, defs_b, _ = load_defs(Path(p["shadow"]) / "orig" / ("B__" + b.name))
            build_candidate(shadow_a, "0" * 64, tree_a, lines_a, defs_a, tree_b, defs_b, p["rows"])
            caught = False
        except RuntimeError as exc:
            caught = "環繞斷言" in str(exc)
        chk("⑨ 環繞斷言會咬:計畫 sha 對不上影子 A → 拒絕注入", caught)
        d = T / "X_ENG003_Thin_v0102.py"
        d.write_text('import glob\n_STEM = "X_ENG003_Thin"\nP = sorted(glob.glob(_STEM + "_v*.py"))\n\n\ndef f():\n    return 1\n',
                     encoding="utf-8")
        meta = thin_tail(d)
        chk("⑩ 薄尾偵測(樹外退回字面判準):家族名與 `_v*` 拆開寫(_STEM + \"_v*.py\")也要抓到;出處寫明",
            meta["thin_tail"] and meta["how"].startswith("字面判準"), meta["how"])
        chk("⑪ 兩次跑各落新影子夾(不覆蓋舊影子)", p["shadow"] != p2["shadow"])
        try:
            resolve_input(T / "nope.py")
            absent = False
        except FileNotFoundError as exc:
            absent = "試過" in str(exc)
        chk("⑬ 經 VCGC run 時 cwd = 引擎夾:相對路徑依序試 目前目錄 → 倉根 → VIA 根;找不到回 ABSENT 並列出試過哪裡(不丟 traceback)",
            absent and resolve_input(a) == a.resolve())
    here = Path(__file__).resolve().parent
    body, tail = here / "CGC_MDL279_MCPServer_v0100.py", here / "CGC_MDL279_MCPServer_v0102.py"
    if via_root(here) and body.is_file() and tail.is_file():
        tb, tt = thin_tail(body), thin_tail(tail)
        chk("⑫ 真樹整合:薄尾判定問的是鎖版 token 工具的 chain(不另寫尺)· MCP v0100 = 本體 · v0102 = 薄尾(釘名前版)",
            tb["how"].startswith("chain(") and tt["how"].startswith("chain(") and not tb["thin_tail"] and tt["thin_tail"],
            f"(v0100 {tb.get('link')} · v0102 {tt.get('link')})")
    else:
        print("  [SKIP] ⑫ 真樹整合:不在 VIA 樹內(缺件不是壞掉)")
    bad = len(fails)
    print(f"  [計] {total[0]} 檢 OK {total[0] - bad} · FAIL {bad} · 讀法 {'libcst' if cst else 'stdlib-ast(LibCST 未安裝)'}")
    print(f"[{'PASS' if not bad else 'FAIL'}] {NAME} {VERSION} --selftest · {total[0] - bad}/{total[0]}", flush=True)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=f"{NAME} {VERSION}:影子隔離 + 逐定義比對 + 零遺失證明(只寫 VIA_Reports/shadow_merge)")
    ap.add_argument("verb", nargs="?", choices=("compare", "selftest", "help"), default="help")
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    g = ap.parse_args()
    if g.selftest or g.verb == "selftest":
        print(f"=== {NAME} {VERSION} 自測(合成夾具;零網路;真樹只讀)===")
        return selftest()
    if g.verb != "compare" or not (g.a and g.b):
        ap.print_usage()
        return 2
    try:
        p = run(Path(g.a), Path(g.b), Path(g.out) if g.out else None)
    except FileNotFoundError as exc:
        print(f"[{NAME} {VERSION}] ABSENT · {exc}")
        return 3
    except SyntaxError as exc:
        print(f"[{NAME} {VERSION}] RED · 原檔語法錯,不比對:{exc.filename}:{exc.lineno} {exc.msg}")
        return 1
    print(json.dumps(p, ensure_ascii=False, indent=1) if g.json else render(p))
    if not p["originals_unchanged"]:
        return 2
    return 0 if p["proof"]["verdict"] == "PROVEN_ZERO_LOSS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
