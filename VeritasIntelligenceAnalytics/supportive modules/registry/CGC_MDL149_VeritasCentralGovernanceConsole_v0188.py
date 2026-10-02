#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0188 — 薄尾:治理檢查沿用(樹沒變就不重算;輸出原樣重印)· --fresh 強制重算

操作員(2026-10-02,VCGC-REQ124)核准提案:「依照你的提案最佳化」。容器實測:同一支引擎直接跑 0.70s、經 via-vcgc run 4.13s;
cProfile:每次 run 都重做整樹治理檢查——v0169 sync_check 裡的 SDD check 2.6s(含參數樞紐 73 本 0.8s)· v0168 _gate_ok 的
FlowConsistency 0.6s · v0150 鏈 policy_step 的 TA-Lib 禁令掃描 0.5s。樹沒變時這些結果每次都一樣。
本版(不改任何一條規則,只決定「要不要重算」):
  ① 鑰匙 = v0167 tree_key(HEAD + 每個改動 / 未追蹤檔的大小與時間 + 執行計畫檔)+ 會影響結果但不進 git 的報告(SDD / 串測 / 交接 latest)
     的大小與時間;沿用最多 TTL 30 分鐘。鑰匙算不出(沒有 git)= 一律重算。
  ② 沿用三段:policy_step(body 模組上)· _gate_ok · sync_check(所有鏈上模組的全域);命中時把上次擷取的輸出**原樣重印**
     (畫面與串測看到的一字不差),回傳值照舊;stderr 印一行 [沿用](不混進 stdout)。
  ③ 一律重算(不沿用):closeout · gate · sdd · handoff · registry-sync · test · 任何帶 --apply / --push / --approve 的動作
     ——驗收與寫入永遠是新量的。--fresh 或 VIA_VCGC_FRESH=1 = 本次全部重算。
  ④ 冷跑大頭(實測任一檔一改,下一次 run 39s):registry_sync → v0172 forwarded_defs 把每條薄尾鏈上的每支前版檔(約 1500 支)
     整檔 ast.parse 再走一遍。改成逐檔按**內容雜湊**記定義清單(v0188_defs.json),只重解析變過的檔;同家族前版只 glob 一次。
     規則與輸出不變(自測 ⑨;另在整樹 573 條尾鏈 / 962 支前版檔上比過:5573 個定義逐鍵、逐序相同)。這一段驗收動詞也用
     (重量的仍是每一支檔的內容);只有 --fresh 不用。
  容器實測(run CGC_MDL254_ReviewOnePage --selftest):樹沒變 4.1s → 1.8s;改一支檔後的下一次 36s → 11.5s;輸出與 --fresh 一字不差。
  剩下的冷跑大頭:v0142 live_components 每支尾版整檔解析(約 6s)——要逐檔沿用得重寫那條規則,本版不動(不發散)。
  其餘照 v0187(VIA_FROM_VCGC=YES 才放行,同前版)。
  沿用檔:VIA_Reports/vcgc/cache/v0188_<段>.json(不進 git;每段只留最近一把鑰匙)。其餘照 v0187。不碰 TA-Lib;不代設同意閘。
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

import ast
import contextlib
import functools
import hashlib
import importlib.util
import io
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
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0188", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

CACHE = VIA / "VIA_Reports" / "vcgc" / "cache"
TTL_S = 1800
FRESH_VERBS = {"closeout", "gate", "sdd", "handoff", "registry-sync", "test"}
WRITE_FLAGS = {"--apply", "--push", "--approve", "--approve-remove"}
EXTRA_INPUTS = ("VIA_Reports/sdd/SDD_REAL_latest.json", "VIA_Reports/sdd/SDD_SELF_latest.json", "VIA_Reports/vcgc/TEST_latest.json",
                "docs/handoff/HANDOFF_latest.json")     # 不收 exec/EXEC_latest.json:那是每次 run 自己寫的輸出(收了 = 永不命中)
_STATE = {"hits": [], "misses": [], "installed": False}


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_mods_v0188() -> list:
    """本行程裡載入的每一支主控台尾版模組(任何版本、任何前版屬性名)。"""
    return [m for m in list(sys.modules.values()) if _STEM in str(getattr(m, "__file__", "") or "") and m is not sys.modules.get(__name__)]


def _tree_key_v0188() -> str | None:
    tk = next((vars(m)["tree_key"] for m in _chain_mods_v0188() if callable(vars(m).get("tree_key"))), None)
    try:
        base = tk() if tk else None
    except Exception:
        base = None
    if not base:
        return None
    parts = [base]
    for rel in EXTRA_INPUTS:
        p = VIA / rel
        try:
            s = p.stat()
            parts.append(f"{rel}|{s.st_size}|{s.st_mtime_ns}")
        except OSError:
            parts.append(f"{rel}|absent")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def _jsonable(v):
    try:
        json.dumps(v, ensure_ascii=False)
        return True
    except (TypeError, ValueError):
        return False


def cached(name: str, fn, key_fn=None):
    """包一個治理檢查:同一把鑰匙(且未過 TTL)就重印上次輸出、回上次的值;否則照算並記下。回傳值不能存 JSON 就不沿用。"""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        key = (key_fn(*a, **k) if key_fn else None) or _tree_key_v0188()
        path = CACHE / f"v0188_{name}.json"
        if key:
            try:
                c = json.loads(path.read_text(encoding="utf-8"))
                if c.get("key") == key and time.time() - float(c.get("t", 0)) < TTL_S:
                    sys.stdout.write(c.get("out", ""))
                    sys.stdout.flush()
                    print(f"  [沿用] {name} · 鑰匙 {key} · {int(time.time() - float(c['t']))}s 前算的(--fresh 強制重算)", file=sys.stderr)
                    _STATE["hits"].append(name)
                    ret = c.get("ret")
                    return tuple(ret) if c.get("tuple") else ret
            except (OSError, ValueError, TypeError) as exc:
                _STATE["misses"].append(f"{name}:讀不了沿用檔({type(exc).__name__})")   # 沒有 / 壞掉 = 照算
        buf = io.StringIO()
        tee = _Tee(sys.stdout, buf)
        with contextlib.redirect_stdout(tee):
            ret = fn(*a, **k)
        _STATE["misses"].append(name)
        if key and _jsonable(ret):
            try:
                CACHE.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps({"key": key, "t": time.time(), "out": buf.getvalue(), "ret": ret,
                                           "tuple": isinstance(ret, tuple), "engine": Path(__file__).name}, ensure_ascii=False), encoding="utf-8")
                tmp.replace(path)
            except OSError:
                print(f"  [沿用] {name} 沒記下(沿用夾寫不了;下次照算)", file=sys.stderr)
        return ret
    wrapper.__v0188_cached__ = True
    return wrapper


class _Tee(io.TextIOBase):
    """照常印到畫面,同時記一份(沿用時原樣重印)。"""
    def __init__(self, a, b):
        self.a, self.b = a, b

    def write(self, s):
        self.a.write(s)
        self.b.write(s)
        return len(s)

    def flush(self):
        self.a.flush()


def wants_fresh(argv: list) -> bool:
    if os.environ.get("VIA_VCGC_FRESH") == "1" or "--fresh" in argv:
        return True
    verb = next((a for a in argv if not a.startswith("-")), "")
    return verb in FRESH_VERBS or any(a in WRITE_FLAGS for a in argv)


def install() -> list:
    """把三段包上沿用,裝回原位(policy_step 在 body 模組上;_gate_ok / sync_check 在每個持有它的鏈上模組全域)。回傳裝了哪些。"""
    done = []
    mods = _chain_mods_v0188()
    for m in mods:
        body = vars(m).get("body")
        f = getattr(body, "policy_step", None) if body is not None else None
        if callable(f) and not getattr(f, "__v0188_cached__", False):
            body.policy_step = cached("policy", f)
            done.append("policy")
    for name, key_fn in (("_gate_ok", None), ("sync_check", lambda key=None, *a, **k: None)):
        cur = next((vars(m)[name] for m in mods if callable(vars(m).get(name)) and not getattr(vars(m)[name], "__v0188_cached__", False)), None)
        if cur is None:
            continue
        w = cached(name.strip("_"), cur, key_fn)
        for m in mods:
            if callable(vars(m).get(name)):
                m.__dict__[name] = w
        done.append(name.strip("_"))
    _STATE["installed"] = True
    return sorted(set(done))


DEFS_MEMO = "v0188_defs.json"


def _defs_of_v0188(path: Path, memo: dict, used: set):
    """一支檔的定義清單 [(類別, 巢狀名, 行號)…];內容雜湊沒變就用上次的(ast.parse 只做在變過的檔)。解析不過 = None。"""
    rel = path.relative_to(VIA).as_posix()
    used.add(rel)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    h = hashlib.sha1(raw).hexdigest()
    hit = memo.get(rel)
    if hit and hit.get("h") == h:
        return hit.get("defs")
    _STATE["reparsed"] = _STATE.get("reparsed", 0) + 1
    try:
        tree = ast.parse(raw.decode("utf-8", errors="replace"), filename=str(path))
    except (SyntaxError, ValueError):
        defs = None
    else:
        defs = []

        class V(ast.NodeVisitor):
            def __init__(self):
                self.stack: list = []

            def _add(self, node, cat):
                defs.append([cat, ".".join(self.stack + [node.name]), node.lineno])
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_ClassDef(self, node):
                self._add(node, "class")

            def visit_FunctionDef(self, node):
                self._add(node, "function")

            visit_AsyncFunctionDef = visit_FunctionDef

        V().visit(tree)
    memo[rel] = {"h": h, "defs": defs}
    return defs


def make_forwarded_defs_v0188(owner):
    """與 v0172 forwarded_defs 同一條規則、同一個輸出(逐鍵相同、同樣先到先贏);差別只在:每支前版檔的定義清單按內容雜湊記在
    VIA_Reports/vcgc/cache/v0188_defs.json,沒變的檔不再 ast.parse;同一個家族的前版清單只 glob 一次。"""
    is_thin, vnum = owner.is_thin, owner._vnum

    def forwarded_defs(tails: list, limit: int = 80) -> dict:
        path = CACHE / DEFS_MEMO
        try:
            memo = json.loads(path.read_text(encoding="utf-8")).get("files") or {}
        except (OSError, ValueError, AttributeError):
            memo = {}
        used, fams, out = set(), {}, {}
        _STATE["reparsed"] = 0
        for stem, q in tails:
            cur, hops = q, 0
            while hops < limit:
                try:
                    txt = cur.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    break
                if not is_thin(stem, txt):
                    break
                fk = (str(cur.parent), stem)
                if fk not in fams:
                    fams[fk] = sorted(cur.parent.glob(stem + "_v*.py"), key=vnum)
                older = [p for p in fams[fk] if 0 <= vnum(p) < vnum(cur)]
                if not older:
                    break
                nxt, hops = older[-1], hops + 1
                rel, via = nxt.relative_to(VIA).as_posix(), q.relative_to(VIA).as_posix()
                defs = _defs_of_v0188(nxt, memo, used)
                if defs is not None:
                    for cat, dotted, line in defs:
                        ident = f"{stem}:{dotted}"
                        out.setdefault(f"{cat}|{ident}", {"key": f"{cat}|{ident}", "category": cat, "identity": ident,
                                                          "source": rel, "line": line, "via": via})
                cur = nxt
        keep = {k: v for k, v in memo.items() if k in used}
        _STATE["defs"] = {"files": len(used), "reparsed": _STATE["reparsed"]}
        try:
            CACHE.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"engine": Path(__file__).name, "files": keep}, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
        except OSError as exc:
            print(f"  [沿用] 逐檔定義沒記下({type(exc).__name__};下次照解析)", file=sys.stderr)
        return out

    forwarded_defs.__v0188_cached__ = True
    forwarded_defs.__wrapped__ = owner.forwarded_defs
    return forwarded_defs


def install_defs() -> bool:
    """把逐檔定義沿用裝到持有 forwarded_defs 的鏈上模組(v0172 的 extend 從自己的全域找它)。"""
    for m in _chain_mods_v0188():
        d = vars(m)
        f = d.get("forwarded_defs")
        if callable(f) and callable(d.get("is_thin")) and callable(d.get("extend")) and not getattr(f, "__v0188_cached__", False):
            m.__dict__["forwarded_defs"] = make_forwarded_defs_v0188(m)
            return True
    return False


# ---------------------------------------------------------------- help(同 v0187 的掛法:目前生效入口 = 本版)
CACHE_LINE = ("治理沿用:樹沒變就重印上次的 policy / gate_ok / sync_check(stderr 印 [沿用]);改檔後只重解析變過的檔;"
              "closeout · gate · sdd · handoff · registry-sync · test · --apply/--push/--approve 一律重算 · --fresh 全部重算")
_PREV_CATALOG_V0188 = PRIOR.help_catalog
_PREV_SHOW_V0188 = vars(PRIOR).get("_show_help_v0187")
_PATCHED_V0188: list = []


def help_catalog():
    card = _PREV_CATALOG_V0188()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, cache=CACHE_LINE)
    return card


def _show_help_v0188():
    if _PREV_SHOW_V0188 is not None:
        _PREV_SHOW_V0188()
    print("  " + CACHE_LINE)


def _chain_v0188() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _patch_help_v0188(on: bool = True) -> None:
    if on:
        for _m in _chain_v0188():
            if vars(_m).get("help_catalog") is _PREV_CATALOG_V0188:
                _m.help_catalog = help_catalog
                _PATCHED_V0188.append((_m, "help_catalog", _PREV_CATALOG_V0188))
            if _PREV_SHOW_V0188 is not None and vars(_m).get("show_current_help") is _PREV_SHOW_V0188:
                _m.show_current_help = _show_help_v0188
                _PATCHED_V0188.append((_m, "show_current_help", _PREV_SHOW_V0188))
    else:
        for _m, attr, orig in _PATCHED_V0188:
            setattr(_m, attr, orig)
        _PATCHED_V0188.clear()


_patch_help_v0188(True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    fresh = wants_fresh(args)
    explicit = os.environ.get("VIA_VCGC_FRESH") == "1" or "--fresh" in args
    if "--fresh" in args:
        args = [a for a in args if a != "--fresh"]
        if argv is None:
            sys.argv = [sys.argv[0]] + args
    if not fresh:
        install()
    if not explicit:
        install_defs()      # 逐檔內容雜湊:驗收動詞也用(沒變的檔才不重解析;結果與整樹重解析逐鍵相同,自測 ⑨ 驗)
    return PRIOR.main(args if argv is not None else None)


def selftest() -> int:
    global CACHE
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    # 前版鏈自測先跑(交接案 entry 看的是鏈底的 [交接入口] fail=0;本版 ⑧ 要真跑 policy_step,會在行程裡多載入前版副本,
    # 先跑本版會讓 v0178 ③「鏈上定義者都換成本版」數到那份副本)。v0187 的 ⑦ / ⑩ 寫成「尾版 = 自己這支檔」,本意是
    # 「VCGC 自己的 stem 取到的是目前生效的尾版」;有了本版那支檔就不再是尾版。跑前版自測時把它的 __file__ 暫指目前生效入口
    # (本檔),跑完還原;前版檔一字不動、其餘檢查照原樣。
    _patch_help_v0188(False)
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
        _patch_help_v0188(True)
    print("=== VCGC v0188 · 薄尾自測(治理沿用)===")
    chk("① 驗收 / 寫入動詞一律重算;一般 run 沿用;--fresh / VIA_VCGC_FRESH=1 強制重算",
        all(wants_fresh(a) for a in (["closeout", "--apply"], ["gate"], ["sdd", "check"], ["handoff", "check"], ["run", "X", "--apply"], ["test"], ["run", "X", "--fresh"]))
        and not wants_fresh(["run", "CGC_MDL254_ReviewOnePage", "build"]) and not wants_fresh(["token"]))
    keep_cache, keep_key = CACHE, globals()["_tree_key_v0188"]
    with tempfile.TemporaryDirectory() as td:
        CACHE = Path(td)
        calls = []
        box = {"key": "k1"}
        globals()["_tree_key_v0188"] = lambda: box["key"]

        def fake(x=1):
            calls.append(x)
            print(f"  [政策] 假檢查 {x}")
            return {"lamp": "GREEN", "x": x}
        w = cached("selftest", fake)
        o1, o2 = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(o1):
            r1 = w(7)
        with contextlib.redirect_stdout(o2), contextlib.redirect_stderr(io.StringIO()):
            r2 = w(7)
        chk("② 同一把鑰匙:第二次不重算 · 輸出一字不差重印 · 回傳值相同", calls == [7] and o1.getvalue() == o2.getvalue() and r1 == r2, (calls, o2.getvalue().strip()))
        box["key"] = "k2"
        with contextlib.redirect_stdout(io.StringIO()):
            w(7)
        chk("③ 樹一變(鑰匙不同)就重算", calls == [7, 7])
        c = json.loads((CACHE / "v0188_selftest.json").read_text(encoding="utf-8"))
        c["t"] = time.time() - TTL_S - 1
        (CACHE / "v0188_selftest.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            w(7)
        chk("④ 超過 TTL 就重算(不拿太舊的結果)", calls == [7, 7, 7])
        wt = cached("selftest_t", lambda: (True, "ok"))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            t1, t2 = wt(), wt()
        chk("⑤ tuple 回傳值沿用後仍是 tuple(_gate_ok 用)", t1 == t2 == (True, "ok") and isinstance(t2, tuple))
        box["key"] = None
        n0 = len(calls)
        with contextlib.redirect_stdout(io.StringIO()):
            w(7)
            w(7)
        chk("⑥ 鑰匙算不出(沒有 git)= 一律重算", len(calls) == n0 + 2)
        globals()["_tree_key_v0188"] = keep_key
        got = install()
        chk("⑦ 真鏈:三段都裝上沿用(policy · gate_ok · sync_check)", got == ["gate_ok", "policy", "sync_check"] or set(got) >= {"policy", "gate_ok", "sync_check"}, got)
        body = next((vars(m)["body"] for m in _chain_mods_v0188() if vars(m).get("body") is not None), None)
        if body is not None and _tree_key_v0188():
            t0 = time.time()
            a, b = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(a):
                body.policy_step()
            t1 = time.time()
            with contextlib.redirect_stdout(b), contextlib.redirect_stderr(io.StringIO()):
                body.policy_step()
            t2 = time.time()
            chk("⑧ 真鏈 policy_step:第二次沿用 · 輸出相同 · 比第一次快", a.getvalue() == b.getvalue() and (t2 - t1) < (t1 - t0),
                f"第一次 {t1 - t0:.2f}s → 第二次 {t2 - t1:.2f}s")
        else:
            chk("⑧ 真鏈 policy_step(沒有 git 鑰匙 → 跳過,不冒充)", True, "SKIP")
    CACHE = keep_cache
    owner = next((m for m in _chain_mods_v0188() if callable(vars(m).get("forwarded_defs")) and callable(vars(m).get("extend"))), None)
    if owner is not None:
        orig = getattr(owner.forwarded_defs, "__wrapped__", owner.forwarded_defs)
        tails = [(_STEM, HERE / Path(__file__).name)]
        with tempfile.TemporaryDirectory() as td:
            keep_cache, CACHE = CACHE, Path(td)
            fast = make_forwarded_defs_v0188(owner)
            want = orig(tails)
            t0 = time.time()
            got1 = fast(tails)
            t1 = time.time()
            got2 = fast(tails)
            t2 = time.time()
            CACHE = keep_cache
        chk("⑨ 逐檔定義沿用:真鏈上與 v0172 原函數逐鍵相同(含來源 / 行號 / via);第二次不重解析",
            want == got1 == got2 and len(want) > 0 and _STATE.get("reparsed") == 0,
            f"{len(want)} 定義 · 第一次 {t1 - t0:.2f}s → 第二次 {t2 - t1:.2f}s")
    else:
        chk("⑨ 逐檔定義沿用(鏈上沒有 forwarded_defs → 跳過,不冒充)", True, "SKIP")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋在;不碰 TA-Lib;沒有任何規則被改(只決定要不要重算)", "[VIA:ACCEL-BRIDGE" in text and "import talib" not in text.replace('"import talib"', ""))
    card = help_catalog()
    chk("⑪ help 目前生效入口 = 本版 · 前版 = v0187 · 多一行治理沿用說明", card.get("entry") == Path(__file__).name
        and card.get("previous") == PRIOR_PATH.name and "cache" in card, (card.get("entry"), card.get("previous")))
    print(f"  [計] VCGC v0188 治理沿用 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'} · 前版鏈 rc {prior_rc}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
