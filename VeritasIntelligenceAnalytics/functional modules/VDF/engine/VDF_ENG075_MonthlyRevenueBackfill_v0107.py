#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG075_MonthlyRevenueBackfill v0107 — 薄尾:轉接改走生效鏈(PR #542 Codex P1;取代 VDF_ENG075_MonthlyRevenueBackfill_v0106 的另載法)

操作員令(2026-10-20):「繼續,用中文回復  一路實測修復到底 … 授權全自動完成 測完開PR合併」。
病因(PR #542 Codex P1,實測確認):v0106 的模組層 __getattr__ 把前版鏈每一支各自另載一份再取名稱;
  但鏈上中間層的 _prior() 會在取前版時補丁(例:把前版的 gate_open 換成 ScrapeGate 的 gate_open),
  另載的那份沒有補丁 → 經尾版取 run() / gate_open() 拿到的是沒補丁的舊定義(同意閘判法跟實際執行路徑不同)。
本版(行為照前版鏈實際執行路徑,不另造):
  ① 生效鏈:v0105 照常載入;往下每一層,上一層若有無參 _prior()(前版自己取前版,含補丁)就用它回的模組,
     沒有才另載(上一層不補丁,兩者等價)。模組層 __getattr__ 沿生效鏈由新到舊取。
  ② 直接執行 = 原樣交給 v0105(runpy;參數 · 輸出 · 結束碼 · 同意閘行為一字不改)。
  ③ 自測 ⑥:每層有 _prior() 就一定用它的回傳;生效模組的每個函式(含補丁進來的)跟前版自己再取一次的結果同碼。
     自測 ⑦(有 gate_open 補丁才算):轉接取到的 gate_open 用字典實測 —— 沒同意 False · 雙同意 True(不碰環境變數)。
     自測 ⑧:取下一層的防呆(_prior 回錯檔 → 另載;要參數的 _prior 不當取前版)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import ast
import importlib.util
import inspect
import re
import runpy
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG075_MonthlyRevenueBackfill"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"



CHAIN_VERSIONS = ('0105', '0104', '0103', '0100')       # 照 CGC_MDL158 chain 圖的實際委派鏈(尾版 → 本體);更舊、已被本體重寫取代的版不轉
CHAIN = [HERE / ("%s_v%s.py" % (_STEM, v)) for v in CHAIN_VERSIONS]
PRIOR_PATH = CHAIN[0]
_MODS: dict = {}


def _module(p: Path):
    """前版鏈某一支(惰性載入一次;模組名帶雙方版號,不和別處載入的同一支撞名)。"""
    if p not in _MODS:
        name = "%s_fwd_v%s_from_v%s" % (_STEM, p.stem.rsplit("_v", 1)[-1], Path(__file__).stem.rsplit("_v", 1)[-1])
        spec = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        _MODS[p] = mod
    return _MODS[p]


_EFF: list = []        # 生效鏈 [(路徑, 模組, 取法)]


def _prior_fn(mod):
    """上一層自己取前版的無參 _prior()(沒有 / 要參數 → None)。"""
    f = vars(mod).get("_prior") if mod is not None else None
    if not callable(f) or isinstance(f, type):
        return None
    try:
        sig = inspect.signature(f)
    except (TypeError, ValueError):
        return None
    if any(x.default is x.empty and x.kind not in (x.VAR_POSITIONAL, x.VAR_KEYWORD) for x in sig.parameters.values()):
        return None
    return f


def _next_module(prev, p: Path, load=None) -> tuple:
    """上一層有無參 _prior() 且回的就是 p 那支 → 用它(含補丁);否則另載。回 (模組, 取法)。"""
    f = _prior_fn(prev)
    if f is not None:
        r = f()
        if isinstance(r, types.ModuleType) and Path(getattr(r, "__file__", "") or "").resolve() == Path(p).resolve():
            return r, "上一層 _prior()"
    return (load or _module)(p), "另載"


def _effective() -> list:
    """生效鏈:CHAIN[0] 照常載入;往下每層照 _next_module 取。只算一次。"""
    if not _EFF:
        prev = None
        for p in CHAIN:
            mod, how = _next_module(prev, p)
            _EFF.append((p, mod, how))
            prev = mod
    return _EFF


def _same_fn(a, b) -> bool:
    """同一份程式碼(檔 · 起行 · 位元碼);不同模組實例也算同一個定義。"""
    return (inspect.isfunction(a) and inspect.isfunction(b)
            and (a.__code__.co_filename, a.__code__.co_firstlineno, a.__code__.co_code)
            == (b.__code__.co_filename, b.__code__.co_firstlineno, b.__code__.co_code))


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    for p, mod, _how in _effective():
        if name in vars(mod):
            return vars(mod)[name]
    raise AttributeError("%s:前版鏈 %s 都沒有 %s" % (TAG, [q.name for q in CHAIN], name))


def public_names() -> list:
    """前版鏈每支檔的頂層公開名稱(def / class / 賦值;不以底線開頭)。"""
    out = set()
    for p in CHAIN:
        for node in ast.parse(p.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    if isinstance(t, ast.Name):
                        out.add(t.id)
    return sorted(n for n in out if not n.startswith("_"))


def check_forwarding() -> int:
    """本版轉接檢查;回 0 = 全過。"""
    p = f = 0

    def chk(label, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % label)
        else:
            f += 1
            print("  [FAIL] %s%s" % (label, (" · " + str(note)[:300]) if note else ""))

    me = sys.modules[__name__]
    names = public_names()
    miss = [n for n in names if not hasattr(me, n)]
    chk("① 前版鏈 %d 支的公開名稱 %d 個全取得到(由新到舊取最新定義)" % (len(CHAIN), len(names)), names and not miss, miss)
    newest = {}
    for q in reversed(CHAIN):
        for n in public_names_of(q):
            newest[n] = q
    effm = {p: m for p, m, _h in _effective()}
    wrong = [n for n, q in newest.items() if n not in vars(me) and getattr(me, n) is not vars(effm[q]).get(n)]
    chk("② 同名取最新那一支的定義(生效鏈上的那份,不是更舊的)", not wrong, wrong)
    probe = _effective()[0][1]
    probe.__fwd_probe__ = 1                       # 鏈上真的有的雙底線名稱也不准轉
    try:
        getattr(me, "__fwd_probe__")
        dunder = False
    except AttributeError:
        dunder = True
    finally:
        del probe.__fwd_probe__
    try:
        getattr(me, "no_such_name_fwd_check")
        unknown = False
    except AttributeError as exc:
        unknown = "前版鏈" in str(exc)
    chk("③ 雙底線名稱不轉 · 鏈上沒有的名稱照實 AttributeError(說明找過哪幾支)", dunder and unknown)
    globs_prior = re.compile(r"glob\([^)\n]*(?:%s|_STEM)[^)\n]*_v\*\.py" % re.escape(_STEM))   # glob 取本族前版(不是網路橋那種 glob)
    links = []
    for a, b in zip(CHAIN, CHAIN[1:]):
        ta = a.read_text(encoding="utf-8")
        if b.stem not in ta and not globs_prior.search(ta):
            links.append("%s 沒連到 %s" % (a.name, b.name))
    body = CHAIN[-1]
    tb = body.read_text(encoding="utf-8")
    older = [q.name for q in HERE.glob(_STEM + "_v*.py")
             if q.stem.rsplit("_v", 1)[-1] < body.stem.rsplit("_v", 1)[-1] and q.stem in tb]
    if older or globs_prior.search(tb):
        links.append("%s 還連更舊的 %s(不是本體)" % (body.name, older or "glob"))
    chk("⑤ 委派鏈完整:每支都連到下一支(檔名或 glob 取前版)· 最後一支 %s 是本體(不再連更舊的)" % body.name, not links, links)
    eff = _effective()
    bad, patched = [], []
    for (pa, ma, _ha), (pb, mb, hb) in zip(eff, eff[1:]):
        pf = _prior_fn(ma)
        if pf is None:
            continue
        if hb != "上一層 _prior()":
            bad.append("%s 有 _prior() 卻沒用它" % pa.name)
            continue
        fresh = pf()                                  # 前版自己再取一次(另一個實例)
        for k, v in vars(fresh).items():
            if k.startswith("__") or not inspect.isfunction(v):
                continue
            if not _same_fn(vars(mb).get(k), v):
                bad.append("%s.%s" % (pb.name, k))
            elif v.__code__.co_filename != str(pb) and Path(v.__code__.co_filename).resolve() != pb.resolve():
                patched.append(k)
    chk("⑥ 生效鏈:每層有 _prior() 就用它的回傳(%s);函式跟前版自己再取一次同碼 · 補丁進來的 %s 也傳到"
        % (" → ".join(h for _p, _m, h in eff[1:]) or "單層", sorted(set(patched)) or "無"), not bad, bad)
    fake_b = types.ModuleType("fwd_fake_b")
    fake_b.__file__ = str(HERE / "fwd_fake_b.py")
    other = types.ModuleType("fwd_fake_other")
    other.__file__ = str(HERE / "fwd_fake_other.py")
    lv1 = types.ModuleType("fwd_fake_l1")
    lv1._prior = lambda: other                    # 回的不是下一支
    lv2 = types.ModuleType("fwd_fake_l2")
    lv2._prior = lambda: fake_b
    lv3 = types.ModuleType("fwd_fake_l3")
    lv3._prior = lambda need: fake_b              # 要參數 → 不是取前版函式
    side = lambda q: ("另載的", Path(q).name)
    got = [_next_module(lv1, HERE / "fwd_fake_b.py", side), _next_module(lv2, HERE / "fwd_fake_b.py", side),
           _next_module(lv3, HERE / "fwd_fake_b.py", side), _next_module(None, HERE / "fwd_fake_b.py", side)]
    chk("⑧ 取下一層的防呆:_prior() 回的不是下一支 → 另載 · 回的是 → 用它 · 要參數的 _prior 不當取前版 · 沒上一層 → 另載",
        [h for _m, h in got] == ["另載", "上一層 _prior()", "另載", "另載"] and got[1][0] is fake_b, [h for _m, h in got])
    if "gate_open" in set(patched):
        g = getattr(me, "gate_open")
        ok_env = {"VIA_NET_" + "CONSENT": "YES", "VIA_SCRAPE_" + "CONSENT": "I_ACCEPT_RESPONSIBLE_SCRAPING"}
        try:
            gate = (g({}) is False, g(ok_env) is True)
        except TypeError as exc:
            gate = ("TypeError", str(exc)[:80])
        chk("⑦ 轉接取到的 gate_open 是補丁後那支:沒同意 False · 雙同意 True(字典實測,不碰環境變數)", gate == (True, True), gate)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("④ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print("  [計] %s 轉接 %d 名 · 本版 %d/%d · %s" % (TAG, len(names), p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def public_names_of(p: Path) -> list:
    out = set()
    for node in ast.parse(p.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Name):
                    out.add(t.id)
    return sorted(n for n in out if not n.startswith("_"))


def selftest() -> int:
    """程式呼叫的自測:本版轉接檢查 + 前版鏈自己的 selftest(有的話)。"""
    rc = check_forwarding()
    if rc:
        return rc
    prior = __getattr__("selftest") if "selftest" in public_names() else None
    return prior() if callable(prior) else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        print("=== %s · 薄尾自測(前版鏈公開名稱轉接;零網路)===" % TAG, flush=True)
        if check_forwarding():
            raise SystemExit(1)
    runpy.run_path(str(PRIOR_PATH), run_name="__main__")
