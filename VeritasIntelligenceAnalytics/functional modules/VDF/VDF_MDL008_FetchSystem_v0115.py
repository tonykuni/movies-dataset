#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL008_FetchSystem v0115 — 薄尾(v0100–v0114 一字不動):擷取家改寫認得參數橋的相對寫法;夾具不准寫進倉內 db/

實錄(2026-11-28,交接閘 VDF 紅列 vdf_fetch_integration · 容器):`fetch test` 輸出 15/23 檔合格,缺的 8 檔全在
MDL002(1-3-YFinanceUniverse)· MDL003(1-4-SentimentMacro)· MDL006(1-6-FinancialModel)。三支子行程都 rc 0,
可是輸出落到倉內 functional modules/VDF/db/(gitignored,所以 repo_writes 也沒抓到),暫存擷取家裡一檔都沒有。
根因:參數橋 [VIA:GOV-PARAM:v0100] 把舊的絕對路徑常數(v0100 LEGACY_PREFIXES 認得、會改到 --home)換成
`_VDF_PARAM("_PROD_BASE", _VDF_VIA_ROOT_REL("module/VDF/dict"))`;常數不見了 → 改寫 0 處 → 那個夾不存在
→ 引擎退到 `Path(__file__).parent / "db"` = 倉內。MDL002 還讀到倉內舊料、印「已是最新 · 零寫檔」。
本版:
  ① 掛在定義那一層(v0105 的模組層 rewrite_tree_v0105;compile_engine 與兩個載入鉤都讀它):照 v0105 改完後,
     樹裡每個 `def _VDF_VIA_ROOT_REL(rel)` 開頭多一段 —— rel 是 `module/VDF/dict…` 或 `dict…`(就是 LEGACY_PREFIXES 去掉
     VIA 根的那兩段)就回 `--home` 下同一相對位置。常數呼叫與參數冊 via_root_rel 兩條路都收;其他相對路徑照原函式。
  ② 子行程從本版起(照 v0102 … v0111 的作法:呼叫期間 v0107 的 __file__ 指向本檔),① 才在子行程生效。
  ③ 整合測試另看倉內 functional modules/VDF/db/:測試期間有新增或改動的檔 → 記進 repo_writes、整體不過(不再漏抓)。
  自測(裁定甲):本版 + 直接前版 v0114(v0114 ⑥ 往下跑 v0113 鏈那一步不算進本版,照實印「未跑」)。
零網路自測;不設同意閘;不用 TA-Lib。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import contextlib
import importlib.util
import inspect
import io
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v0115"
ROOT_REL_FN = "_VDF_VIA_ROOT_REL"
LEGACY_RELS = ("module/VDF/dict", "dict")          # = v0100 LEGACY_PREFIXES 去掉 VIA 根
DB_GUARD = HERE / "db"                             # 引擎找不到擷取家時退回的倉內夾
SKIPPED = "[計] 裁定甲:v0113 以前的前版鏈不算進本版(未跑)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                  # v0114
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _find(attr: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if attr in vars(m):
            return m
        m = vars(m).get("PRIOR")
    raise LookupError(attr)


P111 = _find("run_v0111")
V0107, V0105, V0101 = P111.V0107, P111.V0105, P111.V0101
P113 = PRIOR.PRIOR
_REWRITE_V0105 = V0105.rewrite_tree_v0105
_RUN_V0111 = P111.PRIOR.PRIOR._RUN_V0107          # v0111 run 包的那一層(v0111 自己會把 __file__ 改回 v0111)
_IT_V0101 = V0101.integration_test_v0101


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _guard_stmts(arg: str, home: str) -> list:
    src = (f"_via_fx_r = str({arg}).replace('\\\\', '/').strip('/')\n"
           f"for _via_fx_pre in {LEGACY_RELS!r}:\n"
           f"    if _via_fx_r == _via_fx_pre or _via_fx_r.startswith(_via_fx_pre + '/'):\n"
           f"        return str(__import__('pathlib').Path({home!r}, *[x for x in _via_fx_r[len(_via_fx_pre):].split('/') if x]))\n")
    fn = ast.parse("def _f(" + arg + "):\n" + "".join("    " + ln + "\n" for ln in src.splitlines())).body[0]
    return fn.body


def rewrite_tree_v0115(tree, home) -> int:
    """v0105 那一套(舊絕對路徑 · output_hub)照跑,再把 _VDF_VIA_ROOT_REL 的舊佈局相對路徑導到 --home。回改寫筆數。"""
    n = _REWRITE_V0105(tree, home)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == ROOT_REL_FN and node.args.args \
                and not getattr(node, "_via_fx_v0115", False):
            body = _guard_stmts(node.args.args[0].arg, str(Path(home)))
            doc = node.body[:1] if node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) else []
            node.body = doc + body + node.body[len(doc):]
            node._via_fx_v0115 = True
            n += 1
    ast.fix_missing_locations(tree)
    return n


def run_v0115(*args, **kwargs):
    """同 v0111 run(叫它包的那一層);呼叫期間 v0107 的 __file__ 指向本檔 → 子行程 = 本版(① 在子行程生效)。結束還原。"""
    keep = V0107.__dict__.get("__file__")
    V0107.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0111(*args, **kwargs)
    finally:
        V0107.__dict__["__file__"] = keep


def _db_snapshot(root: Path) -> dict:
    out = {}
    if Path(root).is_dir():
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                p = Path(dp, f)
                try:
                    st = p.stat()
                except OSError:
                    continue
                out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


def integration_test_v0115(rows: list) -> dict:
    """v0101 整合測試照跑;另比對倉內 db/ 測試前後(新增 · 改動 = 夾具寫進倉內 → 不過)。"""
    before = _db_snapshot(DB_GUARD)
    rep = _IT_V0101(rows)
    after = _db_snapshot(DB_GUARD)
    touched = sorted(k for k, v in after.items() if before.get(k) != v)
    if touched:
        rep["repo_writes"] = sorted(set(rep.get("repo_writes") or []) | {f"db/{k}" for k in touched[:50]})
        rep["db_guard"] = {"root": "functional modules/VDF/db", "touched": len(touched)}
        rep["pass"] = False
    return rep


def _install_v0115() -> None:
    V0105.rewrite_tree_v0105 = rewrite_tree_v0115
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = P111.BASE.run = run_v0115
    V0105.run_v0105 = V0107.PRIOR.run_v0106 = V0107.run_v0107 = P111.PRIOR.PRIOR.run_v0109 = P111.PRIOR.run_v0110 = run_v0115
    V0101.integration_test_v0101 = integration_test_v0115


_install_v0115()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


_SKIP_CALLS = []


def _chain_skipped() -> int:
    _SKIP_CALLS.append(1)                          # v0114 ⑥ 把前版輸出收進自己的緩衝,另記一筆才看得到
    print("  " + SKIPPED, flush=True)
    return 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(裁定甲:本版 + 直接前版 v0114 · 零網路)===", flush=True)
    with tempfile.TemporaryDirectory(prefix="mdl008_v0115_") as td:
        home = Path(td) / "dict"
        src = ("def _VDF_VIA_ROOT_REL(rel):\n    '''doc'''\n    return '/nowhere/' + rel\n"
               "A = _VDF_VIA_ROOT_REL('module/VDF/dict')\nB = _VDF_VIA_ROOT_REL('module\\\\VDF\\\\dict\\\\1-3-X')\n"
               "C = _VDF_VIA_ROOT_REL('supportive modules/x')\nD = _VDF_VIA_ROOT_REL('dict/0-1-L')\nE = _VDF_VIA_ROOT_REL('dictionary')\n"
               f"F = {(P111.BASE.LEGACY_PREFIXES[0] + chr(92) + '1-4-S')!r}\n"          # 舊絕對常數取自 v0100 本身(本檔不寫本機路徑)
               "_hub = __import__('pathlib').Path('/elsewhere') / 'output_hub'\n")
        tree = ast.parse(src)
        n = V0105.rewrite_tree_v0105(tree, home)
        g = {}
        exec(compile(tree, "<synthetic>", "exec"), g)
        want = {"A": str(home), "B": str(home / "1-3-X"), "C": "/nowhere/supportive modules/x", "D": str(home / "0-1-L"),
                "E": "/nowhere/dictionary", "F": str(home / "1-4-S"), "_hub": home / "output_hub"}
        got = {k: g[k] for k in want}
        chk("① 合成樹:module/VDF/dict · dict 兩種舊佈局(含反斜線)→ --home 同一位置;其他相對路徑 · 字首像的字照原函式;"
            "舊絕對常數與 output_hub 照 v0105", got == want and n >= 3, (n, {k: v for k, v in got.items() if v != want[k]}))
        n2 = V0105.rewrite_tree_v0105(tree, home)
        chk("① b 同一棵樹再改一次不重複插段(冪等)", sum(1 for x in ast.walk(tree) if getattr(x, "_via_fx_v0115", False)) == 1, n2)
        book = PRIOR.load_book() if callable(getattr(PRIOR, "load_book", None)) else V0101.load_book_v0101()
        files = {r["id"]: r["file"] for r in book["engines"] if r["id"] in ("002", "003", "006")}
        real = {}
        for eid, fn in sorted(files.items()):
            p = HERE / fn
            t = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            V0105.rewrite_tree_v0105(t, home)
            fd = [x for x in t.body if isinstance(x, ast.FunctionDef) and x.name == ROOT_REL_FN]
            if not fd:
                real[eid] = "no-fn"
                continue
            ns = {"__file__": str(p)}
            exec(compile(ast.Module(body=fd, type_ignores=[]), str(p), "exec"), ns)
            real[eid] = ns[ROOT_REL_FN]("module/VDF/dict") == str(home) and ns[ROOT_REL_FN]("module/VDF/dict/1-6-F") == str(home / "1-6-F")
        chk("② 真引擎(擷取冊 002 · 003 · 006 現役檔)改寫後 _VDF_VIA_ROOT_REL('module/VDF/dict') = --home", len(real) == 3 and all(v is True for v in real.values()), real)
        seen = []
        keep_run = globals()["_RUN_V0111"]
        try:
            globals()["_RUN_V0111"] = lambda *a, **k: seen.append(V0107.__dict__.get("__file__")) or ["ran"]
            r = V0101.run_v0101([], "fixture", home)
        finally:
            globals()["_RUN_V0111"] = keep_run
        chk("③ 跑子行程時 v0107 的 __file__ = 本檔(子行程從本版起)· 跑完還原", r == ["ran"] and seen == [str(Path(__file__).resolve())]
            and V0107.__dict__.get("__file__") != str(Path(__file__).resolve()), seen)
        keep_guard, keep_it = globals()["DB_GUARD"], globals()["_IT_V0101"]
        gdir = Path(td) / "db"
        gdir.mkdir()
        (gdir / "old.parquet").write_bytes(b"x")
        try:
            globals()["DB_GUARD"] = gdir
            def _leaky(rows):
                (gdir / "1-3-YFinanceUniverse").mkdir(exist_ok=True)
                (gdir / "1-3-YFinanceUniverse" / "YFinanceData.parquet").write_bytes(b"y")
                return {"pass": True, "repo_writes": []}
            globals()["_IT_V0101"] = _leaky
            bad = V0101.integration_test_v0101([])
            globals()["_IT_V0101"] = lambda rows: {"pass": True, "repo_writes": []}
            good = V0101.integration_test_v0101([])
        finally:
            globals()["DB_GUARD"], globals()["_IT_V0101"] = keep_guard, keep_it
        chk("④ 整合測試期間倉內 db/ 多了檔 → repo_writes 點名 · 不過;沒寫 → 照原判", bad["pass"] is False
            and bad["repo_writes"] == ["db/1-3-YFinanceUniverse/YFinanceData.parquet"] and good == {"pass": True, "repo_writes": []}, (bad, good))
    keep_sel = P113.selftest
    _SKIP_CALLS.clear()
    P113.selftest = _chain_skipped
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc4 = PRIOR.selftest()
    finally:
        P113.selftest = keep_sel
        _install_v0115()
    out = buf.getvalue()
    fails = [ln.strip()[:160] for ln in out.splitlines() if "[FAIL]" in ln]
    chk("⑤ 直接前版 v0114 ①–⑦ 全過(⑥ 的 v0113 鏈換成「未跑」,裁定甲)", rc4 == 0 and not fails and _SKIP_CALLS == [1], (rc4, fails[:3], len(_SKIP_CALLS)))
    print("  [略] v0114 ⑥ 前版 v0113 自測:不算進本版(裁定甲 · 未跑);要看仍可各自 --selftest", flush=True)
    sig = inspect.signature(main)
    pub = [k for k, v in vars(PRIOR).items() if not k.startswith("_") and callable(v)]
    me = sys.modules.get(__name__)
    chk("⑥ main(argv=None) · v0114 公開名稱從本版都拿得到(TAILAPI)· 本版裝回(改寫 · 子行程 · 整合測試)", list(sig.parameters) == ["argv"]
        and all(hasattr(me, k) for k in pub) and V0105.rewrite_tree_v0105 is rewrite_tree_v0115 and V0101.run_v0101 is run_v0115
        and V0101.integration_test_v0101 is integration_test_v0115)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器真的載到 · 網路工具橋在位 · 零 TA-Lib · 不設同意閘", VIA_ACCEL is not None and VIA_NET_TOOL_PATH is not None
        and text.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", text, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
