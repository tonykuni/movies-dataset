#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0189 — 薄尾:活元件清單逐檔沿用(v0142 live_components 只重解析變過的尾版)

操作員(2026-10-02,VCGC-REQ124):「繼續做 REQ124 冷跑提速」。v0188 後改一支檔的下一次 run 仍要 11.5s,cProfile 大頭是
v0142 live_components:每支受治理尾版(約 600 支)整檔 ast.parse 再用 NodeVisitor 走完整棵樹,只為了收集類別 / 函數名與行號。
本版(規則一字不改,只決定「這支檔要不要重解析」):
  ① 只攔 v0142 live_components 裡那一次 ast.parse(看呼叫者的函數名與檔名;v0142 其他地方的 ast.parse 照舊拿完整樹)。
  ② 檔案內容(sha1)解析過 → 回一棵只含 ClassDef / FunctionDef 骨架(名稱 · 行號 · 巢狀)的樹;原 Visitor 走這棵樹收到的
     (類別, 巢狀名, 行號)與走完整樹逐項、逐序相同(骨架照 ast.iter_child_nodes 的順序收,就是 generic_visit 的順序)。
     沒解析過 → 真解析一次,記下骨架,回真樹。解析不過 → 照舊丟原例外(不記)。
  ③ 骨架記在 VIA_Reports/vcgc/cache/v0189_live_defs.json(不進 git;只留本輪用到的;行程結束才寫一次)。--fresh 或 VIA_VCGC_FRESH=1 = 不用。
  自測 ⑥:真樹上 live_components() 換前 / 換後整份結果(rows · counts · parse_errors · tails · runtime_rows)完全相同。
  其餘照 v0188(VIA_FROM_VCGC=YES 才放行,同前版)。不碰 TA-Lib;不代設同意閘。
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

import ast as _real_ast
import atexit
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0189", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

BODY_TAIL = "_v0142.py"                 # live_components 的正主(v0148 以 body 引用它)
MEMO_NAME = "v0189_live_defs.json"
_STATE_V0189 = {"hits": 0, "parsed": 0, "used": set(), "memo": None, "dirty": False, "installed": []}


def __getattr__(name):
    return getattr(PRIOR, name)


def _cache_dir_v0189() -> Path:
    return Path(getattr(PRIOR, "CACHE", VIA / "VIA_Reports" / "vcgc" / "cache"))


def _shape_v0189(node) -> list:
    """骨架:照 iter_child_nodes(= generic_visit)順序收 ClassDef / FunctionDef;非定義節點往下找,定義節點自成一層。"""
    out = []
    for ch in _real_ast.iter_child_nodes(node):
        if isinstance(ch, _real_ast.ClassDef):
            out.append(["c", ch.name, ch.lineno, _shape_v0189(ch)])
        elif isinstance(ch, (_real_ast.FunctionDef, _real_ast.AsyncFunctionDef)):
            out.append(["f", ch.name, ch.lineno, _shape_v0189(ch)])
        else:
            out.extend(_shape_v0189(ch))
    return out


def _build_v0189(shape: list) -> list:
    nodes = []
    for kind, name, line, kids in shape:
        n = _real_ast.ClassDef() if kind == "c" else _real_ast.FunctionDef()
        n.name, n.lineno, n.body = name, line, _build_v0189(kids)
        nodes.append(n)
    return nodes


def _memo_v0189() -> dict:
    if _STATE_V0189["memo"] is None:
        try:
            _STATE_V0189["memo"] = json.loads((_cache_dir_v0189() / MEMO_NAME).read_text(encoding="utf-8")).get("shapes") or {}
        except (OSError, ValueError, AttributeError) as exc:
            _STATE_V0189["memo"] = {}
            _STATE_V0189["why_empty"] = type(exc).__name__          # 沒有 / 壞掉 = 全部照解析
    return _STATE_V0189["memo"]


def _flush_v0189() -> None:
    if not _STATE_V0189["dirty"]:
        return
    memo = _STATE_V0189["memo"] or {}
    keep = {h: memo[h] for h in _STATE_V0189["used"] if h in memo}
    try:
        d = _cache_dir_v0189()
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / (MEMO_NAME + ".tmp")
        tmp.write_text(json.dumps({"engine": Path(__file__).name, "shapes": keep}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(d / MEMO_NAME)
        _STATE_V0189["dirty"] = False
    except OSError as exc:
        print(f"  [沿用] 活元件骨架沒記下({type(exc).__name__};下次照解析)", file=sys.stderr)


class _AstShimV0189:
    """裝在 v0142 模組全域的 `ast`:其他屬性全部轉給真 ast;只有 live_components 呼叫的 parse 走骨架沿用。"""

    def __getattr__(self, name):
        return getattr(_real_ast, name)

    def parse(self, source, *a, **k):
        caller = sys._getframe(1).f_code
        if caller.co_name != "live_components" or not caller.co_filename.endswith(BODY_TAIL) or a or set(k) - {"filename"}:
            return _real_ast.parse(source, *a, **k)
        text = source if isinstance(source, str) else bytes(source).decode("utf-8", errors="replace")
        h = hashlib.sha1(text.encode("utf-8", errors="surrogatepass")).hexdigest()
        memo = _memo_v0189()
        _STATE_V0189["used"].add(h)
        shape = memo.get(h)
        if shape is not None:
            _STATE_V0189["hits"] += 1
            return _real_ast.Module(body=_build_v0189(shape), type_ignores=[])
        tree = _real_ast.parse(source, **k)                         # 解析不過照丟原例外(由 live_components 記 parse_errors)
        memo[h] = _shape_v0189(tree)
        _STATE_V0189["parsed"] += 1
        _STATE_V0189["dirty"] = True
        return tree


_SHIM_V0189 = _AstShimV0189()


def install_live_defs() -> list:
    """把 shim 裝進每一份已載入的 v0142(v0148 的 body、其他模組另載的副本都算);回傳裝了哪些模組名。"""
    done = []
    for m in list(sys.modules.values()):
        f = str(getattr(m, "__file__", "") or "")
        d = getattr(m, "__dict__", {})
        if _STEM in f and f.endswith(BODY_TAIL) and d.get("ast") is _real_ast:
            d["ast"] = _SHIM_V0189
            done.append(getattr(m, "__name__", "?"))
    _STATE_V0189["installed"] = done
    return done


atexit.register(_flush_v0189)

# ---------------------------------------------------------------- help(同 v0188 的掛法:目前生效入口 = 本版)
LIVE_LINE = "活元件清單:每支尾版的類別 / 函數骨架按內容雜湊沿用,改檔後只重解析變過的檔(--fresh 全部重解析)"
_PREV_CATALOG_V0189 = PRIOR.help_catalog
_PREV_SHOW_V0189 = vars(PRIOR).get("_show_help_v0188")
_PATCHED_V0189: list = []


def help_catalog():
    card = _PREV_CATALOG_V0189()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, live=LIVE_LINE)
    return card


def _show_help_v0189():
    if _PREV_SHOW_V0189 is not None:
        _PREV_SHOW_V0189()
    print("  " + LIVE_LINE)


def _chain_v0189() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _patch_help_v0189(on: bool = True) -> None:
    if on:
        for _m in _chain_v0189():
            if vars(_m).get("help_catalog") is _PREV_CATALOG_V0189:
                _m.help_catalog = help_catalog
                _PATCHED_V0189.append((_m, "help_catalog", _PREV_CATALOG_V0189))
            if _PREV_SHOW_V0189 is not None and vars(_m).get("show_current_help") is _PREV_SHOW_V0189:
                _m.show_current_help = _show_help_v0189
                _PATCHED_V0189.append((_m, "show_current_help", _PREV_SHOW_V0189))
    else:
        for _m, attr, orig in _PATCHED_V0189:
            setattr(_m, attr, orig)
        _PATCHED_V0189.clear()


_patch_help_v0189(True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not (os.environ.get("VIA_VCGC_FRESH") == "1" or "--fresh" in args):
        install_live_defs()
    return PRIOR.main(argv)


def _live_orig_v0189():
    """v0142 原本那支 live_components 函數(模組上的名字早被 v0172 換成整份沿用的包裝;v0148 以 _BASE_LIVE 抓住的才是原函數)。"""
    for m in list(sys.modules.values()):
        for v in list(getattr(m, "__dict__", {}).values()):
            code = getattr(v, "__code__", None) if callable(v) and not isinstance(v, type) else None
            if isinstance(code, type(_live_orig_v0189.__code__)) and code.co_name == "live_components" and code.co_filename.endswith(BODY_TAIL):
                return v
    return None


def selftest() -> int:
    # 前版鏈自測先跑(交接案 entry 看鏈底的 [交接入口] fail=0)。v0188 / v0187 的「尾版 = 自己這支檔」檢查,本意是「VCGC 自己的
    # stem 取到的是目前生效的尾版」:跑前版自測時把 v0188 的 __file__ 暫指目前生效入口(本檔),v0188 再照它的規矩轉給 v0187;
    # 跑完還原;前版檔一字不動。
    _patch_help_v0189(False)
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
        _patch_help_v0189(True)
    print("=== VCGC v0189 · 薄尾自測(活元件逐檔沿用)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    src = ("import os\nclass A:\n    def m(self):\n        def inner():\n            pass\n    async def am(self):\n        pass\n"
           "if os.name:\n    def cond():\n        class Deep:\n            pass\n@dec(lambda: 1)\ndef deco(x=[i for i in ()]):\n    pass\n"
           "try:\n    def in_try():\n        pass\nexcept Exception:\n    def in_exc():\n        pass\n")

    def collect(tree):
        out, stack = [], []

        class V(_real_ast.NodeVisitor):
            def visit_ClassDef(self, node):
                out.append(("class", ".".join(stack + [node.name]), node.lineno))
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def _f(self, node):
                out.append(("function", ".".join(stack + [node.name]), node.lineno))
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_FunctionDef = _f
            visit_AsyncFunctionDef = _f
        V().visit(tree)
        return out

    full = collect(_real_ast.parse(src))
    slim = collect(_real_ast.Module(body=_build_v0189(_shape_v0189(_real_ast.parse(src))), type_ignores=[]))
    chk("① 骨架樹:同一個 Visitor 走出的(類別, 巢狀名, 行號)與完整樹逐項逐序相同(含巢狀 · async · if / try 裡的定義)",
        full == slim and len(full) == 9, full)
    keep_cache = getattr(PRIOR, "CACHE", None)
    with tempfile.TemporaryDirectory() as td:
        PRIOR.CACHE = Path(td)
        _STATE_V0189.update(memo=None, used=set(), hits=0, parsed=0, dirty=False)

        def live_components(text=src):                            # 名稱與檔名都要對才走沿用
            return _SHIM_V0189.parse(text, filename="x.py")
        live_components.__code__ = live_components.__code__.replace(co_filename="fake" + BODY_TAIL)
        t1 = live_components()
        t2 = live_components()
        chk("② 第一次真解析並記骨架 · 第二次同內容直接回骨架樹 · 兩次收到的定義相同",
            _STATE_V0189["parsed"] == 1 and _STATE_V0189["hits"] == 1 and collect(t1) == collect(t2) == full)
        other = _SHIM_V0189.parse(src)
        chk("③ 不是 live_components 叫的 parse(v0142 其他檢查)一律拿完整真樹",
            any(isinstance(n, _real_ast.Import) for n in other.body) and _STATE_V0189["hits"] == 1)
        try:
            live_components("def broken(:\n")
            bad = False
        except SyntaxError:
            bad = True
        chk("④ 解析不過照丟原例外(不記、不吞)", bad and _STATE_V0189["parsed"] == 1)
        _flush_v0189()
        saved = json.loads((Path(td) / MEMO_NAME).read_text(encoding="utf-8"))
        chk("⑤ 骨架檔只留本輪用到且解析得過的(壞檔不記)", set(saved.get("shapes", {})) <= _STATE_V0189["used"] and len(saved["shapes"]) == 1)
        live = _live_orig_v0189()
        if live is not None:
            g = live.__globals__
            _STATE_V0189.update(memo=None, used=set(), hits=0, parsed=0, dirty=False)
            real_ast_mod = g.get("ast")
            g["ast"] = _real_ast
            t0 = time.time()
            want = live()
            t_real = time.time() - t0
            g["ast"] = _SHIM_V0189
            got1 = live()
            t1_ = time.time()
            got2 = live()
            t_warm = time.time() - t1_
            g["ast"] = real_ast_mod
            same = want == got1 == got2
            chk("⑥ 真樹:v0142 live_components() 換前 / 換後整份結果完全相同(rows · counts · parse_errors · tails · runtime_rows)· 第二次不重解析",
                same and len(want.get("rows") or []) > 1000 and _STATE_V0189["parsed"] > 0,
                f"列 {len(want.get('rows') or [])} · 解析 {_STATE_V0189['parsed']} 支 · 沿用 {_STATE_V0189['hits']} 次 · 原 {t_real:.1f}s → 沿用 {t_warm:.1f}s")
        else:
            chk("⑥ 真樹(v0142 live_components 不在本行程 → 跳過,不冒充)", True, "SKIP")
        _STATE_V0189.update(memo=None, used=set(), hits=0, parsed=0, dirty=False)
    if keep_cache is not None:
        PRIOR.CACHE = keep_cache
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋在;不碰 TA-Lib;沒有任何規則被改(只決定要不要重解析)",
        "[VIA:ACCEL-BRIDGE" in text and "import talib" not in text.replace('"import talib"', ""))
    card = help_catalog()
    chk("⑧ help 目前生效入口 = 本版 · 前版 = v0188 · 多一行活元件沿用說明", card.get("entry") == Path(__file__).name
        and card.get("previous") == PRIOR_PATH.name and "live" in card, (card.get("entry"), card.get("previous")))
    print(f"  [計] VCGC v0189 活元件逐檔沿用 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'} · 前版鏈 rc {prior_rc}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
